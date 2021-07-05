# Author: Amund M. Raniseth
# Date: 01.07.2021

import os
from pathlib import Path
import logging
import cellpy
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import numpy as np



#### WORK IN PROGRESS ####

def plot(files, **kwargs):
    g = G()                                     # Get obj for handling global params
    outpath = handle_outpath(kwargs["outpath"]) # Takes care of the output path
    cyclelifeplotobjects = []                   # Something to store the objects in
    specific_cycles = False

    for file in files:
        plot = Plot(**kwargs)                       # Initialize plot object

        # Get the data
        cpobj = cellpy.get(filename = file)     # Initiate cellpy object
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
            plot_galvanostatic(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles)

        if kwargs["dqdvplot"] == True and kwargs["galvanostatic_plot"] == False:
            plot_dQdV(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles)

        if kwargs["galvanostatic_plot"] == True and kwargs["dqdvplot"] == True:
            plot_gc_and_dQdV(cpobj, cyc_nums, color, plot, file, outpath)


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
        ax.scatter(dchgs[0], dchgs[1], c = color, label = str(filename))


    # Get labels and handles for legend generation and eventual savefile
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], marker='o', color='black', alpha = 0.2, label = 'Charge capacity', linestyle=''))
    ax.legend(handles=handles)

    # Set all plot settings from Plot object
    plot.fix_cyclelife(fig, ax)
    fig.suptitle("Capacity versus Cycle life")

    # Save fig
    savepath = outpath.strip("_") + "_Cyclelife.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')

def plot_gc_and_dQdV(cpobj, cyc_nums, color, plot, file, outpath):
    # Get Pandas DataFrame of pot vs cap from cellpy object
    df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)

    # Group by cycle and make list of cycle numbers
    cycgrouped = df.groupby("cycle")
    keys = []
    for key, item in cycgrouped:
        keys.append(key)

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
    plot.fix(fig, ax)
    fig.suptitle(file)


    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_dQdV-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')
    

def plot_galvanostatic(cpobj, cyc_nums, color, plot, file, outpath, specific_cycles):

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
    plot.fix(fig, ax)
    fig.suptitle(file)


    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_GC-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')


# Global class for when differentiation between testdata is needed
class G:
    def __init__(self):
        # List of available colors
        self.colors =  ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan' ]


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
        for kwarg in self.kwargs:
            # Galvanostatic plot details
            if kwarg == "galvanostatic_xlabel":
                ax.set(xlabel = self.kwargs["galvanostatic_xlabel"])
            elif kwarg == "galvanostatic_ylabel":
                ax.set(ylabel = self.kwargs["galvanostatic_ylabel"])
            elif kwarg == "galvanostatic_potlim":
                ax.set(ylim = self.kwargs["galvanostatic_potlim"])
            elif kwarg == "galvanostatic_caplim":
                ax.set(xlim = self.kwargs["galvanostatic_caplim"])
            elif kwarg == "specific_cycles":
                if self.kwargs["specific_cycles"] != None:
                    ax.legend()
            
            # General plot details
            elif kwarg == "figsize":
                fig.set_size_inches(self.kwargs["figsize"])
            elif kwarg == "figtitle":
                if type(self.kwargs["figtitle"]) == str:
                    fig.suptitle(self.kwargs["figtitle"])

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
        for kwarg in self.kwargs:
            # Cyclelife plot details
            if kwarg == "cyclelife_xlabel":
                ax.set(xlabel = self.kwargs["cyclelife_xlabel"])
            elif kwarg == "cyclelife_ylabel":
                ax.set(ylabel = self.kwargs["cyclelife_ylabel"])
            elif kwarg == "cyclelife_percentage":
                if self.kwargs["cyclelife_percentage"] == True:
                    ax.set(ylabel = self.kwargs["cyclelife_ylabel_percent"])
            
            # General plot details
            elif kwarg == "figsize":
                fig.set_size_inches(self.kwargs["figsize"])
            elif kwarg == "figtitle":
                if type(self.kwargs["figtitle"]) == str:
                    fig.suptitle(self.kwargs["figtitle"])

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