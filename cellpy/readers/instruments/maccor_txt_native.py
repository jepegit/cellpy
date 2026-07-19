"""Pilot loader for the two-stage design: Maccor txt (issue #559).

The first loader written as ``harmonize(parse(source), declarations)``. It runs
alongside the legacy ``maccor_txt`` loader and changes no existing behaviour —
the legacy path stays the default until the port (#560) switches over. What it
proves is that the vendor-specific part really is just parsing, and everything
after it can be declared.

The Maccor "three" dialect (WMG/SIMBA) has three quirks worth naming, because
they are the kind of thing that has to live *somewhere*:

- **One signed capacity column.** ``mAmp-hr`` holds whichever direction is
  active, identified by the ``State`` column (C/D/R). Splitting it into the two
  native columns is a post hook, since no rename can express it.
- **Duration strings.** ``TestTime`` looks like ``  0d 00:01:00.00``.
- **Milli-everything.** Currents in mA, capacities in mAh, potentials in mV —
  declared in ``raw_units``, converted once at ingestion by the framework, not
  by hand here.

Capacity granularity was determined from the data, not assumed: ``mAmp-hr``
resets when the direction changes within a cycle and continues across
same-direction steps, so once split by state each column is already
cycle-cumulative — the harmonized-raw target. Hence ``PER_CYCLE``.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl
from cellpycore.config import default_schema
from cellpycore.metadata.models import TestMeta
from cellpycore.units import CellpyUnits

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.contract import LoaderResult
from cellpy.readers.instruments.declarations import (
    LoaderDeclarations,
    ResetGranularity,
)
from cellpy.readers.instruments.harmonize import harmonize

_SCHEMA = default_schema().raw

# Vendor state codes -> direction.
_CHARGE_STATES = ("C",)
_DISCHARGE_STATES = ("D",)

# "  0d 00:01:00.00"
_DURATION = re.compile(
    r"\s*(?P<days>\d+)d\s+(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>[\d.]+)"
)

_VENDOR_CAPACITY = "mAmp-hr"
_VENDOR_STATE = "State"
_VENDOR_CYCLE = "Cyc#"

# Names the split hook produces; declared in column_map like any other column.
_CHARGE_CAPACITY = "_charge_capacity"
_DISCHARGE_CAPACITY = "_discharge_capacity"


def _duration_to_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    match = _DURATION.match(str(value))
    if match is None:
        return None
    return (
        int(match["days"]) * 86400
        + int(match["hours"]) * 3600
        + int(match["minutes"]) * 60
        + float(match["seconds"])
    )


def split_capacity_by_state(frame: pl.DataFrame) -> pl.DataFrame:
    """Split the single signed capacity column into charge and discharge.

    Reproduces the legacy ``_state_splitter`` semantics: within a cycle, each
    direction's column carries the vendor value on that direction's rows, holds
    the last value for the rest of the cycle (the legacy "propagate"), and is
    zero before the direction first appears.
    """
    if _VENDOR_CAPACITY not in frame.columns or _VENDOR_STATE not in frame.columns:
        raise LoaderError(
            f"expected {_VENDOR_CAPACITY!r} and {_VENDOR_STATE!r} columns in the "
            f"Maccor file; got {frame.columns}"
        )

    def _directional(states: tuple[str, ...], alias: str) -> pl.Expr:
        return (
            pl.when(pl.col(_VENDOR_STATE).is_in(states))
            .then(pl.col(_VENDOR_CAPACITY))
            .otherwise(None)
            .forward_fill()
            .over(_VENDOR_CYCLE)
            .fill_null(0.0)
            .alias(alias)
        )

    return frame.with_columns(
        _directional(_CHARGE_STATES, _CHARGE_CAPACITY),
        _directional(_DISCHARGE_STATES, _DISCHARGE_CAPACITY),
    )


MACCOR_THREE = LoaderDeclarations(
    column_map={
        "Rec#": _SCHEMA.datapoint_num,
        _VENDOR_CYCLE: _SCHEMA.cycle_num,
        "Step": _SCHEMA.step_num,
        "TestTime": _SCHEMA.test_time,
        "StepTime": _SCHEMA.step_time,
        "mAmps": _SCHEMA.current,
        "Volts": _SCHEMA.potential,
        "DPt Time": _SCHEMA.epoch_time_utc,
        _CHARGE_CAPACITY: _SCHEMA.cumulative_charge_capacity,
        _DISCHARGE_CAPACITY: _SCHEMA.cumulative_discharge_capacity,
    },
    raw_units=CellpyUnits(current="mA", charge="mAh", voltage="mV", mass="g"),
    # Determined from the data (see module docstring), not assumed.
    reset_granularity={
        _SCHEMA.cumulative_charge_capacity: ResetGranularity.PER_CYCLE,
        _SCHEMA.cumulative_discharge_capacity: ResetGranularity.PER_CYCLE,
    },
    post_hooks=(split_capacity_by_state,),
)


class MaccorTxtLoader:
    """Maccor tab-delimited txt, two-stage style.

    Conforms structurally to
    :class:`~cellpy.readers.instruments.contract.InstrumentLoader`.
    """

    name = "maccor_txt_native"
    instrument = "maccor"
    supported_suffixes = (".txt",)

    #: Rows of preamble before the header line.
    skip_rows = 4

    declarations = MACCOR_THREE

    def can_load(self, source: Path) -> bool:
        """Sniff the header line without parsing the file."""
        source = Path(source)
        if source.suffix.lower() not in self.supported_suffixes:
            return False
        try:
            with source.open("r", encoding="utf-8", errors="replace") as handle:
                head = [handle.readline() for _ in range(self.skip_rows + 1)]
        except OSError:
            return False
        return any(_VENDOR_CAPACITY in line for line in head)

    def parse(self, source: Path) -> pl.DataFrame:
        """Vendor stage: read the file into a frame with vendor column names."""
        source = Path(source)
        try:
            frame = pl.read_csv(
                source,
                separator="\t",
                skip_rows=self.skip_rows,
                has_header=True,
                encoding="utf8-lossy",
                truncate_ragged_lines=True,
                infer_schema_length=10_000,
            )
        except Exception as exc:
            raise LoaderError(f"could not parse Maccor file {source}: {exc}") from exc

        conversions = []
        for column in ("TestTime", "StepTime"):
            if column in frame.columns and frame[column].dtype == pl.String:
                conversions.append(
                    pl.col(column)
                    .map_elements(_duration_to_seconds, return_dtype=pl.Float64)
                    .alias(column)
                )
        if "DPt Time" in frame.columns and frame["DPt Time"].dtype == pl.String:
            conversions.append(
                pl.col("DPt Time")
                .str.strip_chars()
                .str.to_datetime("%m/%d/%Y %I:%M:%S %p", strict=False)
                .alias("DPt Time")
            )
        if conversions:
            frame = frame.with_columns(conversions)
        return frame

    def load(
        self,
        source: Path,
        *,
        instrument_config: object | None = None,
        **kwargs: object,
    ) -> tuple[LoaderResult, ...]:
        """Parse and harmonize one Maccor file into a single test."""
        vendor_frame = self.parse(Path(source))
        raw = harmonize(vendor_frame, self.declarations)
        return (
            LoaderResult(
                raw=raw,
                raw_units=self.declarations.raw_units,
                # A draft: only what the file knows. Provenance is stamped by
                # the framework, which alone knows where this came from.
                test_meta=TestMeta(),
            ),
        )
