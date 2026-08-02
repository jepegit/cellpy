"""Typed batch loading options + spec resolution.

Replaces the kwargs tunnels of the legacy ``CyclingExperiment.update`` (79
``kwargs.pop/get`` calls, precedence documented in a single docstring) with two
dataclasses and one pure function:

- :class:`LoadPolicy` -- batch-wide loading knobs (``force_cellpy``/``force_raw``/
  ``force_recalc``/... collapse into typed fields).
- :class:`CellSpec` -- fully resolved per-cell loading instructions.
- :func:`resolve_specs` -- the *single* place journal rows, policy-level
  overrides and per-cell overrides merge, with the precedence the legacy code
  smeared across ~200 lines of ``update()``:

      journal row  <  journal ``argument``  <  policy overrides  <  per-cell

The legacy merge was ``{**cell_spec_page, **kwargs, **cell_spec}``
(batch_experiments.py:361); this reproduces it as a tested, pure function.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from cellpy.batch.journal import FILENAME, Journal


class SourcePreference(str, Enum):
    """Which source a cell is loaded from."""

    AUTO = "auto"  # local .cellpy if present, else raw (no freshness check)
    NEWEST = "newest"  # compare raw vs cellpy via cellpy.get check_file_ids
    CELLPY_ONLY = "cellpy_only"  # replaces force_cellpy=True
    RAW_ONLY = "raw_only"  # replaces force_raw_file=True


@dataclass
class LoadPolicy:
    """Batch-wide loading options (one object instead of a kwargs tunnel)."""

    source: SourcePreference = SourcePreference.AUTO
    recalc: bool = False  # replaces force_recalc
    max_cycle: int | None = None
    accept_errors: bool = True  # errors collected, not raised
    all_in_memory: bool = False
    skip_bad_cells: bool = False
    selector: dict | None = None  # forwarded to the cellpy-file loader
    loader_kwargs: dict = field(default_factory=dict)  # the one escape hatch
    #: batch-level per-field overrides applied to every cell (e.g. {"mass": 1.0}).
    overrides: dict = field(default_factory=dict)


@dataclass
class CellSpec:
    """Fully resolved per-cell loading instructions."""

    label: str
    raw_files: list = field(default_factory=list)
    cellpy_file: Any | None = None
    instrument: str | None = None
    model: str | None = None
    mass: float | None = None
    nom_cap: float | None = None
    nom_cap_specifics: str | None = None
    area: float | None = None
    cycle_mode: str | None = None
    #: leftover per-cell knobs (recalc, data_points, ...) not mapped to a field.
    overrides: dict = field(default_factory=dict)


#: Journal columns that map directly to a typed :class:`CellSpec` field.
_SPEC_FIELDS = ("instrument", "model", "mass", "nom_cap", "nom_cap_specifics", "area", "cycle_mode")


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and value != value


def _clean(value: Any) -> Any:
    """Normalise pandas/polars null-ish values to ``None``."""
    if value is None or _is_nan(value):
        return None
    return value


def _coerce_scalar(value: Any) -> Any:
    """Coerce a string spec value the way the legacy update() did."""
    if not isinstance(value, str):
        return value
    low = value.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("none", ""):
        return None
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def parse_argument(argument: Any) -> dict:
    """Parse a journal ``argument`` cell into a dict of coerced values.

    Accepts a dict (``{"recalc": "False"}``), the compact string form
    (``"recalc=False;data_points=(1, 10000)"``), or null-ish -> ``{}``.
    """
    if argument is None or _is_nan(argument):
        return {}
    if isinstance(argument, dict):
        return {key: _coerce_scalar(val) for key, val in argument.items()}
    if isinstance(argument, str):
        text = argument.strip()
        if not text:
            return {}
        parsed: dict = {}
        for part in text.split(";"):
            if "=" not in part:
                continue
            key, val = part.split("=", 1)
            parsed[key.strip()] = _coerce_scalar(val.strip())
        return parsed
    return {}


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def resolve_specs(
    journal: Journal,
    policy: LoadPolicy | None = None,
    per_cell: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[CellSpec]:
    """Resolve one :class:`CellSpec` per cell in ``journal``.

    Precedence (later wins): journal columns < journal ``argument`` <
    ``policy.overrides`` < ``per_cell[label]``.
    """
    policy = policy or LoadPolicy()
    per_cell = per_cell or {}

    specs: list[CellSpec] = []
    for row in journal.pages.iter_rows(named=True):
        label = row[FILENAME]

        journal_fields = {
            field_name: _clean(row.get(field_name))
            for field_name in _SPEC_FIELDS
            if field_name in row
        }
        # cell_type stands in for cycle_mode when the latter is absent
        if not journal_fields.get("cycle_mode") and _clean(row.get("cell_type")):
            journal_fields["cycle_mode"] = _clean(row.get("cell_type"))

        argument = parse_argument(row.get("argument"))
        overrides = dict(per_cell.get(label, {}))

        merged = {**journal_fields, **argument, **policy.overrides, **overrides}

        specs.append(
            CellSpec(
                label=label,
                raw_files=_as_list(_clean(row.get("raw_file_names"))),
                cellpy_file=_clean(row.get("cellpy_file_name")),
                instrument=merged.get("instrument"),
                model=merged.get("model"),
                mass=merged.get("mass"),
                nom_cap=merged.get("nom_cap"),
                nom_cap_specifics=merged.get("nom_cap_specifics"),
                area=merged.get("area"),
                cycle_mode=merged.get("cycle_mode"),
                overrides={
                    key: val
                    for key, val in merged.items()
                    if key not in _SPEC_FIELDS
                },
            )
        )
    return specs
