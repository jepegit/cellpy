"""Fail if a ``See `name` `` docstring reference does not resolve (#993).

#968 swapped Sphinx roles for markdown code spans and dropped the module path
from about half the cross-references. The rendered page survives that (a reader
clicks or searches); every other consumer — IDEs, ``help()``, docs tooling,
cellpy-mcp's ``describe_api`` — needs the dotted path to follow the pointer to
the delegate that actually documents the arguments.

``tests/test_no_sphinx_doc_roles.py`` guards the *syntax*; this module guards
the *targets*.
"""

from __future__ import annotations

import importlib
import pathlib
import re

import pytest

CELLPY_SRC = pathlib.Path(__file__).resolve().parents[1] / "cellpy"

REFERENCE_RE = re.compile(r"See `([A-Za-z_][A-Za-z0-9_.]*)`")


def _resolve(dotted: str):
    """Import the longest importable prefix, then walk the rest as attributes."""
    parts = dotted.split(".")
    for stop in range(len(parts), 0, -1):
        try:
            target = importlib.import_module(".".join(parts[:stop]))
        except ImportError:
            continue
        for attribute in parts[stop:]:
            target = getattr(target, attribute)
        return target
    raise ImportError(f"no importable module in {dotted!r}")


def _references():
    for path in sorted(CELLPY_SRC.rglob("*.py")):
        where = path.relative_to(CELLPY_SRC).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            for match in REFERENCE_RE.finditer(line):
                yield f"{where}:{lineno}", match.group(1)


@pytest.mark.essential
def test_every_see_reference_names_an_importable_target():
    unresolved: list[str] = []
    for where, dotted in _references():
        if "." not in dotted:
            unresolved.append(f"{where}: `{dotted}` is a bare name, give the dotted path")
            continue
        try:
            _resolve(dotted)
        except (ImportError, AttributeError) as exc:
            unresolved.append(f"{where}: `{dotted}` does not resolve ({exc})")

    assert not unresolved, (
        "docstring cross-references must name an importable target:\n"
        + "\n".join(unresolved)
    )


@pytest.mark.essential
def test_the_thinnest_delegates_point_at_their_documentation():
    """`get_cap`, `to_csv` and `to_excel` carry the most undocumented arguments."""
    from cellpy.readers.cellreader import CellpyCell

    for name in ["get_cap", "to_csv", "to_excel"]:
        match = REFERENCE_RE.search(getattr(CellpyCell, name).__doc__ or "")
        assert match, f"CellpyCell.{name} has no cross-reference to follow"
        delegate = _resolve(match.group(1))
        assert delegate.__doc__, f"{match.group(1)} has no docstring to borrow"
