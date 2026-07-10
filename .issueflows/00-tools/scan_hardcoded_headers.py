#!/usr/bin/env python3
"""AST scan for hard-coded column-header string literals.

Compares string literals in column-access-like contexts against canonical header
values from ``cellpy.parameters.internal_settings``.

Usage (from cellpy repo root)::

    uv run .issueflows/00-tools/scan_hardcoded_headers.py cellpy/filters cellpy/exporters

Emits a markdown findings table to stdout.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure cellpy is importable when run via uv from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cellpy.parameters import internal_settings as iset  # noqa: E402


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    literal: str
    context: str
    header_class: str


def _canonical_values() -> dict[str, set[str]]:
    groups = {
        "HeadersNormal": iset.get_headers_normal(),
        "HeadersSummary": iset.get_headers_summary(),
        "HeadersStepTable": iset.get_headers_step_table(),
        "HeadersJournal": iset.get_headers_journal(),
    }
    out: dict[str, set[str]] = {}
    for name, obj in groups.items():
        vals: set[str] = set()
        for key, val in vars(obj).items():
            if key.startswith("_"):
                continue
            if isinstance(val, str) and val:
                vals.add(val)
        out[name] = vals
    return out


def _all_canonical(flat: dict[str, set[str]]) -> dict[str, str]:
    """Map literal -> header class name (first match)."""
    mapping: dict[str, str] = {}
    for cls, vals in flat.items():
        for v in vals:
            mapping.setdefault(v, cls)
    return mapping


def _context_label(node: ast.AST, parent: ast.AST | None) -> str:
    if isinstance(parent, ast.Subscript) and parent.slice is node:
        return "subscript key"
    if isinstance(parent, ast.keyword):
        return f"kwarg {parent.arg!r}"
    if isinstance(parent, ast.Compare):
        return "comparison"
    if isinstance(parent, ast.Dict):
        return "dict key/value"
    if isinstance(parent, ast.Tuple) and isinstance(parent.ctx, ast.Load):
        return "tuple default"
    if isinstance(parent, ast.List) and isinstance(parent.ctx, ast.Load):
        return "list literal"
    return type(parent).__name__ if parent else "literal"


class _Visitor(ast.NodeVisitor):
    def __init__(self, path: Path, canonical: dict[str, str]) -> None:
        self.path = path
        self.canonical = canonical
        self.findings: list[Finding] = []
        self._parent_stack: list[ast.AST] = []

    def visit(self, node: ast.AST) -> None:
        self._parent_stack.append(node)
        parent = self._parent_stack[-2] if len(self._parent_stack) > 1 else None

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lit = node.value
            if lit in self.canonical and self._is_interesting(parent, node):
                self.findings.append(
                    Finding(
                        path=self.path,
                        line=node.lineno,
                        literal=lit,
                        context=_context_label(node, parent),
                        header_class=self.canonical[lit],
                    )
                )

        self.generic_visit(node)
        self._parent_stack.pop()

    def _is_interesting(self, parent: ast.AST | None, node: ast.Constant) -> bool:
        if parent is None:
            return False
        # Column subscript: df["col"]
        if isinstance(parent, ast.Subscript) and parent.slice is node:
            return True
        # Keyword args to pandas-ish calls
        if isinstance(parent, ast.keyword) and parent.arg in {
            "by",
            "subset",
            "x",
            "y",
            "color",
            "column",
            "index",
            "columns",
        }:
            return True
        # Default column tuples in signatures / calls
        if isinstance(parent, (ast.Tuple, ast.List)):
            return True
        # String keys in small dicts used as rename maps — conservative
        if isinstance(parent, ast.Dict):
            return True
        return False


def _scan_file(path: Path, canonical: dict[str, str]) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        print(f"WARN: skip {path}: {exc}", file=sys.stderr)
        return []
    visitor = _Visitor(path, canonical)
    visitor.visit(tree)
    return visitor.findings


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _emit_markdown(findings: list[Finding], repo_root: Path) -> None:
    if not findings:
        print("No hard-coded canonical header literals in column-access contexts.")
        return

    print("| File | Line | Literal | Header class | Context |")
    print("|---|---|---|---|---|")
    for f in sorted(findings, key=lambda x: (x.path, x.line, x.literal)):
        print(
            f"| `{_rel(f.path, repo_root)}` | {f.line} | `{f.literal}` | "
            f"`{f.header_class}` | {f.context} |"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    flat = _canonical_values()
    canonical = _all_canonical(flat)

    files: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)

    all_findings: list[Finding] = []
    for f in files:
        if f.name == "__init__.py" and f.stat().st_size < 600:
            continue
        all_findings.extend(_scan_file(f, canonical))

    _emit_markdown(all_findings, args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
