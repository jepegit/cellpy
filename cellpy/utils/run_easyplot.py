# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    from cellpy.utils import easyplot

    files = [   "./data/raw/20160805_test001_45_cc_01.res",
                "./data/raw/20160805_test001_45_cc_01_copy.res"]

    easyplot.plot(files,
        cyclelifeplot = True,
        cyclelife_xlabel = "Cycles",
        cyclelife_ylabel = "Capacity [mAh/g]",
        cyclelife_ylabel_percent = "Capacity retention [%]",
        cyclelife_coulombic_efficiency = True,
        cyclelife_percentage = False,
        galvanostatic_plot = True,
        galvanostatic_potlim = (0,1),     #min and max limit on potential-axis
        galvanostatic_caplim = None,
        galvanostatic_xlabel = "Capacity [mAh/g]",
        galvanostatic_ylabel = "Cell potential [V]",
        specific_cycles = [1, 2, 5, 10],
        dqdvplot = False,       # NOT YET IMPLEMENTED
        outpath = "./",
        figsize = (6,4), # 6 inches wide, 4 inches tall
        figtitle = None, # None = original filepath
    )