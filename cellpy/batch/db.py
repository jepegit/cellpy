"""Journal-from-database (batch v3, #703).

Wraps the existing db readers (the simple Excel reader and the JSON readers)
to produce a new :class:`~cellpy.batch.journal.Journal`. The legacy
``LabJournal`` still owns the actual db parsing (deleted at E4); this is the
thin bridge that turns its pandas pages into the new polars model.
"""

from __future__ import annotations

from typing import Any

from cellpy.batch.journal import FILENAME, Journal, _empty_session, _to_polars


def journal_from_db(
    name: str,
    project: str,
    *,
    db_reader: str = "default",
    db_file: str | None = None,
    batch_col: str | None = None,
    raw_file_dir: Any = None,
    cellpy_file_dir: Any = None,
    **kwargs: Any,
) -> Journal:
    """Read a batch from a database into a :class:`Journal`.

    ``db_reader`` selects the reader (``"default"``/``"simple_excel_reader"``,
    ``"batbase_json_reader"``, ``"custom_json_reader"``); ``db_file`` and
    ``column_map`` are forwarded for the JSON readers.
    """
    from cellpy.utils.batch_tools.batch_journals import LabJournal

    lab_kwargs: dict[str, Any] = {"db_reader": db_reader, "batch_col": batch_col}
    if db_file is not None:
        lab_kwargs["db_file"] = db_file
    if "column_map" in kwargs:
        lab_kwargs["column_map"] = kwargs.pop("column_map")

    lab = LabJournal(**lab_kwargs)

    from_db_kwargs: dict[str, Any] = dict(kwargs)
    if raw_file_dir is not None:
        from_db_kwargs["raw_file_dir"] = raw_file_dir
    if cellpy_file_dir is not None:
        from_db_kwargs["cellpy_file_dir"] = cellpy_file_dir
    lab.from_db(name=name, project=project, **from_db_kwargs)

    pdf = lab.pages
    if FILENAME not in pdf.columns:
        pdf = pdf.rename_axis(FILENAME).reset_index()
    else:
        pdf = pdf.reset_index(drop=True)

    session = lab.session or _empty_session()
    return Journal(
        name=name,
        project=project,
        pages=_to_polars(pdf),
        session=session,
        meta={"name": name, "project": project},
    )
