#!/usr/bin/env python3
"""Mechanical prms section → cellpy.config migration (issue #453 M2)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "cellpy"

SKIP = {
    ROOT / "parameters" / "_shim.py",
    ROOT / "parameters" / "prms.py",
}

REPLACEMENTS = [
    ("prmreader.prms.Paths", "config.paths"),
    ("prmreader.prms.Batch", "config.batch"),
    ("prms.CellInfo", "config.defaults.cell_info"),
    ("prms.Materials", "config.defaults.materials"),
    ("prms.FileNames", "config.file_names"),
    ("prms.DbCols", "config.db_cols"),
    ("prms.Instruments", "config.instruments"),
    ("prms.Reader", "config.reader"),
    ("prms.Paths", "config.paths"),
    ("prms.Batch", "config.batch"),
    ("prms.Db", "config.db"),
]

CONFIG_IMPORT = "import cellpy.config as config\n"


def needs_config(text: str) -> bool:
    return "config." in text and "import cellpy.config as config" not in text


def migrate_file(path: Path) -> bool:
    if path in SKIP or not path.suffix == ".py":
        return False
    original = path.read_text(encoding="utf-8")
    text = original
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text == original:
        return False
    if needs_config(text):
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for idx, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = idx + 1
            elif line.strip() and not line.startswith("#"):
                break
        lines.insert(insert_at, CONFIG_IMPORT)
        text = "".join(lines)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    changed = []
    for path in sorted(ROOT.rglob("*.py")):
        if migrate_file(path):
            changed.append(path.relative_to(ROOT.parent))
    print(f"Updated {len(changed)} files")
    for item in changed:
        print(f"  {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
