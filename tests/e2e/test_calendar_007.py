"""Feature 007: only this occurrence or the series, duration by the edge, all day in the grid, summary."""

import uuid

from helpers import new_task
from playwright.sync_api import expect
from test_calendar_006 import calendar, day, db, drag, new_page


def create(page, server, title, start, end, repeat="none", until=None, **extra):
    account_id = page.request.get(server + "/api/start").json()["account"]["id"]
    r = page.request.post(server + "/api/ops", data={"account_id": account_id, "ops": [{
        "op": "event.save", "id": str(uuid.uuid4()), "project_id": None, "title": title,
        "start": start, "end": end, "all_day": False, "repeat": repeat, "until": until,
        "location": "", "description": "", "base_rev": 0, **extra}]})
    assert r.json()["results"][0]["status"] == "ok"


def rows(page, expected=None):
    """Events in the database; with `expected`, waits until the queue's send arrives."""
    for _ in range(50):
        with db() as con:
            current = sorted(con.execute('SELECT title, start, "end", repeat, skipped FROM event'))
        if expected is None or current == expected:
            return current
        page.wait_for_timeout(100)
    return current


def test_only_this_one_when_dragging(browser, server):
    page = new_page(browser, server)
    create(page, server, "Series", day(-6) + "T13:00", day(-6) + "T14:00", "weekly")
    page.reload()
    calendar(page)
    drag(page, page.locator(".cal-event", has_text="Series"), 3, 15 * 60)
    pop = page.locator("#series-pop")
    expect(pop).to_contain_text("Change only this one or the whole series?")
    pop.get_by_role("button", name="Only this one").click()
    expected = sorted([
        ("Series", f"{day(-6)}T13:00", f"{day(-6)}T14:00", "weekly", f'["{day(1)}"]'),
        ("Series", f"{day(3)}T15:00", f"{day(3)}T16:00", "none", "[]"),
    ])
    assert rows(page, expected) == expected
    expect(page.locator(".cal-day").nth(1).locator(".cal-event")).to_have_count(0)
    expect(page.locator(".cal-day").nth(3).locator(".cal-event", has_text="Series")).to_be_visible()
    page.get_by_role("button", name="Next week").click()
    expect(page.locator(".cal-day").nth(1).locator(".cal-event", has_text="Series")).to_be_visible()


def test_cancel(browser, server):
    page = new_page(browser, server)
    create(page, server, "Series", day(-6) + "T13:00", day(-6) + "T14:00", "weekly")
    page.reload()
    calendar(page)
    before = rows(page)
    drag(page, page.locator(".cal-event", has_text="Series"), 3, 15 * 60)
    expect(page.locator("#series-pop")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#series-pop")).to_have_count(0)
    expect(page.locator(".cal-day").nth(1).locator(".cal-event", has_text="Series")).to_be_visible()
    page.wait_for_timeout(300)
    assert rows(page) == before


def pull_edge(page, block, column, minute):
    b = block.bounding_box()
    c = page.locator(".cal-day").nth(column).bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] - 2)
    page.mouse.down()
    page.mouse.move(c["x"] + c["width"] / 2, c["y"] + minute, steps=8)
    page.mouse.up()


def test_edge(browser, server):
    page = new_page(browser, server)
    create(page, server, "Single", day(2) + "T09:00", day(2) + "T10:00")
    create(page, server, "Series", day(-6) + "T13:00", day(-6) + "T14:00", "weekly")
    page.reload()
    calendar(page)
    pull_edge(page, page.locator(".cal-event", has_text="Single"), 2, 11 * 60)
    pull_edge(page, page.locator(".cal-event", has_text="Series"), 1, 14 * 60 + 30)
    page.locator("#series-pop").get_by_role("button", name="Whole series").click()
    expected = sorted([
        ("Series", f"{day(-6)}T13:00", f"{day(-6)}T14:30", "weekly", "[]"),
        ("Single", f"{day(2)}T09:00", f"{day(2)}T11:00", "none", "[]"),
    ])
    assert rows(page, expected) == expected


def test_delete_only_this_one(browser, server):
    page = new_page(browser, server)
    create(page, server, "Series", day(-6) + "T13:00", day(-6) + "T14:00", "weekly")
    page.reload()
    calendar(page)
    page.locator(".cal-event", has_text="Series").click()
    page.locator(".event-editor").get_by_role("button", name="Delete").click()
    page.locator(".event-editor .confirm").get_by_role("button", name="Only this one").click()
    expected = [("Series", f"{day(-6)}T13:00", f"{day(-6)}T14:00", "weekly", f'["{day(1)}"]')]
    assert rows(page, expected) == expected
    expect(page.locator(".cal-event", has_text="Series")).to_have_count(0)
    page.get_by_role("button", name="Next week").click()
    expect(page.locator(".cal-event", has_text="Series")).to_have_count(1)


def test_all_day(browser, server):
    page = new_page(browser, server)
    calendar(page)
    band = page.locator(".all-day:not(.due-strip)")
    expect(band).to_have_count(0)
    create(page, server, "Holiday", day(2) + "T00:00", day(3) + "T00:00", all_day=True)
    create(page, server, "Trip", day(4) + "T00:00", day(5) + "T00:00", all_day=True,
           fills_day=True)
    page.reload()
    calendar(page)
    expect(band).to_have_count(1)
    expect(band.locator(".all-day-event", has_text="Holiday")).to_be_visible()
    trip = page.locator(".cal-day").nth(4).locator(".cal-event", has_text="Trip")
    expect(trip).to_contain_text("All day")
    assert trip.bounding_box()["height"] > 1000

    page.locator(".all-day-event", has_text="Holiday").click()
    expect(page.locator("#event-full")).to_be_visible()
    page.locator("#event-form [name=fullDay]").check()
    page.get_by_role("button", name="Save event").click()
    expect(band).to_have_count(0)


def test_summary_and_card(browser, server):
    page = new_page(browser, server)
    create(page, server, "Medicine", day(-7) + "T08:00", day(-7) + "T08:15", "daily", day(40))
    page.reload()
    agenda = page.locator(".p-agenda")
    row = agenda.locator(".event-row", has_text="Medicine")
    expect(row).to_have_count(1)
    end = day(40)
    expect(row).to_contain_text(f"Every day, until {end[5:7]}/{end[8:10]}")
    new_task(page, "Nothing at all")
    page.keyboard.press("Escape")
    expect(page.locator(".task-card", has_text="Nothing at all").locator(".card-sub")).to_have_text("")


def test_fill_day_checks_all_day(browser, server):
    page = new_page(browser, server)
    calendar(page)
    page.get_by_role("button", name="+ New event").click()
    form = page.locator("#event-form")
    form.locator("[name=fullDay]").check()
    expect(form.locator("[name=allDay]")).to_be_checked()
    expect(form.locator("[name=fullDay]")).to_be_checked()
    form.locator("[name=allDay]").uncheck()
    expect(form.locator("[name=fullDay]")).not_to_be_checked()
