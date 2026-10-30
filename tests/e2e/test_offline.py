"""Sending after the connection drops (SC-004, FR-056 to FR-059)."""

import os
import re
import sqlite3

from helpers import log_in, new_task, sign_up, sw_ready
from playwright.sync_api import expect

PENDING = re.compile(r"Offline · \d+ changes? waiting")


def db():
    return sqlite3.connect(os.environ["SEMANA_DB"])


def test_drop_with_reopened_tab(page, context, browser, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Contract")
    expect(page.locator("#storage")).to_have_text("Saved")
    sw_ready(page)

    context.set_offline(True)
    page.locator("#doc-title").fill("Contract reviewed")
    page.locator("#notes").click()
    page.keyboard.type("Written offline")
    page.locator("#sub-new-input").fill("Sign")
    page.keyboard.press("Enter")
    new_task(page, "Another offline")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text(PENDING)

    page.close()
    page = context.new_page()
    page.goto(server)
    expect(page.locator(".task-card")).to_have_count(2)
    expect(page.locator("#task-list")).to_contain_text("Contract reviewed")
    expect(page.locator("#storage")).to_have_text(PENDING)

    context.set_offline(False)
    expect(page.locator("#storage")).to_have_text("Saved", timeout=10_000)

    other = browser.new_context().new_page()
    other.goto(server)
    log_in(other, "a@test.com")
    expect(other.locator("#task-list")).to_contain_text("Another offline")
    other.locator(".task-card", has_text="Contract reviewed").click()
    expect(other.locator("#notes")).to_contain_text("Written offline")
    expect(other.locator(".sub-text")).to_have_value("Sign")


def test_logout_with_pending_asks(page, context, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Something")
    expect(page.locator("#storage")).to_have_text("Saved")
    context.set_offline(True)
    page.locator("#doc-title").fill("Something changed")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text(PENDING)
    page.locator(".profile-menu summary").click()
    page.get_by_role("button", name="Log out").click()
    expect(page.locator("#profile-pop")).to_contain_text(re.compile(r"will be discarded\. Log out anyway\?"))


def _pending_with_session_deleted(page, context, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Original")
    expect(page.locator("#storage")).to_have_text("Saved")
    context.set_offline(True)
    page.locator("#doc-title").fill("Edited without session")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text(PENDING)
    with db() as con:
        con.execute("DELETE FROM session")
    context.set_offline(False)
    expect(page.locator(".auth-notice")).to_contain_text("Your session expired. Log in again to send")


def test_expired_session_sends_after_login(page, context, server):
    _pending_with_session_deleted(page, context, server)
    log_in(page, "a@test.com")
    expect(page.locator("#task-list")).to_contain_text("Edited without session")
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if db().execute("SELECT title FROM task").fetchall() == [("Edited without session",)]:
            break
        page.wait_for_timeout(100)
    assert db().execute("SELECT title FROM task").fetchall() == [("Edited without session",)]


def test_pending_never_goes_to_another_account(page, context, browser, server):
    other = browser.new_context().new_page()
    sign_up(other, server, "b@test.com")
    _pending_with_session_deleted(page, context, server)
    log_in(page, "b@test.com")
    expect(page.locator(".empty-list")).to_be_visible()
    expect(page.locator("#storage")).to_have_text("Saved")
    assert db().execute("SELECT title FROM task").fetchall() == [("Original",)]


def test_week_not_loaded_needs_connection(page, context, server):
    sign_up(page, server, "a@test.com")
    context.set_offline(True)
    page.get_by_role("button", name="Next week").click()
    expect(page.locator("#toast")).to_contain_text("You need a connection to open this week.")


# --- feature 002: calendar and due dates ---

def open_calendar(page):
    page.get_by_role("button", name="Calendar").click()
    expect(page.get_by_role("heading", name="Agenda")).to_be_visible()


def new_event(page, title):
    page.get_by_role("button", name="+ New event").click()
    page.locator("#event-form [name=title]").fill(title)
    page.get_by_role("button", name="Save event").click()
    expect(page.locator(".cal-event", has_text=title)).to_be_visible()


def test_calendar_offline(page, context, browser, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "With due date")
    expect(page.locator("#storage")).to_have_text("Saved")
    sw_ready(page)

    context.set_offline(True)
    page.locator("#due-input").fill("2030-01-15")
    expect(page.locator(".due-chip")).to_contain_text("Due")
    page.keyboard.press("Escape")
    open_calendar(page)
    new_event(page, "Offline meeting")
    expect(page.locator("#storage")).to_have_text(PENDING)

    page.close()
    page = context.new_page()
    page.goto(server)
    expect(page.locator("#storage")).to_have_text(PENDING)
    open_calendar(page)
    expect(page.locator(".cal-event", has_text="Offline meeting")).to_be_visible()

    context.set_offline(False)
    expect(page.locator("#storage")).to_have_text("Saved", timeout=10_000)

    other = browser.new_context().new_page()
    other.goto(server)
    log_in(other, "a@test.com")
    other.locator(".task-card", has_text="With due date").click()
    expect(other.locator(".due-chip")).to_contain_text("Jan 15")
    open_calendar(other)
    expect(other.locator(".cal-event", has_text="Offline meeting")).to_be_visible()


def test_event_conflict(page, browser, server):
    sign_up(page, server, "a@test.com")
    open_calendar(page)
    new_event(page, "Original")
    expect(page.locator("#storage")).to_have_text("Saved")

    other = browser.new_context().new_page()
    other.goto(server)
    log_in(other, "a@test.com")
    open_calendar(other)
    other.locator(".cal-event", has_text="Original").click()
    page.locator(".cal-event", has_text="Original").click()

    page.locator("#event-form [name=title]").fill("From the first")
    page.get_by_role("button", name="Save event").click()
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if db().execute("SELECT title FROM event").fetchone()[0] == "From the first":
            break
        page.wait_for_timeout(100)

    other.locator("#event-form [name=title]").fill("From the second")
    other.get_by_role("button", name="Save event").click()
    other.locator("#toast").get_by_role("button", name="View").click()
    notice = other.locator(".event-editor .conflict")
    expect(notice).to_contain_text("changed on another device")
    expect(notice).to_contain_text("From the first")
    other.get_by_role("button", name="Keep my version").click()
    expect(other.locator(".event-editor .conflict")).to_contain_text("From the first")
    expect(other.locator("#storage")).to_have_text("Saved")

    # The footer already said "Saved"; wait for the kept version to reach the server.
    for _ in range(50):
        if db().execute("SELECT title FROM event").fetchone()[0] == "From the second":
            break
        other.wait_for_timeout(100)
    page.reload()
    open_calendar(page)
    expect(page.locator(".cal-event", has_text="From the second")).to_be_visible()
