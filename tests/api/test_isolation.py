"""Isolation between accounts (SC-005, FR-005). Every op in `semana.ops.OPS` needs a case."""
import pytest

from semana.ops import OPS

WEEK = "2026-10-26"
TASK = "00000000-0000-4000-8000-00000000000a"
SUB = "00000000-0000-4000-8000-00000000000b"
NEW = "00000000-0000-4000-8000-0000000000ff"
EVENT = "00000000-0000-4000-8000-00000000000c"

CASES = {
    "project.create": lambda a: {"id": a["project"], "name": "Stolen"},
    "task.create": lambda a: {"id": NEW, "project_id": a["project"], "week": WEEK},
    "task.progress": lambda a: {"id": TASK, "value": 100},
    "task.important": lambda a: {"id": TASK, "value": False},
    "task.reorder": lambda a: {"project_id": a["project"], "week": WEEK, "ids": [NEW, TASK]},
    "task.delete": lambda a: {"id": TASK},
    "task.title": lambda a: {"id": TASK, "value": "B was here", "base_rev": 1},
    "task.notes": lambda a: {"id": TASK, "value": "<p>B</p>", "base_rev": 1},
    "subtask.create": lambda a: {"id": NEW, "task_id": TASK, "text": "B"},
    "subtask.text": lambda a: {"id": SUB, "value": "B", "base_rev": 0},
    "subtask.done": lambda a: {"id": SUB, "done": True},
    "subtask.delete": lambda a: {"id": SUB},
    "task.due": lambda a: {"id": TASK, "value": "2026-12-01"},
    "event.save": lambda a: event(EVENT, None, 1),
    "event.delete": lambda a: {"id": EVENT},
    "account.appearance": lambda a: {"theme": "ink", "mode": "light", "font": "mono",
                                     "palette": "neutral"},
    "account.language": lambda a: {"value": "pt-BR"},
    "week.notes": lambda a: {"project_id": a["project"], "week": WEEK,
                             "value": "<p>B</p>", "base_rev": 1},
}

def event(id, project, base_rev):
    return {"id": id, "project_id": project, "title": "B", "start": "2026-10-27T09:00",
            "end": "2026-10-27T10:00", "all_day": False, "repeat": "none", "until": None,
            "location": "", "description": "", "base_rev": base_rev}


# Deletes answer `ok` even when nothing was deleted (R6), so the result does not tell
# "from another account" from "missing"; what matters is that A stays intact.
# Account settings only ever touch the caller's own account.
DELETES = {"task.delete", "subtask.delete", "event.delete", "account.appearance",
           "account.language"}


@pytest.fixture
def accounts(app_client, new_account, clock):
    a, b = app_client, app_client.new()
    ia = new_account(a, "a@x.com")
    ib = new_account(b, "b@x.com")
    project = ia["projects"][0]["id"]
    r = a.post("/api/ops", json={"account_id": ia["account"]["id"], "ops": [
        {"op": "task.create", "id": TASK, "project_id": project, "week": WEEK},
        {"op": "task.title", "id": TASK, "value": "From A", "base_rev": 0},
        {"op": "task.notes", "id": TASK, "value": "<p>A</p>", "base_rev": 0},
        {"op": "task.important", "id": TASK, "value": True},
        {"op": "subtask.create", "id": SUB, "task_id": TASK, "text": "A's sub"},
        {"op": "week.notes", "project_id": project, "week": WEEK,
         "value": "<p>A</p>", "base_rev": 0},
        {"op": "task.due", "id": TASK, "value": "2026-10-28"},
        {"op": "event.save", **event(EVENT, project, 0), "title": "From A"},
    ]})
    assert all(x["status"] == "ok" for x in r.json()["results"])
    return a, b, {"project": project, "account": ia["account"]["id"]}, ib


def week_of(client, project):
    return (client.get(f"/api/week?project={project}&week={WEEK}").json(),
            client.get(f"/api/agenda?week={WEEK}").json(),
            client.get("/api/start").json()["account"])


def test_get(accounts):
    _, b, data_a, ib = accounts
    r = b.get(f"/api/week?project={data_a['project']}&week={WEEK}")
    assert r.status_code == 404 and r.json() == {"error": "not_found"}
    ids_b = {p["id"] for p in ib["projects"]}
    assert {p["id"] for p in b.get("/api/start").json()["projects"]} == ids_b
    assert data_a["project"] not in ids_b


@pytest.mark.parametrize("name", sorted(OPS))
def test_operation(accounts, name, clock):
    a, b, data_a, ib = accounts
    if name not in CASES:
        pytest.fail(f"op without an isolation case: {name}")
    before = week_of(a, data_a["project"])
    clock.advance(minutes=5)
    r = b.post("/api/ops", json={"account_id": ib["account"]["id"],
                                 "ops": [{"op": name, **CASES[name](data_a)}]})
    status = r.json()["results"][0]["status"]
    assert status in ({"ok", "not_found"} if name in DELETES else {"not_found"})
    assert week_of(a, data_a["project"]) == before


def test_batch_from_other_account(accounts):
    a, b, data_a, _ = accounts
    r = b.post("/api/ops", json={"account_id": data_a["account"],
                                 "ops": [{"op": "task.delete", "id": TASK}]})
    assert r.status_code == 409 and r.json() == {"error": "wrong_account"}
    assert len(week_of(a, data_a["project"])[0]["tasks"]) == 1


def test_agenda_isolated(accounts):
    _, b, _, _ = accounts
    assert b.get(f"/api/agenda?week={WEEK}").json() == {"week": WEEK, "events": [], "dues": []}


def test_event_with_foreign_project(accounts):
    _, b, data_a, ib = accounts
    r = b.post("/api/ops", json={"account_id": ib["account"]["id"],
                                 "ops": [{"op": "event.save", **event(NEW, data_a["project"], 0)}]})
    assert r.json()["results"][0]["status"] == "not_found"


def test_search_isolated(accounts):
    _, b, _, _ = accounts
    assert b.get("/api/search").json() == {"tasks": [], "notes": [], "events": []}


def test_backup_isolated(accounts):
    a, b, _, _ = accounts
    from_a = a.get("/api/backup").json()
    assert b.post("/api/backup", json=from_a).json() == {"status": "ok"}
    assert a.get("/api/backup").json() | {"exported_at": ""} == from_a | {"exported_at": ""}
    from_b = b.get("/api/backup").json()
    assert [t["title"] for t in from_b["tasks"]] == [t["title"] for t in from_a["tasks"]]
    ids_a = {x["id"] for k in ("projects", "tasks", "events") for x in from_a[k]}
    ids_b = {x["id"] for k in ("projects", "tasks", "events") for x in from_b[k]}
    assert ids_a and ids_a.isdisjoint(ids_b)


def test_image_isolated(accounts):
    import base64
    import uuid
    a, b, _, _ = accounts
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    i = str(uuid.uuid4())
    h = {"Content-Type": "image/png"}
    assert a.put(f"/api/images/{i}", content=png, headers=h).status_code == 201
    assert b.get(f"/api/images/{i}").status_code == 404
    assert b.put(f"/api/images/{i}", content=png, headers=h).status_code == 404
    assert a.get(f"/api/images/{i}").content == png
