# -*- coding: utf-8 -*-
"""easyplot module for cellpy. It provides easy plotting of any cellpy-readable data using matplotlib.
Author: Amund M. Raniseth
Date: 01.07.2021
"""


import logging
import os
import warnings
from pathlib import Path
from re import S

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import lines
from matplotlib.artist import kwdoc
from matplotlib.lines import Line2D
from matplotlib.scale import LogScale
from matplotlib.ticker import FuncFormatter

import cellpy
from cellpy import log
from cellpy.utils.batch_tools.batch_journals import LabJournal
from cellpy.parameters.internal_settings import (
    get_headers_journal,
    keys_journal_session,
)

hdr_journal = get_headers_journal()

# Dictionary of all possible user input arguments(as keys) with example values of correct type
# Value is a tuple (immutable) of type and default value.
USER_PARAMS = {
    "cyclelife_plot": (bool, True),
    "cyclelife_separate_data": (
        bool,
        False,
    ),  # will plot each cyclelife datafile in separate plots
    "cyclelife_percentage": (bool, False),
    "cyclelife_coulombic_efficiency": (bool, False),
    "cyclelife_coulombic_efficiency_ylabel": (str, "Coulombic efficiency [%]"),
    "cyclelife_charge_c_rate": (bool, False),
    "cyclelife_discharge_c_rate": (bool, False),
    "cyclelife_c_rate_ylabel": (str, "Effective C-rate"),
    "cyclelife_ir": (bool, False),  # Allows user to plot IR data aswell
    "cyclelife_xlabel": (str, "Cycles"),
    "cyclelife_ylabel": (str, r"Capacity $\left[\frac{mAh}{g}\right]$"),
    "cyclelife_ylabel_percent": (str, "Capacity retention [%]"),
    "cyclelife_legend_outside": (
        bool,
        False,
    ),  # if True, the legend is placed outside the plot
    "cyclelife_degradation_slope": (
        bool,
        False,
    ),  # Adds simple degradation slope regression to plot
    "capacity_determination_from_ratecap": (
        bool,
        False,
    ),  # If True, uses the ratecap and capacity to determine the exp capacity
    "galvanostatic_plot": (bool, True),
    "galvanostatic_potlim": (tuple, None),  # min and max limit on potential-axis
    "galvanostatic_caplim": (tuple, None),
    "galvanostatic_xlabel": (str, r"Capacity $\left[\frac{mAh}{g}\right]$"),
    "galvanostatic_ylabel": (str, "Cell potential [V]"),
    "galvanostatic_normalize_capacity": (
        bool,
        False,
    ),  # Normalizes all cycles' capacity to 1.
    "dqdv_plot": (bool, False),
    "dqdv_potlim": (tuple, None),  # min and max limit on potential-axis
    "dqdv_dqlim": (tuple, None),
    "dqdv_xlabel": (
        str,
        r"dQ/dV $\left[\frac{mAh}{gV}\right]$",
    ),  # TODO what unit? jees
    "dqdv_ylabel": (str, "Cell potential [V]"),
    "specific_cycles": (list, None),
    "exclude_cycles": (list, None),
    "all_in_one": (
        bool,
        False,
    ),  # Decides if everything should be plotted in the same plot in GC and dQdV plot
    "only_dischg": (bool, False),  # Only show discharge curves
    "only_chg": (bool, False),  # Only show charge curves
    "outpath": (str, "./"),
    "outtype": (str, ".png"),  # What file format to save in
    "outname": (str, None),  # Overrides the automatic filename generation
    "figsize": (tuple, (6, 4)),  # 6 inches wide, 4 inches tall
    "figres": (int, 100),  # Dots per Inch
    "figtitle": (str, "Title"),  # None = original filepath
    "save_figures": (bool, True),
    "save_journal": (bool, False),  # Save journal
}


def help():
    """Method of the EasyPlot class which prints some helptext in addition to all supported params."""
    ## Prints out help page of this module
    help_str = (
        "The easyplot extension to cellpy aims to easily plot data in a pretty manner.\n"
        "In order to use this function, you must import cellpy, and easyplot from cellpy.utils.\n"
        "\n"
        "Usage:\n"
        "Create list of datafiles you want to plot on the following format:\n"
        "\n"
        "files = [\n"
        "\t'./folder/filename.ext',\n"
        "\t'./folder/filename2.ext',\n"
        "\t]\n"
        "\n"
        "And then call the easyplot.plot function with the files list as the first parameter, and any optional keyword arguments.\n"
        "Here is an example of the use of all keyword arguments:\n"
    )
    for kw in USER_PARAMS:
        if type(USER_PARAMS[kw][1]) == str:
            insert = "'" + USER_PARAMS[kw][1] + "'"
        else:
            insert = str(USER_PARAMS[kw][1])
        help_str += "\t" + kw + " = " + insert + ",\n"
    print(help_str)


