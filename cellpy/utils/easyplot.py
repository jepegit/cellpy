# -*- coding: utf-8 -*-
"""easyplot module for cellpy. It provides easy plotting of any cellpy-readable data using matplotlib.
"""
# Author: Amund M. Raniseth
# Date: 01.07.2021


import os
from pathlib import Path
import logging
import cellpy
from matplotlib import lines
from matplotlib.artist import kwdoc
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import numpy as np
import warnings


class EasyPlot:
    """Main easyplot class.
    Takes all the inputs from the user in its kwargs upon object initialization.
    Gathers data, handles and plots it when object.plot() is called.

    Help: initiate an object and call the object.help() function.
    """

    def __init__(self, files, nicknames, **kwargs):
        """Initialization function of the EasyPlot class. Takes a list of filenames, eventual list of nicknames and kwargs which are supported."""

        # Make all user input variables of self
        self.files = files
        self.nicknames = nicknames
        self.kwargs = kwargs
        self.figs = []
        self.file_data = []
        self.use_arbin_sql = False

        # List of available colors
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

        # Dictionary of all possible user input arguments(as keys) with example values of correct type
        # Value is a tuple (immutable) of type and default value.
        self.user_params = {
            "cyclelife_plot": (bool, True),
            "cyclelife_percentage": (bool, False),
            "cyclelife_coulombic_efficiency": (bool, False),
            "cyclelife_coulombic_efficiency_ylabel": (str, "Coulombic efficiency [%]"),
            "cyclelife_xlabel": (str, "Cycles"),
            "cyclelife_ylabel": (str, r"Capacity $\left[\frac{mAh}{g}\right]$"),
            "cyclelife_ylabel_percent": (str, "Capacity retention [%]"),
            "cyclelife_legend_outside": (
                bool,
                False,
            ),  # if True, the legend is placed outside the plot
            "galvanostatic_plot": (bool, True),
            "galvanostatic_potlim": (
                tuple,
                None,
            ),  # min and max limit on potential-axis
            "galvanostatic_caplim": (tuple, None),
            "galvanostatic_xlabel": (str, r"Capacity $\left[\frac{mAh}{g}\right]$"),
            "galvanostatic_ylabel": (str, "Cell potential [V]"),
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
            "figsize": (tuple, (6, 4)),  # 6 inches wide, 4 inches tall
            "figres": (int, 100),  # Dots per Inch
            "figtitle": (str, "Title"),  # None = original filepath
        }

        # Fill in the rest of the variables from self.user_params if the user didn't specify
        self.fill_input()

        # Verify that the user input is sufficient
        self.verify_input()

    def plot(self):
        """This is the method the user calls on his/hers easyplot object in order to gather the data and plot it."""

        # Load all cellpy files
        for file in self.files:
            # If using arbin sql
            if self.use_arbin_sql:
                cpobj = cellpy.get(
                    filename=file, instrument="arbin_sql"
                )  # Initiate cellpy object
            else:  # Not Arbin SQL? Then its probably a local file
                # Check that file exist
                if not os.path.isfile(file):
                    logging.error("File not found: " + str(file))
                    raise FileNotFoundError
                cpobj = cellpy.get(filename=file)  # Load regular file
                # Check that we get data
            if cpobj == None:
                warnings.warn(
                    "File reader returned no data for filename "
                    + file
                    + ", Please make sure that the file exists or that the data exists in an eventual database."
                )

            # Get ID of all cycles
            cyc_nums = cpobj.get_cycle_numbers()

            if (
                self.kwargs["specific_cycles"] != None
            ):  # Only get the cycles which both exist in data, and that the user want
                cyc_not_available = (
                                        set(cyc_nums) ^ set(self.kwargs["specific_cycles"])
                                    ) & set(self.kwargs["specific_cycles"])
                if len(cyc_not_available) > 0:
                    warn_str = (
                        "You want to plot cycles which are not available in the data! Datafile: "
                        + os.path.basename(file).split(".")[0]
                        + ", Cycle(s): "
                        + str(cyc_not_available)
                    )
                    warnings.warn(warn_str)
                cyc_nums = list(
                    set(cyc_nums).intersection(self.kwargs["specific_cycles"])
                )

            if self.kwargs["exclude_cycles"] != None:
                cyc_nums = list(set(cyc_nums) - set(self.kwargs["exclude_cycles"]))

            color = self.give_color()  # Get a color for the data

            self.file_data.append((cpobj, cyc_nums, color, file))

        # If the user want cyclelife plot, we do it to all the input files.
        if self.kwargs["cyclelife_plot"] == True:
            self.plot_cyclelife()

        if (
            self.kwargs["galvanostatic_plot"] == True
            and self.kwargs["dqdv_plot"] == False
        ):
            self.plot_gc()

        if (
            self.kwargs["dqdv_plot"] == True
            and self.kwargs["galvanostatic_plot"] == False
        ):
            self.plot_dQdV()

        if (
            self.kwargs["galvanostatic_plot"] == True
            and self.kwargs["dqdv_plot"] == True
        ):
            self.plot_gc_and_dQdV()

    def help(self):
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
        for kw in self.user_params:
            if type(self.user_params[kw][1]) == str:
                insert = "'" + self.user_params[kw][1] + "'"
            else:
                insert = str(self.user_params[kw][1])
            help_str += "\t" + kw + " = " + insert + ",\n"
        print(help_str)

    def verify_input(self):

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
        if self.kwargs["only_dischg"] == True and self.kwargs["only_chg"] == True:
            logging.error(
                "You can't plot 'only' discharge AND charge curves! Set one to False please."
            )

    def fill_input(self):
        # Fill in the rest of the variables from self.user_params if the user didn't specify
        # Can't just join dicts since they have differing formats, need to loop...
        for key in self.user_params:
            try:
                self.kwargs[key]
            except KeyError as e:
                self.kwargs[key] = self.user_params[key][1]

    def set_arbin_sql_credentials(
        self, server="localhost", uid="sa", pwd="Changeme123", driver="SQL Server"
    ):
        cellpy.prms.Instruments.Arbin["SQL_server"] = server
        cellpy.prms.Instruments.Arbin["SQL_UID"] = uid
        cellpy.prms.Instruments.Arbin["SQL_PWD"] = pwd
        cellpy.prms.Instruments.Arbin["SQL_Driver"] = driver
        self.use_arbin_sql = True

    def give_color(self):
        # Picks the first color from the color list and gives it away
        color = self.colors[0]
        self.colors = self.colors[1:]
        return color

    def give_fig(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        self.figs.append((fig, ax))
        return (fig, ax)

    def handle_outpath(self):
        if os.path.isdir(self.kwargs["outpath"]):
            return self.kwargs["outpath"]
        elif not os.path.isdir(self.kwargs["outpath"]):
            try:
                os.makedirs(self.kwargs["outpath"])
                return self.kwargs["outpath"]
            except OSError as e:
                logging.error(
                    "Cannot create output directory "
                    + self.kwargs["outpath"]
                    + ". Please make sure you have write permission. Errormessage: "
                    + e
                )

    def plot_cyclelife(self):
        # Spawn fig and axis for plotting
        fig, ax = self.give_fig()
        if self.kwargs["cyclelife_coulombic_efficiency"] == True:
            # Spawn twinx axis and set label
            ax_ce = ax.twinx()
            ax_ce.set(ylabel=self.kwargs["cyclelife_coulombic_efficiency_ylabel"])

        outpath = self.outpath
        for cpobj, cyc_nums, color, filename in self.file_data:
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

            if (
                self.kwargs["cyclelife_percentage"] == True
            ):  # Normalize all datapoints on the first one
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

            # Actully place it in plot
            ax.scatter(
                chgs[0], chgs[1], c=color, alpha=0.2,
            )
            ax.scatter(dchgs[0], dchgs[1], c=color, label=label)

            if self.kwargs["cyclelife_coulombic_efficiency"] == True:
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

        # Get labels and handles for legend generation and eventual savefile
        handles, labels = ax.get_legend_handles_labels()
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
        if self.kwargs["cyclelife_coulombic_efficiency"] == True:
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

        # Set all plot settings from Plot object
        self.fix_cyclelife(fig, ax, handles)

        # Save fig
        savepath = outpath.strip("_") + "_Cyclelife.png"
        self.save_fig(fig, savepath)

    def plot_gc(self):

        if self.kwargs["all_in_one"] == True:  # Everything goes in the same figure.

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
                            self.kwargs["only_dischg"] == False
                            and self.kwargs["only_chg"] == False
                        ):
                            ax.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"] == True:
                            dchg = cyc_df.groupby("direction")
                            dchg_df = dchg.get_group(-1)
                            ax.plot(
                                dchg_df["capacity"],
                                dchg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_chg"] == True:
                            chg = cyc_df.groupby("direction")
                            chg_df = chg.get_group(1)
                            ax.plot(
                                chg_df["capacity"],
                                chg_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )

                savepath += os.path.basename(filename).split(".")[0]

            fig.suptitle("Galvanostatic cyclingdata")
            self.fix_gc(fig, ax)

            # Save fig
            savepath += "_GC-plot.png"
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
                            self.kwargs["only_dischg"] == False
                            and self.kwargs["only_chg"] == False
                        ):
                            ax.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label="Cycle " + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"] == True:
                            dchg = cyc_df.groupby("direction")
                            dchg_df = dchg.get_group(-1)
                            ax.plot(
                                dchg_df["capacity"],
                                dchg_df["voltage"],
                                label="Cycle " + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_chg"] == True:
                            chg = cyc_df.groupby("direction")
                            chg_df = chg.get_group(1)
                            ax.plot(
                                chg_df["capacity"],
                                chg_df["voltage"],
                                label="Cycle " + str(cyc),
                                c=cyccolor,
                            )

                # Set all plot settings from Plot object
                fig.suptitle(os.path.basename(filename))
                self.fix_gc(fig, ax)

                # Save fig
                savepath = (
                    self.outpath
                    + os.path.basename(filename).split(".")[0]
                    + "_GC-plot.png"
                )
                self.save_fig(fig, savepath)

    def plot_dQdV(self):
        from cellpy.utils import ica

        if self.kwargs["all_in_one"] == True:  # Everything goes in the same figure.

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
            savepath += "_dQdV-plot.png"
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
                    + "_dQdV-plot.png"
                )
                self.save_fig(fig, savepath)

    def plot_gc_and_dQdV(self):
        from cellpy.utils import ica

        if self.kwargs["all_in_one"] == True:  # Everything goes in the same figure.
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
                            self.kwargs["only_dischg"] == False
                            and self.kwargs["only_chg"] == False
                        ):
                            ax1.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"] == True:
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
                        elif self.kwargs["only_chg"] == True:
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
            savepath = savepath + "_GC-dQdV-plot.png"
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
                            self.kwargs["only_dischg"] == False
                            and self.kwargs["only_chg"] == False
                        ):
                            ax1.plot(
                                cyc_df["capacity"],
                                cyc_df["voltage"],
                                label=os.path.basename(filename).split(".")[0]
                                      + ", Cyc "
                                      + str(cyc),
                                c=cyccolor,
                            )
                        elif self.kwargs["only_dischg"] == True:
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
                        elif self.kwargs["only_chg"] == True:
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
                    + "_GC-dQdV-plot.png"
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
        savepath = self.outpath + os.path.basename(file).split(".")[0] + "_GC-dQdV-plot.png"
        print("Saving to: " + savepath)
        fig.savefig(savepath, bbox_inches='tight')"""

    def fix_cyclelife(self, fig, ax, handles):
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
        ax.xaxis.get_major_locator().set_params(integer=True)

        # Apply all kwargs to plot
        try:
            # Cyclelife plot details
            ax.set(xlabel=self.kwargs["cyclelife_xlabel"])
            if self.kwargs["cyclelife_percentage"] == True:
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
        if self.kwargs["cyclelife_legend_outside"] == True:
            if self.kwargs["cyclelife_coulombic_efficiency"] == True:
                ax.legend(handles=handles, bbox_to_anchor=(1.18, 1), loc="upper left")
            else:
                ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc="upper left")

            figsize = self.kwargs["figsize"]
            fig.set_size_inches((figsize[0] + 3, figsize[1]))
        else:
            ax.legend(handles=handles)
        fig.tight_layout()  # Needed to not clip ylabel on coulombic efficiency

    def fix_gc(self, fig, ax):
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
        # The point of this is to have savefig parameters the same across all plots (for now just fig dpi and bbox inches)
        print("Saving to: " + savepath)
        fig.savefig(savepath, bbox_inches="tight", dpi=self.kwargs["figres"])
