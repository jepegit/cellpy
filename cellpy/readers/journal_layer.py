"""The batch journal as a metadata source (metadata plan Step 6, #563).

The journal has always been write-only as far as metadata is concerned: batch
builds its pages *from* loaded cells (``batch.py``), and nothing ever read a row
back to say "this is what we know about that cell". So a mass corrected in the
journal was corrected for the report but not for the cell, and the two could
disagree indefinitely.

This module supplies the missing direction — a journal row as a
:class:`~cellpy.readers.meta_resolver.MetaResolver` layer, sitting where the
plan puts it: below explicit user arguments, above whatever the instrument file
happened to contain.

It is a *source*, not a store (plan Step 6). Nothing here writes journal pages.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from cellpy.parameters.internal_settings import get_headers_journal

#: journal column -> CellMeta field. Only columns that genuinely describe the
#: cell are mapped: `filename`, `group`, `sub_group`, `selected` and friends are
#: batch bookkeeping and have no business in metadata.
_JOURNAL_TO_CELL_META = {
    "mass": "mass",
    "nom_cap": "nom_cap",
    "nom_cap_specifics": "nom_cap_specifics",
    "loading": "active_electrode_loading",
    "area": "active_electrode_area",
    "cell_type": "cell_type",
    "comment": "comment",
}

#: journal column -> TestMeta field.
_JOURNAL_TO_TEST_META = {
    "label": "cell_name",
    "instrument": "source_type",
}


def _is_missing(value: Any) -> bool:
    """True for values a journal uses to mean "not filled in"."""
    if value is None:
        return True
    # Journal pages come from Excel/JSON round-trips, so blanks arrive as NaN
    # or as an empty string depending on the path. Neither means "set this to
    # empty" — they mean the column was left alone.
    if isinstance(value, str) and not value.strip():
        return True
    try:
        import math

        return isinstance(value, float) and math.isnan(value)
    except Exception:  # pragma: no cover - defensive
        return False


def to_cell_meta(row: Mapping[str, Any]) -> dict[str, Any]:
    """Extract ``CellMeta`` values from one journal page row.

    Args:
        row: a mapping of journal column → value (e.g. ``pages.loc[cell_id]``
            as a dict, or any row-like mapping).

    Returns:
        A ``{field: value}`` dict suitable as the resolver's ``journal`` layer.
        Columns the journal left blank are omitted rather than passed as None,
        so the resolver's "None means I don't know" rule is never even reached.
    """
    return _extract(row, _JOURNAL_TO_CELL_META)


def to_test_meta(row: Mapping[str, Any]) -> dict[str, Any]:
    """Extract ``TestMeta`` values from one journal page row.

    Named ``to_test_meta`` rather than ``test_meta_from_...``: any name starting
    with ``test_`` is collected as a test case by pytest wherever it is
    imported, which turns a helper into a spurious failing test.
    """
    return _extract(row, _JOURNAL_TO_TEST_META)


def _extract(
    row: Mapping[str, Any], mapping: Mapping[str, str]
) -> dict[str, Any]:
    headers = get_headers_journal()
    extracted: dict[str, Any] = {}

    for journal_attr, meta_field in mapping.items():
        column = getattr(headers, journal_attr, journal_attr)
        if column not in row:
            continue
        value = row[column]
        if _is_missing(value):
            continue
        extracted[meta_field] = value

    logging.debug("journal layer contributed: %s", sorted(extracted))
    return extracted


def journal_row_for(pages: Any, cell_id: Any) -> dict[str, Any] | None:
    """Pull one row out of a journal ``pages`` frame as a plain dict.

    Returns None when the cell is not in the journal — a perfectly ordinary
    situation (loading a file that no batch has catalogued), not an error.
    """
    if pages is None:
        return None
    try:
        if cell_id in pages.index:
            return pages.loc[cell_id].to_dict()
        # keys-in-columns (polars plan): look for an id column instead
        headers = get_headers_journal()
        id_column = getattr(headers, "id_key", "id_key")
        if id_column in getattr(pages, "columns", []):
            matches = pages[pages[id_column] == cell_id]
            if len(matches):
                return matches.iloc[0].to_dict()
    except Exception as exc:  # pragma: no cover - defensive
        logging.debug("could not read journal row for %r: %s", cell_id, exc)
    return None
