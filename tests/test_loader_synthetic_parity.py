"""Value parity for dialects with no sample file, on synthesised input (#560).

Five of the eight shipped configuration-driven dialects have no vendor file in
the repository, so ``test_loader_port_parity`` could not reach them. That
matters for the switchover: "the exception list is empty" says the *covered*
dialects agree, not that every dialect will.

The bugs this arc has actually found — a wrong reset granularity, duration
strings cast to null, a column mapped to the wrong native name, a unit template
left unresolved — are all **configuration-level**. They do not need real vendor
data to reproduce; they need a file spelled the way the configuration says. So
each file here is generated *from the configuration's own declarations*: its
column names, separator, decimal mark, skiprows and state keys.

What this does not do is exercise vendor quirks — the odd row, the interrupted
run, the stray 0xFF byte. Those still need real files. This closes the
systematic half of the gap, not the empirical half.
"""

from __future__ import annotations

import datetime as dt
import importlib
import warnings

import polars as pl
import pytest

from cellpy.readers import data_structures as ds
from cellpy.readers.instruments.config_declarations import (
    substitute_unit_templates,
)
from cellpy.readers.instruments.harmonize import harmonize

#: configuration module, instrument, model, file suffix.
SYNTHETIC_CASES = (
    ("maccor_txt_three", "maccor_txt", "three", ".txt"),
    ("neware_txt_zero", "neware_txt", "ONE", ".csv"),
    ("neware_txt_two", "neware_txt", "TIOTECH", ".csv"),
)

#: 300 data rows, because auto-delimiter detection needs a sample. Measured
#: while building these fixtures: with ``sep`` unset, files of 20 and 100 data
#: rows fail with a bare ``IndexError`` while 150 and 300 load — so a small
#: fixture fails for a reason that has nothing to do with the dialect under
#: test. That threshold is a real loading bug for short vendor files, filed
#: separately; here it only dictates the fixture size.
N_CYCLES, N_STEPS, N_ROWS = 30, 2, 5

TOLERANCE = 1e-6

#: ``date_time`` is a passthrough string on the native side and a datetime on
#: the legacy side — the representation gap tracked on the metadata arc.
SKIP_COLUMNS = ("date_time",)


