"""The client's pure functions in the browser: sanitizing (R11), and links and paths (FR-037)."""

import json
from pathlib import Path

import pytest

CASES = json.loads((Path(__file__).parent.parent / "fixtures" / "html_cases.json").read_text())


@pytest.fixture
def pure(page, server):
    page.goto(server + "/terms")
    page.evaluate("async () => { window.P = await import('/js/pure.js') }")
    return lambda js, *a: page.evaluate(f"(a) => {{ const P = window.P; return {js} }}", list(a))


def test_sanitize_matches_expected(pure):
    outputs = pure("a[0].map(c => P.sanitizeHTML(c.input))", CASES)
    for case, output in zip(CASES, outputs, strict=True):
        assert output == case["output"], case["name"]


@pytest.mark.parametrize(
    ("text", "href"),
    [
        ("example.com.br/x", "https://example.com.br/x"),
        ("ana@example.com", "mailto:ana@example.com"),
        ('"C:\\Users\\ana\\Final contract.pdf"', "file:///C:/Users/ana/Final%20contract.pdf"),
        ("C:\\Users\\ana\\Ação.pdf", "file:///C:/Users/ana/A%C3%A7%C3%A3o.pdf"),
        ("\\\\server\\folder\\a.docx", "file://server/folder/a.docx"),
        ("/home/ana/a.txt", "file:///home/ana/a.txt"),
        ("https://site.com.br/a?b=1", "https://site.com.br/a?b=1"),
    ],
)
def test_parse_link(pure, text, href):
    assert pure("P.parseLink(a[0])", text) == {"href": href}


def test_tilde_asks_for_full_path(pure):
    assert "full path" in pure("P.parseLink(a[0]).error", "~/a.txt")


@pytest.mark.parametrize(
    "path",
    ["C:\\Users\\ana\\Final contract.pdf", "C:\\Users\\ana\\Ação.pdf", "\\\\server\\folder\\a.docx", "/home/ana/a.txt"],
)
def test_path_round_trip(pure, path):
    assert pure("P.nativePath(P.parseLink(a[0]).href)", path) == path


def test_labels(pure):
    assert pure("P.linkLabel(a[0])", "https://site.com.br/folder/") == "site.com.br/folder"
    assert pure("P.linkLabel(a[0])", "mailto:ana@example.com") == "ana@example.com"
    assert pure("P.fileName(a[0])", "file:///C:/Users/ana/Final%20contract.pdf") == "Final contract.pdf"


@pytest.mark.parametrize(
    ("text", "href"),
    [
        ("www.example.com", "https://www.example.com/"),
        ('"C:\\Users\\ana\\a.pdf"', "file:///C:/Users/ana/a.pdf"),
        ("\\\\server\\folder\\a.docx", "file://server/folder/a.docx"),
        ("/Users/ana/a.pdf", "file:///Users/ana/a.pdf"),
        ("plain text", ""),
        ("https://a.com\nhttps://b.com", ""),
    ],
)
def test_auto_link(pure, text, href):
    assert pure("P.autoLink(a[0])", text) == href
