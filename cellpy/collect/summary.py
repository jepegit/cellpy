"""Summary collection (collectors redesign, #705).

Built on ``batch.aggregate.combine_summaries`` (the tidy long-format frame).
The full rate-filtering / grouping / CV-partition feature set of the legacy
``helpers.concat_summaries`` ports onto the options model here in B2 (#706);
this arc lands the core collect-on-aggregate path + column selection.
"""

from __future__ import annotations

from typing import Any

from cellpy.batch import aggregate
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import SummaryOptions

_KEYS = ("cell", "group", "sub_group")


def collect_summaries(
    batch: Any, options: SummaryOptions | None = None, **overrides
) -> Collection:
    """Collect per-cell summaries into one tidy :class:`Collection`."""
    opts = options or SummaryOptions()
    if overrides:
        opts = opts.replace(**overrides)

    frame = aggregate.combine_summaries(batch.cells, batch.journal)

    if opts.columns and frame.height:
        keep = [c for c in (*_KEYS, "cycle_num") if c in frame.columns]
        keep += [c for c in opts.columns if c in frame.columns and c not in keep]
        frame = frame.select(keep)

    for transform in opts.transforms:
        frame = transform(frame)

    meta = CollectionMeta(
        kind="summary",
        batch_name=batch.journal.name,
        options={
            "columns": list(opts.columns) if opts.columns else None,
            "group_it": opts.group_it,
        },
        cells_included=list(batch.cells),
    )
    return Collection(
        data=frame,
        kind="summary",
        name=f"{batch.journal.name or 'batch'}_summary",
        meta=meta,
    )
