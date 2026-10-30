import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends

MIGRATIONS = Path(__file__).parent / "migrations"


def connect(path=None):
    con = sqlite3.connect(
        path or os.environ.get("SEMANA_DB", "semana.sqlite3"),
        isolation_level=None,
        check_same_thread=False,
    )
    con.row_factory = sqlite3.Row
    for pragma in ("journal_mode=WAL", "foreign_keys=ON", "busy_timeout=5000", "synchronous=NORMAL"):
        con.execute(f"PRAGMA {pragma}")
    return con


def migrate(con):
    # BEGIN IMMEDIATE: with 2 workers, only one applies; the other re-reads user_version afterwards.
    # ponytail: splits the file on ";", so migrations cannot have ";" inside strings
    with transaction(con):
        version = con.execute("PRAGMA user_version").fetchone()[0]
        for f in sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
            n = int(f.name[:3])
            if n > version:
                for statement in f.read_text().split(";"):
                    if statement.strip():
                        con.execute(statement)
                con.execute(f"PRAGMA user_version = {n}")


@contextmanager
def transaction(con):
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
    except BaseException:
        con.execute("ROLLBACK")
        raise
    con.execute("COMMIT")


def connection():
    con = connect()
    try:
        yield con
    finally:
        con.close()


Con = Annotated[sqlite3.Connection, Depends(connection)]
