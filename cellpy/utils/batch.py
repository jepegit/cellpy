"""Deprecated shim: ``cellpy.utils.batch`` -> :mod:`cellpy.batch`.

The batch subsystem was redesigned and now lives in :mod:`cellpy.batch`
(journal / policy / runner / store / aggregate / qc / outputs / facade). This
module keeps the historical import path and entry points working -- returning
the new :class:`cellpy.batch.Batch` -- and will remain permanently as a thin
re-export. The legacy ``batch_tools`` internals were removed in 2.1;
the DB-journal path they used to own is now native in :mod:`cellpy.batch`.
"""

from __future__ import annotations

import logging
from typing import Any

from cellpy import log
from cellpy._deprecation import warn_once
from cellpy.batch import (
    Batch,
    CellSpec,
    LoadPolicy,
    SourcePreference,
    combine_summaries,
    journal_from_frame,
    read_journal,
)
from cellpy.batch import from_journal as _new_from_journal
from cellpy.batch import load as _new_load
from cellpy.batch.journal import Journal

__all__ = [
    "Batch",
    "LoadPolicy",
    "CellSpec",
    "SourcePreference",
    "combine_summaries",
    "load",
    "init",
    "naked",
    "from_journal",
    "init2",
    "from_journal2",
    "load_journal",
    "load_pages",
    "process_batch",
    "iterate_batches",
]

_JSON_DB_READERS = ("custom_json_reader", "batbase_json_reader")


def _setup_logging(default_log_level=None, testing=False) -> None:
    try:
        log.setup_logging(
            default_level=default_log_level, testing=testing, reset_big_log=True
        )
    except TypeError:  # older/newer signature
        try:
            log.setup_logging(default_level=default_log_level, testing=testing)
        except Exception:  # noqa: BLE001 - logging setup must never block loading
            logging.getLogger(__name__).debug("could not set up logging")


def init(name=None, project=None, *, empty=False, **kwargs) -> Batch:
    """Initialise a batch (shim -> :func:`cellpy.batch.load`).

    Legacy flow ``init() -> create_journal() -> update()`` is preserved: with a
    database source, ``init`` defers the read to ``create_journal``.
    """
    _setup_logging(kwargs.pop("default_log_level", None), kwargs.pop("testing", False))
    file_name = kwargs.pop("file_name", None)
    frame = kwargs.pop("frame", None)
    batch_col = kwargs.pop("batch_col", None)
    db_reader = kwargs.pop("db_reader", "default")

    if empty or db_reader is None:
        return Batch(Journal(name=name, project=project))
    if file_name is not None:
        return _new_from_journal(file_name)
    if frame is not None:
        return Batch(journal_from_frame(frame, name=name, project=project))

    reader = "simple_excel_reader" if db_reader == "default" else db_reader
    return Batch(
        Journal(name=name, project=project),
        _db={"db_reader": reader, "batch_col": batch_col},
    )


def naked(name=None, project=None) -> Batch:
    """Return an empty batch (shim)."""
    return Batch(Journal(name=name, project=project))


def from_journal(journal_file, autolink=True, testing=False, **kwargs) -> Batch:
    """Create a batch from a journal file (shim -> :func:`cellpy.batch.from_journal`)."""
    _setup_logging(testing=testing)
    b = _new_from_journal(journal_file)
    if autolink:
        b.link()
    return b


def load(
    name=None,
    project=None,
    *,
    journal_file=None,
    reader=None,
    column_map=None,
    batch_col=None,
    frame=None,
    testing=False,
    raw_file_dir=None,
    cellpy_file_dir=None,
    policy=None,
    **kwargs,
) -> Batch:
    """Load a batch from a journal source (shim -> :mod:`cellpy.batch`)."""
    _setup_logging(kwargs.pop("default_log_level", None), testing)

    if journal_file is not None and reader in _JSON_DB_READERS:
        return Batch.from_db(
            name,
            project,
            db_reader=reader,
            db_file=str(journal_file),
            column_map=column_map,
            batch_col=batch_col,
            raw_file_dir=raw_file_dir,
            cellpy_file_dir=cellpy_file_dir,
            policy=policy,
        )
    if journal_file is not None:
        return _new_from_journal(journal_file, policy=policy)
    if frame is not None:
        return _new_load(name, project, frame=frame, policy=policy)

    return Batch.from_db(
        name,
        project,
        db_reader=reader or "simple_excel_reader",
        batch_col=batch_col,
        raw_file_dir=raw_file_dir,
        cellpy_file_dir=cellpy_file_dir,
        policy=policy,
    )


# -- deprecated aliases (kept importable, warn once) ---------------------


def init2(*args, **kwargs) -> Batch:
    warn_once("cellpy.utils.batch.init2", "cellpy.batch.load")
    return init(*args, **kwargs)


def from_journal2(journal_file, **kwargs) -> Batch:
    warn_once("cellpy.utils.batch.from_journal2", "cellpy.batch.from_journal")
    return from_journal(journal_file, **kwargs)


def load_journal(journal_file, **kwargs) -> Batch:
    warn_once("cellpy.utils.batch.load_journal", "cellpy.batch.from_journal")
    return _new_from_journal(journal_file)


def load_pages(file_name) -> Any:
    warn_once("cellpy.utils.batch.load_pages", "cellpy.batch.read_journal(...).pages")
    return read_journal(file_name).pages


def process_batch(*args, **kwargs) -> Batch:
    warn_once(
        "cellpy.utils.batch.process_batch",
        "cellpy.batch.load(...).update() (see the migration guide recipe)",
    )
    b = load(*args, **kwargs)
    b.update()
    return b


def iterate_batches(*args, **kwargs) -> None:
    warn_once(
        "cellpy.utils.batch.iterate_batches",
        "a loop over cellpy.batch.load(...) (see the migration guide recipe)",
    )
    raise NotImplementedError(
        "iterate_batches is a docs recipe in batch v3; see the migration guide."
    )
