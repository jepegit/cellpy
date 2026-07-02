"""Acceptance tests for the cellpy-core seam.

These tests verify that ``CellpyCell`` delegates Data ownership and the per-cycle
summary pipeline to ``cellpy-core`` (via ``OldCellpyCellCore``), see issue #377.

They are derived from the proof-of-concept ``tests/test_slim.py`` on branch
``334-isolate-parts-needed-for-cellpy-core`` and extended with real assertions.
"""

import logging
import pathlib

import pytest

from cellpy import log
from cellpycore.cell_core import OldCellpyCellCore

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.fixture(scope="function")
def cpi():
    from cellpy import cellreader

    return cellreader.CellpyCell()


def test_core_seam_wired(cpi):
    """CellpyCell exposes a cellpy-core OldCellpyCellCore as ``self.core``."""
    assert isinstance(cpi.core, OldCellpyCellCore)
    # legacy headers/units are restored by the bridge
    assert cpi.core.raw_cols.charge_capacity_txt == cpi.headers_normal.charge_capacity_txt
    assert cpi.core.cycle_cols.charge_capacity == cpi.headers_summary.charge_capacity


def test_data_ownership_in_core(cpi):
    """Data ownership lives behind the seam (the data property reads core._data)."""
    cpi.initialize()
    assert cpi.data is cpi.core._data
    new_data = type(cpi.data)()
    cpi.data = new_data
    assert cpi.core._data is new_data


def test_make_summary_through_core(cpi, parameters):
    """End-to-end: from_raw -> make_summary delegates to the core and produces
    the expected summary."""
    cpi.set_instrument("arbin_res")
    cpi.from_raw(parameters.res_file_path)
    cpi.mass = 1.0
    cpi.make_summary(find_ir=True, find_end_voltage=True)

    summary = cpi.data.summary
    h = cpi.headers_summary

    assert summary is not None
    assert not summary.empty
    # the calculated summary columns produced by cellpy-core are present
    for col in (
        h.charge_capacity,
        h.discharge_capacity,
        h.coulombic_efficiency,
        h.charge_c_rate,
    ):
        assert col in summary.columns
    # golden value (matches the legacy/pre-seam summary; see test_from_raw_local)
    assert summary.loc[1, h.data_point] == 1457


def test_make_summary_save_roundtrip(cpi, parameters, tmp_path):
    """The seam keeps the load/save path working end-to-end."""
    cpi.set_instrument("arbin_res")
    cpi.from_raw(parameters.res_file_path)
    cpi.mass = 1.0
    cpi.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / "seam_roundtrip.h5"
    logging.info(f"saving cellpy file to {name}")
    cpi.save(name)
    assert name.is_file()


def test_direct_core_make_core_summary(cpi, parameters):
    """The core can build a summary directly from a loaded Data object."""
    cpi.set_instrument("arbin_res")
    cpi.from_raw(parameters.res_file_path)
    cpi.mass = 1.0
    cpi.make_step_table()

    data = cpi.data
    data = cpi.core.make_core_summary(data, find_ir=True, find_end_voltage=True)

    h = cpi.headers_summary
    assert data.summary is not None
    assert not data.summary.empty
    assert h.charge_capacity in data.summary.columns
    assert h.discharge_capacity in data.summary.columns


def test_make_summary_selector_kwargs_deprecated(cpi, parameters):
    """The legacy selector kwargs are accepted but warn and have no effect."""
    cpi.set_instrument("arbin_res")
    cpi.from_raw(parameters.res_file_path)
    cpi.mass = 1.0
    with pytest.warns(DeprecationWarning, match="deprecated"):
        cpi.make_summary(selector_type="non-cv")
    assert cpi.data.summary is not None
    assert not cpi.data.summary.empty
