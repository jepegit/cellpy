import time
import logging
import pandas as pd

from cellpy import cellreader, dbreader
from cellpy.utils import batch_helpers as helper

logger = logging.getLogger(__name__)


def cycles_engine():
    """engine to extract cycles"""
    pass


def summary_engine():
    """engine to extract summary data"""
    pass


def dq_dv_engine():
    """engine that performs incremental analysis of the cycle-data"""
    pass


def simple_db_engine(reader=None, srnos=None):
    """engine that gets values from the simple excel 'db'"""

    if reader is None:
        reader = dbreader.Reader

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
    for key in list(info_dict.keys()):
        logger.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logger.debug("groups: %s" % str(_groups))
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
