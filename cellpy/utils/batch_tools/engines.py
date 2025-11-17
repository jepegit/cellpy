"""Engines are functions that are used by the Do-ers.

    Keyword Args: experiments, farms, barn, optionals
    Returns: farms, barn
"""

import logging
import time
import warnings
from typing import List, Any, Optional

import pandas as pd

from cellpy import dbreader
from cellpy.readers.core import PagesDictBase
from cellpy.readers import json_dbreader
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.utils.batch_tools import batch_helpers as helper

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()

PagesDict = PagesDictBase


# For allowing additional keys beyond the base structure:
# PagesDict = Dict[str, List[Union[str, float, int, None]]] for flexibility

SELECTED_SUMMARIES = [
    hdr_summary["discharge_capacity_gravimetric"],
    hdr_summary["charge_capacity_gravimetric"],
    hdr_summary["discharge_capacity_areal"],
    hdr_summary["charge_capacity_areal"],
    hdr_summary["discharge_capacity"],  # raw
    hdr_summary["charge_capacity"],  # raw
    hdr_summary["discharge_capacity_absolute"],  # absolute
    hdr_summary["charge_capacity_absolute"],  # absolute
    hdr_summary["coulombic_efficiency"],
    hdr_summary["cumulated_coulombic_efficiency"],
    hdr_summary["ir_discharge"],
    hdr_summary["ir_charge"],
    hdr_summary["end_voltage_discharge"],
    hdr_summary["end_voltage_charge"],
    hdr_summary["charge_c_rate"],
    hdr_summary["discharge_c_rate"],
]


def cycles_engine(**kwargs):
    """engine to extract cycles"""
    logging.debug("cycles_engine::Not finished yet (sorry).")
    warnings.warn(
        "This utility function will be seriously changed soon and possibly removed",
        category=DeprecationWarning,
    )
    # raise NotImplementedError

    experiments = kwargs["experiments"]

    farms = []
    barn = "raw_dir"  # Its a murder in the red barn - murder in the red barn

    for experiment in experiments:
        farms.append([])
        if experiment.all_in_memory:
            logging.debug("all in memory")
            for key in experiment.cell_data_frames:
                logging.debug(f"extracting cycles from {key} (NOT IMPLEMENTED YET)")
                # extract cycles here and send it to the farm
        else:
            logging.debug("dont have it in memory - need to lookup in the files")
            for key in experiment.cell_data_frames:
                logging.debug(f"looking up cellpyfile for {key} (NOT IMPLEMENTED YET)")
                # extract cycles here and send it to the farm

    return farms, barn


def raw_data_engine(**kwargs):
    """engine to extract raw data"""
    warnings.warn(
        "This utility function will be seriously changed soon and possibly removed",
        category=DeprecationWarning,
    )
    logging.debug("cycles_engine")
    farms = None
    barn = "raw_dir"
    raise NotImplementedError


def summary_engine(**kwargs):
    """engine to extract summary data"""
    logging.debug("summary_engine")
    # farms = kwargs["farms"]

    farms = []
    experiments = kwargs.pop("experiments")
    reset = kwargs.pop("reset", False)

    for experiment in experiments:
        if experiment.selected_summaries is None:
            selected_summaries = SELECTED_SUMMARIES
        else:
            selected_summaries = experiment.selected_summaries
        logging.debug(f"selected summaries: {selected_summaries}")
        if reset or experiment.summary_frames is None:
            logging.debug("No summary frames found")
            logging.debug("Re-loading")
            experiment.summary_frames = _load_summaries(experiment)
        farm = helper.join_summaries(experiment.summary_frames, selected_summaries)
        farms.append(farm)
    barn = "batch_dir"

    return farms, barn


def _load_summaries(experiment):
    summary_frames = {}
    for label in experiment.cell_names:
        # TODO: replace this with direct lookup from hdf5?
        summary_frames[label] = experiment.data[label].data.summary
    return summary_frames


def dq_dv_engine(**kwargs):
    """engine that performs incremental analysis of the cycle-data"""
    warnings.warn(
        "This utility function will be seriously changed soon and possibly removed",
        category=DeprecationWarning,
    )
    farms = None
    barn = "raw_dir"
    raise NotImplementedError


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
    """Create pages_dict from reader and cell_ids.
    
    Args:
        reader: a reader object (dbreader.Reader or json_dbreader.BatbaseJSONReader)
        cell_ids: keys (cell IDs) or None to use batch_name
        batch_name: name of the batch (used if cell_ids are not given)
        include_key: include the key col in the pages (the cell IDs)
        include_individual_arguments: include the argument column in the pages
        additional_column_names: list of additional column names to include in the pages
        
    Returns:
        pages_dict: dictionary with journal data (PagesDict type)
    """
    if cell_ids is None:
        logging.debug("cell_ids is None")
        pages_dict = reader.from_batch(
            batch_name=batch_name,
            include_key=include_key,
            include_individual_arguments=include_individual_arguments,
        )
        logging.debug("pages_dict: {pages_dict}")

    else:
        logging.debug("cell_ids is not None")
        pages_dict = dict()
        # TODO: rename this to "cell" or "cell_id" or something similar:
        pages_dict[hdr_journal["filename"]] = _query(reader.get_cell_name, cell_ids)
        # How many cells are in the batch?
        number_of_cells = len(pages_dict[hdr_journal["filename"]])
        logging.debug(f"number of cells in the batch: {number_of_cells}")
        if include_key:
            pages_dict[hdr_journal["id_key"]] = cell_ids
        if include_individual_arguments:
            pages_dict[hdr_journal["argument"]] = _query(reader.get_args, cell_ids)
        pages_dict[hdr_journal["mass"]] = _query(reader.get_mass, cell_ids)
        pages_dict[hdr_journal["total_mass"]] = _query(reader.get_total_mass, cell_ids)
        try:
            pages_dict[hdr_journal["nom_cap_specifics"]] = _query(reader.get_nom_cap_specifics, cell_ids)
        except Exception as e:
            logging.debug(f"Error in getting nom_cap_specifics: {e}")
            pages_dict[hdr_journal["nom_cap_specifics"]] = "gravimetric"
        try:
            # updated 06.01.2025: some old db files returns None for file_name_indicator
            _file_name_indicator = _query(reader.get_file_name_indicator, cell_ids)
            if _file_name_indicator is None:
                _file_name_indicator = _query(reader.get_cell_name, cell_ids)
            pages_dict[hdr_journal["file_name_indicator"]] = _file_name_indicator
        except Exception as e:
            logging.debug(f"Error in getting file_name_indicator: {e}")
            pages_dict[hdr_journal["file_name_indicator"]] = pages_dict[
                hdr_journal["filename"]
            ]  # TODO: use of "filename"!

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


