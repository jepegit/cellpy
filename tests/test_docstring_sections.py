"""Docstring section titles that the API docs can render (#1128).

griffe's Google-style parser only recognises ``Examples:``. A singular
``Example:`` falls through to a generic admonition whose body is rendered as
markdown, so ``>>>`` prompts become nested blockquotes and the code loses its
highlighting in the API reference. This test fails on the first offender so
the mistake cannot come back through a copy-pasted docstring.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "cellpy"
_SINGULAR_EXAMPLE = re.compile(r"^\s*Example:\s*$", re.MULTILINE)


def _docstring_nodes(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                yield node, doc


def _singular_example_sections() -> list[str]:
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node, doc in _docstring_nodes(tree):
            if _SINGULAR_EXAMPLE.search(doc):
                line = getattr(node, "lineno", 1)
                hits.append(f"{path.relative_to(SRC.parent.parent)}:{line}")
    return hits


@pytest.mark.essential
def test_docstrings_use_plural_examples_section():
    hits = _singular_example_sections()
    assert not hits, "Use 'Examples:' (griffe does not parse 'Example:'):\n  " + "\n  ".join(hits)
