"""Convenience collector + recipes.

:class:`BatchCollector` is the thin successor of the legacy
``utils.collectors.BatchCollector`` family: run a collect function, hold the
resulting :class:`~cellpy.collect.collection.Collection`, and offer
``save`` / ``plot`` on top. It replaces the "elevated arguments" machinery --
~20 parameters redeclared per subclass and merged through three priority
layers -- with a single options object plus a collect callable. The
``utils.collectors`` compatibility shim and the handover of ``plot`` to
``cellpy.plotting`` both live here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import polars as pl

from cellpy.collect.curves import collect_cycles
from cellpy.collect.dva import collect_dva
from cellpy.collect.ica import collect_ica
from cellpy.collect.options import CurveOptions, IcaOptions, SummaryOptions
from cellpy.collect.summary import collect_summaries

#: A collect function takes ``(batch, options, **overrides)`` -> Collection.
Collector = Callable[..., Any]


class BatchCollector:
    """Run a collect function and hold its :class:`Collection`.

    Args:
        batch: the :class:`~cellpy.batch.Batch` to collect from.
        collector: a collect callable, e.g. :func:`collect_summaries`.
        options: the options dataclass for ``collector`` (optional).
        name: display/base name (defaults to the batch/journal name).
        autorun: run the collector immediately (default ``True``).
        **overrides: option overrides forwarded to ``collector``.
    """

    def __init__(
        self,
        batch: Any,
        collector: Collector,
        options: Any | None = None,
        *,
        name: str | None = None,
        autorun: bool = True,
        **overrides,
    ):
        self.batch = batch
        self.collector = collector
        self.options = options
        self.overrides = overrides
        self.name = name or getattr(batch.journal, "name", None) or "batch"
        self._collection: Any | None = None
        if autorun:
            self.update()

    def update(self, **overrides) -> "BatchCollector":
        """(Re)run the collector; extra kwargs merge into the option overrides."""
        if overrides:
            self.overrides = {**self.overrides, **overrides}
        self._collection = self.collector(self.batch, self.options, **self.overrides)
        return self

    @property
    def collection(self) -> Any:
        if self._collection is None:
            self.update()
        return self._collection

    @property
    def data(self) -> pl.DataFrame:
        return self.collection.data

    def save(self, directory: str | Path, **kwargs) -> list[Path]:
        """Persist the collection (explicit directory, no cwd fallback)."""
        return self.collection.save(directory, **kwargs)

    def plot(self, **kwargs) -> Any:
        """Draw the collection via ``cellpy.plotting``."""
        plot = getattr(self.collection, "plot", None)
        if plot is None:
            raise NotImplementedError(
                "Collection plotting is handed over to cellpy.plotting. "
                "Use `.data` for the collected frame in the meantime."
            )
        return plot(**kwargs)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        kind = getattr(self._collection, "kind", "?")
        rows = getattr(getattr(self._collection, "data", None), "height", "?")
        return f"<BatchCollector {self.name!r} kind={kind} rows={rows}>"


def summary_collector(
    batch: Any, options: SummaryOptions | None = None, *, autorun: bool = True, **overrides
) -> BatchCollector:
    """Convenience :class:`BatchCollector` bound to :func:`collect_summaries`."""
    return BatchCollector(
        batch, collect_summaries, options, autorun=autorun, **overrides
    )


def cycles_collector(
    batch: Any, options: CurveOptions | None = None, *, autorun: bool = True, **overrides
) -> BatchCollector:
    """Convenience :class:`BatchCollector` bound to :func:`collect_cycles`."""
    return BatchCollector(batch, collect_cycles, options, autorun=autorun, **overrides)


def ica_collector(
    batch: Any, options: IcaOptions | None = None, *, autorun: bool = True, **overrides
) -> BatchCollector:
    """Convenience :class:`BatchCollector` bound to :func:`collect_ica`."""
    return BatchCollector(batch, collect_ica, options, autorun=autorun, **overrides)


def dva_collector(
    batch: Any, options: IcaOptions | None = None, *, autorun: bool = True, **overrides
) -> BatchCollector:
    """Convenience :class:`BatchCollector` bound to :func:`collect_dva`."""
    return BatchCollector(batch, collect_dva, options, autorun=autorun, **overrides)


def normalize_column(
    column: str, norm_factor: float, out: str | None = None
) -> Callable[[pl.DataFrame], pl.DataFrame]:
    """Build a transform that adds ``100 * column / norm_factor`` as a new series.

    Works on both the wide (non-grouped) frame -- adding an ``<out>`` column --
    and the grouped long frame -- adding an ``<out>`` *variable* with ``mean``
    (and ``std``) scaled. Missing columns are left untouched.
    """
    target = out or f"{column}_norm"

    def _transform(frame: pl.DataFrame) -> pl.DataFrame:
        if "variable" in frame.columns and "mean" in frame.columns:
            sub = frame.filter(pl.col("variable") == column)
            if sub.height == 0:
                return frame
            exprs = [
                pl.lit(target).alias("variable"),
                (100 * pl.col("mean") / norm_factor).alias("mean"),
            ]
            if "std" in sub.columns:
                exprs.append((100 * pl.col("std") / norm_factor).alias("std"))
            return pl.concat([frame, sub.with_columns(exprs)], how="diagonal_relaxed")
        if column in frame.columns:
            return frame.with_columns(
                (100 * pl.col(column) / norm_factor).alias(target)
            )
        return frame

    return _transform


def standard_gravimetric(
    batch: Any,
    norm_factor: float = 120.0,
    *,
    group_it: bool = True,
    columns: tuple[str, ...] = (
        "charge_capacity",
        "discharge_capacity",
        "coulombic_efficiency",
    ),
    retention_on: str = "discharge_capacity",
    autorun: bool = True,
    **overrides,
) -> BatchCollector:
    """The standard gravimetric summary recipe.

    Successor of ``collectors.standard_gravimetric_collector``: collect the
    charge/discharge/CE metrics, partition capacity by CV step, average per
    group, and add a normalized discharge-capacity-retention series
    (``100 * discharge / norm_factor``). Uses native cellpycore column names
    (the legacy ``*_gravimetric`` suffix is not part of the native schema).
    The figure itself lands with the plotting handover.
    """
    options = SummaryOptions(
        columns=columns,
        partition_by_cv=True,
        group_it=group_it,
        transforms=(normalize_column(retention_on, norm_factor),),
    )
    return BatchCollector(
        batch, collect_summaries, options, autorun=autorun, **overrides
    )
