"""Event recurrence and overlap in the calendar (SC-003, FR-012, FR-024).

The expected occurrences are derived in Python another way: the series is generated from the
start (week by week or month by month) and then cut by week."""

from datetime import date, datetime, timedelta

import pytest

FIRST, LAST = date(2026, 1, 5), date(2027, 12, 27)  # Mondays over 24 months
WEEKS = [FIRST + timedelta(weeks=i) for i in range((LAST - FIRST).days // 7 + 1)]


@pytest.fixture
def occurrences(page, server):
    page.goto(server + "/terms")
    page.evaluate("async () => { window.P = await import('/js/pure.js') }")

    def compute(event):
        weeks = [s.isoformat() for s in WEEKS]
        return page.evaluate(
            "([e, ws]) => ws.map(w => window.P.occurrences(e, w).map(o => o.start))",
            [event, weeks])
    return compute


def series(start, end, repeat, until):
    """Every (start, end) occurrence of the series, generated from the start."""
    first, dur = datetime.fromisoformat(start), datetime.fromisoformat(end) - datetime.fromisoformat(start)
    limit = date.fromisoformat(until) if until else first.date()
    out = []
    if repeat == "weekly":
        d = first
        while d.date() <= limit:
            out.append((d, d + dur))
            d += timedelta(weeks=1)
    elif repeat == "monthly":
        year, month = first.year, first.month
        while date(year, month, 1) <= limit:
            try:
                d = first.replace(year=year, month=month)
            except ValueError:  # month without that day
                d = None
            if d and d.date() <= limit:
                out.append((d, d + dur))
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    else:
        out.append((first, first + dur))
    return out


def expected(event):
    everything = series(event["start"], event["end"], event["repeat"], event["until"])
    res = []
    for s in WEEKS:
        a, b = datetime.combine(s, datetime.min.time()), datetime.combine(s + timedelta(7), datetime.min.time())
        res.append([i.strftime("%Y-%m-%dT%H:%M") for i, f in everything if f > a and i < b])
    return res


CASES = {
    "weekly until 03/31": ("2026-01-06T09:00", "2026-01-06T10:00", "weekly", "2026-03-31"),
    "monthly on the 31st": ("2026-01-31T14:00", "2026-01-31T15:00", "monthly", "2027-12-31"),
    "monthly on the 29th": ("2026-01-29T08:00", "2026-01-29T09:00", "monthly", "2027-12-31"),
    "weekly across new year": ("2026-12-28T10:00", "2026-12-28T11:00", "weekly", "2027-01-31"),
    "single across midnight": ("2026-05-03T23:00", "2026-05-04T01:00", "none", ""),
    "3-day all day": ("2026-07-08T00:00", "2026-07-11T00:00", "none", ""),
}


@pytest.mark.parametrize("name", CASES)
def test_occurrences(occurrences, name):
    start, end, repeat, until = CASES[name]
    e = {"id": "x", "title": name, "start": start, "end": end, "allDay": end.endswith("T00:00"),
         "repeat": repeat, "until": until}
    assert occurrences(e) == expected(e)


def test_cases_cover_short_months():
    _, _, _, until = CASES["monthly on the 31st"]
    months = {i.month for i, _ in series("2026-01-31T14:00", "2026-01-31T15:00", "monthly", until)}
    assert months == {1, 3, 5, 7, 8, 10, 12}
    assert all(i.month != 2 for i, _ in series("2026-01-29T08:00", "2026-01-29T09:00", "monthly", "2027-12-31"))
    assert series(*CASES["weekly until 03/31"])[-1][0].date() == date(2026, 3, 31)


def test_overlap(page, server):
    page.goto(server + "/terms")
    r = page.evaluate("""async () => {
        const P = await import('/js/pure.js');
        return P.layoutEvents([{id: 'a', a: 540, b: 600}, {id: 'b', a: 550, b: 620}, {id: 'c', a: 560, b: 580},
                               {id: 'd', a: 700, b: 760}]);
    }""")
    together = [x for x in r if x["id"] in "abc"]
    assert sorted(x["lane"] for x in together) == [0, 1, 2]
    assert {x["columns"] for x in together} == {3}
    assert next(x for x in r if x["id"] == "d")["columns"] == 1


def ev(start, repeat="none", until="", end=None):
    return {"id": "e", "title": "x", "start": start, "end": end or start[:11] + "10:00",
            "allDay": False, "repeat": repeat, "until": until, "projectId": "",
            "description": "", "location": ""}


def test_daily_and_endless(occurrences):
    daily = occurrences(ev("2026-03-04T09:00", "daily"))
    by_week = dict(zip((s.isoformat() for s in WEEKS), daily, strict=True))
    assert by_week["2026-02-23"] == []
    assert len(by_week["2026-03-02"]) == 5  # Wednesday to Sunday
    assert len(by_week["2027-12-27"]) == 7
    weekly = occurrences(ev("2026-01-06T09:00", "weekly"))
    assert all(len(x) == 1 for x in weekly)


@pytest.fixture
def P(page, server):
    page.goto(server + "/terms")
    page.evaluate("async () => { window.P = await import('/js/pure.js'); window.I = await import('/js/i18n.js') }")
    return page


def test_next_occurrence(P):
    def nxt(e, today):
        return P.evaluate("([e, h]) => window.P.nextOccurrence(e, h)", [e, today])
    today = "2026-10-29"
    assert nxt(ev("2026-11-10T09:00"), today) == "2026-11-10"
    assert nxt(ev("2026-09-01T09:00"), today) == "2026-09-01"
    assert nxt(ev("2026-09-01T09:00", "weekly"), today) == "2026-11-03"  # Tuesdays
    assert nxt(ev("2026-09-01T09:00", "weekly", "2026-10-01"), today) == "2026-09-29"
    assert nxt(ev("2026-12-01T09:00", "weekly"), today) == "2026-12-01"
    assert nxt(ev("2026-09-29T09:00", "daily"), today) == "2026-10-29"


def test_skipped_dates_and_text(P):
    e = ev("2026-10-26T09:00", "daily") | {"except": ["2026-10-27", "2026-10-29"]}
    days = P.evaluate("e => window.P.occurrences(e, '2026-10-26').map(o => o.occurrence)", e)
    assert days == ["2026-10-26", "2026-10-28", "2026-10-30", "2026-10-31", "2026-11-01"]
    assert P.evaluate("e => window.P.nextOccurrence(e, '2026-10-29')", e) == "2026-10-30"

    def text(e, lang="en"):
        return P.evaluate("([e, l]) => { window.I.setLanguage(l); return window.P.repeatText(e) }", [e, lang])
    assert text(ev("2026-10-27T09:00")) == ""
    assert text(ev("2026-10-27T09:00", "daily", "2026-12-15")) == "Every day, until 12/15"
    assert text(ev("2026-10-27T09:00", "weekly")) == "Every Tuesday"
    assert text(ev("2026-10-31T09:00", "weekly")) == "Every Saturday"
    assert text(ev("2026-10-15T09:00", "monthly", "2027-03-15")) == "Every month on the 15th, until 03/15/2027"
    assert text(ev("2026-10-02T09:00", "monthly")) == "Every month on the 2nd"
    # Portuguese keeps the wording from before the translation
    assert text(ev("2026-10-27T09:00", "daily", "2026-12-15"), "pt-BR") == "Todos os dias, até 15/12"
    assert text(ev("2026-10-27T09:00", "weekly"), "pt-BR") == "Toda terça"
    assert text(ev("2026-10-31T09:00", "weekly"), "pt-BR") == "Todo sábado"
    assert text(ev("2026-10-15T09:00", "monthly", "2027-03-15"), "pt-BR") == "Todo dia 15, até 15/03/2027"
