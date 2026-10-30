"""Account backup (feature 005): export, and import replacing everything (R2, R3)."""
import base64
import json
import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from semana import clock, rollover
from semana.accounts import Account
from semana.db import Con, transaction
from semana.images import store, valid_mime
from semana.ops import (
    EVENT_FIELDS,
    EventSave,
    Html,
    Monday,
    ProjectName,
    SubtaskText,
    Title,
    columns,
)
from semana.reads import event_json
from semana.sanitize import IMAGE, clean

routes = APIRouter(prefix="/api")

Id = Annotated[str, StringConstraints(min_length=1, max_length=130)]


class Project(BaseModel):
    id: Id
    name: ProjectName


class Subtask(BaseModel):
    id: Id
    text: SubtaskText
    created_at: AwareDatetime
    done_at: AwareDatetime | None


class LogEntry(BaseModel):
    id: Id
    at: AwareDatetime
    kind: Literal["system", "note"]
    text: Annotated[str, StringConstraints(max_length=10_000)]


class Task(BaseModel):
    id: Id
    project_id: Id
    week: Monday
    title: Title
    notes: Html
    important: bool
    progress: int = Field(ge=0, le=100)
    position: float
    weeks_open: int = Field(ge=1)
    due: date | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    subtasks: list[Subtask]
    log: list[LogEntry]


class Note(BaseModel):
    project_id: Id
    week: Monday
    html: Html


class Event(EventSave):
    id: Id
    project_id: Id | None
    base_rev: int = 0


class Snapshot(BaseModel):
    week: Monday
    tasks: list[Task]


class Image(BaseModel):
    id: Id
    mime: str
    data: str  # base64


class Backup(BaseModel):
    format: Literal["semana-backup"]
    version: Literal[1]
    processed_week: Monday
    projects: list[Project] = Field(min_length=1)
    tasks: list[Task]
    notes: list[Note]
    events: list[Event]
    snapshots: list[Snapshot]
    images: list[Image] = []

    @model_validator(mode="after")
    def _links(self):
        def unique(ids):
            ids = list(ids)
            return len(ids) == len(set(ids))
        pids = {p.id for p in self.projects}
        if not (unique(p.id for p in self.projects) and unique(t.id for t in self.tasks)
                and unique(s.id for t in self.tasks for s in t.subtasks)
                and unique(h.id for t in self.tasks for h in t.log)
                and unique(e.id for e in self.events)
                and unique((n.project_id, n.week) for n in self.notes)):
            raise ValueError("duplicate IDs")
        if any(x.project_id not in pids for x in [*self.tasks, *self.notes]):
            raise ValueError("unknown project")
        return self


# --- export ---

def _file_task(t):
    """task_json (reads) → task in the file: without revisions."""
    return {
        **{k: t[k] for k in ("id", "project_id", "week", "title", "notes", "important",
                             "progress", "position", "weeks_open", "due", "created_at",
                             "updated_at")},
        "subtasks": [{k: s[k] for k in ("id", "text", "created_at", "done_at")}
                     for s in t["subtasks"]],
        "log": t["log"],
    }


@routes.get("/backup")
def export(account: Account, con: Con):
    from semana.reads import task_json
    rollover.apply(con, account["id"])
    aid = account["id"]
    a = con.execute("SELECT processed_week FROM account WHERE id = ?", (aid,)).fetchone()
    tasks = con.execute(
        "SELECT * FROM task WHERE account_id = ? ORDER BY week, project_id, position", (aid,)
    ).fetchall()
    events = con.execute(
        "SELECT * FROM event WHERE account_id = ? ORDER BY start, id", (aid,)
    ).fetchall()
    snapshots = con.execute(
        "SELECT week, tasks FROM snapshot WHERE account_id = ? ORDER BY week", (aid,)
    ).fetchall()
    return {
        "format": "semana-backup",
        "version": 1,
        "exported_at": clock.iso(clock.now()),
        "processed_week": a["processed_week"],
        "projects": [dict(p) for p in con.execute(
            "SELECT id, name, created_at FROM project WHERE account_id = ?"
            " ORDER BY created_at, rowid", (aid,))],
        "tasks": [_file_task(task_json(con, t)) for t in tasks],
        "notes": [dict(n) for n in con.execute(
            "SELECT project_id, week, html FROM week_notes"
            " WHERE account_id = ? AND html <> '' ORDER BY week, project_id", (aid,))],
        "events": [{k: v for k, v in event_json(x).items() if k != "rev"} for x in events],
        "snapshots": [{"week": r["week"],
                       "tasks": [_file_task(t) for t in json.loads(r["tasks"])]}
                      for r in snapshots],
        "images": [{"id": i["id"], "mime": i["mime"],
                    "data": base64.b64encode(i["data"]).decode()}
                   for i in con.execute(
                       "SELECT id, mime, data FROM image WHERE account_id = ?"
                       " ORDER BY created_at, id", (aid,))],
    }


# --- import ---

