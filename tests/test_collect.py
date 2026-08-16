"""Tests for the cellpy.collect foundation (collectors redesign, #705/#706)."""

import re
from types import SimpleNamespace

import polars as pl
import pytest

import cellpy
from cellpy.batch import Batch, Journal
from cellpy.batch.journal import FILENAME
from cellpy.batch.store import CellStore
from cellpy.collect import (
    BatchCollector,
    Collection,
    CollectionMeta,
    SummaryOptions,
    collect_cycles,
    collect_summaries,
    cycles_collector,
    dva_collector,
    ica_collector,
    load_collection,
    normalize_column,
    normalize_column_on_max,
    standard_gravimetric,
    summary_collector,
)
from cellpy.plotting import registry
from tests import fdv


def _batch_with_cells(cells: dict, pages: pl.DataFrame) -> Batch:
    b = Batch(Journal(name="b", project="p", pages=pages))
    b._store = CellStore.from_cells(cells)
    return b


# ---- options ------------------------------------------------------------


def test_summary_options_replace_is_immutable():
    opts = SummaryOptions()
    changed = opts.replace(group_it=True)
    assert opts.group_it is False
    assert changed.group_it is True


# ---- Collection product -------------------------------------------------


def test_collection_save_load_roundtrip_and_wide(tmp_path):
    frame = pl.DataFrame(
        {"cell": ["a", "a"], "cycle_num": [1, 2], "charge_capacity": [1.0, 2.0]}
    )
    col = Collection(frame, "summary", "test", CollectionMeta(kind="summary", batch_name="b"))

    written = col.save(tmp_path, formats=("parquet", "csv"))
    assert any(p.suffix == ".json" for p in written)
    assert (tmp_path / "test.parquet").is_file()

    loaded = load_collection(tmp_path / "test.parquet")
    assert loaded.data.equals(frame)
    assert loaded.meta.batch_name == "b"

    wide = col.to_wide(values="charge_capacity", index="cycle_num", columns="cell")
    assert "a" in wide.columns


def test_collection_save_requires_directory():
    col = Collection(pl.DataFrame({"a": [1]}), "summary", "x", CollectionMeta(kind="summary"))
    with pytest.raises(ValueError, match="explicit directory"):
        col.save(None)


# ---- collect_summaries (on batch.aggregate) -----------------------------


@pytest.fixture(scope="module")
def real_cell():
    return cellpy.get(cellpy_file=fdv.cellpy_file_path, testing=True)


@pytest.fixture(scope="module")
def real_batch(real_cell):
    return _batch_with_cells(
        {"c45": real_cell},
        pl.DataFrame({FILENAME: ["c45"], "group": [1], "sub_group": [1]}),
    )


def test_collect_summaries(real_batch):
    col = collect_summaries(real_batch)
    assert col.kind == "summary"
    assert col.data.height > 0
    for key in ("cell", "group", "sub_group"):
        assert key in col.data.columns
    assert col.meta.cells_included == ["c45"]


def test_collect_summaries_column_selection(real_batch):
    col = collect_summaries(real_batch, columns=("charge_capacity",))
    assert "charge_capacity" in col.data.columns
    assert "cell" in col.data.columns  # keys always kept


def test_collect_summaries_max_cycle(real_batch):
    col = collect_summaries(real_batch, max_cycle=5)
    assert col.data["cycle_num"].max() <= 5


def test_collect_summaries_rate_filter(real_batch):
    # charge C-rate is ~0.043 for cycles 1-3, ~0.085 from cycle 4 on.
    col = collect_summaries(
        real_batch, rate=0.043, rate_std=0.01, rate_on="charge"
    )
    assert set(col.data["cycle_num"].to_list()) == {1, 2, 3}


def test_collect_summaries_rate_inverted(real_batch):
    col = collect_summaries(
        real_batch, rate=0.043, rate_std=0.01, rate_on="charge", rate_inverted=True
    )
    cycles = set(col.data["cycle_num"].to_list())
    assert cycles and cycles.isdisjoint({1, 2, 3})


