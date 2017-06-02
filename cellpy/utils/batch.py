"""Routines for batch processing of cells."""

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
import matplotlib.pyplot as plt
import matplotlib as mpl

from cellpy.parameters import prms as prms
from cellpy import cellreader, dbreader, filefinder
logger = logging.getLogger(__name__)

logging.captureWarnings(True)

DEFAULT_PLOT_STYLE = {"markersize": prms.Batch["markersize"]}

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
    """The Batch object
    
    The Batch class is a utility class for pipe-lining batch processing of cell cycle data.
    It is primarily designed for use in `jupyter notebooks`. The typical usage structure is:
    
    1. Import the batch module (this also gives you access to the cellpy parameters (`batch.prms`)
    
    >>> from cellpy.utils import batch
    
    2. Initialization of the batch class
    
    >>> b = batch.init()
    >>> # you can also give the name of the batch, the project name, the log-level, and the batch column number
    >>> # as parameters to the batch.init function, e.g.
    >>> # b = batch.init("batch_name", "project_name", default_log_level="INFO", batch_col=5)
    
    3. Set parameters for your experiment
    
    >>> b.name = "experiment_set_01"
    >>> b.project = "new_exiting_chemistry"
    >>> 
    >>> # set additional parameters if the defaults are not ok:
    >>> 
    >>> b.export_raw = True
    >>> b.export_cycles = True
    >>> b.export_ica = True
    >>> b.save_cellpy_file = True
    >>> b.force_raw_file = False
    >>> b.force_cellpy_file = True
     
    4. The next step is to extract and collect the information needed from your data-base into a DataFrame, and create
       an appropriate folder structure (outdir/project_name/batch_name/raw_data)
    
    >>> b.create_info_df()
    >>> 
    >>> # or load it from a previous run:
    >>> # filename = "../out_data/experiment_set_01/cellpy_batch_new_exiting_chemistry.json"
    >>> # b.load_info_df(filename)
    >>> 
    >>> b.create_folder_structure()
    >>> 
    >>> # You can view your information DataFrame by the pandas head function:
    >>> 
    >>> b.info_df.head()
    
    5. To run the processing, you can use the convenience function `load_and_save_raw'. This function
       loads all your data-files and saves csv-files of the results.
    
    >>> b.load_and_save_raw()
    
    6. Create some summary csv-files (e.g. containing charge capacities vs. cycle number for all your data-files).
    
    >>> b.make_summaries()
    
    7. Plot
    
    >>> b.plot_summaries()
    
    8. Create some statistics
    
    >>> b.make_stats()
    ... Sorry, but I have not implemented this yet...
    
    9. Report
    
    >>> b.report()
    ... Sorry, reporting is not implemented yet :-(
    
    """

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

        self.symbol_label = prms.Batch["symbol_label"]
        self.color_style_label = prms.Batch["color_style_label"]

        self.info_file = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None
        self.info_file = None

        self.reader = None
        self.info_df = None
        self.summaries = None
        self.summary_df = None
        self.stats = None
        self.frames = None
        self.keys = None

        self.figure = dict()
        self.axes = dict()

        self.export_raw = True
        self.export_cycles = False
        self.export_ica = False
        self.save_cellpy_file = True
        self.force_raw_file = False
        self.force_cellpy_file = False


        self._packable = ['name', 'project', 'batch_col','selected_summaries',
                          'output_format', 'time_stamp', 'project_dir', 'batch_dir', 'raw_dir']

        # Not afraid to walk down un-known territory...
        self._kwargs = kwargs
        self._set_attributes()

        # Just to keep track of the parameters (delete this):
        for key in prms.Paths:
            logger.debug("Starting parameters:")
            txt = "%s: %s" % (key, str(prms.Paths[key]))
            logger.debug(txt)

        # These 'exist-attrs' are not used yet:
        self._info_df_exists = False
        self._folder_structure_exists = False
        self._data_exists = False

        # Time to get to work...
        logger.debug("created Batch class")
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
                warnings.warn("Trying to set non-existing attribute (%s)" % key)

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
        logger.debug(str(self.info_df.head(5)))


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
        logger.debug("loaded info_df")
        logger.debug(" info_file: %s" % self.info_file)

    def create_folder_structure(self):
        """Creates a folder structure based on the project and batch name.
        
        Project - Batch-name - Raw-data-dir

        The info_df json-file will be stored in the Project folder.
        The summary-files will be saved in the Batch-name folder.
        The raw data (including exported cycles and ica-data) will be saved to the Raw-data-dir.
        
        """
        self.info_file, directories = create_folder_structure(self.project, self.name)
        self.project_dir, self.batch_dir, self.raw_dir = directories
        logger.debug("create folders:" + str(directories))

    def load_and_save_raw(self):
        """Loads the cellpy or raw-data file(s) and saves to csv"""
        sep = prms.Reader["sep"]
        self.frames, self.keys, errors = read_and_save_data(self.info_df, self.raw_dir, sep=sep,
                                                    force_raw=self.force_raw_file,
                                                    force_cellpy=self.force_cellpy_file,
                                                    export_cycles=self.export_cycles,
                                                    export_raw=self.export_raw,
                                                    export_ica=self.export_ica,
                                                    save=self.save_cellpy_file)
        logger.debug("loaded and saved data. errors:" + str(errors))

    def make_summaries(self):
        """Make and save summary csv files, each containing values from all cells"""
        self.summary_df = save_summaries(self.frames, self.keys, self.selected_summaries, self.batch_dir, self.name)
        logger.debug("made and saved summaries")

    def make_stats(self):
        """Not implemented yet"""
        pass

    def _create_colors_markers_list(self):
        import cellpy.utils.plotutils as plot_utils
        return plot_utils.create_colormarkerlist_for_info_df(self.info_df, symbol_label=self.symbol_label,
                                                             color_style_label=self.color_style_label)
    def plot_summaries(self, show=False, save=True):
        color_list, symbol_list = self._create_colors_markers_list()
        summary_df = self.summary_df
        selected_summaries = self.selected_summaries
        batch_dir = self.batch_dir
        batch_name = self.name
        fig, ax = plot_summary_figure(self.info_df, summary_df, color_list, symbol_list, selected_summaries,
                                      batch_dir, batch_name, show=show, save=save)
        self.figure["summaries"] = fig
        self.axes["summaries"] = ax

