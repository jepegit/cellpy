# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    from cellpy.utils import easyplot

    files = [   
            "./data/raw/20160805_test001_45_cc_01.res",
            "./data/raw/20160805_test001_45_cc_01_copy.res"
            ]

    easyplot.plot(files,
        cyclelifeplot = True,
        cyclelife_percentage = False,
        cyclelife_coulombic_efficiency = True,
        cyclelife_coulombic_efficiency_ylabel = "Coulombic efficiency [%]",
        cyclelife_xlabel = "Cycles",
        cyclelife_ylabel = "Capacity [mAh/g]",
        cyclelife_ylabel_percent = "Capacity retention [%]",
        cyclelife_legend_outside = False, # if True, the legend is placed outside the plot
        galvanostatic_plot = False,
        galvanostatic_potlim = (0,1),     #min and max limit on potential-axis
        galvanostatic_caplim = None,
        galvanostatic_xlabel = "Capacity [mAh/g]",
        galvanostatic_ylabel = "Cell potential [V]",
        dqdvplot = False,
        dqdvplot_potlim = (0,1),     #min and max limit on potential-axis
        dqdvplot_dqlim = None,
        dqdvplot_xlabel = "dQ/dV [?]", # TODO what unit? jees
        dqdvplot_ylabel = "Cell potential [V]",
        specific_cycles = None, #[1, 2, 5, 10],
        outpath = "./",
        figsize = (6,4), # 6 inches wide, 4 inches tall
        figtitle = None, # None = original filepath
    )