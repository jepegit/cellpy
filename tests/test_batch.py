import ast
import json
import logging
import os
import pathlib
import tempfile
import time

import pandas
import pytest

from cellpy import log, prms
from cellpy.utils import batch as batch
from cellpy.utils import helpers
from cellpy.batch import _dbengine
from cellpy.parameters.internal_settings import get_headers_journal

log.setup_logging(default_level="DEBUG", testing=True)

hdr_journal = get_headers_journal()

# TODO: I think these tests saves new versions of cellpyfiles each time. Fix that.
# TODO: Most likely some of these tests also saves an updated batch json file. Fix that.


@pytest.fixture(scope="module")
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture
def batch_instance(clean_dir, parameters):
    # Change to temporary directory so that files are saved there
    original_cwd = os.getcwd()
    os.chdir(clean_dir)

    try:
        prms.Paths.db_filename = parameters.db_file_name
        prms.Paths.cellpydatadir = clean_dir
        prms.Paths.outdatadir = clean_dir
        prms.Paths.rawdatadir = parameters.raw_data_dir
        prms.Paths.db_path = parameters.db_dir
        prms.Paths.filelogdir = clean_dir
        prms.Paths.batchfiledir = clean_dir
        prms.Paths.notebookdir = clean_dir
        prms.Paths.instrumentdir = parameters.instrument_dir
        prms.Paths.templatedir = parameters.template_dir
        prms.Paths.examplesdir = parameters.examples_dir
        prms.Batch.auto_use_file_list = False
        yield batch
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


@pytest.fixture
def populated_batch(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )

    b.create_journal()
    b.paginate()
    b.update(testing=True)
    return b


def test_reading_db(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )

    b.create_journal()


def test_batbase_json_reader_pages_dict_shape():
    """Test BatBaseJSONReader produces pages_dict with expected journal keys (no file search)."""
    from pathlib import Path
    from cellpy.readers import json_dbreader

    fixture_dir = Path(__file__).parent / "fixtures"
    json_file = fixture_dir / "cellpy_batbase_like.json"
    assert json_file.exists(), f"Fixture missing: {json_file}"

    reader = json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert reader.pages_dict is not None
    assert hdr_journal["filename"] in reader.pages_dict
    assert hdr_journal["id_key"] in reader.pages_dict
    assert hdr_journal["mass"] in reader.pages_dict
    assert hdr_journal["total_mass"] in reader.pages_dict

    number_of_cells = len(reader.pages_dict[hdr_journal["filename"]])
    assert number_of_cells == 1
    assert reader.pages_dict[hdr_journal["filename"]][0] == "20160805_test001_45_cc"


def test_batbase_json_reader_validation_missing_required_column(tmp_path):
    """BatBaseJSONReader raises ValueError when a required column is missing."""
    from cellpy.readers import json_dbreader

    # Missing "Test Name" and "ID Key"
    bad = {"Mass (mg)": [1], "Total Mass (mg)": [1]}
    json_file = tmp_path / "bad.json"
    json_file.write_text(json.dumps(bad))
    with pytest.raises(ValueError) as exc_info:
        json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert "missing required column" in exc_info.value.args[0]
    assert "Test Name" in exc_info.value.args[0]


def test_batbase_json_reader_validation_no_rows(tmp_path):
    """BatBaseJSONReader raises ValueError when the journal has no rows."""
    from cellpy.readers import json_dbreader

    empty = {"Test Name": [], "ID Key": []}
    json_file = tmp_path / "empty.json"
    json_file.write_text(json.dumps(empty))
    with pytest.raises(ValueError) as exc_info:
        json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert "no rows" in exc_info.value.args[0]


