"""Journal-from-database.

Reads a batch selection from a cellpy database (the simple Excel reader or the
JSON readers) into a new `Journal`. The database
parsing is done natively by `_dbengine`; the db
readers themselves live in `dbreader` /
`json_dbreader`.
"""

from __future__ import annotations

import logging
from typing import Any

from cellpy.batch import _dbengine
from cellpy.batch.journal import FILENAME, Journal, _empty_session, _to_polars
from cellpy.readers import dbreader


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
    """Read a batch from a database into a `Journal`.

    ``db_reader`` selects the reader (``"default"``/``"simple_excel_reader"``,
    ``"batbase_json_reader"``, ``"custom_json_reader"``); ``db_file`` and
    ``column_map`` are forwarded for the JSON readers.

    Extra kwargs (e.g. ``skip_file_search``, ``file_list``, ``pre_path``,
    ``sub_folders``) are forwarded to
    `simple_db_engine` /
    `find_files`. Pass ``skip_file_search=True``
    when the JSON already carries ``raw_file_names`` / ``cellpy_file_name``.

    ``project`` also scopes the one-shot raw-file-directory dump used when
    ``config.batch.auto_use_file_list`` is True (default False).
    """
    column_map = kwargs.pop("column_map", None)
    dbreader_kwargs = kwargs.pop("dbreader_kwargs", None) or {}

    reader = _dbengine.make_db_reader(
        db_reader=db_reader, db_file=db_file, column_map=column_map
    )

    engine_kwargs: dict[str, Any] = dict(kwargs)
    # The batch project scopes the auto_use_file_list dump (#900).
    engine_kwargs.setdefault("project", project)
    if raw_file_dir is not None:
        engine_kwargs["raw_file_dir"] = raw_file_dir
    if cellpy_file_dir is not None:
        engine_kwargs["cellpy_file_dir"] = cellpy_file_dir

    if reader is None:
        logging.debug("no db reader; creating empty journal pages")
        pdf = _empty_pages()
    else:
        if isinstance(reader, dbreader.Reader):  # simple excel-db
            id_keys = reader.select_batch(name, batch_col or "b01", **dbreader_kwargs)
            if len(id_keys) != len(set(id_keys)):
                duplicates = sorted({x for x in id_keys if id_keys.count(x) > 1})
                logging.warning(f"Found duplicate id_keys: {duplicates}")
            pdf = _dbengine.simple_db_engine(reader, id_keys, **engine_kwargs)
        else:
            pdf = _dbengine.simple_db_engine(
                reader, batch_name=name, **engine_kwargs
            )

        if pdf.empty:
            logging.critical(
                "EMPTY JOURNAL PAGES: are you sure you have provided correct "
                f"input to batch? (name={name!r}, project={project!r})"
            )

    if FILENAME not in pdf.columns:
        pdf = pdf.rename_axis(FILENAME).reset_index()
    else:
        pdf = pdf.reset_index(drop=True)

    return Journal(
        name=name,
        project=project,
        pages=_to_polars(pdf),
        session=_empty_session(),
        meta={"name": name, "project": project},
    )


def _empty_pages():
    import pandas as pd

    return pd.DataFrame()
