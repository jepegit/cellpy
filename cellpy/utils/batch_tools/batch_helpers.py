import logging
import os
import warnings

import pandas as pd

import csv
import itertools

from cellpy import filefinder, prms
from cellpy.exceptions import ExportFailed, NullData, WrongFileVersion
import cellpy.parameters.internal_settings

# logger = logging.getLogger(__name__)
hdr_summary = cellpy.parameters.internal_settings.get_headers_summary()
hdr_journal = cellpy.parameters.internal_settings.get_headers_journal()


def look_up_and_get(cellpy_file_name, table_name, root=None):
    """Extracts table from cellpy hdf5-file."""

    # infoname = '/CellpyData/info'
    # dataname = '/CellpyData/dfdata'
    # summaryname = '/CellpyData/dfsummary'
    # fidname = '/CellpyData/fidtable'
    # stepname = '/CellpyData/step_table'

    if root is None:
        root = "/CellpyData"
    table_path = "/".join([root, table_name])

    logging.debug(f"look_up_and_get({cellpy_file_name}, {table_name}")
    store = pd.HDFStore(cellpy_file_name)
    try:
        table = store.select(table_path)
        store.close()
    except KeyError as e:
        logging.warning("Could not read the table")
        store.close()
        raise WrongFileVersion(e)
    return table


def create_folder_structure(project_name, batch_name):
    """This function creates a folder structure for the batch project.

    The folder structure consists of main working folder ``project_name`
    located in the ``outdatadir`` (as defined in the cellpy configuration file)
    with a sub-folder named ``batch_name``. It also creates a folder
    inside the ``batch_name`` folder for storing the raw data.
    If the folders does not exist, they will be made. The function also returns
    the name of the info-df.

    Args:
        project_name: name of the project
        batch_name: name of the batch

    Returns: (info_file, (project_dir, batch_dir, raw_dir))

    """
    out_data_dir = prms.Paths["outdatadir"]
    project_dir = os.path.join(out_data_dir, project_name)
    batch_dir = os.path.join(project_dir, batch_name)
    raw_dir = os.path.join(batch_dir, "raw_data")

    # create folders
    if not os.path.isdir(project_dir):
        os.mkdir(project_dir)
    if not os.path.isdir(batch_dir):
        os.mkdir(batch_dir)
    if not os.path.isdir(raw_dir):
        os.mkdir(raw_dir)

    # create file-name for the info_df (json)
    info_file = "cellpy_batch_%s.json" % batch_name
    info_file = os.path.join(project_dir, info_file)
    return info_file, (project_dir, batch_dir, raw_dir)


def find_files(info_dict, file_list=None, pre_path=None, **kwargs):
    """Find files using cellpy.filefinder.

    Args:
        info_dict: journal pages.
        file_list: list of files names to search through.
        pre_path: path to prepend found files from file_list (if file_list is given).
        **kwargs: sent to filefinder.search_for_files.

    Returns:
        info_dict
    """
    # searches for the raw data files and the cellpyfile-name
    # TODO: implement faster file searching
    # TODO: implement option for not searching for raw-file names if force_cellpy is True
    for run_name in info_dict[hdr_journal["filename"]]:
        logging.debug(f"checking for {run_name}")
        raw_files, cellpyfile = filefinder.search_for_files(run_name, file_list=file_list, pre_path=pre_path, **kwargs)
        if not raw_files:
            raw_files = None
        info_dict[hdr_journal["raw_file_names"]].append(raw_files)
        info_dict[hdr_journal["cellpy_file_name"]].append(cellpyfile)

    return info_dict


def fix_groups(groups):
    """Takes care of strange group numbers."""
    _groups = []
    for g in groups:
        try:
            if not float(g) > 0:
                _groups.append(1000)
            else:
                _groups.append(int(g))
        except TypeError as e:
            logging.info("Error in reading group number (check your db)")
            logging.debug(g)
            logging.debug(e)
            _groups.append(1000)
    return _groups


def save_multi(data, file_name, sep=";"):
    """Convenience function for storing data column-wise in a csv-file."""
    logging.debug("saving multi")
    with open(file_name, "w", newline="") as f:
        logging.debug(f"{file_name} opened")
        writer = csv.writer(f, delimiter=sep)
        try:
            writer.writerows(itertools.zip_longest(*data))
            logging.info(f"{file_name} OK")
        except Exception as e:
            logging.info(f"Exception encountered in batch._save_multi: {e}")
            raise ExportFailed
        logging.debug("wrote rows using itertools in _save_multi")


def make_unique_groups(info_df):
    """This function cleans up the group numbers a bit."""
    # fixes group numbering
    unique_g = info_df[hdr_journal.group].unique()
    unique_g = sorted(unique_g)
    new_unique_g = list(range(len(unique_g)))
    info_df[hdr_journal.sub_group] = info_df[hdr_journal.group] * 0
    for i, j in zip(unique_g, new_unique_g):
        counter = 1
        for indx, row in info_df.loc[info_df[hdr_journal.group] == i].iterrows():
            info_df.at[indx, hdr_journal.sub_group] = counter
            counter += 1
        info_df.loc[info_df[hdr_journal.group] == i, hdr_journal.group] = j + 1
    return info_df


def _remove_date_and_celltype(label,):
    parts = label.split("_")
    parts.pop(0)
    if parts[-1] in ["cc", "ec", "eth"]:
        parts.pop(-1)
    return "_".join(parts)


