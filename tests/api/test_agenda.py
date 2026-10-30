"""GET /api/agenda (feature 002): candidate series and the week's due dates."""
import os
import sqlite3
import uuid

import pytest

WEEK = "2026-10-26"


def uid():
    return str(uuid.uuid4())


@pytest.fixture
def account(app_client, new_account, clock):
    start = new_account(app_client, "a@x.com")
    c, aid = app_client, start["account"]["id"]
    personal, work = (p["id"] for p in start["projects"])

    class Account:
        client = c

        def ops(self, *items):
            r = c.post("/api/ops", json={"account_id": aid, "ops": list(items)})
            assert r.status_code == 200, r.text
            return r.json()["results"]

        def agenda(self, week=WEEK):
            return c.get(f"/api/agenda?week={week}").json()

        def event(self, start, end, repeat="none", until=None):
            i = uid()
            r = self.ops({"op": "event.save", "id": i, "project_id": None,
                          "title": i, "start": start, "end": end, "all_day": False,
                          "repeat": repeat, "until": until, "location": "", "description": "",
                          "base_rev": 0})
            assert r[0]["status"] == "ok", r
            return i

        def task(self, due, progress=0, project=personal, week=WEEK):
            i = uid()
            self.ops({"op": "task.create", "id": i, "project_id": project, "week": week},
                     {"op": "task.due", "id": i, "value": due},
                     {"op": "task.progress", "id": i, "value": progress})
            return i

    Account.personal, Account.work = personal, work
    return Account()


def test_candidate_series(account):
    inside = account.event("2026-10-28T09:00", "2026-10-28T10:00")
    crosses = account.event("2026-10-25T22:00", "2026-10-26T01:00")
    series = account.event("2026-08-04T09:00", "2026-08-04T10:00", "weekly", "2026-12-15")
    account.event("2026-09-10T09:00", "2026-09-10T10:00")
    account.event("2026-07-07T09:00", "2026-07-07T10:00", "weekly", "2026-09-01")
    account.event("2026-11-02T09:00", "2026-11-02T10:00")
    endless = account.event("2025-10-28T09:00", "2025-10-28T10:00", "daily")
    ids = {x["id"] for x in account.agenda()["events"]}
    assert ids == {inside, crosses, series, endless}


def test_invalid_week(account):
    r = account.client.get("/api/agenda?week=2026-10-27")
    assert r.status_code == 422


def test_account_deletion_deletes_events(account):
    account.event("2026-10-28T09:00", "2026-10-28T10:00")
    r = account.client.request("DELETE", "/api/account", json={"password": "password123"})
    assert r.status_code == 204
    con = sqlite3.connect(os.environ["SEMANA_DB"])
    assert con.execute("SELECT count(*) FROM event").fetchone()[0] == 0
    con.close()


def test_dues(account):
    open_ = account.task("2026-10-28")
    done = account.task("2026-10-30", 100, account.work)
    late = account.task("2026-10-15")
    done_before = account.task("2026-10-15", 100)
    account.task("2026-11-05")
    dues = {d["task_id"]: d for d in account.agenda()["dues"]}
    assert set(dues) == {open_, done, late}
    assert dues[done]["project_id"] == account.work
    assert dues[open_]["week"] == WEEK
    assert dues[open_]["important"] is False
    # Past week: its due dates in any state, without adding late ones.
    assert {d["task_id"] for d in account.agenda("2026-10-12")["dues"]} == {late, done_before}
    assert account.agenda("2026-10-19")["dues"] == []
