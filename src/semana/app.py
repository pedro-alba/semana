import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from semana import accounts, backup, images, ops, reads
from semana.db import connect, migrate

STATIC = Path(__file__).parent / "static"


def page(name):
    """File from the instance customization folder (SEMANA_CUSTOM_DIR), if any; else the app's."""
    folder = os.environ.get("SEMANA_CUSTOM_DIR")
    if folder and (Path(folder) / name).is_file():
        return Path(folder) / name
    return STATIC / name


def prefers_portuguese(request):
    """`?lang=` wins; without it, the highest-priority Accept-Language entry."""
    lang = request.query_params.get("lang")
    if lang is not None:
        return lang == "pt-BR"
    best, best_q = "", 0.0
    for item in request.headers.get("accept-language", "").split(","):
        tag, _, params = item.strip().partition(";")
        try:
            q = float(params.strip()[2:]) if params.strip().startswith("q=") else 1.0
        except ValueError:
            continue
        if q > best_q:
            best, best_q = tag.strip().lower(), q
    return best.startswith("pt")


def legal_page(request, name):
    file = f"{name}.pt-BR.html" if prefers_portuguese(request) else f"{name}.html"
    return FileResponse(page(file), headers={"Vary": "Accept-Language"})


HEADERS = {
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; font-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; "
    "frame-ancestors 'none'",
    "Referrer-Policy": "same-origin",
    "X-Content-Type-Options": "nosniff",
}


@asynccontextmanager
async def lifespan(app):
    con = connect()
    migrate(con)
    con.close()
    yield


def create_app():
    log = logging.getLogger("semana")
    if not log.handlers:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def protections(request: Request, call_next):
        mime = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if (request.method in ("POST", "DELETE") and request.url.path.startswith("/api")
                and mime != "application/json"):
            resp = JSONResponse({"error": "bad_content_type"}, 415)
        else:
            resp = await call_next(request)
        resp.headers.update(HEADERS)
        return resp

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        fields = [str(e["loc"][1] if len(e["loc"]) > 1 else e["loc"][0]) for e in exc.errors()]
        return JSONResponse({"error": "invalid", "fields": list(dict.fromkeys(fields))}, 422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        if isinstance(exc.detail, dict):
            return JSONResponse(exc.detail, exc.status_code)
        return await http_exception_handler(request, exc)

    for m in (accounts, reads, ops, backup, images):
        app.include_router(m.routes)

    @app.get("/password", include_in_schema=False)
    def password():
        return FileResponse(STATIC / "index.html")

    @app.get("/terms", include_in_schema=False)
    def terms(request: Request):
        return legal_page(request, "terms")

    @app.get("/privacy", include_in_schema=False)
    def privacy(request: Request):
        return legal_page(request, "privacy")

    @app.get("/sw.js", include_in_schema=False)
    def sw():
        return FileResponse(STATIC / "sw.js", headers={"Cache-Control": "no-cache"})

    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
    return app


app = create_app()
