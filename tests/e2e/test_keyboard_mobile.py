"""Full flow with the keyboard only, on a 360 px screen (SC-008)."""

import pytest
from helpers import sign_up
from playwright.sync_api import expect


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 360, "height": 740}, "has_touch": True}


def no_side_scroll(page):
    assert page.evaluate("document.scrollingElement.scrollWidth") <= 360


def test_keyboard_only_at_360px(page, server):
    page.goto(server)
    expect(page.get_by_label("E-mail")).to_be_focused()
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Create account")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_label("E-mail")).to_be_focused()
    page.keyboard.type("a@test.com")
    page.keyboard.press("Tab")
    page.keyboard.type("good-password-1")
    no_side_scroll(page)
    page.keyboard.press("Enter")
    expect(page.locator("#storage")).to_have_text("Saved")
    no_side_scroll(page)

    for title in ("First", "Second"):
        page.get_by_role("button", name="+ New task").focus()
        page.keyboard.press("Enter")
        expect(page.locator("#doc-title")).to_be_focused()
        page.keyboard.type(title)
        page.keyboard.press("Enter")
        expect(page.locator("#notes")).to_be_focused()
        page.keyboard.type("Note for " + title)
        page.keyboard.press("Escape")
        expect(page.locator(".task-card", has_text=title)).to_be_focused()
    no_side_scroll(page)

    page.keyboard.press("Alt+ArrowUp")
    cards = page.locator(".task-card .card-title")
    expect(cards).to_have_text(["Second", "First"])
    expect(page.locator(".task-card", has_text="Second")).to_be_focused()

    page.keyboard.press("Enter")
    page.keyboard.press("ArrowRight")
    expect(page.locator(".task-card", has_text="Second").locator(".sr-progress")).to_have_text("5")
    expect(page.locator("#storage")).to_have_text("Saved")

    page.reload()
    expect(cards).to_have_text(["Second", "First"])

    page.locator(".profile-menu summary").focus()
    page.keyboard.press("Enter")
    logout = page.get_by_role("button", name="Log out")
    for _ in range(40):  # goes through the appearance and language choices (004)
        page.keyboard.press("Tab")
        if logout.evaluate("b => b === document.activeElement"):
            break
    expect(logout).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()
    no_side_scroll(page)


def test_calendar_keyboard_mobile(browser, server):
    # No touch: with touch, Chromium won't let you type into <input type="date"> (it uses the native picker).
    page = browser.new_context(viewport={"width": 360, "height": 740}).new_page()
    sign_up(page, server, "c@test.com")
    page.get_by_role("button", name="Calendar").focus()
    page.keyboard.press("Enter")
    page.get_by_role("button", name="+ New event").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#event-form [name=title]")).to_be_focused()
    page.keyboard.type("By keyboard")
    page.keyboard.press("Enter")
    expect(page.locator(".cal-event", has_text="By keyboard")).to_be_visible()
    expect(page.locator("#storage")).to_have_text("Saved")
    no_side_scroll(page)

    page.get_by_role("button", name="Tasks", exact=True).focus()
    page.keyboard.press("Enter")
    page.get_by_role("button", name="+ New task").focus()
    page.keyboard.press("Enter")
    page.keyboard.type("With due date")
    page.get_by_role("button", name="Set due date").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#due-input")).to_be_focused()
    page.keyboard.type("01152030")  # date field in the test browser's format (en-US)
    expect(page.locator(".due-chip")).to_contain_text("Jan 15")
    expect(page.locator("#storage")).to_have_text("Saved")
    no_side_scroll(page)
