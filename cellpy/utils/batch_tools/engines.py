import time
import logging
import pandas as pd

from cellpy import dbreader
from cellpy.parameters.internal_settings import get_headers_journal
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

hdr_journal = get_headers_journal()


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
    logging.debug("cycles_engine")
    raise NotImplementedError

    experiments = kwargs["experiments"]
    farms = []
    barn = "raw_dir"

    for experiment in experiments:
        farms.append([])

    return farms, barn


def summary_engine(**kwargs):
    """engine to extract summary data"""
    logging.debug("summary_engine")
    # farms = kwargs["farms"]

    farms = []
    experiments = kwargs["experiments"]

    for experiment in experiments:
        if experiment.selected_summaries is None:
            selected_summaries = SELECTED_SUMMARIES
        else:
            selected_summaries = experiment.selected_summaries

        if experiment.summary_frames is None:
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
    return farms, barn


def simple_db_engine(reader=None, srnos=None):
    """engine that gets values from the simple excel 'db'"""

    if reader is None:
        reader = dbreader.Reader()
        logging.debug("No reader provided. Creating one myself.")

    info_dict = dict()
    info_dict[hdr_journal["filename"]] = [reader.get_cell_name(srno) for srno in srnos]
    info_dict[hdr_journal["mass"]] = [reader.get_mass(srno) for srno in srnos]
    info_dict[hdr_journal["total_mass"]] = [
        reader.get_total_mass(srno) for srno in srnos
    ]
    info_dict[hdr_journal["loading"]] = [reader.get_loading(srno) for srno in srnos]

    info_dict[hdr_journal["nom_cap"]] = [reader.get_nom_cap(srno) for srno in srnos]
    info_dict[hdr_journal["experiment"]] = [
        reader.get_experiment_type(srno) for srno in srnos
    ]

    info_dict[hdr_journal["fixed"]] = [
        reader.inspect_hd5f_fixed(srno) for srno in srnos
    ]
    info_dict[hdr_journal["label"]] = [reader.get_label(srno) for srno in srnos]
    info_dict[hdr_journal["cell_type"]] = [reader.get_cell_type(srno) for srno in srnos]
    info_dict[hdr_journal["raw_file_names"]] = []
    info_dict[hdr_journal["cellpy_file_name"]] = []
    info_dict[hdr_journal["comment"]] = [reader.get_comment(srno) for srno in srnos]

    logging.debug(f"created info-dict from {reader.db_file}:")
    # logging.debug(info_dict)

    for key in list(info_dict.keys()):
        logging.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logging.debug(">\ngroups: %s" % str(_groups))
    groups = helper.fix_groups(_groups)
    info_dict[hdr_journal["group"]] = groups

    my_timer_start = time.time()
    filename_cache = []
    info_dict = helper.find_files(info_dict, filename_cache)
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logging.info(
            "The function _find_files was very slow. "
            "Save your info_df so you don't have to run it again!"
        )

    info_df = pd.DataFrame(info_dict)

    info_df = info_df.sort_values([hdr_journal.group, hdr_journal.filename])
    info_df = helper.make_unique_groups(info_df)

    info_df[hdr_journal.label] = info_df[hdr_journal.filename].apply(
        helper.create_labels
    )

    # TODO: check if drop=False works [#index]
    info_df.set_index(hdr_journal["filename"], inplace=True)  # edit this to allow for
    # non-nummeric index-names (for tab completion and python-box)
    return info_df
