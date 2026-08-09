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

# Re-exported for discoverability: build a Batch from in-memory cells, then feed
# it to collect_summaries / collect_cycles (#787). The canonical home is
# ``cellpy.batch.from_cells`` / ``Batch.from_cells``.
from cellpy.batch.facade import from_cells
from cellpy.collect.cells import CellItem, iter_cells
from cellpy.collect.collection import Collection, CollectionMeta, load_collection
from cellpy.collect.collector import (
    BatchCollector,
    cycles_collector,
    dva_collector,
    ica_collector,
    normalize_column,
    normalize_column_on_max,
    standard_gravimetric,
    summary_collector,
)
from cellpy.collect.curves import collect_cycles
from cellpy.collect.dva import collect_dva
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
    "collect_dva",
    "from_cells",
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
    "dva_collector",
    "standard_gravimetric",
    "normalize_column",
    "normalize_column_on_max",
]
