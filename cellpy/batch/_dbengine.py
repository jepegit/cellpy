"""Native DB-journal engine for batch v3 (E4, #716).

Reads a batch selection from a cellpy database (the simple Excel reader or the
JSON readers) into a pandas ``pages`` frame, then hands it to
:mod:`cellpy.batch.db` which converts it to the polars :class:`Journal`.

This is the native replacement for the ``LabJournal.from_db`` path that used
to live in ``cellpy/utils/batch_tools`` (``batch_journals`` + ``engines`` +
``batch_helpers``), removed in 2.1. The database readers themselves
(:mod:`cellpy.readers.dbreader`, :mod:`cellpy.readers.json_dbreader`) are
unchanged and still own the actual db access; only the journal-building glue
moved here.
"""

from __future__ import annotations

import logging
import time
import warnings
from typing import Any, List, Optional

import pandas as pd

import cellpy.config as config
from cellpy import filefinder, prms
from cellpy.exceptions import UnderDefined
from cellpy.parameters.internal_settings import (
    get_headers_journal,
    get_headers_summary,
)
from cellpy.readers import data_structures as core
from cellpy.readers import dbreader, json_dbreader
from cellpy.readers.data_structures import PagesDictBase

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()

PagesDict = PagesDictBase

CELL_TYPE_IDS = ["cc", "ec", "eth"]


# --- reader construction ---------------------------------------------------


def make_db_reader(
    db_reader: Any = "default",
    db_file: str | None = None,
    column_map: Any = None,
):
    """Build a db-reader object from a ``db_reader`` selector.

    Mirrors the reader construction that used to live in
    ``LabJournal.__init__``. Returns ``None`` for ``"off"``/``None`` (no db).
    A reader object passed in directly is returned unchanged.
    """
    if db_reader is None:
        return None

    if not isinstance(db_reader, str):
        # already a reader object
        return db_reader

    if db_reader == "off":
        return None
    if db_reader == "default":
        db_reader = config.db.db_type

    if db_reader in ("simple_excel_reader", "default"):
        return dbreader.Reader()

    if db_reader == "batbase_json_reader":
        if db_file is None:
            raise UnderDefined("db_file is not provided")
        import os

        if not os.path.exists(db_file):
            raise FileNotFoundError(f"The file {db_file} does not exist")
        return json_dbreader.BatBaseJSONReader(json_file=db_file)

    if db_reader == "custom_json_reader":
        if db_file is None:
            raise UnderDefined("db_file is not provided")
        import os

        if not os.path.exists(db_file):
            raise FileNotFoundError(f"The file {db_file} does not exist")
        return json_dbreader.CustomJSONReader(json_file=db_file, column_map=column_map)

    if db_reader == "sql_db_reader":
        raise NotImplementedError("sql_db_reader is not implemented yet")

    raise UnderDefined(f"The db-reader '{db_reader}' is not supported")


# --- helpers (ported from batch_helpers) -----------------------------------


def create_factory():
    """Build an instrument factory (used to resolve raw-file extensions)."""
    instrument_factory = core.InstrumentFactory()
    instruments = core.find_all_instruments()
    for instrument_id, instrument in instruments.items():
        instrument_factory.register_builder(instrument_id, instrument)
    return instrument_factory


def find_files(
    info_dict,
    file_list=None,
    pre_path=None,
    sub_folders=None,
    skip_file_search=False,
    **kwargs,
):
    """Find raw/cellpy files for each cell using :mod:`cellpy.filefinder`.

    Populates ``raw_file_names`` and ``cellpy_file_name`` in ``info_dict``.
    When ``skip_file_search`` is True the dict is returned unchanged (e.g.
    when a custom JSON db already carries the paths).
    """
    if skip_file_search:
        return info_dict

    sub_folders = sub_folders or config.file_names.sub_folders
    instrument_factory = create_factory()
    file_name_indicators = info_dict.get(
        hdr_journal["file_name_indicator"], hdr_journal["filename"]
    )

    if hdr_journal["raw_file_names"] not in info_dict:
        info_dict[hdr_journal["raw_file_names"]] = []
    if hdr_journal["cellpy_file_name"] not in info_dict:
        info_dict[hdr_journal["cellpy_file_name"]] = []

    for i, run_name in enumerate(file_name_indicators):
        try:
            instrument = info_dict[hdr_journal["instrument"]][i]
            raw_ext = instrument_factory.query(instrument, "raw_ext")
            if raw_ext:
                config.file_names.raw_extension = raw_ext
        except IndexError:
            warnings.warn(f"no instrument given for {run_name}")

        logging.debug(f"checking for {run_name}")
        raw_files, cellpyfile = filefinder.search_for_files(
            run_name,
            file_list=file_list,
            with_prefix=True,
            pre_path=pre_path,
            sub_folders=sub_folders,
            **kwargs,
        )
        if not raw_files:
            raw_files = None
        info_dict[hdr_journal["raw_file_names"]].append(raw_files)
        info_dict[hdr_journal["cellpy_file_name"]].append(cellpyfile)

    return info_dict


