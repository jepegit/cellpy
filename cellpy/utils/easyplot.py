# Author: Amund M. Raniseth
# Date: 01.07.2021

import os
from pathlib import Path
import logging
import cellpy
from matplotlib.artist import kwdoc
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import numpy as np



#### WORK IN PROGRESS ####

def help():
    ## Prints out help page of this module
    help_str =   """The easyplot extension to cellpy aims to easily plot data in a pretty manner\n
In order to use this function, you must import cellpy, and easyplot from cellpy.utils.\n
\n
Usage:\n
Create list of datafiles you want to plot on the following format:\n
files = [\n
\t'./folder/filename.ext',\n
\t'./folder/filename2.ext',\n
\t]\n
\n
And then call the easyplot.plot function with the files list as the first parameter, and any optional keyword arguments.\n
Here is an example of the use of all keyword arguments:\n"""
    g = G(["?", "?"])
    for kw in g.user_params:
        if type(g.user_params[kw][1]) == str:
            insert = "'"+g.user_params[kw][1] + "'"
        else:
            insert = str(g.user_params[kw][1])
        help_str += "\t" + kw + " = " + insert + ",\n"
    print(help_str)


def plot(files, **kwargs):
    g = G(files, **kwargs)                      # Spawn obj for handling global params
    outpath = handle_outpath(g.outpath) # Takes care of the output path
    cyclelifeplotobjects = []                   # Something to store the objects in
    specific_cycles = False                     # TODO: This should be better implemented, especially when feature for file-individual cycle selection is implemented.
    print(kwargs)
    for file in g.files:
        plot = Plot(**kwargs)                       # Initialize file-individual plot object

        # Get the data
        cpobj = cellpy.get(filename = file, instrument="arbin_sql_csv")     # Initiate cellpy object
        cyc_nums = cpobj.get_cycle_numbers()    # Get ID of all cycles
        if kwargs["specific_cycles"] != None:   # Only get the cycles which both exist in data, and that the user want
            cyc_nums = list(set(cyc_nums).intersection(kwargs["specific_cycles"])) 
            specific_cycles = True
        else:
            specific_cycles = False
        
        color = g.give_color()               # Get a color for the data
        
        # Plot whatever the user want
        if kwargs["cyclelifeplot"] == True :
            cyclelifeplotobjects.append((cpobj, cyc_nums, color, file)) # Remember that tuples are immutable

        if kwargs["galvanostatic_plot"] == True and kwargs["dqdvplot"] == False:
            plot_gc(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles)

        if kwargs["dqdvplot"] == True and kwargs["galvanostatic_plot"] == False:
            plot_dQdV(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles)

        if kwargs["galvanostatic_plot"] == True and kwargs["dqdvplot"] == True:
            plot_gc_and_dQdV(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles)

    # If the user want cyclelife plot, we do it to all the input files.
    if kwargs["cyclelifeplot"] == True:
        plot_cyclelife(cyclelifeplotobjects, **kwargs)

def plot_cyclelife(cyclelifeplotobjects, **kwargs):
    # Initialize custom plot obj and matplotlib fig and ax objects
    plot = Plot(**kwargs)
    fig, ax = plt.subplots(figsize=(6, 4))
    outpath = kwargs["outpath"]


    for cpobj, cyc_nums, color, filename in cyclelifeplotobjects:
        # Get Pandas DataFrame of pot vs cap from cellpy object
        df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)
        outpath += os.path.basename(filename).split(".")[0] + "_"

        # Group by cycle and make list of cycle numbers
        cycgrouped = df.groupby("cycle")
        keys = []
        for key, item in cycgrouped:
            keys.append(key)

        chgs = [[],[]] #List with cycle num and capacity
        dchgs = [[],[]]
        # Accumulate cycles
        for cyc in keys: #Loop over all cycles
            if cyc in cyc_nums: #Check if it is in list of wanted cycles
                cyc_df = cycgrouped.get_group(cyc)  #Get the group of datapoints from specific cycle

                cyc_redox_grouped = cyc_df.groupby("direction") # Group by direction (meaning if it is charging or discharging)

                dchg_df = cyc_redox_grouped.get_group(-1)           # Data for the discharge curve
                dchgs[0].append(cyc)    # Append to dchg list
                dchgs[1].append(dchg_df["capacity"].iat[-2])    

                chg_df = cyc_redox_grouped.get_group(1)             # Data for the charge curve
                chgs[0].append(cyc)      # Append to chg list
                chgs[1].append(chg_df["capacity"].iat[-2])

        if kwargs["cyclelife_percentage"] == True: # Normalize all datapoints on the first one
            norm_fact = dchgs[1][0]/100 # /100 is to get range from 0-100(%) in stead of 0-1
            for i in range(len(chgs[1])):
                chgs[1][i] /= norm_fact
            for i in range(len(dchgs[1])):
                dchgs[1][i] /= norm_fact

        # Actully place it in plot
        ax.scatter(chgs[0], chgs[1], c = color, alpha = 0.2, )
        ax.scatter(dchgs[0], dchgs[1], c = color, label = str(os.path.basename(filename)))

    if kwargs["cyclelife_coulombic_efficiency"] == True:
        ax_ce = ax.twinx()
        ax_ce.set(ylabel = kwargs["cyclelife_coulombic_efficiency_ylabel"])
        coulombic_efficiency = cpobj.cell.summary["coulombic_efficiency_u_percentage"]
        ax_ce.scatter(range(len(coulombic_efficiency)), coulombic_efficiency, c = color, marker = "+")


    # Get labels and handles for legend generation and eventual savefile
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], marker='o', color='black', alpha = 0.2, label = 'Charge capacity', linestyle=''))
    if kwargs["cyclelife_coulombic_efficiency"] == True:
        handles.append(Line2D([0], [0], marker='+', color='black', alpha = 1, label = 'Coulombic Efficiency', linestyle=''))
    

    # Set all plot settings from Plot object
    plot.fix_cyclelife(fig, ax) #This done first since we need to adjust figsize afterwords if the legend is to be placed outside
    if kwargs["cyclelife_legend_outside"] == True:
        if kwargs["cyclelife_coulombic_efficiency"] == True:
            ax.legend(handles=handles, bbox_to_anchor=(1.15, 1), loc='upper left')
        else:
            ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left')

        figsize = kwargs["figsize"]
        fig.set_size_inches((figsize[0]+3, figsize[1]))
    else:
        ax.legend(handles=handles)
    fig.suptitle("Capacity versus Cycle life")
    fig.tight_layout() #Needed to not clip ylabel on coulombic efficiency

    # Save fig
    savepath = outpath.strip("_") + "_Cyclelife.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')

