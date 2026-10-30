"""Parity between the client and server sanitizers (R11), over tests/fixtures/html_cases.json."""
import json
from html.parser import HTMLParser
from pathlib import Path

import pytest

from semana.sanitize import clean

CASES = json.loads((Path(__file__).parent.parent / "fixtures/html_cases.json").read_text())
TAGS = {"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "mark", "a", "br"}
SCHEMES = ("http:", "https:", "mailto:", "file:")


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS:
            self.problems.append(f"tag {tag}")
        for name, value in attrs:
            if not (tag == "a" and name == "href"):
                self.problems.append(f"attribute {name} on {tag}")
            elif not (value or "").strip().lower().startswith(SCHEMES):
                self.problems.append(f"href {value!r}")

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag not in TAGS:
            self.problems.append(f"tag /{tag}")


def problems(html):
    c = Collector()
    c.feed(html)
    c.close()
    return c.problems


def test_enough_cases():
    assert len(CASES) >= 25


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(case):
    assert problems(case["output"]) == []  # the client's own output follows FR-035/036
    assert clean(case["output"]) == case["output"]  # (a) client output is a fixed point
    x = clean(case["input"])
    assert problems(x) == []  # (b) nothing outside the list
    assert clean(x) == x  # (c) idempotent


def test_images():
    u = "/api/images/0b8f1c2e-3d4a-4b5c-8d6e-7f8091a2b3c4"
    assert clean(f'<p><img src="{u}" width="300" onerror="x()"></p>') == (
        f'<p><img src="{u}" width="300"></p>')
    assert clean('<p><img src="https://x.com/a.png">hi</p>') == "<p>hi</p>"
    assert clean('<img src="javascript:alert(1)">') == ""
    assert clean(f'<img src="{u}/../x">') == ""
    assert clean(f'<img src="{u}" width="9">') == f'<img src="{u}">'
    assert clean('<img src="/api/imagens/0b8f1c2e-3d4a-4b5c-8d6e-7f8091a2b3c4">') == ""
    assert clean('<a href="/relative">r</a>') == "<a>r</a>"