def sql_db_engine(*args, **kwargs) -> pd.DataFrame:
    print("sql_db_engine")
    print(f"args: {args}")
    print(f"kwargs: {kwargs}")
    return pd.DataFrame()


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
):
    """Engine that gets values from the db for given set of cell IDs.

    The simple_db_engine looks up values for mass, names, etc. from
    the db using the reader object. In addition, it searches for the
    corresponding raw files / data.

    Args:
        reader: a reader object (defaults to dbreader.Reader)
        cell_ids: keys (cell IDs) (assumes that the db has already been filtered, if not, use batch_name).
        file_list: file list to send to filefinder (instead of searching in folders for files).
        pre_path: prepended path to send to filefinder.
        include_key: include the key col in the pages (the cell IDs).
        include_individual_arguments: include the argument column in the pages.
        additional_column_names: list of additional column names to include in the pages (only valid for the simple excel reader).
        batch_name: name of the batch (used if cell_ids are not given)
        clean_journal: remove the file_name_indicator column from the pages (default: True).
        **kwargs: sent to filefinder

    Returns:
        pages (pandas.DataFrame)
    """

    # This is not really a proper Do-er engine. But not sure where to put it.
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
    elif isinstance(reader, json_dbreader.BatBaseJSONReader):
        pages_dict = reader.pages_dict
        logging.debug(f"pages_dict: {pages_dict}")
        logging.debug(f"number of cells in the batch: {len(pages_dict[hdr_journal['filename']])}")

    logging.debug(f"created info-dict from {reader.db_file}:")
    del reader

    for key in list(pages_dict.keys()):
        logging.debug(f"[length: {len(pages_dict[key]):04d}] {key}: {str(pages_dict[key])}")

    _groups = pages_dict[hdr_journal["group"]]
    groups = helper.fix_groups(_groups)
    pages_dict[hdr_journal["group"]] = groups
    my_timer_start = time.time()
    logging.debug("finding files")
    pages_dict = helper.find_files(pages_dict, file_list=file_list, pre_path=pre_path, **kwargs)
    logging.debug("files found")
    logging.debug(f"pages_dict: {pages_dict}")
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logging.debug(
            "The function _find_files was very slow. "
            "Save your journal so you don't have to run it again! "
            "You can load it again using the from_journal(journal_name) method."
        )
    pages = pd.DataFrame(pages_dict)
    if clean_journal:
        if hdr_journal["file_name_indicator"] in pages.columns:
            pages = pages.drop(columns=[hdr_journal["file_name_indicator"]])

    try:
        pages = pages.sort_values([hdr_journal.group, hdr_journal.filename])
    except TypeError as e:
        _report_suspected_duplicate_id(
            e,
            "sort the values",
            pages[[hdr_journal.group, hdr_journal.filename]],
        )

    pages = helper.make_unique_groups(pages)

    try:
        pages[hdr_journal.label] = pages[hdr_journal.filename].apply(helper.create_labels)
    except AttributeError as e:
        _report_suspected_duplicate_id(e, "make labels", pages[[hdr_journal.label, hdr_journal.filename]])
    except IndexError as e:
        logging.debug(f"Could not make labels: {e}")
    except Exception as e:
        logging.debug(f"Could not make labels (UNHANDLED EXCEPTION): {e}")
        raise e

    else:
        # TODO: check if drop=False works [#index]
        pages.set_index(hdr_journal["filename"], inplace=True)  # edit this to allow for
        # non-numeric index-names (for tab completion and python-box)
    _check_pages_frame(pages)
    return pages


def _check_pages_frame(pages):
    logging.debug(f"pages.columns: {pages.columns}")
    logging.debug(f"pages.index: {pages.index}")
    logging.debug(f"pages.index.unique(): {pages.index.unique()}")
    logging.debug(f"pages.dtypes: {pages.dtypes}")
    duplicates = pages.index.duplicated()
    if duplicates.any():
        logging.critical(f"Oh no! Found {duplicates.sum()} duplicate cell names in your db - this is not allowed!")
        logging.critical(f"Duplicate cell names: {pages.index[duplicates].tolist()}")
    else:
        logging.debug("No duplicate indices found")
    logging.debug(f"pages.shape: {pages.shape}")


def _report_suspected_duplicate_id(e, what="do it", on=None):
    logging.warning(f"could not {what}")
    logging.warning(f"{on}")
    logging.warning("maybe you have a corrupted db?")
    logging.warning(
        "typically happens if the cell_id is not unique (several rows or records in "
        "your db has the same cell_id or key) or if you have non-unique cell names"
    )
    logging.warning(e)
