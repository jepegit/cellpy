"""cellpy.collect -- collection as a first-class product (collectors redesign, #705).

A collection is a product, not a side effect: :class:`Collection` = a tidy frame
plus provenance. Built on ``cellpy.batch.aggregate`` (Epic A), replacing the
``utils/collectors`` "elevated arguments" machinery and fixing the cross-cell
cycle-narrowing bug by design. ``cellpy.utils.collectors`` becomes a shim (B3).

Arcs: options/collection/collect_summaries + per-cell curves (#705, this arc);
rate/group pipeline (#706); convenience class + shims (#707); plotting (#708).
"""

from __future__ import annotations

from cellpy.collect.cells import CellItem, iter_cells
from cellpy.collect.collection import Collection, CollectionMeta, load_collection
from cellpy.collect.curves import collect_cycles
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
    "iter_cells",
    "CellItem",
    "SummaryOptions",
    "CurveOptions",
    "IcaOptions",
    "SaveOptions",
]
