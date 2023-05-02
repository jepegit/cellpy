"""Engines are functions that are used by the Do-ers.

    Keyword Args: experiments, farms, barn, optionals
    Returns: farms, barn
"""

import logging
import time
import warnings

import pandas as pd

from cellpy import dbreader
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.utils.batch_tools import batch_helpers as helper

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()

SELECTED_SUMMARIES = [
    hdr_summary["discharge_capacity_gravimetric"],
    hdr_summary["charge_capacity_gravimetric"],
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
                logging.debug(f"extracting cycles from {key}")
                # extract cycles here and send it to the farm
        else:
            logging.debug("dont have it in memory - need to lookup in the files")
            for key in experiment.cell_data_frames:
                logging.debug(f"looking up cellpyfile for {key}")
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
        logging.debug(f"Error in querying db.")
        logging.debug(e)
        result = [None for _ in range(len(cell_ids))]
    return result


def sql_db_engine(*args, **kwargs) -> pd.DataFrame:
    print("sql_db_engine")
    print(f"args: {args}")
    print(f"kwargs: {kwargs}")
    return pd.DataFrame()


# TODO-246: load area
def simple_db_engine(
    reader=None,
    cell_ids=None,
    file_list=None,
    pre_path=None,
    include_key=False,
    include_individual_arguments=True,
    additional_column_names=None,
    batch_name=None,
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
        additional_column_names: list of additional column names to include in the pages.
        batch_name: name of the batch (used if cell_ids are not given)
        **kwargs: sent to filefinder

    Returns:
        pages (pandas.DataFrame)
    """

    new_version = False

    # This is not really a proper Do-er engine. But not sure where to put it.
    logging.debug("simple_db_engine")
    if reader is None:
        reader = dbreader.Reader()
        logging.debug("No reader provided. Creating one myself.")

    if cell_ids is None:
        pages_dict = reader.from_batch(
            batch_name=batch_name,
            include_key=include_key,
            include_individual_arguments=include_individual_arguments,
        )

    else:
        pages_dict = dict()
        pages_dict[hdr_journal["filename"]] = _query(reader.get_cell_name, cell_ids)
        if include_key:
            pages_dict[hdr_journal["id_key"]] = cell_ids

        if include_individual_arguments:
            pages_dict[hdr_journal["argument"]] = _query(reader.get_args, cell_ids)

        pages_dict[hdr_journal["mass"]] = _query(reader.get_mass, cell_ids)
        pages_dict[hdr_journal["total_mass"]] = _query(reader.get_total_mass, cell_ids)
        pages_dict[hdr_journal["loading"]] = _query(reader.get_loading, cell_ids)
        pages_dict[hdr_journal["nom_cap"]] = _query(reader.get_nom_cap, cell_ids)
        pages_dict[hdr_journal["area"]] = _query(reader.get_area, cell_ids)
        pages_dict[hdr_journal["experiment"]] = _query(
            reader.get_experiment_type, cell_ids
        )
        pages_dict[hdr_journal["fixed"]] = _query(reader.inspect_hd5f_fixed, cell_ids)
        pages_dict[hdr_journal["label"]] = _query(reader.get_label, cell_ids)
        pages_dict[hdr_journal["cell_type"]] = _query(reader.get_cell_type, cell_ids)
        pages_dict[hdr_journal["instrument"]] = _query(reader.get_instrument, cell_ids)
        pages_dict[hdr_journal["raw_file_names"]] = []
        pages_dict[hdr_journal["cellpy_file_name"]] = []
        pages_dict[hdr_journal["comment"]] = _query(reader.get_comment, cell_ids)
        pages_dict[hdr_journal["group"]] = _query(reader.get_group, cell_ids)

        if additional_column_names is not None:
            for k in additional_column_names:
                try:
                    pages_dict[k] = _query(reader.get_by_column_label, cell_ids, k)
                except Exception as e:
                    logging.info(f"Could not retrieve from column {k} ({e})")

        logging.debug(f"created info-dict from {reader.db_file}:")

    for key in list(pages_dict.keys()):
        logging.debug("%s: %s" % (key, str(pages_dict[key])))

    _groups = pages_dict[hdr_journal["group"]]
    groups = helper.fix_groups(_groups)
    pages_dict[hdr_journal["group"]] = groups

    my_timer_start = time.time()
    pages_dict = helper.find_files(
        pages_dict, file_list=file_list, pre_path=pre_path, **kwargs
    )
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logging.critical(
            "The function _find_files was very slow. "
            "Save your journal so you don't have to run it again! "
            "You can load it again using the from_journal(journal_name) method."
        )

    pages = pd.DataFrame(pages_dict)
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
        pages[hdr_journal.label] = pages[hdr_journal.filename].apply(
            helper.create_labels
        )
    except AttributeError as e:
        _report_suspected_duplicate_id(
            e, "make labels", pages[[hdr_journal.label, hdr_journal.filename]]
        )

    else:
        # TODO: check if drop=False works [#index]
        pages.set_index(hdr_journal["filename"], inplace=True)  # edit this to allow for
        # non-numeric index-names (for tab completion and python-box)
    return pages


def _report_suspected_duplicate_id(e, what="do it", on=None):
    logging.warning(f"could not {what}")
    logging.warning(f"{on}")
    logging.warning("maybe you have a corrupted db?")
    logging.warning(
        "typically happens if the cell_id is not unique (several rows or records in "
        "your db has the same cell_id or key)"
    )
    logging.warning(e)
