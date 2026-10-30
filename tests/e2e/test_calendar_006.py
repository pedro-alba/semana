"""Feature 006: event editor, details card, dragging, project memory and search."""

import os
import sqlite3
import uuid
from datetime import date, timedelta

from helpers import log_in, sign_up
from playwright.sync_api import expect

MONDAY = date.today() - timedelta(days=date.today().weekday())


def db():
    return sqlite3.connect(os.environ["SEMANA_DB"])


def day(n):
    return (MONDAY + timedelta(days=n)).isoformat()


def create(page, server, title, start, end, repeat="none", location=""):
    account_id = page.request.get(server + "/api/start").json()["account"]["id"]
    r = page.request.post(server + "/api/ops", data={"account_id": account_id, "ops": [{
        "op": "event.save", "id": str(uuid.uuid4()), "project_id": None, "title": title,
        "start": start, "end": end, "all_day": False, "repeat": repeat, "until": None,
        "location": location, "description": "Bring the book", "base_rev": 0}]})
    assert r.json()["results"][0]["status"] == "ok"


def calendar(page):
    page.get_by_role("button", name="Calendar").click()
    expect(page.get_by_role("heading", name="Agenda")).to_be_visible()


def new_page(browser, server, email="a@test.com"):
    page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
    sign_up(page, server, email)
    return page


def test_editor(browser, server):
    page = new_page(browser, server)
    calendar(page)
    page.get_by_role("button", name="+ New event").click()
    form = page.locator("#event-form")
    names = form.locator("[name]").evaluate_all("els => els.map(e => e.name)")
    assert names == ["title", "description", "allDay", "fullDay", "start", "end", "repeat", "until",
                     "projectId", "location"]
    until = page.locator("#event-until")
    expect(form.locator("[name=repeat]")).to_have_value("none")
    expect(until).to_be_hidden()
    form.locator("[name=repeat]").select_option("daily")
    expect(until).to_be_visible()
    form.locator("[name=repeat]").select_option("none")
    expect(until).to_be_hidden()

    start = form.locator("[name=start]")
    d = start.input_value()[:10]
    start.fill(d + "T15:30")
    start.dispatch_event("change")
    expect(form.locator("[name=end]")).to_have_value(d + "T16:30")
    start.fill(d + "T08:00")  # the end is still after it: unchanged
    start.dispatch_event("change")
    expect(form.locator("[name=end]")).to_have_value(d + "T16:30")

    form.locator("[name=title]").fill("Daily")
    form.locator("[name=repeat]").select_option("daily")
    page.get_by_role("button", name="Save event").click()
    # the footer already said "Saved": wait for the event to reach the server
    for _ in range(50):
        with db() as con:
            if con.execute("SELECT count(*) FROM event").fetchone()[0]:
                break
        page.wait_for_timeout(100)
    page.get_by_role("button", name="Next week").click()
    expect(page.locator(".cal-event", has_text="Daily")).to_have_count(7)


def test_card(browser, server):
    page = new_page(browser, server)
    create(page, server, "Class", day(1) + "T09:00", day(1) + "T10:00", "weekly", "School")
    page.reload()
    calendar(page)
    block = page.locator(".cal-event", has_text="Class")
    block.hover()
    card = page.locator("#event-card")
    expect(card).to_be_visible()
    for text in ("Class", "09:00–10:00", "Every Tuesday", "School", "Bring the book"):
        expect(card).to_contain_text(text)
    page.mouse.move(5, 5)
    expect(card).to_be_hidden()
    block.focus()
    expect(card).to_be_visible()


def drag(page, block, column, minute):
    b = block.bounding_box()
    c = page.locator(".cal-day").nth(column).bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + 10)
    page.mouse.down()
    target = (c["x"] + c["width"] / 2, c["y"] + minute + 10)
    page.mouse.move(*target, steps=8)
    page.mouse.up()


def test_drag(browser, server):
    page = new_page(browser, server)
    create(page, server, "Single", day(1) + "T09:00", day(1) + "T10:00")
    create(page, server, "Series", day(-5) + "T13:00", day(-5) + "T14:00", "weekly")
    page.reload()
    calendar(page)

    drag(page, page.locator(".cal-event", has_text="Single"), 2, 11 * 60)
    expect(page.locator("#storage")).to_have_text("Saved")
    expect(page.locator(".cal-day").nth(2).locator(".cal-event", has_text="Single")).to_be_visible()
    drag(page, page.locator(".cal-event", has_text="Series"), 3, 14 * 60)
    page.locator("#series-pop").get_by_role("button", name="Whole series").click()
    expect(page.locator(".cal-day").nth(3).locator(".cal-event", has_text="Series")).to_be_visible()
    expected = {"Single": f"{day(2)}T11:00 {day(2)}T12:00", "Series": f"{day(-4)}T14:00 {day(-4)}T15:00"}
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        with db() as con:
            rows = dict(con.execute("SELECT title, start || ' ' || \"end\" FROM event"))
        if rows == expected:
            break
        page.wait_for_timeout(100)
    assert rows == expected

    page.locator(".cal-event", has_text="Single").click()
    expect(page.locator("#event-form [name=title]")).to_have_value("Single")


def test_memory(browser, server):
    page = new_page(browser, server)
    project = page.locator("#project")
    project.select_option(label="Work")
    expect(page.locator("#project option:checked")).to_have_text("Work")
    calendar(page)
    page.locator("#project").select_option(label="Personal")
    page.reload()
    expect(page.locator("#project option:checked")).to_have_text("Work")
    calendar(page)
    expect(page.locator("#project option:checked")).to_have_text("Personal")

    page.get_by_role("button", name="Tasks", exact=True).click()
    page.locator(".profile-menu summary").click()
    page.locator("#profile-pop").get_by_role("button", name="Log out").click()
    page.get_by_role("button", name="Create account").click()
    page.get_by_label("E-mail").fill("b@test.com")
    page.get_by_label("Password").fill("good-password-1")
    page.locator("#signup-form button.primary").click()
    expect(page.locator("#storage")).to_have_text("Saved")
    expect(page.locator("#project option:checked")).to_have_text("Personal")
    page.locator(".profile-menu summary").click()
    page.locator("#profile-pop").get_by_role("button", name="Log out").click()
    log_in(page, "a@test.com")
    expect(page.locator("#project option:checked")).to_have_text("Work")


def test_search(browser, server):
    page = new_page(browser, server)
    today = date.today().isoformat()
    start = (date.today() - timedelta(days=14)).isoformat()
    create(page, server, "English class", start + "T19:00", start + "T20:00", "weekly", "School")
    page.get_by_role("button", name="Search").click()
    page.keyboard.type("school")
    result = page.locator(".so", has_text="English class")
    expect(result).to_contain_text("Event")
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Agenda")).to_be_visible()
    focused = page.locator(".cal-event:focus")
    expect(focused).to_contain_text("English class")
    assert focused.get_attribute("data-day") == today
    expect(page.locator("#event-card")).to_be_visible()