def fix_groups(groups):
    """Renumber arbitrary group labels to consecutive ints starting at 1."""
    _groups = []
    unique_groups = list(set(groups))
    lookup = {}
    for i, g in enumerate(unique_groups):
        lookup[g] = i + 1
    for g in groups:
        _groups.append(lookup[g])
    return _groups


def make_unique_groups(info_df):
    """Clean up group numbering and assign per-group sub-group numbers."""
    unique_g = info_df[hdr_journal.group].unique()
    unique_g = sorted(unique_g)
    new_unique_g = list(range(len(unique_g)))
    info_df[hdr_journal.sub_group] = info_df[hdr_journal.group] * 0
    for i, j in zip(unique_g, new_unique_g):
        counter = 1
        for indx, _row in info_df.loc[info_df[hdr_journal.group] == i].iterrows():
            info_df.at[indx, hdr_journal.sub_group] = counter
            counter += 1
        info_df.loc[info_df[hdr_journal.group] == i, hdr_journal.group] = j + 1
    return info_df


def _remove_date_and_celltype(label):
    parts = label.split("_")
    parts.pop(0)
    try:
        if parts[-1] in CELL_TYPE_IDS:
            parts.pop(-1)
    except IndexError:
        logging.debug("could not remove date and cell type; using label as is")
        return label
    return "_".join(parts)


def create_labels(label, *args):
    """Re-format a run-name into a display label (drops the leading date)."""
    return _remove_date_and_celltype(label)


# --- pages-dict builders (ported from engines) -----------------------------


def _query(reader_method, cell_ids, column_name=None):
    if not any(cell_ids):
        logging.debug("Received empty cell_ids")
        return []

    try:
        if column_name is None:
            result = [reader_method(cell_id) for cell_id in cell_ids]
        else:
            result = [reader_method(column_name, cell_id) for cell_id in cell_ids]
    except Exception as e:
        logging.debug("Error in querying db.")
        logging.debug(e)
        result = [None for _ in range(len(cell_ids))]
    return result


def _create_pages_dict(
    reader,
    cell_ids: Optional[List[Any]] = None,
    batch_name: Optional[str] = None,
    include_key: bool = False,
    include_individual_arguments: bool = True,
    additional_column_names: Optional[List[str]] = None,
) -> PagesDict:
    """Build the raw ``pages`` dict from a reader and a set of cell IDs."""
    if cell_ids is None:
        logging.debug("cell_ids is None")
        pages_dict = reader.from_batch(
            batch_name=batch_name,
            include_key=include_key,
            include_individual_arguments=include_individual_arguments,
        )
        return pages_dict

    logging.debug("cell_ids is not None")
    pages_dict = dict()
    pages_dict[hdr_journal["filename"]] = _query(reader.get_cell_name, cell_ids)
    number_of_cells = len(pages_dict[hdr_journal["filename"]])
    logging.debug(f"number of cells in the batch: {number_of_cells}")
    if include_key:
        pages_dict[hdr_journal["id_key"]] = cell_ids
    if include_individual_arguments:
        pages_dict[hdr_journal["argument"]] = _query(reader.get_args, cell_ids)
    pages_dict[hdr_journal["mass"]] = _query(reader.get_mass, cell_ids)
    pages_dict[hdr_journal["total_mass"]] = _query(reader.get_total_mass, cell_ids)
    try:
        pages_dict[hdr_journal["nom_cap_specifics"]] = _query(
            reader.get_nom_cap_specifics, cell_ids
        )
    except Exception as e:
        logging.debug(f"Error in getting nom_cap_specifics: {e}")
        pages_dict[hdr_journal["nom_cap_specifics"]] = "gravimetric"
    try:
        _file_name_indicator = _query(reader.get_file_name_indicator, cell_ids)
        if _file_name_indicator is None:
            _file_name_indicator = _query(reader.get_cell_name, cell_ids)
        pages_dict[hdr_journal["file_name_indicator"]] = _file_name_indicator
    except Exception as e:
        logging.debug(f"Error in getting file_name_indicator: {e}")
        pages_dict[hdr_journal["file_name_indicator"]] = pages_dict[
            hdr_journal["filename"]
        ]

    journal_fields = [
        ("loading", reader.get_loading),
        ("nom_cap", reader.get_nom_cap),
        ("area", reader.get_area),
        ("experiment", reader.get_experiment_type),
        ("fixed", reader.inspect_hd5f_fixed),
        ("label", reader.get_label),
        ("cell_type", reader.get_cell_type),
        ("instrument", reader.get_instrument),
        ("comment", reader.get_comment),
        ("group", reader.get_group),
    ]

    for field_name, reader_method in journal_fields:
        try:
            pages_dict[hdr_journal[field_name]] = _query(reader_method, cell_ids)
        except Exception as e:
            logging.debug(f"Error in getting {field_name}: {e}")

    if additional_column_names is not None:
        for k in additional_column_names:
            try:
                pages_dict[k] = _query(reader.get_by_column_label, cell_ids, k)
            except Exception as e:
                logging.info(f"Could not retrieve from column {k} ({e})")

    pages_dict[hdr_journal["raw_file_names"]] = []
    pages_dict[hdr_journal["cellpy_file_name"]] = []

    return pages_dict


