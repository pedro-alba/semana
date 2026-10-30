import json
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from semana import clock
from semana.accounts import Account
from semana.db import Con, transaction
from semana.sanitize import clean

routes = APIRouter(prefix="/api")

OPS: dict[str, tuple[type[BaseModel], Callable]] = {}

OK = {"status": "ok"}
NOT_FOUND = {"status": "not_found"}


def operation(name, model):
    def register(f):
        OPS[name] = (model, f)
        return f
    return register


def _monday(s):
    if not clock.is_monday(s):
        raise ValueError("not a Monday")
    return s


def _max_1mb(s):
    if len(s.encode()) > 1_000_000:
        raise ValueError("larger than 1 MB")
    return s


Monday = Annotated[str, AfterValidator(_monday)]
Html = Annotated[str, AfterValidator(_max_1mb)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
SubtaskText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
ProjectName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class Batch(BaseModel):
    account_id: str
    ops: list[dict] = Field(max_length=200)


@routes.post("/ops")
def apply_ops(batch: Batch, account: Account, con: Con):
    if batch.account_id != account["id"]:
        return JSONResponse({"error": "wrong_account"}, 409)
    results = []
    for op in batch.ops:
        if op.get("op") not in OPS:
            results.append({"status": "invalid", "fields": ["op"]})
            continue
        model, handler = OPS[op["op"]]
        try:
            m = model.model_validate(op)
        except ValidationError as e:
            fields = list(dict.fromkeys(str(err["loc"][0]) for err in e.errors() if err["loc"]))
            results.append({"status": "invalid", "fields": fields})
            continue
        with transaction(con):
            results.append(handler(con, account, m))
    return {"results": results}


# --- helpers ---

def owned(con, table, id, account_id):
    return con.execute(
        f"SELECT * FROM {table} WHERE id = ? AND account_id = ?", (str(id), account_id)
    ).fetchone()


def touch_task(con, task_id):
    con.execute(
        "UPDATE task SET updated_at = ? WHERE id = ?", (clock.iso(clock.now()), str(task_id))
    )


def _exists(con, table, id, account_id):
    """For idempotent creates: None if the id is free, else the result to return."""
    owner = con.execute(f"SELECT account_id FROM {table} WHERE id = ?", (str(id),)).fetchone()
    if owner is None:
        return None
    return OK if owner["account_id"] == account_id else NOT_FOUND


def _max_position(con, account_id, project_id, week, exclude=""):
    return con.execute(
        "SELECT COALESCE(MAX(position), 0) FROM task"
        " WHERE account_id = ? AND project_id = ? AND week = ? AND id != ?",
        (account_id, project_id, week, exclude),
    ).fetchone()[0]


def write_text(con, table, column, key, account_id, value, base_rev):
    rev_col = "rev" if column == "html" else f"{column}_rev"
    where = " AND ".join(f"{k} = ?" for k in key) + " AND account_id = ?"
    args = (*key.values(), account_id)
    row = con.execute(f"SELECT {column}, {rev_col} FROM {table} WHERE {where}", args).fetchone()
    if row is None:
        return NOT_FOUND
    current, rev = row
    if base_rev == rev:
        con.execute(f"UPDATE {table} SET {column} = ?, {rev_col} = ? WHERE {where}",
                    (value, rev + 1, *args))
        return {"status": "ok", "rev": rev + 1}
    if value == current:
        return {"status": "ok", "rev": rev}
    return {"status": "conflict", "value": current, "rev": rev}


# --- projects and tasks ---

class ProjectCreate(BaseModel):
    id: UUID
    name: ProjectName


@operation("project.create", ProjectCreate)
def project_create(con, account, m):
    if exists := _exists(con, "project", m.id, account["id"]):
        return exists
    con.execute(
        "INSERT INTO project (id, account_id, name, created_at) VALUES (?, ?, ?, ?)",
        (str(m.id), account["id"], m.name, clock.iso(clock.now())),
    )
    return OK


class TaskCreate(BaseModel):
    id: UUID
    project_id: UUID
    week: Monday


@operation("task.create", TaskCreate)
def task_create(con, account, m):
    if not owned(con, "project", m.project_id, account["id"]):
        return NOT_FOUND
    if exists := _exists(con, "task", m.id, account["id"]):
        return exists
    now = clock.now()
    week = max(m.week, clock.monday(now, account["timezone"]))
    position = _max_position(con, account["id"], str(m.project_id), week) + 1
    con.execute(
        "INSERT INTO task (id, account_id, project_id, week, position, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(m.id), account["id"], str(m.project_id), week, position,
         clock.iso(now), clock.iso(now)),
    )
    return OK


class TaskProgress(BaseModel):
    id: UUID
    value: int = Field(ge=0, le=100)


@operation("task.progress", TaskProgress)
def task_progress(con, account, m):
    t = owned(con, "task", m.id, account["id"])
    if not t:
        return NOT_FOUND
    position = t["position"]
    if (t["progress"] == 100) != (m.value == 100):
        position = _max_position(con, account["id"], t["project_id"], t["week"], t["id"]) + 1
    con.execute(
        "UPDATE task SET progress = ?, position = ? WHERE id = ?", (m.value, position, t["id"])
    )
    touch_task(con, t["id"])
    return OK


