"""Deprecation helper: once-per-call-site warnings and DEPRECATIONS.md registry."""

from __future__ import annotations

import inspect
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Tuple

CallSite = Tuple[str, str, int]


@dataclass(frozen=True)
class DeprecationEntry:
    name: str
    replacement: str
    removal: str
    introduced: str = "2.0"


_REGISTRY: Dict[str, DeprecationEntry] = {}
_WARNED_SITES: Set[CallSite] = set()


def _register(name: str, replacement: str, *, removal: str = "2.1", introduced: str = "2.0") -> None:
    if name not in _REGISTRY:
        _REGISTRY[name] = DeprecationEntry(
            name=name,
            replacement=replacement,
            removal=removal,
            introduced=introduced,
        )


def warn_once(
    name: str,
    replacement: str,
    *,
    removal: str = "2.1",
    introduced: str = "2.0",
    stacklevel: int = 2,
) -> None:
    """Emit a DeprecationWarning once per call site and register in the table."""
    _register(name, replacement, removal=removal, introduced=introduced)

    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        site: CallSite = (name, "<unknown>", 0)
    else:
        caller = frame.f_back
        site = (name, caller.f_code.co_filename, caller.f_lineno)

    if site in _WARNED_SITES:
        return
    _WARNED_SITES.add(site)

    message = f"{name} is deprecated; use {replacement} instead (removed in {removal})"
    warnings.warn(message, DeprecationWarning, stacklevel=stacklevel + 1)


def get_registry() -> Dict[str, DeprecationEntry]:
    """Return a copy of the registered deprecations (for tests and rendering)."""
    return dict(_REGISTRY)


def render_deprecations_md() -> str:
    """Render the deprecation table as markdown."""
    lines = [
        "# Deprecations",
        "",
        "Auto-generated table of registered deprecations. Regenerate with:",
        "",
        "```shell",
        "uv run python -m cellpy._deprecation",
        "```",
        "",
        "| Name | Replacement | Introduced | Removal |",
        "| --- | --- | --- | --- |",
    ]
    for entry in sorted(_REGISTRY.values(), key=lambda item: item.name):
        lines.append(
            f"| `{entry.name}` | `{entry.replacement}` | {entry.introduced} | {entry.removal} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_deprecations_md(path: str | Path) -> None:
    """Write the rendered deprecation table to *path*."""
    Path(path).write_text(render_deprecations_md(), encoding="utf-8")


def _seed_known_deprecations() -> None:
    """Register deprecations that exist before any runtime call (for doc generation)."""
    _register("make_new_cell", "CellpyCell.vacant", removal="2.1")
    _register(
        "cellpy.utils.easyplot",
        "cellpy.utils.plotutils and cellpy.utils.collectors",
        removal="2.0",
        introduced="1.1",
    )


if __name__ == "__main__":
    _seed_known_deprecations()
    write_deprecations_md(Path(__file__).resolve().parents[1] / "DEPRECATIONS.md")