def test_collect_summaries_partition_by_cv_adds_columns(real_batch):
    # this cell has no cv_ steps, so *_cv columns are ~0 but must still appear.
    col = collect_summaries(
        real_batch, columns=("charge_capacity",), partition_by_cv=True
    )
    assert "charge_capacity_non_cv" in col.data.columns
    assert "charge_capacity_cv" in col.data.columns


# ---- group averaging (helpers._make_average port) -----------------------


class _SummaryCell:
    """A fake cell exposing a polars summary (schema falls back to defaults)."""

    def __init__(self, charge_capacity):
        self.data = SimpleNamespace(
            summary=pl.DataFrame(
                {
                    "cycle_num": list(range(1, len(charge_capacity) + 1)),
                    "charge_capacity": [float(v) for v in charge_capacity],
                }
            ),
            steps=None,
        )


def test_collect_summaries_group_average():
    pages = pl.DataFrame(
        {FILENAME: ["x", "y"], "group": [1, 1], "sub_group": [1, 2]}
    )
    b = _batch_with_cells(
        {"x": _SummaryCell([10.0, 20.0]), "y": _SummaryCell([20.0, 40.0])}, pages
    )

    col = collect_summaries(b, group_it=True, columns=("charge_capacity",))
    data = col.data

    # long format: one row per (group, cycle_num, variable) with mean + std
    for key in ("group", "cycle_num", "variable", "mean", "std"):
        assert key in data.columns

    cc = data.filter(pl.col("variable") == "charge_capacity").sort("cycle_num")
    assert cc["mean"].to_list() == [15.0, 30.0]
    # std of [10, 20] (ddof=1) == 7.071...; of [20, 40] == 14.142...
    assert cc["std"].to_list() == pytest.approx([7.0710678, 14.1421356])


def test_collect_summaries_group_average_needs_group_column():
    # no group column in pages -> grouping is a no-op, stays wide
    pages = pl.DataFrame({FILENAME: ["x"]})
    b = _batch_with_cells({"x": _SummaryCell([1.0, 2.0])}, pages)
    col = collect_summaries(b, group_it=True)
    assert "variable" not in col.data.columns


# ---- is_grouped flag (#790) ---------------------------------------------


def test_is_grouped_true_when_averaged():
    pages = pl.DataFrame({FILENAME: ["x", "y"], "group": [1, 1], "sub_group": [1, 2]})
    b = _batch_with_cells(
        {"x": _SummaryCell([10.0, 20.0]), "y": _SummaryCell([20.0, 40.0])}, pages
    )
    col = collect_summaries(b, group_it=True, columns=("charge_capacity",))
    assert col.is_grouped is True
    assert col.meta.grouped is True


def test_is_grouped_false_on_single_cell_group_fallback():
    # group_it=True but only a singleton group -> wide fallback
    pages = pl.DataFrame({FILENAME: ["x"], "group": [1], "sub_group": [1]})
    b = _batch_with_cells({"x": _SummaryCell([1.0, 2.0])}, pages)
    col = collect_summaries(b, group_it=True)
    assert col.is_grouped is False


@pytest.mark.essential
def test_group_it_averages_multi_when_mixed_with_singleton():
    """Multi-member groups average even if another group is a singleton (#816)."""
    pages = pl.DataFrame(
        {
            FILENAME: ["a", "b", "c"],
            "group": [1, 1, 2],
            "sub_group": [1, 2, 1],
        }
    )
    b = _batch_with_cells(
        {
            "a": _SummaryCell([10.0, 20.0]),
            "b": _SummaryCell([20.0, 40.0]),
            "c": _SummaryCell([5.0, 7.0]),
        },
        pages,
    )
    col = collect_summaries(b, group_it=True, columns=("charge_capacity",))
    assert col.is_grouped is True
    data = col.data
    for key in ("group", "cycle_num", "variable", "mean", "std"):
        assert key in data.columns

    g1 = data.filter(
        (pl.col("group") == 1) & (pl.col("variable") == "charge_capacity")
    ).sort("cycle_num")
    assert g1["mean"].to_list() == [15.0, 30.0]
    assert g1["std"].to_list() == pytest.approx([7.0710678, 14.1421356])

    g2 = data.filter(
        (pl.col("group") == 2) & (pl.col("variable") == "charge_capacity")
    ).sort("cycle_num")
    assert g2["mean"].to_list() == [5.0, 7.0]
    assert g2["std"].to_list() == [None, None]


