"""Batch journal model + JSON IO (batch v3, #698).

A journal is a *document*, not an actor: reading one never touches the
filesystem layout, and the data model is separated from serialisation. This is
the successor of ``utils/batch_tools/batch_journals.LabJournal`` (a ~1100-line
class mixing data model, three file formats, path fixing, selection state and
folder generation). Folder layout lives in :mod:`cellpy.batch.layout`.

The on-disk JSON format is preserved for compatibility: a top-level object with
``info_df`` (pages, pandas ``to_json`` "columns" orient), ``metadata`` and
``session``. Pages follow the keys-in-columns law (polars report section 1.3):
the cell label lives in the ``filename`` *column*, never in an index.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import polars as pl

from cellpy.parameters.internal_settings import (
    get_headers_journal,
    keys_journal_session,
)

_hdr = get_headers_journal()
#: Name of the column holding the (unique) cell label.
FILENAME = _hdr["filename"]

#: Bump when the on-disk journal shape changes in a non-backward way.
JOURNAL_FORMAT_VERSION = 1


def _empty_session() -> dict:
    return {key: None for key in keys_journal_session}


@dataclass
class Journal:
    """A batch journal: the cells of an experiment plus session/meta state.

    Attributes:
        name: batch name.
        project: project name.
        pages: one row per cell; ``filename`` is a column (keys-in-columns).
        session: mutable session state (starred/bad_cells/bad_cycles/notes).
        meta: free-form metadata carried through save/load (name, project,
            time_stamp, project_dir, ...).
    """

    name: str | None = None
    project: str | None = None
    pages: pl.DataFrame = field(default_factory=pl.DataFrame)
    session: dict = field(default_factory=_empty_session)
    meta: dict = field(default_factory=dict)

    @property
    def cell_names(self) -> list[str]:
        """The cell labels, in page order."""
        if FILENAME in self.pages.columns:
            return self.pages[FILENAME].to_list()
        return []

    def __len__(self) -> int:
        return self.pages.height


def _to_polars(pdf: pd.DataFrame) -> pl.DataFrame:
    """Convert a pandas pages frame to polars, column by column.

    Columns that hold any python ``list`` (e.g. ``raw_file_names``, where a
    cell may have several raw files) are normalised to a ``List[str]`` column:
    scalar values are wrapped in a single-element list and nulls become empty
    lists. This removes the legacy str-or-list ambiguity that made pages
    impossible to represent as a typed frame.
    """
    data: dict[str, pl.Series] = {}
    for col in pdf.columns:
        values = pdf[col].tolist()
        if any(isinstance(v, list) for v in values):
            normalised = [
                v
                if isinstance(v, list)
                else ([] if v is None or (isinstance(v, float) and pd.isna(v)) else [v])
                for v in values
            ]
            data[col] = pl.Series(col, normalised, dtype=pl.List(pl.Utf8))
        else:
            data[col] = pl.Series(col, values)
    return pl.DataFrame(data)


def _pages_from_info_df(info_df: dict) -> pl.DataFrame:
    """Parse the legacy ``info_df`` mapping into a polars frame.

    ``info_df`` is ``{column: {cell_label: value}}`` (pandas "columns" orient).
    We parse via pandas (the format is pandas-shaped), guarantee the cell label
    is a real ``filename`` column, and hand back polars.
    """
    pdf = pd.DataFrame(info_df)
    pdf = pdf.dropna(how="all")
    if FILENAME not in pdf.columns:
        # the cell label only lived in the index -> promote it to a column
        pdf = pdf.rename_axis(FILENAME).reset_index()
    else:
        pdf = pdf.reset_index(drop=True)
    return _to_polars(pdf)


def _pages_to_info_df(pages: pl.DataFrame) -> dict:
    """Serialise pages back to the legacy ``info_df`` mapping."""
    pdf = pages.to_pandas()
    if FILENAME in pdf.columns:
        pdf = pdf.set_index(FILENAME, drop=False)
    return json.loads(pdf.to_json(default_handler=str))


def read_journal(path: Path | str) -> Journal:
    """Load a journal into the :class:`Journal` model.

    ``.json`` is the native, round-trippable format. ``.xlsx`` is supported
    **read-only** (a lab convenience); writing Excel is intentionally not
    supported in batch v3 (see :func:`write_journal`).
    """
    path = Path(path)
    if path.suffix == ".xlsx":
        return _read_journal_excel(path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    if "info_df" not in raw:
        raise ValueError(f"not a cellpy journal (missing 'info_df'): {path}")

    meta = raw.get("metadata") or {}
    session = raw.get("session") or _empty_session()
    for key in keys_journal_session:
        session.setdefault(key, None)

    pages = _pages_from_info_df(raw["info_df"])
    return Journal(
        name=meta.get("name"),
        project=meta.get("project"),
        pages=pages,
        session=session,
        meta=meta,
    )


def _read_journal_excel(path: Path) -> Journal:
    """Read the ``pages`` sheet of an Excel journal (read-only)."""
    pdf = pd.read_excel(path, sheet_name="pages", engine="openpyxl")
    if FILENAME not in pdf.columns:
        # legacy Excel writes the cell label as the (index) first column
        first = pdf.columns[0]
        if str(first).lower().startswith("unnamed") or first == "index":
            pdf = pdf.rename(columns={first: FILENAME})
    pdf = pdf.dropna(how="all").reset_index(drop=True)

    meta: dict = {}
    try:
        mdf = pd.read_excel(path, sheet_name="meta", engine="openpyxl")
        if {"parameter", "value"}.issubset(mdf.columns):
            meta = dict(zip(mdf["parameter"], mdf["value"]))
    except (ValueError, KeyError):
        pass

    return Journal(
        name=meta.get("name", path.stem),
        project=meta.get("project"),
        pages=_to_polars(pdf),
        meta=meta,
    )


def read_custom_json(path: Path | str, column_map: Mapping[str, str]) -> pl.DataFrame:
    """Read an arbitrary JSON file into journal pages via a column map (#345).

    ``column_map`` maps *source* JSON keys to cellpy journal keys, e.g.
    ``{"cell_id": "filename", "mass_mg": "mass", "instrument_name": "instrument"}``.
    The JSON may be a dict of columns (``{key: [values]}``) or a list of
    records. At least one source key must map to ``filename``.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    pdf = pd.DataFrame(data)

    rename = {
        src: _hdr[cellpy_key]
        for src, cellpy_key in column_map.items()
        if src in pdf.columns
    }
    pdf = pdf.rename(columns=rename)
    keep = [c for c in pdf.columns if c in set(rename.values())]
    pdf = pdf[keep]

    if FILENAME not in pdf.columns:
        raise ValueError(
            "column_map must map a source column to 'filename' "
            f"(got mappings to {sorted(set(rename.values()))})"
        )
    return _to_polars(pdf.reset_index(drop=True))


def journal_from_custom_json(
    path: Path | str,
    column_map: Mapping[str, str],
    name: str | None = None,
    project: str | None = None,
) -> Journal:
    """Build a :class:`Journal` from an arbitrary JSON file (#345)."""
    return Journal(
        name=name, project=project, pages=read_custom_json(path, column_map)
    )


def write_journal(journal: Journal, path: Path | str) -> Path:
    """Write a :class:`Journal` to ``path`` in the compatible JSON format.

    Only ``.json`` is written. Excel journals are read-only in batch v3
    (metadata plan Step 4); export a report frame instead of a journal.
    """
    path = Path(path)
    if path.suffix == ".xlsx":
        raise ValueError(
            "Excel journals are read-only in batch v3; write a .json journal "
            "instead (use outputs.write_excel for report frames)."
        )
    meta = dict(journal.meta)
    meta.setdefault("name", journal.name)
    meta.setdefault("project", journal.project)
    top_level = {
        "info_df": _pages_to_info_df(journal.pages),
        "metadata": meta,
        "session": journal.session,
    }
    path.write_text(json.dumps(top_level, default=str), encoding="utf-8")
    return path


def journal_from_frame(
    frame: pl.DataFrame | pd.DataFrame,
    name: str | None = None,
    project: str | None = None,
) -> Journal:
    """Build a journal from a dataframe of pages (polars or pandas).

    The cell label must be available as a ``filename`` column (or the pandas
    index, which is promoted to one).
    """
    if isinstance(frame, pl.DataFrame):
        pages = frame
    else:
        pdf = frame
        if FILENAME not in pdf.columns:
            pdf = pdf.rename_axis(FILENAME).reset_index()
        else:
            pdf = pdf.reset_index(drop=True)
        pages = _to_polars(pdf)
    return Journal(name=name, project=project, pages=pages)
