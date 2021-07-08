# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    from cellpy.utils import easyplot

    files = [   
            "./data/raw/20160805_test001_45_cc_01.res",
            "./data/raw/20160805_test001_45_cc_01_copy.res",
            #"./data/20210430_seam10_01_01_cc_01_Channel_48_Wb_1.xlsx.csv",
            #"./data/20210430_seam10_01_02_cc_01_Channel_49_Wb_1.xlsx.csv"
            ]

    nicknames = ["Seam10_01_01", "Seam10_01_02"]

    ezplt = easyplot.EasyPlot(files, nicknames,
        cyclelife_plot = False,
        cyclelife_percentage = True,
        cyclelife_coulombic_efficiency = False,
        cyclelife_coulombic_efficiency_ylabel = "Coulombic efficiency [%]",
        cyclelife_xlabel = "Cycles",
        cyclelife_ylabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        cyclelife_ylabel_percent = "Capacity retention [%]",
        cyclelife_legend_outside = True, # if True, the legend is placed outside the plot
        galvanostatic_plot = True,
        galvanostatic_potlim = (0,1),     #min and max limit on potential-axis
        galvanostatic_caplim = None,
        galvanostatic_xlabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        galvanostatic_ylabel = "Cell potential [V]",
        dqdv_plot = False,
        dqdv_potlim = (0,1),     #min and max limit on potential-axis
        dqdv_dqlim = None,
        dqdv_xlabel = "Cell potential [V]",
        dqdv_ylabel = r"dQ/dV $\left[\frac{mAh}{gV}\right]$",
        specific_cycles = [1, 2, 5, 10],
        outpath = "./",
        figsize = (6,4), # 6 inches wide, 4 inches tall
        figtitle = None, # None = original filepath
    )
    
    #ezplt.help()
    ezplt.plot()