class TaskImportant(BaseModel):
    id: UUID
    value: bool


@operation("task.important", TaskImportant)
def task_important(con, account, m):
    t = owned(con, "task", m.id, account["id"])
    if not t:
        return NOT_FOUND
    con.execute("UPDATE task SET important = ? WHERE id = ?", (int(m.value), t["id"]))
    touch_task(con, t["id"])
    return OK


class TaskReorder(BaseModel):
    project_id: UUID
    week: Monday
    ids: list[UUID] = Field(max_length=1000)


@operation("task.reorder", TaskReorder)
def task_reorder(con, account, m):
    if not owned(con, "project", m.project_id, account["id"]):
        return NOT_FOUND
    positions = dict(con.execute(
        "SELECT id, position FROM task WHERE account_id = ? AND project_id = ? AND week = ?",
        (account["id"], str(m.project_id), m.week),
    ).fetchall())
    ids = [i for i in dict.fromkeys(str(i) for i in m.ids) if i in positions]
    for id, position in zip(ids, sorted(positions[i] for i in ids)):
        con.execute("UPDATE task SET position = ? WHERE id = ? AND account_id = ?",
                    (position, id, account["id"]))
    return OK


class IdOnly(BaseModel):
    id: UUID


class TaskDue(BaseModel):
    id: UUID
    value: date | None


@operation("task.due", TaskDue)
def task_due(con, account, m):
    t = owned(con, "task", m.id, account["id"])
    if not t:
        return NOT_FOUND
    con.execute("UPDATE task SET due = ? WHERE id = ?",
                (m.value and m.value.isoformat(), t["id"]))
    touch_task(con, t["id"])
    return OK


@operation("task.delete", IdOnly)
def task_delete(con, account, m):
    con.execute("DELETE FROM task WHERE id = ? AND account_id = ?", (str(m.id), account["id"]))
    return OK


# --- task text ---

class TaskTitle(BaseModel):
    id: UUID
    value: Title
    base_rev: int


@operation("task.title", TaskTitle)
def task_title(con, account, m):
    r = write_text(con, "task", "title", {"id": str(m.id)}, account["id"], m.value, m.base_rev)
    if r["status"] == "ok":
        touch_task(con, m.id)
    return r


class TaskNotes(BaseModel):
    id: UUID
    value: Html
    base_rev: int


@operation("task.notes", TaskNotes)
def task_notes(con, account, m):
    r = write_text(con, "task", "notes", {"id": str(m.id)}, account["id"],
                   clean(m.value), m.base_rev)
    if r["status"] == "ok":
        touch_task(con, m.id)
    return r


# --- subtasks ---

class SubtaskCreate(BaseModel):
    id: UUID
    task_id: UUID
    text: SubtaskText
    created_at: AwareDatetime | None = None
    done_at: AwareDatetime | None = None


@operation("subtask.create", SubtaskCreate)
def subtask_create(con, account, m):
    if not owned(con, "task", m.task_id, account["id"]):
        return NOT_FOUND
    if exists := _exists(con, "subtask", m.id, account["id"]):
        return exists
    con.execute(
        "INSERT INTO subtask (id, account_id, task_id, text, created_at, done_at)"
        " VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
        (str(m.id), account["id"], str(m.task_id), m.text,
         clock.iso(m.created_at or clock.now()),
         m.done_at and clock.iso(m.done_at)),
    )
    touch_task(con, m.task_id)
    return OK


class SubtaskTextOp(BaseModel):
    id: UUID
    value: SubtaskText
    base_rev: int


@operation("subtask.text", SubtaskTextOp)
def subtask_text(con, account, m):
    s = owned(con, "subtask", m.id, account["id"])
    if not s:
        return NOT_FOUND
    r = write_text(con, "subtask", "text", {"id": s["id"]}, account["id"], m.value, m.base_rev)
    if r["status"] == "ok":
        touch_task(con, s["task_id"])
    return r


class SubtaskDone(BaseModel):
    id: UUID
    done: bool


@operation("subtask.done", SubtaskDone)
def subtask_done(con, account, m):
    s = owned(con, "subtask", m.id, account["id"])
    if not s:
        return NOT_FOUND
    done_at = (s["done_at"] or clock.iso(clock.now())) if m.done else None
    con.execute("UPDATE subtask SET done_at = ? WHERE id = ?", (done_at, s["id"]))
    touch_task(con, s["task_id"])
    return OK


@operation("subtask.delete", IdOnly)
def subtask_delete(con, account, m):
    s = owned(con, "subtask", m.id, account["id"])
    if s:
        con.execute("DELETE FROM subtask WHERE id = ?", (s["id"],))
        touch_task(con, s["task_id"])
    return OK


# --- week notes ---

class WeekNotes(BaseModel):
    project_id: UUID
    week: Monday
    value: Html
    base_rev: int


