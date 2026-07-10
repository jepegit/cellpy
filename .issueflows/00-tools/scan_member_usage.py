#!/usr/bin/env python3
"""AST scan for Data / CellpyCell member access in Python source trees.

Usage (from cellpy repo root)::

    uv run .issueflows/00-tools/scan_member_usage.py cellpy/filters cellpy/exporters

Emits a markdown summary to stdout. Used for Stage-0 consumer inventory reports.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

# Receivers treated as non-cellpy (false-positive guards from the utils report).
_SKIP_RECEIVER_ROOTS = frozenset(
    {
        "logging",
        "logger",
        "pd",
        "np",
        "plt",
        "fig",
        "json",
        "os",
        "sys",
        "pathlib",
        "re",
        "warnings",
        "shutil",
        "stat",
        "tempfile",
        "time",
        "fnmatch",
    }
)

_CELL_RECEIVER_ROOTS = frozenset({"cell", "c", "cpobj", "cell_data", "cellpydata"})

_IO_MEMBERS = frozenset({"to_csv", "to_bdf", "save", "load", "from_raw"})

_DATA_MEMBERS = frozenset(
    {
        "raw",
        "steps",
        "summary",
        "raw_units",
        "meta_common",
        "raw_data_files",
        "loaded_from",
        "nom_cap",
        "cell_name",
        "loading",
        "empty",
        "mass",
        "tot_mass",
    }
)

_CELLPYCELL_MEMBERS = frozenset(
    {
        "data",
        "empty",
        "cell_name",
        "mass",
        "active_mass",
        "tot_mass",
        "nominal_capacity",
        "nom_cap_specifics",
        "raw_units",
        "cellpy_units",
        "headers_normal",
        "headers_summary",
        "headers_step_table",
        "get_cap",
        "get_ccap",
        "get_dcap",
        "get_ocv",
        "get_cycle_numbers",
        "make_summary",
        "make_step_table",
        "save",
        "load",
        "from_raw",
        "to_csv",
        "to_bdf",
    }
)


@dataclass(frozen=True)
class Hit:
    path: Path
    line: int
    chain: str
    member: str
    target: str  # "CellpyCell" or "Data"


def _receiver_root(node: ast.AST) -> str | None:
    """Return the leftmost name in an attribute chain, if it is a simple Name."""
    cur = node
    while isinstance(cur, ast.Attribute):
        cur = cur.value
    if isinstance(cur, ast.Name):
        return cur.id
    return None


def _attr_chain(node: ast.Attribute) -> str:
    parts: list[str] = []
    cur: ast.AST = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    elif isinstance(cur, ast.Call):
        parts.append("<call>")
    else:
        parts.append("<expr>")
    return ".".join(reversed(parts))


def _classify_member(chain: str, member: str, root: str | None) -> str | None:
    if member in _DATA_MEMBERS and ".data." in chain:
        return "Data"
    if member not in _CELLPYCELL_MEMBERS:
        return None
    if root in _SKIP_RECEIVER_ROOTS:
        return None
    if member in _IO_MEMBERS and root not in _CELL_RECEIVER_ROOTS:
        return None
    if member == "empty" and root not in _CELL_RECEIVER_ROOTS:
        return None
    if root not in _CELL_RECEIVER_ROOTS:
        return None
    return "CellpyCell"


def _scan_file(path: Path) -> list[Hit]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        print(f"WARN: skip {path}: {exc}", file=sys.stderr)
        return []

    hits: list[Hit] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        root = _receiver_root(node)
        if root in _SKIP_RECEIVER_ROOTS:
            continue
        target = _classify_member(_attr_chain(node), node.attr, root)
        if target is None:
            continue
        hits.append(
            Hit(
                path=path,
                line=node.lineno,
                chain=_attr_chain(node),
                member=node.attr,
                target=target,
            )
        )
    return hits


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _emit_markdown(hits: list[Hit], repo_root: Path) -> None:
    if not hits:
        print("No Data / CellpyCell member accesses found.")
        return

    by_member: dict[tuple[str, str], list[Hit]] = {}
    for hit in hits:
        key = (hit.target, hit.member)
        by_member.setdefault(key, []).append(hit)

    print("| Target | Member | Sites | Notes |")
    print("|---|---|---|---|")
    for (target, member), group in sorted(by_member.items()):
        sites = ", ".join(
            f"`{_rel(h.path, repo_root)}:{h.line}`"
            for h in sorted(group, key=lambda x: (x.path, x.line))
        )
        chains = sorted({h.chain for h in group})
        note = f"receivers: {', '.join(f'`{c}`' for c in chains[:4])}"
        if len(chains) > 4:
            note += f" (+{len(chains) - 4} more)"
        print(f"| `{target}` | `{member}` | {sites} | {note} |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Package directories or .py files to scan",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repo root for relative paths in output (default: cwd)",
    )
    args = parser.parse_args(argv)

    files: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)

    all_hits: list[Hit] = []
    for f in files:
        if f.name == "__init__.py" and f.stat().st_size < 600:
            continue
        all_hits.extend(_scan_file(f))

    # Deduplicate identical line+member
    seen: set[tuple[str, int, str]] = set()
    unique: list[Hit] = []
    for h in all_hits:
        key = (_rel(h.path, args.repo_root), h.line, h.member)
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)

    _emit_markdown(unique, args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
