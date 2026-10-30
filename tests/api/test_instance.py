"""Instance configuration: customization folder, legal page language and source link (AGPL §13)."""


def test_instance_legal_texts(app_client, tmp_path, monkeypatch):
    default = app_client.get("/terms").text
    assert "[" in default  # the repository template has placeholders to fill in
    (tmp_path / "terms.html").write_text("<p>My instance terms</p>")
    (tmp_path / "terms.pt-BR.html").write_text("<p>Termos da minha instância</p>")
    monkeypatch.setenv("SEMANA_CUSTOM_DIR", str(tmp_path))
    assert app_client.get("/terms").text == "<p>My instance terms</p>"
    assert app_client.get("/terms?lang=pt-BR").text == "<p>Termos da minha instância</p>"
    assert app_client.get("/privacy").status_code == 200  # no own file: the template


def test_legal_page_language(app_client):
    def lang(url, accept=None):
        r = app_client.get(url, headers={"Accept-Language": accept} if accept else {})
        assert r.status_code == 200
        return r.text.split('lang="')[1].split('"')[0]

    for page in ("/terms", "/privacy"):
        assert lang(page) == "en"
        assert lang(page, "pt-BR,pt;q=0.9,en;q=0.8") == "pt-BR"
        assert lang(page, "pt") == "pt-BR"
        assert lang(page, "en-US,en;q=0.9,pt-BR;q=0.8") == "en"
        assert lang(page, "en;q=0.5,pt-PT;q=0.7") == "pt-BR"
        assert lang(page + "?lang=pt-BR", "en") == "pt-BR"
        assert lang(page + "?lang=en", "pt-BR") == "en"
    assert "Accept-Language" in app_client.get("/terms").headers["vary"]
    assert app_client.get("/password").status_code == 200


def test_source_url(app_client, new_account, monkeypatch):
    assert new_account(app_client, "a@x.com")["source_url"] is None
    monkeypatch.setenv("SEMANA_SOURCE_URL", "https://github.com/example/semana")
    assert app_client.get("/api/start").json()["source_url"] == "https://github.com/example/semana"
