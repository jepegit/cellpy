"""Routines for batch processing of cells"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import warnings
import logging
import pandas as pd
import itertools
import csv

from cellpy.parameters import prms as prms
from cellpy import cellreader, dbreader, filefinder
logger = logging.getLogger(__name__)

logging.captureWarnings(True)

batch_prms = dict()
batch_prms["batch_name"] = "MyBatch"
batch_prms["project_name"] = "MyCellpyProject"


def _remove_date(label):
    _ = label.split("_")
    return _[1]+"_"+_[2]

def create_labels(label):
    return _remove_date(label)


def _fix_groups(groups):
    _groups = []
    for g in groups:
        if not float(g) > 0:
            _groups.append(1000)
        else:
            _groups.append(int(g))
    return _groups


def _get_reader():
    return dbreader.reader


def _create_info_dict(reader, srnos):
    info_dict = dict()
    info_dict["filenames"] = [reader.get_cell_name(srno) for srno in srnos]
    info_dict["masses"] = [reader.get_mass(srno) for srno in srnos]
    info_dict["total_masses"] = [reader.get_total_mass(srno) for srno in srnos]
    info_dict["loadings"] = [reader.get_loading(srno) for srno in srnos]
    info_dict["fixed"] = [reader.inspect_hd5f_fixed(srno) for srno in srnos]
    info_dict["labels"] = [reader.get_label(srno) for srno in srnos]

    info_dict["raw_file_names"] = []
    info_dict["cellpy_file_names"] = []

    _groups = [reader.get_group(srno) for srno in srnos]
    groups = _fix_groups(_groups)
    info_dict["groups"] = groups

    info_dict = _find_files(info_dict)

    return info_dict


def _find_files(info_dict):
    for run_name in info_dict["filenames"]:
        raw_files, cellpyfile = filefinder.search_for_files(run_name)
        if not raw_files:
            raw_files = None
        info_dict["raw_file_names"].append(raw_files)
        info_dict["cellpy_file_names"].append(cellpyfile)

    return info_dict


def _make_unique_groups(info_df):
    unique_g = info_df.groups.unique()
    unique_g = sorted(unique_g)
    new_unique_g = range(len(unique_g))
    info_df["sub_groups"] = info_df["groups"] * 0
    for i, j in zip(unique_g, new_unique_g):
        counter = 1
        for indx, row in info_df.loc[info_df.groups == i].iterrows():
            info_df.set_value(indx, "sub_groups", counter)
            counter += 1
        info_df.loc[info_df.groups == i, 'groups'] = j + 1
    return info_df


def set_project(project_name):
    batch_prms["project_name"] = project_name

    # project_name = "SiBEC"

def make_df_from_batch(batch_name, batch_col=5, reader_type=None):
    batch_name = batch_name
    batch_col = batch_col

    reader = _get_reader()
    batch_prms["srnos"] = reader.select_batch(batch_name, batch_col)

    info_dict = _create_info_dict(reader, srnos)
    info_df = pd.DataFrame(info_dict)
    info_df = info_df.sort_values(["groups", "filenames"])
    info_df = _make_unique_groups(info_df)
    info_df["labels"] = info_df["filenames"].apply(create_labels)
    info_df.set_index("filenames", inplace=True)

    return info_df

def create_folder_structure(info_df, project_name=None, batch_name=None):
    if project_name is None:
        project_name = batch_prms["project_name"]
    if batch_name is None:
        batch_name = batch_prms["batch_name"]

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

    # saving the json file
    info_df.to_json(info_file)


def save_multi(data, file_name, sep=";"):
    with open(file_name, "wb") as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(itertools.izip_longest(*data))



def __read_and_save_data(info_df, raw_dir):
    cycle_mode = "anode"
    force_raw = False
    no_export = False
    export_cycles = True
    export_raw = True
    do_export_dqdv = True
    keys = []
    frames = []
    for indx, row in info_df.iterrows():
        if not row.raw_file_names:
            print("File not found!")
            print(indx)
        else:
            print("Processing (%s)..." % indx)
            cell_data = cellreader.cellpydata()
            # cell_data.set_cellpy_datadir(prms.cellpydatadir)
            # cell_data.set_raw_datadir(prms.rawdatadir)
            cell_data.set_cycle_mode(cycle_mode)
            cell_data.loadcell(raw_files=row.raw_file_names, cellpy_file=row.cellpy_file_names,
                               mass=row.masses, summary_on_raw=True,
                               force_raw=force_raw)
            if not cell_data.check():
                print("...not loaded...")
            else:
                print("...loaded succesfully...")
                # keys.append(row.filenames) # this will not work anymore since we promoted filenames to index
                keys.append(indx)
                # process summary
                summary_tmp = cell_data.get_summary()
                summary_tmp.set_index("Cycle_Index", inplace=True)
                frames.append(summary_tmp)

                # process raw_data
                # export cycles
                # save normal, stats, and step tables
                if not no_export:
                    print("...exporting data....")
                    cell_data.exportcsv(raw_dir, sep=";", cycles=export_cycles, raw=export_raw)
                    # calc and export dqdv
                    if do_export_dqdv:
                        export_dqdv(cell_data, savedir=raw_dir, sep=";")
    return frames, keys


def save_summaries(frames, keys):
    batch_dir = " get me"
    batch_name = " get me"

    selected_summaries = dict()
    selected_summaries["charge_cap"] = "Charge_Capacity(mAh/g)"
    selected_summaries["discharge_cap"] = "Discharge_Capacity(mAh/g)"
    selected_summaries["coulombic_eff"] = "Coulombic_Efficiency(percentage)"
    selected_summaries["internal_resistance_charge"] = "IR_Charge(Ohms)"
    selected_summaries["internal_resistance_discharge"] = "IR_Discharge(Ohms)"
    selected_summaries["cum_coul_diff"] = "Cumulated_Coulombic_Difference(mAh/g)"
    summary_df = pd.concat(frames, keys=keys, axis=1)
    # saving the selected summaries
    for key, value in selected_summaries.iteritems():
        _summary_file_name = os.path.join(batch_dir, "summary_%s_%s.csv" % (key, batch_name))
        _summary_df = summary_df.iloc[:, summary_df.columns.get_level_values(1) == value]
        # include function to tweak headers here (need to learn MultiIndex)
        _header = _summary_df.columns
        _summary_df.to_csv(_summary_file_name, sep=";")

#----------------------

def extract_dqdv(cell_data, extract_func):
    # extracting charge
    list_of_cycles = cell_data.get_cycle_numbers()
    out_data = []
    for cycle in list_of_cycles:
        c, v = extract_func(cycle)
        try:
            v, dQ = dqdv(v, c)
            v = v.tolist()
            dQ = dQ.tolist()
        except IndexError or OverflowError as e:
            error_in_dqdv = True
            v = list()
            dq = list()
            print(" -could not process this (cycle %i)" % (cycle))
            print(" %s" % e)

        header_x = "dQ cycle_no %i" % cycle
        header_y = "voltage cycle_no %i" % cycle
        dQ.insert(0, header_x)
        v.insert(0, header_y)

        out_data.append(v)
        out_data.append(dQ)
    return out_data


def export_dqdv(cell_data, savedir, sep):
    filename = cell_data.tests[0].loaded_from  # should probably include a method in cellpyreader to extract this value
    no_merged_sets = ""
    firstname, extension = os.path.splitext(filename)
    firstname += no_merged_sets
    if savedir:
        firstname = os.path.join(savedir, os.path.basename(firstname))
    outname_charge = firstname + "_dqdv_charge.csv"
    outname_discharge = firstname + "_dqdv_discharge.csv"

    list_of_cycles = cell_data.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print("%s: you have %i cycles" % (filename, number_of_cycles))

    # extracting charge
    out_data = extract_dqdv(cell_data, cell_data.get_ccap)
    save_multi(data=out_data, file_name=outname_charge, sep=sep)

    # extracting discharge
    out_data = extract_dqdv(cell_data, cell_data.get_dcap)
    save_multi(data=out_data, file_name=outname_discharge, sep=sep)


if __name__ == '__main__':
    warnings.warn("to be implemented")
