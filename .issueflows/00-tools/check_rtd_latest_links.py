#!/usr/bin/env python3
"""Assert Read the Docs ``latest`` URLs in docs resolve to built site paths.

Also checks ``<!-- agent-doc: <src.md> -->`` comments: the source file must
exist under ``docs/``, and the next ``latest`` URL in that block must match
``…/en/latest/<src without .md>/``.

Usage (from the cellpy repo root, after ``zensical build``)::

    uv run .issueflows/00-tools/check_rtd_latest_links.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RTD_LATEST = re.compile(
    r"https://cellpy\.readthedocs\.io/en/latest/([^\s)\]\"'<>]+)"
)
AGENT_DOC = re.compile(r"<!--\s*agent-doc:\s*([^\s]+)\s*-->")
SKIP_DIR_NAMES = frozenset({"_old_docs"})


def _normalize_url_path(raw: str) -> str:
    path = raw.split("#", 1)[0].split("?", 1)[0]
    path = path.rstrip(".,;:")
    return path.rstrip("/")


def _iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    docs = root / "docs"
    if docs.is_dir():
        for path in docs.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix in {".md", ".txt"}:
                files.append(path)
    agents = root / "AGENTS.md"
    if agents.is_file():
        files.append(agents)
    return sorted(files)


def _site_candidates(site: Path, url_path: str) -> list[Path]:
    if not url_path:
        return [site / "index.html", site]
    if Path(url_path).suffix:
        return [site / url_path]
    return [
        site / url_path / "index.html",
        site / f"{url_path}.html",
        site / url_path,
    ]


def _exists_on_site(site: Path, url_path: str) -> bool:
    return any(candidate.exists() for candidate in _site_candidates(site, url_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--site",
        type=Path,
        default=None,
        help="Built site directory (default: <root>/site)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    site = (args.site or (root / "site")).resolve()
    docs = root / "docs"

    if not site.exists():
        print(f"error: built site not found at {site}", file=sys.stderr)
        print("run: uv run --group docs zensical build", file=sys.stderr)
        return 1

    missing_pages: list[str] = []
    comment_errors: list[str] = []

    for path in _iter_text_files(root):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)

        for match in RTD_LATEST.finditer(text):
            url_path = _normalize_url_path(match.group(1))
            if not _exists_on_site(site, url_path):
                missing_pages.append(f"{rel}: /{url_path}")

        for comment in AGENT_DOC.finditer(text):
            src = comment.group(1).strip()
            src_file = docs / src
            if not src_file.is_file():
                comment_errors.append(f"{rel}: agent-doc source missing: {src}")
                continue
            expected = src.removesuffix(".md")
            rest = text[comment.end() :]
            next_url = RTD_LATEST.search(rest)
            if next_url is None:
                comment_errors.append(f"{rel}: no latest URL after agent-doc {src}")
                continue
            actual = _normalize_url_path(next_url.group(1))
            if actual != expected:
                comment_errors.append(
                    f"{rel}: agent-doc {src} points at /{actual}, expected /{expected}"
                )

    if missing_pages or comment_errors:
        if missing_pages:
            print("latest URLs missing from site/:", file=sys.stderr)
            for item in missing_pages:
                print(f"  {item}", file=sys.stderr)
        if comment_errors:
            print("agent-doc comment errors:", file=sys.stderr)
            for item in comment_errors:
                print(f"  {item}", file=sys.stderr)
        return 1

    print("all latest RTD URLs and agent-doc comments resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
