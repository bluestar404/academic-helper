"""Regex-based escaping for user strings before LaTeX compilation."""

from __future__ import annotations

import re

DEFAULT_LATEX_ESCAPE_MAP: dict[str, str] = {
    "%": r"\%",
    "&": r"\&",
    "$": r"\$",
    "_": r"\_",
}


def build_escape_patterns(
    escape_map: dict[str, str],
) -> list[tuple[re.Pattern[str], str]]:
    """Compile substitution patterns; longest keys first for multi-char keys."""
    ordered_keys = sorted(escape_map.keys(), key=len, reverse=True)
    return [
        (re.compile(re.escape(key)), escape_map[key]) for key in ordered_keys
    ]


def sanitize_text(
    text: str,
    *,
    escape_map: dict[str, str] | None = None,
) -> str:
    """Escape layout-breaking characters; returns a new string."""
    patterns = build_escape_patterns(escape_map or DEFAULT_LATEX_ESCAPE_MAP)
    result = text
    for pattern, replacement in patterns:
        result = pattern.sub(replacement, result)
    return result


def sanitize_optional(
    text: str | None,
    *,
    escape_map: dict[str, str] | None = None,
) -> str | None:
    if text is None:
        return None
    return sanitize_text(text, escape_map=escape_map)
