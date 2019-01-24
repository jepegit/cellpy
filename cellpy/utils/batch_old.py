"""Routines for batch processing of cells."""

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

import cellpy.parameters.internal_settings
from cellpy import prms
from cellpy import cellreader, filefinder
from cellpy.readers import dbreader
from cellpy.exceptions import ExportFailed, NullData

logger = logging.getLogger(__name__)

logging.captureWarnings(True)

DEFAULT_PLOT_STYLE = {"markersize": prms.Batch["markersize"]}

warnings.warn("will be removed shortly", DeprecationWarning)


class FigureType(object):
    """Object for storing figure type definitions.

    Creates and FigureType instance with information on number of subplots
    (rows and columns), and selectors for showing charge and discharge as list
    of booleans.

    """

    def __init__(self, number_of_rows=1, number_of_cols=1,
                 capacity_selector=None, ir_selector=None,
                 end_voltage_selector=None,
                 axes=None):
        self.number_of_rows_and_cols = (number_of_rows, number_of_cols)

        self.capacity_selector = capacity_selector
        if self.capacity_selector is None:
            self.capacity_selector = [True, True]

        self.ir_selector = ir_selector
        if self.ir_selector is None:
            self.ir_selector = [True, True]

        self.end_voltage_selector = end_voltage_selector
        if self.end_voltage_selector is None:
            self.end_voltage_selector = [True, True]

        self.axes = axes
        if self.axes is None:
            self.axes = {"ce_ax": 0}

    @property
    def rows(self):
        return self.number_of_rows_and_cols[0]

    @property
    def columns(self):
        return self.number_of_rows_and_cols[-1]

    def retrieve_axis(self, ax_label, ax):
        if ax_label in list(self.axes.keys()):
            return ax[self.axes[ax_label]]
        else:
            return None

            # if figure_type == "summaries":
            #     ce_ax, cap_ax, ir_ax = ax
            #     ev_ax = None
            # elif figure_type == "experimental":
            #     ce_ax, cap_ax, ev_ax, ir_ax = ax
            # else:
            #     ce_ax, cap_ax, ir_ax = ax
            #     ev_ax = None


figure_types = dict()
figure_types["summaries"] = FigureType(3, 1, [True, True], [True, True],
                                       [True, True],
                                       {"ce_ax": 0, "cap_ax": 1,
                                        "ir_ax": 2, }, )
figure_types["unlimited"] = FigureType(3, 1, [True, True], [True, True],
                                       [True, True],
                                       {"ce_ax": 0, "cap_ax": 1,
                                        "ir_ax": 2, }, )
figure_types["charge_limited"] = FigureType(4, 1, [True, True], [True, False],
                                            [False, True],
                                            {"ce_ax": 0, "cap_ax": 1,
                                             "ev_ax": 2, "ir_ax": 3, }, )
figure_types["discharge_limited"] = FigureType(4, 1, [True, True],
                                               [False, True], [True, False],
                                               {"ce_ax": 0, "cap_ax": 1,
                                                "ev_ax": 2, "ir_ax": 3, }, )


def _create_info_dict(reader, srnos):
    # reads from the db and populates a dictionary
    cell_type = prms.Reader["cycle_mode"]
    info_dict = dict()
    info_dict["filenames"] = [reader.get_cell_name(srno) for srno in srnos]
    info_dict["masses"] = [reader.get_mass(srno) for srno in srnos]
    info_dict["total_masses"] = [reader.get_total_mass(srno) for srno in srnos]
    info_dict["loadings"] = [reader.get_loading(srno) for srno in srnos]
    info_dict["fixed"] = [reader.inspect_hd5f_fixed(srno) for srno in srnos]
    info_dict["labels"] = [reader.get_label(srno) for srno in srnos]
    info_dict["cell_type"] = [cell_type for srno in srnos]
    info_dict["raw_file_names"] = []
    info_dict["cellpy_file_names"] = []
    for key in list(info_dict.keys()):
        logger.debug("%s: %s" % (key, str(info_dict[key])))

    _groups = [reader.get_group(srno) for srno in srnos]
    logger.debug("groups: %s" % str(_groups))
    groups = _fix_groups(_groups)
    info_dict["groups"] = groups

    my_timer_start = time.time()
    filename_cache = []
    info_dict = _find_files(info_dict, filename_cache)
    my_timer_end = time.time()
    if (my_timer_end - my_timer_start) > 5.0:
        logger.info(
            "The function _find_files was very slow. "
            "Save your info_df so you don't have to run it again!"
        )

    return info_dict


def _find_files(info_dict, filename_cache=None):
    # searches for the raw data files and the cellpyfile-name
    for run_name in info_dict["filenames"]:
        if prms._use_filename_cache:
            raw_files, cellpyfile, filename_cache = filefinder.search_for_files(run_name, cache=filename_cache)
        else:
            raw_files, cellpyfile = filefinder.search_for_files(run_name)
        if not raw_files:
            raw_files = None
        info_dict["raw_file_names"].append(raw_files)
        info_dict["cellpy_file_names"].append(cellpyfile)

    return info_dict