def test_batbase_json_reader_validation_null_in_required_column(tmp_path):
    """BatBaseJSONReader raises ValueError when a required column contains null."""
    from cellpy.readers import json_dbreader

    bad = {
        "Test Name": ["a", None],
        "ID Key": [1, 2],
        "Mass (mg)": [1, 1],
        "Total Mass (mg)": [1, 1],
    }
    json_file = tmp_path / "bad.json"
    json_file.write_text(json.dumps(bad))
    with pytest.raises(ValueError) as exc_info:
        json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert "contains null" in exc_info.value.args[0]
    assert "Test Name" in exc_info.value.args[0]
    assert "row index 1" in exc_info.value.args[0]


def test_batbase_json_reader_cell_type_from_test_mode_inverted(tmp_path):
    """When Test Mode is 'inverted (anode mode)', cell_type is 'anode'."""
    from cellpy.readers import json_dbreader

    data = {
        "Test Name": ["run1"],
        "ID Key": [1],
        "Mass (mg)": [1],
        "Total Mass (mg)": [1],
        "Loading (mg/cm2)": [1],
        "Nominal Capacity": [2],
        "Area (cm2)": [1],
        "Cell Type": ["hc"],
        "Test Mode": ["inverted (anode mode)"],
        "Instrument": ["arbin_res"],
        "Unit": ["mAh/g"],
        "Group": [1],
    }
    json_file = tmp_path / "batbase.json"
    json_file.write_text(json.dumps(data))
    reader = json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert reader.pages_dict[hdr_journal["cell_type"]] == ["anode"]


def test_batbase_json_reader_cell_type_from_test_mode_standard(tmp_path):
    """When Test Mode is not 'inverted (anode mode)', cell_type is 'standard'."""
    from cellpy.readers import json_dbreader

    data = {
        "Test Name": ["run1"],
        "ID Key": [1],
        "Mass (mg)": [1],
        "Total Mass (mg)": [1],
        "Loading (mg/cm2)": [1],
        "Nominal Capacity": [2],
        "Area (cm2)": [1],
        "Test Mode": ["standard"],
        "Instrument": ["arbin_res"],
        "Unit": ["mAh/g"],
        "Group": [1],
    }
    json_file = tmp_path / "batbase.json"
    json_file.write_text(json.dumps(data))
    reader = json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert reader.pages_dict[hdr_journal["cell_type"]] == ["standard"]


def test_batbase_json_reader_cell_type_backward_compat_no_test_mode(tmp_path):
    """Without Test Mode, cell_type comes from Cell Type (hci -> anode, else standard)."""
    from cellpy.readers import json_dbreader

    data = {
        "Test Name": ["run1"],
        "ID Key": [1],
        "Mass (mg)": [1],
        "Total Mass (mg)": [1],
        "Loading (mg/cm2)": [1],
        "Nominal Capacity": [2],
        "Area (cm2)": [1],
        "Cell Type": ["hci"],
        "Instrument": ["arbin_res"],
        "Unit": ["mAh/g"],
        "Group": [1],
    }
    json_file = tmp_path / "batbase.json"
    json_file.write_text(json.dumps(data))
    reader = json_dbreader.BatBaseJSONReader(json_file, store_raw_data=False)
    assert reader.pages_dict[hdr_journal["cell_type"]] == ["anode"]


