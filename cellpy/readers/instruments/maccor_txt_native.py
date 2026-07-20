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
from cellpy.readers.instruments.hooks import state_splitter

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
_VENDOR_DATAPOINT = "Rec#"

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


#: Split the single signed capacity column into charge and discharge.
#:
#: Uses the shared :func:`~cellpy.readers.instruments.hooks.state_splitter`.
#: This module previously carried its own copy built on ``forward_fill()``,
#: which was **not** the legacy behaviour it claimed to reproduce: a forward
#: fill also fills rests *between* two same-direction rows, where
#: ``_state_splitter`` leaves them at 0 and only propagates after the
#: direction's last row in the cycle. The in-tree Maccor fixtures happen not to
#: contain that pattern, so the difference never showed — see
#: ``tests/test_hooks.py::test_propagate_is_not_a_forward_fill``.
split_capacity_by_state = state_splitter(
    base_column=_VENDOR_CAPACITY,
    state_column=_VENDOR_STATE,
    cycle_column=_VENDOR_CYCLE,
    datapoint_column=_VENDOR_DATAPOINT,
    charge_keys=_CHARGE_STATES,
    discharge_keys=_DISCHARGE_STATES,
    charge_output=_CHARGE_CAPACITY,
    discharge_output=_DISCHARGE_CAPACITY,
    propagate=True,
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
    # Known-and-discarded: State/mAmp-hr are consumed by the split hook, ES is
    # a Maccor status flag, "Unnamed: 12" is a trailing-tab artifact.
    # TODO(#560 tier port): mWatt-hr is an energy and should become a
    # passthrough column instead of a discard (cellpy-core#139).
    dropped=("State", "ES", "mAmp-hr", "mWatt-hr", "Unnamed: 12"),
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
