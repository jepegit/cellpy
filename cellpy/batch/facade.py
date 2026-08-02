"""Batch facade.

The thin, notebook-friendly ``Batch`` class that ties the pieces together:
journal + policy/resolve_specs + runner/result/store +
aggregate/qc/outputs. Keeps the beloved surface the characterization net
pinned -- ``pages``, ``cells``, ``summaries``, ``update``, ``report``,
``save``, ``mark_as_bad``, ``drop`` -- while everything underneath is the new
package.

Plot wiring: ``plot()`` delegates to the plotting layer via a small legacy
adapter; the full tidy-frame plot path lands with the collectors redesign
(Epic B, batch plan section 4.7).
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import polars as pl

from cellpy.batch import aggregate, qc
from cellpy.batch.journal import (
    FILENAME,
    Journal,
    journal_from_frame,
    read_journal,
    write_journal,
)
from cellpy.batch.layout import BatchPaths, ensure_dirs
from cellpy.batch.policy import LoadPolicy, SourcePreference
from cellpy.batch.result import BatchResult
from cellpy.batch.runner import run
from cellpy.batch.store import CellStore
from cellpy.parameters.internal_settings import get_headers_journal

_log = logging.getLogger(__name__)
_HDR_JOURNAL = get_headers_journal()
_CELLPY_FILE_COL = _HDR_JOURNAL["cellpy_file_name"]
_EXPORT_KWARGS = frozenset({"export_cycles", "export_raw", "export_ica"})
_EXPORT_KWARGS_WARNED = False


class Batch:
    """A batch of cells: a journal, a lazy cell store, and derived frames."""

    def __init__(
        self,
        journal: Journal,
        policy: LoadPolicy | None = None,
        _db: dict | None = None,
    ) -> None:
        self.journal = journal
        self.policy = policy or LoadPolicy()
        self._store = CellStore()
        self._result: BatchResult | None = None
        self._summaries: pl.DataFrame | None = None
        self._db = _db  # deferred db-read config for create_journal()

    @classmethod
    def from_db(
        cls, name: str, project: str, policy: LoadPolicy | None = None, **db_kwargs
    ) -> "Batch":
        """Build a batch by reading a database (Excel or JSON)."""
        from cellpy.batch.db import journal_from_db

        return cls(journal_from_db(name, project, **db_kwargs), policy=policy)

    @classmethod
    def from_cells(
        cls,
        cells: Mapping[str, Any] | Sequence[Any],
        *,
        groups: Mapping[str, Any] | None = None,
        sub_groups: Mapping[str, Any] | None = None,
        group_labels: Mapping[Any, str] | None = None,
        selected: Mapping[str, bool] | None = None,
        name: str = "in_memory",
        project: str = "in_memory",
        policy: LoadPolicy | None = None,
    ) -> "Batch":
        """Build a batch from already-loaded ``CellpyCell`` objects.

        The pieces a batch needs -- a journal ``pages`` frame (polars, keyed by
        ``filename``) plus a populated cell store -- are constructed here, so a
        GUI/notebook holding cells in memory can feed them straight to
        :func:`cellpy.collect.collect_summaries` / ``collect_cycles`` or
        ``batch.plot()`` without writing a journal to disk.

        Args:
            cells: ``{label: CellpyCell}`` or a sequence of cells (labels are
                taken from ``cell.cell_name``, falling back to ``cell_001`` ...,
                de-duplicated).
            groups / sub_groups: optional ``{label: value}`` maps (defaults:
                group 1 for all; sub_group 1..N).
            group_labels: optional ``{group: display label}`` map.
            selected: optional ``{label: bool}`` (defaults True) for the journal
                ``selected`` column.
            name / project: journal name/project.
        """
        if isinstance(cells, Mapping):
            cell_map: dict[str, Any] = dict(cells)
        else:
            cell_map = {}
            for i, cell in enumerate(cells, start=1):
                label = getattr(cell, "cell_name", None) or f"cell_{i:03d}"
                base, n = label, 1
                while label in cell_map:
                    n += 1
                    label = f"{base}_{n}"
                cell_map[label] = cell

        labels = list(cell_map)
        groups = dict(groups or {})
        sub_groups = dict(sub_groups or {})
        selected = dict(selected or {})

        group_col = [groups.get(lbl, 1) for lbl in labels]
        pages_data: dict[str, list] = {
            FILENAME: labels,
            "group": group_col,
            "sub_group": [sub_groups.get(lbl, i) for i, lbl in enumerate(labels, 1)],
            "label": labels,
            "selected": [bool(selected.get(lbl, True)) for lbl in labels],
        }
        if group_labels:
            gl = dict(group_labels)
            pages_data["group_label"] = [gl.get(g) for g in group_col]

        pages = pl.DataFrame(pages_data)
        batch = cls(Journal(name=name, project=project, pages=pages), policy=policy)
        batch._store = CellStore.from_cells(cell_map)
        return batch

    # -- data surface ----------------------------------------------------
    @property
    def pages(self) -> pl.DataFrame:
        return self.journal.pages

    @property
    def cell_names(self) -> list[str]:
        return self.journal.cell_names

    @property
    def cells(self) -> CellStore:
        return self._store

    @property
    def result(self) -> BatchResult | None:
        return self._result

    def update(
        self, on_progress=None, executor: str = "serial", **overrides
    ) -> BatchResult:
        """Load every cell, caching them in the store.

        ``executor`` is ``"serial"`` (default), ``"threads"`` or ``"processes"``.
        Known :class:`LoadPolicy` fields in ``overrides`` update the policy;
        unknown (legacy) kwargs like ``testing`` are forwarded to the loader
        (``cellpy.get``) via ``loader_kwargs``.
        """
        policy = self.policy
        if overrides:
            known = {f.name for f in fields(LoadPolicy)}
            policy_over = {k: v for k, v in overrides.items() if k in known}
            extra = {k: v for k, v in overrides.items() if k not in known}
            if policy_over:
                policy = replace(policy, **policy_over)
            if extra:
                policy = replace(
                    policy, loader_kwargs={**policy.loader_kwargs, **extra}
                )
        self._result = run(
            self.journal, policy, on_progress=on_progress, executor=executor
        )
        self._store = CellStore.from_cells(self._result.cells())
        self._summaries = None
        return self._result

    def load(self, **overrides) -> BatchResult:
        """Load cells (alias of :meth:`update`, kept for the legacy surface)."""
        return self.update(**overrides)

    def recalc(self, **overrides) -> BatchResult:
        return self.update(recalc=True, **overrides)

    @property
    def summaries(self) -> pl.DataFrame:
        if self._summaries is None:
            self._summaries = aggregate.combine_summaries(self._store, self.journal)
        return self._summaries

    def combine_summaries(self, **_kwargs) -> pl.DataFrame:
        self._summaries = aggregate.combine_summaries(self._store, self.journal)
        return self._summaries

    @property
    def tests(self) -> pl.DataFrame:
        """Per-test metadata across the batch (tidy long-format).

        One row per (cell, ``test_id``) with the native ``TestMeta`` fields plus
        ``cell``/``group``/``sub_group`` keys -- the per-test records a merged
        (campaign) cell carries. Empty frame if no cell exposes test metadata.
        """
        return aggregate.combine_tests(self._store, self.journal)

    def make_summaries(self) -> pl.DataFrame:
        return self.combine_summaries()

    def report(self, check: bool = True) -> pl.DataFrame:
        return qc.check(self._store, self.journal)

    # -- journal ops -----------------------------------------------------
    def save(self, path: Path | str | None = None) -> Path:
        target = Path(path) if path else Path(
            f"cellpy_batch_{self.journal.name or 'batch'}.json"
        )
        return write_journal(self.journal, target)

    def export_journal(self, path: Path | str | None = None) -> Path:
        return self.save(path)

    def create_journal(self, **kwargs) -> Journal:
        """Populate the journal from the configured database (if any).

        Mirrors the legacy ``init()`` -> ``create_journal()`` flow: ``init``
        stores the db config, ``create_journal`` performs the read.
        """
        if self._db is not None:
            from cellpy.batch.db import journal_from_db

            config = {**self._db, **kwargs}
            self.journal = journal_from_db(
                self.journal.name, self.journal.project, **config
            )
            self._summaries = None
        return self.journal

    def paginate(self) -> tuple[Path, ...]:
        paths = BatchPaths.create(
            self.journal.name or "batch", self.journal.project or ""
        )
        return ensure_dirs(paths)

    def mark_as_bad(self, label: str) -> None:
        bad = list(self.journal.session.get("bad_cells") or [])
        if label not in bad:
            bad.append(label)
        self.journal.session["bad_cells"] = bad

    def drop(self, label: str) -> "Batch":
        self.journal.pages = self.journal.pages.filter(pl.col(FILENAME) != label)
        self._store.unload(label)
        self._summaries = None
        return self

    def drop_cells_marked_bad(self) -> "Batch":
        """Drop every label listed in ``journal.session["bad_cells"]``."""
        bad = list(self.journal.session.get("bad_cells") or [])
        for label in bad:
            if label in self.journal.cell_names:
                self.drop(label)
        return self

    def link(self) -> "Batch":
        """No-op in batch v3 (the store loads lazily); kept for the surface."""
        return self

    # -- plotting (delegated; full wiring is Epic B) ---------------------
    def plot(self, backend: str | None = None, show: bool = False, **kwargs) -> Any:
        from cellpy.plotting.batch_summary import batch_summary_plot

        return batch_summary_plot(
            _LegacyExperimentAdapter(self.journal, self._store),
            backend=backend,
            show=show,
            **kwargs,
        )

    @property
    def experiment(self) -> "_LegacyExperimentAdapter":
        """Backward-compat view for legacy consumers (helpers/collectors).

        ``cellpy.utils.helpers`` and ``cellpy.utils.collectors`` still reach
        into ``b.experiment.{cell_names,data,journal.pages,summary_frames}``.
        This adapter keeps them working against the new Batch until they are
        migrated (Epic B/C); it is not part of the blessed API.
        """
        return _LegacyExperimentAdapter(self.journal, self._store)

    def __repr__(self) -> str:
        return (
            f"Batch(name={self.journal.name!r}, project={self.journal.project!r}, "
            f"cells={len(self.journal)})"
        )


class _LegacyJournalAdapter:
    def __init__(self, journal: Journal) -> None:
        pdf = journal.pages.to_pandas()
        if FILENAME in pdf.columns:
            pdf = pdf.set_index(FILENAME, drop=False)
        self.pages = pdf


class _LegacyExperimentAdapter:
    """Minimal shim exposing the legacy ``experiment`` surface over a new Batch.

    Covers what ``helpers``/``collectors`` and the summary plotter read:
    ``journal.pages``, ``cell_names``, ``data``, ``summary_frames`` and
    ``memory_dumped``. Full migration of those consumers is Epic B/C.

    ``memory_dumped["summary_engine"]`` keeps the legacy *farm* layout that
    ``batch_summary_plot`` expects: one DataFrame per summary variable, with
    cell labels as columns and ``cycle_index`` as the index (``df.name`` =
    variable). ``summary_frames`` stays per-cell for helpers/collectors.
    """

    def __init__(self, journal: Journal, store: CellStore) -> None:
        import pandas as pd

        from cellpy.parameters.internal_settings import get_headers_summary

        self.journal = _LegacyJournalAdapter(journal)
        self.data = store
        self.cell_names = list(store)
        summary_frames: dict[str, Any] = {}
        per_cell: dict[str, Any] = {}
        cycle_col = get_headers_summary().cycle_index
        for label, cell in store.items():
            summary = getattr(getattr(cell, "data", None), "summary", None)
            if summary is None:
                continue
            pdf = summary.to_pandas() if hasattr(summary, "to_pandas") else summary
            if not isinstance(pdf, pd.DataFrame) or pdf.empty:
                continue
            pdf = pdf.copy()
            if cycle_col in pdf.columns:
                pdf = pdf.set_index(cycle_col)
            elif pdf.index.name != cycle_col:
                pdf.index.name = cycle_col
            per_cell[label] = pdf
            summary_frames[label] = pdf

        farms: list[Any] = []
        if per_cell:
            wide = pd.concat(per_cell, axis=1)
            wide = wide.swaplevel(0, 1, axis=1).sort_index(axis=1)
            for var in wide.columns.get_level_values(0).unique():
                farm = wide[var].copy()
                farm.name = var
                farms.append(farm)

        self.memory_dumped = {"summary_engine": farms}
        self.summary_frames = summary_frames



# -- module-level constructors -------------------------------------------

_JSON_DB_READERS = frozenset({"custom_json_reader", "batbase_json_reader"})


def from_journal(
    journal_file: Path | str, policy: LoadPolicy | None = None, **_kwargs
) -> Batch:
    """Build a :class:`Batch` from a cellpy journal file (.json or .xlsx).

    For BatBase / custom JSON downloads that need post-read file search, use
    :func:`load` with ``db_reader="batbase_json_reader"`` or
    ``"custom_json_reader"`` (and ``column_map`` for custom JSON).
    """
    return Batch(read_journal(journal_file), policy=policy)


def from_cells(cells, **kwargs) -> Batch:
    """Build a :class:`Batch` from already-loaded cells (see
    :meth:`Batch.from_cells`) -- feed it to ``collect_summaries`` /
    ``collect_cycles`` or call ``batch.plot()``."""
    return Batch.from_cells(cells, **kwargs)


def _journal_path(name: str, journal_dir: Path | str | None = None) -> Path:
    """Default autoload/save path: ``{journal_dir or cwd}/cellpy_batch_{name}.json``."""
    base = Path(journal_dir) if journal_dir is not None else Path.cwd()
    return base / f"cellpy_batch_{name}.json"


def _warn_ignored_export_kwargs(kwargs: dict[str, Any]) -> None:
    global _EXPORT_KWARGS_WARNED
    hit = sorted(_EXPORT_KWARGS.intersection(kwargs))
    if not hit or _EXPORT_KWARGS_WARNED:
        return
    _EXPORT_KWARGS_WARNED = True
    warnings.warn(
        f"batch.load ignores {hit} in batch v3; use collectors / export helpers "
        "instead.",
        UserWarning,
        stacklevel=3,
    )


def _resolve_policy(
    *,
    policy: LoadPolicy | None,
    force_raw_file: bool,
    force_cellpy: bool,
    force_recalc: bool,
    accept_errors: bool | None,
    max_cycle: int | None,
) -> LoadPolicy:
    """Map legacy force_* flags onto a :class:`LoadPolicy`.

    Raises:
        ValueError: if ``policy`` conflicts with force_raw_file / force_cellpy.
    """
    if force_raw_file and force_cellpy:
        raise ValueError("force_raw_file and force_cellpy cannot both be True")

    if force_raw_file:
        wanted = SourcePreference.RAW_ONLY
    elif force_cellpy:
        wanted = SourcePreference.CELLPY_ONLY
    else:
        wanted = None

    if policy is not None and wanted is not None and policy.source != wanted:
        raise ValueError(
            f"conflicting load source: policy.source={policy.source!r} vs "
            f"force flags implying {wanted!r}"
        )

    base = policy or LoadPolicy()
    updates: dict[str, Any] = {}
    if wanted is not None:
        updates["source"] = wanted
    if force_recalc:
        updates["recalc"] = True
    if accept_errors is not None:
        updates["accept_errors"] = accept_errors
    if max_cycle is not None:
        updates["max_cycle"] = max_cycle
    return replace(base, **updates) if updates else base


def _default_cellpy_path(label: str) -> Path:
    """Fallback ``.cellpy`` path under ``config.paths.cellpydatadir``."""
    import cellpy.config as config

    return Path(config.paths.cellpydatadir) / f"{label}.cellpy"


def _persist_cells(batch: Batch, journal_path: Path) -> Path:
    """Save loaded cells as ``.cellpy`` and write the journal JSON.

    When ``cellpy_file_name`` is missing or null (e.g. ``load(frame=...)``),
    paths default to ``{cellpydatadir}/{label}.cellpy``.
    """
    if _CELLPY_FILE_COL not in batch.pages.columns:
        defaults = [str(_default_cellpy_path(lbl)) for lbl in batch.cell_names]
        batch.journal.pages = batch.pages.with_columns(
            pl.Series(_CELLPY_FILE_COL, defaults)
        )

    saved: list[str] = []
    for row in batch.pages.iter_rows(named=True):
        label = row[FILENAME]
        dest_raw = row.get(_CELLPY_FILE_COL)
        dest = (
            Path(dest_raw).with_suffix(".cellpy")
            if dest_raw
            else _default_cellpy_path(label)
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        if label in batch.cells and batch.cells.is_loaded(label):
            _log.info("saving %s -> %s", label, dest)
            batch.cells[label].save(dest, overwrite=True)
        else:
            _log.debug("skip save (not loaded): %s", label)
        saved.append(str(dest))

    batch.journal.pages = batch.journal.pages.with_columns(
        pl.Series(_CELLPY_FILE_COL, saved)
    )
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    return batch.save(journal_path)


def _finalize(
    batch: Batch,
    *,
    policy: LoadPolicy,
    drop_bad_cells: bool,
    save_cellpy: bool,
    journal_path: Path | None,
    update_kwargs: dict[str, Any],
) -> Batch:
    """Shared post-construction pipeline: drop bad → update → persist."""
    batch.policy = policy
    if drop_bad_cells:
        batch.drop_cells_marked_bad()
    batch.update(**update_kwargs)
    batch.combine_summaries()
    if save_cellpy:
        if journal_path is None:
            name = batch.journal.name or "batch"
            journal_path = _journal_path(name)
        _persist_cells(batch, journal_path)
    return batch


def load(
    name: str | None = None,
    project: str | None = None,
    *,
    journal: Journal | None = None,
    journal_file: Path | str | None = None,
    journal_dir: Path | str | None = None,
    frame: Any | None = None,
    db: str | bool | None = None,
    db_reader: str | None = None,
    reader: str | None = None,
    reader_path: str | None = None,
    batch_col: str | None = None,
    policy: LoadPolicy | None = None,
    allow_from_journal: bool = True,
    force_reload: bool = False,
    force_raw_file: bool = False,
    force_cellpy: bool = False,
    force_recalc: bool = False,
    drop_bad_cells: bool = True,
    save_cellpy: bool = True,
    accept_errors: bool | None = None,
    max_cycle: int | None = None,
    **kwargs,
) -> Batch:
    """Load a batch the notebook-friendly way (v1 orchestration on v3).

    Resolves a journal (explicit file, cwd/`journal_dir` autoload, or database),
    runs :meth:`Batch.update`, optionally drops bad cells, and by default
    persists ``.cellpy`` files plus the journal JSON.

    Journal location: ``journal_dir`` or :func:`pathlib.Path.cwd` (typically the
    notebook folder when the kernel was started there). Autoload looks for
    ``cellpy_batch_{name}.json`` in that directory when ``allow_from_journal``
    is True.

    Args:
        name / project: batch identity (required for DB / autoload paths).
        journal: explicit in-memory journal model.
        journal_file: path to a cellpy journal, or a BatBase/custom JSON DB file
            when ``reader`` / ``db_reader`` is a JSON reader.
        journal_dir: directory for journal autoload/save (default: cwd).
        frame: build journal pages from a dataframe.
        db / db_reader / reader: database reader selection (``reader`` aliases
            ``db_reader``).
        reader_path: DB file path for non-default readers.
        batch_col: Excel batch column (default ``b01`` when reading the DB).
        policy: explicit :class:`LoadPolicy` (conflicts with force_* raise).
        allow_from_journal: autoload ``cellpy_batch_{name}.json`` when present.
        force_reload: kept for API parity; journal hits always ``update()``.
        force_raw_file / force_cellpy: map to ``SourcePreference``.
        force_recalc: set ``policy.recalc``.
        drop_bad_cells: drop ``session["bad_cells"]`` before update.
        save_cellpy: write ``.cellpy`` files and journal JSON (default True).
        accept_errors / max_cycle: forwarded into the load policy.
        **kwargs: DB engine knobs (``column_map``, ``raw_file_dir``, …) and
            loader extras (``testing``, …). ``export_cycles`` / ``export_raw`` /
            ``export_ica`` are accepted but ignored (warned once).

    Returns:
        Populated :class:`Batch`.

    Raises:
        ValueError: missing required args, force-flag conflicts, missing journal
            when ``journal_file`` is set but absent.
        FileNotFoundError: ``journal_file`` path does not exist.
    """
    _ = force_reload  # journal hits always update(); flag kept for call-site parity
    _warn_ignored_export_kwargs(kwargs)
    for key in _EXPORT_KWARGS:
        kwargs.pop(key, None)

    if db_reader is None and reader is not None:
        db_reader = reader
    elif db_reader is not None and reader is not None and db_reader != reader:
        raise ValueError(
            f"conflicting db_reader={db_reader!r} and reader={reader!r}; "
            "pass only db_reader= (canonical) or only reader= (alias)"
        )

    resolved = _resolve_policy(
        policy=policy,
        force_raw_file=force_raw_file,
        force_cellpy=force_cellpy,
        force_recalc=force_recalc,
        accept_errors=accept_errors,
        max_cycle=max_cycle,
    )

    # Split kwargs: known LoadPolicy extras / loader vs DB engine args.
    policy_field_names = {f.name for f in fields(LoadPolicy)}
    update_kwargs = {
        k: kwargs.pop(k)
        for k in list(kwargs)
        if k in policy_field_names or k in {"testing", "executor", "on_progress"}
    }
    db_kwargs = dict(kwargs)
    if batch_col is not None:
        db_kwargs.setdefault("batch_col", batch_col)
    if reader_path is not None:
        db_kwargs.setdefault("db_file", reader_path)

    journal_path: Path | None = None
    batch: Batch | None = None

    if journal is not None:
        batch = Batch(journal, policy=resolved)
        if name or project:
            journal_path = _journal_path(
                name or batch.journal.name or "batch", journal_dir
            )
    elif journal_file is not None:
        journal_file = Path(journal_file)
        if not journal_file.is_file():
            raise FileNotFoundError(f"journal_file not found: {journal_file}")
        if db_reader in _JSON_DB_READERS:
            if not name or not project:
                raise ValueError(
                    "name and project are required when loading a JSON db file "
                    f"with db_reader={db_reader!r}"
                )
            batch = Batch.from_db(
                name,
                project,
                db_reader=db_reader,
                db_file=str(journal_file),
                policy=resolved,
                **db_kwargs,
            )
            journal_path = _journal_path(name, journal_dir)
        else:
            batch = Batch(read_journal(journal_file), policy=resolved)
            journal_path = Path(journal_file)
    elif frame is not None:
        batch = Batch(
            journal_from_frame(frame, name=name, project=project), policy=resolved
        )
        if name:
            journal_path = _journal_path(name, journal_dir)
    else:
        # Autoload journal from journal_dir/cwd, else DB.
        if allow_from_journal and name:
            candidate = _journal_path(name, journal_dir)
            if candidate.is_file():
                _log.info("loading journal %s", candidate)
                batch = Batch(read_journal(candidate), policy=resolved)
                journal_path = candidate

        if batch is None:
            if not name or not project:
                if db is not None or db_reader is not None:
                    raise ValueError(
                        "name and project are required when loading from a database"
                    )
                return Batch(Journal(name=name, project=project), policy=resolved)
            chosen = db_reader
            if chosen is None:
                chosen = db if isinstance(db, str) else "default"
            if chosen == "default":
                chosen = "simple_excel_reader"
            if batch_col is None:
                db_kwargs.setdefault("batch_col", "b01")
            batch = Batch.from_db(
                name, project, db_reader=chosen, policy=resolved, **db_kwargs
            )
            journal_path = _journal_path(name, journal_dir)
            ensure_dirs(
                BatchPaths.create(name, project, project_dir=journal_dir or Path.cwd())
            )

    assert batch is not None
    return _finalize(
        batch,
        policy=resolved,
        drop_bad_cells=drop_bad_cells,
        save_cellpy=save_cellpy,
        journal_path=journal_path,
        update_kwargs=update_kwargs,
    )
