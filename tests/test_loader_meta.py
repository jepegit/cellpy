"""Tests for loader-emitted per-test metadata (issue #508, V2-05/06/08).

Loads route parsed metadata into the meta boxes (surfacing in the derived
``TestMeta`` record), stamp the compact ``test_id`` grouping key on raw, stamp
instrument ``raw_units`` by value, and record load provenance.
"""

from __future__ import annotations

import pytest

from cellpy import cellreader
from cellpy.parameters.internal_settings import get_headers_normal, merge_raw_units
from cellpy.readers import test_meta

HN = get_headers_normal()


@pytest.fixture
def arbin_cell(parameters):
    c = cellreader.CellpyCell()
    c.from_raw(parameters.res_file_path)
    return c


def test_raw_gets_compact_test_id(arbin_cell):
    """V2-05: the raw test_id column holds the compact key (0), not tester ids."""
    assert sorted(arbin_cell.data.raw[HN.test_id_txt].unique()) == [0]


def test_loader_meta_routed_into_boxes(arbin_cell):
    box = arbin_cell.data.meta_test_dependent
    assert box.channel_index is not None
    assert box.creator is not None
    # orphan attributes stay set (backward compatibility)
    assert arbin_cell.data.channel_index == box.channel_index
    assert arbin_cell.data.creator == box.creator


def test_derived_record_carries_loader_meta_and_provenance(arbin_cell, parameters):
    rec = arbin_cell.data.tests.get(0)
    assert rec.test_id == 0
    assert rec.channel is not None
    assert rec.creator is not None
    # provenance (CORE_ONLY_TEST fields, from Data._provenance)
    assert rec.source_kind == "file"
    assert rec.source_type == "arbin_res"
    assert rec.source_uri
    import pathlib

    assert rec.raw_file_names == [pathlib.Path(parameters.res_file_path).name]
    assert rec.uuid
    assert rec.loaded_datetime


def test_pec_string_test_id_routed_and_coerced(parameters):
    c = cellreader.CellpyCell()
    c.set_instrument("pec_csv")
    c.from_raw(parameters.pec_file_path)
    box = c.data.meta_test_dependent
    assert box.test_ID == "187"  # tester id, provenance (string preserved)
    rec = c.data.tests.get(0)
    assert rec.test_id == 0  # compact key wins on the derived record
    assert sorted(c.data.raw[HN.test_id_txt].unique()) == [0]


def test_cycle_modes_in_data_matches_active_record(arbin_cell):
    """Regression (latent bug): raw used to carry tester id 1 while the active
    record is test_id 0, so present-id filtering mismatched."""
    from cellpycore.metadata.models import TestMeta

    arbin_cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="cathode"))
    # only the active test (0) is present in raw -> extras stay dormant
    modes = test_meta.cycle_modes_in_data(arbin_cell.data)
    assert modes == {arbin_cell.cycle_mode}


def test_vacant_copies_provenance(arbin_cell):
    other = cellreader.CellpyCell.vacant(cell=arbin_cell)
    assert other.data._provenance == arbin_cell.data._provenance
    assert other.data.tests.get(0).source_type == "arbin_res"


def test_direct_base_loader_call_stamps_raw_units(parameters):
    """The config-driven loader family stamps instrument units on the returned
    Data (previously only cellpy.get/from_raw applied them)."""
    c = cellreader.CellpyCell()
    c.set_instrument("maccor_txt", model="one")
    data = c.loader(parameters.mcc_file_path, sep="\t")
    expected = merge_raw_units(c.loader_class.get_raw_units())
    assert dict(data.raw_units) == dict(expected)


def test_merge_raw_units_overlay():
    merged = merge_raw_units({"mass": "kg", "bogus_label": "x"})
    assert merged["mass"] == "kg"
    assert "bogus_label" not in merged
    # untouched defaults survive
    assert merged["charge"] == "Ah"
