import uuid

import pytest

WEEK = "2026-10-26"


def ops(client, account_id, *items):
    r = client.post("/api/ops", json={"account_id": account_id, "ops": list(items)})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def week(client, project, monday=WEEK):
    r = client.get(f"/api/week?project={project}&week={monday}")
    assert r.status_code == 200, r.text
    return r.json()


def uid():
    return str(uuid.uuid4())


@pytest.fixture
def account(app_client, new_account, clock):
    start = new_account(app_client, "a@x.com")
    c = app_client
    aid, project = start["account"]["id"], start["projects"][0]["id"]

    class Account:
        client = c

        def ops(self, *items):
            return ops(c, aid, *items)

        def week(self, monday=WEEK, project=project):
            return week(c, project, monday)

        def tasks(self, monday=WEEK):
            return self.week(monday)["tasks"]

        def task(self, id):
            return next(t for t in self.tasks() if t["id"] == id)

        def create(self, n=1, monday=WEEK):
            ids = [uid() for _ in range(n)]
            r = self.ops(*({"op": "task.create", "id": i, "project_id": project,
                            "week": monday} for i in ids))
            assert all(x == {"status": "ok"} for x in r)
            return ids

    Account.id, Account.project, Account.clock = aid, project, clock
    return Account()


def ordered_ids(account):
    return [t["id"] for t in account.tasks()]


# --- US2 ---

def test_create(account):
    a, b = account.create(2)
    t = account.task(b)
    assert (t["position"], t["progress"], t["title"], t["weeks_open"]) == (2, 0, "", 1)
    before = account.tasks()
    assert account.ops({"op": "task.create", "id": a, "project_id": account.project,
                        "week": "2026-11-02"}) == [{"status": "ok"}]
    assert account.tasks() == before
    assert account.tasks("2026-11-02") == []


def test_create_in_closed_week_goes_to_current(account):
    (a,) = account.create(monday="2026-10-19")
    assert [t["id"] for t in account.tasks()] == [a]


def test_create_invalid_week(account):
    r = account.ops({"op": "task.create", "id": uid(), "project_id": account.project,
                     "week": "2026-10-27"})
    assert r == [{"status": "invalid", "fields": ["week"]}]


def test_progress_moves_between_groups(account):
    a, b, c = account.create(3)
    account.ops({"op": "task.progress", "id": a, "value": 100})
    assert ordered_ids(account) == [b, c, a]
    account.ops({"op": "task.progress", "id": b, "value": 100})
    assert ordered_ids(account) == [c, a, b]
    account.ops({"op": "task.progress", "id": a, "value": 60})
    assert ordered_ids(account) == [c, b, a]
    assert account.task(a)["progress"] == 60
    for v in (101, -1):
        assert account.ops({"op": "task.progress", "id": a, "value": v}) == [
            {"status": "invalid", "fields": ["value"]}]


def test_reorder(account):
    a, b, c, d = account.create(4)
    account.clock.advance(hours=1)
    account.ops({"op": "task.progress", "id": a, "value": 100})  # a goes to position 5
    before = {t["id"]: t["updated_at"] for t in account.tasks()}
    account.clock.advance(hours=1)
    r = account.ops({"op": "task.reorder", "project_id": account.project, "week": WEEK,
                     "ids": [d, uid(), b]})
    assert r == [{"status": "ok"}]
    assert ordered_ids(account) == [d, c, b, a]
    assert {t["id"]: t["updated_at"] for t in account.tasks()} == before


def test_important_and_progress_touch(account):
    (a,) = account.create()
    for op, value, hour in (("task.important", True, 13), ("task.progress", 30, 14)):
        account.clock.advance(hours=1)
        account.ops({"op": op, "id": a, "value": value})
        assert account.task(a)["updated_at"] == f"2026-10-27T{hour}:00:00Z"
    assert account.task(a)["important"] is True


def test_repeated_delete(account):
    (a,) = account.create()
    assert account.ops({"op": "task.delete", "id": a}, {"op": "task.delete", "id": a}) == [
        {"status": "ok"}, {"status": "ok"}]
    assert account.tasks() == []


def test_project(account):
    p = uid()
    assert account.ops({"op": "project.create", "id": p, "name": "  Home "}) == [{"status": "ok"}]
    assert account.ops({"op": "project.create", "id": p, "name": "Other"}) == [{"status": "ok"}]
    projects = account.client.get("/api/start").json()["projects"]
    assert [x["name"] for x in projects] == ["Personal", "Work", "Home"]
    for name in ("  ", "x" * 61):
        assert account.ops({"op": "project.create", "id": uid(), "name": name}) == [
            {"status": "invalid", "fields": ["name"]}]


def test_unknown_op_and_large_batch(account):
    assert account.ops({"op": "task.fly"}) == [{"status": "invalid", "fields": ["op"]}]
    r = account.client.post("/api/ops", json={"account_id": account.id, "ops": [{}] * 201})
    assert r.status_code == 422 and r.json() == {"error": "invalid", "fields": ["ops"]}


