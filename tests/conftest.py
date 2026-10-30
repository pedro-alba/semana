import socket
import threading
import time
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta

import pytest
import uvicorn
from fastapi.testclient import TestClient

from semana import clock as clock_module
from semana.app import create_app


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """TestClient over a fresh database. `app_client.new()` creates another client, with separate
    cookies, over the same app."""
    monkeypatch.setenv("SEMANA_DB", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("SEMANA_SECURE_COOKIE", "0")
    app = create_app()
    with ExitStack() as stack:
        def new():
            return stack.enter_context(TestClient(app))
        client = new()
        client.new = new
        yield client


class Clock:
    def __init__(self):
        self.instant = datetime(2026, 10, 27, 12, tzinfo=UTC)

    def set(self, iso):
        self.instant = datetime.fromisoformat(iso)

    def advance(self, **delta):
        self.instant += timedelta(**delta)


@pytest.fixture
def clock(monkeypatch):
    c = Clock()
    monkeypatch.setattr(clock_module, "now", lambda: c.instant)
    return c


@pytest.fixture
def new_account():
    def create(client, email, timezone="America/Sao_Paulo"):
        r = client.post("/api/account",
                        json={"email": email, "password": "password123", "timezone": timezone})
        assert r.status_code == 201, r.text
        return client.get("/api/start").json()
    return create


@pytest.fixture
def server(tmp_path, monkeypatch):
    """Real server on a free port, for browser tests. Returns the base URL."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("SEMANA_DB", str(tmp_path / "e2e.sqlite3"))
    monkeypatch.setenv("SEMANA_SECURE_COOKIE", "0")
    monkeypatch.setenv("SEMANA_BASE_URL", url)
    srv = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=port,
                                        log_level="warning"))
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not srv.started:
        assert thread.is_alive() and time.monotonic() < deadline, "server did not start"
        time.sleep(0.05)
    yield url
    srv.should_exit = True
    thread.join(5)
