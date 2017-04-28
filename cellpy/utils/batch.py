"""Routines for batch processing of cells.

typical usage:

from cellpy.utils import batch

# initialization of the batch class
b = batch.init()

# giving necessary info
b.name = "experiment_set_01"
b.project = "new_exiting_chemistry"
 
# doing the stuff
b.loadnsave()
b.report()
b.summaryplot()

"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import warnings
import logging
import pandas as pd
import itertools
import time
import csv
import json

from cellpy.parameters import prms as prms
from cellpy import cellreader, dbreader, filefinder
logger = logging.getLogger(__name__)

logging.captureWarnings(True)


def create_selected_summaries_dict(summaries_list):
    """Creates a dictionary with summary column headers.
    
    Examples:
        >>> summaries_to_output = ["discharge_capacity", "charge_capacity"]
        >>> summaries_to_output_dict = create_selected_summaries_dict(summaries_to_output)
        >>> print(summaries_to_output_dict)
        {'discharge_capacity': "Discharge_Capacity(mAh/g)",
               'charge_capacity': "Charge_Capacity(mAh/g)}
         
    Args:
        summaries_list: list containing cellpy summary column id names

    Returns: dictionary of the form {cellpy id name: cellpy summary header name,}

    """
    headers_summary = cellreader.get_headers_summary()
    selected_summaries = dict()  # this should be sent as input
    for h in summaries_list:
        selected_summaries[h] = headers_summary[h]
    return selected_summaries


class Batch(object):
    """The Batch object"""

    def __init__(self, *args, **kwargs):

        self.name = None
        if len(args)>0:
            self.name = args[0]

        self.project = None
        if len(args)>1:
            self.project = args[1]


        self.time_stamp = None
        self.selected_summaries = ["discharge_capacity", "charge_capacity", "coulombic_efficiency",
                                   "cumulated_coulombic_efficiency",
                                   "ir_discharge", "ir_charge",
                                   "end_voltage_discharge", "end_voltage_charge"]

        self.output_format = None
        self.batch_col = 5

        self.info_file = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None
        self.info_file = None

        self.reader = None
        self.info_df = None
        self.summaries = None
        self.stats = None
        self.frames = None
        self.keys = None

        self.export_raw = True
        self.export_cycles = False
        self.export_ica = False
        self.save_cellpy_file = True
        self.force_raw_file = False

        self._is_ready_for_plotting = False
        self._is_ready_for_loading = False
        self._is_ready_for_saving = False

        self._packable = ['name', 'project', 'batch_col','selected_summaries',
                          'output_format', 'time_stamp', 'project_dir', 'batch_dir', 'raw_dir']

        # Not afraid to walk down un-known territory...
        self._kwargs = kwargs
        self._set_attributes()


        # Just to keep track of the parameters (delete this):
        for key in prms.Paths:
            logger.info("Starting parameters:")
            txt = "%s: %s" % (key, str(prms.Paths[key]))
            logger.info(txt)

        # Time to get to work...
        self._set_reader()


    def __str__(self):
        txt0 = "<Cellpy.Utils.Batch instance in %s>:" % __name__
        # How to kill a class: write "print(self)" in its __str__ method ;-)
        txt1 = len(txt0)*"-"
        txt = txt0 + "\n" + txt1 + "\n"
        for attr in vars(self):
            if not attr.startswith("_"):
                if attr == "info_df":
                    if self.info_df is None:
                        txt += "%s: %s\n" % (str(attr), "None")
                    else:
                        txt += "%s: %s\n" % (str(attr), "pandas.DataFrame")
                else:
                    txt += "%s: %s\n" % (str(attr), str(getattr(self, attr)))
        return txt


    def _prm_packer(self, metadata=None):

        packable = self._packable
        if metadata is None:
            _metadata = dict()
            for p in packable:
                _metadata[p] = getattr(self, p)
            return _metadata

        else:
            for p in metadata:
                setattr(self, p, metadata[p])


    def _set_attributes(self, attrs=None):
        # Just for fun...
        if attrs is None:
            attrs = self._kwargs
        for key in attrs:
            if key.startswith("_"):
                w_txt = "Cannot set attribute starting with '_' ('Not allowed', says the King)"
                warnings.warn(w_txt)

            if hasattr(self, key):
                setattr(self,key, self._kwargs[key])
            else:
                w_txt = "Trying to set non-existing attribute (%s)" % key
                warnings.warn(w_txt)

    def _set_reader(self):
        # look into the prms and find out what to use for reading the database
        reader_label = prms.Db["db_type"]
        self.reader = get_db_reader(reader_label)


    def create_info_df(self):
        """Creates a DataFrame with info about the runs (loaded from the DB)"""
        logger.debug("running create_info_df")
        # initializing the reader
        reader = self.reader()
        self.info_df = make_df_from_batch(self.name, batch_col=self.batch_col, reader=reader)
        logger.info(str(self.info_df.head(5)))


    def save_info_df(self):
        """Saves the DataFrame with info about the runs to a JSON file"""
        logger.debug("running save_info_df")

        info_df = self.info_df
        top_level_dict = {}
        top_level_dict['info_df'] = info_df

        # packing prms
        top_level_dict['metadata'] = self._prm_packer()

        jason_string = json.dumps(top_level_dict, default=lambda info_df: json.loads(info_df.to_json()))
        with open(self.info_file, 'w') as outfile:
            outfile.write(jason_string)


    def load_info_df(self, file_name=None):
        """Loads a DataFrame with all the needed info about the run (JSON file)"""
        if file_name is None:
            file_name = self.info_file

        with open(file_name, 'r') as infile:
            top_level_dict = json.load(infile)

        new_info_df_dict = top_level_dict['info_df']
        new_info_df = pd.DataFrame(new_info_df_dict)
        self.info_df = new_info_df

        self._prm_packer(top_level_dict['metadata'])
        self.info_file = file_name


    def create_folder_structure(self):
        self.info_file, directories = create_folder_structure(self.project, self.name)
        self.project_dir, self.batch_dir, self.raw_dir = directories

    def load_and_save_raw(self):
        sep = prms.Reader["sep"]
        self.frames, self.keys, errors = read_and_save_data(self.info_df, self.raw_dir, sep=sep,
                                                    force_raw=self.force_raw_file,
                                                    export_cycles=self.export_cycles,
                                                    export_raw=self.export_raw,
                                                    export_ica=self.export_ica,
                                                    save=self.save_cellpy_file)


    def make_summaries(self):
        save_summaries(self.frames, self.keys, self.selected_summaries, self.batch_dir, self.name)


    def make_stats(self):
        pass

    def make_figures(self):
        pass



def get_db_reader(db_type):
    """returns the db_reader.
    
    Args:
        db_type: type of db_reader (string) in ('simple_excel_reader', )

    Returns: db_reader (function)

    """
    if db_type == "simple_excel_reader":
        return dbreader.reader


def make_df_from_batch(batch_name, batch_col=5, reader=None, reader_label=None):
    batch_name = batch_name
    batch_col = batch_col
    if reader is None:
        reader_obj = get_db_reader(reader_label)
        reader = reader_obj()

    srnos = reader.select_batch(batch_name, batch_col)
    info_dict = _create_info_dict(reader, srnos)
    info_df = pd.DataFrame(info_dict)
    info_df = info_df.sort_values(["groups", "filenames"])
    info_df = _make_unique_groups(info_df)
    info_df["labels"] = info_df["filenames"].apply(create_labels)
    info_df.set_index("filenames", inplace=True)

    return info_df


def _create_info_dict(reader, srnos):
    info_dict = dict()
    info_dict["filenames"] = [reader.get_cell_name(srno) for srno in srnos]
    info_dict["masses"] = [reader.get_mass(srno) for srno in srnos]
    info_dict["total_masses"] = [reader.get_total_mass(srno) for srno in srnos]
    info_dict["loadings"] = [reader.get_loading(srno) for srno in srnos]
    info_dict["fixed"] = [reader.inspect_hd5f_fixed(srno) for srno in srnos]
    info_dict["labels"] = [reader.get_label(srno) for srno in srnos]
    info_dict["cell_type"] = ["anode" for srno in srnos]

    info_dict["raw_file_names"] = []
    info_dict["cellpy_file_names"] = []

    _groups = [reader.get_group(srno) for srno in srnos]
    groups = _fix_groups(_groups)
    info_dict["groups"] = groups

    my_timer_start = time.time()
    info_dict = _find_files(info_dict)
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logger.info("The function _find_files was very slow. Save your info_df so you don't have to run it again!")

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


def create_folder_structure(project_name, batch_name):
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
    return (info_file, (project_dir, batch_dir, raw_dir))



def save_multi(data, file_name, sep=";"):
    with open(file_name, "wb") as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(itertools.izip_longest(*data))



def read_and_save_data(info_df, raw_dir, sep=";", force_raw=False,
                       export_cycles=False, export_raw=True,
                       export_ica=False, save=True):
    """Reads and saves cell data defined by the info-DataFrame.
    
    Args:
        info_df: pandas.DataFrame with information about the runs.
        raw_dir: path to location where you want to save raw data.
        sep: delimiter to use when exporting to csv.
        force_raw: load raw data even-though cellpy-file is up-to-data.
        export_cycles: set to True for exporting cycles to csv.
        export_raw: set to True for exporting raw data to csv.
        export_ica: set to True for calculating and exporting dQ/dV to csv.
        save: set to False to prevent saving a cellpy-file.

    Returns: frames and keys.
    """

    no_export = False
    do_export_dqdv = export_ica
    keys = []
    frames = []
    number_of_runs = len(info_df)
    counter = 0
    errors = []
    for indx, row in info_df.iterrows():
        counter += 1
        h_txt = "[" + counter*"|" + (number_of_runs-counter)*"." + "]"
        l_txt = "starting to process file # %i (index=%s)" % (counter, indx)
        logger.debug(l_txt)
        print(h_txt)
        # here we should print (or write to log) file n of N (e.g. [3/12] or [|||       ])
        if not row.raw_file_names:
            print("File not found!")
            print(indx)
            logger.debug("File(s) not found for index=%s" % indx)
            errors.append(indx)
            continue

        print("Processing (%s)..." % indx)
        logger.debug("Processing (%s)..." % indx)
        cell_data = cellreader.cellpydata()
        logger.debug("setting cycle mode (%s)..." % row.cell_type)
        cell_data.set_cycle_mode(row.cell_type)
        logger.debug("loading cell")
        try:
            cell_data.loadcell(raw_files=row.raw_file_names, cellpy_file=row.cellpy_file_names,
                               mass=row.masses, summary_on_raw=True,
                               force_raw=force_raw)
        except Exception as e:
            logger.debug('Failed to load: '+ str(e))
            errors.append("loadcell:" +str(indx))
            continue

        if not cell_data.check():
            print("...not loaded...")
            logger.debug("Did not pass check(). Could not load cell!")
            errors.append("check:" +str(indx))
            continue

        print("...loaded successfully...")
        keys.append(indx)

        summary_tmp = cell_data.get_summary()
        summary_tmp.set_index("Cycle_Index", inplace=True)
        frames.append(summary_tmp)
        if save:
            if not row.fixed:
                logger.info("saving cell to %s" % row.cellpy_file_names)
                cell_data.save_test(row.cellpy_file_names)
            else:
                logger.debug("saving cell skipped (set to 'fixed' in info_df)")

        if no_export:
            continue

        if export_raw:
            print("...exporting data....")
            logger.debug("Exporting csv")
            cell_data.exportcsv(raw_dir, sep=sep, cycles=export_cycles, raw=export_raw)

        if do_export_dqdv:
            logger.debug("Exporting dqdv")
            try:
                export_dqdv(cell_data, savedir=raw_dir, sep=sep)
            except Exception as e:
                print("...could not make/export dq/dv data...")
                logger.debug("Failed to make/export dq/dv data (%s): %s" % (indx, str(e)))
                errors.append("ica:" + str(indx))
    return frames, keys, errors


def save_summaries(frames, keys, selected_summaries, batch_dir, batch_name):
    """writes the summaries to csv-files"""
    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    summary_df = pd.concat(frames, keys=keys, axis=1)
    # saving the selected summaries
    for key, value in selected_summaries_dict.iteritems():
        _summary_file_name = os.path.join(batch_dir, "summary_%s_%s.csv" % (key, batch_name))
        _summary_df = summary_df.iloc[:, summary_df.columns.get_level_values(1) == value]
        # include function to tweak headers here (need to learn MultiIndex)
        _header = _summary_df.columns
        _summary_df.to_csv(_summary_file_name, sep=";")
        logger.info("saved summary (%s) to %s" % (key, _summary_file_name))
    logger.info("finished saving summaries")

#----------------------


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


def extract_dqdv(cell_data, extract_func):
    from cellpy.utils.ica import dqdv
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


# -----------------------------------------------------------------------------

def init(*args, **kwargs):
    """Returns an initialized instance of the Batch class"""
    b = Batch(*args, **kwargs)
    return b


def main():
    print("Running batch.py")
    b = init("bec_exp06", "SiBEC", reader="excel", me="Jan Petter")
    b.create_info_df()
    b.create_folder_structure()
    b.save_info_df()
    b.load_info_df(r"C:\Scripting\Processing\Celldata\outdata\SiBEC\cellpy_batch_bec_exp06.json")
    print(b)
    print("The info DataFrame:")
    print(b.info_df.head(5))
    b.load_and_save_raw()
    b.make_summaries()
    print("Finished!")



if __name__ == '__main__':
    main()