def test_batch_resend(account):
    t, s = uid(), uid()
    batch = [
        {"op": "task.create", "id": t, "project_id": account.project, "week": WEEK},
        {"op": "task.title", "id": t, "value": "A", "base_rev": 0},
        {"op": "task.progress", "id": t, "value": 100},
        {"op": "subtask.create", "id": s, "task_id": t, "text": "s"},
        {"op": "subtask.done", "id": s, "done": True},
        {"op": "task.progress", "id": t, "value": 40},
    ]
    first = account.ops(*batch)
    state = account.week()
    assert account.ops(*batch) == first
    assert account.week() == state


# --- US3: text with revision ---

def test_title_with_revision(account, app_client):
    (a,) = account.create()
    def title(v, rev):
        return account.ops({"op": "task.title", "id": a, "value": v, "base_rev": rev})[0]

    assert title(" Contract ", 0) == {"status": "ok", "rev": 1}
    assert account.task(a)["title"] == "Contract"
    assert title("Contract", 0) == {"status": "ok", "rev": 1}
    assert title("Other", 0) == {"status": "conflict", "value": "Contract", "rev": 1}
    assert title("Other", 1) == {"status": "ok", "rev": 2}
    assert title("x" * 501, 2) == {"status": "invalid", "fields": ["value"]}


def test_different_fields_do_not_conflict(account, app_client):
    (a,) = account.create()
    other = app_client.new()
    assert other.post("/api/login", json={"email": "a@x.com", "password": "password123"}).is_success
    r1 = account.ops({"op": "task.title", "id": a, "value": "T", "base_rev": 0})
    r2 = ops(other, account.id, {"op": "task.notes", "id": a, "value": "<p>N</p>",
                                 "base_rev": 0})
    assert r1 == r2 == [{"status": "ok", "rev": 1}]
    t = account.task(a)
    assert (t["title"], t["notes"]) == ("T", "<p>N</p>")


def test_notes_sanitized_and_limit(account):
    (a,) = account.create()
    r = account.ops({"op": "task.notes", "id": a, "base_rev": 0,
                     "value": '<p onclick="x()">hi<script>alert(1)</script></p>'})
    assert r == [{"status": "ok", "rev": 1}]
    assert account.task(a)["notes"] == "<p>hi</p>"
    r = account.ops({"op": "task.notes", "id": a, "base_rev": 1,
                     "value": "<p>" + "x" * 1_000_000 + "</p>"})
    assert r == [{"status": "invalid", "fields": ["value"]}]


def test_subtasks(account):
    (a,) = account.create()
    s = uid()
    create = {"op": "subtask.create", "id": s, "task_id": a, "text": " Call "}
    assert account.ops(create, create) == [{"status": "ok"}] * 2
    assert [x["text"] for x in account.task(a)["subtasks"]] == ["Call"]
    for empty in ("", "   "):
        assert account.ops({"op": "subtask.text", "id": s, "value": empty, "base_rev": 0}) == [
            {"status": "invalid", "fields": ["value"]}]
        assert account.ops({**create, "id": uid(), "text": empty}) == [
            {"status": "invalid", "fields": ["text"]}]
    assert account.ops({"op": "subtask.text", "id": s, "value": "Call now", "base_rev": 0}) == [
        {"status": "ok", "rev": 1}]

    account.clock.advance(hours=2)
    account.ops({"op": "subtask.done", "id": s, "done": True})
    t = account.task(a)
    assert t["subtasks"][0]["done_at"] == "2026-10-27T14:00:00Z"
    assert t["updated_at"] == "2026-10-27T14:00:00Z"
    account.clock.advance(hours=1)
    account.ops({"op": "subtask.done", "id": s, "done": False})
    t = account.task(a)
    assert t["subtasks"][0]["done_at"] is None
    assert t["updated_at"] == "2026-10-27T15:00:00Z"

    # undoing a delete: recreate with the original fields
    account.ops({"op": "subtask.delete", "id": s}, {"op": "subtask.delete", "id": s})
    assert account.task(a)["subtasks"] == []
    account.ops({**create, "text": "Call now", "created_at": "2026-10-27T12:00:00Z",
                 "done_at": "2026-10-27T14:00:00Z"})
    sub = account.task(a)["subtasks"][0]
    assert (sub["created_at"], sub["done_at"]) == ("2026-10-27T12:00:00Z",
                                                   "2026-10-27T14:00:00Z")


def test_delete_task_deletes_children(account):
    import os
    import sqlite3

    (a,) = account.create()
    account.ops({"op": "subtask.create", "id": uid(), "task_id": a, "text": "s"})
    account.clock.advance(days=7)
    account.client.get("/api/start")  # rollover writes a log entry
    assert account.tasks("2026-11-02")[0]["log"]
    account.ops({"op": "task.delete", "id": a})
    con = sqlite3.connect(os.environ["SEMANA_DB"])
    for table in ("subtask", "log_entry"):
        assert con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
    con.close()


# --- US6: week notes ---

def write_notes(account, value, rev, monday=WEEK):
    return account.ops({"op": "week.notes", "project_id": account.project, "week": monday,
                        "value": value, "base_rev": rev})[0]


