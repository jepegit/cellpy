"""Named plot families — the declarative replacement for the old
``SummaryPlotInfo._create_col_info`` column table (#636 / epic #567).

Column names for summary families are header-bound (they depend on
``c.headers_summary``), so each family carries a small resolver rather than a
frozen list of strings. Non-summary families (e.g. ``cycles`` for
``cycles_plot``, #646) register with ``extras["entry_point"]`` so
``families(entry_point=...)`` / the summary oracle stay scoped.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from cellpy.plotting.spec import PanelSpec

logger = logging.getLogger(__name__)

ColumnsFn = Callable[[Any], list[str]]
TransformsFn = Callable[[Any, Callable[..., Any]], dict[str, Any]]


@dataclass(frozen=True)
class PlotFamily:
    """One named ``summary_plot(y=...)`` figure family."""

    name: str
    description: str
    column_builder: ColumnsFn
    mode: Optional[str] = None
    supports_formation: bool = True
    supports_cv_split: bool = False
    panels: tuple[PanelSpec, ...] = ()
    transforms_builder: Optional[TransformsFn] = None
    extras: dict[str, Any] = field(default_factory=dict)

    def columns(self, hdr: Any) -> list[str]:
        return list(self.column_builder(hdr))

    def transforms(self, hdr: Any, normalize_col: Callable[..., Any]) -> dict[str, Any]:
        if self.transforms_builder is None:
            return {}
        return dict(self.transforms_builder(hdr, normalize_col))


_FAMILIES: dict[str, PlotFamily] = {}


def get(name: str) -> PlotFamily:
    """Return the registered family for *name*.

    Raises:
        ValueError: *name* is not registered. The message lists known families.
    """
    try:
        return _FAMILIES[name]
    except KeyError as exc:
        known = ", ".join(sorted(_FAMILIES))
        raise ValueError(
            f"unknown plot family {name!r} (known: {known}). "
            f"Use _register_family to add new families."
        ) from exc


def _entry_point(family: PlotFamily) -> str:
    """Public entry that owns this family (default: ``summary_plot``)."""
    return (family.extras or {}).get("entry_point", "summary_plot")


def families(*, entry_point: Optional[str] = None) -> list[tuple[str, str]]:
    """Return ``(name, description)`` for registered families, in registration order.

    Pass ``entry_point="summary_plot"`` (or ``"cycles_plot"``, …) to restrict the
    list to one public plot entry. ``None`` returns every registered family.
    """
    out: list[tuple[str, str]] = []
    for family in _FAMILIES.values():
        if entry_point is not None and _entry_point(family) != entry_point:
            continue
        out.append((family.name, family.description))
    return out


def iter_families(*, entry_point: Optional[str] = None) -> list[PlotFamily]:
    """Return registered families in registration order.

    See :func:`families` for the optional ``entry_point`` filter (#646).
    """
    if entry_point is None:
        return list(_FAMILIES.values())
    return [f for f in _FAMILIES.values() if _entry_point(f) == entry_point]


def _register_family(family: PlotFamily) -> None:
    """Provisionally register (or overwrite) a :class:`PlotFamily`.

    Public promotion of this hook waits for a release of in-tree use (#567).
    """
    if family.name in _FAMILIES:
        logger.warning("plotting.registry: overwriting registered family %r", family.name)
    _FAMILIES[family.name] = family


# --- column / transform builders (mechanical port of _create_col_info) --------


def _cap_raw(hdr: Any) -> list[str]:
    return [hdr.charge_capacity_raw, hdr.discharge_capacity_raw]


def _caps(hdr: Any, mode: str) -> list[str]:
    return [col + f"_{mode}" for col in _cap_raw(hdr)]


def _split(cols: list[str]) -> list[str]:
    return cols + [col + "_cv" for col in cols] + [col + "_non_cv" for col in cols]


def _cumloss_columns(hdr: Any, mode: str) -> list[str]:
    return [
        hdr.charge_capacity + f"_{mode}" + "_cv",
        hdr.cumulated_discharge_capacity_loss + f"_{mode}",
        hdr.discharge_capacity + f"_{mode}",
        hdr.coulombic_efficiency,
    ]


def _fullcell_columns(hdr: Any, mode: str) -> list[str]:
    return [
        hdr.charge_capacity + f"_{mode}" + "_cv",
        hdr.discharge_capacity + f"_{mode}",
        "mod_01_" + hdr.discharge_capacity + f"_{mode}",
        hdr.coulombic_efficiency,
    ]


def _cumloss_transforms(hdr: Any, normalize_col: Callable[..., Any], mode: str) -> dict[str, Any]:
    key = hdr.cumulated_discharge_capacity_loss + f"_{mode}"
    return {key: {(2, key): normalize_col}}


def _retention_transforms(hdr: Any, normalize_col: Callable[..., Any], mode: str) -> dict[str, Any]:
    mod_key = "mod_01_" + hdr.discharge_capacity + f"_{mode}"
    retention_key = hdr.discharge_capacity + "_retention" + f"_{mode}"
    return {mod_key: {(2, retention_key): normalize_col}}


def _register_builtin_families() -> None:
    builtins: list[PlotFamily] = [
        PlotFamily(
            name="voltages",
            description="End-of-charge and end-of-discharge voltages vs cycle",
            column_builder=lambda hdr: [hdr.end_voltage_charge, hdr.end_voltage_discharge],
            mode=None,
        ),
        PlotFamily(
            name="capacities",
            description="Raw charge/discharge capacity vs cycle",
            column_builder=_cap_raw,
            mode="raw",
        ),
        PlotFamily(
            name="capacities_gravimetric",
            description="Gravimetric charge/discharge capacity vs cycle",
            column_builder=lambda hdr: _caps(hdr, "gravimetric"),
            mode="gravimetric",
        ),
        PlotFamily(
            name="capacities_areal",
            description="Areal charge/discharge capacity vs cycle",
            column_builder=lambda hdr: _caps(hdr, "areal"),
            mode="areal",
        ),
        PlotFamily(
            name="capacities_absolute",
            description="Absolute charge/discharge capacity vs cycle",
            column_builder=lambda hdr: _caps(hdr, "absolute"),
            mode="absolute",
        ),
        PlotFamily(
            name="capacities_gravimetric_split_constant_voltage",
            description="Gravimetric capacity split into CV / non-CV parts",
            column_builder=lambda hdr: _split(_caps(hdr, "gravimetric")),
            mode="gravimetric",
            supports_cv_split=True,
        ),
        PlotFamily(
            name="capacities_areal_split_constant_voltage",
            description="Areal capacity split into CV / non-CV parts",
            column_builder=lambda hdr: _split(_caps(hdr, "areal")),
            mode="areal",
            supports_cv_split=True,
        ),
        PlotFamily(
            name="capacities_gravimetric_coulombic_efficiency",
            description="Gravimetric capacity with coulombic efficiency",
            column_builder=lambda hdr: _caps(hdr, "gravimetric") + [hdr.coulombic_efficiency],
            mode="gravimetric",
        ),
        PlotFamily(
            name="capacities_areal_coulombic_efficiency",
            description="Areal capacity with coulombic efficiency",
            column_builder=lambda hdr: _caps(hdr, "areal") + [hdr.coulombic_efficiency],
            mode="areal",
        ),
        PlotFamily(
            name="capacities_absolute_coulombic_efficiency",
            description="Absolute capacity with coulombic efficiency",
            column_builder=lambda hdr: _caps(hdr, "absolute") + [hdr.coulombic_efficiency],
            mode="absolute",
        ),
        PlotFamily(
            name="capacities_gravimetric_with_rate",
            description="Gravimetric capacity with C-rate panels",
            column_builder=lambda hdr: _caps(hdr, "gravimetric")
            + [hdr.charge_c_rate, hdr.discharge_c_rate],
            mode="gravimetric",
        ),
        PlotFamily(
            name="capacities_areal_with_rate",
            description="Areal capacity with C-rate panels",
            column_builder=lambda hdr: _caps(hdr, "areal")
            + [hdr.charge_c_rate, hdr.discharge_c_rate],
            mode="areal",
        ),
        PlotFamily(
            name="capacities_absolute_with_rate",
            description="Absolute capacity with C-rate panels",
            column_builder=lambda hdr: _caps(hdr, "absolute")
            + [hdr.charge_c_rate, hdr.discharge_c_rate],
            mode="absolute",
        ),
        PlotFamily(
            name="fullcell_standard_gravimetric",
            description="Full-cell standard: CE, capacity, retention, CV (gravimetric)",
            column_builder=lambda hdr: _fullcell_columns(hdr, "gravimetric"),
            mode="gravimetric",
            transforms_builder=lambda hdr, norm: _retention_transforms(hdr, norm, "gravimetric"),
        ),
        PlotFamily(
            name="fullcell_standard_areal",
            description="Full-cell standard: CE, capacity, retention, CV (areal)",
            column_builder=lambda hdr: _fullcell_columns(hdr, "areal"),
            mode="areal",
            transforms_builder=lambda hdr, norm: _retention_transforms(hdr, norm, "areal"),
        ),
        PlotFamily(
            name="fullcell_standard_absolute",
            description="Full-cell standard: CE, capacity, retention, CV (absolute)",
            column_builder=lambda hdr: _fullcell_columns(hdr, "absolute"),
            mode="absolute",
            transforms_builder=lambda hdr, norm: _retention_transforms(hdr, norm, "absolute"),
        ),
        PlotFamily(
            name="fullcell_standard_cumloss_gravimetric",
            description="Full-cell standard with cumulated loss (gravimetric)",
            column_builder=lambda hdr: _cumloss_columns(hdr, "gravimetric"),
            mode="gravimetric",
            transforms_builder=lambda hdr, norm: _cumloss_transforms(hdr, norm, "gravimetric"),
        ),
        PlotFamily(
            name="fullcell_standard_cumloss_areal",
            description="Full-cell standard with cumulated loss (areal)",
            column_builder=lambda hdr: _cumloss_columns(hdr, "areal"),
            mode="areal",
            transforms_builder=lambda hdr, norm: _cumloss_transforms(hdr, norm, "areal"),
        ),
        PlotFamily(
            name="fullcell_standard_cumloss_absolute",
            description="Full-cell standard with cumulated loss (absolute)",
            column_builder=lambda hdr: _cumloss_columns(hdr, "absolute"),
            mode="absolute",
            transforms_builder=lambda hdr, norm: _cumloss_transforms(hdr, norm, "absolute"),
        ),
        PlotFamily(
            name="fullcell_standard_dev",
            description="Full-cell standard (dev layout, gravimetric)",
            column_builder=lambda hdr: [
                hdr.charge_capacity + "_gravimetric" + "_cv",
                hdr.discharge_capacity + "_gravimetric",
                hdr.coulombic_efficiency,
                "mod_01_" + hdr.discharge_capacity + "_gravimetric",
            ],
            mode="gravimetric",
            transforms_builder=lambda hdr, norm: _retention_transforms(hdr, norm, "gravimetric"),
        ),
        # Stage 2 (#646): voltage–capacity curves. Not a summary_plot(y=...) name.
        PlotFamily(
            name="cycles",
            description="Voltage vs capacity by cycle",
            column_builder=lambda hdr: ["capacity", "potential", "cycle_num"],
            supports_formation=True,
            extras={"entry_point": "cycles_plot", "kind": "cycles"},
        ),
        # Stage 2 (#647): raw time-series and cycle-info overlays.
        PlotFamily(
            name="raw",
            description="Raw time-series traces",
            column_builder=lambda hdr: ["voltage", "current"],
            supports_formation=False,
            extras={"entry_point": "raw_plot", "kind": "raw"},
        ),
        PlotFamily(
            name="cycle_info",
            description="Raw traces with step/cycle annotations",
            column_builder=lambda hdr: ["test_time", "voltage", "current"],
            supports_formation=False,
            extras={"entry_point": "cycle_info_plot", "kind": "cycle_info"},
        ),
        # Stage 2 (#648): ICA / DVA from cellpy.ica long frames.
        PlotFamily(
            name="ica",
            description="Incremental capacity (dQ/dV vs voltage)",
            column_builder=lambda hdr: ["voltage", "dqdv", "cycle", "direction"],
            supports_formation=False,
            extras={"entry_point": "ica_plot", "kind": "ica"},
        ),
        PlotFamily(
            name="dva",
            description="Differential voltage (dV/dQ vs capacity)",
            column_builder=lambda hdr: ["capacity", "dvdq", "cycle", "direction"],
            supports_formation=False,
            extras={"entry_point": "dva_plot", "kind": "dva"},
        ),
    ]
    for family in builtins:
        _register_family(family)


_register_builtin_families()