def test_is_grouped_false_by_default(real_batch):
    assert collect_summaries(real_batch).is_grouped is False


def test_grouped_flag_survives_save_load(tmp_path):
    pages = pl.DataFrame({FILENAME: ["x", "y"], "group": [1, 1], "sub_group": [1, 2]})
    b = _batch_with_cells(
        {"x": _SummaryCell([10.0, 20.0]), "y": _SummaryCell([20.0, 40.0])}, pages
    )
    col = collect_summaries(b, group_it=True, columns=("charge_capacity",))
    col.save(tmp_path, formats=("parquet",))
    loaded = load_collection(tmp_path / f"{col.name}.parquet")
    assert loaded.is_grouped is True


# ---- BatchCollector convenience + recipes (#707) ------------------------


def test_batch_collector_autoruns_and_exposes_data(real_batch):
    bc = BatchCollector(real_batch, collect_summaries, columns=("charge_capacity",))
    assert bc.collection.kind == "summary"
    assert "charge_capacity" in bc.data.columns


def test_batch_collector_no_autorun_then_update(real_batch):
    bc = BatchCollector(real_batch, collect_summaries, autorun=False)
    assert bc._collection is None
    bc.update(max_cycle=3)
    assert bc.data["cycle_num"].max() <= 3


def test_batch_collector_plot_renders(real_batch):
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    bc = summary_collector(real_batch, columns=("charge_capacity",))
    figure = bc.plot()
    assert figure is not None
    assert len(figure.data) > 0


def test_batch_collector_save(real_batch, tmp_path):
    bc = summary_collector(real_batch, columns=("charge_capacity",))
    written = bc.save(tmp_path)
    assert any(p.suffix == ".json" for p in written)


def test_normalize_column_wide():
    frame = pl.DataFrame({"cycle_num": [1, 2], "discharge_capacity": [60.0, 120.0]})
    out = normalize_column("discharge_capacity", 120.0)(frame)
    assert out["discharge_capacity_norm"].to_list() == [50.0, 100.0]


def test_normalize_column_long():
    frame = pl.DataFrame(
        {
            "group": [1, 1],
            "cycle_num": [1, 2],
            "variable": ["discharge_capacity", "discharge_capacity"],
            "mean": [60.0, 120.0],
            "std": [0.0, 0.0],
        }
    )
    out = normalize_column("discharge_capacity", 120.0)(frame)
    norm = out.filter(pl.col("variable") == "discharge_capacity_norm").sort("cycle_num")
    assert norm["mean"].to_list() == [50.0, 100.0]


# ---- Batch.tests: per-test metadata surface (F6 D2, #711) ---------------


class _TestRecord:
    def __init__(self, test_id, cell_name, cycle_mode="anode"):
        self.test_id = test_id
        self.cell_name = cell_name
        self.cycle_mode = cycle_mode
        self.raw_file_names = [f"{cell_name}.res"]


class _MultiTestCell:
    """A cell whose ``data.tests`` yields several per-test metadata records."""

    def __init__(self, records):
        self.data = SimpleNamespace(tests=records)


def test_batch_tests_surfaces_per_test_metadata():
    pages = pl.DataFrame({FILENAME: ["m"], "group": [1], "sub_group": [1]})
    cell = _MultiTestCell(
        [_TestRecord(0, "cell_A"), _TestRecord(1, "cell_B", cycle_mode="full")]
    )
    b = _batch_with_cells({"m": cell}, pages)

    frame = b.tests
    assert frame.height == 2  # one row per test_id
    for key in ("cell", "group", "sub_group", "test_id", "cell_name", "cycle_mode"):
        assert key in frame.columns
    assert set(frame["test_id"].to_list()) == {0, 1}
    assert frame.filter(pl.col("test_id") == 1)["cycle_mode"].item() == "full"
    # list field flattened to a string
    assert frame["raw_file_names"].dtype == pl.Utf8


