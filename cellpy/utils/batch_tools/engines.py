"""Engines are functions that are used by the Do-ers.

    Keyword Args: experiments, farms, barn, optionals
    Returns: farms, barn
"""

import time
import logging
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


def simple_db_engine(
    reader=None, srnos=None, file_list=None, pre_path=None, include_key=False, **kwargs
):
    """engine that gets values from the simple excel 'db'"""
    # This is not really a proper Do-er engine. But not sure where to put it.
    if reader is None:
        reader = dbreader.Reader()
        logging.debug("No reader provided. Creating one myself.")

    info_dict = dict()
    info_dict[headers_journal["filename"]] = [reader.get_cell_name(srno) for srno in srnos]
    if include_key:
        info_dict[headers_journal["id_key"]] = srnos
    info_dict[headers_journal["mass"]] = [reader.get_mass(srno) for srno in srnos]
    info_dict[headers_journal["total_mass"]] = [
        reader.get_total_mass(srno) for srno in srnos
    ]
    info_dict[headers_journal["loading"]] = [reader.get_loading(srno) for srno in srnos]

    info_dict[headers_journal["nom_cap"]] = [reader.get_nom_cap(srno) for srno in srnos]
    info_dict[headers_journal["experiment"]] = [
        reader.get_experiment_type(srno) for srno in srnos
    ]

    info_dict[headers_journal["fixed"]] = [
        reader.inspect_hd5f_fixed(srno) for srno in srnos
    ]
    info_dict[headers_journal["label"]] = [reader.get_label(srno) for srno in srnos]
    info_dict[headers_journal["cell_type"]] = [reader.get_cell_type(srno) for srno in srnos]
    info_dict[headers_journal["instrument"]] = [
        reader.get_instrument(srno) for srno in srnos
    ]
    info_dict[headers_journal["raw_file_names"]] = []
    info_dict[headers_journal["cellpy_file_name"]] = []
    info_dict[headers_journal["comment"]] = [reader.get_comment(srno) for srno in srnos]

    # get id_key (not implemented yet

    logging.debug(f"created info-dict from {reader.db_file}:")
    # logging.debug(info_dict)

    for key in list(info_dict.keys()):
        logging.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logging.debug(">\ngroups: %s" % str(_groups))
    groups = helper.fix_groups(_groups)
    info_dict[headers_journal["group"]] = groups

    my_timer_start = time.time()
    info_dict = helper.find_files(
        info_dict, file_list=file_list, pre_path=pre_path, **kwargs
    )
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logging.critical(
            "The function _find_files was very slow. "
            "Save your journal so you don't have to run it again! "
            "You can load it again using the from_journal(journal_name) method."
        )

    info_df = pd.DataFrame(info_dict)
    try:
        info_df = info_df.sort_values([headers_journal.group, headers_journal.filename])
    except TypeError as e:
        logging.warning("could not sort the values")
        logging.warning(f"{info_df[[headers_journal.group, headers_journal.filename]]}")
        logging.warning("maybe you have a corrupted db?")
        logging.warning(
            "typically happens if the srno is not unique (several rows or records in "
            "your db has the same srno or key)"
        )
        logging.warning(e)

    info_df = helper.make_unique_groups(info_df)
    try:
        info_df[headers_journal.label] = info_df[headers_journal.filename].apply(
            helper.create_labels
        )
    except AttributeError as e:
        logging.warning("could not make labels")
        logging.warning("maybe you have a corrupted db?")
        logging.warning(
            "typically happens if the srno is not unique (several rows or records in "
            "your db has the same srno or key)"
        )
        logging.warning(e)
    else:
        # TODO: check if drop=False works [#index]
        info_df.set_index(
            headers_journal["filename"], inplace=True
        )  # edit this to allow for
        # non-numeric index-names (for tab completion and python-box)
    return info_df
