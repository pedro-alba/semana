"""GET /api/search (feature 003): the account search index."""
import uuid

WEEK = "2026-10-26"


def uid():
    return str(uuid.uuid4())


def test_index(app_client, new_account, clock):
    c = app_client
    start = new_account(c, "a@x.com")
    aid = start["account"]["id"]
    personal, work = (p["id"] for p in start["projects"])
    t1, t2, s1, s2 = uid(), uid(), uid(), uid()
    r = c.post("/api/ops", json={"account_id": aid, "ops": [
        {"op": "task.create", "id": t1, "project_id": personal, "week": WEEK},
        {"op": "task.title", "id": t1, "value": "Meeting with Joana", "base_rev": 0},
        {"op": "task.notes", "id": t1, "value": "<p>budget</p>", "base_rev": 0},
        {"op": "task.due", "id": t1, "value": "2026-10-30"},
        {"op": "task.important", "id": t1, "value": True},
        {"op": "subtask.create", "id": s1, "task_id": t1, "text": "Send agenda"},
        {"op": "subtask.create", "id": s2, "task_id": t1, "text": "Done"},
        {"op": "subtask.done", "id": s2, "done": True},
        {"op": "task.create", "id": t2, "project_id": work, "week": "2026-11-09"},
        {"op": "week.notes", "project_id": personal, "week": WEEK,
         "value": "<p>ideas</p>", "base_rev": 0},
        {"op": "week.notes", "project_id": work, "week": WEEK,
         "value": "", "base_rev": 0},
    ]})
    assert all(x["status"] == "ok" for x in r.json()["results"])
    b = c.get("/api/search").json()
    tasks = {t["id"]: t for t in b["tasks"]}
    assert set(tasks) == {t1, t2}
    t = tasks[t1]
    assert (t["title"], t["notes"], t["due"], t["important"], t["progress"]) == (
        "Meeting with Joana", "<p>budget</p>", "2026-10-30", True, 0)
    assert sorted(t["subtasks"]) == ["Done", "Send agenda"]
    assert (t["week"], t["project_id"]) == (WEEK, personal) and t["updated_at"]
    assert tasks[t2]["project_id"] == work and tasks[t2]["subtasks"] == []
    assert b["notes"] == [{"project_id": personal, "week": WEEK, "html": "<p>ideas</p>"}]
    assert b["events"] == []
    e = uid()
    r = c.post("/api/ops", json={"account_id": aid, "ops": [
        {"op": "event.save", "id": e, "project_id": work, "title": "Class",
         "start": "2026-10-27T19:00", "end": "2026-10-27T20:00", "all_day": False,
         "repeat": "weekly", "until": None, "location": "School", "description": "english",
         "base_rev": 0}]})
    assert r.json()["results"][0]["status"] == "ok"
    assert c.get("/api/search").json()["events"] == [{
        "id": e, "project_id": work, "title": "Class", "start": "2026-10-27T19:00",
        "end": "2026-10-27T20:00", "all_day": False, "repeat": "weekly", "until": None,
        "location": "School", "description": "english", "fills_day": False, "skipped": []}]


def test_no_session(app_client):
    assert app_client.get("/api/search").status_code == 401
