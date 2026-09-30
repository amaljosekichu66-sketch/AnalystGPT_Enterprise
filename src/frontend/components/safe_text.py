"""
Escaping helpers for rendering untrusted text in Streamlit (SEC-07).

LLM output is steerable by dataset content (a cell value can carry prompt
instructions), so it must be treated like user input:

- `html_text()` for anything placed inside `unsafe_allow_html=True` markup;
- `markdown_text()` for anything rendered as markdown. Markdown is not
  HTML-safe by itself: `![x](https://host/?q=...)` makes the viewer's browser
  fetch an attacker URL, and `[x](javascript:...)` is a live link. Bare URLs
  are defused too, since GFM would autolink them.
"""

from __future__ import annotations

import html
import re
from typing import Any

_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|~])")

#: GFM turns bare `https://...` and `www....` into links (I15). A zero-width
#: joiner after the scheme or `www` keeps the text but stops the autolink.
_AUTOLINK = re.compile(r"(?i)\b(https?|ftp|mailto|javascript|data)(:)|\b(www)(\.)")
_ZWJ = "\u200d"


#: Markdown punctuation encoded as numeric entities inside HTML blocks. They
#: display as the same characters, but markdown can no longer parse them.
#: One table, applied in a single pass, so no entity is ever re-escaped.
_HTML_BLOCK_ESCAPES = str.maketrans(
    {
        **{c: f"&#{ord(c)};" for c in "\\`*_{}[]()#+!|~"},
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }
)


def html_text(value: Any) -> str:
    """
    Escape a value for interpolation into `unsafe_allow_html` markup.

    Besides HTML escaping, newlines are collapsed (a blank line ends
    CommonMark's raw-HTML block, after which markdown would be parsed again)
    and markdown punctuation is entity-encoded.
    """
    text = " ".join(("" if value is None else str(value)).split())
    return text.translate(_HTML_BLOCK_ESCAPES)


def markdown_text(value: Any) -> str:
    """Escape a value so markdown renders it literally (no tags, links, images or emphasis)."""
    # HTML-escape first (tags become &lt; / &gt; entities, which markdown renders
    # as text) without quote entities, whose '#' would otherwise be escaped too.
    text = html.escape("" if value is None else str(value), quote=False)
    text = _MARKDOWN_SPECIAL.sub(r"\\\1", text)
    return _AUTOLINK.sub(lambda m: f"{m.group(1) or m.group(3)}{_ZWJ}{m.group(2) or m.group(4)}", text)