def create_labels(label, *args):
    """Returns a re-formatted label (currently it only removes the dates
    from the run-name)"""
    return _remove_date_and_celltype(label)


def create_selected_summaries_dict(summaries_list):
    """Creates a dictionary with summary column headers.

    Examples:
        >>> summaries_to_output = ["discharge_capacity", "charge_capacity"]
        >>> summaries_to_output_dict = create_selected_summaries_dict(
        >>>    summaries_to_output
        >>> )
        >>> print(summaries_to_output_dict)
        {'discharge_capacity': "Discharge_Capacity(mAh/g)",
               'charge_capacity': "Charge_Capacity(mAh/g)}

    Args:
        summaries_list: list containing cellpy summary column id names

    Returns: dictionary of the form {cellpy id name: cellpy summary
        header name,}

    """
    selected_summaries = dict()
    for h in summaries_list:
        selected_summaries[h] = hdr_summary[h]
    return selected_summaries


def pick_summary_data(key, summary_df, selected_summaries):
    """picks the selected pandas.DataFrame"""

    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    value = selected_summaries_dict[key]
    return summary_df.iloc[:, summary_df.columns.get_level_values(1) == value]


def join_summaries(summary_frames, selected_summaries, keep_old_header=False):
    """parse the summaries and combine based on column (selected_summaries)"""
    if not summary_frames:
        raise NullData("No summaries available to join")
    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    frames = []
    keys = []  # test-name
    for key in summary_frames:
        keys.append(key)
        if summary_frames[key].empty:
            logging.debug("Empty summary_frame encountered")
        frames.append(summary_frames[key])

    out = []

    summary_df = pd.concat(frames, keys=keys, axis=1)
    for key, value in selected_summaries_dict.items():
        _summary_df = summary_df.iloc[
            :, summary_df.columns.get_level_values(1) == value
        ]
        _summary_df.name = key

        if not keep_old_header:
            try:
                _summary_df.columns = _summary_df.columns.droplevel(-1)
            except AttributeError as e:
                logging.debug("could not drop level from frame")
                logging.debug(e)

        out.append(_summary_df)
    logging.debug("finished joining summaries")

    return out


def generate_folder_names(name, project):
    """Creates sensible folder names."""

    out_data_dir = prms.Paths.outdatadir
    project_dir = os.path.join(out_data_dir, project)
    batch_dir = os.path.join(project_dir, name)
    raw_dir = os.path.join(batch_dir, "raw_data")
    return out_data_dir, project_dir, batch_dir, raw_dir


def _extract_dqdv(cell_data, extract_func, last_cycle):
    """Simple wrapper around the cellpy.utils.ica.dqdv function."""

    from cellpy.utils.ica import dqdv

    list_of_cycles = cell_data.get_cycle_numbers()
    if last_cycle is not None:
        list_of_cycles = [c for c in list_of_cycles if c <= int(last_cycle)]
        logging.debug(f"only processing up to cycle {last_cycle}")
        logging.debug(f"you have {len(list_of_cycles)} cycles to process")
    out_data = []
    for cycle in list_of_cycles:
        try:
            c, v = extract_func(cycle)
            v, dq = dqdv(v, c)
            v = v.tolist()
            dq = dq.tolist()
        except NullData as e:
            v = list()
            dq = list()
            logging.info(" Ups! Could not process this (cycle %i)" % cycle)
            logging.info(" %s" % e)

        header_x = "dQ cycle_no %i" % cycle
        header_y = "voltage cycle_no %i" % cycle
        dq.insert(0, header_x)
        v.insert(0, header_y)

        out_data.append(v)
        out_data.append(dq)
    return out_data


def export_dqdv(cell_data, savedir, sep, last_cycle=None):
    """Exports dQ/dV data from a CellpyData instance.

    Args:
        cell_data: CellpyData instance
        savedir: path to the folder where the files should be saved
        sep: separator for the .csv-files.
        last_cycle: only export up to this cycle (if not None)
    """
    logging.debug("exporting dqdv")
    filename = cell_data.cell.loaded_from
    no_merged_sets = ""
    firstname, extension = os.path.splitext(filename)
    firstname += no_merged_sets
    if savedir:
        firstname = os.path.join(savedir, os.path.basename(firstname))
        logging.debug(f"savedir is true: {firstname}")

    outname_charge = firstname + "_dqdv_charge.csv"
    outname_discharge = firstname + "_dqdv_discharge.csv"

    list_of_cycles = cell_data.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    logging.debug("%s: you have %i cycles" % (filename, number_of_cycles))

    # extracting charge
    out_data = _extract_dqdv(cell_data, cell_data.get_ccap, last_cycle)
    logging.debug("extracted ica for charge")
    try:
        save_multi(data=out_data, file_name=outname_charge, sep=sep)
    except ExportFailed as e:
        logging.info("could not export ica for charge")
        warnings.warn(f"ExportFailed exception raised: {e}")
    else:
        logging.debug("saved ica for charge")

    # extracting discharge
    out_data = _extract_dqdv(cell_data, cell_data.get_dcap, last_cycle)
    logging.debug("extracted ica for discharge")
    try:
        save_multi(data=out_data, file_name=outname_discharge, sep=sep)
    except ExportFailed as e:
        logging.info("could not export ica for discharge")
        warnings.warn(f"ExportFailed exception raised: {e}")
    else:
        logging.debug("saved ica for discharge")
