import os
import sqlite3
import threading
import uuid

import pytest


def uid():
    return str(uuid.uuid4())


@pytest.fixture
def account(app_client, new_account, clock):
    clock.set("2026-10-20T12:00:00Z")
    start = new_account(app_client, "a@x.com")
    c, aid, project = app_client, start["account"]["id"], start["projects"][0]["id"]

    class Account:
        client = c

        def ops(self, *items):
            r = c.post("/api/ops", json={"account_id": aid, "ops": list(items)})
            return r.json()["results"]

        def week(self, monday):
            return c.get(f"/api/week?project={project}&week={monday}").json()

        def create(self, monday, progress=0):
            i = uid()
            self.ops({"op": "task.create", "id": i, "project_id": project, "week": monday},
                     {"op": "task.title", "id": i, "value": f"t{progress}", "base_rev": 0},
                     {"op": "task.progress", "id": i, "value": progress})
            return i

    Account.id, Account.project, Account.clock = aid, project, clock
    return Account()


def count(table):
    con = sqlite3.connect(os.environ["SEMANA_DB"])
    n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    con.close()
    return n


def by_id(tasks):
    return {t["id"]: t for t in tasks}


def test_carry_over(account, clock):
    tsub = account.create("2026-10-19")
    account.ops({"op": "subtask.create", "id": uid(), "task_id": tsub, "text": "s"},
                {"op": "task.notes", "id": tsub, "value": "<p>n</p>", "base_rev": 0})
    clock.set("2026-10-27T12:00:00Z")
    t0 = account.create("2026-10-26")
    t40 = account.create("2026-10-26", 40)
    timp = account.create("2026-10-26")
    account.ops({"op": "task.important", "id": timp, "value": True})
    done = account.create("2026-10-26", 100)
    plan = account.create("2026-11-02")
    before = by_id(account.week("2026-10-26")["tasks"])
    assert [t["id"] for t in before.values()] == [tsub, t0, t40, timp, done]
    assert before[tsub]["log"][0]["text"] == "Carried over from the week of 2026-10-19"

    clock.set("2026-11-02T02:59:00Z")  # Sunday 23:59 in São Paulo
    assert account.client.get("/api/start").json()["current_week"] == "2026-10-26"
    assert account.week("2026-10-26")["state"] == "current"
    assert count("snapshot") == 1  # only the one for the week of 10/19

    clock.set("2026-11-02T03:00:00Z")  # Monday 00:00 in São Paulo
    new = account.week("2026-11-02")
    assert new["state"] == "current"
    assert [t["id"] for t in new["tasks"]] == [tsub, t0, t40, timp, plan]
    assert [t["position"] for t in new["tasks"]] == [1, 2, 3, 4, 5]
    after = by_id(new["tasks"])
    for i in (tsub, t0, t40, timp):
        a, d = before[i], after[i]
        assert d["log"][-1]["text"] == "Carried over from the week of 2026-10-26"
        assert d["log"][-1]["kind"] == "system"
        assert d["weeks_open"] == a["weeks_open"] + 1
        changed = {"week", "position", "weeks_open", "log"}
        assert {k: v for k, v in d.items() if k not in changed} == {
            k: v for k, v in a.items() if k not in changed}
    assert [after[i]["weeks_open"] for i in (t0, t40, timp, tsub)] == [2, 2, 2, 3]
    assert after[timp]["important"] and after[tsub]["subtasks"][0]["text"] == "s"
    assert after[plan]["weeks_open"] == 1

    old = account.week("2026-10-26")
    assert old["state"] == "past"
    assert [t["id"] for t in old["tasks"]] == [tsub, t0, t40, timp, done]
    assert old["tasks"][1] == before[t0]

    # (f) deleting after the rollover does not change the snapshot
    account.ops({"op": "task.delete", "id": t0})
    assert account.week("2026-10-26") == old
    # (h) a late create goes to the current week
    late = account.create("2026-10-26")
    assert account.week("2026-11-02")["tasks"][-1]["id"] == late
    assert account.week("2026-11-09")["state"] == "planning"


def test_due_kept(account, clock):
    clock.set("2026-10-27T12:00:00Z")
    t = account.create("2026-10-26")
    account.ops({"op": "task.due", "id": t, "value": "2026-11-20"})
    clock.set("2026-11-02T12:00:00Z")
    assert account.week("2026-11-02")["tasks"][0]["due"] == "2026-11-20"
    assert account.week("2026-10-26")["tasks"][0]["due"] == "2026-11-20"


@pytest.mark.parametrize("weeks", [2, 5])
def test_absence(account, clock, weeks):
    clock.set("2026-10-27T12:00:00Z")
    open_ = account.create("2026-10-26", 50)
    future = account.create("2026-12-28")
    clock.advance(weeks=weeks)
    account.client.post("/api/login", json={"email": "a@x.com", "password": "password123"})
    end = account.client.get("/api/start").json()["current_week"]
    t = by_id(account.week(end)["tasks"])[open_]
    assert t["weeks_open"] == 1 + weeks
    assert len(t["log"]) == weeks
    assert count("snapshot") == weeks  # one per week with tasks
    assert count("log_entry") == weeks
    assert [x["id"] for x in account.week("2026-12-28")["tasks"]] == [future]


def test_idempotency(account, clock, app_client):
    clock.set("2026-10-27T12:00:00Z")
    account.create("2026-10-26")
    clock.advance(weeks=3)
    clients = []
    for _ in range(4):
        c = app_client.new()
        assert c.post("/api/login", json={"email": "a@x.com", "password": "password123"}).is_success
        clients.append(c)
    barrier = threading.Barrier(len(clients))
    errors = []

    def call(c):
        barrier.wait()
        r = c.get("/api/start")
        if r.status_code != 200:
            errors.append(r.text)

    threads = [threading.Thread(target=call, args=(c,)) for c in clients]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    account.client.get("/api/start")
    account.client.get("/api/start")
    assert count("snapshot") == 3 and count("log_entry") == 3
