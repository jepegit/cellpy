"""The harmonized-raw flip (Phase B/C / #560).

``prms.Reader.use_harmonized_raw`` (default **on** as of Phase C) routes
single-file raw loading through the two-stage ``harmonize(parse())`` pipeline.
Set it to ``False`` for the emergency ``loader()+to_native`` fallback.

biologics_mpr covers the clean end-to-end path (epoch_time_utc / mask).
``arbin_res`` with the wide-aux fixture covers the #621 regressions
(aux survival + datapoint preservation).
"""

from __future__ import annotations

import warnings

import pytest

import cellpy
import cellpy.config as config

SOURCE = "testdata/data/biol.mpr"
AUX_SOURCE = "testdata/data/aux_one_x_dx.res"


def _get(source=SOURCE, instrument="biologics_mpr"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return cellpy.get(source, instrument=instrument, mass=1.0, testing=True)


@pytest.fixture
def harmonized_raw_off():
    previous = getattr(config.reader, "use_harmonized_raw", True)
    config.reader.use_harmonized_raw = False
    try:
        yield
    finally:
        config.reader.use_harmonized_raw = previous


@pytest.mark.essential
def test_default_is_on_so_raw_has_epoch_time_utc():
    """Phase C: the default path is harmonize(parse()), which stamps epoch_time_utc."""
    assert getattr(config.reader, "use_harmonized_raw", True) is True
    c = _get()
    assert "epoch_time_utc" in c.data.raw.columns
    assert "mask" in c.data.raw.columns


@pytest.mark.essential
def test_flip_off_falls_back_to_loader_to_native(harmonized_raw_off):
    """Emergency off-switch restores the rename path (date_time, no epoch)."""
    c = _get()
    assert "epoch_time_utc" not in c.data.raw.columns
    assert "date_time" in c.data.raw.columns or "datetime" in [
        c.lower() for c in c.data.raw.columns
    ]


@pytest.mark.essential
def test_default_path_still_builds_a_summary():
    c = _get()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c.make_summary()
    assert len(c.data.summary) >= 1


@pytest.mark.essential
def test_default_keeps_arbin_aux_and_datapoints():
    """Phase C / #621: aux columns survive and datapoint_num is the vendor index."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            c = cellpy.get(
                AUX_SOURCE, instrument="arbin_res", mass=1.0, testing=True
            )
        except Exception as exc:  # noqa: BLE001 — missing Access/mdbtools
            pytest.skip(f"arbin_res unavailable here: {exc}")
    assert "aux_temperature_0" in c.data.raw.columns, (
        f"aux column missing; got {[c for c in c.data.raw.columns if 'aux' in c]}"
    )
    assert "datapoint_num" in c.data.raw.columns
    assert int(c.data.raw["datapoint_num"].iloc[0]) == 1
    assert int(c.data.raw["datapoint_num"].iloc[-1]) == len(c.data.raw)