def get_db_reader(db_type):
    """returns the db_reader.
    
    Args:
        db_type: type of db_reader (string) in ('simple_excel_reader', )

    Returns: db_reader (function)

    """
    if db_type == "simple_excel_reader":
        return dbreader.reader


def make_df_from_batch(batch_name, batch_col=5, reader=None, reader_label=None):
    """
    
    Args:
        batch_name (str): Name of the batch.
        batch_col (int): The column number where the batch name is in the db.
        reader (method): the db-loader method.
        reader_label (str): the label for the db-loader (if db-loader method is not given)

    Returns: info_df (pandas DataFrame)

    """
    batch_name = batch_name
    batch_col = batch_col
    logger.debug("batch_name, batch_col: (%s,%i)" % (batch_name, batch_col))
    if reader is None:
        reader_obj = get_db_reader(reader_label)
        reader = reader_obj()

    srnos = reader.select_batch(batch_name, batch_col)
    logger.debug("srnos:" + str(srnos))
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
    for key in info_dict.keys():
        logger.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logger.debug("groups: %s" % str(_groups))
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



def read_and_save_data(info_df, raw_dir, sep=";", force_raw=False, force_cellpy=False,
                       export_cycles=False, export_raw=True,
                       export_ica=False, save=True):
    """Reads and saves cell data defined by the info-DataFrame.
    
    Args:
        info_df: pandas.DataFrame with information about the runs.
        raw_dir: path to location where you want to save raw data.
        sep: delimiter to use when exporting to csv.
        force_raw: load raw data even-though cellpy-file is up-to-date.
        force_cellpy: load cellpy files even-though cellpy-file is not up-to-date.
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
        if not row.raw_file_names and not force_cellpy:
            print("File not found!")
            print(indx)
            logger.debug("File(s) not found for index=%s" % indx)
            errors.append(indx)
            continue

        print("Processing (%s)..." % indx)
        logger.debug("Processing (%s)..." % indx)
        cell_data = cellreader.CellpyData()
        if not force_cellpy:
            logger.debug("setting cycle mode (%s)..." % row.cell_type)
            cell_data.set_cycle_mode(row.cell_type)

        logger.debug("loading cell")
        if not force_cellpy:
            try:
                cell_data.loadcell(raw_files=row.raw_file_names, cellpy_file=row.cellpy_file_names,
                                   mass=row.masses, summary_on_raw=True,
                                   force_raw=force_raw)
            except Exception as e:
                logger.debug('Failed to load: '+ str(e))
                errors.append("loadcell:" +str(indx))
                continue
        else:
            try:
                cell_data.load(row.cellpy_file_names)
            except Exception as e:
                logger.debug('Failed to load: '+ str(e))
                errors.append("load:" +str(indx))
                continue


        if not cell_data.check():
            print("...not loaded...")
            logger.debug("Did not pass check(). Could not load cell!")
            errors.append("check:" +str(indx))
            continue

        print("...loaded successfully...")
        keys.append(indx)

        summary_tmp = cell_data.get_summary()
        logger.info("Trying to get summary_data")
        if summary_tmp is None:
            logger.info("No existing summary made - running make_summary")
            cell_data.make_summary(find_end_voltage=True, find_ir=True)

        if not summary_tmp.index.name == "Cycle_Index":
            logger.debug("Setting index to Cycle_Index")
            summary_tmp.set_index("Cycle_Index", inplace=True)
        frames.append(summary_tmp)

        if save:
            if not row.fixed:
                logger.info("saving cell to %s" % row.cellpy_file_names)
                cell_data.save(row.cellpy_file_names)
            else:
                logger.debug("saving cell skipped (set to 'fixed' in info_df)")

        if no_export:
            continue

        if export_raw:
            print("...exporting data....")
            logger.debug("Exporting csv")
            cell_data.to_csv(raw_dir, sep=sep, cycles=export_cycles, raw=export_raw)

        if do_export_dqdv:
            logger.debug("Exporting dqdv")
            try:
                export_dqdv(cell_data, savedir=raw_dir, sep=sep)
            except Exception as e:
                print("...could not make/export dq/dv data...")
                logger.debug("Failed to make/export dq/dv data (%s): %s" % (indx, str(e)))
                errors.append("ica:" + str(indx))
    if len(errors) > 0:
        print("Finished with errors!")
        print(errors)
    else:
        print("Finished")

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
        logger.info("saved summary (%s) to:\n       %s" % (key, _summary_file_name))
    logger.info("finished saving summaries")
    return summary_df


def pick_summary_data(key, summary_df, selected_summaries):
    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    value = selected_summaries_dict[key]
    return summary_df.iloc[:, summary_df.columns.get_level_values(1)==value]


def plot_summary_data(ax, df, info_df, color_list, symbol_list, is_charge=False, plot_style=None):

    logger.debug("trying to plot summary data")
    if plot_style is None:
        logger.debug("no plot_style given, using default")
        plot_style = DEFAULT_PLOT_STYLE
    else:
        logger.debug("plot_style given")

    list_of_lines = list()

    for datacol in df.columns:
        group = info_df.get_value(datacol[0], "groups")
        sub_group = info_df.get_value(datacol[0], "sub_groups")
        color = color_list[group - 1]
        marker = symbol_list[sub_group - 1]
        plot_style["marker"] = marker
        plot_style["markeredgecolor"] = color
        plot_style["color"] = color
        plot_style["markerfacecolor"] = 'none'
        logger.debug("selecting color for group: " + str(color))

        if not is_charge:
            plot_style["markerfacecolor"] = color
        lines = ax.plot(df[datacol], **plot_style)
        list_of_lines.extend(lines)

    return list_of_lines, plot_style


def plot_summary_figure(info_df, summary_df, color_list, symbol_list, selected_summaries,
                        batch_dir, batch_name, plot_style=None, show=False, save=True):
    # Not finished yet



    standard_fig, (ce_ax, cap_ax, ir_ax) = plt.subplots(nrows=3, ncols=1, sharex=True)  # , figsize = (5,4))

    # pick data
    ce_df = pick_summary_data("coulombic_efficiency", summary_df, selected_summaries)
    cc_df = pick_summary_data("charge_capacity", summary_df, selected_summaries)
    dc_df = pick_summary_data("discharge_capacity", summary_df, selected_summaries)
    irc_df = pick_summary_data("ir_charge", summary_df, selected_summaries)
    ird_df = pick_summary_data("ir_discharge", summary_df, selected_summaries)

    # generate labels
    ce_labels = [info_df.get_value(filename, "labels") for filename in ce_df.columns.get_level_values(0)]

    # adding charge/discharge label
    ce_labels.extend(["", "discharge", "charge"])

    # plot ce
    list_of_lines, plot_style = plot_summary_data(ce_ax, ce_df, info_df=info_df, color_list=color_list,
                                                  symbol_list=symbol_list, is_charge=False, plot_style=plot_style)

    # adding charge/discharge label
    color = plot_style["color"]
    markersize = plot_style["markersize"]

    open_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                  markeredgecolor=color, markerfacecolor='none',
                                  markersize=markersize)
    closed_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                    markeredgecolor=color, markerfacecolor=color,
                                    markersize=markersize)
    no_label = mpl.lines.Line2D([], [], color='none', marker='s', markersize=0)
    list_of_lines.extend([no_label, closed_label, open_label])

    ce_ax.set_ylabel("Coulombic\nefficiency\n(%)")
    ce_ax.locator_params(nbins=5)

    plot_summary_data(cap_ax, cc_df, is_charge=True, info_df=info_df, color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)
    plot_summary_data(cap_ax, dc_df, is_charge=False, info_df=info_df, color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)
    cap_ax.set_ylabel("Capacity\n(mAh/g)")
    cap_ax.locator_params(nbins=4)

    plot_summary_data(ir_ax, irc_df, is_charge=True, info_df=info_df, color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)
    plot_summary_data(ir_ax, ird_df, is_charge=False, info_df=info_df, color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)

    ir_ax.set_ylabel("Internal\nresistance\n(Ohms)")
    ir_ax.set_xlabel("Cycle number")
    ir_ax.locator_params(axis="y", nbins=4)
    ir_ax.locator_params(axis="x", nbins=10)
    # should use MaxNLocator here instead

    # tweaking
    plt.subplots_adjust(left=0.07, right=0.93, top=0.9, wspace=0.25, hspace=0.15)

    # adding legend
    logger.debug("trying to add legends " + str(ce_labels))
    standard_fig.legend(handles=list_of_lines, labels=ce_labels,
                        bbox_to_anchor=(1.02, 1.1), loc=2,
                        # bbox_transform=plt.gcf().transFigure,
                        bbox_transform=ce_ax.transAxes,
                        numpoints=1,
                        ncol=1, labelspacing=0.,
                        prop={"size": 10})

    # plt.tight_layout()
    if save:
        extension = prms.Batch["fig_extension"]
        dpi = prms.Batch["dpi"]
        figure_file_name = os.path.join(batch_dir, "summaryplot_1_%s.%s" % (batch_name, extension))
        standard_fig.savefig(figure_file_name, dpi=dpi, bbox_inches='tight')
    if show:
        plt.show()
    return standard_fig, (ce_ax, cap_ax, ir_ax)

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

    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)

    import cellpy.log as log
    log.setup_logging(custom_log_dir=prms.Paths["filelogdir"],
                      default_level=default_log_level)
    b = Batch(*args, **kwargs)
    return b


def main():
    print("Running batch.py")
    b = init("bec_exp06", "SiBEC", default_log_level="DEBUG", reader="excel", me="Jan Petter")
    # b.create_info_df()
    # b.create_folder_structure()
    # b.save_info_df()
    # b.load_info_df(r"C:\Scripting\Processing\Celldata\outdata\SiBEC\cellpy_batch_bec_exp06.json")
    # print(b)
    # print("The info DataFrame:")
    # print(b.info_df.head(5))
    # b.load_and_save_raw()
    # b.make_summaries()
    # print("Finished!")



if __name__ == '__main__':
    main()

