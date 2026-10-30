import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta
from functools import cache
from typing import Annotated, Literal
from zoneinfo import available_timezones

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from semana import clock, mail
from semana.db import Con, transaction

COOKIE = "semana_session"
DURATION = timedelta(days=30)

routes = APIRouter(prefix="/api")


# --- password and session ---

def hash_password(s):
    n, r, p = 2**14, 8, 5
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(s.encode(), salt=salt, n=n, r=r, p=p, maxmem=64 * 1024 * 1024, dklen=32)
    b64 = base64.b64encode
    return f"scrypt${n}${r}${p}${b64(salt).decode()}${b64(h).decode()}"


def check_password(s, h):
    _, n, r, p, salt, expected = h.split("$")
    calc = hashlib.scrypt(
        s.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
        maxmem=64 * 1024 * 1024, dklen=32,
    )
    return hmac.compare_digest(calc, base64.b64decode(expected))


def _sha(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(con, account_id):
    token = secrets.token_urlsafe(32)
    now = clock.iso(clock.now())
    con.execute(
        "INSERT INTO session (token_hash, account_id, created_at, used_at) VALUES (?, ?, ?, ?)",
        (_sha(token), account_id, now, now),
    )
    return token


def set_cookie(resp, token):
    resp.set_cookie(
        COOKIE, token, max_age=int(DURATION.total_seconds()), path="/", httponly=True,
        samesite="lax", secure=os.environ.get("SEMANA_SECURE_COOKIE") != "0",
    )


def clear_cookie(resp):
    resp.delete_cookie(COOKIE, path="/")


def current_account(request: Request, con: Con):
    token = request.cookies.get(COOKIE)
    if token:
        now = clock.now()
        row = con.execute(
            "SELECT account.*, session.token_hash, session.used_at AS session_used_at"
            " FROM session JOIN account ON account.id = session.account_id"
            " WHERE session.token_hash = ? AND session.used_at > ?",
            (_sha(token), clock.iso(now - DURATION)),
        ).fetchone()
        if row:
            if row["session_used_at"] < clock.iso(now - timedelta(hours=1)):
                con.execute(
                    "UPDATE session SET used_at = ? WHERE token_hash = ?",
                    (clock.iso(now), row["token_hash"]),
                )
            return row
    raise HTTPException(401, {"error": "no_session"})


Account = Annotated[sqlite3.Row, Depends(current_account)]


def account_json(a):
    return {"id": a["id"], "email": a["email"], "timezone": a["timezone"],
            "appearance": json.loads(a["appearance"]), "language": a["language"]}


# --- bodies ---

@cache
def _timezones():
    return available_timezones()


class Email(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip()
        if "@" not in v or len(v) > 254:
            raise ValueError("invalid e-mail")
        return v


class Password(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        if len(v) < 8:
            raise ValueError("password too short")
        return v


class Signup(Email, Password):
    timezone: str
    language: Literal["en", "pt-BR"] = "en"  # language of the sign-up screen, for the default projects

    @field_validator("timezone")
    @classmethod
    def _timezone(cls, v):
        if v not in _timezones():
            raise ValueError("invalid time zone")
        return v


DEFAULT_PROJECTS = {"en": ("Personal", "Work"), "pt-BR": ("Pessoal", "Trabalho")}


class Login(BaseModel):
    email: str
    password: str


class ResetRequest(Email):
    language: Literal["en", "pt-BR"] | None = None


class Reset(Password):
    token: str


class CurrentPassword(BaseModel):
    password: str


# --- reset e-mail ---

RESET_MAIL = {
    "en": ("Reset your Semana password",
           ("To create a new password, open the link below. It is valid for 1 hour.\n\n"
            "{link}\n\nIf you did not ask for this, ignore this e-mail.")),
    "pt-BR": ("Redefinir sua senha do Semana",
              ("Para criar uma nova senha, abra o link abaixo. Ele vale por 1 hora.\n\n"
               "{link}\n\nSe você não pediu, ignore este e-mail.")),
}


# --- routes ---

@routes.post("/account", status_code=201)
def signup(body: Signup, response: Response, con: Con):
    now = clock.now()
    account_id = str(uuid.uuid4())
    password_hash = hash_password(body.password)
    with transaction(con):
        if con.execute("SELECT 1 FROM account WHERE email = ?", (body.email,)).fetchone():
            return JSONResponse({"error": "email_taken"}, 409)
        con.execute(
            "INSERT INTO account (id, email, password_hash, timezone, processed_week, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (account_id, body.email, password_hash, body.timezone,
             clock.add_days(clock.monday(now, body.timezone), -7), clock.iso(now)),
        )
        for name in DEFAULT_PROJECTS[body.language]:
            con.execute(
                "INSERT INTO project (id, account_id, name, created_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), account_id, name, clock.iso(now)),
            )
        token = create_session(con, account_id)
        account = con.execute("SELECT * FROM account WHERE id = ?", (account_id,)).fetchone()
    set_cookie(response, token)
    return {"account": account_json(account)}


@routes.post("/login")
def login(body: Login, request: Request, response: Response, con: Con):
    now = clock.now()
    email = body.email.strip().lower()
    ip = request.client.host if request.client else ""
    window = clock.iso(now - timedelta(minutes=15))
    con.execute("DELETE FROM login_attempt WHERE at < ?", (clock.iso(now - timedelta(days=7)),))
    for column, value, limit in (("email", email, 5), ("ip", ip, 30)):
        n, first = con.execute(
            f"SELECT count(*), min(at) FROM login_attempt WHERE {column} = ? AND at > ?",
            (value, window),
        ).fetchone()
        if n >= limit:
            retry_at = clock.iso(datetime.fromisoformat(first) + timedelta(minutes=15))
            return JSONResponse({"error": "locked", "retry_at": retry_at}, 429)
    account = con.execute("SELECT * FROM account WHERE email = ?", (email,)).fetchone()
    if not account or not check_password(body.password, account["password_hash"]):
        con.execute(
            "INSERT INTO login_attempt (email, ip, at) VALUES (?, ?, ?)",
            (email, ip, clock.iso(now)),
        )
        return JSONResponse({"error": "credentials"}, 401)
    con.execute("DELETE FROM login_attempt WHERE email = ?", (email,))
    token = create_session(con, account["id"])
    set_cookie(response, token)
    return {"account": account_json(account)}


@routes.post("/logout", status_code=204)
def logout(account: Account, con: Con):
    con.execute("DELETE FROM session WHERE token_hash = ?", (account["token_hash"],))
    resp = Response(status_code=204)
    clear_cookie(resp)
    return resp


@routes.post("/password/request", status_code=202)
def request_reset(body: ResetRequest, tasks: BackgroundTasks, con: Con):
    account = con.execute(
        "SELECT id, email, language FROM account WHERE email = ?", (body.email,)
    ).fetchone()
    if account:
        token = secrets.token_urlsafe(32)
        expires = clock.iso(clock.now() + timedelta(hours=1))
        con.execute(
            "INSERT INTO password_token (token_hash, account_id, expires_at) VALUES (?, ?, ?)",
            (_sha(token), account["id"], expires),
        )
        link = f"{os.environ.get('SEMANA_BASE_URL', 'http://127.0.0.1:8000')}/password#{token}"
        language = account["language"] if account["language"] in RESET_MAIL else body.language
        subject, text = RESET_MAIL[language or "en"]
        tasks.add_task(mail.send, account["email"], subject, text.format(link=link))
    return Response(status_code=202)


@routes.post("/password/reset", status_code=204)
def reset_password(body: Reset, con: Con):
    now = clock.iso(clock.now())
    password_hash = hash_password(body.password)
    with transaction(con):
        row = con.execute(
            "SELECT * FROM password_token WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?",
            (_sha(body.token), now),
        ).fetchone()
        if not row:
            return JSONResponse({"error": "invalid_token"}, 400)
        con.execute(
            "UPDATE account SET password_hash = ? WHERE id = ?", (password_hash, row["account_id"])
        )
        con.execute(
            "UPDATE password_token SET used_at = ? WHERE token_hash = ?", (now, row["token_hash"])
        )
        con.execute("DELETE FROM session WHERE account_id = ?", (row["account_id"],))
    return Response(status_code=204)


@routes.delete("/account", status_code=204)
def delete_account(body: CurrentPassword, account: Account, con: Con):
    if not check_password(body.password, account["password_hash"]):
        return JSONResponse({"error": "wrong_password"}, 403)
    with transaction(con):
        con.execute("DELETE FROM account WHERE id = ?", (account["id"],))
        con.execute("DELETE FROM login_attempt WHERE email = ?", (account["email"].lower(),))
    resp = Response(status_code=204)
    clear_cookie(resp)
    return resp