class EasyPlot:
    """Main easyplot class.
    Takes all the inputs from the user in its kwargs upon object initialization.
    Gathers data, handles and plots it when object.plot() is called.

    Help: type easyplot.help()
    """

    def __init__(self, files=None, nicknames=None, journal=None, **kwargs):
        """Initialization function of the EasyPlot class.
        Input parameters:
        filenames (list of strings).
        nicknames (list of strings), must match length of filenames.
        journal (str or pathlib.Path object): journal file name (should not be used if files is given).
        any kwargs: use easyplot.help() to print all kwargs to terminal.

        Returns:
        easyplot object

        Most basic usage:
        ezpltobj = easyplot.EasyPlot(["name1", "name2"], None)"""

        # Make all user input variables of self
        self.files = files
        self.nicknames = nicknames
        self.kwargs = kwargs

        # More needed variables
        self.figs = []
        self.file_data = []
        self.use_arbin_sql = False
        if journal is not None:
            self.journal_file = Path(journal)
        else:
            self.journal_file = None
        self.journal = None

        # Dictionary of all possible user input arguments(as keys) with example values of correct type
        # Value is a tuple (immutable) of type and default value.
        self.user_params = USER_PARAMS

        # Create 'empty' attributes for later use
        self.outpath = None
        self.masses = None
        self.labels = None
        self.nom_caps = None
        self.colors = None

        # List of available colors

        # Fill in the rest of the variables from self.user_params if the user didn't specify
        self.fill_input()

        # Verify that the user input is sufficient
        self.verify_input()
        self._generate_list_of_available_colors()

    def _generate_list_of_available_colors(self):
        if 19 >= len(self.files) > 10:
            self.colors = [
                "#e6194b",
                "#3cb44b",
                "#ffe119",
                "#4363d8",
                "#f58231",
                "#911eb4",
                "#46f0f0",
                "#f032e6",
                "#bcf60c",
                "#fabebe",
                "#008080",
                "#e6beff",
                "#9a6324",
                "#fffac8",
                "#800000",
                "#aaffc3",
                "#808000",
                "#ffd8b1",
                "#000075",
                "#808080",
                "#000000",
            ]
            warnings.warn(
                "You inserted more than 10 datafiles! In a desperate attempt to keep "
                "the plots tidy, another colorpalette with 19 distinct colors were chosen."
            )
        elif len(self.files) > 19:
            warnings.warn(
                "You inserted more than 19 datafiles! We do not have that "
                "many colors in the palette, this some colors are beeing recycled. "
                "Keep track of the filenames and legends and make sure this doesn't confuse you."
            )
        else:
            self.colors = [
                              "tab:blue",
                              "tab:orange",
                              "tab:green",
                              "tab:red",
                              "tab:purple",
                              "tab:brown",
                              "tab:pink",
                              "tab:gray",
                              "tab:olive",
                              "tab:cyan",
                          ] * 5

    def plot(self):
        """This is the method the user calls on his/hers easyplot object in order to gather the data and plot it.
        Usage: object.plot()"""

        # Load all cellpy files
        logging.debug("starting plotting")
        for file in self.files:
            if isinstance(file, (list, tuple)):
                logging.debug("linked files provided - need to merge")
                linked_files = True
            else:
                linked_files = False

            # If using arbin sql
            if self.use_arbin_sql:
                cpobj = cellpy.get(
                    filename=file, instrument="arbin_sql"
                )  # Initiate cellpy object
            else:  # Not Arbin SQL? Then its probably a local file

                # Check that file(s) exist
                if linked_files:
                    file_name = "_".join(file)
                    for _f in file:
                        if not os.path.isfile(_f):
                            logging.error("File not found: " + str(_f))
                            raise FileNotFoundError

                else:
                    file_name = file
                    if not os.path.isfile(file):
                        logging.error("File not found: " + str(file))
                        print(os.getcwd())
                        raise FileNotFoundError

                cpobj = cellpy.get(filename=file)  # Load regular file
                # Check that we get data
            if cpobj is None:
                warnings.warn(
                    f"File reader returned no data for filename {file}. Please make sure that the file exists or "
                    f"that the data exists in an eventual database."
                )

            # Get ID of all cycles
            cyc_nums = cpobj.get_cycle_numbers()

            # Only get the cycles which both exist in data, and that the user want
            if self.kwargs["specific_cycles"] is not None:
                cyc_not_available = (
                                        set(cyc_nums) ^ set(self.kwargs["specific_cycles"])
                                    ) & set(self.kwargs["specific_cycles"])
                if len(cyc_not_available) > 0:
                    warn_str = (
                        f"You want to plot cycles which are not available in the data! Datafile(s): "
                        f"{file}"
                        f", Cycle(s): {str(cyc_not_available)}"
                    )
                    warnings.warn(warn_str)
                cyc_nums = list(
                    set(cyc_nums).intersection(self.kwargs["specific_cycles"])
                )

            if self.kwargs["exclude_cycles"] is not None:
                cyc_nums = list(set(cyc_nums) - set(self.kwargs["exclude_cycles"]))

            color = self.give_color()  # Get a color for the data

            self.file_data.append((cpobj, cyc_nums, color, file_name))

        # Check kwargs/input parameters to see what plots to make
        if self.kwargs["cyclelife_plot"]:
            self.plot_cyclelife()

        if self.kwargs["galvanostatic_plot"] and not self.kwargs["dqdv_plot"]:
            self.plot_gc()

        if self.kwargs["dqdv_plot"] and not self.kwargs["galvanostatic_plot"]:
            self.plot_dQdV()

        if self.kwargs["galvanostatic_plot"] and self.kwargs["dqdv_plot"]:
            self.plot_gc_and_dQdV()

        if self.kwargs["capacity_determination_from_ratecap"]:
            self.plot_cap_from_rc()

        self._wrap_up()

    def _wrap_up(self):
        # saving journal file
        if self.kwargs["save_journal"]:
            if self.journal is not None:
                if self.outpath is not None:
                    journal_file_path = Path(self.outpath) / self.journal_file.name
                else:
                    journal_file_path = self.journal_file.name

                # if we want to enforce that the file will be a xlsx file:
                # journal_file_path = journal_file_path.with_suffix(".xlsx")

                journal_file_path = journal_file_path.with_suffix(".json")
                self.journal.to_file(
                    file_name=journal_file_path, paginate=False, to_project_folder=False
                )
                xlsx_journal_file_path = journal_file_path.with_name(
                    f"{journal_file_path.stem}.xlsx"
                )
                self.journal.to_file(
                    file_name=xlsx_journal_file_path,
                    paginate=False,
                    to_project_folder=False,
                )

    def verify_input(self):
        """Verifies that the users' input to the object is correct."""
        # Check that output dir exist (or create one)
        self.outpath = self.handle_outpath()  # Takes care of the output path

        # Check the nicknames
        if self.nicknames:
            if len(self.nicknames) != len(self.files):
                logging.error(
                    "Use nicknames = None, or specify exactly one nickname per datafile. You have specified "
                    + str(len(self.nicknames))
                    + " nicknames while inputting "
                    + str(len(self.files))
                    + " datafiles"
                )
                raise AssertionError

        # Check that all kwargs are used correctly
        for key in self.kwargs:
            # Check that input parameter exist
            try:
                self.user_params[key]
            except KeyError as e:
                logging.error(
                    "Input parameter "
                    + key
                    + " is not a valid parameter! Please see example configuration for help or run easyplot.help()"
                )

            # Check that the type is correct
            if type(self.kwargs[key]) != self.user_params[key][0] and type(
                self.kwargs[key]
            ) != type(None):
                logging.error(
                    "Type of inputparameter for keyword '"
                    + key
                    + "' is wrong. The user specified "
                    + str(type(self.kwargs[key]))
                    + " but the program needs a "
                    + str(self.user_params[key][0])
                )
                raise TypeError

        # Check that the user isn't trying to plot "only" both discharge and charge.
        if self.kwargs["only_dischg"] and self.kwargs["only_chg"]:
            logging.error(
                "You can't plot 'only' discharge AND charge curves! Set one to False please."
            )

        if self.journal_file is not None:
            # Check that the user isn't providing both a list of files and a journal filename
            if self.files is not None:
                logging.error(
                    "You can't give both filenames and a journal file at the same time."
                )
                logging.error("Chose either filenames OR journal file name please.")
                raise ValueError
            self._read_journal_file()
            self._populate_from_journal()  # Temporary fix - the parameters should be read directly from journal later
        else:
            if self.files is None:
                logging.error("No file names provided.")
                logging.error("Add file names OR journal file name please.")
                raise ValueError

    def _read_journal_file(self):
        logging.debug(f"reading journal file {self.journal_file}")
        journal = LabJournal(db_reader=None)
        journal.from_file(self.journal_file, paginate=False)
        self.journal = journal

    def _populate_from_journal(self):
        logging.debug(f"populating from journal")
        # populating from only a subset of the available journal columns
        # - can be increased later
        try:
            self.files = self.journal.pages[hdr_journal["raw_file_names"]].to_list()
        except AttributeError:
            logging.debug("No raw files found in your journal")

        try:
            self.masses = self.journal.pages[hdr_journal["mass"]].to_list()
        except AttributeError:
            logging.debug("No masses found in your journal")

        try:
            self.labels = self.journal.pages[hdr_journal["label"]].to_list()
        except AttributeError:
            logging.debug("No labels found in your journal")

        try:
            self.nom_cap = self.journal.pages[hdr_journal["nom_cap"]].to_list()
        except AttributeError:
            logging.debug("No nominal capacity found in your journal")

        try:
            self.cellpy_files = self.journal.pages[
                hdr_journal["cellpy_file_name"]
            ].to_list()
        except AttributeError:
            logging.debug("No cellpy files found in your journal")

    def fill_input(self):
        """Fill in the rest of the variables from self.user_params if the user didn't specify"""
        # Can't just join dicts since they have differing formats, need to loop...
        for key in self.user_params:
            try:
                self.kwargs[key]
            except KeyError:
                self.kwargs[key] = self.user_params[key][1]

    def set_arbin_sql_credentials(
        self,
        server="localhost",
        uid="sa",
        pwd="Changeme123",
        driver="ODBC Driver 17 for SQL Server",
    ):
        """Sets cellpy.prms.Instruments.Arbin details to fit what is inserted.
            Parameters: Server = 'IP of server', uid = 'username', pwd = 'password', driver = 'ODBC Driver 17 for SQL Server' """
        cellpy.prms.Instruments.Arbin["SQL_server"] = server
        cellpy.prms.Instruments.Arbin["SQL_UID"] = uid
        cellpy.prms.Instruments.Arbin["SQL_PWD"] = pwd
        cellpy.prms.Instruments.Arbin["SQL_Driver"] = driver
        self.use_arbin_sql = True

    def give_color(self):
        """Picks the first color from the color list and gives it away"""
        color = self.colors[0]
        self.colors = self.colors[1:]
        return color

    def give_fig(self):
        """Gives figure to whoever asks and appends it to figure list"""

        fig, ax = plt.subplots(figsize=(6, 4))
        self.figs.append((fig, ax))
        return fig, ax

    def handle_outpath(self):
        """Makes sure that self.outpath exists, or creates it."""
        out_path = self.kwargs["outpath"]

        # should make this a pathlib.Path object - but not sure if str is assumed later on in the code
        if os.path.isdir(out_path):
            logging.debug(f"out path set to {out_path}")
            return out_path
        elif not os.path.isdir(out_path):
            logging.debug(f"outpath does not exits - creating")
            try:
                os.makedirs(out_path)
                logging.debug(f"out path set to {out_path}")
                return out_path
            except OSError as e:
                logging.error(
                    f"Cannot create output directory {out_path}. Please make sure you "
                    f"have write permission. Error message: {e}"
                )

    def plot_cyclelife(self):
        """Takes all the parameters inserted in the object creation and plots cyclelife"""
        # Spawn fig and axis for plotting
        if not self.kwargs["cyclelife_separate_data"]:
            fig, ax = self.give_fig()
            if self.kwargs["cyclelife_coulombic_efficiency"]:
                # Spawn twinx axis and set label
                ax_ce = ax.twinx()
                ax_ce.set(ylabel=self.kwargs["cyclelife_coulombic_efficiency_ylabel"])
            if (
                self.kwargs["cyclelife_charge_c_rate"]
                or self.kwargs["cyclelife_discharge_c_rate"]
            ):
                ax_c_rate = ax.twinx()

                def format_label(x, pos):
                    # The commented out code here makes the fractioned C-rate like C/50 and so on.
                    """
                    if x >= 1:
                        s = '%.2gC' % x
                    elif x == 0:
                        s = r'C/$\infty$'
                    else:
                        newfloat = 1/x
                        s = 'C/%.2g' % newfloat
                        """
                    # The following just has decimal place C-rate.
                    s = "%.3gC" % x
                    return s

                ax_c_rate.yaxis.set_major_formatter(FuncFormatter(format_label))
                ax_c_rate.set(ylabel="Effective C-rate")

            if self.kwargs["cyclelife_ir"]:
                ax_ir = ax.twinx()

            outpath = self.outpath

        for cpobj, cyc_nums, color, filename in self.file_data:
            if self.kwargs["cyclelife_separate_data"]:
                fig, ax = self.give_fig()
                if self.kwargs["cyclelife_coulombic_efficiency"]:
                    # Spawn twinx axis and set label
                    ax_ce = ax.twinx()
                    ax_ce.set(
                        ylabel=self.kwargs["cyclelife_coulombic_efficiency_ylabel"]
                    )
                if (
                    self.kwargs["cyclelife_charge_c_rate"]
                    or self.kwargs["cyclelife_discharge_c_rate"]
                ):
                    ax_c_rate = ax.twinx()

                    def format_label(x, pos):
                        # The following just has decimal place C-rate.
                        s = "%.3gC" % x
                        return s

                    ax_c_rate.yaxis.set_major_formatter(FuncFormatter(format_label))
                    ax_c_rate.set(ylabel="Effective C-rate")

                if self.kwargs["cyclelife_ir"]:
                    ax_ir = ax.twinx()

            # Get Pandas DataFrame of pot vs cap from cellpy object
            df = cpobj.get_cap(
                method="forth-and-forth",
                label_cycle_number=True,
                categorical_column=True,
            )
            outpath += os.path.basename(filename).split(".")[0] + "_"

            # Group by cycle and make list of cycle numbers
            cycgrouped = df.groupby("cycle")
            keys = []
            for key, item in cycgrouped:
                keys.append(key)

            chgs = [[], []]  # List with cycle num and capacity
            dchgs = [[], []]
            # Accumulate cycles
            for cyc in keys:  # Loop over all cycles
                if cyc in cyc_nums:  # Check if it is in list of wanted cycles
                    cyc_df = cycgrouped.get_group(
                        cyc
                    )  # Get the group of datapoints from specific cycle

                    cyc_redox_grouped = cyc_df.groupby(
                        "direction"
                    )  # Group by direction (meaning if it is charging or discharging)

                    dchg_df = cyc_redox_grouped.get_group(
                        -1
                    )  # Data for the discharge curve
                    dchgs[0].append(cyc)  # Append to dchg list
                    dchgs[1].append(dchg_df["capacity"].iat[-2])

                    chg_df = cyc_redox_grouped.get_group(1)  # Data for the charge curve
                    chgs[0].append(cyc)  # Append to chg list
                    chgs[1].append(chg_df["capacity"].iat[-2])

            if self.kwargs[
                "cyclelife_percentage"
            ]:  # Normalize all datapoints on the first one
                norm_fact = (
                    dchgs[1][0] / 100
                )  # /100 is to get range from 0-100(%) in stead of 0-1
                for i in range(len(chgs[1])):
                    chgs[1][i] /= norm_fact
                for i in range(len(dchgs[1])):
                    dchgs[1][i] /= norm_fact

            # Make label from filename or nickname
            if self.nicknames:
                label = self.nicknames[self.files.index(filename)]
            else:
                label = str(os.path.basename(filename))
            # print("Discharge capacities:")
            # print(dchgs[1])
            # Actully place it in plot
            if not self.kwargs["only_dischg"] and not self.kwargs["only_chg"]:
                ax.scatter(
                    chgs[0], chgs[1], c=color, alpha=0.2,
                )
                ax.scatter(dchgs[0], dchgs[1], c=color, label=label)
            elif self.kwargs["only_dischg"]:
                ax.scatter(dchgs[0], dchgs[1], c=color, label=label)
            elif self.kwargs["only_chg"]:
                ax.scatter(
                    chgs[0], chgs[1], c=color, alpha=0.2,
                )

            if self.kwargs["cyclelife_coulombic_efficiency"]:
                # Get CE for cyc_nums
                coulombic_efficiency = cpobj.cell.summary[
                    "coulombic_efficiency_u_percentage"
                ]
                cycs = []
                CEs = []
                for cyc in keys:
                    if cyc in cyc_nums:
                        cycs.append(cyc)
                        CEs.append(coulombic_efficiency[cyc])

                # Place it in the plot
                ax_ce.scatter(cycs, CEs, c=color, marker="+")
                # print(filename + " Dchg 1-3: " + str(dchgs[1][0:3])  + ", CE 1-3: " + str(coulombic_efficiency[0:3]))

            if (
                self.kwargs["cyclelife_charge_c_rate"]
                or self.kwargs["cyclelife_discharge_c_rate"]
            ):
                # charge_c_rate = cpobj.cell.summary["charge_c_rate"] #This gives incorrect c-rates.

                stepstable = cpobj.cell.steps
                chg_c_rates, dchg_c_rates = get_effective_C_rates(stepstable)

                selected_chg_c_rates = []
                selected_dchg_c_rates = []
                selected_cycs = []

                for cyc in keys:
                    if cyc in cyc_nums:
                        selected_chg_c_rates.append(chg_c_rates[cyc - 1])
                        selected_dchg_c_rates.append(dchg_c_rates[cyc - 1])
                        selected_cycs.append(cyc)

                if (
                    self.kwargs["cyclelife_charge_c_rate"]
                    and not self.kwargs["cyclelife_discharge_c_rate"]
                ):
                    ax_c_rate.scatter(
                        selected_cycs, selected_chg_c_rates, c=color, marker="_"
                    )
                elif (
                    not self.kwargs["cyclelife_charge_c_rate"]
                    and self.kwargs["cyclelife_discharge_c_rate"]
                ):
                    ax_c_rate.scatter(
                        selected_cycs, selected_dchg_c_rates, c=color, marker="_"
                    )
                elif (
                    self.kwargs["cyclelife_charge_c_rate"]
                    and self.kwargs["cyclelife_discharge_c_rate"]
                ):
                    ax_c_rate.scatter(
                        selected_cycs, selected_chg_c_rates, c=color, marker="_"
                    )
                    ax_c_rate.scatter(
                        selected_cycs,
                        selected_dchg_c_rates,
                        c=color,
                        alpha=0.2,
                        marker="_",
                    )

            if self.kwargs["cyclelife_degradation_slope"]:
                from scipy.stats import linregress

                slope, intercept, r, p, se = linregress(dchgs[0], dchgs[1])
                x = np.linspace(0, ax.get_xlim()[1] * 0.9, 10)
                degradation_unit = (
                    r" $\frac{mAh}{g\cdot cycle}$"
                    if not self.kwargs["cyclelife_percentage"]
                    else r" $\frac{\%}{cycle}$"
                )
                intercept_unit = (
                    r" $\frac{mAh}{g}$"
                    if not self.kwargs["cyclelife_percentage"]
                    else r"%"
                )
                ax.plot(
                    x,
                    x * slope + intercept,
                    c=color,
                    label="Degradation: %g" % slope
                          + degradation_unit
                          + "\nIntercept:       %g" % intercept
                          + intercept_unit
                          + ", r=%g" % r,
                )

            """if self.kwargs["cyclelife_ir"]:
                chg_ir = []
                dchg_ir = []


                steptable = cpobj.steps
                print(steptable)
                newdf = steptable[["ir", "cycle", "type"]]
                for i,elem in enumerate(newdf.iterrows()):
                    if elem[1]["type"] == "charge":
                        chg_ir.append(elem[1]["ir"])
                    elif elem[1]["type"] == "discharge":
                        dchg_ir.append(elem[1]["ir"])
                print(chg_ir)

                for cyc in keys:
                    if cyc in cyc_nums:
                        ax_ir.scatter(cyc, chg_ir[cyc], c = color, marker = "*")
                        """

            if self.kwargs["cyclelife_separate_data"]:
                # Set all plot settings from Plot object
                self.fix_cyclelife(fig, ax)

                # Save fig
                savepath = outpath.strip("_") + "_Cyclelife"
                self.save_fig(fig, savepath)

        if not self.kwargs["cyclelife_separate_data"]:

            # Set all plot settings from Plot object
            self.fix_cyclelife(fig, ax)

            # Save fig
            savepath = outpath.strip("_") + "_Cyclelife"
            self.save_fig(fig, savepath)

    def plot_gc(self):
        """Takes all the parameters inserted in the object creation and plots Voltage-Capacity curves"""

        if self.kwargs["all_in_one"]:  # Everything goes in the same figure.

            fig, ax = self.give_fig()
            colors = [
                         "tab:blue",
                         "tab:orange",
                         "tab:green",
                         "tab:red",
                         "tab:purple",
                         "tab:brown",
                         "tab:pink",
                         "tab:gray",
                         "tab:olive",
                         "tab:cyan",
                     ] * 5
            savepath = self.outpath

            colorbar_incrementor = -1
            for cpobj, cyc_nums, color, filename in self.file_data:
                # Get Pandas DataFrame of pot vs cap from cellpy object
                df = cpobj.get_cap(
                    method="forth-and-forth",
                    label_cycle_number=True,
                    categorical_column=True,
                )

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Make label from filename or nickname
                if self.nicknames:
                    label = str(self.nicknames[self.files.index(filename)])
                else:
                    label = str(os.path.basename(filename))

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    cbaxes = fig.add_axes(
                        [1.05 + colorbar_incrementor / 8, 0.1, 0.03, 0.8]
                    )
                    colorbar_incrementor += 1
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                        cax=cbaxes,
                        label="Cycle number for "
                              + os.path.basename(filename).split(".")[0],
                    )
                    # fig.colorbar.ax.yaxis.get_major_locator().set_params(integer=True) #TODO fix such that we dont have decimals on the cycle colorbar!!

                # Plot cycles
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)

                        if (
                            not self.kwargs["only_dischg"]
                            and not self.kwargs["only_chg"]
                        ):
                            pass
                        elif self.kwargs["only_dischg"]:
                            dchg = cyc_df.groupby("direction")
                            cyc_df = dchg.get_group(-1)
                        elif self.kwargs["only_chg"]:
                            chg = cyc_df.groupby("direction")
                            cyc_df = chg.get_group(1)

                        # TODO: The way this is set up, when plotting both discharge and charge, the whole cycle is normalized on the maximum capacity, meaning the charge can be normalized on the discharge or the other way around.
                        if self.kwargs["galvanostatic_normalize_capacity"]:
                            # Then we normalize capacity column on the max value (since this should be max cap)
                            maxcap = cyc_df["capacity"].max()
                            cyc_df["capacity"] = cyc_df["capacity"].div(maxcap)
                            ax.set_xlabel("Normalized Capacity")

                        ax.plot(
                            cyc_df["capacity"],
                            cyc_df["voltage"],
                            label=label + ", Cyc " + str(cyc),
                            c=cyccolor,
                        )

                savepath += os.path.basename(filename).split(".")[0]

            fig.suptitle("Galvanostatic cyclingdata")
            self.fix_gc(fig, ax)

            # Save fig
            savepath += "_GC-plot"
            self.save_fig(fig, savepath)

        else:  # Then each data goes in its own figure
            for cpobj, cyc_nums, color, filename in self.file_data:
                fig, ax = self.give_fig()

                # Get Pandas DataFrame of pot vs cap from cellpy object
                df = cpobj.get_cap(
                    method="forth-and-forth",
                    label_cycle_number=True,
                    categorical_column=True,
                )

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap), label="Cycle"
                    )
                    # fig.colorbar.ax.yaxis.get_major_locator().set_params(integer=True) #TODO fix such that we dont have decimals on the cycle colorbar!!

                # Make label from filename or nickname
                if self.nicknames:
                    label = str(self.nicknames[self.files.index(filename)])
                else:
                    label = str(os.path.basename(filename))

                # Plot cycles
                colors = [
                    "tab:blue",
                    "tab:orange",
                    "tab:green",
                    "tab:red",
                    "tab:purple",
                    "tab:brown",
                    "tab:pink",
                    "tab:gray",
                    "tab:olive",
                    "tab:cyan",
                ]
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        # TODO: This if elif block is pretty much the same as the one above (for all in one plot), can it be reused in stead of written twice?
                        if (
                            not self.kwargs["only_dischg"]
                            and not self.kwargs["only_chg"]
                        ):
                            pass
                        elif self.kwargs["only_dischg"]:
                            dchg = cyc_df.groupby("direction")
                            cyc_df = dchg.get_group(-1)
                        elif self.kwargs["only_chg"]:
                            chg = cyc_df.groupby("direction")
                            cyc_df = chg.get_group(1)

                        # TODO: The way this is set up, when plotting both discharge and charge, the whole cycle is normalized on the maximum capacity, meaning the charge can be normalized on the discharge or the other way around.
                        if self.kwargs["galvanostatic_normalize_capacity"]:
                            # Then we normalize capacity column on the max value (since this should be max cap)
                            maxcap = cyc_df["capacity"].max()
                            cyc_df["capacity"] = cyc_df["capacity"].div(maxcap)
                            ax.set_xlabel("Normalized Capacity")

                        ax.plot(
                            cyc_df["capacity"],
                            cyc_df["voltage"],
                            label=label.split(".")[0] + ", Cyc " + str(cyc),
                            c=cyccolor,
                        )

                # Set all plot settings from Plot object

                fig.suptitle(label)
                self.fix_gc(fig, ax)

                # Save fig
                savepath = (
                    self.outpath + os.path.basename(filename).split(".")[0] + "_GC-plot"
                )
                self.save_fig(fig, savepath)

    def plot_dQdV(self):
        """Takes all the parameters inserted in the object creation and plots dQdV"""
        from cellpy.utils import ica

        if self.kwargs["all_in_one"]:  # Everything goes in the same figure.

            fig, ax = self.give_fig()
            colors = [
                         "tab:blue",
                         "tab:orange",
                         "tab:green",
                         "tab:red",
                         "tab:purple",
                         "tab:brown",
                         "tab:pink",
                         "tab:gray",
                         "tab:olive",
                         "tab:cyan",
                     ] * 5
            savepath = self.outpath

            colorbar_incrementor = -1
            for cpobj, cyc_nums, color, filename in self.file_data:
                # Get Pandas DataFrame of dQdV
                if self.kwargs["only_dischg"]:
                    _, df = ica.dqdv_frames(cpobj, split=True)
                elif self.kwargs["only_chg"]:
                    df, _ = ica.dqdv_frames(cpobj, split=True)
                else:
                    df = ica.dqdv_frames(cpobj)

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    cbaxes = fig.add_axes(
                        [1.05 + colorbar_incrementor / 8, 0.1, 0.03, 0.8]
                    )
                    colorbar_incrementor += 1
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                        cax=cbaxes,
                        label="Cycle number for "
                              + os.path.basename(filename).split(".")[0],
                    )

                    # fig.colorbar.ax.yaxis.get_major_locator().set_params(integer=True) #TODO fix such that we dont have decimals on the cycle colorbar!!

                # Plot cycles
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        ax.plot(
                            cyc_df["voltage"],
                            cyc_df["dq"],
                            label=os.path.basename(filename).split(".")[0]
                                  + ", Cyc "
                                  + str(cyc),
                            c=cyccolor,
                        )
                savepath += os.path.basename(filename).split(".")[0]

            fig.suptitle("dQdV")
            self.fix_dqdv(fig, ax)

            # Save fig
            savepath += "_dQdV-plot"
            self.save_fig(fig, savepath)

        else:
            for cpobj, cyc_nums, color, filename in self.file_data:
                fig, ax = self.give_fig()

                # Get Pandas DataFrame of dQdV
                if self.kwargs["only_dischg"]:
                    _, df = ica.dqdv_frames(cpobj, split=True)
                elif self.kwargs["only_chg"]:
                    df, _ = ica.dqdv_frames(cpobj, split=True)
                else:
                    df = ica.dqdv_frames(cpobj)

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Create the plot obj
                fig, ax = plt.subplots(figsize=(6, 4))

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap), label="Cycle"
                    )
                    # fig.colorbar.ax.yaxis.get_major_locator().set_params(integer=True) #TODO fix such that we dont have decimals on the cycle colorbar!!

                # Plot cycles
                colors = [
                    "tab:blue",
                    "tab:orange",
                    "tab:green",
                    "tab:red",
                    "tab:purple",
                    "tab:brown",
                    "tab:pink",
                    "tab:gray",
                    "tab:olive",
                    "tab:cyan",
                ]
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])
                        cyc_df = cycgrouped.get_group(cyc)
                        ax.plot(
                            cyc_df["voltage"],
                            cyc_df["dq"],
                            label="Cycle " + str(cyc),
                            c=cyccolor,
                        )

                # Set all plot settings from Plot object
                fig.suptitle(os.path.basename(filename))
                self.fix_dqdv(fig, ax)

                # Save fig
                savepath = (
                    self.outpath
                    + os.path.basename(filename).split(".")[0]
                    + "_dQdV-plot"
                )
                self.save_fig(fig, savepath)

    def plot_gc_and_dQdV(self):
        """Takes all the parameters inserted in the object creation and plots Voltage-Curves and dQdV data together"""
        from cellpy.utils import ica

        if self.kwargs["all_in_one"]:  # Everything goes in the same figure.
            fig, ax = self.give_fig()
            fig.delaxes(ax)
            ax1, ax2 = fig.subplots(1, 2, sharey=True)
            fig.set_size_inches(8, 4)
            fig.subplots_adjust(wspace=0)

            colors = [
                         "tab:blue",
                         "tab:orange",
                         "tab:green",
                         "tab:red",
                         "tab:purple",
                         "tab:brown",
                         "tab:pink",
                         "tab:gray",
                         "tab:olive",
                         "tab:cyan",
                     ] * 5
            savepath = self.outpath

            colorbar_incrementor = -1
            for cpobj, cyc_nums, color, filename in self.file_data:

                # Get Pandas DataFrame of pot vs cap from cellpy object
                df = cpobj.get_cap(
                    method="forth-and-forth",
                    label_cycle_number=True,
                    categorical_column=True,
                )

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    cbaxes = fig.add_axes(
                        [1.05 + colorbar_incrementor / 8, 0.1, 0.03, 0.8]
                    )
                    colorbar_incrementor += 1
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                        cax=cbaxes,
                        label="Cycle number for "
                              + os.path.basename(filename).split(".")[0],
                        pad=0.2,
                    )

                # Plot GC in leftmost plot (ax)
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        if (
                            not self.kwargs["only_dischg"]
                            and not self.kwargs["only_chg"]
                        ):
                            ax1.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"]:
                            dchg = cyc_df.groupby("direction")
                            dchg_df = dchg.get_group(-1)
                            ax1.plot(
                                dchg_df["capacity"],
                                dchg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_chg"]:
                            chg = cyc_df.groupby("direction")
                            chg_df = chg.get_group(1)
                            ax1.plot(
                                chg_df["capacity"],
                                chg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )

                # Get Pandas DataFrame for dQdV
                if self.kwargs["only_dischg"]:
                    _, df = ica.dqdv_frames(cpobj, split=True)
                elif self.kwargs["only_chg"]:
                    df, _ = ica.dqdv_frames(cpobj, split=True)
                else:
                    df = ica.dqdv_frames(cpobj)

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Plot cycles
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        ax2.plot(
                            cyc_df["dq"],
                            cyc_df["voltage"],
                            label=os.path.basename(filename).split(".")[0]
                                  + ", Cyc "
                                  + str(cyc),
                            c=cyccolor,
                        )
                savepath += os.path.basename(filename).split(".")[0]

            # Set all plot settings from Plot object
            fig.suptitle("GC and dQdV")
            self.fix_gc_and_dqdv(fig, [ax1, ax2])

            # Save fig
            savepath = savepath + "_GC-dQdV-plot"
            self.save_fig(fig, savepath)

        else:  # Then all files are placed in separate plots
            for cpobj, cyc_nums, color, filename in self.file_data:
                fig, ax = self.give_fig()
                fig.delaxes(ax)
                ax1, ax2 = fig.subplots(1, 2, sharey=True)
                fig.set_size_inches(8, 4)
                fig.subplots_adjust(wspace=0)

                colors = [
                             "tab:blue",
                             "tab:orange",
                             "tab:green",
                             "tab:red",
                             "tab:purple",
                             "tab:brown",
                             "tab:pink",
                             "tab:gray",
                             "tab:olive",
                             "tab:cyan",
                         ] * 5

                # Get Pandas DataFrame of pot vs cap from cellpy object
                df = cpobj.get_cap(
                    method="forth-and-forth",
                    label_cycle_number=True,
                    categorical_column=True,
                )

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Fix colorbar or cycle colors
                if self.kwargs["specific_cycles"] == None:  # Plot all cycles
                    # Set up colormap and add colorbar
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "name", [color, "black"], N=256, gamma=1.0
                    )
                    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
                    fig.colorbar(
                        mpl.cm.ScalarMappable(norm=norm, cmap=cmap), label="Cycle"
                    )

                # Plot GC in leftmost plot (ax)
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        if (
                            not self.kwargs["only_dischg"]
                            and not self.kwargs["only_chg"]
                        ):
                            ax1.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"]:
                            dchg = cyc_df.groupby("direction")
                            dchg_df = dchg.get_group(-1)
                            ax1.plot(
                                dchg_df["capacity"],
                                dchg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_chg"]:
                            chg = cyc_df.groupby("direction")
                            chg_df = chg.get_group(1)
                            ax1.plot(
                                chg_df["capacity"],
                                chg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )

                # Get Pandas DataFrame for dQdV
                if self.kwargs["only_dischg"]:
                    _, df = ica.dqdv_frames(cpobj, split=True)
                elif self.kwargs["only_chg"]:
                    df, _ = ica.dqdv_frames(cpobj, split=True)
                else:
                    df = ica.dqdv_frames(cpobj)

                # Group by cycle and make list of cycle numbers
                cycgrouped = df.groupby("cycle")
                keys = []
                for key, item in cycgrouped:
                    keys.append(key)

                # Plot cycles
                for cyc in keys:
                    if cyc in cyc_nums:
                        if self.kwargs["specific_cycles"]:
                            cyccolor = colors[0]
                            colors = colors[1:]
                        else:
                            cyccolor = cmap(cyc / keys[-1])

                        cyc_df = cycgrouped.get_group(cyc)
                        ax2.plot(
                            cyc_df["dq"],
                            cyc_df["voltage"],
                            label=os.path.basename(filename).split(".")[0]
                                  + ", Cyc "
                                  + str(cyc),
                            c=cyccolor,
                        )

                # Set all plot settings from Plot object
                fig.suptitle(os.path.basename(filename))
                self.fix_gc_and_dqdv(fig, [ax1, ax2])

                # Save fig
                savepath = (
                    self.outpath
                    + os.path.basename(filename).split(".")[0]
                    + "_GC-dQdV-plot"
                )
                self.save_fig(fig, savepath)

        """# Fix colorbar or cycle colors
        if not specific_cycles: # If this is none, then plot all!
            # Set up colormap and add colorbar
            cmap = mpl.colors.LinearSegmentedColormap.from_list("name", [color, "black"], N=256, gamma=1.0)
            norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
            fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),label='Cycle')

        ## Plot GC on the left subplot (ax[0]) ##

        # Get Pandas DataFrame of pot vs cap from cellpy object
        df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)

        # Group by cycle and make list of cycle numbers
        cycgrouped = df.groupby("cycle")
        keys = []
        for key, item in cycgrouped:
            keys.append(key)

        # Plot cycles
        colors =  ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan' ]
        for cyc in keys:
            if cyc in cyc_nums:
                if specific_cycles:
                    cyccolor = colors[0]
                    colors = colors[1:]
                else:
                    cyccolor = cmap(cyc/keys[-1])
                cyc_df = cycgrouped.get_group(cyc)
                axs[0].plot(cyc_df["capacity"], cyc_df["voltage"], label="Cycle " + str(cyc), c = cyccolor)


        ## Plot dQdV on the right subplot (ax[1]) ##

        from cellpy.utils import ica
        # Get Pandas DataFrame of pot vs cap from cellpy object
        df = ica.dqdv_frames(cpobj)

        # Group by cycle and make list of cycle numbers
        cycgrouped = df.groupby("cycle")
        keys = []
        for key, item in cycgrouped:
            keys.append(key)

        # Plot cycles
        colors =  ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan' ]
        for cyc in keys:
            if cyc in cyc_nums:
                if specific_cycles:
                    cyccolor = colors[0]
                    colors = colors[1:]
                else:
                    cyccolor = cmap(cyc/keys[-1])
                cyc_df = cycgrouped.get_group(cyc)
                axs[1].plot(cyc_df["dq"], cyc_df["voltage"], label=str(cyc), c = cyccolor)

        # Set all plot settings from Plot object
        fig.suptitle(os.path.basename(file))
        self.fix_gc_and_dqdv(fig, axs)

        # Save fig
        savepath = self.outpath + os.path.basename(file).split(".")[0] + "_GC-dQdV-plot"
        print("Saving to: " + savepath)
        fig.savefig(savepath, bbox_inches='tight')"""

    def plot_cap_from_rc(self):
        """Takes all the parameters inserted in the object creation and plots capacity VS inverse c-rate"""
        # Spawn fig and axis for plotting
        fig, ax = self.give_fig()

        # Get labels and handles for legend generation and eventual savefile
        handles, labels = ax.get_legend_handles_labels()
        # handles.append(Line2D([0], [0], marker='o', color='black', alpha = 0.2, label = 'Charge capacity', linestyle=''))
        # handles.append(Line2D([0], [0], marker='o', color='black', alpha = 0.2, label = 'Disharge capacity', linestyle=''))
        # handles.append(Line2D([0], [0], marker='+', color='black', label = 'Cap avg per C-rate', linestyle=''))

        outpath = self.outpath
        for cpobj, cyc_nums, color, filename in self.file_data:
            # Get Pandas DataFrame of pot vs cap from cellpy object
            # df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)
            outpath += os.path.basename(filename).split(".")[0] + "_"

            handles.append(
                Line2D([0], [0], marker="o", color=color, label=filename, linestyle="")
            )

            stepstable = cpobj.cell.steps
            chglist, dchglist = get_effective_C_rates_and_caps(stepstable)

            # Remove all cycles which are not in cyc_nums by looking at the 0th element (cyc num) of every sublist in chglist
            new_chglist = [x for x in chglist if x[0] in cyc_nums]
            new_dchglist = [x for x in dchglist if x[0] in cyc_nums]

            linregress_xlist = []
            linregress_ylist = []
            for chg, dchg in zip(new_chglist, new_dchglist):
                # print(dchg)
                # ax.scatter(chg[1] , chg[2] , color = color, alpha = 0.2)
                ax.scatter(1 / dchg[1], dchg[2], color=color, alpha=1)

                linregress_xlist.append(1 / dchg[1])
                linregress_ylist.append(dchg[2])

            # print(linregress_ylist)
            # Fitting curve to the exponential function
            # Import curve fitting package from scipy
            # from scipy.optimize import curve_fit

            x_arr = np.array(linregress_xlist)
            y_arr = np.array(linregress_ylist)

            # Average the capacity for each c-rate
            def _reduce_to_averages(xvals, yvals):
                """This function scans through the data and averages relevant points together."""

                point_grouped = []
                point_lst = []
                dists = []
                for i in range(1, len(xvals)):
                    prev_point = np.array((xvals[i - 1], yvals[i - 1]))
                    curr_point = np.array((xvals[i], yvals[i]))

                    dev = 0.3
                    if (
                        (prev_point * (1 - dev))[0]
                        < curr_point[0]
                        < (prev_point * (1 + dev))[0]
                    ):
                        # If this point is within dev (percentage sort of) of last point, then its in the same c-rate
                        point_lst.append(curr_point)
                    else:
                        # New c-rate
                        point_grouped.append(point_lst)
                        point_lst = []

                print(point_grouped)

                x_arr = []
                y_arr = []

                for group in point_grouped:
                    stacked_arr = np.stack(group, axis=1)
                    averaged_arr = np.average(stacked_arr, axis=1)
                    x_arr.append(averaged_arr[0])
                    y_arr.append(averaged_arr[1])

                print(x_arr)
                print(y_arr)

                return x_arr, y_arr

            # x_arr, y_arr = _reduce_to_averages(x_arr, y_arr)

            # ax.scatter(x_arr, y_arr, marker="+")
            # def _exp_func(x,a,b,c):
            #    return -a* (b**x) + a + -a * (b**(x+c)) +a

            # pars, cov = curve_fit(f=_exp_func, p0 = [50, 0.7, 0], xdata = x_arr, ydata=y_arr, bounds = ([0,0.1, -20],[1e9, 1, 20]))

            # x_vals = np.linspace(min(x_arr), max(x_arr), 100) #x_arr[0], x_arr[-1], 100)
            # ax.plot(x_vals, _exp_func(x_vals, *pars))
            # ax.hlines(max(y_arr), ax.get_xlim()[0], ax.get_xlim()[1], colors = color, linestyle='--')
            # Get the standard deviations of the parameters (square roots of the # diagonal of the covariance)
            # std_dev = np.sqrt(np.diag(cov))
            # Make a sweet legend to put on this
            # handles.append(
            #    Line2D(
            #        [0], [0],
            #        marker="_", color=color,
            #        label = 'Calculated maximum capacity:' + '\n' +'{:.2e} $\pm$ {:.2e}'.format(pars[0], std_dev[0]) + r'$\left[\mu Ah\right]$', linestyle=''
            #        ))

            ax.hlines(
                max(y_arr),
                ax.get_xlim()[0],
                ax.get_xlim()[1],
                colors=color,
                linestyle="--",
            )
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="_",
                    color=color,
                    label="Highest capacity:"
                          + "\n"
                          + "{:.2e}".format(max(y_arr))
                          + r"$\left[\mu Ah\right]$",
                    linestyle="",
                )
            )

        self.fix_cap_from_rc(fig, ax, handles)

        # Save fig
        savepath = outpath + "CapDet"
        self.save_fig(fig, savepath)

    def fix_cyclelife(self, fig, ax):
        """Makes the finishing touches to the cyclelife plot"""
        # Applies kwargs settings and other plot settings

        ## Parameters which could be user defined later
        """
        ax.set(
            xticks = (np.arange(0, 150), step=20)),
            yticks = (np.arange(3, 5, step=0.2)),
            )
        """
        # Get labels and handles for legend generation and eventual savefile
        handles, labels = ax.get_legend_handles_labels()
        if not self.kwargs["only_dischg"]:
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="black",
                    alpha=0.2,
                    label="Charge capacity",
                    linestyle="",
                )
            )

        if self.kwargs["cyclelife_coulombic_efficiency"]:
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="+",
                    color="black",
                    alpha=1,
                    label="Coulombic Efficiency",
                    linestyle="",
                )
            )

        if (
            self.kwargs["cyclelife_charge_c_rate"]
            and not self.kwargs["cyclelife_discharge_c_rate"]
        ):
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="_",
                    color="black",
                    alpha=1,
                    label="Effective charge C-rate",
                    linestyle="",
                )
            )
        elif (
            not self.kwargs["cyclelife_charge_c_rate"]
            and self.kwargs["cyclelife_discharge_c_rate"]
        ):
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="_",
                    color="black",
                    alpha=1,
                    label="Effective discharge C-rate",
                    linestyle="",
                )
            )
        elif (
            self.kwargs["cyclelife_charge_c_rate"]
            and self.kwargs["cyclelife_discharge_c_rate"]
        ):
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="_",
                    color="black",
                    alpha=1,
                    label="Effective charge C-rate",
                    linestyle="",
                )
            )
            handles.append(
                Line2D(
                    [0],
                    [0],
                    marker="_",
                    color="black",
                    alpha=0.2,
                    label="Effective discharge C-rate",
                    linestyle="",
                )
            )

        # The params below should always be like this.
        ax.tick_params(direction="in", top="true", right="true")
        ax.xaxis.get_major_locator().set_params(integer=True)

        # Apply all kwargs to plot
        try:
            # Cyclelife plot details
            ax.set(xlabel=self.kwargs["cyclelife_xlabel"])
            if self.kwargs["cyclelife_percentage"]:
                ax.set(ylabel=self.kwargs["cyclelife_ylabel_percent"])
            else:
                ax.set(ylabel=self.kwargs["cyclelife_ylabel"])

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                fig.suptitle(self.kwargs["figtitle"])
            else:
                fig.suptitle("Capacity versus Cycle life")

        except Exception as e:
            logging.error(e)

        # Take care of having the legend outside the plot
        if self.kwargs["cyclelife_legend_outside"]:
            if (
                self.kwargs["cyclelife_coulombic_efficiency"]
                or self.kwargs["cyclelife_charge_c_rate"]
                or self.kwargs["cyclelife_discharge_c_rate"]
            ):
                ax.legend(handles=handles, bbox_to_anchor=(1.18, 1), loc="upper left")
            else:
                ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc="upper left")

            figsize = self.kwargs["figsize"]
            fig.set_size_inches((figsize[0] + 3, figsize[1]))
        else:
            ax.legend(handles=handles)
        fig.tight_layout()  # Needed to not clip ylabel on coulombic efficiency

    def fix_cap_from_rc(self, fig, ax, handles):
        """Makes the finishing touches to the capacity vs inverse C-rate plot"""
        ax.tick_params(direction="in", top="true", right="true")
        ax.set(
            xlabel=r"Inverse C-rate $\left[ h \right]$",
            ylabel=r"Capacity $\left[\mu Ah \right]$",
        )
        # General plot details
        fig.set_size_inches(self.kwargs["figsize"])
        if type(self.kwargs["figtitle"]) == str:
            fig.suptitle(self.kwargs["figtitle"])
        else:
            fig.suptitle("Capacity determination from Rate Capability")

        # Take care of having the legend outside the plot
        if self.kwargs["cyclelife_legend_outside"]:
            ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc="upper left")

            figsize = self.kwargs["figsize"]
            fig.set_size_inches((figsize[0] + 3, figsize[1]))
        else:
            ax.legend(handles=handles)
        fig.tight_layout()  # Needed to not clip ylabel on coulombic efficiency

    def fix_gc(self, fig, ax):
        """Makes the finishing touches to the voltage-curves plot"""
        # Applies kwargs settings and other plot settings

        ## Parameters which could be user defined later
        """
        ax.set(
            xticks = (np.arange(0, 150), step=20)),
            yticks = (np.arange(3, 5, step=0.2)),
            )
        """

        # The params below should always be like this.
        ax.tick_params(direction="in", top="true", right="true")

        # Apply all kwargs to plot
        try:
            # Galvanostatic plot details
            ax.set(xlabel=self.kwargs["galvanostatic_xlabel"])
            ax.set(ylabel=self.kwargs["galvanostatic_ylabel"])
            ax.set(ylim=self.kwargs["galvanostatic_potlim"])
            ax.set(xlim=self.kwargs["galvanostatic_caplim"])

            if self.kwargs["specific_cycles"] != None:
                ax.legend()

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                fig.suptitle(self.kwargs["figtitle"])

        except Exception as e:
            logging.error(e)

    def fix_dqdv(self, fig, ax):
        """Makes the finishing touches to the dQdV plot"""
        # Applies kwargs settings and other plot settings

        ## Parameters which could be user defined later
        """
        ax.set(
            xticks = (np.arange(0, 150), step=20)),
            yticks = (np.arange(3, 5, step=0.2)),
            )
        """

        # The params below should always be like this.
        ax.tick_params(direction="in", top="true", right="true")

        # Apply all kwargs to plot
        try:
            # Cyclelife plot details
            ax.set(xlabel=self.kwargs["dqdv_xlabel"])
            ax.set(ylabel=self.kwargs["dqdv_ylabel"])
            ax.set(ylim=self.kwargs["dqdv_dqlim"])
            ax.set(xlim=self.kwargs["dqdv_potlim"])

            if self.kwargs["specific_cycles"] != None:
                ax.legend()

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                fig.suptitle(self.kwargs["figtitle"])

        except Exception as e:
            logging.error(e)

    def fix_gc_and_dqdv(self, fig, axs):
        """Makes the finishing touches to the dQdV / Voltage curves plot"""
        for ax in axs:
            # The params below should always be like this.
            ax.tick_params(direction="in", top="true", right="true")

        # Apply all kwargs to plot
        try:
            # dQdV plot details
            axs[1].set(
                xlabel=self.kwargs["dqdv_ylabel"]
            )  # switched x and y label since this dQdV plot is flipped to match the adjacent gc plot
            axs[1].set(ylabel="")  # Empty since we already have potential on gc axs
            axs[1].set(ylim=self.kwargs["galvanostatic_potlim"])
            axs[1].set(xlim=self.kwargs["dqdv_dqlim"])

            # Galvanostatic plot details
            axs[0].set(xlabel=self.kwargs["galvanostatic_xlabel"])
            axs[0].set(ylabel=self.kwargs["galvanostatic_ylabel"])
            axs[0].set(ylim=self.kwargs["galvanostatic_potlim"])
            axs[0].set(xlim=self.kwargs["galvanostatic_caplim"])

            if self.kwargs["specific_cycles"] != None:
                axs[0].legend()

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                fig.suptitle(self.kwargs["figtitle"])

        except Exception as e:
            print(e)
            logging.error(e)

    def save_fig(self, fig, savepath):
        """The point of this is to have savefig parameters the same across
        all plots (for now just fig dpi and bbox inches)"""
        if self.kwargs.get("save_figures", True):
            if self.kwargs["outname"]:
                savepath = (
                    self.kwargs["outpath"]
                    + self.kwargs["outname"]
                    + self.kwargs["outtype"]
                )
            else:
                savepath += self.kwargs["outtype"]

            print("Saving to: " + savepath)
            fig.savefig(savepath, bbox_inches="tight", dpi=self.kwargs["figres"])