@operation("week.notes", WeekNotes)
def week_notes(con, account, m):
    if not owned(con, "project", m.project_id, account["id"]):
        return NOT_FOUND
    value = clean(m.value)
    key = {"project_id": str(m.project_id), "week": m.week}
    r = write_text(con, "week_notes", "html", key, account["id"], value, m.base_rev)
    if r["status"] != "not_found":
        return r
    if m.base_rev == 0:
        con.execute(
            "INSERT INTO week_notes (account_id, project_id, week, html, rev)"
            " VALUES (?, ?, ?, ?, 1)",
            (account["id"], str(m.project_id), m.week, value),
        )
        return {"status": "ok", "rev": 1}
    return {"status": "conflict", "value": "", "rev": 0}


# --- events (feature 002) ---

def _moment(s):
    if len(s) != 16:
        raise ValueError("format YYYY-MM-DDTHH:MM")
    datetime.strptime(s, "%Y-%m-%dT%H:%M")
    return s


Moment = Annotated[str, AfterValidator(_moment)]
EVENT_FIELDS = ("project_id", "title", "start", "end", "all_day", "repeat", "until",
                "location", "description", "fills_day", "skipped")


class EventSave(BaseModel):
    id: UUID
    project_id: UUID | None
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    start: Moment
    end: Moment
    all_day: bool
    repeat: Literal["none", "daily", "weekly", "monthly"]
    until: date | None
    location: Annotated[str, StringConstraints(max_length=500)]
    description: Annotated[str, StringConstraints(max_length=10_000)]
    fills_day: bool = False
    skipped: list[date] = Field(default_factory=list, max_length=1000)
    base_rev: int

    @model_validator(mode="after")
    def _rules(self):
        start = datetime.fromisoformat(self.start)
        end = datetime.fromisoformat(self.end)
        if not start < end <= start + timedelta(days=31):
            raise ValueError("end must be after start, within 31 days")
        if self.repeat == "none" and self.until is not None:
            raise ValueError("end date only with repeat")
        if self.until and self.until < start.date():
            raise ValueError("end date before start")
        return self

    def row(self):
        return {
            "project_id": self.project_id and str(self.project_id), "title": self.title,
            "start": self.start, "end": self.end, "all_day": int(self.all_day),
            "repeat": self.repeat, "until": self.until and self.until.isoformat(),
            "location": self.location, "description": self.description,
            "fills_day": int(self.fills_day),
            "skipped": json.dumps(sorted({d.isoformat() for d in self.skipped})),
        }


def columns(names):
    return ", ".join(f'"{k}"' for k in names)


@operation("event.save", EventSave)
def event_save(con, account, m):
    from semana.reads import event_json
    if m.project_id and not owned(con, "project", m.project_id, account["id"]):
        return NOT_FOUND
    new, now = m.row(), clock.iso(clock.now())
    row = con.execute("SELECT * FROM event WHERE id = ?", (str(m.id),)).fetchone()
    if row is None:
        if m.base_rev != 0:
            return {"status": "conflict", "value": None, "rev": 0}
        con.execute(
            f"INSERT INTO event (id, account_id, {columns(EVENT_FIELDS)},"
            " created_at, updated_at) VALUES (?, ?, " + "?, " * len(EVENT_FIELDS) + "?, ?)",
            (str(m.id), account["id"], *new.values(), now, now),
        )
        return {"status": "ok", "rev": 1}
    if row["account_id"] != account["id"]:
        return NOT_FOUND
    if all(row[k] == v for k, v in new.items()):
        return {"status": "ok", "rev": row["rev"]}
    if m.base_rev != row["rev"]:
        return {"status": "conflict", "value": event_json(row), "rev": row["rev"]}
    con.execute(
        "UPDATE event SET " + ", ".join(f'"{k}" = ?' for k in new)
        + ", rev = ?, updated_at = ? WHERE id = ?",
        (*new.values(), row["rev"] + 1, now, row["id"]),
    )
    return {"status": "ok", "rev": row["rev"] + 1}


@operation("event.delete", IdOnly)
def event_delete(con, account, m):
    con.execute("DELETE FROM event WHERE id = ? AND account_id = ?", (str(m.id), account["id"]))
    return OK


# --- account settings ---

class AccountAppearance(BaseModel):
    theme: Literal["graphite", "paper", "ink"]
    mode: Literal["light", "dark", "system"]
    font: Literal["theme", "mono", "sans", "serif"]
    palette: Literal["classic", "sunset", "lavender", "moss", "traffic", "neutral"]


@operation("account.appearance", AccountAppearance)
def account_appearance(con, account, m):
    con.execute("UPDATE account SET appearance = ? WHERE id = ?",
                (json.dumps(m.model_dump()), account["id"]))
    return OK


class AccountLanguage(BaseModel):
    value: Literal["auto", "en", "pt-BR"]


@operation("account.language", AccountLanguage)
def account_language(con, account, m):
    con.execute("UPDATE account SET language = ? WHERE id = ?", (m.value, account["id"]))
    return OK
