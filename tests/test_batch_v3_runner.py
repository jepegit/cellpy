"""Tests for batch v3 runner/result/store (#700)."""

import polars as pl
import pytest

from cellpy.batch import (
    BatchLoadError,
    BatchResult,
    CellOutcome,
    CellResult,
    CellSpec,
    CellStore,
    Journal,
    LoadPolicy,
    SourcePreference,
    load_cell,
    run,
)
from cellpy.batch.journal import FILENAME


# ---- result.py ----------------------------------------------------------


def _mk_results():
    return BatchResult(
        [
            CellResult("a", CellOutcome.LOADED, cell=object(), source="cellpy", seconds=0.1),
            CellResult("b", CellOutcome.FAILED, error=ValueError("boom"), seconds=0.2),
            CellResult("c", CellOutcome.SKIPPED),
        ]
    )


def test_batchresult_partitions_and_report():
    br = _mk_results()
    assert [r.label for r in br.loaded] == ["a"]
    assert [r.label for r in br.failed] == ["b"]
    assert [r.label for r in br.skipped] == ["c"]
    assert set(br.cells()) == {"a"}
    assert br["b"].error.args[0] == "boom"

    rep = br.report()
    assert isinstance(rep, pl.DataFrame)
    assert rep.height == 3
    assert set(rep.columns) == {"cell", "outcome", "source", "seconds", "error"}
    assert rep.filter(pl.col("cell") == "b")["error"].item() == "boom"


def test_raise_if_failed():
    with pytest.raises(BatchLoadError, match="b"):
        _mk_results().raise_if_failed()
    ok = BatchResult([CellResult("a", CellOutcome.LOADED)])
    assert ok.raise_if_failed() is ok


# ---- store.py (incl. the lstrip bug fix) --------------------------------


def test_cellstore_is_lazy():
    calls = []

    def make(label):
        return lambda: (calls.append(label), f"cell::{label}")[1]

    store = CellStore({"a": make("a"), "b": make("b")})
    assert list(store) == ["a", "b"]
    assert len(store) == 2
    assert calls == []  # nothing loaded yet
    assert store["a"] == "cell::a"
    assert calls == ["a"]
    assert store["a"] == "cell::a"  # cached, not reloaded
    assert calls == ["a"]
    assert store.is_loaded("a") and not store.is_loaded("b")
    store.unload("a")
    assert not store.is_loaded("a")


def test_cellstore_no_label_mangling():
    """The legacy x_/lstrip accessor turned 'xenon_cell' into 'enon_cell'."""
    store = CellStore.from_cells({"xenon_cell": "X", "x_ray": "R"})
    assert set(store) == {"xenon_cell", "x_ray"}
    assert store["xenon_cell"] == "X"
    assert store["x_ray"] == "R"
    assert set(store._ipython_key_completions_()) == {"xenon_cell", "x_ray"}


# ---- runner.py source selection -----------------------------------------


@pytest.mark.essential
def test_auto_uses_existing_cellpy_without_raw(tmp_path):
    from cellpy.batch.runner import _get_kwargs

    cellpy_path = tmp_path / "cell.cellpy"
    cellpy_path.write_bytes(b"x")
    spec = CellSpec(
        label="a",
        cellpy_file=str(cellpy_path),
        raw_files=["scp://host/raw.h5"],
    )
    kwargs, source = _get_kwargs(spec, LoadPolicy(source=SourcePreference.AUTO))
    assert source == "cellpy"
    assert kwargs["cellpy_file"] == str(cellpy_path)
    assert "filename" not in kwargs


@pytest.mark.essential
def test_auto_falls_back_to_raw_when_cellpy_missing(tmp_path):
    from cellpy.batch.runner import _get_kwargs

    raw = ["scp://host/raw.h5"]
    spec = CellSpec(
        label="a",
        cellpy_file=str(tmp_path / "missing.cellpy"),
        raw_files=raw,
    )
    kwargs, source = _get_kwargs(spec, LoadPolicy(source=SourcePreference.AUTO))
    assert source == "raw"
    assert kwargs["filename"] == raw
    assert "cellpy_file" not in kwargs


@pytest.mark.essential
def test_newest_passes_both_paths(tmp_path):
    from cellpy.batch.runner import _get_kwargs

    cellpy_path = tmp_path / "cell.cellpy"
    cellpy_path.write_bytes(b"x")
    raw = ["scp://host/raw.h5"]
    spec = CellSpec(
        label="a",
        cellpy_file=str(cellpy_path),
        raw_files=raw,
    )
    kwargs, source = _get_kwargs(spec, LoadPolicy(source=SourcePreference.NEWEST))
    assert source == "cellpy"
    assert kwargs["cellpy_file"] == str(cellpy_path)
    assert kwargs["filename"] == raw


# ---- runner.py (integration with cellpy.get) ----------------------------


