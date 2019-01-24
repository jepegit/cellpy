import time
import logging
import pandas as pd

from cellpy import dbreader
from cellpy.utils.batch_tools import batch_helpers as helper

logger = logging.getLogger(__name__)


def cycles_engine(**kwargs):
    """engine to extract cycles"""
    logging.info("cycles_engine:")
    logging.info("Not ready for production")
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
        else:
            logging.debug("dont have it in memory - need to lookup in the files")
            for key in experiment.cell_data_frames:
                logging.debug(f"looking up cellpyfile for {key}")

    return farms, barn


def raw_data_engine(**kwargs):
    """engine to extract raw data"""
    logger.debug("cycles_engine")
    raise NotImplementedError

    experiments = kwargs["experiments"]
    farms = []
    barn = "raw_dir"

    for experiment in experiments:
        farms.append([])

    return farms, barn


def summary_engine(**kwargs):
    """engine to extract summary data"""
    logger.debug("summary_engine")
    # farms = kwargs["farms"]

    farms = []
    experiments = kwargs["experiments"]

    for experiment in experiments:
        if experiment.selected_summaries is None:
            selected_summaries = [
                "discharge_capacity", "charge_capacity",
                "coulombic_efficiency",
                "cumulated_coulombic_efficiency",
                "ir_discharge", "ir_charge",
                "end_voltage_discharge", "end_voltage_charge",
            ]
        else:
            selected_summaries = experiment.selected_summaries
        farm = helper.join_summaries(
            experiment.summary_frames,
            selected_summaries
        )
        farms.append(farm)
    barn = "batch_dir"

    return farms, barn


def dq_dv_engine(**kwargs):
    """engine that performs incremental analysis of the cycle-data"""
    farms = None
    barn = "raw_dir"
    return farms, barn


def simple_db_engine(reader=None, srnos=None):
    """engine that gets values from the simple excel 'db'"""

    if reader is None:
        reader = dbreader.Reader()
        logger.debug("No reader provided. Creating one myself.")

    info_dict = dict()
    info_dict["filenames"] = [reader.get_cell_name(srno) for srno in srnos]
    info_dict["masses"] = [reader.get_mass(srno) for srno in srnos]
    info_dict["total_masses"] = [reader.get_total_mass(srno) for srno in srnos]
    info_dict["loadings"] = [reader.get_loading(srno) for srno in srnos]
    info_dict["fixed"] = [reader.inspect_hd5f_fixed(srno) for srno in srnos]
    info_dict["labels"] = [reader.get_label(srno) for srno in srnos]
    info_dict["cell_type"] = [reader.get_cell_type(srno) for srno in srnos]
    info_dict["raw_file_names"] = []
    info_dict["cellpy_file_names"] = []

    logger.debug("created info-dict")

    for key in list(info_dict.keys()):
        logger.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logger.debug(">\ngroups: %s" % str(_groups))
    groups = helper.fix_groups(_groups)
    info_dict["groups"] = groups

    my_timer_start = time.time()
    filename_cache = []
    info_dict = helper.find_files(info_dict, filename_cache)
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logger.info(
            "The function _find_files was very slow. "
            "Save your info_df so you don't have to run it again!"
        )

    info_df = pd.DataFrame(info_dict)
    info_df = info_df.sort_values(["groups", "filenames"])
    info_df = helper.make_unique_groups(info_df)

    info_df["labels"] = info_df["filenames"].apply(helper.create_labels)
    info_df.set_index("filenames", inplace=True)
    return info_df
