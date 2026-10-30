import json
import uuid

from semana import clock
from semana.db import transaction


def _pending(con, account_id):
    a = con.execute(
        "SELECT timezone, processed_week FROM account WHERE id = ?", (account_id,)
    ).fetchone()
    current = clock.monday(clock.now(), a["timezone"])
    return a["processed_week"], current


def apply(con, account_id):
    from semana.reads import task_json

    processed, current = _pending(con, account_id)
    if clock.add_days(processed, 7) >= current:
        return
    with transaction(con):
        processed, current = _pending(con, account_id)
        at = clock.iso(clock.now())
        while (w := clock.add_days(processed, 7)) < current:
            following = clock.add_days(w, 7)
            tasks = con.execute(
                "SELECT * FROM task WHERE account_id = ? AND week = ? ORDER BY position",
                (account_id, w),
            ).fetchall()
            if tasks:
                con.execute(
                    "INSERT OR IGNORE INTO snapshot (account_id, week, tasks) VALUES (?, ?, ?)",
                    (account_id, w, json.dumps([task_json(con, t) for t in tasks])),
                )
            text = f"Carried over from the week of {w}"
            projects = {t["project_id"] for t in tasks}
            for project_id in projects:
                open_ = [t for t in tasks if t["project_id"] == project_id and t["progress"] < 100]
                if not open_:
                    continue
                con.execute(
                    "UPDATE task SET position = position + ? WHERE account_id = ? AND project_id = ?"
                    " AND week = ?",
                    (len(open_), account_id, project_id, following),
                )
                for i, t in enumerate(open_, 1):
                    con.execute(
                        "UPDATE task SET week = ?, position = ?,"
                        " weeks_open = weeks_open + 1 WHERE id = ? AND account_id = ?",
                        (following, i, t["id"], account_id),
                    )
                    con.execute(
                        "INSERT INTO log_entry (id, account_id, task_id, at, kind, text)"
                        " VALUES (?, ?, ?, ?, 'system', ?)",
                        (str(uuid.uuid4()), account_id, t["id"], at, text),
                    )
            con.execute("UPDATE account SET processed_week = ? WHERE id = ?", (w, account_id))
            processed = w
