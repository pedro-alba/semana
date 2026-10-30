"""Empty overview: generic lines in place of content, and "On the agenda" in the right column."""

from helpers import sign_up
from playwright.sync_api import expect


def test_empty(browser, server):
    page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
    sign_up(page, server, "a@test.com")
    for panel in (".p-subs", ".p-agenda", ".p-stale"):
        expect(page.locator(panel + " .ghost")).to_be_visible()
    expect(page.locator("#task-list .ghost-card")).to_have_count(3)
    expect(page.locator(".p-subs .sr-only")).to_have_text("No open subtasks.")
    subs, agenda, stale = (page.locator(p).bounding_box() for p in (".p-subs", ".p-agenda", ".p-stale"))
    assert agenda["x"] == subs["x"] == stale["x"]
    assert subs["y"] < agenda["y"] < stale["y"]
