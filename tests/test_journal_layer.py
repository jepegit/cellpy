"""The journal as a metadata source (#563, metadata plan Step 6).

The journal was write-only for metadata: batch built pages from cells, and
nothing read a row back. A mass corrected in the journal was corrected for the
report but not for the cell, and the two could disagree indefinitely.
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest
from cellpycore.metadata.models import CellMeta

from cellpy import log
from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.readers.journal_layer import (
    journal_row_for,
    to_cell_meta,
    to_test_meta,
)
from cellpy.readers.meta_resolver import Layer, resolve_cell_meta

log.setup_logging(default_level=logging.DEBUG, testing=True)

HEADERS = get_headers_journal()


def _row(**overrides):
    row = {
        HEADERS.mass: 12.5,
        HEADERS.nom_cap: 3.4,
        HEADERS.loading: 1.1,
        HEADERS.cell_type: "full_cell",
        HEADERS.filename: "some_cell",
        HEADERS.group: 1,
    }
    row.update(overrides)
    return row


@pytest.mark.essential
def test_journal_row_yields_cell_meta_fields():
    extracted = to_cell_meta(_row())
    assert extracted["mass"] == 12.5
    assert extracted["nom_cap"] == 3.4
    assert extracted["active_electrode_loading"] == 1.1
    assert extracted["cell_type"] == "full_cell"


@pytest.mark.essential
def test_batch_bookkeeping_columns_are_not_metadata():
    """`group`, `filename`, `selected` describe the batch, not the cell."""
    extracted = to_cell_meta(_row())
    assert "group" not in extracted
    assert "filename" not in extracted
    assert "selected" not in extracted


@pytest.mark.essential
@pytest.mark.parametrize("blank", [None, float("nan"), "", "   "])
def test_blank_journal_cells_are_omitted_not_passed_as_none(blank):
    """Journal blanks arrive as NaN or "" depending on the round-trip path.

    Neither means "set this to empty" — omitting them keeps a blank column from
    ever reaching the resolver as a value.
    """
    extracted = to_cell_meta(_row(**{HEADERS.mass: blank}))
    assert "mass" not in extracted


@pytest.mark.essential
def test_a_blank_journal_mass_does_not_override_the_file():
    """The failure this guards: a half-filled journal wiping real metadata."""
    journal = to_cell_meta(_row(**{HEADERS.mass: float("nan")}))
    meta, resolution = resolve_cell_meta(
        CellMeta(), journal=journal, draft=CellMeta(mass=7.0)
    )
    assert meta.mass == 7.0
    assert resolution.source_of("mass") is Layer.RAW_FILE


@pytest.mark.essential
def test_journal_sits_between_kwargs_and_the_file():
    journal = to_cell_meta(_row())
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        kwargs={"mass": 1.0},
        journal=journal,
        draft=CellMeta(mass=7.0, nom_cap=99.0),
    )
    # the user still wins
    assert meta.mass == 1.0
    assert resolution.source_of("mass") is Layer.KWARGS
    # ... but the journal beats the file
    assert meta.nom_cap == 3.4
    assert resolution.source_of("nom_cap") is Layer.JOURNAL


@pytest.mark.essential
def test_test_meta_fields_come_across_too():
    extracted = to_test_meta(
        {HEADERS.label: "cell A", HEADERS.instrument: "arbin_res"}
    )
    assert extracted["cell_name"] == "cell A"
    assert extracted["source_type"] == "arbin_res"


# -- pulling a row out of a pages frame ----------------------------------------


@pytest.mark.essential
def test_journal_row_for_reads_an_indexed_pages_frame():
    pages = pd.DataFrame(
        [{HEADERS.mass: 5.0}, {HEADERS.mass: 6.0}], index=["cell_a", "cell_b"]
    )
    row = journal_row_for(pages, "cell_b")
    assert row[HEADERS.mass] == 6.0


@pytest.mark.essential
def test_journal_row_for_reads_a_keys_in_columns_frame():
    """The polars plan moves keys out of the index; support both shapes."""
    pages = pd.DataFrame(
        [
            {HEADERS.id_key: "cell_a", HEADERS.mass: 5.0},
            {HEADERS.id_key: "cell_b", HEADERS.mass: 6.0},
        ]
    )
    row = journal_row_for(pages, "cell_b")
    assert row[HEADERS.mass] == 6.0


@pytest.mark.essential
def test_a_cell_absent_from_the_journal_is_not_an_error():
    """Loading a file no batch has catalogued is ordinary."""
    pages = pd.DataFrame([{HEADERS.mass: 5.0}], index=["cell_a"])
    assert journal_row_for(pages, "not_in_the_journal") is None
    assert journal_row_for(None, "anything") is None


@pytest.mark.essential
def test_an_absent_journal_resolves_to_the_file_values():
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        journal=to_cell_meta(journal_row_for(None, "x") or {}),
        draft=CellMeta(mass=7.0),
    )
    assert meta.mass == 7.0
    assert resolution.source_of("mass") is Layer.RAW_FILE
