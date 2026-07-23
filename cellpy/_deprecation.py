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
    # Legacy header attribute access (headers_normal.voltage_txt, hdr_steps.cycle,
    # hdr_summary[...]) is shimmed to the native cellpycore schema names at the
    # native-headers flip (D6). One summary row here; the shim warns per attribute
    # at runtime (cellpy.parameters.legacy_header_shim).
    _register(
        "legacy header attribute access (headers_normal / _summary / _step_table)",
        "c.schema.raw / c.schema.steps / c.schema.summary",
        removal="2.1",
        introduced="2.0",
    )
    # cellpy.utils.easyplot was removed in 2.0 (#544); it is no longer a
    # pending deprecation, so it is dropped from the registry / DEPRECATIONS.md.

    # ICA redesign (#566). The 1.x entry points survive as shims over the new
    # pure core and reproduce the old numbers exactly; they warn per call site.
    _register(
        "ica.Converter",
        "cellpy.ica.transform_half_cycle with IcaOptions",
        removal="2.1",
    )
    _register(
        "ica.dqdv_cycle",
        "cellpy.ica.dqdv (returns the specced long frame)",
        removal="2.1",
    )
    _register(
        "ica.dqdv_cycles",
        "cellpy.ica.dqdv (returns the specced long frame)",
        removal="2.1",
    )
    _register(
        "ica.dqdv_np",
        "cellpy.ica.transform_half_cycle with IcaOptions",
        removal="2.1",
    )
    _register("ica.dqdv(cycle=...)", "cellpy.ica.dqdv(cycles=...)", removal="2.1")
    _register(
        "ica.dqdv(label_direction=...)",
        "the direction column, which the specced frame always carries",
        removal="2.1",
    )
    _register(
        "ica.dqdv(split=... / tidy=...)",
        "cellpy.ica.dqdv(direction=...) and cellpy.ica.to_wide()",
        removal="2.1",
    )
    # The ICA output frame carries both spellings for one release.
    _register(
        "the 'dq' column of the ica output frame",
        "the 'dqdv' column of the same frame",
        removal="2.1",
    )

    # Plotting redesign (#567). The old implementation behind this name was
    # unconditionally broken (its first statement unpacked a None); the name
    # now delegates to summary_plot and goes away in 2.1.
    _register(
        "plotutils.summary_plot_legacy",
        "cellpy.utils.plotutils.summary_plot (same figures, same options)",
        removal="2.1",
    )
    # Stage 1 (#639): interactive= is a warn_once alias for backend=.
    _register(
        "summary_plot(interactive=...)",
        'backend="plotly"|"matplotlib"',
        removal="2.1",
    )
    # Stage 2 (#646): cycles_plot backend= + range spelling.
    _register(
        "cycles_plot(interactive=...)",
        'backend="plotly"|"matplotlib"',
        removal="2.1",
    )
    _register(
        "cycles_plot(xlim=...)",
        "cycles_plot(x_range=...)",
        removal="2.1",
    )
    _register(
        "cycles_plot(ylim=...)",
        "cycles_plot(y_range=...)",
        removal="2.1",
    )
    # Stage 2 (#647): raw_plot / cycle_info_plot backend=.
    _register(
        "raw_plot(interactive=...)",
        'backend="plotly"|"matplotlib"',
        removal="2.1",
    )
    _register(
        "cycle_info_plot(interactive=...)",
        'backend="plotly"|"matplotlib"',
        removal="2.1",
    )


if __name__ == "__main__":
    _seed_known_deprecations()
    write_deprecations_md(Path(__file__).resolve().parents[1] / "DEPRECATIONS.md")