def test_reading_json_db(batch_instance, parameters):
    """Test batch journal from BatBase-like JSON and file search (uses testdata paths)."""
    from pathlib import Path
    from cellpy.readers import json_dbreader

    fixture_dir = Path(__file__).parent / "fixtures"
    json_file = fixture_dir / "cellpy_batbase_like.json"
    assert json_file.exists(), f"Fixture missing: {json_file}"

    reader = json_dbreader.BatBaseJSONReader(json_file, store_raw_data=True)
    assert reader.pages_dict is not None
    assert hdr_journal["filename"] in reader.pages_dict
    assert hdr_journal["mass"] in reader.pages_dict
    assert hdr_journal["total_mass"] in reader.pages_dict

    number_of_cells = len(reader.pages_dict[hdr_journal["filename"]])

    pages = _dbengine.simple_db_engine(
        reader=reader,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert len(pages) == number_of_cells
    assert hdr_journal["raw_file_names"] in pages.columns
    assert hdr_journal["cellpy_file_name"] in pages.columns
    assert hdr_journal["group"] in pages.columns
    assert hdr_journal["sub_group"] in pages.columns
    assert hdr_journal["label"] in pages.columns
    assert hdr_journal["cell_type"] in pages.columns
    assert hdr_journal["instrument"] in pages.columns

    # File search should have populated paths (exact paths depend on testdata layout)
    raw_names = pages[hdr_journal["raw_file_names"]].iloc[0]
    cellpy_name = pages[hdr_journal["cellpy_file_name"]].iloc[0]
    run_name = "20160805_test001_45_cc"
    assert raw_names is not None and len(raw_names) >= 1
    assert any(run_name in str(p) for p in (raw_names if isinstance(raw_names, list) else [raw_names]))
    assert cellpy_name is not None and run_name in str(cellpy_name)


def test_custom_json_reader_pages_dict_and_engine(batch_instance, parameters):
    """Test CustomJSONReader with column map and simple_db_engine (file search)."""
    from pathlib import Path
    from cellpy.readers import json_dbreader

    fixture_dir = Path(__file__).parent / "fixtures"
    json_file = fixture_dir / "custom_json_batch_like.json"
    assert json_file.exists(), f"Fixture missing: {json_file}"

    column_map = {
        "cell_id": "filename",
        "mass_mg": "mass",
        "total_mass_mg": "total_mass",
        "instrument_name": "instrument",
    }
    reader = json_dbreader.CustomJSONReader(
        json_file, column_map=column_map, store_raw_data=False
    )
    assert reader.pages_dict is not None
    assert hdr_journal["filename"] in reader.pages_dict
    assert reader.pages_dict[hdr_journal["filename"]][0] == "20160805_test001_45_cc"

    pages = _dbengine.simple_db_engine(
        reader=reader,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert len(pages) == 1
    assert hdr_journal["raw_file_names"] in pages.columns
    assert hdr_journal["cellpy_file_name"] in pages.columns
    raw_names = pages[hdr_journal["raw_file_names"]].iloc[0]
    assert raw_names is not None
    assert not isinstance(raw_names, list) or len(raw_names) >= 1


def test_find_files_skip_file_search():
    """Test that find_files(skip_file_search=True) leaves existing paths unchanged."""

    info_dict = {
        hdr_journal["filename"]: ["cell_a"],
        hdr_journal["file_name_indicator"]: ["cell_a"],
        hdr_journal["raw_file_names"]: [["/path/to/raw.res"]],
        hdr_journal["cellpy_file_name"]: ["/path/to/cell_a.h5"],
        hdr_journal["instrument"]: [None],
    }
    out = _dbengine.find_files(info_dict, skip_file_search=True)
    assert out[hdr_journal["raw_file_names"]] == [["/path/to/raw.res"]]
    assert out[hdr_journal["cellpy_file_name"]] == ["/path/to/cell_a.h5"]


def test_reading_cell_specs(batch_instance):
    # For the simple excel dbreader, cell specs are given in the
    # columns "argument" as str.
    # The argument str must be on the form:
    #    "keyword-1=value-1;keyword-2=value2"

    from cellpy.batch import resolve_specs

    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b02", testing=True
    )
    b.create_journal()
    # batch v3: the argument column is resolved into CellSpec.overrides
    specs = resolve_specs(b.journal)
    labels = b.cell_names
    by_label = {s.label: s for s in specs}
    assert by_label[labels[0]].overrides.get("recalc") is True
    assert by_label[labels[1]].overrides.get("recalc") is False
    assert by_label[labels[1]].overrides.get("data_points") == (1, 10_000)
    assert not by_label[labels[2]].overrides.get("recalc")


def test_load_journal_json(parameters, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_json_path, testing=True)
    assert len(b.pages) == 5
    assert hdr_journal["argument"] in b.pages.columns


def test_load_limited_journal_excel(parameters, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_xlsx_path, testing=True)
    assert len(b.pages) == 2
    # batch v3: keys-in-columns (the cell label is a `filename` column)
    assert hdr_journal["filename"] in b.pages.columns


@pytest.mark.skip_on_macos
def test_load_full_journal_excel_and_check_headers_generated(
    parameters, batch_instance
):
    b = batch_instance.from_journal(
        parameters.journal_file_full_xlsx_path, testing=True
    )
    assert len(b.pages) == 2
    # batch v3: polars pages, keys-in-columns (no pandas index)
    assert hdr_journal["filename"] in b.pages.columns


def test_load_with_explicit_cellpy_journal_file(parameters, batch_instance):
    """Test load() with journal_file= path to cellpy journal (info_df format)."""
    b = batch_instance.load(
        "test_batch",
        "test_project",
        journal_file=parameters.journal_file_json_path,
        allow_from_journal=False,
        drop_bad_cells=False,
        testing=True,
    )
    assert b is not None
    assert len(b.pages) == 5
    assert hdr_journal["argument"] in b.pages.columns


def test_load_with_explicit_custom_json(parameters, batch_instance):
    """Test load() with journal_file= and reader='custom_json_reader'."""
    fixture_path = pathlib.Path(__file__).parent / "fixtures" / "custom_json_batch_like.json"
    assert fixture_path.exists()

    column_map = {
        "cell_id": "filename",
        "mass_mg": "mass",
        "total_mass_mg": "total_mass",
        "instrument_name": "instrument",
    }
    b = batch_instance.load(
        "test_batch",
        "test_project",
        journal_file=str(fixture_path),
        reader="custom_json_reader",
        column_map=column_map,
        allow_from_journal=False,
        testing=True,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert b is not None
    assert len(b.pages) == 1
    assert b.cell_names[0] == "20160805_test001_45_cc"
    assert hdr_journal["raw_file_names"] in b.pages.columns
    assert hdr_journal["cellpy_file_name"] in b.pages.columns


def test_load_with_explicit_batbase_json(parameters, batch_instance):
    """Test load() with journal_file= and reader='batbase_json_reader'."""
    fixture_path = pathlib.Path(__file__).parent / "fixtures" / "cellpy_batbase_like.json"
    assert fixture_path.exists()

    b = batch_instance.load(
        "test_batch",
        "test_project",
        journal_file=str(fixture_path),
        reader="batbase_json_reader",
        allow_from_journal=False,
        testing=True,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert b is not None
    assert len(b.pages) == 1
    assert b.cell_names[0] == "20160805_test001_45_cc"


# TODO: make this test
def test_update_with_cellspecs(parameters, batch_instance):
    # from journal and as argument (see batch_experiment.py, update).
    pass


def test_load_save_journal_roundtrip_cell_specs(parameters, clean_dir, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_json_path, testing=True)
    out = pathlib.Path(clean_dir) / "j.json"
    b.save(out)
    spec_1 = b.pages[hdr_journal["argument"]][0]
    assert spec_1 == "recalc=False"
    assert out.is_file()
    b2 = batch_instance.from_journal(out, testing=True)
    assert len(b.pages) == 5
    assert hdr_journal["argument"] in b.pages.columns
    assert b2.pages[hdr_journal["argument"]][0] == spec_1


def test_load_save_journal_roundtrip_json(parameters, clean_dir, batch_instance):
    """Characterization (batch v3 / #697): JSON journal survives a
    from_journal -> to_file -> from_journal round-trip with its pages intact.
    Pins today's behaviour before the journal module is rewritten (A2)."""
    b1 = batch_instance.from_journal(parameters.journal_file_json_path, testing=True)
    out = pathlib.Path(clean_dir) / "roundtrip.json"
    b1.save(out)
    assert out.is_file()

    b2 = batch_instance.from_journal(out, testing=True)
    # same number of cells, same labels, same argument column
    assert len(b2.pages) == len(b1.pages) == 5
    assert b2.cell_names == b1.cell_names
    assert hdr_journal["argument"] in b2.pages.columns
    assert (
        b2.pages[hdr_journal["argument"]][0]
        == b1.pages[hdr_journal["argument"]][0]
    )


@pytest.mark.skip_on_macos
def test_load_save_journal_roundtrip_excel(parameters, clean_dir, batch_instance):
    """Characterization (batch v3 / #697): an Excel journal read into the model
    and written back out as JSON reloads with the same pages. Excel becomes
    read-only in batch v3 (A2), so the round-trip is Excel -> model -> JSON."""
    b1 = batch_instance.from_journal(
        parameters.journal_file_full_xlsx_path, testing=True
    )
    out = pathlib.Path(clean_dir) / "from_excel.json"
    b1.save(out)
    assert out.is_file()

    b2 = batch_instance.from_journal(out, testing=True)
    assert len(b2.pages) == len(b1.pages) == 2
    assert b2.cell_names == b1.cell_names


# --- batch v3 end-to-end (via the new cellpy.batch facade) ---------------
# The Batch surface itself is pinned in tests/test_batch_v3_facade.py; here we
# exercise the full journal -> load -> update -> summaries flow through the
# legacy cellpy.utils.batch entry points (now shims over cellpy.batch).


def test_populated_batch_end_to_end_values(populated_batch, parameters):
    """End-to-end value characterization: journal -> load -> update ->
    summaries, asserting values (not just shapes) for a real batch."""
    b = populated_batch

    # journal populated and cells loaded
    assert len(b.pages) >= 1
    assert len(b.cell_names) == len(b.pages)

    # per-cell capacity extraction is stable (known value, cf. the get_cap test)
    name = parameters.run_name_2
    if name in b.cell_names:
        cap_df = b.cells[name].get_cap(cycle=1)
        assert len(cap_df) == 1105

    # combined summaries are non-empty and carry charge_capacity
    b.combine_summaries()
    summaries = b.summaries
    assert summaries is not None and len(summaries) > 0
    assert "charge_capacity" in summaries.columns


@pytest.mark.essential
@pytest.mark.xfail(
    reason="batch v3 plot delegation over the tidy summaries frame lands with "
    "the collectors redesign (Epic B, #708)",
    strict=False,
)
def test_issue668_batch_plot_variants(populated_batch):
    """#668: ``b.plot(...)`` builds a figure. Full wiring is Epic B."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = populated_batch.plot(backend="plotly", show=False, ir=True, direction="discharge")
    assert fig is not None


# TODO: make this test
def test_load_journal_custom_db_reader(batch_instance):
    pass


def test_query():
    def mock_reader_method(cell_id):
        spec = {
            1: "recalc=True",
            2: "recalc=False;other=12",
        }
        return spec[cell_id]

    cell_ids = [1, 2]
    out = _dbengine._query(mock_reader_method, cell_ids)
    assert "=" in out[0]
    assert ";" in out[1]


@pytest.mark.skip(reason="shaky test - fails intermittently in CI")
def test_cycling_summary_plotter(populated_batch):
    populated_batch.combine_summaries()
    populated_batch.plot()


@pytest.mark.xfail(
    reason="helpers.concatenate_summaries (rate/group collection) migrates onto "
    "the polars aggregate/collectors in Epic C/B (#706); superseded by "
    "cellpy.batch.combine_summaries",
    strict=False,
)
def test_concatinator(populated_batch):
    cellnames = populated_batch.cell_names
    c = populated_batch.experiment.data[cellnames[0]]
    cf = helpers.concatenate_summaries(
        populated_batch, columns=["charge_capacity"], rate=0.04, group_it=True
    )
    print(cf.head(5))


@pytest.mark.xfail(
    reason="helpers.concatenate_summaries/yank_outliers migrate onto polars in "
    "Epic C (#706)",
    strict=False,
)
def test_concatinator_yanked(populated_batch):
    removed = helpers.yank_outliers(
        populated_batch, remove_indexes=[3, 4, 5], keep_old=False
    )
    print(removed)
    c1 = populated_batch.experiment.data[populated_batch.cell_names[0]]
    print(c1.data.summary.head(10))
    cf1 = helpers.concatenate_summaries(
        populated_batch, columns=["charge_capacity"], rate=0.04, group_it=True
    )
    cf2 = helpers.concatenate_summaries(
        populated_batch,
        columns=["charge_capacity"],
        rate=0.04,
        group_it=True,
        inverted=True,
    )
    print(cf1.head())
    print(cf2.head())


def test_report(populated_batch):
    print(populated_batch.report)


def test_batch_update(parameters, batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )
    b.create_journal()
    b.paginate()
    b.update(testing=True)


@pytest.mark.essential
def test_batch_plot_backend_triage():
    """plotly/matplotlib supported; seaborn + bokeh removed in 2.1 (E1, #713)."""
    from cellpy.plotting.batch_summary import resolve_batch_plot_backend

    assert resolve_batch_plot_backend("plotly") == "plotly"
    assert resolve_batch_plot_backend("matplotlib") == "matplotlib"
    with pytest.raises(ValueError, match="seaborn"):
        resolve_batch_plot_backend("seaborn")
    with pytest.raises(ValueError, match="bokeh"):
        resolve_batch_plot_backend("bokeh")
    with pytest.raises(ValueError, match="not supported"):
        resolve_batch_plot_backend("not-a-backend")


@pytest.mark.essential
@pytest.mark.xfail(
    reason="batch v3 Batch.plot returns the figure directly (no .plotter); the "
    "tidy-frame plot path lands with the collectors redesign (Epic B, #708)",
    strict=False,
)
def test_batch_plot_delegates_without_batch_plotters(populated_batch):
    """``Batch.plot`` builds a figure via ``cellpy.plotting`` (#658)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    populated_batch.plot(backend="plotly", show=False)
    assert populated_batch.plotter.figure is not None


BATCH_SNAPSHOT_PATH = (
    pathlib.Path(__file__).resolve().parent / "data" / "batch_figure_specs.json"
)


def _batch_figure_menu(populated_batch) -> dict:
    from tests.figure_spec_support import describe_figure

    populated_batch.plot(backend="plotly", show=False, ir=True, rate=False)
    return {
        "figures": {
            "batch_cycle_life[plotly]": describe_figure(populated_batch.plotter.figure),
        }
    }


def write_batch_figure_specs(populated_batch=None) -> pathlib.Path:
    """Regenerate ``batch_figure_specs.json`` (dev helper / snapshot regen)."""
    if populated_batch is None:
        raise RuntimeError("pass a populated_batch when calling from tests")
    specs = _batch_figure_menu(populated_batch)
    BATCH_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_SNAPSHOT_PATH.write_text(
        json.dumps(specs, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return BATCH_SNAPSHOT_PATH


@pytest.mark.essential
@pytest.mark.xfail(
    reason="batch v3 plot layout snapshot re-baselines with the collectors "
    "redesign (Epic B, #708)",
    strict=False,
)
def test_batch_figure_structure_matches_snapshot(populated_batch):
    """Batch.plot cycle-life layout is part of the plotting contract (#658)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    if not BATCH_SNAPSHOT_PATH.is_file():
        pytest.skip(f"missing snapshot {BATCH_SNAPSHOT_PATH}")
    expected = json.loads(BATCH_SNAPSHOT_PATH.read_text(encoding="utf-8"))["figures"]
    actual = _batch_figure_menu(populated_batch)["figures"]
    assert set(actual) == set(expected)
    for name, want in expected.items():
        got = actual[name]
        assert got["backend"] == want["backend"], name
        assert got.get("n_traces") == want.get("n_traces"), name
        assert got.get("n_axes") == want.get("n_axes"), name


# def test_iterate_folder(batch_instance):
# # Since the batch-files contains full paths I need to figure out how to make a custom json-file for the test.
#     folder_name = prms.Paths.batchfiledir
#     batch.iterate_batches(folder_name, default_log_level="CRITICAL")
