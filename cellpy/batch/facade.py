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
from cellpy.batch.policy import LoadPolicy
from cellpy.batch.result import BatchResult
from cellpy.batch.runner import run
from cellpy.batch.store import CellStore


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
    """

    def __init__(self, journal: Journal, store: CellStore) -> None:
        self.journal = _LegacyJournalAdapter(journal)
        self.data = store
        self.cell_names = list(store)
        summaries = []
        summary_frames = {}
        for label, cell in store.items():
            summary = getattr(getattr(cell, "data", None), "summary", None)
            if summary is None:
                continue
            pdf = summary.to_pandas() if hasattr(summary, "to_pandas") else summary
            pdf.name = label
            summaries.append(pdf)
            summary_frames[label] = pdf
        self.memory_dumped = {"summary_engine": summaries}
        self.summary_frames = summary_frames


# -- module-level constructors -------------------------------------------


def from_journal(
    journal_file: Path | str, policy: LoadPolicy | None = None, **_kwargs
) -> Batch:
    """Build a :class:`Batch` from a journal file (.json or .xlsx)."""
    return Batch(read_journal(journal_file), policy=policy)


def load(
    name: str | None = None,
    project: str | None = None,
    *,
    journal: Journal | None = None,
    journal_file: Path | str | None = None,
    frame: Any | None = None,
    db: str | bool | None = None,
    policy: LoadPolicy | None = None,
    **kwargs,
) -> Batch:
    """Build a :class:`Batch` from a journal source.

    Source precedence: explicit ``journal`` model, ``journal_file``, ``frame``,
    then a database read (``db`` reader name, or when only ``name``/``project``
    are given). Falls back to an empty named journal.
    """
    if journal is not None:
        return Batch(journal, policy=policy)
    if journal_file is not None:
        return Batch(read_journal(journal_file), policy=policy)
    if frame is not None:
        return Batch(journal_from_frame(frame, name=name, project=project), policy=policy)
    if db is not None or (name and project):
        reader = db if isinstance(db, str) else "default"
        return Batch.from_db(name, project, db_reader=reader, policy=policy, **kwargs)
    return Batch(Journal(name=name, project=project), policy=policy)
