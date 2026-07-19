"""Legend and marker post-processing for plotly traces — one implementation (#567).

These two helpers existed in **three** places, under two naming conventions:

| | plotutils | collectors | batch_plotters |
|---|---|---|---|
| legend | `_plotly_legend_replacer` | `legend_replacer` | `_plotly_legend_replacer` |
| markers | `_plotly_remove_markers` | `remove_markers` | `_plotly_remove_markers` |

The marker helpers were functionally identical in all three (only the docstring
differed). The legend helpers were identical in plotutils and collectors, while
the batch_plotters copy carried an extra ``inverted_mode`` that swaps group and
sub-group. That copy is therefore the superset, and it is the one kept — with
``inverted_mode=False`` as the default, which reproduces the other two exactly.
"""

from __future__ import annotations

import logging

from cellpy.parameters.internal_settings import get_headers_journal

hdr_journal = get_headers_journal()


def remove_markers(trace):
    """Turn a plotly trace into a plain line."""
    trace.update(marker=None, mode="lines")
    return trace


def legend_replacer(trace, df, group_legends=True, inverted_mode=False):
    """Replace a ``"group,subgroup"`` legend label with the cell name.

    Plotly names a trace after the columns it was grouped by, so a batch figure
    ends up with legends like ``"2,1"``. This looks the pair up in the journal
    and substitutes the cell name, in the legend and in the hover text.

    Args:
        trace: the plotly trace to update, in place.
        df: journal frame carrying group / sub-group / cell columns.
        group_legends: put every sub-group of a group in one legend entry.
        inverted_mode: the label reads ``"subgroup,group"`` rather than
            ``"group,subgroup"``.

    Returns:
        The trace, updated.
    """
    name = trace.name
    parts = name.split(",")
    if len(parts) != 2:
        # Not a grouped trace; leave it alone rather than guessing.
        logging.debug(
            "cannot replace the legend label %r: only 'group,subgroup' labels "
            "are understood",
            name,
        )
        return trace

    group = int(parts[0])
    subgroup = int(parts[1])
    if inverted_mode:
        group, subgroup = subgroup, group

    cell_label = df.loc[
        (df[hdr_journal.group] == group) & (df[hdr_journal.sub_group] == subgroup),
        "cell",
    ].values[0]

    trace.update(
        name=cell_label,
        legendgroup=group if group_legends else cell_label,
        hovertemplate=f"{cell_label}<br>{trace.hovertemplate}",
    )
    return trace
