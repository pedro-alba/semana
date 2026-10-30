import os
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


def now():
    fixed = os.environ.get("SEMANA_NOW")
    if fixed and os.environ.get("SEMANA_SECURE_COOKIE") == "0":
        return datetime.fromisoformat(fixed).astimezone(UTC)
    return datetime.now(UTC)


def iso(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def monday(dt, timezone):
    d = dt.astimezone(ZoneInfo(timezone)).date()
    return (d - timedelta(days=d.weekday())).isoformat()


def is_monday(s):
    try:
        return date.fromisoformat(s).weekday() == 0 and len(s) == 10
    except (TypeError, ValueError):
        return False


def add_days(s, n):
    return (date.fromisoformat(s) + timedelta(days=n)).isoformat()
