# -*- coding: utf-8 -*-
# This is a test file and will be replaced by a jupyter notebook example in the tutorial section when easyplot functionality is done.

if __name__ == "__main__":
    import cellpy
    import easyplot

    files = [   
            # === SEAM 12 RATE CAPABILITY ===
    #'20210712_seam12_04_rc_01_cc_01',
    #'20210712_seam12_04_rc_02_cc_01',
    #'20210712_seam12_04_rc_03_cc_01',
    #'20210712_seam12_05_rc_01_cc_01',
    #'20210712_seam12_05_rc_02_cc_01',
    #'20210712_seam12_05_rc_03_cc_01',
    #'20210712_seam12_06_rc_01_cc_01',
    #'20210712_seam12_06_rc_02_cc_01',
    #'20210712_seam12_06_rc_03_cc_01',
    #'20210712_seam12_07_rc_01_cc_01',
    #'20210712_seam12_07_rc_02_cc_01',
    #'20210712_seam12_07_rc_03_cc_01',
    # === SEAM 12 1ST GC ===
    '20210628_seam12_04_01_cc_01',
    #'20210628_seam12_04_02_cc_02',
    #'20210628_seam12_04_03_cc_01',
    #'20210628_seam12_05_01_cc_01',
    #'20210628_seam12_05_02_cc_01',
    #'20210628_seam12_05_03_cc_01',
    #'20210628_seam12_06_01_cc_01',
    #'20210628_seam12_06_02_cc_01',
    #'20210628_seam12_06_03_cc_01',
    #'20210628_seam12_07_01_cc_01',
    #'20210628_seam12_07_02_cc_01',
    #'20210628_seam12_07_03_cc_01',
            ]

    nicknames = None  # ["Seam10_01_01", "Seam10_01_02"]

    ezplt = easyplot.EasyPlot(files, nicknames,
        cyclelife_plot = True,
        cyclelife_percentage = False,
        cyclelife_coulombic_efficiency = False,
        cyclelife_coulombic_efficiency_ylabel = "Coulombic efficiency [%]",
        cyclelife_charge_c_rate = True,
        cyclelife_discharge_c_rate = True,
        cyclelife_xlabel = "Cycles",
        cyclelife_ylabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        cyclelife_ylabel_percent = "Capacity retention [%]",
        cyclelife_legend_outside = True, # if True, the legend is placed outside the plot
        capacity_determination_from_ratecap = True,
        galvanostatic_plot = True,
        galvanostatic_potlim = (0,1),     #min and max limit on potential-axis
        galvanostatic_caplim = None,
        galvanostatic_xlabel = r"Capacity $\left[\frac{mAh}{g}\right]$",
        galvanostatic_ylabel = "Cell potential [V]",
        dqdv_plot = True,
        dqdv_potlim = None,     #min and max limit on potential-axis
        dqdv_dqlim = None,
        dqdv_xlabel = "Cell potential [V]",
        dqdv_ylabel = r"dQ/dV $\left[\frac{mAh}{gV}\right]$",
        specific_cycles = None,#[]
        exclude_cycles = None,#[]
        all_in_one = True,
        only_dischg = True,
        only_chg = False,
        outpath = "./ezplots/deleteme/",
        figsize = (6,4), # 6 inches wide, 4 inches tall
        figres = 100, # Dots per inch
        figtitle = None, # None = original filepath
    )
    ezplt.set_arbin_sql_credentials("localhost", "sa", "Amund1234", "SQL Server")
    # ezplt.help()
    ezplt.plot()
