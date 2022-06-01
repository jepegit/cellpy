"""Engines are functions that are used by the Do-ers.

    Keyword Args: experiments, farms, barn, optionals
    Returns: farms, barn
"""

import logging
import time

import pandas as pd

from cellpy import dbreader
from cellpy.parameters.internal_settings import headers_journal
from cellpy.utils.batch_tools import batch_helpers as helper

# logger = logging.getLogger(__name__)


SELECTED_SUMMARIES = [
    "discharge_capacity",
    "charge_capacity",
    "coulombic_efficiency",
    "cumulated_coulombic_efficiency",
    "ir_discharge",
    "ir_charge",
    "end_voltage_discharge",
    "end_voltage_charge",
    "charge_c_rate",
    "discharge_c_rate",
]


def cycles_engine(**kwargs):
    """engine to extract cycles"""
    logging.debug("cycles_engine::Not finished yet (sorry).")
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
        summary_frames[label] = experiment.data[label].cell.summary
    return summary_frames


def dq_dv_engine(**kwargs):
    """engine that performs incremental analysis of the cycle-data"""
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


def simple_db_engine(
    reader=None,
    cell_ids=None,
    file_list=None,
    pre_path=None,
    include_key=False,
    include_individual_arguments=True,
    additional_column_names=None,
    **kwargs,
):
    """Engine that gets values from the db for given set of cell IDs.

    The simple_db_engine looks up values for mass, names, etc. from
    the db using the reader object. In addition, it searches for the
    corresponding raw files / data.

    Args:
        reader: a reader object (defaults to dbreader.Reader)
        cell_ids: keys (cell IDs)
        file_list: file list to send to filefinder (instead of searching in folders for files).
        pre_path: prepended path to send to filefinder.
        include_key: include the key col in the pages (the cell IDs).
        include_individual_arguments: include the argument column in the pages.
        additional_column_names: list of additional column names to include in the pages.
        **kwargs: sent to filefinder

    Returns:
        pages (pandas.DataFrame)
    """

    # This is not really a proper Do-er engine. But not sure where to put it.
    if reader is None:
        reader = dbreader.Reader()
        logging.debug("No reader provided. Creating one myself.")
    pages_dict = dict()
    pages_dict[headers_journal["filename"]] = _query(reader.get_cell_name, cell_ids)
    if include_key:
        pages_dict[headers_journal["id_key"]] = cell_ids

    if include_individual_arguments:
        pages_dict[headers_journal["argument"]] = _query(reader.get_args, cell_ids)

    pages_dict[headers_journal["mass"]] = _query(reader.get_mass, cell_ids)
    pages_dict[headers_journal["total_mass"]] = _query(reader.get_total_mass, cell_ids)
    pages_dict[headers_journal["loading"]] = _query(reader.get_loading, cell_ids)
    pages_dict[headers_journal["nom_cap"]] = _query(reader.get_nom_cap, cell_ids)
    pages_dict[headers_journal["experiment"]] = _query(reader.get_experiment_type, cell_ids)
    pages_dict[headers_journal["fixed"]] = _query(reader.inspect_hd5f_fixed, cell_ids)
    pages_dict[headers_journal["label"]] = _query(reader.get_label, cell_ids)
    pages_dict[headers_journal["cell_type"]] = _query(reader.get_cell_type, cell_ids)
    pages_dict[headers_journal["instrument"]] = _query(reader.get_instrument, cell_ids)
    pages_dict[headers_journal["raw_file_names"]] = []
    pages_dict[headers_journal["cellpy_file_name"]] = []
    pages_dict[headers_journal["comment"]] = _query(reader.get_comment, cell_ids)

    if additional_column_names is not None:
        for k in additional_column_names:
            try:
                pages_dict[k] = _query(reader.get_by_column_label, cell_ids, k)
            except Exception as e:
                logging.info(f"Could not retrieve from column {k} ({e})")

    # get id_key (not implemented yet

    logging.debug(f"created info-dict from {reader.db_file}:")
    # logging.debug(info_dict)

    for key in list(pages_dict.keys()):
        logging.debug("%s: %s" % (key, str(pages_dict[key])))

    _groups = _query(reader.get_group, cell_ids)

    logging.debug(">\ngroups: %s" % str(_groups))
    groups = helper.fix_groups(_groups)
    pages_dict[headers_journal["group"]] = groups

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
        pages = pages.sort_values([headers_journal.group, headers_journal.filename])
    except TypeError as e:
        _report_suspected_duplicate_id(e, "sort the values", pages[[headers_journal.group, headers_journal.filename]])

    pages = helper.make_unique_groups(pages)

    try:
        pages[headers_journal.label] = pages[headers_journal.filename].apply(
            helper.create_labels
        )
    except AttributeError as e:
        _report_suspected_duplicate_id(e, "make labels", pages[[headers_journal.label, headers_journal.filename]])

    else:
        # TODO: check if drop=False works [#index]
        pages.set_index(
            headers_journal["filename"], inplace=True
        )  # edit this to allow for
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
