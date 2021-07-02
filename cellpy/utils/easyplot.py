# Author: Amund M. Raniseth
# Date: 01.07.2021

import os
from pathlib import Path
import logging
import cellpy
import matplotlib.pyplot as plt
import matplotlib as mpl


#### WORK IN PROGRESS ####

def plot(files, **kwargs):
    plot = Plot(**kwargs) #Initialize plot object
    outpath = handle_outpath(kwargs["outpath"]) #Takes care of the output path

    for file in files:
        # Get the data
        cpobj = cellpy.get(filename = file)     # Initiate cellpy object
        cyc_nums = cpobj.get_cycle_numbers()    # Get ID of all cycles
        color = plot.give_color()               # Get a color for the curves
        
        if kwargs["galvanostatic_plot"] == True:
            plot_galvanostatic(cpobj, cyc_nums, color, plot, file, outpath)


def plot_galvanostatic(cpobj, cyc_nums, color, plot, file, outpath):

    # Get Pandas DataFrame of pot vs cap from cellpy object
    df = cpobj.get_cap(method="forth-and-forth", label_cycle_number=True, categorical_column=True)

    # Group by cycle and make list of cycle numbers
    cycgrouped = df.groupby("cycle")
    keys = []
    for key, item in cycgrouped:
        keys.append(key)

    # Create the plot obj
    fig, ax = plt.subplots(figsize=(6, 4))

    # Set up colormap and add colorbar
    cmap = mpl.colors.LinearSegmentedColormap.from_list("name", [color, "black"], N=256, gamma=1.0)
    norm = mpl.colors.Normalize(vmin=cyc_nums[0], vmax=cyc_nums[-1])
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),label='Cycle')

    # Plot cycles
    for cyc in keys:
        cyccolor = cmap(cyc/keys[-1])
        cyc_df = cycgrouped.get_group(cyc)
        if cyc in cyc_nums:   
            ax.plot(cyc_df["capacity"], cyc_df["voltage"], label=str(key), c = cyccolor)

    # Set all plot settings from Plot object
    plot.fix(fig, ax)
    fig.suptitle(file)


    # Save fig
    savepath = outpath + os.path.basename(file).split(".")[0] + "_GC-plot.png" 
    print("Saving to: " + savepath)
    fig.savefig(savepath, bbox_inches='tight')


class Plot:
    def __init__(self, **kwargs):
        # Set all kwargs as self.kwarg vars
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.kwargs = kwargs

        # List of available colors
        self.colors =  ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan' ]

    def give_color(self):
        # Picks the first color from the color list and gives it away
        color = self.colors[0]
        self.colors=self.colors[1:]
        return color

    def fix(self, fig, ax):
        # Applies all the user settings to the fig and axis
        ax.set(
            ylabel = 'Potential [V]',
            xlabel = 'Specific Capacity [mAh/g]',
            #ylim = (2.5,5),
            #xlim = (0, 150),
            #xticks = (np.arange(0, 150), step=20)),
            #yticks = (np.arange(3, 5, step=0.2)),
            )
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
            
            # General plot details
            elif kwarg == "figsize":
                fig.set_size_inches(self.kwargs["figsize"])
            elif kwarg == "figtitle":
                if type(kwargs["figtitle"]) == str:
                    fig.suptitle(kwargs["figtitle"])


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