def plot_gc_and_dQdV(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles):
    ### WIP ###

    fig, axs = plt.subplots(1, 2, sharey=True, figsize=(8, 4))
    fig.subplots_adjust(wspace=0)

    # Fix colorbar or cycle colors
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
            axs[0].plot(cyc_df["capacity"], cyc_df["voltage"], label="Cycle" + str(cyc), c = cyccolor)
    

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
    fig.suptitle(file)
    plot.fix_dqdv(fig, axs[1])
    axs[1].set(ylabel="") # Fix func sets ylabel, but here it is the same as galvanostatic x-label so it can be removed
    plot.fix(fig, axs[0])

    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_GC-dQdV-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')
    #print("DO NOT ASK FOR BOTH GALVANOSTATIC AND DQDV PLOTS AT THE SAME TIME, THE FEATURE HAS NOT BEEN IMPLEMENTED")
    #raise NotImplementedError

def plot_dQdV(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles):
    from cellpy.utils import ica
    # Get Pandas DataFrame of pot vs cap from cellpy object
    df = ica.dqdv_frames(cpobj)

    # Group by cycle and make list of cycle numbers
    cycgrouped = df.groupby("cycle")
    keys = []
    for key, item in cycgrouped:
        keys.append(key)

    # Create the plot obj
    fig, ax = plt.subplots(figsize=(6, 4))

    # Fix colorbar or cycle colors
    if not specific_cycles: # If this is none, then plot all!
        # Set up colormap and add colorbar
        cmap = mpl.colors.LinearSegmentedColormap.from_list("name", [color, "black"], N=256, gamma=1.0)
        norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),label='Cycle')

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
            ax.plot(cyc_df["dq"], cyc_df["voltage"], label=str(cyc), c = cyccolor)

    # Set all plot settings from Plot object
    fig.suptitle(os.path.basename(file))
    plot.fix_dqdv(fig, ax)

    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_dQdV-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')
    

def plot_gc(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles):

    # Get Pandas DataFrame of pot vs cap from cellpy object
    df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)

    # Group by cycle and make list of cycle numbers
    cycgrouped = df.groupby("cycle")
    keys = []
    for key, item in cycgrouped:
        keys.append(key)

    # Create the plot obj
    fig, ax = plt.subplots(figsize=(6, 4))

    # Fix colorbar or cycle colors
    if not specific_cycles: # If this is none, then plot all!
        # Set up colormap and add colorbar
        cmap = mpl.colors.LinearSegmentedColormap.from_list("name", [color, "black"], N=256, gamma=1.0)
        norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),label='Cycle')

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
            ax.plot(cyc_df["capacity"], cyc_df["voltage"], label="Cycle" + str(cyc), c = cyccolor)

    # Set all plot settings from Plot object
    fig.suptitle(os.path.basename(file))
    plot.fix(fig, ax)


    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_GC-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')


