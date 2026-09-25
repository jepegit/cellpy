"""load_since on the cheap-partial loaders (issue #780, L2).

Four shipped loaders match ``SupportsIncrementalLoad``; the rest do not. A
chunk is the same harmonized frame a full ``harmonize(parse())`` yields for
those rows, the marker rewinds to the start of the last cycle read, and a
head cell plus a real chunk equals a full load (the #778 oracle).
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

import cellpy
from cellpy.readers.instruments import (
    arbin_res,
    arbin_sql,
    biologics_mpr,
    local_instrument,
    maccor_txt,
    neware_txt,
    pec_csv,
)
from cellpy.readers.instruments.contract import IncrementalChunk, LoadMarker, SupportsIncrementalLoad
from cellpy.readers.instruments.harmonize import harmonize
from cellpy.readers.instruments.incremental import last_cycle_start
from tests import fdv
from tests.incremental_support import (
    NEWARE_KWARGS,
    NEWARE_UIO,
    assert_cell_frames_equal,
    incremental_update,
    truncate_text_file,
)

MACCOR = NEWARE_UIO.parent / "maccor_001.txt"
RES = NEWARE_UIO.parent / "20160805_test001_45_cc_01.res"

needs_neware = pytest.mark.skipif(not NEWARE_UIO.is_file(), reason="neware_uio.csv fixture missing")
needs_maccor = pytest.mark.skipif(not MACCOR.is_file(), reason="maccor_001.txt fixture missing")
needs_res = pytest.mark.skipif(
    not RES.is_file() or arbin_res.mdb_export_unavailable_reason() is not None,
    reason="res fixture or mdbtools missing",
)


def _full(loader, path) -> pl.DataFrame:
    return harmonize(loader.parse(path), loader.declarations(), strict=False)


@pytest.mark.essential
def test_only_the_four_cheap_partial_loaders_are_incremental():
    for module in (neware_txt, maccor_txt, arbin_res, arbin_sql):
        assert issubclass(module.DataLoader, SupportsIncrementalLoad), module.__name__
    for module in (pec_csv, biologics_mpr, local_instrument):
        assert not issubclass(module.DataLoader, SupportsIncrementalLoad), module.__name__


@pytest.mark.essential
def test_last_cycle_start_finds_the_trailing_run():
    frame = pl.DataFrame({"c": [1, 1, 2, 2, 2, 3]})
    assert last_cycle_start(frame, "c") == 5
    assert last_cycle_start(pl.DataFrame({"c": [4, 4]}), "c") == 0
    assert last_cycle_start(pl.DataFrame({"c": []}), "c") == 0
    assert last_cycle_start(frame, None) == 0
    assert last_cycle_start(frame, "missing") == 0


@needs_neware
@pytest.mark.essential
def test_neware_load_since_none_equals_full_harmonized_read():
    chunk = neware_txt.DataLoader(model="UIO").load_since(NEWARE_UIO, None)
    full = _full(neware_txt.DataLoader(model="UIO"), NEWARE_UIO)
    assert isinstance(chunk, IncrementalChunk)
    assert chunk.new_raw.equals(full)
    assert chunk.complete is False
    # marker = data-row index of the first row of the last cycle
    assert chunk.marker.row_count == last_cycle_start(full, "cycle_num")
    assert chunk.marker.last_source_datapoint_num is None


@needs_neware
@pytest.mark.essential
def test_neware_load_since_marker_rereads_from_last_cycle_start(tmp_path):
    full = _full(neware_txt.DataLoader(model="UIO"), NEWARE_UIO)
    # head = everything up to the middle of cycle 3
    cycle3 = full.filter(pl.col("cycle_num") == 3)
    cut = int((cycle3["datapoint_num"].min() + cycle3["datapoint_num"].max()) // 2)
    head_path = truncate_text_file(NEWARE_UIO, tmp_path / "head.csv", cut)

    head = neware_txt.DataLoader(model="UIO").load_since(head_path, None)
    assert head.new_raw.height == cut
    cycle3_start = int(cycle3["datapoint_num"].min())
    assert head.marker.row_count == cycle3_start - 1  # datapoint_num is 1-based

    tail = neware_txt.DataLoader(model="UIO").load_since(NEWARE_UIO, head.marker)
    assert int(tail.new_raw["datapoint_num"].min()) == cycle3_start
    assert tail.new_raw.equals(full.slice(head.marker.row_count))
    assert tail.marker.row_count == last_cycle_start(full, "cycle_num")


@needs_neware
@pytest.mark.essential
def test_neware_head_cell_plus_chunk_equals_full_load(tmp_path):
    """The #778 oracle driven by a real load_since chunk."""
    full_cell = cellpy.get(NEWARE_UIO, testing=True, **NEWARE_KWARGS)
    steps = full_cell.data.steps
    st = full_cell.schema.steps
    later = steps[steps[st.cycle_num] == 3].iloc[1]
    cut = (int(later[st.datapoint_num_first]) + int(later[st.datapoint_num_last])) // 2
    head_path = truncate_text_file(NEWARE_UIO, tmp_path / "head.csv", cut)
    head_cell = cellpy.get(head_path, testing=True, **NEWARE_KWARGS)

    marker = neware_txt.DataLoader(model="UIO").load_since(head_path, None).marker
    chunk = neware_txt.DataLoader(model="UIO").load_since(NEWARE_UIO, marker)
    new_raw = chunk.new_raw.to_pandas()
    new_raw[full_cell.schema.raw.test_id] = head_cell.data.active_test_id

    updated = incremental_update(head_cell, new_raw)
    assert_cell_frames_equal(updated, full_cell)