def _save_multi(data, file_name, sep=";"):
    """convenience function for storing data column-wise in a csv-file."""
    logger.debug("saving multi")
    with open(file_name, "w", newline='') as f:
        logger.debug(f"{file_name} opened")
        writer = csv.writer(f, delimiter=sep)
        try:
            writer.writerows(itertools.zip_longest(*data))
        except Exception as e:
            logger.info(f"Exception encountered in batch._save_multi: {e}")
            raise ExportFailed
        logger.debug("wrote rows using itertools in _save_multi")


def _make_unique_groups(info_df):
    # fixes group numbering
    unique_g = info_df.groups.unique()
    unique_g = sorted(unique_g)
    new_unique_g = list(range(len(unique_g)))
    info_df["sub_groups"] = info_df["groups"] * 0
    for i, j in zip(unique_g, new_unique_g):
        counter = 1
        for indx, row in info_df.loc[info_df.groups == i].iterrows():
            info_df.at[indx, "sub_groups"] = counter
            # info_df.set_value(indx, "sub_groups", counter)
            counter += 1
        info_df.loc[info_df.groups == i, 'groups'] = j + 1
    return info_df


def _remove_date(label):
    _ = label.split("_")
    return _[1] + "_" + _[2]


def _fix_groups(groups):
    _groups = []
    for g in groups:
        if not float(g) > 0:
            _groups.append(1000)
        else:
            _groups.append(int(g))
    return _groups


def _extract_dqdv(cell_data, extract_func, last_cycle):
    """Simple wrapper around the cellpy.utils.ica.dqdv function."""

    from cellpy.utils.ica import dqdv
    list_of_cycles = cell_data.get_cycle_numbers()
    if last_cycle is not None:
        list_of_cycles = [c for c in list_of_cycles if c <= int(last_cycle)]
        logger.debug(f"only processing up to cycle {last_cycle}")
        logger.debug(f"you have {len(list_of_cycles)} cycles to process")
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
            logger.info(" Ups! Could not process this (cycle %i)" % cycle)
            logger.info(" %s" % e)

        header_x = "dQ cycle_no %i" % cycle
        header_y = "voltage cycle_no %i" % cycle
        dq.insert(0, header_x)
        v.insert(0, header_y)

        out_data.append(v)
        out_data.append(dq)
    return out_data


