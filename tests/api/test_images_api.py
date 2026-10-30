"""Note images (feature 008): PUT and GET /api/images/{id}."""
import base64
import uuid

import pytest

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def uid():
    return str(uuid.uuid4())


def upload(c, id, data=PNG, mime="image/png"):
    return c.put(f"/api/images/{id}", content=data, headers={"Content-Type": mime})


def test_round_trip(app_client, new_account):
    c = app_client
    new_account(c, "a@x.com")
    i = uid()
    assert upload(c, i).status_code == 201
    assert upload(c, i).status_code == 200  # repeating changes nothing
    r = c.get(f"/api/images/{i}")
    assert r.status_code == 200 and r.content == PNG
    assert r.headers["content-type"] == "image/png" and "private" in r.headers["cache-control"]
    assert c.get(f"/api/images/{uid()}").status_code == 404


@pytest.mark.parametrize(("id", "data", "mime"), [
    ("not-a-uuid", PNG, "image/png"),
    (None, PNG, "image/svg+xml"),
    (None, PNG, "image/jpeg"),  # PNG bytes declared as JPEG
    (None, b"<html>hi</html>", "image/png"),
])
def test_invalid(app_client, new_account, id, data, mime):
    c = app_client
    new_account(c, "a@x.com")
    assert upload(c, id or uid(), data, mime).status_code == 422


def test_limits(app_client, new_account, monkeypatch):
    c = app_client
    new_account(c, "a@x.com")
    monkeypatch.setattr("semana.images.MAX_IMAGE", 100)
    r = upload(c, uid(), PNG + b"\0" * 100)
    assert r.status_code == 413 and r.json() == {"error": "too_large"}
    monkeypatch.setattr("semana.images.QUOTA", len(PNG) * 2)
    assert upload(c, uid()).status_code == 201
    assert upload(c, uid()).status_code == 201
    r = upload(c, uid())
    assert r.status_code == 413 and r.json() == {"error": "quota"}


def test_no_session(app_client):
    assert upload(app_client, uid()).status_code == 401
    assert app_client.get(f"/api/images/{uid()}").status_code == 401


def test_account_deletion_deletes(app_client, new_account):
    import os
    import sqlite3
    c = app_client
    new_account(c, "a@x.com")
    upload(c, uid())
    assert c.request("DELETE", "/api/account", json={"password": "password123"}).status_code == 204
    with sqlite3.connect(os.environ["SEMANA_DB"]) as con:
        assert con.execute("SELECT count(*) FROM image").fetchone()[0] == 0


def test_backup_carries_images(app_client, new_account):
    c = app_client
    aid = new_account(c, "a@x.com")["account"]["id"]
    i, t = uid(), uid()
    upload(c, i)
    project = c.get("/api/start").json()["projects"][0]["id"]
    r = c.post("/api/ops", json={"account_id": aid, "ops": [
        {"op": "task.create", "id": t, "project_id": project, "week": "2026-11-02"},
        {"op": "task.notes", "id": t, "base_rev": 0,
         "value": f'<p>before<img src="/api/images/{i}" width="320">after</p>'}]})
    assert all(x["status"] == "ok" for x in r.json()["results"])
    b = c.get("/api/backup").json()
    assert [(x["id"], x["mime"]) for x in b["images"]] == [(i, "image/png")]
    assert c.post("/api/backup", json=b).json() == {"status": "ok"}
    after = c.get("/api/backup").json()
    new = after["images"][0]["id"]
    assert new != i
    assert after["tasks"][0]["notes"] == (
        f'<p>before<img src="/api/images/{new}" width="320">after</p>')
    assert c.get(f"/api/images/{new}").content == PNG
    assert c.get(f"/api/images/{i}").status_code == 404
