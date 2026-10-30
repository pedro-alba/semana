"""Account settings: `appearance` (feature 004) and `language`, with their ops."""

CHOICE = {"theme": "paper", "mode": "system", "font": "serif", "palette": "moss"}


def ops(c, aid, *items):
    return [x["status"] for x in c.post("/api/ops", json={"account_id": aid, "ops": list(items)})
            .json()["results"]]


def test_default_empty(app_client):
    c = app_client
    r = c.post("/api/account", json={"email": "a@x.com", "password": "password123",
                                     "timezone": "America/Sao_Paulo"})
    assert r.json()["account"]["appearance"] == {}
    assert c.get("/api/start").json()["account"]["appearance"] == {}
    other = c.new()
    r = other.post("/api/login", json={"email": "a@x.com", "password": "password123"})
    assert r.json()["account"]["appearance"] == {}


def test_saves(app_client, new_account):
    c = app_client
    aid = new_account(c, "a@x.com")["account"]["id"]
    op = {"op": "account.appearance", **CHOICE}
    assert ops(c, aid, op, op) == ["ok", "ok"]
    assert c.get("/api/start").json()["account"]["appearance"] == CHOICE
    other = c.new()
    r = other.post("/api/login", json={"email": "a@x.com", "password": "password123"})
    assert r.json()["account"]["appearance"] == CHOICE


def test_invalid(app_client, new_account):
    c = app_client
    aid = new_account(c, "a@x.com")["account"]["id"]
    r = c.post("/api/ops", json={"account_id": aid, "ops": [
        {"op": "account.appearance", **CHOICE, "theme": "blue"},
        {"op": "account.appearance", "theme": "paper", "mode": "dark", "font": "theme"},
    ]}).json()["results"]
    assert r == [{"status": "invalid", "fields": ["theme"]},
                 {"status": "invalid", "fields": ["palette"]}]
    assert c.get("/api/start").json()["account"]["appearance"] == {}


def test_language(app_client, new_account):
    c = app_client
    start = new_account(c, "a@x.com")
    aid = start["account"]["id"]
    assert start["account"]["language"] == "auto"
    for value in ("pt-BR", "en", "auto"):
        assert ops(c, aid, {"op": "account.language", "value": value}) == ["ok"]
        assert c.get("/api/start").json()["account"]["language"] == value
    assert ops(c, aid, {"op": "account.language", "value": "pt-BR"}) == ["ok"]
    r = c.new().post("/api/login", json={"email": "a@x.com", "password": "password123"})
    assert r.json()["account"]["language"] == "pt-BR"
    r = c.post("/api/ops", json={"account_id": aid, "ops": [
        {"op": "account.language", "value": "fr"}, {"op": "account.language"}]}).json()
    assert r["results"] == [{"status": "invalid", "fields": ["value"]}] * 2
    assert c.get("/api/start").json()["account"]["language"] == "pt-BR"