class Batch(object):
    """The Batch object

    The Batch class is a utility class for pipe-lining batch processing of cell
    cycle data. It is primarily designed for use in `jupyter notebooks`.
    The typical usage structure is:

    1. Import the batch module (this also gives you access to the cellpy
        parameters (`batch.prms`)

    >>> from cellpy.utils import batch

    2. Initialization of the batch class

    >>> b = batch.init()
    >>> # you can also give the name of the batch, the project name,
    >>> # the log-level, and the batch column number
    >>> # as parameters to the batch.init function, e.g.
    >>> # b = batch.init("batch_name", "project_name",
    >>> # default_log_level="INFO", batch_col="b01")

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

    4. The next step is to extract and collect the information needed from your
       data-base into a DataFrame, and create an appropriate folder structure
       (outdir/project_name/batch_name/raw_data)

    >>> b.create_info_df()
    >>>
    >>> # or load it from a previous run:
    >>> # filename = "../out_data/experiment_set_01/cellpy_batch" +
    >>> #   "_new_exiting_chemistry.json"
    >>> # b.load_info_df(filename)
    >>>
    >>> b.create_folder_structure()
    >>>
    >>> # You can view your information DataFrame by the pandas head function:
    >>>
    >>> b.info_df.head()

    5. To run the processing, you can use the convenience function
        `load_and_save_raw`. This function
        loads all your data-files and saves csv-files of the results.

    >>> b.load_and_save_raw()

    6. Create some summary csv-files (e.g. containing charge capacities vs.
        cycle number for all your data-files).

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
        if len(args) > 0:
            self.name = args[0]

        self.project = None
        if len(args) > 1:
            self.project = args[1]

        self.time_stamp = None
        self.default_figure_types = list(figure_types.keys())
        self.default_figure_type = prms.Batch["figure_type"]
        self.selected_summaries = ["discharge_capacity", "charge_capacity",
                                   "coulombic_efficiency",
                                   "cumulated_coulombic_efficiency",
                                   "ir_discharge", "ir_charge",
                                   "end_voltage_discharge",
                                   "end_voltage_charge",

                                   ]
        self.output_format = None
        self.batch_col = "b01"

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
        self.shifted_cycles = False
        self.export_ica = False
        self.save_cellpy_file = True
        self.force_raw_file = False
        self.force_cellpy_file = False
        self.use_cellpy_stat_file = None
        self.last_cycle = None

        self._packable = ['name', 'project', 'batch_col', 'selected_summaries',
                          'output_format', 'time_stamp', 'project_dir',
                          'batch_dir', 'raw_dir']

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
        txt1 = len(txt0) * "-"
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
                w_txt = "Cannot set attribute starting with '_' " \
                        "('Not allowed', says the King)"
                warnings.warn(w_txt)

            if hasattr(self, key):
                setattr(self, key, self._kwargs[key])
            else:
                warnings.warn("Trying to set non-existing attribute (%s)" % key)

    def _set_reader(self):
        # look into the prms and find out what to use for reading the database
        reader_label = prms.Db["db_type"]
        self.reader = get_db_reader(reader_label)

    def _create_colors_markers_list(self):
        from cellpy.utils import plotutils
        return plotutils.create_colormarkerlist_for_info_df(
            self.info_df,
            symbol_label=self.symbol_label,
            color_style_label=self.color_style_label
        )

    def create_info_df(self):
        """Creates a DataFrame with info about the runs (loaded from the DB)"""
        logger.debug("running create_info_df")
        # initializing the reader
        reader = self.reader()
        self.info_df = make_df_from_batch(self.name, batch_col=self.batch_col,
                                          reader=reader)
        logger.debug(str(self.info_df.head(5)))

    def save_info_df(self):
        """Saves the DataFrame with info about the runs to a JSON file"""
        logger.debug("running save_info_df")

        info_df = self.info_df
        top_level_dict = {'info_df': info_df, 'metadata': self._prm_packer()}

        # packing prms

        jason_string = json.dumps(top_level_dict,
                                  default=lambda info_df: json.loads(
                                      info_df.to_json()))
        with open(self.info_file, 'w') as outfile:
            outfile.write(jason_string)
        logger.info("Saved file to {}".format(self.info_file))

    def load_info_df(self, file_name=None):
        """Loads a DataFrame with all the needed info about the run
        (JSON file)"""

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

        The info_df JSON-file will be stored in the Project folder.
        The summary-files will be saved in the Batch-name folder.
        The raw data (including exported cycles and ica-data) will be saved to
        the Raw-data-dir.

        """
        self.info_file, directories = create_folder_structure(self.project,
                                                              self.name)
        self.project_dir, self.batch_dir, self.raw_dir = directories
        logger.debug("create folders:" + str(directories))

    def load_and_save_raw(self, parent_level="CellpyData"):
        """Loads the cellpy or raw-data file(s) and saves to csv"""
        sep = prms.Reader["sep"]
        if self.use_cellpy_stat_file is None:
            use_cellpy_stat_file = prms.Reader.use_cellpy_stat_file
        else:
            use_cellpy_stat_file = self.use_cellpy_stat_file
        logger.debug(f"b.load_and_save_raw: "
                     f"use_cellpy_stat_file = {use_cellpy_stat_file}")
        self.frames, self.keys, errors = read_and_save_data(
            self.info_df,
            self.raw_dir,
            sep=sep,
            force_raw=self.force_raw_file,
            force_cellpy=self.force_cellpy_file,
            export_cycles=self.export_cycles,
            shifted_cycles=self.shifted_cycles,
            export_raw=self.export_raw,
            export_ica=self.export_ica,
            save=self.save_cellpy_file,
            use_cellpy_stat_file=use_cellpy_stat_file,
            parent_level=parent_level,
            last_cycle=self.last_cycle
        )
        logger.debug("loaded and saved data. errors:" + str(errors))

    def make_summaries(self):
        """Make and save summary csv files,
        each containing values from all cells"""
        self.summary_df = save_summaries(self.frames, self.keys,
                                         self.selected_summaries,
                                         self.batch_dir, self.name)
        logger.debug("made and saved summaries")

    def make_stats(self):
        """Not implemented yet"""
        raise NotImplementedError

    def plot_test(self, show=True, save=False):
        figure_type = "shiftedcap"
        fig, ax = plt.subplots()

        # need to get symbol list etc
        color_list, symbol_list = self._create_colors_markers_list()
        plot_style = None
        batch_dir = self.batch_dir
        batch_name = self.name

        # need to get the df
        try:
            df_c = pick_summary_data("shifted_charge_capacity", self.summary_df,
                                     self.selected_summaries)
            df_d = pick_summary_data("shifted_discharge_capacity",
                                     self.summary_df, self.selected_summaries)
        except AttributeError:
            logger.debug("shifted capacities not part of summary data "
                         "(selected_summaries)")
            return None

        # generate labels
        labels = [self.info_df.get_value(filename, "labels") for filename in
                  df_c.columns.get_level_values(0)]

        # adding charge/discharge label
        labels.extend(["", "discharge", "charge"])

        list_of_lines, plot_style = plot_summary_data(
            ax, df_d,
            info_df=self.info_df,
            color_list=color_list,
            symbol_list=symbol_list,
            is_charge=False,
            plot_style=plot_style,
        )

        # adding charge/discharge legend signs
        color = plot_style["color"]
        markersize = plot_style["markersize"]

        open_label = mpl.lines.Line2D(
            [], [],
            color=color,
            marker='s',
            markeredgecolor=color,
            markerfacecolor='none',
            markersize=markersize
        )

        closed_label = mpl.lines.Line2D(
            [], [],
            color=color,
            marker='s',
            markeredgecolor=color,
            markerfacecolor=color,
            markersize=markersize
        )

        no_label = mpl.lines.Line2D(
            [], [],
            color='none',
            marker='s',
            markersize=0
        )

        list_of_lines.extend([no_label, closed_label, open_label])

        plot_summary_data(
            ax, df_c,
            info_df=self.info_df,
            color_list=color_list,
            symbol_list=symbol_list,
            is_charge=True,
            plot_style=plot_style
        )

        # setting axes labels
        ax.set_xlabel("cycle")
        ax.set_ylabel("capacity")
        # adding legend
        logger.debug("trying to add legends " + str(labels))
        fig.legend(
            handles=list_of_lines,
            labels=labels,
            bbox_to_anchor=(1.02, 1.1),
            loc=2,
            # bbox_transform=plt.gcf().transFigure,
            bbox_transform=ax.transAxes,
            numpoints=1,
            ncol=1, labelspacing=0.,
            prop={"size": 10}
        )

        if save:
            extension = prms.Batch["fig_extension"]
            dpi = prms.Batch["dpi"]
            figure_file_name = os.path.join(batch_dir, "%splot_%s.%s" % (
            figure_type, batch_name, extension))
            fig.savefig(figure_file_name, dpi=dpi, bbox_inches='tight')
            plt.savefig()

        if show:
            plt.show()

        return fig, ax

    def plot_shifted_cap(self, show=True, save=False):

        figure_type = "shiftedcap"
        fig, ax = plt.subplots()

        # need to get symbol list etc
        color_list, symbol_list = self._create_colors_markers_list()
        plot_style = None
        batch_dir = self.batch_dir
        batch_name = self.name

        # need to get the df
        try:
            df_c = pick_summary_data("shifted_charge_capacity", self.summary_df,
                                     self.selected_summaries)
            df_d = pick_summary_data("shifted_discharge_capacity",
                                     self.summary_df, self.selected_summaries)
        except AttributeError:
            logger.debug("shifted capacities not part of summary data "
                         "(selected_summaries)")
            return None

        # generate labels
        labels = [self.info_df.get_value(filename, "labels") for filename in
                  df_c.columns.get_level_values(0)]

        # adding charge/discharge label
        labels.extend(["", "discharge", "charge"])

        list_of_lines, plot_style = plot_summary_data(ax, df_d,
                                                      info_df=self.info_df,
                                                      color_list=color_list,
                                                      symbol_list=symbol_list,
                                                      is_charge=False,
                                                      plot_style=plot_style)

        # adding charge/discharge legend signs
        color = plot_style["color"]
        markersize = plot_style["markersize"]

        open_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                      markeredgecolor=color,
                                      markerfacecolor='none',
                                      markersize=markersize)
        closed_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                        markeredgecolor=color,
                                        markerfacecolor=color,
                                        markersize=markersize)
        no_label = mpl.lines.Line2D([], [], color='none', marker='s',
                                    markersize=0)
        list_of_lines.extend([no_label, closed_label, open_label])

        plot_summary_data(ax, df_c, info_df=self.info_df, color_list=color_list,
                          symbol_list=symbol_list, is_charge=True,
                          plot_style=plot_style)

        # setting axes labels
        ax.set_xlabel("cycle")
        ax.set_ylabel("capacity")
        # adding legend
        logger.debug("trying to add legends " + str(labels))
        fig.legend(handles=list_of_lines, labels=labels,
                   bbox_to_anchor=(1.02, 1.1), loc=2,
                   # bbox_transform=plt.gcf().transFigure,
                   bbox_transform=ax.transAxes,
                   numpoints=1,
                   ncol=1, labelspacing=0.,
                   prop={"size": 10})

        if save:
            extension = prms.Batch["fig_extension"]
            dpi = prms.Batch["dpi"]
            figure_file_name = os.path.join(batch_dir, "%splot_%s.%s" % (
            figure_type, batch_name, extension))
            fig.savefig(figure_file_name, dpi=dpi, bbox_inches='tight')
            plt.savefig()

        if show:
            plt.show()

        return fig, ax

    def plot_cum_irrev(self, show=True, save=False):
        # not ready for production yet...
        #   seems low level and high level is percentage of slippage

        figure_type = "irrevcum"
        fig, ax = plt.subplots()

        # need to get symbol list etc
        color_list, symbol_list = self._create_colors_markers_list()
        plot_style = None
        batch_dir = self.batch_dir
        batch_name = self.name

        # need to get the df
        try:
            df_c = pick_summary_data("low_level", self.summary_df,
                                     self.selected_summaries)
            df_d = pick_summary_data("high_level", self.summary_df,
                                     self.selected_summaries)
        except AttributeError:
            logger.debug(
                "low_level not part of summary data (selected_summaries)")
            return None

        # generate labels
        labels = [self.info_df.get_value(filename, "labels") for filename in
                  df_c.columns.get_level_values(0)]

        # adding charge/discharge label
        labels.extend(["", "low_level", "high_level"])

        list_of_lines, plot_style = plot_summary_data(ax, df_d,
                                                      info_df=self.info_df,
                                                      color_list=color_list,
                                                      symbol_list=symbol_list,
                                                      is_charge=False,
                                                      plot_style=plot_style)

        # adding charge/discharge legend signs
        color = plot_style["color"]
        markersize = plot_style["markersize"]

        open_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                      markeredgecolor=color,
                                      markerfacecolor='none',
                                      markersize=markersize)
        closed_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                        markeredgecolor=color,
                                        markerfacecolor=color,
                                        markersize=markersize)
        no_label = mpl.lines.Line2D([], [], color='none', marker='s',
                                    markersize=0)
        list_of_lines.extend([no_label, closed_label, open_label])

        plot_summary_data(ax, df_c, info_df=self.info_df, color_list=color_list,
                          symbol_list=symbol_list, is_charge=True,
                          plot_style=plot_style)

        # setting axes labels
        ax.set_xlabel("cycle")
        ax.set_ylabel("percentage")
        # adding legend
        logger.debug("trying to add legends " + str(labels))
        fig.legend(handles=list_of_lines, labels=labels,
                   bbox_to_anchor=(1.02, 1.1), loc=2,
                   # bbox_transform=plt.gcf().transFigure,
                   bbox_transform=ax.transAxes,
                   numpoints=1,
                   ncol=1, labelspacing=0.,
                   prop={"size": 10})

        if save:
            extension = prms.Batch["fig_extension"]
            dpi = prms.Batch["dpi"]
            figure_file_name = os.path.join(batch_dir, "%splot_%s.%s" % (
            figure_type, batch_name, extension))
            fig.savefig(figure_file_name, dpi=dpi, bbox_inches='tight')
            plt.savefig()

        if show:
            plt.show()

        return fig, ax

    def plot_summaries(self, show=False, save=True, figure_type=None):
        """Plot summary graphs.

        Args:
            show: shows the figure if True.
            save: saves the figure if True.
            figure_type: optional, figure type to create.
        """

        if not figure_type:
            figure_type = self.default_figure_type

        if not figure_type in self.default_figure_types:
            logger.debug("unknown figure type selected")
            figure_type = self.default_figure_type

        color_list, symbol_list = self._create_colors_markers_list()
        summary_df = self.summary_df
        selected_summaries = self.selected_summaries
        batch_dir = self.batch_dir
        batch_name = self.name
        fig, ax = plot_summary_figure(self.info_df, summary_df, color_list,
                                      symbol_list, selected_summaries,
                                      batch_dir, batch_name, show=show,
                                      save=save, figure_type=figure_type)
        self.figure[figure_type] = fig
        self.axes[figure_type] = ax

    def report(self):
        """Not implemented yet"""
        raise NotImplementedError


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
    headers_summary = cellpy.parameters.internal_settings.get_headers_summary()
    selected_summaries = dict()  # this should be sent as input
    for h in summaries_list:
        selected_summaries[h] = headers_summary[h]
    return selected_summaries


