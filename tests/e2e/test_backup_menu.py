"""Prototype import and backup (feature 005): conversion, the backup menu, export and import."""

import json
import re
from datetime import date
from pathlib import Path

from helpers import new_task, sign_up
from playwright.sync_api import expect

FIXTURES = Path(__file__).parent.parent / "fixtures"


def read(page, text):
    return page.evaluate("""async t => {
        const P = await import('/js/pure.js'), b = P.readBackup(t);
        return b && {b, summary: P.backupSummary(b)};
    }""", text)


def test_conversion(page, server):
    page.goto(server + "/terms")
    v2 = read(page, (FIXTURES / "prototype_v2.json").read_text())
    assert v2 is not None
    b = v2["b"]
    assert (b["format"], b["version"], b["processed_week"]) == ("semana-backup", 1, "2026-09-28")
    assert v2["summary"] == {"projects": 2, "tasks": 3, "events": 2, "weeks": 3}
    t = b["tasks"][0]
    assert (t["title"], t["important"], t["due"], t["weeks_open"]) == (
        "Relatório do trimestre", True, "2026-10-09", 2)
    assert "<script" not in t["notes"] and "<strong>Rascunho</strong>" in t["notes"]
    assert [s["done_at"] for s in t["subtasks"]] == [None, "2026-10-06T10:00:00.000Z"]
    assert [h["kind"] for h in t["log"]] == ["system", "note"]
    assert b["notes"] == [{"project_id": "pessoal", "week": "2026-10-05",
                           "html": "<p>Semana de <mark>fechamento</mark></p>"}]
    e1, e2 = b["events"]
    assert (e1["repeat"], e1["until"], e2["project_id"], e2["repeat"], e2["until"]) == (
        "weekly", "2099-12-31", None, "none", None)
    assert b["snapshots"][0]["week"] == "2026-09-28"

    v1 = read(page, (FIXTURES / "prototype_v1.json").read_text())["b"]["tasks"][0]
    assert v1["important"] and v1["notes"].startswith("<p>Primeira linha</p><p>Segunda linha</p>")
    assert 'href="https://exemplo.com/minuta"' in v1["notes"]
    assert [(s["text"], s["done_at"] is not None) for s in v1["subtasks"]] == [
        ("Enviar minuta", False), ("Ligar para o cliente", True)]
    assert [h["text"] for h in v1["log"] if h["kind"] == "note"] == ["Cliente pediu ajustes"]

    assert read(page, '{"x": 1}') is None
    assert read(page, "not json") is None
    own = json.dumps({"format": "semana-backup", "version": 1, "projects": []})
    assert read(page, own)["b"]["format"] == "semana-backup"


def open_menu(page):
    menu = page.locator(".profile-menu")
    if not menu.evaluate("d => d.open"):
        menu.locator("summary").click()
    return page.locator("#profile-pop")


def test_import_prototype(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Old")
    page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text("Saved")

    pop = open_menu(page)
    page.locator("#import").set_input_files(str(FIXTURES / "prototype_v2.json"))
    expect(pop).to_contain_text("2 projects")
    expect(pop).to_contain_text("3 tasks")
    expect(pop).to_contain_text("2 events")
    expect(pop).to_contain_text("This deletes all of the account's current data")
    pop.get_by_role("button", name="Cancel").click()
    expect(page.locator(".task-card", has_text="Old")).to_be_visible()

    pop = open_menu(page)
    page.locator("#import").set_input_files(str(FIXTURES / "prototype_v2.json"))
    pop.get_by_role("button", name="Import and replace").click()
    expect(page.get_by_text("Backup imported.")).to_be_visible()
    expect(page.locator(".task-card", has_text="Old")).to_have_count(0)
    # open in the prototype: the rollover brought it to the current week
    expect(page.locator(".task-card", has_text="Relatório do trimestre")).to_be_visible()
    page.get_by_role("button", name="Calendar").click()
    expect(page.locator("#calendar")).to_contain_text("Aula de inglês")


def test_export_and_invalid(page, context, server, tmp_path):
    sign_up(page, server, "a@test.com")
    new_task(page, "Keep")
    page.keyboard.press("Escape")
    open_menu(page)
    with page.expect_download() as d:
        page.locator("#profile-pop").get_by_role("button", name="Export full backup").click()
    assert re.fullmatch(r"semana-backup-\d{4}-\d{2}-\d{2}\.json", d.value.suggested_filename)
    assert d.value.suggested_filename[14:24] <= date.today().isoformat()
    b = json.loads(Path(d.value.path()).read_text())
    assert b["format"] == "semana-backup" and [t["title"] for t in b["tasks"]] == ["Keep"]

    bad = tmp_path / "other.json"
    bad.write_text('{"name": "not a backup"}')
    open_menu(page)
    page.locator("#import").set_input_files(str(bad))
    expect(page.get_by_text("Invalid backup. Your current data was kept.")).to_be_visible()
    expect(page.locator(".task-card", has_text="Keep")).to_be_visible()

    context.set_offline(True)
    pop = open_menu(page)
    pop.get_by_role("button", name="Export full backup").click()
    expect(page.locator("#toast")).to_have_text("No connection. Connect to export.")
    pop = open_menu(page)
    pop.get_by_role("button", name="Import and replace").click()
    expect(page.locator("#toast")).to_have_text("No connection. Connect to import.")


def test_menu_at_360px_and_keyboard(browser, server):
    page = browser.new_context(viewport={"width": 360, "height": 740}).new_page()
    sign_up(page, server, "a@test.com")
    assert page.evaluate("document.scrollingElement.scrollWidth") <= 360
    page.locator(".profile-menu summary").focus()
    page.keyboard.press("Enter")
    pop = page.locator("#profile-pop")
    box = pop.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 360
    export = pop.get_by_role("button", name="Export full backup")
    for _ in range(40):  # goes through the appearance and language choices
        page.keyboard.press("Tab")
        if export.evaluate("b => b === document.activeElement"):
            break
    expect(export).to_be_focused()
    page.keyboard.press("Tab")
    expect(pop.get_by_role("button", name="Import and replace")).to_be_focused()
    with page.expect_file_chooser():
        page.keyboard.press("Enter")
