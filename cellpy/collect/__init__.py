"""cellpy.collect -- collection as a first-class product.

A collection is a product, not a side effect: :class:`Collection` = a tidy frame
plus provenance. Built on ``cellpy.batch.aggregate`` (Epic A), replacing the
``utils/collectors`` "elevated arguments" machinery and fixing the cross-cell
cycle-narrowing bug by design. ``cellpy.utils.collectors`` is now a thin shim
whose legacy ``Batch*Collector`` family is removed in 2.1.

Arcs: options/collection/collect_summaries + per-cell curves; rate/group
pipeline; convenience class + recipes; ICA collection + plotting
handover (Collection.plot -> cellpy.plotting) + collectors shim.
"""

from __future__ import annotations

from cellpy.collect.cells import CellItem, iter_cells
from cellpy.collect.collection import Collection, CollectionMeta, load_collection
from cellpy.collect.collector import (
    BatchCollector,
    cycles_collector,
    ica_collector,
    normalize_column,
    standard_gravimetric,
    summary_collector,
)
from cellpy.collect.curves import collect_cycles
from cellpy.collect.ica import collect_ica
from cellpy.collect.options import (
    CurveOptions,
    IcaOptions,
    SaveOptions,
    SummaryOptions,
)
from cellpy.collect.summary import collect_summaries

__all__ = [
    "Collection",
    "CollectionMeta",
    "load_collection",
    "collect_summaries",
    "collect_cycles",
    "collect_ica",
    "iter_cells",
    "CellItem",
    "SummaryOptions",
    "CurveOptions",
    "IcaOptions",
    "SaveOptions",
    "BatchCollector",
    "summary_collector",
    "cycles_collector",
    "ica_collector",
    "standard_gravimetric",
    "normalize_column",
]