def get_db_reader(db_type):
    """Returns the db_reader.

    Args:
        db_type: type of db_reader (string) in ('simple_excel_reader', )

    Returns: db_reader (function)

    """
    if db_type == "simple_excel_reader":
        return dbreader.Reader
    else:
        raise NotImplementedError


def make_df_from_batch(batch_name, batch_col="b01", reader=None, reader_label=None):
    """Create a pandas DataFrame with the info needed for ``cellpy`` to load
    the runs.

    Args:
        batch_name (str): Name of the batch.
        batch_col (str): The column where the batch name is in the db.
        reader (method): the db-loader method.
        reader_label (str): the label for the db-loader (if db-loader method is
            not given)

    Returns: info_df (pandas DataFrame)
    """

    batch_name = batch_name
    batch_col = batch_col
    logger.debug(f"batch_name, batch_col: {batch_name}, {batch_col}")
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


def read_and_save_data(info_df, raw_dir, sep=";", force_raw=False,
                       force_cellpy=False,
                       export_cycles=False, shifted_cycles=False,
                       export_raw=True,
                       export_ica=False, save=True, use_cellpy_stat_file=False,
                       parent_level="CellpyData",
                       last_cycle=None,
                       ):
    """Reads and saves cell data defined by the info-DataFrame.

    The function iterates through the ``info_df`` and loads data from the runs.
    It saves individual data for each run (if selected), as well as returns a
    list of ``cellpy`` summary DataFrames, a list of the indexes (one for each
    run; same as used as index in the ``info_df``), as well as a list with
    indexes of runs (cells) where an error was encountered during loading.

    Args:
        use_cellpy_stat_file: use the stat file to perform the calculations.
        info_df: pandas.DataFrame with information about the runs.
        raw_dir: path to location where you want to save raw data.
        sep: delimiter to use when exporting to csv.
        force_raw: load raw data even-though cellpy-file is up-to-date.
        force_cellpy: load cellpy files even-though cellpy-file is not
            up-to-date.
        export_cycles: set to True for exporting cycles to csv.
        shifted_cycles: set to True for exporting the cycles with a cumulated
            shift.
        export_raw: set to True for exporting raw data to csv.
        export_ica: set to True for calculating and exporting dQ/dV to csv.
        save: set to False to prevent saving a cellpy-file.
        parent_level: optional, should use "cellpydata" for older hdf5-files and
            default for newer ones.

    Returns: frames (list of cellpy summary DataFrames), keys (list of indexes),
        errors (list of indexes that encountered errors).
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
        h_txt = "[" + counter * "|" + (number_of_runs - counter) * "." + "]"
        l_txt = "starting to process file # %i (index=%s)" % (counter, indx)
        logger.debug(l_txt)
        print(h_txt)
        if not row.raw_file_names and not force_cellpy:
            logger.info("File(s) not found!")
            logger.info(indx)
            logger.debug("File(s) not found for index=%s" % indx)
            errors.append(indx)
            continue
        else:
            logger.info(f"Processing {indx}")
        cell_data = cellreader.CellpyData()
        if not force_cellpy:
            logger.info("setting cycle mode (%s)..." % row.cell_type)
            cell_data.set_cycle_mode(row.cell_type)

        logger.info("loading cell")
        if not force_cellpy:
            logger.info("not forcing")
            try:
                cell_data.loadcell(raw_files=row.raw_file_names,
                                   cellpy_file=row.cellpy_file_names,
                                   mass=row.masses, summary_on_raw=True,
                                   force_raw=force_raw,
                                   use_cellpy_stat_file=use_cellpy_stat_file)
            except Exception as e:
                logger.debug('Failed to load: ' + str(e))
                errors.append("loadcell:" + str(indx))
                continue
        else:
            logger.info("forcing")
            try:
                cell_data.load(row.cellpy_file_names, parent_level=parent_level)
            except Exception as e:
                logger.info(f"Critical exception encountered {type(e)} "
                            "- skipping this file")
                logger.debug('Failed to load. Error-message: ' + str(e))
                errors.append("load:" + str(indx))
                continue

        if not cell_data.check():
            logger.info("...not loaded...")
            logger.debug("Did not pass check(). Could not load cell!")
            errors.append("check:" + str(indx))
            continue

        logger.info("...loaded successfully...")
        keys.append(indx)

        summary_tmp = cell_data.dataset.dfsummary
        logger.info("Trying to get summary_data")
        if summary_tmp is None:
            logger.info("No existing summary made - running make_summary")
            cell_data.make_summary(find_end_voltage=True, find_ir=True)

        if summary_tmp.index.name == b"Cycle_Index":
            logger.debug("Strange: 'Cycle_Index' is a byte-string")
            summary_tmp.index.name = 'Cycle_Index'

        if not summary_tmp.index.name == "Cycle_Index":
            logger.debug("Setting index to Cycle_Index")
            # check if it is a byte-string
            if b"Cycle_Index" in summary_tmp.columns:
                logger.debug("Seems to be a byte-string in the column-headers")
                summary_tmp.rename(columns={b"Cycle_Index": 'Cycle_Index'},
                                   inplace=True)
            summary_tmp.set_index("Cycle_Index", inplace=True)

        frames.append(summary_tmp)

        if save:
            if not row.fixed:
                logger.info("saving cell to %s" % row.cellpy_file_names)
                cell_data.ensure_step_table = True
                cell_data.save(row.cellpy_file_names)
            else:
                logger.debug("saving cell skipped (set to 'fixed' in info_df)")

        if no_export:
            continue

        if export_raw:
            logger.info("exporting csv")
            cell_data.to_csv(raw_dir, sep=sep, cycles=export_cycles,
                             shifted=shifted_cycles, raw=export_raw,
                             last_cycle=last_cycle)

        if do_export_dqdv:
            logger.info("exporting dqdv")
            try:
                export_dqdv(cell_data, savedir=raw_dir, sep=sep,
                            last_cycle=last_cycle)
            except Exception as e:
                logging.error("Could not make/export dq/dv data")
                logger.debug("Failed to make/export "
                             "dq/dv data (%s): %s" % (indx, str(e)))
                errors.append("ica:" + str(indx))

    if len(errors) > 0:
        logger.error("Finished with errors!")
        logger.debug(errors)
    else:
        logger.info("Finished")

    return frames, keys, errors


def save_summaries(frames, keys, selected_summaries, batch_dir, batch_name):
    """Writes the summaries to csv-files

    Args:
        frames: list of ``cellpy`` summary DataFrames
        keys: list of indexes (typically run-names) for the different runs
        selected_summaries: list defining which summary data to save
        batch_dir: directory to save to
        batch_name: the batch name (will be used for making the file-name(s))

    Returns: a pandas DataFrame with your selected summaries.

    """
    if not frames:
        logger.info("Could save summaries - no summaries to save!")
        logger.info("You have no frames - aborting")
        return None
    if not keys:
        logger.info("Could save summaries - no summaries to save!")
        logger.info("You have no keys - aborting")
        return None

    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    summary_df = pd.concat(frames, keys=keys, axis=1)
    # saving the selected summaries
    for key, value in selected_summaries_dict.items():
        _summary_file_name = os.path.join(batch_dir, "summary_%s_%s.csv" % (
        key, batch_name))
        _summary_df = summary_df.iloc[:,
                      summary_df.columns.get_level_values(1) == value]
        # include function to tweak headers here (need to learn MultiIndex)
        _header = _summary_df.columns
        _summary_df.to_csv(_summary_file_name, sep=";")
        logger.info(
            "saved summary (%s) to:\n       %s" % (key, _summary_file_name))
    logger.info("finished saving summaries")
    return summary_df


def pick_summary_data(key, summary_df, selected_summaries):
    """picks the selected pandas.DataFrame"""

    selected_summaries_dict = create_selected_summaries_dict(selected_summaries)
    value = selected_summaries_dict[key]
    return summary_df.iloc[:, summary_df.columns.get_level_values(1) == value]


def plot_summary_data(ax, df, info_df, color_list, symbol_list, is_charge=False,
                      plot_style=None):
    """creates a plot of the selected df-data in the given axes.

    Typical usage:
        standard_fig, (ce_ax, cap_ax, ir_ax) = plt.subplots(nrows=3, ncols=1,
                                                            sharex=True)
        list_of_lines, plot_style = plot_summary_data(ce_ax, ce_df,
                                                      info_df=info_df,
                                                      color_list=color_list,
                                                      symbol_list=symbol_list,
                                                      is_charge=False,
                                                      plot_style=plot_style)

        the ce_df is a pandas.DataFrame with ce-values for all your selected
        cells. the color_list and the symbol_list are both list with colors and
        symbols to use when plotting to ensure that if you have several subplots
        (axes), then the lines and symbols match up for each given cell.

    Args:
        ax: the matplotlib axes to plot on
        df: DataFrame with the data to plot
        info_df: DataFrame with info for the data
        color_list: List of colors to use
        symbol_list: List of symbols to use
        is_charge: plots open symbols if True
        plot_style: selected style of the plot

    Returns: list of the matplotlib lines (convenient to have if you are adding
        a custom legend) the plot style (dictionary with matplotlib plotstyles)

    """

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


def plot_summary_figure(info_df, summary_df, color_list, symbol_list,
                        selected_summaries,
                        batch_dir, batch_name, plot_style=None, show=False,
                        save=True,
                        figure_type=None):
    """Create a figure with summary graphs.
    Args:
        info_df: the pandas DataFrame with info about the runs.
        summary_df: a pandas DataFrame with the summary data.
        color_list: a list of colors to use (one pr. group)
        symbol_list: a list of symbols to use (one pr. cell in largest group)
        selected_summaries: a list of the selected summaries to plot
        batch_dir: path to the folder where the figure should be saved.
        batch_name: the batch name.
        plot_style: the matplotlib plot-style to use.
        show: show the figure if True.
        save: save the figure if True.
        figure_type: a string for selecting type of figure to make.
    """
    figure_type_object = figure_types[figure_type]

    logger.debug("creating figure ({})".format(figure_type))
    standard_fig, ax = plt.subplots(nrows=figure_type_object.rows,
                                    ncols=figure_type_object.columns,
                                    sharex=True)

    ce_ax = figure_type_object.retrieve_axis("ce_ax", ax)
    cap_ax = figure_type_object.retrieve_axis("cap_ax", ax)
    ir_ax = figure_type_object.retrieve_axis("ir_ax", ax)
    ev_ax = figure_type_object.retrieve_axis("ev_ax", ax)

    # pick data (common for all plot types)
    # could include a if cd_ax: pick_summary_data...
    ce_df = pick_summary_data("coulombic_efficiency", summary_df,
                              selected_summaries)
    cc_df = pick_summary_data("charge_capacity", summary_df, selected_summaries)
    dc_df = pick_summary_data("discharge_capacity", summary_df,
                              selected_summaries)

    # generate labels
    ce_labels = [info_df.get_value(filename, "labels") for filename in
                 ce_df.columns.get_level_values(0)]

    # adding charge/discharge label
    ce_labels.extend(["", "discharge", "charge"])

    # plot ce
    list_of_lines, plot_style = plot_summary_data(ce_ax, ce_df, info_df=info_df,
                                                  color_list=color_list,
                                                  symbol_list=symbol_list,
                                                  is_charge=False,
                                                  plot_style=plot_style)
    ce_ax.set_ylabel("Coulombic\nefficiency\n(%)")
    ce_ax.locator_params(nbins=5)

    # adding charge/discharge label
    color = plot_style["color"]
    markersize = plot_style["markersize"]

    open_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                  markeredgecolor=color, markerfacecolor='none',
                                  markersize=markersize)
    closed_label = mpl.lines.Line2D([], [], color=color, marker='s',
                                    markeredgecolor=color,
                                    markerfacecolor=color,
                                    markersize=markersize)
    no_label = mpl.lines.Line2D([], [], color='none', marker='s', markersize=0)
    list_of_lines.extend([no_label, closed_label, open_label])

    # plotting capacity (common)
    plot_summary_data(cap_ax, cc_df, is_charge=True, info_df=info_df,
                      color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)
    plot_summary_data(cap_ax, dc_df, is_charge=False, info_df=info_df,
                      color_list=color_list,
                      symbol_list=symbol_list, plot_style=plot_style)
    cap_ax.set_ylabel("Capacity\n(mAh/g)")
    cap_ax.locator_params(nbins=4)

    # plotting ir data (common)
    plot_ir_charge, plot_ir_discharge = figure_type_object.ir_selector
    if plot_ir_charge:
        irc_df = pick_summary_data("ir_charge", summary_df, selected_summaries)
        plot_summary_data(ir_ax, irc_df, is_charge=True, info_df=info_df,
                          color_list=color_list,
                          symbol_list=symbol_list, plot_style=plot_style)
    if plot_ir_discharge:
        ird_df = pick_summary_data("ir_discharge", summary_df,
                                   selected_summaries)
        plot_summary_data(ir_ax, ird_df, is_charge=False, info_df=info_df,
                          color_list=color_list,
                          symbol_list=symbol_list, plot_style=plot_style)

    ir_ax.set_ylabel("Internal\nresistance\n(Ohms)")
    ir_ax.set_xlabel("Cycle number")
    ir_ax.locator_params(axis="y", nbins=4)
    ir_ax.locator_params(axis="x", nbins=10)
    # should use MaxNLocator here instead

    # pick data (not common for all plot types)
    if ev_ax is not None:
        plot_ev_charge, plot_ev_discharge = figure_type_object\
            .end_voltage_selector
        if plot_ev_charge:
            evc_df = pick_summary_data("end_voltage_charge", summary_df,
                                       selected_summaries)
            plot_summary_data(ev_ax, evc_df, is_charge=True, info_df=info_df,
                              color_list=color_list,
                              symbol_list=symbol_list, plot_style=plot_style)
        if plot_ev_discharge:
            evd_df = pick_summary_data("end_voltage_discharge", summary_df,
                                       selected_summaries)
            plot_summary_data(ev_ax, evd_df, is_charge=False, info_df=info_df,
                              color_list=color_list,
                              symbol_list=symbol_list, plot_style=plot_style)

        ev_ax.set_ylabel("End\nvoltage\n(V)")
        ev_ax.locator_params(axis="y", nbins=4)

    # tweaking
    plt.subplots_adjust(left=0.07, right=0.93, top=0.9, wspace=0.25,
                        hspace=0.15)

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
        figure_file_name = os.path.join(batch_dir, "%splot_%s.%s" % (
        figure_type, batch_name, extension))
        standard_fig.savefig(figure_file_name, dpi=dpi, bbox_inches='tight')
    if show:
        plt.show()
    return standard_fig, (ce_ax, cap_ax, ir_ax)


def create_labels(label, *args):
    """Returns a re-formatted label (currently it only removes the dates
    from the run-name)"""
    return _remove_date(label)


def export_dqdv(cell_data, savedir, sep, last_cycle=None):
    """Exports dQ/dV data from a CellpyData instance.

    Args:
        cell_data: CellpyData instance
        savedir: path to the folder where the files should be saved
        sep: separator for the .csv-files.
        last_cycle: only export up to this cycle (if not None)
    """
    logger.debug("exporting dqdv")
    filename = cell_data.dataset.loaded_from
    no_merged_sets = ""
    firstname, extension = os.path.splitext(filename)
    firstname += no_merged_sets
    if savedir:
        firstname = os.path.join(savedir, os.path.basename(firstname))
        logger.debug(f"savedir is true: {firstname}")

    outname_charge = firstname + "_dqdv_charge.csv"
    outname_discharge = firstname + "_dqdv_discharge.csv"

    list_of_cycles = cell_data.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    logger.debug("%s: you have %i cycles" % (filename, number_of_cycles))

    # extracting charge
    out_data = _extract_dqdv(cell_data, cell_data.get_ccap, last_cycle)
    logger.debug("extracted ica for charge")
    try:
        _save_multi(data=out_data, file_name=outname_charge, sep=sep)
    except ExportFailed:
        logger.info("could not export ica for charge")
    else:
        logger.debug("saved ica for charge")

    # extracting discharge
    out_data = _extract_dqdv(cell_data, cell_data.get_dcap, last_cycle)
    logger.debug("extracxted ica for discharge")
    try:
        _save_multi(data=out_data, file_name=outname_discharge, sep=sep)
    except ExportFailed:
        logger.info("could not export ica for discharge")
    else:
        logger.debug("saved ica for discharge")


def init(*args, **kwargs):
    """Returns an initialized instance of the Batch class"""
    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)
    import cellpy.log as log
    log.setup_logging(custom_log_dir=prms.Paths["filelogdir"],
                      default_level=default_log_level)
    b = Batch(*args, **kwargs)
    return b


def _print_dict_keys(dir_items, name="KEYS", bullet=" -> "):
    number_of_stars_to_print = (79 - len(name)) // 2
    print()
    print(number_of_stars_to_print * "*", end='')
    print(name, end='')
    print(number_of_stars_to_print * "*")
    for item in dir_items:
        if not item.startswith("_"):
            print("{}{}".format(bullet, item))


def debugging():
    """This one I use for debugging..."""
    print("In debugging")
    json_file = r"C:\Scripting\Processing\Cell" \
                r"data\outdata\SiBEC\cellpy_batch_bec_exp02.json"

    b = init(default_log_level="DEBUG")
    b.load_info_df(json_file)
    print(b.info_df.head())

    # setting some variables
    b.export_raw = False
    b.export_cycles = False
    b.export_ica = False
    b.save_cellpy_file = True
    b.force_raw_file = False
    b.force_cellpy_file = True

    b.load_and_save_raw(parent_level="cellpydata")


def main():
    load_json = False
    if not load_json:
        print("Running batch_old.py (loading from db)")
        b = init("bec_exp06", "CellpyTest", default_log_level="DEBUG",
                 reader="excel", me="Jan Petter")
        b.selected_summaries.extend(
            ["shifted_charge_capacity", "shifted_discharge_capacity",
             "low_level", "high_level", ])
        b.create_info_df()
        b.create_folder_structure()
        b.save_info_df()
        print(b.info_file)
    else:
        print("Running batch_old.py (loading JSON)")
        b = init(default_log_level="DEBUG")
        b.load_info_df(
            r"C:\Scripting\Processing\Cell"
            r"data\outdata\CellpyTest\cellpy_batch_bec_exp06.json"
        )
    print(b)
    print("The info DataFrame:")
    print(b.info_df.head(5))
    b.force_cellpy_file = True
    b.load_and_save_raw()
    b.make_summaries()
    print(b.default_figure_types)
    b.plot_summaries(show=False)
    b.plot_summaries(show=True, figure_type="charge_limited")
    _print_dict_keys(dir(b), name="batch instance")

    # test new plots
    print("plotting cummulated irreversible capacities")
    fig, ax = b.plot_cum_irrev(show=True)
    print("plotting shifted capacities")
    fig, ax = b.plot_shifted_cap(show=True)

    print("Finished!")


if __name__ == '__main__':
    # debugging()
    main()
