import os
import sqlite3

import pytest

from semana import mail

PASSWORD = "password123"


def signup(c, email="a@x.com", password=PASSWORD, timezone="America/Sao_Paulo"):
    return c.post("/api/account", json={"email": email, "password": password, "timezone": timezone})


def login(c, email="a@x.com", password=PASSWORD):
    return c.post("/api/login", json={"email": email, "password": password})


def test_signup(app_client, clock):
    r = signup(app_client)
    assert r.status_code == 201
    assert r.json()["account"]["email"] == "a@x.com"
    assert r.json()["account"]["language"] == "auto"
    start = app_client.get("/api/start").json()
    assert [p["name"] for p in start["projects"]] == ["Personal", "Work"]
    assert start["current_week"] == "2026-10-26"
    assert start["now"] == "2026-10-27T12:00:00Z"
    assert signup(app_client.new(), "A@x.com").json() == {"error": "email_taken"}
    assert signup(app_client.new(), "A@x.com").status_code == 409
    r = signup(app_client.new(), "b@x.com", password="1234567")
    assert r.status_code == 422 and r.json() == {"error": "invalid", "fields": ["password"]}
    r = signup(app_client.new(), "b@x.com", timezone="Mars/Base")
    assert r.status_code == 422 and r.json()["fields"] == ["timezone"]


def test_content_type_and_headers(app_client):
    r = app_client.post("/api/account", content="{}", headers={"content-type": "text/plain"})
    assert r.status_code == 415 and r.json() == {"error": "bad_content_type"}
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert app_client.get("/api/start").json() == {"error": "no_session"}


def test_login_and_logout(app_client, clock):
    signup(app_client)
    other = app_client.new()
    assert login(other, password="wrong123").json() == {"error": "credentials"}
    r = login(other, "A@X.com")
    assert r.status_code == 200 and r.json()["account"]["email"] == "a@x.com"
    assert other.get("/api/start").status_code == 200
    assert other.post("/api/logout", json={}).status_code == 204
    assert other.get("/api/start").status_code == 401
    assert app_client.get("/api/start").status_code == 200


def test_session_expires(app_client, clock):
    signup(app_client)
    for _ in range(3):
        clock.advance(days=29)
        assert app_client.get("/api/start").status_code == 200
    clock.advance(days=31)
    assert app_client.get("/api/start").status_code == 401


def test_lock_by_email(app_client, clock):
    signup(app_client)
    c = app_client.new()
    for _ in range(5):
        assert login(c, password="wrong123").status_code == 401
    r = login(c)
    assert r.status_code == 429
    assert r.json() == {"error": "locked", "retry_at": "2026-10-27T12:15:00Z"}
    clock.advance(minutes=15, seconds=1)
    assert login(c).status_code == 200


def test_success_clears_failures(app_client, clock):
    signup(app_client)
    c = app_client.new()
    for _ in range(4):
        login(c, password="wrong123")
    assert login(c).status_code == 200
    for _ in range(4):
        assert login(c, password="wrong123").status_code == 401
    assert login(c).status_code == 200


def test_lock_by_ip(app_client, clock):
    c = app_client.new()
    for i in range(30):
        assert login(c, f"n{i}@x.com").status_code == 401
    assert login(c, "other@x.com").status_code == 429


@pytest.fixture
def sent(monkeypatch):
    out = []
    monkeypatch.setattr(mail, "send", lambda to, subject, text: out.append((subject, text)))
    return out


def test_recovery(app_client, clock, sent):
    signup(app_client)
    for email in ("a@x.com", "nobody@x.com"):
        r = app_client.post("/api/password/request", json={"email": email})
        assert r.status_code == 202 and r.content == b""
    assert len(sent) == 1
    token = sent[0][1].split("/password#")[1].split()[0]

    def reset(token, password="new-password"):
        return app_client.post("/api/password/reset", json={"token": token, "password": password})

    assert reset(token, "short").status_code == 422
    assert reset(token).status_code == 204
    assert app_client.get("/api/start").status_code == 401  # old sessions drop
    assert reset(token).json() == {"error": "invalid_token"}
    assert login(app_client, password="new-password").status_code == 200

    app_client.post("/api/password/request", json={"email": "a@x.com"})
    clock.advance(minutes=61)
    r = reset(sent[-1][1].split("/password#")[1].split()[0])
    assert r.status_code == 400


def test_reset_mail_language(app_client, new_account, sent):
    c = app_client
    aid = new_account(c, "a@x.com")["account"]["id"]

    def request(**extra):
        assert c.post("/api/password/request", json={"email": "a@x.com", **extra}).status_code == 202
        return sent[-1][0]

    assert request() == "Reset your Semana password"
    assert request(language="pt-BR") == "Redefinir sua senha do Semana"
    assert c.post("/api/password/request",
                  json={"email": "a@x.com", "language": "fr"}).status_code == 422
    c.post("/api/ops", json={"account_id": aid, "ops": [{"op": "account.language", "value": "en"}]})
    assert request(language="pt-BR") == "Reset your Semana password"  # the account wins
    c.post("/api/ops", json={"account_id": aid,
                             "ops": [{"op": "account.language", "value": "pt-BR"}]})
    assert request() == "Redefinir sua senha do Semana"
    assert "Para criar uma nova senha" in sent[-1][1]


def test_delete_account(app_client, clock):
    a = app_client
    assert signup(a).status_code == 201
    start = a.get("/api/start")
    account_id = start.json()["account"]["id"]
    project = start.json()["projects"][0]["id"]
    task = "00000000-0000-4000-8000-000000000001"
    a.post("/api/ops", json={"account_id": account_id, "ops": [
        {"op": "task.create", "id": task, "project_id": project, "week": "2026-10-26"},
        {"op": "subtask.create", "id": "00000000-0000-4000-8000-000000000002",
         "task_id": task, "text": "x"},
        {"op": "week.notes", "project_id": project, "week": "2026-10-26",
         "value": "<p>n</p>", "base_rev": 0},
    ]})
    clock.advance(days=7)
    a.get("/api/start")  # creates the snapshot and log entry
    a.post("/api/password/request", json={"email": "a@x.com"})

    def delete(password):
        return a.request("DELETE", "/api/account", json={"password": password})

    assert delete("wrong123").json() == {"error": "wrong_password"}
    assert delete("wrong123").status_code == 403
    assert delete(PASSWORD).status_code == 204
    assert a.get("/api/start").status_code == 401

    con = sqlite3.connect(os.environ["SEMANA_DB"])
    tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    assert "snapshot" in tables
    for t in tables:
        columns = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
        column = "account_id" if "account_id" in columns else "id" if t == "account" else None
        if column:
            n = con.execute(f"SELECT count(*) FROM {t} WHERE {column} = ?", (account_id,)).fetchone()
            assert n[0] == 0, t
    con.close()
    assert signup(a).status_code == 201


def test_default_projects_in_signup_language(app_client):
    def projects(email, **extra):
        c = app_client.new()
        r = c.post("/api/account", json={"email": email, "password": "password123",
                                         "timezone": "America/Sao_Paulo", **extra})
        assert r.status_code == 201, r.text
        return [p["name"] for p in c.get("/api/start").json()["projects"]]
    assert projects("en@x.com") == ["Personal", "Work"]
    assert projects("pt@x.com", language="pt-BR") == ["Pessoal", "Trabalho"]
