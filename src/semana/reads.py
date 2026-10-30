import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from semana import clock, rollover
from semana.accounts import Account, account_json
from semana.db import Con

routes = APIRouter(prefix="/api")


def task_json(con, t):
    subtasks = con.execute(
        "SELECT id, text, text_rev, created_at, done_at FROM subtask"
        " WHERE task_id = ? AND account_id = ? ORDER BY created_at, rowid",
        (t["id"], t["account_id"]),
    ).fetchall()
    log = con.execute(
        "SELECT id, at, kind, text FROM log_entry"
        " WHERE task_id = ? AND account_id = ? ORDER BY at, rowid",
        (t["id"], t["account_id"]),
    ).fetchall()
    return {
        "id": t["id"], "project_id": t["project_id"], "week": t["week"],
        "title": t["title"], "title_rev": t["title_rev"],
        "notes": t["notes"], "notes_rev": t["notes_rev"],
        "important": bool(t["important"]), "progress": t["progress"], "position": t["position"],
        "weeks_open": t["weeks_open"],
        "created_at": t["created_at"], "updated_at": t["updated_at"],
        "due": t["due"],
        "subtasks": [dict(s) for s in subtasks],
        "log": [dict(h) for h in log],
    }


@routes.get("/start")
def start(account: Account, con: Con):
    rollover.apply(con, account["id"])
    now = clock.now()
    projects = con.execute(
        "SELECT id, name FROM project WHERE account_id = ? ORDER BY created_at, rowid",
        (account["id"],),
    ).fetchall()
    return {
        "account": account_json(account),
        "current_week": clock.monday(now, account["timezone"]),
        "now": clock.iso(now),
        "projects": [dict(p) for p in projects],
        # AGPL §13: whoever hosts it offers the source code to users
        "source_url": os.environ.get("SEMANA_SOURCE_URL") or None,
    }


@routes.get("/week")
def week(project: str, week: str, account: Account, con: Con):
    if not clock.is_monday(week):
        return JSONResponse({"error": "invalid", "fields": ["week"]}, 422)
    rollover.apply(con, account["id"])
    if not con.execute(
        "SELECT 1 FROM project WHERE id = ? AND account_id = ?", (project, account["id"])
    ).fetchone():
        return JSONResponse({"error": "not_found"}, 404)
    current = clock.monday(clock.now(), account["timezone"])
    state = "past" if week < current else "current" if week == current else "planning"
    if state == "past":
        r = con.execute(
            "SELECT tasks FROM snapshot WHERE account_id = ? AND week = ?", (account["id"], week)
        ).fetchone()
        tasks = [t for t in json.loads(r["tasks"]) if t["project_id"] == project] if r else []
    else:
        rows = con.execute(
            "SELECT * FROM task WHERE account_id = ? AND project_id = ? AND week = ?"
            " ORDER BY position",
            (account["id"], project, week),
        ).fetchall()
        tasks = [task_json(con, t) for t in rows]
    notes = con.execute(
        "SELECT html, rev FROM week_notes WHERE account_id = ? AND project_id = ? AND week = ?",
        (account["id"], project, week),
    ).fetchone()
    return {
        "week": week,
        "state": state,
        "tasks": tasks,
        "notes": dict(notes) if notes else {"html": "", "rev": 0},
    }


def event_json(e):
    return {
        "id": e["id"], "project_id": e["project_id"], "title": e["title"],
        "start": e["start"], "end": e["end"], "all_day": bool(e["all_day"]),
        "repeat": e["repeat"], "until": e["until"], "location": e["location"],
        "description": e["description"], "fills_day": bool(e["fills_day"]),
        "skipped": json.loads(e["skipped"]), "rev": e["rev"],
    }


@routes.get("/agenda")
def agenda(week: str, account: Account, con: Con):
    if not clock.is_monday(week):
        return JSONResponse({"error": "invalid", "fields": ["week"]}, 422)
    rollover.apply(con, account["id"])
    end = clock.add_days(week, 7)
    # Candidate series; the exact cut is done by the client (occurrences).
    events = con.execute(
        "SELECT * FROM event WHERE account_id = ? AND start < ?"
        " AND (\"end\" > ? OR (repeat <> 'none' AND (until IS NULL OR until >= ?)))"
        " ORDER BY start, id",
        (account["id"], end + "T00:00", week + "T00:00", clock.add_days(week, -31)),
    ).fetchall()
    current = clock.monday(clock.now(), account["timezone"])
    dues = con.execute(
        "SELECT id AS task_id, project_id, week, title, due, progress, important"
        " FROM task WHERE account_id = ? AND ((due >= ? AND due < ?)"
        " OR (? AND progress < 100 AND due < ?)) ORDER BY due, id",
        (account["id"], week, end, week == current, week),
    ).fetchall()
    return {
        "week": week,
        "events": [event_json(e) for e in events],
        "dues": [{**d, "important": bool(d["important"])} for d in map(dict, dues)],
    }


@routes.get("/search")
def search(account: Account, con: Con):
    """Account search index (003 R1): ranking runs on the client, online and offline."""
    subs = {}
    for s in con.execute(
        "SELECT task_id, text FROM subtask WHERE account_id = ? ORDER BY created_at, rowid",
        (account["id"],),
    ):
        subs.setdefault(s["task_id"], []).append(s["text"])
    tasks = con.execute(
        "SELECT id, project_id, week, title, notes, progress, important, due,"
        " updated_at FROM task WHERE account_id = ?",
        (account["id"],),
    ).fetchall()
    notes = con.execute(
        "SELECT project_id, week, html FROM week_notes WHERE account_id = ? AND html <> ''",
        (account["id"],),
    ).fetchall()
    events = con.execute("SELECT * FROM event WHERE account_id = ?", (account["id"],)).fetchall()
    return {
        "tasks": [{**t, "important": bool(t["important"]), "subtasks": subs.get(t["id"], [])}
                  for t in map(dict, tasks)],
        "notes": [dict(n) for n in notes],
        "events": [{k: v for k, v in event_json(e).items() if k != "rev"} for e in events],
    }