def test_week_notes(account):
    assert account.week()["notes"] == {"html": "", "rev": 0}
    assert write_notes(account, "<p>a</p>", 1) == {"status": "conflict", "value": "", "rev": 0}
    assert write_notes(account, "<p>a</p><script>x</script>", 0) == {"status": "ok", "rev": 1}
    assert account.week()["notes"] == {"html": "<p>a</p>", "rev": 1}
    assert write_notes(account, "<p>b</p>", 0) == {"status": "conflict", "value": "<p>a</p>",
                                                   "rev": 1}
    assert write_notes(account, "", 1) == {"status": "ok", "rev": 2}
    assert account.week()["notes"] == {"html": "", "rev": 2}
    assert write_notes(account, "<p>a</p>", 0, "2026-10-27") == {"status": "invalid",
                                                                 "fields": ["week"]}


def test_invalid_week_and_foreign_project(account):
    c = account.client
    r = c.get(f"/api/week?project={account.project}&week=2026-10-27")
    assert r.status_code == 422 and r.json() == {"error": "invalid", "fields": ["week"]}
    r = c.get(f"/api/week?project={uid()}&week={WEEK}")
    assert r.status_code == 404


# --- 002 US1: due date ---

def test_due(account):
    (t,) = account.create()
    before = account.task(t)
    assert before["due"] is None
    account.clock.advance(minutes=5)
    assert account.ops({"op": "task.due", "id": t, "value": "2026-11-06"}) == [{"status": "ok"}]
    after = account.task(t)
    assert after["due"] == "2026-11-06"
    assert after["updated_at"] > before["updated_at"]
    assert account.ops({"op": "task.due", "id": t, "value": "2026-11-06"}) == [{"status": "ok"}]
    assert account.task(t)["due"] == "2026-11-06"
    for bad in ("2026-13-01", "tomorrow"):
        assert account.ops({"op": "task.due", "id": t, "value": bad})[0]["status"] == "invalid"
    assert account.ops({"op": "task.due", "id": t, "value": None}) == [{"status": "ok"}]
    assert account.task(t)["due"] is None


# --- 002 US2: events ---

def event(**fields):
    base = {"op": "event.save", "id": fields.pop("id", None) or uid(), "project_id": None,
            "title": "Meeting", "start": "2026-10-27T09:00", "end": "2026-10-27T10:00",
            "all_day": False, "repeat": "none", "until": None, "location": "",
            "description": "", "base_rev": 0}
    return {**base, **fields}


def test_event_create_update_conflict(account, app_client):
    e = event()
    assert account.ops(e) == [{"status": "ok", "rev": 1}]
    assert account.ops(e) == [{"status": "ok", "rev": 1}]
    agenda = account.client.get(f"/api/agenda?week={WEEK}").json()
    assert [x["id"] for x in agenda["events"]] == [e["id"]]
    assert account.ops({**e, "title": "Meeting 2", "base_rev": 1}) == [{"status": "ok", "rev": 2}]
    r = account.ops({**e, "title": "Other", "base_rev": 1})[0]
    assert r["status"] == "conflict" and r["rev"] == 2 and r["value"]["title"] == "Meeting 2"
    assert account.ops({"op": "event.delete", "id": e["id"]}) == [{"status": "ok"}]
    assert account.ops({"op": "event.delete", "id": e["id"]}) == [{"status": "ok"}]
    assert account.ops({**e, "base_rev": 2}) == [{"status": "conflict", "value": None, "rev": 0}]
    assert account.ops({**e, "base_rev": 0}) == [{"status": "ok", "rev": 1}]


@pytest.mark.parametrize("fields", [
    {"end": "2026-10-27T09:00"},
    {"end": "2026-11-28T09:01"},
    {"until": "2026-12-01"},
    {"repeat": "weekly", "until": "2026-10-26"},
    {"repeat": "daily", "until": "2026-10-26"},
    {"repeat": "yearly"},
    {"title": "  "},
    {"title": "x" * 161},
    {"location": "x" * 501},
    {"description": "x" * 10_001},
    {"start": "2026-10-27 09:00"},
])
def test_event_invalid(account, fields):
    assert account.ops(event(**fields))[0]["status"] == "invalid"


def test_event_skipped_and_fills_day(account, app_client):
    e = event(repeat="daily", fills_day=True, all_day=True,
              start="2026-10-27T00:00", end="2026-10-28T00:00",
              skipped=["2026-10-29", "2026-10-28", "2026-10-29"])
    assert account.ops(e)[0]["status"] == "ok"
    x = app_client.get("/api/agenda?week=2026-10-26").json()["events"][0]
    assert (x["fills_day"], x["skipped"]) == (True, ["2026-10-28", "2026-10-29"])
    many = [f"2027-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)] * 3
    assert account.ops(event(repeat="daily", skipped=many[:1001]))[0]["status"] == "invalid"


def test_event_unknown_project(account):
    assert account.ops(event(project_id=uid())) == [{"status": "not_found"}]
    assert account.ops(event(project_id=account.project))[0]["status"] == "ok"