def _duration(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _synthesise(config_name, path):
    """Write a vendor file spelled the way this configuration says it is."""
    config = importlib.import_module(
        f"cellpy.readers.instruments.configurations.{config_name}"
    )
    renaming = substitute_unit_templates(
        dict(config.normal_headers_renaming_dict), config
    )
    formatters = getattr(config, "formatters", {}) or {}
    states = getattr(config, "states", {}) or {}
    post = {k: v for k, v in (getattr(config, "post_processors", {}) or {}).items() if v}

    separator = formatters.get("sep") or ","
    skiprows = formatters.get("skiprows", 0) or 0
    decimal = formatters.get("decimal", ".") or "."
    as_durations = post.get("convert_test_time_to_timedelta") or post.get(
        "convert_step_time_to_timedelta"
    )

    charge = (states.get("charge_keys") or ["C"])[0]
    discharge = (states.get("discharge_keys") or ["D"])[0]

    cycles, steps, datapoints, state_column_values = [], [], [], []
    datapoint = 1
    for cycle in range(1, N_CYCLES + 1):
        for step in range(1, N_STEPS + 1):
            for _ in range(N_ROWS):
                cycles.append(cycle)
                steps.append(step)
                datapoints.append(datapoint)
                state_column_values.append(charge if step == 1 else discharge)
                datapoint += 1
    n = len(cycles)

    def value(attribute, i):
        if attribute == "data_point_txt":
            return datapoints[i]
        if attribute == "cycle_index_txt":
            return cycles[i]
        if attribute in ("step_index_txt", "sub_step_index_txt"):
            return steps[i]
        if attribute in ("test_time_txt", "step_time_txt", "sub_step_time_txt"):
            seconds = (i + 1) * 60
            return _duration(seconds) if as_durations else float(seconds)
        if attribute == "datetime_txt":
            stamp = dt.datetime(2026, 1, 1) + dt.timedelta(seconds=60 * i)
            return stamp.strftime("%Y-%m-%d %H:%M:%S")
        if "capacity" in attribute or "energy" in attribute:
            # Rises within a step so the cumulative handling has something to do.
            return round(0.1 * ((i % N_ROWS) + 1), 4)
        if attribute == "current_txt":
            return 0.05
        if attribute == "voltage_txt":
            return round(3.0 + 0.01 * i, 4)
        return 0.0

    columns = {vendor: [value(attr, i) for i in range(n)] for attr, vendor in renaming.items()}
    state_column = states.get("column_name")
    if state_column and state_column not in columns:
        columns[state_column] = state_column_values

    frame = pl.DataFrame(columns)

    lines = [f"# preamble line {k}" for k in range(skiprows)]
    lines.append(separator.join(frame.columns))
    for row in frame.iter_rows():
        cells = []
        for item in row:
            text = str(item)
            if decimal != "." and isinstance(item, float):
                text = text.replace(".", decimal)
            cells.append(text)
        lines.append(separator.join(cells))

    path.write_text(
        "\n".join(lines) + "\n", encoding=formatters.get("encoding") or "utf-8"
    )
    return path


def _numeric(series):
    dtype = series.dtype
    if dtype.is_numeric():
        return series.cast(pl.Float64)
    if dtype == pl.Duration:
        return series.dt.total_nanoseconds().cast(pl.Float64) / 1e9
    if dtype == pl.String:
        coerced = series.cast(pl.Float64, strict=False)
        if coerced.null_count() == series.null_count():
            return coerced
    return None


@pytest.mark.essential
@pytest.mark.parametrize("config_name, instrument, model, suffix", SYNTHETIC_CASES)
def test_synthesised_dialect_matches_the_legacy_frame(
    config_name, instrument, model, suffix, tmp_path
):
    """Same assertion as the real-file oracle, for a dialect with no sample."""
    import cellpy

    source = _synthesise(config_name, tmp_path / f"{config_name}{suffix}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cell = cellpy.get(
            str(source), instrument=instrument, model=model, mass=1.0, testing=True
        )
        loader = ds.generate_default_factory().create(instrument, model=model)
        vendor = loader.parse(str(source), model=model)

    harmonized = harmonize(vendor, loader.declarations(), strict=False)
    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))

    shared = [c for c in harmonized.columns if c in legacy.columns]
    assert len(shared) >= 8, f"{config_name}: only {shared} in common - too weak"

    mismatched = []
    for column in shared:
        if column in SKIP_COLUMNS:
            continue
        left, right = harmonized[column], legacy[column]
        if left.len() != right.len():
            mismatched.append(f"{column} (rows {left.len()} vs {right.len()})")
            continue
        left_n, right_n = _numeric(left), _numeric(right)
        if left_n is None or right_n is None:
            if left.dtype != right.dtype or not (left == right).all():
                mismatched.append(f"{column} ({right.dtype} -> {left.dtype})")
            continue
        worst = (left_n - right_n).abs().max()
        if worst is None or worst > TOLERANCE:
            mismatched.append(f"{column} (max abs diff {worst})")

    assert not mismatched, (
        f"{config_name}: harmonize() disagrees with the legacy path on "
        f"{mismatched}"
    )


@pytest.mark.essential
@pytest.mark.parametrize("config_name, instrument, model, suffix", SYNTHETIC_CASES)
def test_synthesised_dialect_produces_the_expected_native_columns(
    config_name, instrument, model, suffix, tmp_path
):
    """The dialect reaches native raw at all — not silently emptied columns."""
    source = _synthesise(config_name, tmp_path / f"{config_name}{suffix}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        loader = ds.generate_default_factory().create(instrument, model=model)
        vendor = loader.parse(str(source), model=model)
    harmonized = harmonize(vendor, loader.declarations(), strict=False)

    for column in ("cycle_num", "step_num", "current", "potential", "test_time"):
        assert column in harmonized.columns, f"{config_name}: {column} missing"
        series = harmonized[column]
        assert series.null_count() < series.len(), (
            f"{config_name}: {column} came out entirely null"
        )