def test_batch_tests_empty_without_metadata():
    pages = pl.DataFrame({FILENAME: ["x"]})
    b = _batch_with_cells({"x": _SummaryCell([1.0])}, pages)  # no .data.tests
    assert b.tests.height == 0


def test_standard_gravimetric_recipe():
    pages = pl.DataFrame(
        {FILENAME: ["x", "y"], "group": [1, 1], "sub_group": [1, 2]}
    )
    b = _batch_with_cells(
        {"x": _SummaryCell([60.0, 120.0]), "y": _SummaryCell([80.0, 160.0])}, pages
    )
    bc = standard_gravimetric(
        b, norm_factor=120.0, columns=("charge_capacity",), retention_on="charge_capacity"
    )
    data = bc.data
    # grouped long format with a normalized retention variable added
    variables = set(data["variable"].to_list())
    assert "charge_capacity" in variables
    assert "charge_capacity_norm" in variables


# ---- collect_cycles: the cross-cell narrowing bug is fixed by design ----


class _FakeCell:
    """A cell with a fixed set of available cycles."""

    def __init__(self, cycles):
        self._cycles = list(cycles)

    def get_cycle_numbers(self):
        return list(self._cycles)

    def get_cap(self, cycle):
        return pl.DataFrame({"capacity": [0.0, float(cycle)], "voltage": [0.1, 0.2]})


def test_collect_cycles_per_cell_isolation():
    """cell_a lacks cycle 3; cell_b must still keep it (collectors.py:1609 bug)."""
    pages = pl.DataFrame(
        {FILENAME: ["a", "b"], "group": [1, 1], "sub_group": [1, 2]}
    )
    b = _batch_with_cells(
        {"a": _FakeCell([1, 2]), "b": _FakeCell([1, 2, 3])}, pages
    )

    col = collect_cycles(b, cycles=(1, 2, 3))
    data = col.data

    a_cycles = set(data.filter(pl.col("cell") == "a")["cycle_num"].to_list())
    b_cycles = set(data.filter(pl.col("cell") == "b")["cycle_num"].to_list())
    assert a_cycles == {1, 2}
    # the bug: after cell_a narrowed the shared list, cell_b lost cycle 3
    assert b_cycles == {1, 2, 3}


# ---- save formats (#789) ------------------------------------------------


def _small_collection() -> Collection:
    frame = pl.DataFrame(
        {"cell": ["a", "b"], "cycle_num": [1, 1], "value": [1.5, 2.5]}
    )
    return Collection(
        data=frame, kind="summary", name="c", meta=CollectionMeta(kind="summary")
    )


def test_collection_save_json_round_trips(tmp_path):
    col = _small_collection()
    written = col.save(tmp_path, formats=("json",))
    json_path = tmp_path / "c.json"
    assert json_path in written
    assert json_path.is_file() and json_path.stat().st_size > 0
    back = pl.read_json(json_path)
    assert back.shape == col.data.shape
    assert set(back.columns) == set(col.data.columns)


def test_collection_save_xlsx(tmp_path):
    col = _small_collection()
    try:
        col.save(tmp_path, formats=("xlsx",))
    except RuntimeError:
        pytest.skip("no Excel writer (xlsxwriter/openpyxl) installed")
    xlsx_path = tmp_path / "c.xlsx"
    assert xlsx_path.is_file() and xlsx_path.stat().st_size > 0


def test_collection_save_rejects_unknown_format(tmp_path):
    col = _small_collection()
    with pytest.raises(ValueError, match="unsupported collection format"):
        col.save(tmp_path, formats=("bogus",))


# ---- family-declared collect options (#868) -----------------------------


