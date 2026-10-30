"""Images in notes (feature 008): paste, drop, edge, offline and an invalid type."""

import re

from helpers import new_task, sign_up, sw_ready
from playwright.sync_api import expect

MAKE = """async ([w, h, mime]) => {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d'); x.fillStyle = '#48a'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#fff'; x.fillRect(10, 10, w / 2, h / 2);
    const b = await new Promise(r => c.toBlob(r, mime));
    window.__file = new File([b], 'img', {type: mime});
}"""
PASTE = """() => {
    const dt = new DataTransfer(); dt.items.add(window.__file);
    document.querySelector('#notes').dispatchEvent(
        new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
}"""
IMAGE_SRC = r"/api/images/([0-9a-f-]{36})"


def paste(page, w=400, h=300, mime="image/png"):
    page.evaluate(MAKE, [w, h, mime])
    page.evaluate(PASTE)


def server_html(page, server, title, pattern):
    """The task's notes on the server, waiting for the queue to send (the footer may say "Saved" first)."""
    start = page.request.get(server + "/api/start").json()
    for _ in range(50):
        for p in start["projects"]:
            w = page.request.get(f"{server}/api/week?project={p['id']}&week={start['current_week']}").json()
            for t in w["tasks"]:
                if t["title"] == title and re.search(pattern, t["notes"]):
                    return t["notes"]
        page.wait_for_timeout(100)
    raise AssertionError(f"{pattern!r} did not reach the server")


def image(page):
    img = page.locator("#notes img")
    expect(img).to_have_count(1)
    for _ in range(100):  # a just-pasted image may load only after the upload
        if page.evaluate("document.querySelector('#notes img').naturalWidth") > 0:
            return img
        page.wait_for_timeout(100)
    raise AssertionError("the image did not load")


def test_paste_and_shrink(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Photo")
    page.locator("#notes").click()
    page.keyboard.type("before ")
    paste(page, 3000, 2000, "image/jpeg")
    img = image(page)
    html = server_html(page, server, "Photo", r'<img src="/api/images/[0-9a-f-]{36}">')
    i = re.search(IMAGE_SRC, html).group(1)
    assert img.get_attribute("src") == f"/api/images/{i}"
    r = page.request.get(f"{server}/api/images/{i}")
    assert r.status == 200 and r.headers["content-type"] == "image/jpeg"
    assert page.evaluate("() => document.querySelector('#notes img').naturalWidth") == 1600


def test_edge(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Screenshot")
    page.locator("#notes").click()
    paste(page, 400, 300)
    img = image(page)
    b = img.bounding_box()
    page.mouse.move(b["x"] + b["width"] - 4, b["y"] + b["height"] / 2)
    page.mouse.down()
    page.mouse.move(b["x"] + b["width"] - 204, b["y"] + b["height"] / 2, steps=6)
    page.mouse.up()
    assert 190 <= int(img.get_attribute("width")) <= 210
    server_html(page, server, "Screenshot",
                r'<img src="/api/images/[0-9a-f-]{36}" width="(19\d|20\d|210)">')


def test_drop_into_week_notes(page, server):
    sign_up(page, server, "a@test.com")
    page.evaluate(MAKE, [200, 100, "image/png"])
    notes = page.locator("#notes")
    b = notes.bounding_box()
    page.evaluate("""([x, y]) => {
        const dt = new DataTransfer(); dt.items.add(window.__file);
        document.querySelector('#notes').dispatchEvent(new DragEvent('drop',
            {dataTransfer: dt, clientX: x, clientY: y, bubbles: true, cancelable: true}));
    }""", [b["x"] + 20, b["y"] + 20])
    image(page)
    start = page.request.get(server + "/api/start").json()
    url = f"{server}/api/week?project={start['projects'][0]['id']}&week={start['current_week']}"
    for _ in range(50):  # the footer may say "Saved" before the send finishes
        if "/api/images/" in page.request.get(url).json()["notes"]["html"]:
            break
        page.wait_for_timeout(100)
    page.reload()
    image(page)


def test_offline(page, context, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Offline")
    expect(page.locator("#storage")).to_have_text("Saved")
    sw_ready(page)
    context.set_offline(True)
    page.locator("#notes").click()
    paste(page, 300, 200)
    image(page)  # comes from IndexedDB, through the service worker
    expect(page.locator("#storage")).to_have_text(re.compile("Offline|waiting"))
    context.set_offline(False)
    page.evaluate("dispatchEvent(new Event('online'))")
    html = server_html(page, server, "Offline", IMAGE_SRC)
    i = re.search(IMAGE_SRC, html).group(1)
    for _ in range(50):
        if page.request.get(f"{server}/api/images/{i}").status == 200:
            break
        page.wait_for_timeout(100)
    assert page.request.get(f"{server}/api/images/{i}").status == 200


def test_invalid_type(page, server):
    sign_up(page, server, "a@test.com")
    new_task(page, "Text")
    page.locator("#notes").click()
    page.evaluate("() => { window.__file = new File(['hi'], 'a.txt', {type: 'text/plain'}) }")
    page.evaluate(PASTE)
    expect(page.locator("#toast")).to_contain_text("Use JPG, PNG, GIF or WebP images up to 20 MB.")
    expect(page.locator("#notes img")).to_have_count(0)
