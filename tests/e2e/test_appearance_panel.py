"""Appearance (feature 004): panel in the profile, account on several devices, first paint."""

import re

from helpers import log_in, new_task, sign_up, sw_ready
from playwright.sync_api import expect

ATTR = {"theme": "data-theme", "mode": "data-mode-pref", "font": "data-font", "palette": "data-palette"}


def choose(page, **p):
    profile = page.locator(".profile-menu")
    if not profile.evaluate("d => d.open"):
        profile.locator("summary").click()
    names = {"theme": "theme", "mode": "mode-pref", "font": "font", "palette": "palette"}
    for k, v in p.items():
        page.locator(f'[data-pref="{names[k]}"][data-value="{v}"]').click()


def html_appearance(page):
    return {k: page.locator("html").get_attribute(a) for k, a in ATTR.items()}


def account_appearance(page, server):
    return page.request.get(server + "/api/start").json()["account"]["appearance"]


def test_instant_switch(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Task")
    notes = page.locator("#notes")
    notes.click()
    page.keyboard.type("abcdef")
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(3):
        page.keyboard.press("ArrowLeft")
    choose(page, theme="paper", mode="light", font="mono", palette="lavender")
    html = page.locator("html")
    for a, v in (("data-theme", "paper"), ("data-mode", "light"), ("data-font", "mono"),
                 ("data-palette", "lavender")):
        expect(html).to_have_attribute(a, v)
    for sel in ('[data-pref="theme"][data-value="paper"]', '[data-pref="palette"][data-value="lavender"]'):
        expect(page.locator(sel)).to_have_attribute("aria-checked", "true")
    pop = page.locator("#profile-pop")
    expect(pop).to_contain_text("a@test.com")
    expect(pop).to_contain_text("Preferences for your account. Your data doesn't change.")
    expect(pop.get_by_role("button", name="Log out")).to_be_visible()
    expect(pop.get_by_role("button", name="Delete account")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#doc-title")).to_have_value("Task")
    expect(notes).to_have_text("abcdef")
    expect(notes).to_be_focused()
    page.keyboard.type("X")
    expect(notes).to_have_text("abcXdef")
    expect(page.locator("#storage")).to_have_text("Saved")
    expected = {"theme": "paper", "mode": "light", "font": "mono", "palette": "lavender"}
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if account_appearance(page, server) == expected:
            break
        page.wait_for_timeout(100)
    assert account_appearance(page, server) == expected


def test_system_mode(page, server):
    sign_up(page, server, "a@test.com")
    page.emulate_media(color_scheme="light")
    choose(page, mode="system")
    html = page.locator("html")
    expect(html).to_have_attribute("data-mode", "light")
    page.emulate_media(color_scheme="dark")
    expect(html).to_have_attribute("data-mode", "dark")


# In Graphite the card background is a gradient of the progress color over --surface: it is measured
# against the strongest part (the left one), composed in a probe with the same mix as app.css.
CONTRAST = """() => {
  const rgb = s => { const n = s.match(/[\\d.]+/g).map(Number); return s.startsWith('color(') ? n.map((x, i) => i < 3 ? x * 255 : x) : n };
  const lum = ([r, g, b]) => [r, g, b].map(c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 })
    .reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
  const background = el => { for (; el; el = el.parentElement) { const c = rgb(getComputedStyle(el).backgroundColor); if (c.length < 4 || c[3] > 0) return c } return [255, 255, 255] };
  const bad = [];
  for (const theme of ['graphite', 'paper', 'ink']) for (const mode of ['light', 'dark'])
    for (const palette of ['classic', 'sunset', 'lavender', 'moss', 'traffic', 'neutral']) {
      appearance.apply({theme, mode, font: 'theme', palette}, false);
      for (const card of document.querySelectorAll('.task-card')) {
        let base = background(card);
        if (theme === 'graphite') {
          const probe = document.createElement('i');
          probe.style.cssText = 'position:absolute;inset:0;background:color-mix(in srgb,var(--task-color) ' + (mode === 'dark' ? 32 : 46) + '%,var(--surface))';
          card.append(probe); base = rgb(getComputedStyle(probe).backgroundColor); probe.remove();
        }
        const t = card.querySelector('.card-title'), a = lum(rgb(getComputedStyle(t).color)), b = lum(base);
        const r = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        if (r < 4.5) bad.push([theme, mode, palette, card.style.getPropertyValue('--p'), r.toFixed(2)].join(' '));
      }
    }
  return bad;
}"""


def test_contrast(page, server):
    sign_up(page, server, "a@test.com")
    for p in (0, 50, 100):
        new_task(page, f"Task {p}")
        page.keyboard.press("Escape")
    expect(page.locator("#storage")).to_have_text("Saved")
    ids = page.locator(".task-card").evaluate_all("cs => cs.map(c => c.dataset.id)")
    account_id = page.request.get(server + "/api/start").json()["account"]["id"]
    for _ in range(50):  # the footer may say "Saved" before the tasks reach the server
        r = page.request.post(server + "/api/ops", data={"account_id": account_id, "ops": [
            {"op": "task.progress", "id": i, "value": p} for i, p in zip(ids, (0, 50, 100), strict=True)]})
        if all(x["status"] == "ok" for x in r.json()["results"]):
            break
        page.wait_for_timeout(100)
    assert all(x["status"] == "ok" for x in r.json()["results"]), (ids, r.json())
    page.reload()
    expect(page.locator(".task-card")).to_have_count(3)
    page.add_style_tag(content="*{transition:none!important}")
    bad = page.evaluate(CONTRAST)
    assert not bad, bad


def test_other_device(page, browser, server):
    sign_up(page, server, "a@test.com")
    choose(page, theme="ink", mode="light", font="serif", palette="moss")
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if account_appearance(page, server)["theme"] == "ink":
            break
        page.wait_for_timeout(100)
    other = browser.new_context().new_page()
    other.goto(server)
    log_in(other, "a@test.com")
    expect(other.locator("#storage")).to_have_text("Saved")
    assert html_appearance(other) == {"theme": "ink", "mode": "light", "font": "serif",
                                      "palette": "moss"}
    choose(other, theme="graphite")
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if account_appearance(other, server)["theme"] == "graphite":
            break
        other.wait_for_timeout(100)
    page.evaluate("""() => {
        Object.defineProperty(document, 'hidden', {configurable: true, get: () => false});
        document.dispatchEvent(new Event('visibilitychange'));
    }""")
    expect(page.locator("html")).to_have_attribute("data-theme", "graphite")


ON_BODY = """new MutationObserver((_, o) => {
    if (document.body) { window.__themeOnBody = document.documentElement.dataset.theme; o.disconnect() }
}).observe(document, {childList: true, subtree: true})"""


def test_first_paint(page, context, server):
    sign_up(page, server, "a@test.com")
    choose(page, theme="paper")
    expect(page.locator("#storage")).to_have_text("Saved")
    sw_ready(page)
    page.add_init_script(ON_BODY)
    page.reload()
    assert page.evaluate("window.__themeOnBody") == "paper"
    context.set_offline(True)
    page.reload()
    assert page.evaluate("window.__themeOnBody") == "paper"


def test_pending_offline(page, context, server):
    sign_up(page, server, "a@test.com")
    sw_ready(page)
    context.set_offline(True)
    choose(page, theme="ink")
    expect(page.locator("#storage")).to_have_text(re.compile("Offline"))
    page.reload()
    expect(page.locator("#storage")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("data-theme", "ink")
    context.set_offline(False)
    page.evaluate("dispatchEvent(new Event('online'))")
    expect(page.locator("#storage")).to_have_text("Saved")
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if account_appearance(page, server)["theme"] == "ink":
            break
        page.wait_for_timeout(100)
    assert account_appearance(page, server)["theme"] == "ink"


def test_account_switch(page, server):
    sign_up(page, server, "a@test.com")
    choose(page, theme="paper")
    expect(page.locator("#storage")).to_have_text("Saved")
    page.locator("#profile-pop").get_by_role("button", name="Log out").click()
    expect(page.get_by_role("button", name="Create account")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("data-theme", "paper")
    page.get_by_role("button", name="Create account").click()
    page.get_by_label("E-mail").fill("b@test.com")
    page.get_by_label("Password").fill("good-password-1")
    page.locator("#signup-form button.primary").click()
    expect(page.locator("#storage")).to_have_text("Saved")
    expect(page.locator("html")).to_have_attribute("data-theme", "graphite")
    page.locator(".profile-menu summary").click()
    page.locator("#profile-pop").get_by_role("button", name="Delete account").click()
    page.locator("#delete-form").get_by_label("Confirm with your password").fill("good-password-1")
    page.locator("#delete-form button.danger").click()
    expect(page.get_by_text("Account deleted.")).to_be_visible()
    expect(page.locator("html")).to_have_attribute("data-theme", "graphite")
    assert page.evaluate("localStorage.getItem('semana-appearance')") is None


def test_menu_at_360px(browser, server):
    page = browser.new_context(viewport={"width": 360, "height": 740}, has_touch=True).new_page()
    sign_up(page, server, "a@test.com")
    page.locator(".profile-menu summary").click()
    pop = page.locator("#profile-pop")
    expect(pop).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    box = pop.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 360
    logout = pop.get_by_role("button", name="Log out")
    logout.scroll_into_view_if_needed()
    expect(logout).to_be_in_viewport()
    choose(page, theme="ink")
    expect(page.locator("html")).to_have_attribute("data-theme", "ink")