# Global class for holding input variables and filenames
class G:
    def __init__(self, files, **kwargs):
        # Make all kwargs variables of self
        for key in kwargs:
            setattr(self, key, kwargs[key])

        # Make list of files a variable of self
        self.files = files


        # List of available colors
        self.colors =  ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan' ]

        # Dictionary of all possible user input arguments(as keys) with example values of correct type
        # Value is a tuple (immutable) of type and default value.
        self.user_params = {
            "cyclelife_plot"                        : (bool, True),
            "cyclelife_percentage"                  : (bool, False),
            "cyclelife_coulombic_efficiency"        : (bool, False),
            "cyclelife_coulombic_efficiency_ylabel" : (str, "Coulombic efficiency [%]"),
            "cyclelife_xlabel"                      : (str, "Cycles"),
            "cyclelife_ylabel"                      : (str, "Capacity [mAh/g]"),
            "cyclelife_ylabel_percent"              : (str, "Capacity retention [%]"),
            "cyclelife_legend_outside"              : (bool, False), # if True, the legend is placed outside the plot
            "galvanostatic_plot"    : (bool, True),
            "galvanostatic_potlim"  : (tuple, None),     #min and max limit on potential-axis
            "galvanostatic_caplim"  : (tuple, None),
            "galvanostatic_xlabel"  : (str, "Capacity [mAh/g]"),
            "galvanostatic_ylabel"  : (str, "Cell potential [V]"),
            "dqdvplot"          : (bool, False),
            "dqdvplot_potlim"   : (tuple, None),     #min and max limit on potential-axis
            "dqdvplot_dqlim"    : (tuple, None),
            "dqdvplot_xlabel"   : (str, "dQ/dV [?]"), # TODO what unit? jees
            "dqdvplot_ylabel"   : (str, "Cell potential [V]"),
            "specific_cycles"   : (list, None),
            "outpath"   : (str, "./"),
            "figsize"   : (tuple, (6,4)), # 6 inches wide, 4 inches tall
            "figtitle"  : (str, "Title"), # None = original filepath
        }


    def verify_input():
        # File handling
        for file in self.files:
            if not os.path.isfile(file):
                logging.error("File not found: " + str(file))
                raise FileNotFoundError

        ### Check that all kwargs are used correctly ###

        # categorize all kwargs by self.user_params (which has the correct formatting)
        for key in self.kwargs:
            if not self.user_params[key]:
                logging.error("Input parameter " + key + " is not a valid parameter! Please see example configuration for help or run easyplot.help()")
            if type(self.kwargs[key]) == self.user_params[key][0]:
                logging.error("Type of inputparameter for keyword " + key + " is wrong. The user specified " + str(type(self.kwargs[key])) + " but the program needs a " + str(self.user_params[key][0]))
                raise TypeError

    def give_color(self):
        # Picks the first color from the color list and gives it away
        color = self.colors[0]
        self.colors=self.colors[1:]
        return color
    

class Plot:
    def __init__(self, **kwargs):
        # Set all kwargs as self.kwarg vars
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.kwargs = kwargs
    

    def fix(self, fig, ax):
        # Applies kwargs settings and other plot settings

        ## Parameters which could be user defined later
        """
        ax.set(
            xticks = (np.arange(0, 150), step=20)),
            yticks = (np.arange(3, 5, step=0.2)),
            )
        """

        # The params below should always be like this.
        ax.tick_params(direction='in', top = 'true', right = 'true')

        # Apply all kwargs to plot
        try:
            # Galvanostatic plot details
            ax.set(xlabel = self.kwargs["galvanostatic_xlabel"])
            ax.set(ylabel = self.kwargs["galvanostatic_ylabel"])
            ax.set(ylim = self.kwargs["galvanostatic_potlim"])
            ax.set(xlim = self.kwargs["galvanostatic_caplim"])

            if self.kwargs["specific_cycles"] != None:
                    ax.legend()

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                    fig.suptitle(self.kwargs["figtitle"])
        except Exception as e:
            logging.error(e)
                

    def fix_cyclelife(self, fig, ax):
        # Applies kwargs settings and other plot settings

        ## Parameters which could be user defined later
        """
        ax.set(
            xticks = (np.arange(0, 150), step=20)),
            yticks = (np.arange(3, 5, step=0.2)),
            )
        """

        # The params below should always be like this.
        ax.tick_params(direction='in', top = 'true', right = 'true')

        # Apply all kwargs to plot
        try:
            # Cyclelife plot details
            ax.set(xlabel = self.kwargs["cyclelife_xlabel"])
            if self.kwargs["cyclelife_percentage"] == True:
                ax.set(ylabel =self.kwargs["cyclelife_ylabel_percent"])
            else:
                ax.set(ylabel = self.kwargs["cyclelife_ylabel"])

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
        ax.tick_params(direction='in', top = 'true', right = 'true')

        # Apply all kwargs to plot
        try:
            # Cyclelife plot details
            ax.set(xlabel = self.kwargs["dqdvplot_xlabel"])
            ax.set(ylabel = self.kwargs["dqdvplot_ylabel"])
            ax.set(ylim = self.kwargs["dqdvplot_potlim"])
            ax.set(xlim = self.kwargs["dqdvplot_caplim"])

            # General plot details
            fig.set_size_inches(self.kwargs["figsize"])
            if type(self.kwargs["figtitle"]) == str:
                fig.suptitle(self.kwargs["figtitle"])
        except Exception as e:
            logging.error(e)

def handle_outpath(dictval):
    if os.path.isdir(dictval):
        return dictval
    elif not os.path.isdir(dictval):
        try:
            os.mkdir(dictval)
            return dictval
        except OSError as e:
            print("Cannot create output directory " + dictval + ". Please make sure you have write permission.")
            print(e)
            exit()