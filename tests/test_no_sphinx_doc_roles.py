"""Fail if Sphinx interpreted-text roles reappear in library source (#967).

Zensical + mkdocstrings (Google style) renders ``:class:`Name``` as literal
text. Docstrings should use markdown code spans instead.
"""

from __future__ import annotations

import pathlib
import re

CELLPY_SRC = pathlib.Path(__file__).resolve().parents[1] / "cellpy"

ROLE_RE = re.compile(
    r":(?:class|meth|func|mod|attr|data|exc|obj|paramref):`[^`]+`"
)


def test_no_sphinx_doc_roles_in_cellpy_source():
    hits: list[str] = []
    for path in sorted(CELLPY_SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(CELLPY_SRC).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if ROLE_RE.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()[:120]}")

    assert not hits, "Sphinx roles leak into Zensical docs; use markdown `Name`:\n" + "\n".join(
        hits
    )
