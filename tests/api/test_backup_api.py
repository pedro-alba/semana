"""Account backup (feature 005): GET and POST /api/backup."""
import copy
import uuid

import pytest
from fastapi.testclient import TestClient

WEEK = "2026-10-26"


def uid():
    return str(uuid.uuid4())


def ops(c, aid, *items):
    r = c.post("/api/ops", json={"account_id": aid, "ops": list(items)}).json()["results"]
    assert all(x["status"] == "ok" for x in r), r


def populate(c, clock, new_account):
    start = new_account(c, "a@x.com")
    aid = start["account"]["id"]
    personal, work = (p["id"] for p in start["projects"])
    t1, t2, t3 = uid(), uid(), uid()
    ops(c, aid,
        {"op": "task.create", "id": t1, "project_id": personal, "week": WEEK},
        {"op": "task.title", "id": t1, "value": "Meeting", "base_rev": 0},
        {"op": "task.notes", "id": t1, "value": "<p><strong>agenda</strong></p>", "base_rev": 0},
        {"op": "task.due", "id": t1, "value": "2026-10-30"},
        {"op": "task.important", "id": t1, "value": True},
        {"op": "task.progress", "id": t1, "value": 40},
        {"op": "subtask.create", "id": uid(), "task_id": t1, "text": "Send agenda"},
        {"op": "task.create", "id": t2, "project_id": personal, "week": WEEK},
        {"op": "task.title", "id": t2, "value": "Done", "base_rev": 0},
        {"op": "task.progress", "id": t2, "value": 100},
        {"op": "task.create", "id": t3, "project_id": work, "week": "2026-11-09"},
        {"op": "week.notes", "project_id": personal, "week": WEEK,
         "value": "<p>ideas</p>", "base_rev": 0},
        {"op": "event.save", "id": uid(), "project_id": work, "title": "Class",
         "start": "2026-10-27T09:00", "end": "2026-10-27T10:00", "all_day": False,
         "repeat": "weekly", "until": "2027-01-01", "location": "", "description": "",
         "skipped": ["2026-11-03"], "base_rev": 0},
    )
    clock.advance(days=7)  # the rollover creates the 10/26 snapshot and carries the Meeting
    return aid, t1


def without_ids(b):
    """Replaces each ID by its order of appearance, to compare files from different imports."""
    b = copy.deepcopy(b)
    b.pop("exported_at")
    seen = {}

    def swap(x):
        if isinstance(x, dict):
            # positions are renumbered on import; the relative order is the list order
            return {k: (seen.setdefault(v, len(seen)) if k in ("id", "project_id") and v
                        else swap(v)) for k, v in x.items() if k != "position"}
        if isinstance(x, list):
            return [swap(v) for v in x]
        return x
    for p in b["projects"]:
        p.pop("created_at")
    return swap(b)


def test_round_trip(app_client, clock, new_account):
    c = app_client
    aid, t1 = populate(c, clock, new_account)
    b = c.get("/api/backup").json()
    assert (b["format"], b["version"]) == ("semana-backup", 1)
    assert len(b["projects"]) == 2 and len(b["tasks"]) == 3 and len(b["events"]) == 1
    assert b["notes"] == [{"project_id": b["projects"][0]["id"], "week": WEEK,
                           "html": "<p>ideas</p>"}]
    assert [s["week"] for s in b["snapshots"]] == [WEEK]
    assert b["events"][0]["skipped"] == ["2026-11-03"]
    meeting = next(t for t in b["tasks"] if t["title"] == "Meeting")
    assert meeting["week"] == "2026-11-02" and meeting["weeks_open"] == 2
    assert meeting["subtasks"][0]["text"] == "Send agenda" and meeting["log"]

    ops(c, aid, {"op": "task.delete", "id": t1})
    assert c.post("/api/backup", json=b).json() == {"status": "ok"}
    after = c.get("/api/backup").json()
    assert without_ids(after) == without_ids(b)
    assert {t["id"] for t in after["tasks"]}.isdisjoint({t["id"] for t in b["tasks"]})


def test_no_session(app_client):
    assert app_client.get("/api/backup").status_code == 401
    assert app_client.post("/api/backup", json={}).status_code == 401


def test_empty_account(app_client, new_account):
    c = app_client
    new_account(c, "a@x.com")
    b = c.get("/api/backup").json()
    assert [p["name"] for p in b["projects"]] == ["Personal", "Work"]
    assert b["tasks"] == b["notes"] == b["events"] == b["snapshots"] == []
    assert c.post("/api/backup", json=b).json() == {"status": "ok"}


def task(**k):
    return {"id": "t", "project_id": "p", "week": WEEK, "title": "", "notes": "",
            "important": False, "progress": 0, "position": 0, "weeks_open": 1,
            "due": None, "created_at": "2026-10-27T10:00:00Z",
            "updated_at": "2026-10-27T10:00:00Z", "subtasks": [], "log": [], **k}


def backup_file(**k):
    return {"format": "semana-backup", "version": 1, "processed_week": "2026-10-19",
            "projects": [{"id": "p", "name": "Personal"}], "tasks": [], "notes": [],
            "events": [], "snapshots": [], **k}


@pytest.mark.parametrize("bad", [
    {"format": "other"},
    {"version": 2},
    {"projects": []},
    {"tasks": [task(project_id="x")]},
    {"tasks": [task(title="a" * 501)]},
    {"tasks": [task(), task()]},
    {"tasks": [task(week="2026-10-27")]},
])
def test_invalid(app_client, clock, new_account, bad):
    c = app_client
    populate(c, clock, new_account)
    before = c.get("/api/backup").json()
    r = c.post("/api/backup", json=backup_file(**bad))
    assert r.status_code == 422 and r.json()["error"] == "invalid"
    assert without_ids(c.get("/api/backup").json()) == without_ids(before)


def test_all_or_nothing(app_client, clock, new_account, monkeypatch):
    c = app_client
    populate(c, clock, new_account)
    before = c.get("/api/backup").json()
    calls = []

    def fail(html):
        calls.append(html)
        if len(calls) == 2:
            raise RuntimeError("crash halfway")
        return html
    monkeypatch.setattr("semana.backup.clean", fail)
    no_raise = TestClient(c.app, raise_server_exceptions=False, cookies=c.cookies)
    assert no_raise.post("/api/backup", json=before).status_code == 500
    assert without_ids(c.get("/api/backup").json()) == without_ids(before)


def test_sanitize(app_client, clock, new_account):
    c = app_client
    new_account(c, "a@x.com")
    bad = '<p onclick="x()">hi<script>alert(1)</script></p>'
    r = c.post("/api/backup", json=backup_file(
        tasks=[task(notes=bad, week="2026-11-02")],
        notes=[{"project_id": "p", "week": WEEK, "html": bad}]))
    assert r.json() == {"status": "ok"}
    b = c.get("/api/backup").json()
    assert b["tasks"][0]["notes"] == b["notes"][0]["html"] == "<p>hi</p>"


def test_rollover_after(app_client, clock, new_account):
    c = app_client
    new_account(c, "a@x.com")
    old = "2026-10-05"
    r = c.post("/api/backup", json=backup_file(processed_week="2026-09-28",
                                               tasks=[task(week=old, title="Open")]))
    assert r.json() == {"status": "ok"}
    b = c.get("/api/backup").json()
    t = b["tasks"][0]
    assert t["week"] == WEEK and t["weeks_open"] == 4
    assert old in [s["week"] for s in b["snapshots"]]