def _source_column(name: str) -> str:
    """The summary column a declared family column is derived from."""
    for suffix in ("_non_cv", "_cv"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return re.sub(r"^mod_\d{2}_", "", name)


@pytest.mark.essential
def test_every_summary_family_is_collectable_with_its_own_options(
    real_batch, real_cell
):
    """A family's own options must satisfy the columns the family declares.

    The only columns allowed to stay missing are those whose source is absent
    from the cell's summary in the first place (this cell has no ``*_absolute``
    metrics) — that is a data limit, not a menu the app cannot reach.
    """
    hdr = real_cell.schema.summary
    available = set(real_cell.data.summary.columns)

    for family in registry.iter_families(entry_point="summary_plot"):
        options = family.summary_options(hdr)
        collected = set(collect_summaries(real_batch, options=options).data.columns)
        declared = family.columns(hdr)
        missing = {name for name in declared if name not in collected}
        unavailable = {
            name for name in declared if _source_column(name) not in available
        }
        assert missing == unavailable, family.name


@pytest.mark.essential
def test_fullcell_standard_family_materialises_its_retention_column(
    real_batch, real_cell
):
    hdr = real_cell.schema.summary
    family = registry.get("fullcell_standard_gravimetric")
    data = collect_summaries(real_batch, options=family.summary_options(hdr)).data

    source = "discharge_capacity_gravimetric"
    target = "mod_01_" + source
    assert target in data.columns
    assert data[target].max() == pytest.approx(100.0)
    expected = (100 * data[source] / data[source].max()).to_list()
    assert data[target].to_list() == pytest.approx(expected)


@pytest.mark.essential
def test_summary_options_declares_the_cv_partition_it_needs(real_cell):
    hdr = real_cell.schema.summary
    split = registry.get("capacities_gravimetric_split_constant_voltage")
    fullcell = registry.get("fullcell_standard_gravimetric")
    plain = registry.get("capacities_gravimetric")

    assert split.summary_options(hdr).partition_by_cv
    assert fullcell.summary_options(hdr).partition_by_cv
    assert not plain.summary_options(hdr).partition_by_cv


@pytest.mark.essential
def test_summary_options_transforms_are_callables(real_cell):
    """The shape mismatch from #868: transforms must be frame -> frame."""
    hdr = real_cell.schema.summary
    options = registry.get("fullcell_standard_gravimetric").summary_options(hdr)
    assert options.transforms
    assert all(callable(transform) for transform in options.transforms)


@pytest.mark.essential
def test_summary_options_honours_an_explicit_norm_factor(real_cell):
    hdr = real_cell.schema.summary
    family = registry.get("fullcell_standard_gravimetric")
    frame = pl.DataFrame({"discharge_capacity_gravimetric": [50.0, 100.0]})
    for transform in family.summary_options(hdr, norm_factor=200.0).transforms:
        frame = transform(frame)
    assert frame["mod_01_discharge_capacity_gravimetric"].to_list() == [25.0, 50.0]


@pytest.mark.essential
def test_normalize_column_on_max_wide_and_grouped():
    wide = pl.DataFrame({"charge_capacity": [1.0, 2.0, 4.0]})
    normalized = normalize_column_on_max("charge_capacity", out="norm")(wide)
    assert normalized["norm"].to_list() == [25.0, 50.0, 100.0]

    long = pl.DataFrame(
        {
            "variable": ["charge_capacity", "charge_capacity"],
            "mean": [1.0, 2.0],
            "std": [0.1, 0.2],
        }
    )
    normalized = normalize_column_on_max("charge_capacity", out="norm")(long)
    added = normalized.filter(pl.col("variable") == "norm")
    assert added["mean"].to_list() == [50.0, 100.0]
    assert added["std"].to_list() == pytest.approx([5.0, 10.0])

    assert normalize_column_on_max("nope")(wide).equals(wide)


# ---- named plot family on the collector (#927) --------------------------


@pytest.mark.essential
def test_summary_collector_accepts_a_named_family(real_batch, real_cell):
    """``family=`` must collect exactly what ``family.summary_options`` asks for."""
    hdr = real_cell.schema.summary
    family = registry.get("fullcell_standard_gravimetric")
    expected = collect_summaries(real_batch, options=family.summary_options(hdr)).data

    data = summary_collector(real_batch, family="fullcell_standard_gravimetric").data

    assert data.columns == expected.columns
    assert data.equals(expected)


@pytest.mark.essential
def test_summary_collector_y_is_an_alias_for_family(real_batch):
    """Same names as ``summary_plot(y=...)``, so ``y=`` must work too (#927)."""
    by_family = summary_collector(real_batch, family="capacities_gravimetric").data
    by_y = summary_collector(real_batch, y="capacities_gravimetric").data
    assert by_family.equals(by_y)


@pytest.mark.essential
def test_summary_collector_rejects_an_unknown_family(real_batch):
    with pytest.raises(ValueError, match="unknown plot family"):
        summary_collector(real_batch, family="not_a_family")


@pytest.mark.essential
def test_explicit_columns_win_over_the_family(real_batch):
    data = summary_collector(
        real_batch,
        family="capacities_gravimetric",
        columns=("charge_capacity_gravimetric",),
    ).data
    assert "charge_capacity_gravimetric" in data.columns
    assert "discharge_capacity_gravimetric" not in data.columns


@pytest.mark.essential
def test_a_family_needs_a_cell_to_resolve_its_columns():
    pages = pl.DataFrame({FILENAME: ["x"], "group": [1], "sub_group": [1]})
    b = _batch_with_cells({"x": _SummaryCell([1.0, 2.0])}, pages)  # no .schema
    with pytest.raises(ValueError, match="without a loaded cell"):
        summary_collector(b, family="capacities_gravimetric")


# ---- collector help lists the kwargs users actually pass (#924) ---------


@pytest.mark.essential
@pytest.mark.parametrize(
    ("collector", "expected"),
    [
        (
            summary_collector,
            ("family", "columns", "group_it", "custom_group_labels", "rate"),
        ),
        (cycles_collector, ("cycles", "rate", "mode", "method")),
        (ica_collector, ("cycles", "voltage_resolution")),
        (dva_collector, ("cycles", "capacity_resolution")),
    ],
    ids=["summary", "cycles", "ica", "dva"],
)
def test_collector_help_names_the_common_kwargs(collector, expected):
    """Shift-Tab in Jupyter must show more than ``**overrides`` (#924)."""
    import inspect

    parameters = inspect.signature(collector).parameters
    doc = inspect.getdoc(collector) or ""
    for name in expected:
        assert name in parameters, f"{collector.__name__} signature misses {name}"
        assert f"{name} " in doc, f"{collector.__name__} docstring misses {name}"
    # and the escape hatch to the full option set is named
    assert "Options" in doc
# ---- figure export is discoverable from the collector (#926) ------------


class _FakeFig:
    def __init__(self, payload=b"IMAGE"):
        self.payload = payload
        self.calls = []

    def to_image(self, format="png", scale=1.0, **kwargs):
        self.calls.append({"format": format, "scale": scale, **kwargs})
        return self.payload


@pytest.mark.essential
def test_batch_collector_to_image(real_batch, monkeypatch):
    bc = summary_collector(real_batch, columns=("charge_capacity",))
    fig = _FakeFig(b"from-collector")
    monkeypatch.setattr(bc.collection, "plot", lambda **kwargs: fig)

    assert bc.to_image("svg", scale=2.0) == b"from-collector"
    assert fig.calls[0] == {"format": "svg", "scale": 2.0}


@pytest.mark.essential
def test_batch_collector_save_figure_writes_a_file(real_batch, monkeypatch, tmp_path):
    bc = summary_collector(real_batch, columns=("charge_capacity",))
    monkeypatch.setattr(bc.collection, "plot", lambda **kwargs: _FakeFig(b"PNGBYTES"))

    written = bc.save_figure(tmp_path / "cycle_life")
    assert written == tmp_path / "cycle_life.png"
    assert written.read_bytes() == b"PNGBYTES"


@pytest.mark.essential
def test_save_help_says_data_only_and_names_the_figure_api():
    """``.save?`` used to say nothing about figures at all (#926)."""
    import inspect

    for save in (BatchCollector.save, Collection.save):
        doc = inspect.getdoc(save) or ""
        assert "data only" in doc
        assert "save_figure" in doc
        assert "to_image" in doc