def get_effective_C_rates(steptable):

    newdf = steptable[["step_time_avr", "cycle", "type"]]
    chg_c_rates = []
    dchg_c_rates = []
    for i, elem in enumerate(newdf.iterrows()):
        if elem[1]["type"] == "charge":
            chg_c_rates.append(1 / (elem[1]["step_time_avr"] / 3600))
        elif elem[1]["type"] == "discharge":
            dchg_c_rates.append(1 / (elem[1]["step_time_avr"] / 3600))

    return chg_c_rates, dchg_c_rates


def get_effective_C_rates_and_caps(steptable):
    newdf = steptable[
        ["step_time_avr", "cycle", "type", "charge_avr", "discharge_last"]
    ]
    chglist = (
        []
    )  # [[cycle, chg_crate, chg_cap], [cycle increase with crates and capacities for this cycle]]
    dchglist = []
    for i, elem in enumerate(newdf.iterrows()):
        cyc = elem[1]["cycle"]

        if elem[1]["type"] == "charge":
            chglist.append(
                [
                    cyc,
                    1 / (elem[1]["step_time_avr"] / 3600),
                    elem[1]["charge_avr"] * 1000,
                ]
            )
        elif elem[1]["type"] == "discharge":
            dchglist.append(
                [
                    cyc,
                    1 / (elem[1]["step_time_avr"] / 3600),
                    elem[1]["discharge_last"] * 1000 * 1000,
                ]
            )

    return chglist, dchglist


def main():
    log.setup_logging(default_level="DEBUG")
    f1 = Path("../../testdata/data/20160805_test001_45_cc_01.res")
    f2 = Path("../../testdata/data/20160805_test001_47_cc_01.res")

    raw_files = [f1, f2]
    nicknames = ["cell1", "cell2"]

    logging.debug(raw_files)
    logging.debug(nicknames)

    ezplt = EasyPlot(raw_files, nicknames, figtitle="Test1", save_figures=True)
    ezplt.plot()
    plt.show()

    return


def _dev_journal_loading():
    log.setup_logging(default_level="DEBUG")
    journal_file = Path("../../testdata/db/cellpy_batch_test.json")
    ezplt = EasyPlot(
        None,
        journal=journal_file,
        figtitle="Test1",
        save_figures=False,
        save_journal=True,
        outpath="./tmp/",
    )
    ezplt.plot()
    # plt.show()

    return


if __name__ == "__main__":
    print(" running easyplot ".center(80, "-"))
    _dev_journal_loading()
    print(" finished ".center(80, "-"))
