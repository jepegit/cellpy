"""Warn-only index lint (Polars Phase A / Phase D preparation, issue #457).

Scans the ``cellpy`` package source for pandas index idioms that violate the
*keys live in columns, never in an index* rule (polars plan decision 3).
During Phase A the lint only **warns** — it must never fail the build — so the
count can be watched shrinking as modules are ported. Phase D flips it to a
hard ban outside the sanctioned boundary modules.

Boundary allowlist (index use is sanctioned there):
- ``readers/cellpy_file/`` — the frozen v8 storage format keeps its stored
  index conventions (write-side promotion, where-clauses on the index).
- ``parameters/legacy/`` — legacy-format upgrade shims.
"""

from __future__ import annotations

import pathlib
import re
import warnings

CELLPY_SRC = pathlib.Path(__file__).resolve().parents[1] / "cellpy"

# Sanctioned boundary locations (relative, forward-slash) — index use allowed.
ALLOWED_PARTS = (
    "readers/cellpy_file/",
    "parameters/legacy/",
)

# Idioms that put or keep keys in an index.
PATTERNS = (
    re.compile(r"\.set_index\("),
    re.compile(r"\.loc\["),
    re.compile(r"\.iloc\["),
    re.compile(r"\.iat\["),
)


def _iter_source_files():
    for path in sorted(CELLPY_SRC.rglob("*.py")):
        rel = path.relative_to(CELLPY_SRC).as_posix()
        if any(rel.startswith(part) or f"/{part}" in rel for part in ALLOWED_PARTS):
            continue
        yield rel, path


def test_index_lint_warn_only():
    """Count index idioms outside the boundary modules; warn, never fail."""
    hits: list[str] = []
    for rel, path in _iter_source_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel}:{lineno}: {stripped[:100]}")
                    break

    if hits:
        preview = "\n  ".join(hits[:15])
        warnings.warn(
            f"[index-lint] {len(hits)} pandas index idiom(s) outside the "
            f"boundary modules (keys-live-in-columns rule, #457; "
            f"warn-only until polars plan Phase D). First hits:\n  {preview}",
            stacklevel=1,
        )
    # warn-only: the test never fails on hits — Phase D will flip this.
    assert True
