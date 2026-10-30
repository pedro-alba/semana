"""Search (feature 003): the prototype's ranking, the box flow, the magnifier and offline."""

import re

from helpers import new_task, sign_up, sw_ready
from playwright.sync_api import expect

CURRENT, FUTURE, PAST = "2026-10-26", "2026-11-02", "2026-10-19"


def task(i, title, week=CURRENT, notes="", progress=0, at="2026-10-27T10:00:00Z"):
    return {"id": i, "title": title, "description": notes, "subtasks": [], "week": week,
            "projectId": "p", "lastActivity": at, "progress": progress}


def test_ranking(page, server):
    page.goto(server + "/terms")
    page.evaluate("async () => { window.P = await import('/js/pure.js') }")
    tasks = [
        task("joana", "Café with Joana"),
        task("same", "Café"),
        task("middle", "Notes from the café"),
        task("content", "Minutes", notes="<p>After the café, send the minutes</p>"),
        task("old", "Café", week=PAST),
        task("future", "Café", week=FUTURE),
        task("done", "Café", progress=100),
        task("other", "Groceries", at="2026-10-28T10:00:00Z"),
    ]
    notes = {CURRENT + "|p": "<p>café with parents</p>", PAST + "|p": ""}

    def search(q):
        return page.evaluate("""([ts, ns, q, w]) => {
            const r = window.P.rankSearch(window.P.searchItems(ts, ns), q, w);
            return {ids: r.list.map(it => it.id || it.key), recent: r.recent,
                    snippets: r.list.map(it => window.P.snippetOf(it, r.terms))};
        }""", [tasks, notes, q, CURRENT])

    r = search("cafe")
    assert r["ids"] == search("CAFÉ")["ids"] == search("café")["ids"]
    ids = r["ids"]
    assert ids[:4] == ["same", "future", "done", "old"]
    assert ids.index("joana") < ids.index("middle") < ids.index("content")
    assert ids.index("content") < ids.index(CURRENT + "|p")
    assert PAST + "|p" not in ids
    assert "<mark>café</mark>" in r["snippets"][ids.index("content")]
    assert search("cafe joana")["ids"] == ["joana"]
    empty = search("   ")
    assert empty["recent"] and empty["ids"][0] == "other" and "done" not in empty["ids"]


def test_flow(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Café with Joana")
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Next week").click()
    expect(page.locator(".eyebrow")).to_have_text("PLANNING")
    new_task(page, "Old")
    page.keyboard.type("Review the quarterly budget")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text("Saved")
    page.get_by_role("button", name="Current week and overview").click()

    page.keyboard.press("Control+Space")
    expect(page.locator("#search-input")).to_be_focused()
    page.keyboard.type("quarterly")
    first = page.locator(".so").first
    expect(first).to_contain_text("Old")
    expect(first.locator(".so-snippet mark")).to_have_text("quarterly")
    page.keyboard.press("Enter")
    expect(page.locator("#search")).to_have_count(0)
    expect(page.locator("#doc-title")).to_have_value("Old")
    expect(page.locator(".eyebrow")).to_have_text("PLANNING")
    for _ in range(50):  # the selection comes right after the task opens
        if page.evaluate("getSelection().toString()") == "quarterly":
            break
        page.wait_for_timeout(100)
    assert page.evaluate("getSelection().toString()") == "quarterly"

    page.get_by_role("button", name="Current week and overview").click()
    page.locator(".task-card", has_text="Café").click()
    page.locator("#notes").click()
    page.keyboard.press("Control+Space")
    expect(page.locator("#search")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#notes")).to_be_focused()
    page.keyboard.press("Control+Space")
    page.keyboard.press("Control+Space")
    expect(page.locator("#search")).to_have_count(0)


def test_search_button(browser, server):
    """The button is on every screen: in some browsers (Opera GX) Ctrl+Space belongs to the browser."""
    pc = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
    sign_up(pc, server, "pc@test.com")
    pc.get_by_role("button", name="Search").click()
    expect(pc.locator("#search-input")).to_be_focused()

    phone = browser.new_context(viewport={"width": 360, "height": 740}, has_touch=True).new_page()
    sign_up(phone, server, "phone@test.com")
    new_task(phone, "Buy bread")
    phone.keyboard.press("Escape")
    phone.get_by_role("button", name="Search").tap()
    phone.locator("#search-input").fill("bread")
    phone.locator(".so", has_text="Buy bread").tap()
    expect(phone.locator("#doc-title")).to_have_value("Buy bread")
    assert phone.evaluate("document.scrollingElement.scrollWidth") <= 360


def test_search_offline(page, context, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Contract")
    expect(page.locator("#storage")).to_have_text("Saved")
    sw_ready(page)
    page.keyboard.press("Control+Space")  # downloads the index while online
    expect(page.locator(".so")).to_have_count(1)
    page.keyboard.press("Escape")

    context.set_offline(True)
    page.locator("#doc-title").fill("New contract")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text(re.compile("Offline"))
    page.keyboard.press("Control+Space")
    page.keyboard.type("new")
    expect(page.locator(".so", has_text="New contract")).to_be_visible()
    expect(page.locator("#search")).to_contain_text(
        "Offline: results only from what was already opened on this device.")