@needs_neware
@pytest.mark.essential
def test_marker_past_end_of_file_gives_empty_chunk_and_same_marker():
    marker = LoadMarker(row_count=10**7)
    chunk = neware_txt.DataLoader(model="UIO").load_since(NEWARE_UIO, marker)
    assert chunk.new_raw.height == 0
    assert chunk.marker == marker


@needs_neware
@pytest.mark.essential
def test_load_since_does_not_poison_the_parse_cache():
    loader = neware_txt.DataLoader(model="UIO")
    loader.load_since(NEWARE_UIO, LoadMarker(row_count=9000))
    assert getattr(loader, "_parsed_frame", None) is None
    data = loader.loader(NEWARE_UIO)
    assert len(data.raw) == 9065


@needs_maccor
@pytest.mark.essential
def test_maccor_load_since_matches_full_read_and_row_marker():
    full = _full(maccor_txt.DataLoader(), MACCOR)
    chunk = maccor_txt.DataLoader().load_since(MACCOR, None)
    assert chunk.new_raw.equals(full)
    # single-cycle fixture: the rewind lands on row 0
    assert chunk.marker.row_count == 0

    again = maccor_txt.DataLoader().load_since(MACCOR, chunk.marker)
    assert again.new_raw.equals(full)

    # A caller-made marker mid-cycle still reads the right rows; only the
    # cycle-local capacity rebase differs, which is why loader-made markers
    # rewind to a cycle start.
    since = maccor_txt.DataLoader().load_since(MACCOR, LoadMarker(row_count=100))
    assert since.new_raw.height == full.height - 100
    keys = ["datapoint_num", "cycle_num", "step_num", "current", "potential", "test_time"]
    assert since.new_raw.select(keys).equals(full.slice(100).select(keys))


@needs_res
@pytest.mark.essential
def test_arbin_res_load_since_seeks_on_datapoint_and_rewinds_to_cycle_start():
    full = _full(arbin_res.DataLoader(), RES)
    chunk = arbin_res.DataLoader().load_since(RES, None)
    assert chunk.new_raw.equals(full)
    last_start_row = last_cycle_start(full, "cycle_num")
    last_start_dp = int(full["datapoint_num"][last_start_row])
    assert chunk.marker.last_source_datapoint_num == last_start_dp - 1
    assert chunk.marker.row_count is None

    mid = int(full["datapoint_num"].max()) // 2
    since = arbin_res.DataLoader().load_since(RES, LoadMarker(last_source_datapoint_num=mid))
    assert int(since.new_raw["datapoint_num"].min()) == mid + 1
    assert since.new_raw.equals(full.filter(pl.col("datapoint_num") > mid))

    tail = arbin_res.DataLoader().load_since(RES, chunk.marker)
    assert int(tail.new_raw["datapoint_num"].min()) == last_start_dp
    assert tail.new_raw["cycle_num"].n_unique() == 1


def _two_cycle_mock() -> pd.DataFrame:
    """The 29-row arbin_sql mock sheet repeated as cycles 1 and 2."""
    one = pd.read_excel(fdv.mock_file_path, sheet_name="arbin_sql")
    one["Date_Time"] = one["Date_Time"].astype("int64")
    two = one.copy()
    two["Data_Point"] = two["Data_Point"] + len(one)
    two["Cycle_ID"] = 2
    return pd.concat([one, two], ignore_index=True)


@pytest.mark.essential
def test_arbin_sql_load_since_filters_on_datapoint(monkeypatch):
    mock = _two_cycle_mock()
    seen = []

    def fake_query(self, name, since_data_point=None):
        seen.append(since_data_point)
        frame = mock if since_data_point is None else mock[mock["Data_Point"] > since_data_point]
        return frame.reset_index(drop=True), pd.DataFrame()

    monkeypatch.setattr(arbin_sql.DataLoader, "_query_sql", fake_query)

    chunk = arbin_sql.DataLoader().load_since("some_test", None)
    assert seen == [None]
    assert chunk.new_raw.height == len(mock)
    # cycle 2 starts at Data_Point 30 -> marker 29
    assert chunk.marker.last_source_datapoint_num == 29

    tail = arbin_sql.DataLoader().load_since("some_test", chunk.marker)
    assert seen[-1] == 29
    assert tail.new_raw.height == 29
    assert int(tail.new_raw["datapoint_num"].min()) == 30
    assert tail.marker == chunk.marker

    empty = arbin_sql.DataLoader().load_since("some_test", LoadMarker(last_source_datapoint_num=10**6))
    assert empty.new_raw.height == 0


@pytest.mark.essential
def test_arbin_sql_query_gets_a_datapoint_clause(monkeypatch):
    queries = []

    class FakeConn:
        pass

    def fake_connect(*_args, **_kwargs):
        return FakeConn()

    def fake_read_sql_query(sql, _conn):
        queries.append(sql)
        if "TestList_Table WHERE" in sql and "IV_Basic_Table" not in sql and "StatisticData_Table" not in sql:
            return pd.DataFrame({"Database_Name": ["ArbinPro8Data"], "Test_Name": ["t"]})
        return pd.DataFrame()

    monkeypatch.setattr(arbin_sql.pyodbc, "connect", fake_connect)
    monkeypatch.setattr(arbin_sql.pd, "read_sql_query", fake_read_sql_query)

    arbin_sql.DataLoader()._query_sql("t", since_data_point=123)
    data_queries = [q for q in queries if "IV_Basic_Table" in q]
    assert len(data_queries) == 1
    assert "ArbinPro8Data.dbo.IV_Basic_Table.Data_Point > 123" in data_queries[0]

    queries.clear()
    arbin_sql.DataLoader()._query_sql("t")
    assert all("Data_Point >" not in q for q in queries)
