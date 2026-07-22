"""The opt-in harmonized-raw flip (Phase B / #560).

``prms.Reader.use_harmonized_raw`` routes single-file raw loading through the
two-stage ``harmonize(parse())`` pipeline instead of the legacy
``loader()+to_native`` rename. It ships **off** until Phase C hardening is
done; the mechanism is wired and reversible, and this module keeps it covered
so it does not rot before it is the default.

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


def _get():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return cellpy.get(SOURCE, instrument="biologics_mpr", mass=1.0, testing=True)


@pytest.fixture
def harmonized_raw_on():
    previous = getattr(config.reader, "use_harmonized_raw", False)
    config.reader.use_harmonized_raw = True
    try:
        yield
    finally:
        config.reader.use_harmonized_raw = previous


@pytest.mark.essential
def test_default_is_off_so_raw_has_no_epoch_time_utc():
    """The legacy loader()+to_native path carries date_time, not epoch_time_utc."""
    assert getattr(config.reader, "use_harmonized_raw", False) is False
    c = _get()
    assert "epoch_time_utc" not in c.data.raw.columns


@pytest.mark.essential
def test_flip_on_produces_the_harmonized_native_raw(harmonized_raw_on):
    """With the flip on, raw comes from harmonize(parse()) and carries the
    native epoch_time_utc/mask columns the rename path omits."""
    c = _get()
    assert "epoch_time_utc" in c.data.raw.columns
    assert "mask" in c.data.raw.columns
    # and it is still a usable cell: the summary builds.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c.make_summary()
    assert len(c.data.summary) >= 1


AUX_SOURCE = "testdata/data/aux_one_x_dx.res"


@pytest.mark.essential
def test_flip_on_keeps_arbin_aux_and_datapoints(harmonized_raw_on):
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
    # Vendor Data_Point is 1..n for this fixture — not a synthesised 0..n-1.
    assert int(c.data.raw["datapoint_num"].iloc[0]) == 1
    assert int(c.data.raw["datapoint_num"].iloc[-1]) == len(c.data.raw)
