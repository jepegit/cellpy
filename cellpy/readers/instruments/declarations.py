"""Loader declarations — normalization described, not coded (issue #559).

A loader keeps the part that is genuinely hard and vendor-specific (parsing the
file) and *declares* everything after it: which vendor column is which native
column, what the units are, how timestamps should be read, and — the dangerous
one — what reset granularity the vendor's cumulative columns use.

Declarations are validated **when they are constructed**, which is when the
configuration module is imported. A typo'd native column name is then an import
error naming the typo, instead of a confusing failure in the middle of someone's
load six months later (loader plan §2.2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable, Mapping

from cellpycore.config import default_schema
from cellpycore.units import CellpyUnits, validate_units

from cellpy.exceptions import LoaderError

#: ``aux_<quantity>_<name>`` — the harmonized-raw auxiliary naming scheme.
_AUX_PATTERN = re.compile(r"^aux_(temperature|potential|pressure|resistance)_\w+$")


class ResetGranularity(StrEnum):
    """How often a vendor's cumulative column resets to zero.

    The harmonized-raw target is **cycle-cumulative**: within a cycle the value
    accumulates across that cycle's steps for its direction, and resets at each
    cycle boundary. ``harmonize()`` converts the other two granularities to it.

    Getting this wrong does not raise — it silently changes every capacity in
    the dataset. It is declared per column, and the property test in
    ``tests/test_harmonize.py`` is what actually catches a wrong declaration.
    """

    #: Resets every step. Converted by accumulating step totals within a cycle.
    PER_STEP = "per_step"
    #: Resets every cycle. Already the target convention — left alone.
    PER_CYCLE = "per_cycle"
    #: Never resets. Converted by subtracting each cycle's starting value.
    PER_TEST = "per_test"


@dataclass(frozen=True)
class LoaderDeclarations:
    """Everything ``harmonize()`` needs to turn a vendor frame into native raw.

    Args:
        column_map: vendor column name → native ``RawCols`` name. Vendor
            columns not mentioned here are dropped; native names must exist.
        raw_units: the units the *file* is in, as a validated ``CellpyUnits``.
        timezone: IANA zone for naive vendor timestamps. ``None`` means "treat
            naive timestamps as local time", the shared D3 rule — recorded on
            ``TestMeta.time_zone`` so the assumption is visible later.
        reset_granularity: native cumulative column → its granularity in the
            vendor file. Columns not listed are assumed already cycle-
            cumulative, which is the common case and the target convention.
        aux_map: vendor column → ``aux_<quantity>_<name>``.
        post_hooks: callables applied to the vendor frame *before* renaming,
            for quirks no declaration can express (e.g. Maccor's single
            signed capacity column that must be split by direction).
    """

    column_map: Mapping[str, str]
    raw_units: CellpyUnits
    timezone: str | None = None
    reset_granularity: Mapping[str, ResetGranularity] = field(default_factory=dict)
    aux_map: Mapping[str, str] = field(default_factory=dict)
    post_hooks: tuple[Callable, ...] = ()

    def __post_init__(self) -> None:
        self._validate()

    # -- validation ------------------------------------------------------------
    def _validate(self) -> None:
        native_names = set(default_schema().raw.ordered_names())

        unknown = sorted(set(self.column_map.values()) - native_names)
        if unknown:
            raise LoaderError(
                f"column_map targets columns that are not in the harmonized-raw "
                f"schema: {unknown}. Native columns are {sorted(native_names)}."
            )

        targets = list(self.column_map.values())
        duplicated = sorted({name for name in targets if targets.count(name) > 1})
        if duplicated:
            raise LoaderError(
                f"column_map maps more than one vendor column onto {duplicated}; "
                f"the later one would silently win."
            )

        try:
            validate_units(self.raw_units)
        except Exception as exc:
            raise LoaderError(f"raw_units is not a valid unit spec: {exc}") from exc

        bad_granularity = sorted(
            column for column in self.reset_granularity if column not in native_names
        )
        if bad_granularity:
            raise LoaderError(
                f"reset_granularity refers to columns that are not in the "
                f"harmonized-raw schema: {bad_granularity}."
            )

        undeclared = sorted(
            column
            for column in self.reset_granularity
            if column not in set(self.column_map.values())
        )
        if undeclared:
            raise LoaderError(
                f"reset_granularity declares {undeclared}, which column_map never "
                f"produces; the declaration would have no effect."
            )

        bad_aux = sorted(
            target for target in self.aux_map.values() if not _AUX_PATTERN.match(target)
        )
        if bad_aux:
            raise LoaderError(
                f"aux_map targets {bad_aux} do not follow the "
                f"aux_<quantity>_<name> scheme (quantity is one of temperature, "
                f"potential, pressure, resistance)."
            )

    # -- convenience -----------------------------------------------------------
    @property
    def native_columns(self) -> tuple[str, ...]:
        """Native columns this loader produces, aux included."""
        return tuple(self.column_map.values()) + tuple(self.aux_map.values())