def _report_suspected_duplicate_id(e, what="do it", on=None):
    logging.warning(f"could not {what}")
    logging.warning(f"{on}")
    logging.warning("maybe you have a corrupted db?")
    logging.warning(
        "typically happens if the cell_id is not unique (several rows or records in "
        "your db has the same cell_id or key) or if you have non-unique cell names"
    )
    logging.warning(e)


def _check_pages_frame(pages):
    duplicates = pages.index.duplicated()
    if duplicates.any():
        logging.critical(
            f"Oh no! Found {duplicates.sum()} duplicate cell names in your db - "
            "this is not allowed!"
        )
        logging.critical(f"Duplicate cell names: {pages.index[duplicates].tolist()}")
    logging.debug(f"pages.shape: {pages.shape}")


def simple_db_engine(
    reader=None,
    cell_ids=None,
    file_list=None,
    pre_path=None,
    include_key=False,
    include_individual_arguments=True,
    additional_column_names=None,
    batch_name=None,
    clean_journal=False,
    **kwargs,
) -> pd.DataFrame:
    """Look up cell metadata from the db and find the matching files.

    Returns a pandas ``pages`` frame indexed by cell name. ``reader`` is a
    :class:`cellpy.readers.dbreader.Reader` (or a JSON reader exposing a
    ``pages_dict``); ``cell_ids`` are pre-selected db keys, or ``batch_name``
    is used to select. ``**kwargs`` are forwarded to the file finder.
    """
    logging.debug("simple_db_engine")
    if reader is None:
        reader = dbreader.Reader()
        logging.debug("No reader provided. Creating one myself.")

    if isinstance(reader, str):
        match reader:
            case "simple_excel_reader":
                reader = dbreader.Reader()
            case "batbase_json_reader":
                reader = json_dbreader.BatBaseJSONReader()
            case _:
                raise ValueError(f"Invalid reader: {reader}")

    if isinstance(reader, dbreader.Reader):
        pages_dict = _create_pages_dict(
            reader=reader,
            cell_ids=cell_ids,
            batch_name=batch_name,
            include_key=include_key,
            include_individual_arguments=include_individual_arguments,
            additional_column_names=additional_column_names,
        )
    elif hasattr(reader, "pages_dict"):
        pages_dict = reader.pages_dict
        logging.debug(
            "pages_dict from reader (number of cells): "
            f"{len(pages_dict.get(hdr_journal['filename'], []))}"
        )
    else:
        raise UnderDefined(
            "Unsupported reader (must be dbreader.Reader or provide "
            f"pages_dict): {type(reader)}"
        )

    del reader

    _groups = pages_dict[hdr_journal["group"]]
    groups = fix_groups(_groups)
    pages_dict[hdr_journal["group"]] = groups

    my_timer_start = time.time()
    logging.debug("finding files")
    pages_dict = find_files(
        pages_dict, file_list=file_list, pre_path=pre_path, **kwargs
    )
    logging.debug("files found")
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logging.debug(
            "The function find_files was very slow. "
            "Save your journal so you don't have to run it again!"
        )

    pages = pd.DataFrame(pages_dict)
    if clean_journal:
        if hdr_journal["file_name_indicator"] in pages.columns:
            pages = pages.drop(columns=[hdr_journal["file_name_indicator"]])

    try:
        pages = pages.sort_values([hdr_journal.group, hdr_journal.filename])
    except TypeError as e:
        _report_suspected_duplicate_id(
            e, "sort the values", pages[[hdr_journal.group, hdr_journal.filename]]
        )

    pages = make_unique_groups(pages)

    try:
        pages[hdr_journal.label] = pages[hdr_journal.filename].apply(create_labels)
    except AttributeError as e:
        _report_suspected_duplicate_id(
            e, "make labels", pages[[hdr_journal.label, hdr_journal.filename]]
        )
    except IndexError as e:
        logging.debug(f"Could not make labels: {e}")
    else:
        pages.set_index(hdr_journal["filename"], inplace=True)

    _check_pages_frame(pages)
    return pages
