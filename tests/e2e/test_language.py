"""Interface language: English by default, Portuguese from the browser or the profile, dates by locale."""

import json

from helpers import log_in, new_task, sign_up
from playwright.sync_api import expect


def account_language(page, server):
    return page.request.get(server + "/api/start").json()["account"]["language"]


def test_english_by_default(page, server):
    sign_up(page, server, "a@test.com")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    expect(page.get_by_role("button", name="Tasks", exact=True)).to_be_visible()
    expect(page.locator("footer em")).to_have_text("One day at a time.")
    assert account_language(page, server) == "auto"


def test_portuguese_from_the_browser(browser, server):
    page = browser.new_context(locale="pt-BR").new_page()
    page.goto(server)
    expect(page.locator("html")).to_have_attribute("lang", "pt-BR")
    page.get_by_role("button", name="Criar conta").click()
    expect(page.locator(".auth-legal a").first).to_have_attribute("href", "/terms?lang=pt-BR")
    page.get_by_label("E-mail").fill("a@test.com")
    page.get_by_label("Senha").fill("good-password-1")
    page.locator("#signup-form button.primary").click()
    expect(page.locator("#storage")).to_have_text("Salvo")
    expect(page.get_by_role("button", name="Tarefas", exact=True)).to_be_visible()
    expect(page.locator("footer em")).to_have_text("Nada como um dia após o outro dia.")
    expect(page.locator("#project option")).to_have_text(["Pessoal", "Trabalho"])
    page.get_by_role("button", name="Calendário").click()
    expect(page.locator(".day-head span").first).to_have_text("SEG")


def test_switch_in_profile(page, browser, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Task")
    notes = page.locator("#notes")
    notes.click()
    page.keyboard.type("abcdef")
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(3):
        page.keyboard.press("ArrowLeft")
    page.locator(".profile-menu summary").click()
    page.locator('[data-act="language"][data-value="pt-BR"]').click()

    # Right away, without a reload: the menu stays open, the task stays open.
    expect(page.locator("html")).to_have_attribute("lang", "pt-BR")
    expect(page.get_by_role("button", name="Tarefas", exact=True)).to_be_visible()
    pop = page.locator("#profile-pop")
    expect(pop).to_be_visible()
    expect(pop).to_contain_text("IDIOMA")
    expect(page.locator('[data-act="language"][data-value="pt-BR"]')).to_have_attribute(
        "aria-checked", "true")
    page.keyboard.press("Escape")
    expect(page.locator("#doc-title")).to_have_value("Task")
    expect(notes).to_be_focused()
    page.keyboard.type("X")
    expect(notes).to_have_text("abcXdef")
    expect(page.locator("#storage")).to_have_text("Salvo")

    for _ in range(50):  # the footer may say "Salvo" before the send finishes
        if account_language(page, server) == "pt-BR":
            break
        page.wait_for_timeout(100)
    assert account_language(page, server) == "pt-BR"

    page.reload()
    expect(page.get_by_role("button", name="+ Nova tarefa")).to_be_visible()

    other = browser.new_context().new_page()  # an English browser
    other.goto(server)
    expect(other.get_by_role("heading", name="Log in")).to_be_visible()
    log_in(other, "a@test.com")
    expect(other.locator("#storage")).to_have_text("Salvo")
    expect(other.locator("html")).to_have_attribute("lang", "pt-BR")

    # Back to automatic: the browser's language again.
    other.locator(".profile-menu summary").click()
    other.locator('[data-act="language"][data-value="auto"]').click()
    expect(other.get_by_role("button", name="Tasks", exact=True)).to_be_visible()


def test_dates_follow_language(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "With due date")
    page.locator("#due-input").fill("2030-01-15")
    page.locator("#due-input").dispatch_event("change")
    expect(page.locator(".due-chip")).to_contain_text("Tue, Jan 15")
    page.locator(".profile-menu summary").click()
    page.locator('[data-act="language"][data-value="pt-BR"]').click()
    expect(page.locator(".due-chip")).to_contain_text("15 de jan")
    expect(page.locator(".due-chip")).to_contain_text("Prazo")


def test_dictionaries_match(page, server):
    page.goto(server + "/terms")
    en, pt = page.evaluate("""async () => {
        const I = await import('/js/i18n.js');
        return [I.keys('en'), I.keys('pt-BR')];
    }""")
    assert sorted(en) == sorted(pt)
    assert len(en) > 250


def test_reset_request_sends_language(browser, server):
    page = browser.new_context(locale="pt-BR").new_page()
    page.goto(server)
    page.get_by_role("button", name="Esqueci a senha").click()
    page.get_by_label("E-mail").fill("a@test.com")
    with page.expect_request("**/api/password/request") as r:
        page.locator("#forgot-form button.primary").click()
    assert json.loads(r.value.post_data) == {"email": "a@test.com", "language": "pt-BR"}
    expect(page.locator(".auth-notice")).to_contain_text("Se houver uma conta com esse e-mail")
