import re

import nh3

IMAGE = re.compile(r"/api/images/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
ABSOLUTE = re.compile(r"(https?|mailto|file):", re.IGNORECASE)
NO_SRC = re.compile(r"<img(?![^>]*\ssrc=)[^>]*>")


def _filter(tag, attr, value):
    """Images only from Semana itself (008); links stay absolute only."""
    if tag == "img" and attr == "src":
        return value if IMAGE.fullmatch(value) else None
    if tag == "img" and attr == "width":
        return value if value.isdigit() and 16 <= int(value) <= 4000 else None
    if tag == "a" and attr == "href":
        return value if ABSOLUTE.match(value) else None
    return value


_cleaner = nh3.Cleaner(
    tags={"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "mark", "a", "br", "img"},
    clean_content_tags={"script", "style"},
    attributes={"a": {"href"}, "img": {"src", "width"}, "*": set()},  # empty "*" drops the generic ones
    attribute_filter=_filter,
    url_schemes={"http", "https", "mailto", "file"},
    url_relative="pass_through",
    link_rel=None,
    strip_comments=True,
)


def clean(html: str) -> str:
    return NO_SRC.sub("", _cleaner.clean(html))
