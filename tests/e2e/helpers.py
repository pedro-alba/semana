"""Common steps for the browser tests."""

from playwright.sync_api import expect


def sign_up(page, url, email, password="good-password-1"):
    page.goto(url)
    page.get_by_role("button", name="Create account").click()
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Password").fill(password)
    page.locator("#signup-form button.primary").click()
    expect(page.locator("#storage")).to_have_text("Saved")


def log_in(page, email, password="good-password-1"):
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Password").fill(password)
    page.locator("#login-form button.primary").click()


def new_task(page, title):
    page.get_by_role("button", name="+ New task").click()
    page.keyboard.type(title)
    page.keyboard.press("Enter")


def sw_ready(page):
    page.evaluate("navigator.serviceWorker.ready")
    for _ in range(100):  # the CSP forbids eval, so no wait_for_function with a string
        if page.evaluate("!!navigator.serviceWorker.controller"):
            return
        page.wait_for_timeout(100)
    raise AssertionError("service worker is not in control")
