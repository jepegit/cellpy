"""Legend, marker, and axis-label helpers for plotting (#567 / #647).

Legend/marker helpers existed in **three** places, under two naming conventions:

| | plotutils | collectors | batch_plotters |
|---|---|---|---|
| legend | `_plotly_legend_replacer` | `legend_replacer` | `_plotly_legend_replacer` |
| markers | `_plotly_remove_markers` | `remove_markers` | `_plotly_remove_markers` |

The marker helpers were functionally identical in all three (only the docstring
differed). The legend helpers were identical in plotutils and collectors, while
the batch_plotters copy carried an extra ``inverted_mode`` that swaps group and
sub-group. That copy is therefore the superset, and it is the one kept — with
``inverted_mode=False`` as the default, which reproduces the other two exactly.

Axis labels for ``raw_plot`` / ``cycle_info_plot`` go through
:func:`quantity_label` / :func:`units_quantity_label` so those paths do not
hand-compose ``f"{name} ({unit})"`` strings (#647).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from cellpy.parameters.internal_settings import get_headers_journal

if TYPE_CHECKING:
    from cellpycore.units.spec import CellpyUnits

hdr_journal = get_headers_journal()


def quantity_label(name: str, unit: str) -> str:
    """Compose an axis label ``name (unit)``.

    Args:
        name: human-readable quantity name, e.g. ``"Voltage"``.
        unit: unit string already resolved for the plotted series.

    Returns:
        e.g. ``"Voltage (V)"``, ``"Time (hours)"``.
    """
    return f"{name} ({unit})"


def units_quantity_label(
    name: str,
    physical_property: str,
    mode: Optional[str] = None,
    *,
    units: Optional["CellpyUnits"] = None,
) -> str:
    """Axis label via :func:`cellpy.units.units_label`.

    Args:
        name: human-readable quantity name.
        physical_property: as :func:`~cellpy.units.units_label`.
        mode: as :func:`~cellpy.units.units_label`.
        units: unit spec for the series (e.g. ``cell.data.raw_units``).

    Returns:
        e.g. ``"Voltage (V)"``, ``"Charge capacity (Ah)"``.
    """
    from cellpy.units import with_cellpy_unit

    return with_cellpy_unit(name, physical_property, mode, units=units)


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
