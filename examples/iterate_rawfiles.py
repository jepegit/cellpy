"""Script for iterating through data sets (raw-files) and extracting C.E."""
import os
from cellpy import cellreader, dbreader, prmreader, filefinder, log
import numpy as np
import pandas as pd
import collections
import logging
log_level = logging.DEBUG  # set to logging.DEBUG for more output
log.setup_logging(default_level=log_level)


def get_cum_coul_diff(df, cycles=[1, 5, 10, 20, 50]):
    window = df["Cumulated_Coulombic_Difference(mAh/g)"].rolling(window=5, center=True, axis=0)
    averaged_value = window.mean()
    df['Cumulated_Coulombic_Difference(mAh/g)'] = averaged_value
    df['Cumulated_Coulombic_Difference(mAh/g)'].fillna(method="ffill", inplace=True)
    df['Cumulated_Coulombic_Difference(mAh/g)'].fillna(method="bfill", inplace=True)
    out = []
    for i in cycles:
        try:
            value = df.loc[df['Cycle_Index'] == i,"Cumulated_Coulombic_Difference(mAh/g)"].values[0]
            out.append(value)
        except IndexError:
            out.append(np.nan)
    return out


def get_lifetime(df, average_cycles=[4,5,6], min_cap=100.0):
    ref_capacity = df.loc[df['Cycle_Index'].isin(average_cycles),'Charge_Capacity(mAh/g)'].mean()
    if ref_capacity < min_cap:
        return 0, False
    last_cycle = df['Cycle_Index'].max()
    if last_cycle < max(average_cycles):
        return 0, False
    window = df[['Cycle_Index','Charge_Capacity(mAh/g)']].rolling(window=5,center=True,axis=0)
    averaged_capacity = window.mean()
    df['Charge_Capacity(mAh/g)'] = averaged_capacity['Charge_Capacity(mAh/g)']
    df['Charge_Capacity(mAh/g)'].fillna(method="ffill", inplace=True)
    df['Charge_Capacity(mAh/g)'].fillna(method="bfill", inplace=True)
    good_cycles = df.loc[(df['Charge_Capacity(mAh/g)'] > 0.8*ref_capacity),'Cycle_Index']
    # here we could include a for-loop to find holes
    life = good_cycles.max()
    if life < last_cycle:
        to_max = False
    else:
        to_max = True
    return life, to_max


def check_files(raw_files):
    for f in raw_files:
        if not os.path.isfile(f):
            return False
        if not acceptable_file_size(f):
            return False
    return True


def acceptable_file_size(file_name, max_size=33333333):
    fid_st = os.stat(file_name)
    if fid_st.st_size > max_size:
        return False
    else:
        return True


def load_and_create_summary(rawfiles, cellpyfile, mass):
    cell_data = cellreader.CellpyData()
    try:
        cell_data.loadcell(raw_files=rawfiles, cellpy_file=None, mass=mass)
        cell_data.make_summary()
        cell_data.save_test(cellpyfile)
    except:
        return None
    return cell_data.tests[0].dfsummary


# ------------defining the DataFrames and dicts we need---
number_of_rows = 50
cycle = range(1,number_of_rows+1)
cumcouldiff_df = pd.DataFrame({"cycle": range(1,number_of_rows+1)}).set_index("cycle")
couleff_df = pd.DataFrame({"cycle": range(1,number_of_rows+1)}).set_index("cycle")
summary_columns = ["srno","date","life","lived_to_end","ccd_1","ccd_5","ccd_10","ccd_20","ccd_50"]
summary_dict = collections.OrderedDict()
for k in summary_columns:
    summary_dict[k] = []

# -----------defining folders----------------------------
prms = prmreader.read() # TODO: remove this
db_path = prms.db_path
outdatadir = prms.outdatadir
filelogdir = prms.filelogdir
cellpydatadir = prms.cellpydatadir
rawdatadir = prms.rawdatadir

# -----------selecting runs------------------------------
excel_reader = dbreader.reader()
db_table = excel_reader.table
# db_table is a DataFrame where we can use ordinary pandas stuff to select
# the wanted srnos

# One option is to use the methods for filtering etc in the dbreader, or get all
# srnos = excel_reader.get_all()
srnos = excel_reader.select_batch("highCoul", 12)
# filter_cols = [6,9]
# srnos = excel_reader.filter_by_col(filter_cols)

for n in srnos:
    run_name = excel_reader.get_cell_name(n)
    mass = excel_reader.get_mass(n)
    print
    print 30 * "="
    print "(%i): %s" % (n, run_name)
    print 30 * "-"
    rawfiles, cellpyfile = filefinder.search_for_files(run_name)
    if check_files(rawfiles):
        dfsummary = load_and_create_summary(rawfiles, cellpyfile, mass)
        if dfsummary is None:
            print "No summary made (could be errors in the raw-file)"
        else:
            summary_dict["srno"].append(n)
            summary_dict["date"].append(dfsummary.loc[0,"Date_Time_Txt(str)"])
            life, to_max = get_lifetime(dfsummary)
            summary_dict["life"].append(life)
            summary_dict["lived_to_end"].append(to_max)
            for k, v in zip(["ccd_1", "ccd_5", "ccd_10", "ccd_20", "ccd_50"],
                            get_cum_coul_diff(dfsummary)):
                summary_dict[k].append(v)
            couleff = dfsummary.loc[dfsummary["Cycle_Index"] < 51,"Coulombic_Efficiency(percentage)"]
            couleff_df[n] = couleff
            cumcouldiff = dfsummary.loc[dfsummary["Cycle_Index"] < 51, "Cumulated_Coulombic_Difference(mAh/g)"]
            cumcouldiff_df[n] = cumcouldiff
    print 30 * "="
    print

# Saving data
summary_df = pd.DataFrame(summary_dict)
summary_df = summary_df.set_index("srno")
cumcouldiff_df.to_csv(os.path.join(outdatadir,"cumcouldiff.csv"), sep=";")
couleff_df.to_csv(os.path.join(outdatadir,"couldeff.csv"), sep=";")
summary_df.to_csv(os.path.join(outdatadir,"summary.csv"), sep=";")