def _ordered(tasks):
    """Positions redone as 1, 2, 3… within each project + week, in file order."""
    groups = {}
    for t in sorted(tasks, key=lambda t: t.position):
        groups.setdefault((t.project_id, t.week), []).append(t)
    return [(t, i) for g in groups.values() for i, t in enumerate(g, 1)]


class ImageLimit(Exception):
    pass


@routes.post("/backup")
def import_(body: Backup, account: Account, con: Con):
    try:
        return _import(body, account, con)
    except ImageLimit as e:
        status, error = e.args[0]
        return JSONResponse(error, status)


def _import(body, account, con):
    aid = account["id"]
    now = clock.now()
    current = clock.monday(now, account["timezone"])
    new = {}

    def nid(old):
        return new.setdefault(old, str(uuid.uuid4()))

    def iso(dt):
        return dt and clock.iso(dt)

    # Images (008): new IDs and the text rewritten with them.
    imgs = {}
    for i in body.images:
        try:
            data = base64.b64decode(i.data, validate=True)
        except ValueError:
            data = b""
        if not valid_mime(i.mime, data):
            return JSONResponse({"error": "invalid", "fields": ["images"]}, 422)
        imgs[i.id] = (str(uuid.uuid4()), i.mime, data)

    def clean_html(html):
        def swap(m):
            old = m.group().rsplit("/", 1)[1]
            return "/api/images/" + imgs.get(old, (old,))[0]
        return clean(IMAGE.sub(swap, html))

    def task_row(t, position):
        return {
            "id": nid(t.id), "project_id": new[t.project_id], "week": t.week,
            "title": t.title, "title_rev": 0, "notes": clean_html(t.notes),
            "notes_rev": 0, "important": t.important, "progress": t.progress,
            "position": position, "weeks_open": t.weeks_open,
            "due": t.due and t.due.isoformat(), "created_at": iso(t.created_at),
            "updated_at": iso(t.updated_at),
        }

    with transaction(con):
        con.execute("DELETE FROM project WHERE account_id = ?", (aid,))
        con.execute("DELETE FROM event WHERE account_id = ?", (aid,))
        con.execute("DELETE FROM snapshot WHERE account_id = ?", (aid,))
        con.execute("DELETE FROM image WHERE account_id = ?", (aid,))
        for new_id, mime, data in imgs.values():
            if error := store(con, aid, new_id, mime, data):
                raise ImageLimit(error)
        for p in body.projects:
            con.execute("INSERT INTO project (id, account_id, name, created_at) VALUES (?, ?, ?, ?)",
                        (nid(p.id), aid, p.name, clock.iso(now)))
        for t, position in _ordered(body.tasks):
            row = task_row(t, position)
            row["important"] = int(row["important"])
            con.execute(
                f"INSERT INTO task (account_id, {', '.join(row)})"
                f" VALUES (?, {', '.join('?' * len(row))})", (aid, *row.values()))
            con.executemany(
                "INSERT INTO subtask (id, account_id, task_id, text, created_at, done_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [(nid(s.id), aid, row["id"], s.text, iso(s.created_at),
                  iso(s.done_at)) for s in t.subtasks])
            con.executemany(
                "INSERT INTO log_entry (id, account_id, task_id, at, kind, text)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [(nid(h.id), aid, row["id"], iso(h.at), h.kind, h.text) for h in t.log])
        con.executemany(
            "INSERT INTO week_notes (account_id, project_id, week, html) VALUES (?, ?, ?, ?)",
            [(aid, new[n.project_id], n.week, html) for n in body.notes
             if (html := clean_html(n.html))])
        for e in body.events:
            row = e.row()
            row["project_id"] = new.get(e.project_id)
            con.execute(
                f"INSERT INTO event (id, account_id, {columns(EVENT_FIELDS)},"
                f" created_at, updated_at) VALUES (?, ?, {', '.join('?' * len(row))}, ?, ?)",
                (str(uuid.uuid4()), aid, *(row[k] for k in EVENT_FIELDS),
                 clock.iso(now), clock.iso(now)))
        for s in body.snapshots:
            if s.week >= current:
                continue
            tasks = []
            for t, position in _ordered([t for t in s.tasks if t.project_id in new]):
                row = task_row(t, position)
                row["subtasks"] = [
                    {"id": nid(x.id), "text": x.text, "text_rev": 0,
                     "created_at": iso(x.created_at), "done_at": iso(x.done_at)}
                    for x in t.subtasks]
                row["log"] = [{"id": nid(h.id), "at": iso(h.at), "kind": h.kind, "text": h.text}
                              for h in t.log]
                tasks.append(row)
            con.execute("INSERT INTO snapshot (account_id, week, tasks) VALUES (?, ?, ?)",
                        (aid, s.week, json.dumps(tasks)))
        con.execute("UPDATE account SET processed_week = ? WHERE id = ?",
                    (min(body.processed_week, clock.add_days(current, -7)), aid))
    rollover.apply(con, aid)
    return {"status": "ok"}
