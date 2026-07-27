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
    # make_new_cell was removed in 2.1 (E3, #715) -- use CellpyCell.vacant.
    # Legacy header attribute access (headers_normal / _summary / _step_table,
    # the legacy_header_shim) was removed in 2.1 (E3, #715) -- use c.schema.raw /
    # c.schema.steps / c.schema.summary. No longer registered here.

    # cellpy.utils.easyplot was removed in 2.0 (#544); it is no longer a
    # pending deprecation, so it is dropped from the registry / DEPRECATIONS.md.

    # ICA 1.x shims (Converter, dqdv_cycle/cycles/np, dqdv split=/tidy=/cycle=/
    # label_direction=, the duplicate 'dq' column) were removed in 2.1 (E2, #714)
    # -- no longer registered here.

    # Plotting shims (interactive=, xlim/ylim, backend="seaborn", summary_plot_legacy)
    # were removed in 2.1 (E1, #713) -- no longer registered here.

    # The prms.* global-mutation shim (prms.Paths/Reader/... -> cellpy.config.*)
    # was removed in 2.1 (E5, #717) -- use cellpy.config (e.g. config.paths.x = y)
    # or cellpy.config.override(...). Not a pending deprecation, so not listed.

    # KEPT past 2.1 (E5, #717): the CellpyCell.mass / .nom_cap / .nom_cap_specifics
    # property facades are beloved and cheap -- deliberately NOT deprecated, so
    # they are intentionally absent from this table.

    # ocv_rlx: MultiCycleOcvFit.data/set_data were renamed to cell/set_cell in
    # 2.1 (#709); the old names stay as deprecated aliases until 2.2. Seeded so
    # the table lists them without needing to trigger the runtime warning.
    _register(
        "MultiCycleOcvFit.data",
        "MultiCycleOcvFit.cell",
        removal="2.2",
        introduced="2.1",
    )
    _register(
        "MultiCycleOcvFit.set_data",
        "MultiCycleOcvFit.set_cell",
        removal="2.2",
        introduced="2.1",
    )


if __name__ == "__main__":
    _seed_known_deprecations()
    write_deprecations_md(Path(__file__).resolve().parents[1] / "DEPRECATIONS.md")
