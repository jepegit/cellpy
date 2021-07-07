# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    from cellpy.utils import easyplot

    files = [   
            #"./data/raw/20160805_test001_45_cc_01.res",
            "./data/seam12/20210628_seam12_04_01_cc_01_2021_06_29_152933/20210628_seam12_04_01_cc_01_Channel_48_Wb_1.CSV",
            ]

    easyplot.plot(files,
        cyclelife_plot = True,
        cyclelife_percentage = False,
        cyclelife_coulombic_efficiency = False,
        cyclelife_coulombic_efficiency_ylabel = "Coulombic efficiency [%]",
        cyclelife_xlabel = "Cycles",
        cyclelife_ylabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        cyclelife_ylabel_percent = "Capacity retention [%]",
        cyclelife_legend_outside = False, # if True, the legend is placed outside the plot
        galvanostatic_plot = True,
        galvanostatic_potlim = (0,1),     #min and max limit on potential-axis
        galvanostatic_caplim = None,
        galvanostatic_xlabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        galvanostatic_ylabel = "Cell potential [V]",
        dqdv_plot = True,
        dqdv_potlim = (0,1),     #min and max limit on potential-axis
        dqdv_dqlim = None,
        dqdv_xlabel = r"dQ/dV $\left[\frac{mAh}{gV}\right]$", # TODO what unit? jees
        dqdv_ylabel = "Cell potential [V]",
        specific_cycles = None, #[1, 2, 5, 10],
        outpath = "./",
        figsize = (6,4), # 6 inches wide, 4 inches tall
        figtitle = None, # None = original filepath
    )