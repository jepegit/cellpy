#!/usr/bin/env python3
"""Fail on relative links in ``docs/**/*.md`` whose target file does not exist.

Zensical reports broken links between *pages*, but a link to any other file
(``.ipynb``, ``.xlsx``, an image) is copied through unchecked. This catches
those, e.g. a rendered tutorial still pointing at ``07_custom_loaders.ipynb``
(#1023).

Usage (from the cellpy repo root)::

    uv run .issueflows/00-tools/check_docs_relative_links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path("docs")
SKIP_DIR_NAMES = frozenset({"_old_docs"})

#: ``[text](target)`` and ``![alt](target)``; ignores the optional title.
LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
#: ``src="…"`` / ``href="…"`` in embedded HTML.
HTML_LINK = re.compile(r"""\b(?:src|href)=["']([^"']+)["']""")
FENCE = re.compile(r"^(```|~~~)")


def _targets(text: str):
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line.lstrip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for pattern in (LINK, HTML_LINK):
            for match in pattern.finditer(line):
                yield lineno, match.group(1)


def _is_external(target: str) -> bool:
    return (
        target.startswith(("#", "/", "mailto:", "data:"))
        or re.match(r"^[a-z][a-z0-9+.-]*://", target) is not None
    )


def main() -> int:
    broken: list[str] = []
    for page in sorted(DOCS.rglob("*.md")):
        if any(part in SKIP_DIR_NAMES for part in page.parts):
            continue
        for lineno, target in _targets(page.read_text(encoding="utf-8")):
            if _is_external(target):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            if not path:
                continue
            resolved = (page.parent / path).resolve()
            if not resolved.exists():
                broken.append(f"{page}:{lineno}: {target}")
    for line in broken:
        print(line)
    if broken:
        print(f"{len(broken)} broken relative link(s)", file=sys.stderr)
        return 1
    print("all relative links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