def _one_cell_journal(label, cellpy_file):
    return Journal(
        name="t",
        project="p",
        pages=pl.DataFrame({FILENAME: [label], "cellpy_file_name": [str(cellpy_file)]}),
    )


def test_load_cell_from_cellpy_file(parameters):
    spec = CellSpec(label="c45", cellpy_file=parameters.cellpy_file_path)
    result = load_cell(spec, LoadPolicy(source=SourcePreference.CELLPY_ONLY))
    assert result.ok
    assert result.source == "cellpy"
    assert result.cell is not None
    assert result.seconds >= 0


def test_load_cell_error_is_captured(tmp_path):
    spec = CellSpec(label="bad", cellpy_file=str(tmp_path / "nope.h5"))
    result = load_cell(spec, LoadPolicy(source=SourcePreference.CELLPY_ONLY))
    assert result.outcome == CellOutcome.FAILED
    assert result.error is not None


def test_load_cell_reraises_when_not_accepting(tmp_path):
    spec = CellSpec(label="bad", cellpy_file=str(tmp_path / "nope.h5"))
    with pytest.raises(Exception):
        load_cell(
            spec,
            LoadPolicy(source=SourcePreference.CELLPY_ONLY, accept_errors=False),
        )


def test_run_over_journal(parameters):
    j = _one_cell_journal("c45", parameters.cellpy_file_path)
    seen = []
    br = run(
        j,
        LoadPolicy(source=SourcePreference.CELLPY_ONLY),
        on_progress=lambda i, n, r: seen.append((i, n, r.label)),
    )
    assert len(br) == 1
    assert br["c45"].ok
    assert seen == [(1, 1, "c45")]


def test_run_skips_bad_cells(parameters):
    j = _one_cell_journal("c45", parameters.cellpy_file_path)
    j.session["bad_cells"] = ["c45"]
    br = run(j, LoadPolicy(source=SourcePreference.CELLPY_ONLY, skip_bad_cells=True))
    assert br["c45"].outcome == CellOutcome.SKIPPED




@pytest.mark.essential
def test_recalc_remakes_steps_and_summary(monkeypatch):
    """force_recalc / policy.recalc must remake steps then summary after get."""
    calls = []

    class _Cell:
        def make_step_table(self):
            calls.append("steps")

        def make_summary(self):
            calls.append("summary")

    monkeypatch.setattr(
        "cellpy.batch.runner._cellpy_get",
        lambda **kwargs: _Cell(),
    )
    spec = CellSpec(label="a", cellpy_file="x.cellpy", nom_cap=120.0)
    result = load_cell(spec, LoadPolicy(source=SourcePreference.CELLPY_ONLY, recalc=True))
    assert result.ok
    assert calls == ["steps", "summary"]


@pytest.mark.essential
def test_no_recalc_skips_remake(monkeypatch):
    calls = []

    class _Cell:
        def make_step_table(self):
            calls.append("steps")

        def make_summary(self):
            calls.append("summary")

    monkeypatch.setattr(
        "cellpy.batch.runner._cellpy_get",
        lambda **kwargs: _Cell(),
    )
    spec = CellSpec(label="a", cellpy_file="x.cellpy", nom_cap=120.0)
    result = load_cell(spec, LoadPolicy(source=SourcePreference.CELLPY_ONLY, recalc=False))
    assert result.ok
    assert calls == []

# ---- executors (#704) ---------------------------------------------------


def _two_cell_journal(cellpy_file):
    return Journal(
        name="t",
        project="p",
        pages=pl.DataFrame(
            {
                FILENAME: ["c_a", "c_b"],
                "cellpy_file_name": [str(cellpy_file), str(cellpy_file)],
            }
        ),
    )


def test_run_threads_keeps_live_cells(parameters):
    j = _two_cell_journal(parameters.cellpy_file_path)
    seen = []
    br = run(
        j,
        LoadPolicy(source=SourcePreference.CELLPY_ONLY),
        executor="threads",
        on_progress=lambda i, n, r: seen.append(i),
    )
    assert {r.label for r in br.loaded} == {"c_a", "c_b"}
    assert all(r.cell is not None for r in br.loaded)  # live cells in threads
    assert sorted(seen) == [1, 2]


def test_run_processes_returns_outcomes(parameters):
    j = _one_cell_journal("c45", parameters.cellpy_file_path)
    br = run(j, LoadPolicy(source=SourcePreference.CELLPY_ONLY), executor="processes")
    assert br["c45"].ok
    # processes mode returns pickle-safe results (no live cell across the boundary)
    assert br["c45"].cell is None


def test_run_unknown_executor(parameters):
    j = _one_cell_journal("c45", parameters.cellpy_file_path)
    with pytest.raises(ValueError, match="unknown executor"):
        run(j, executor="magic")
