import logging

import pytest

from cellpy import log
from cellpy.utils import ica

log.setup_logging(default_level=logging.DEBUG, testing=True)

# The 1.x ICA surface (Converter, dqdv_np, dqdv_cycles, dqdv(split=/tidy=/cycle=/
# label_direction=), the duplicate `dq` column) was removed in 2.1 (E2, #714).
# What remains is the specced modern API: dqdv / dvdq / to_wide + value/index
# bounds. The numerical oracle for transform_half_cycle lives in test_ica_api.py.


# --- small pure helpers (public since 1.x) -----------------------------------


def test_ica_value_bounds_simple():
    m1, m2 = ica.value_bounds([1, 2, 3, 4])
    assert m1 == 1
    assert m2 == 4


def test_ica_value_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5, mode="gravimetric", as_frame=False)
    assert ica.value_bounds(capacity) == pytest.approx(
        (0.001106868, 1535.303235807), 0.0001
    )
    assert ica.value_bounds(voltage) == pytest.approx(
        (0.15119725465774536, 1.0001134872436523), 0.0001
    )


def test_ica_index_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5, as_frame=False)
    assert ica.index_bounds(capacity) == pytest.approx(
        (0.001106868, 1535.303235807), 0.0001
    )
    assert ica.index_bounds(voltage) == pytest.approx(
        (0.15119725465774536, 1.0001134872436523), 0.0001
    )


# --- the specced modern frame ------------------------------------------------


_SPECCED_COLS = ["cycle", "direction", "voltage", "capacity", "dqdv"]


def test_dqdv_one_cycle_specced(dataset):
    df_ica = ica.dqdv(dataset, cycles=2)
    assert list(df_ica.columns) == _SPECCED_COLS
    assert not df_ica["voltage"].isna().any()
    assert len(df_ica) == 759


def test_dqdv_multi_cycles_specced(dataset):
    df_ica = ica.dqdv(dataset)
    assert list(df_ica.columns) == _SPECCED_COLS
    # 8889 rows in 1.x, less one splitter row for each of the 18 cycles.
    assert len(df_ica) == 8889 - 18


def test_dqdv_to_wide(dataset):
    wide = ica.to_wide(ica.dqdv(dataset))
    cycles_available = set(dataset.get_cycle_numbers())
    cycles_processed = {
        int(str(c).split()[0]) for c in wide.columns.get_level_values(0)
    }
    assert cycles_available.issuperset(cycles_processed)
    assert "voltage" in wide.columns.get_level_values(1)
    assert "dqdv" in wide.columns.get_level_values(1)


def test_deprecated_ica_surface_is_gone():
    for name in ("Converter", "dqdv_cycle", "dqdv_cycles", "dqdv_np"):
        assert not hasattr(ica, name), name
