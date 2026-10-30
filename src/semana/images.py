"""Note images (feature 008): binary in SQLite, only for the owning account (R1, R2)."""
import uuid

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from semana import clock
from semana.accounts import Account
from semana.db import Con, transaction

routes = APIRouter(prefix="/api")

MAX_IMAGE = 5 * 1024 * 1024
QUOTA = 500 * 1024 * 1024
SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),
}
NOT_FOUND = {"error": "not_found"}


def valid_mime(mime, data):
    """The declared type matches the first bytes (does not trust the header alone)."""
    if mime not in SIGNATURES or not data.startswith(SIGNATURES[mime]):
        return False
    return mime != "image/webp" or data[8:12] == b"WEBP"


def _uuid(s):
    try:
        return str(uuid.UUID(s)) == s
    except ValueError:
        return False


def store(con, account_id, id, mime, data):
    """Stores a new image; returns None or the error (status, body)."""
    if len(data) > MAX_IMAGE:
        return 413, {"error": "too_large"}
    used = con.execute(
        "SELECT COALESCE(SUM(size), 0) FROM image WHERE account_id = ?", (account_id,)
    ).fetchone()[0]
    if used + len(data) > QUOTA:
        return 413, {"error": "quota"}
    con.execute(
        "INSERT INTO image (id, account_id, mime, data, size, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (id, account_id, mime, data, len(data), clock.iso(clock.now())),
    )
    return None


@routes.put("/images/{id}")
async def upload(id: str, request: Request, account: Account, con: Con):
    mime = request.headers.get("content-type", "").split(";")[0].strip().lower()
    data = await request.body()
    if not _uuid(id) or not valid_mime(mime, data):
        return JSONResponse({"error": "invalid"}, 422)
    with transaction(con):
        owner = con.execute("SELECT account_id FROM image WHERE id = ?", (id,)).fetchone()
        if owner:
            return (JSONResponse({"status": "ok"}) if owner["account_id"] == account["id"]
                    else JSONResponse(NOT_FOUND, 404))
        error = store(con, account["id"], id, mime, data)
    if error:
        return JSONResponse(error[1], error[0])
    return JSONResponse({"status": "ok"}, 201)


@routes.get("/images/{id}")
def read(id: str, account: Account, con: Con):
    r = con.execute(
        "SELECT mime, data FROM image WHERE id = ? AND account_id = ?", (id, account["id"])
    ).fetchone()
    if not r:
        return JSONResponse(NOT_FOUND, 404)
    return Response(r["data"], media_type=r["mime"],
                    headers={"Cache-Control": "private, max-age=31536000, immutable"})
