# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 12:20:49 2015

@author: jepe
class version of summary_plot
"""

#-------------needed imports --------------------------------------------------
import sys,os


from cellpy import arbinreader, dbreader, prmreader
from cellpy.utils import plotutils
#------------------------------------------------------------------------------



from numpy import amin, amax, array, argsort
import pandas as pd
import types
import time
import types
import itertools
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MaxNLocator
import pickle as pl



class plotType:
    def __init__(self,
                 label="",
                 columntxt = "",
                 x_range = None,
                 y_range = None,
                 x_axis_lims = None,
                 y_axis_lims = None,
                 x_label = "",
                 y_label = "",
                 label_font = None):
                     
        self.label = label
        self.columntxt = columntxt
        self.x_label = x_label
        self.y_label = y_label
        self.label_font = label_font
        
        if x_range is None:
            self.x_range = []
        else:
            self.x_range = x_range
            
        if y_range is None:
            self.y_range = []
        else:
            self.y_range = y_range
        
        if x_axis_lims is None:
            self.x_axis_lims = []
        else:
            self.x_axis_lims = x_axis_lims
            
        if y_axis_lims is None:
            self.y_axis_lims = []
        else:
            self.y_axis_lims = y_axis_lims



class summaryplot:
    def __init__(self, batch = None, bcol = 5, predirname = "SiNODE", plot_type = 0,
                 use_total_mass = False, refs = None, use_all = True, verbose = False, auto_show = False,
                 figsize = (12,8), legend_stack = 3, only_first=False,
                 axis_txt_sub = "Si",
                 dbc = False,
                 db_file = None,
                 export_hdf5 = True,
                 export_raw=False,
                 export_cycles=False,
                 export_dqdv=False,
                 dqdv_numbermultiplyer =  2,
                 dqdv_method =  "linear",
                 dqdv_finalinterpolation = True,
                 max_cycles = None,
                 fetch_onliners = False,
                 ensure_step_table = False,
                 force_res = False,
                 ):
        self.dqdv_numbermultiplyer = dqdv_numbermultiplyer
        self.dqdv_method = dqdv_method
        self.dqdv_finalinterpolation = dqdv_finalinterpolation
        self.export_dqdv = export_dqdv
        self.export_cycles = export_cycles
        self.max_cycles = max_cycles
        self.dbc = dbc         # use dbc_file instead of db_file (only for reader)
        self.db_file = db_file # custom db_file name (only for reader)
        self.export_hdf5 = export_hdf5
        self.batch = batch
        self.bcol = bcol
        self.sort_method = 1
        self.exit_on_sort_error = False
        self.legend_stack = legend_stack
        self.axis_txt_sub = axis_txt_sub
        self.only_first = only_first
        self.fetch_onliners = fetch_onliners
        self.ensure_step_table = ensure_step_table
        self.force_res = force_res
        # at the moment we asssume refs is a list TODO: fix it
        if refs is None:
            self.refs = []
        else:
            self.refs = refs

        self.refno = 5000
        self.cumcharge_AhUnits = True
        self.current_canvas = 1
        self.refcolor = 'k'
        self.refstyles = ['-' , '--' , '-.' , ':' ]
        self.use_total_mass = use_total_mass
        self.sep = ";"
        self.export_raw = export_raw
        self.savedir_raw = None
        self.verbose = verbose
        self.figsize = figsize
        self.default_legend_axes_number = 1
        self.info = {}
        self.dpi = 300
        self.ylabel_coord_left_1 = -0.085 # left for canvas 1, 2, 4
        self.ylabel_coord_left_2 = -0.17 # left for canvas 3
        self.ylabel_coord_right_1 = 1.11  # right for canvas 4
        self.ylabel_coord_right_2 = 1.5  # right for canvas 3
        self.xlabel_coord_down = -0.2 # not implemented yet
        
        self.delta_ax = 0.05
        self.xlims1 = []
        self.implemented_canvases = [1,2,3,4]

        self.plot_type = plot_type

        self.a = []
        self.group =  []
        self.refgroup = []
        self.labels =  []
        self.allfiles =  []
        self.allmasses =  []
        self.loadings = []
        self.hdf5_fixed_files = []
        self.number_of_tests = 0
        self.d = None


        self.prms = None
        self.predirname = predirname
        self.savedir = None
        self.prename = None
        self.prename2 = "summary_out"
        self.postname = ".csv"
        self.plotlist = []
        self.plotTypes = {}
        self.fig = {}
        self.figname = {}
        self.leg = {}
        self.axes_lib = {}
        self.figtxt_1 = {}
        self.figtxt_2 = {}



#        self.columnslist = [("Discharge_Capacity(mAh/g)",               "_dischargecap"),
#               ("Cumulated_Charge_Capacity(mAh/g)",     "_cumchargecap",),
#               ("Coulombic_Efficiency(percentage)",     "_couleff",),
#               ("ir_discharge",                         "_irdischrg",),
#               ("ir_charge",                            "_irchrg",),
#               ("Charge_Capacity(mAh/g)",               "_chargecap",),
#               ("end_voltage_discharge",                "_endvdischarge",),
#               ("end_voltage_charge",                   "_endvcharge",),
#                    ]

        self.plotdata={}
        
        self.set_mpl_rcparams()
        self.generate_plottypes() # info on the types of plots available
        self.generate_plotlist() # generates list of plots to be plotted



        if batch is not None:
            s=self.run()
            if auto_show is True:
                self.showfig()
                self.save_figs()
                print "\n*** bye!"
                
    def set_mpl_rcparams(self,):
        matplotlib.rcParams['font.size'] = 14
        #matplotlib.rcParams['axes.titlesize'] = "large"
        matplotlib.rcParams['axes.labelsize'] = "small" #"large" # "small" "medium"  "large"    
        matplotlib.rcParams['xtick.labelsize'] = 'medium'
        matplotlib.rcParams['ytick.labelsize'] = 'medium'
        #matplotlib.rcParams['axes.ymargin'] = 0.9
        matplotlib.rcParams['ytick.labelsize'] = 'medium'
        matplotlib.rcParams['ytick.labelsize'] = 'medium'
        matplotlib.rcParams['ytick.labelsize'] = 'medium'
            
    def read_prms(self,):
        self.prms = prmreader.read()

    def set_outdir_top(self,dirname):
        self.prms.outdatadir = dirname

    def set_batch(self,btxt):
        self.batch = btxt

    def set_bcol(self,bcol):
        self.bcol = bcol

    def filter_selected(self,bcol):
        self.a = self.reader.filter_selected(a)

    def make_reader(self,):
        if self.dbc or self.db_file:
            if self.dbc:
                db_file = os.path.join(self.prms.db_path,self.prms.dbc_filename)
            else:
                db_file = self.db_file
            self.reader = dbreader.reader(db_file = db_file)
        else:
            self.reader = dbreader.reader()
        
    def create_outdir(self,):
        if self.prms is None:
            self.read_prms()
        if self.predirname is not None:
            newdir = self.predirname+"_"+self.batch
        else:
            newdir = self.batch

        NewDir = os.path.join(self.prms.outdatadir,newdir)

        if not os.path.isdir(NewDir):
            os.mkdir(NewDir)
            print "created outdate directory"
        self.savedir = NewDir
        
        if self.export_raw or self.export_cycles or self.export_dqdv:
            savedir_raw = os.path.join(self.savedir, "raw_data")
            if not os.path.isdir(savedir_raw):
                os.mkdir(savedir_raw)
                print "created raw data directory"
            self.savedir_raw = savedir_raw
        self.prename = os.path.join(self.savedir, self.prename2)
        # as for now: savedir will be the running directory of the script if
        # this function is not run
        
        

    def generate_plottypes(self,cap_unit = None):
        if cap_unit is None:
            if self.use_total_mass:
                cap_unit = "(Ah/g(Tot))" # jepe fix this (remove this option)
                cum_cap_unit = "(Ah/g(Tot))" # jepe fix this (remove this option)
            else:
                if self.axis_txt_sub is not None:
                    cap_unit = "(mAh/g(%s))" % self.axis_txt_sub
                    cum_cap_unit = "(Ah/g(%s))" % self.axis_txt_sub
                else:
                    cap_unit = "(mAh/g)" 
                    cum_cap_unit = "(Ah/g)" 
                    
        if not self.cumcharge_AhUnits:
            cum_cap_unit = cap_unit

        ylab_dc = "Discharge capacity\n%s" % (cap_unit)
        ylab_c = "Charge capacity\n%s" % (cap_unit)
        ylab_sdc = "Dis.End.Cap.\n%s" % (cap_unit)
        ylab_scc = "Ch.End.Cap.\n%s" % (cap_unit)
        ylab_cc = "Cumulated charge\ncapacity %s" % (cum_cap_unit)

        self.plotTypes["_dischargecap"] = plotType("_dischargecap","Discharge_Capacity(mAh/g)",
                                            x_label = "Cycle",
                                            y_label = ylab_dc,
                                            )
        self.plotTypes["_chargecap"] = plotType("_chargecap","Charge_Capacity(mAh/g)",
                                            x_label = "Cycle",
                                            y_label = ylab_c,
                                            )
        self.plotTypes["_cumchargecap"] = plotType("_cumchargecap","Cumulated_Charge_Capacity(mAh/g)",
                                            x_label = "Cycle",
                                            y_label = ylab_cc,
                                            )
        self.plotTypes["_couleff"] = plotType("_couleff","Coulombic_Efficiency(percentage)",
                                            x_label = "Cycle",
                                            y_label = "Coulombic\nefficiency (%%)",
                                            )
        self.plotTypes["_irdischrg"] = plotType("_irdischrg","ir_discharge",
                                            x_label = "Cycle",
                                            y_label = "IR\ndelith. (Ohms)",
                                            )
        self.plotTypes["_irchrg"] = plotType("_irchrg","ir_charge",
                                            x_label = "Cycle",
                                            y_label = "IR\nlith. (Ohms)",
                                            )
        self.plotTypes["_endvdischarge"] = plotType("_endvdischarge","end_voltage_discharge",
                                            x_label = "Cycle",
                                            y_label = "End voltage\ndischarge (V)",
                                            )
        self.plotTypes["_endvcharge"] = plotType("_endvcharge","end_voltage_charge",
                                            x_label = "Cycle",
                                            y_label = "End voltage\ncharge (V)",
                                            )

        # diagnostics plots
        self.plotTypes["d_shifted_chargecap"] = plotType("shifted_charge_cap","none",
                                            x_label = "Cycle",
                                            y_label = ylab_scc,
                                            )
        self.plotTypes["d_shifted_dischargecap"] = plotType("shifted_discharge_cap","none",
                                            x_label = "Cycle",
                                            y_label = ylab_sdc,
                                            )
        self.plotTypes["d_ric"] = plotType("RIC_cum","none",
                                            x_label = "Cycle",
                                            y_label = "Cum.RIC\n(no units)",
                                            )
        self.plotTypes["d_ric_disconnect"] = plotType("RIC_disconnect_cum","none",
                                            x_label = "Cycle",
                                            y_label = "Cum.RIC_SEI\n(no units)",
                                            )

        self.plotTypes["d_ric_sei"] = plotType("RIC_sei_cum","none",
                                            x_label = "Cycle",
                                            y_label = "Cum.RIC_disc.\n(no units)",
                                            )



    def generate_plotlist(self, selected = None):
        self.plotlist = []
        if selected is None:
            self.plotlist = self.plotTypes.keys()
        else:
            self.plotlist = selected

    def run(self,):
        print "running",
        print self.batch
        print "using batch col",
        print self.bcol
        print "reading prms"
        self.read_prms()
        print self.prms
        print "creating dir"
        self.create_outdir()
        print self.savedir
        print "reading database"
        self.make_reader()
        self.a = self.reader.select_batch(self.batch, self.bcol)
        lena = len(self.a)
        if lena<1:
            print "no experimental runs found"
            return -1
        print "list of experimental runs:"
        print self.a

        print "PROCESSING..."
        self.get_info()
        self.load_cells()

        print "EXPORTING..."
        self.make_diagnostics_plots()
        for ex in self.plotlist:
            self.make_datasets(ex)
            self.save_datasets(ex)
            
        self.save_raw()
        self.save_cycles()
        self.save_dqdv()
        self.save_hdf5()

        print "PLOTTING..."
        try:
            canvases = []
            if self.plot_type == 0:
                canvases = self.implemented_canvases
    
            else:
                if isinstance(self.plot_type, list):
                    canvases = self.plot_type
                else:
                    canvases.append(self.plot_type)
            for canvas in canvases:
                self.make_plot_canvas(canvas)
                self.create_legend(canvas=canvas, max_length=self.legend_stack, flip = False)
                #self.move_legend(canvas=1, offset=[-0.1,0.0])
                #self.set_legend_loc(canvas=1, loc=[0.7,0.9])
            #self.set_ylims("couleff",[95.0,102.0])
            #self.set_ylims("endvcharge",[0.0,1.2])
        except:
            print "Error in plotting"
            print sys.exc_info()[0]


    def end(self,):
        self.closefigs()
        print "***END"
        
        

        
# ---------- Canvases ---------------------------------------------------------

    def scc(self, canvas = 1):
        self.current_canvas = canvas

    def set_current_canvas(self, canvas = 1):
        self.current_canvas = canvas

    def make_plot_canvas_test(self,):
        self.fig[1] = plt.figure(figsize=self.figsize)
        my_styles = plotutils.Styles()
        self.styles = my_styles.get_set(self.group)
        self.test_axes1 = plt.subplot(1,2,1)
        self.test_axes2 = plt.subplot(1,2,2)
        self.plot_ax("_dischargecap",self.test_axes1)
        self.plot_ax("_irdischrg",self.test_axes2)

            

    def make_plot_canvas(self, canvas = 1):
        # TODO: currently defining self.someaxes in all instances of make_plot_canvas,
        # should make a smarter way to do it [e.g. self.someaxes[canvas]]
        if canvas == 1:

            self.fig[canvas] = plt.figure(figsize=self.figsize) # using self.fig[1] here for first time
            self.leg[canvas] = [None,None]

            self.figtxt_1[canvas] = "Figure xx%i: Cycling results (galvanostatic) of electrodes (half-cells, coin-cells); " % (canvas)
            self.figtxt_1[canvas]+= "showing, from top to bottom: coulombic efficiency, discharge capacity, end voltage during charge "
            self.figtxt_1[canvas]+= "(the voltage where pre-set capacity-limit terminates the delithiation step (or pre-set voltage cut-off is reached)) "
            self.figtxt_1[canvas]+= "and internal resistance (after delithiation step) vs. cycle number."

            self.figtxt_2[canvas] = ""

            my_styles = plotutils.Styles()
            self.styles = my_styles.get_set(self.group)
            self._visible = True

            Hspace = 0.00
            gs1 = gridspec.GridSpec(5,3)
            gs1.update(hspace = Hspace)

            self.ce_axes        =  self.fig[canvas].add_subplot(gs1[0,:])
            print "created axes: self.ce_axes (N=0)"

            self.discharge_axes =  self.fig[canvas].add_subplot(gs1[1:3,:], sharex=self.ce_axes)
            print "created axes: self.discharge_axes (N=1)"

            self.endvc_axes     =  self.fig[canvas].add_subplot(gs1[-2,:], sharex=self.ce_axes)
            print "created axes: self.endvc_axes (N=2)"

            self.irdc_axes       =  self.fig[canvas].add_subplot(gs1[-1,:], sharex=self.ce_axes)
            print "created axes: self.irdc_axes (N=3)"

            self.axes_lib[canvas] = {}
            self.axes_lib[canvas]["_couleff"] = 0
            self.axes_lib[canvas]["_dischargecap"] = 1
            self.axes_lib[canvas]["_endvcharge"] = 2
            self.axes_lib[canvas]["_irdischrg"] = 3

            # TODO: get function for making labels
            # TODO: make one plot_xxx function with input _ext and axes
            # TODO: make correct scaling (max, min as output from plot_xxx)
            self.plot_ax("_couleff",self.ce_axes)
            self.plot_ax("_dischargecap",self.discharge_axes)
            self.plot_ax("_endvcharge",self.endvc_axes)
            self.plot_ax("_irdischrg",self.irdc_axes)

            self.scale_ax("_dischargecap",self.discharge_axes)
            self.scale_ax_y("_couleff",self.ce_axes)
            self.scale_ax_y("_endvcharge",self.endvc_axes)
            self.scale_ax_y("_irdischrg",self.irdc_axes)

    #        values = self.plotdata["_dischargecap"][1][0]
    #        self.discharge_axes.plot(values)
    #        self.discharge_axes.set_xlim([0,1000])


            self.set_x_label(ax = self.irdc_axes, plot_type = "_irdischrg")

            self.remove_xticklabels(self.ce_axes)
            self.remove_xticklabels(self.discharge_axes)
            self.remove_xticklabels(self.endvc_axes)


            self.set_y_label(ax = self.ce_axes, plot_type = "_couleff") #TODO: order of axes and id inverted - should change order
            self.set_y_label(ax = self.discharge_axes, plot_type = "_dischargecap")
            self.set_y_label(ax = self.irdc_axes, plot_type = "_irdischrg")
            self.set_y_label(ax = self.endvc_axes, plot_type = "_endvcharge")
            #plt.tight_layout()
            self.set_nlocator(self.ce_axes,ny=4)
            self.set_nlocator(self.discharge_axes,ny=8)
            self.set_nlocator(self.irdc_axes,ny=4)
            self.set_nlocator(self.endvc_axes,ny=4)

            #list_of_axes = self.fig[1].get_axes()

            #plt.savefig(r"C:\Scripting\MyFiles\tmp_out\test.png", dpi = self.dpi)
        elif canvas == 2:
            # without end-voltage
            fx,fy = self.figsize
            fy = 0.8*fy
            self.fig[canvas] = plt.figure(figsize=(fx,fy)) # using self.fig[2] here for first time
            self.leg[canvas] = [None,None]
            self.figtxt_1[canvas] = "Figure xx%i: Cycling results (galvanostatic unrestricted cycling in the range 1-0.01 V) "  % (canvas)
            self.figtxt_1[canvas]+= "of electrodes (half-cells, coin-cells); "
            self.figtxt_1[canvas]+= "showing, from top to bottom: coulombic efficiency, "
            self.figtxt_1[canvas]+= "discharge capacity, and internal resistance (after delithiation step) vs. cycle number."
            self.figtxt_2[canvas] = ""

            my_styles = plotutils.Styles()
            self.styles = my_styles.get_set(self.group)
            self._visible = True

            Hspace = 0.00
            gs1 = gridspec.GridSpec(4,3)
            gs1.update(hspace = Hspace)
            self.ce_axes        =  self.fig[canvas].add_subplot(gs1[0,:])
            print "created axes: self.ce_axes (N=0)"

            self.discharge_axes =  self.fig[canvas].add_subplot(gs1[1:3,:], sharex=self.ce_axes)
            print "created axes: self.discharge_axes (N=1)"
            self.irdc_axes     =  self.fig[canvas].add_subplot(gs1[-1,:], sharex=self.ce_axes)
            print "created axes: self.irdc_axes (N=2)"

            self.axes_lib[canvas] = {}
            self.axes_lib[canvas]["_couleff"] = 0
            self.axes_lib[canvas]["_dischargecap"] = 1
            self.axes_lib[canvas]["_irdischrg"] = 2

            # TODO: get function for making labels
            # TODO: make one plot_xxx function with input _ext and axes
            # TODO: make correct scaling (max, min as output from plot_xxx)
            self.plot_ax("_couleff",self.ce_axes)
            self.plot_ax("_dischargecap",self.discharge_axes)
            self.plot_ax("_irdischrg",self.irdc_axes)

            self.scale_ax("_dischargecap",self.discharge_axes)
            self.scale_ax_y("_couleff",self.ce_axes)
            self.scale_ax_y("_irdischrg",self.irdc_axes)

    #        values = self.plotdata["_dischargecap"][1][0]
    #        self.discharge_axes.plot(values)
    #        self.discharge_axes.set_xlim([0,1000])


            self.set_x_label(ax = self.irdc_axes, plot_type = "_irdischrg")

            self.remove_xticklabels(self.ce_axes)
            self.remove_xticklabels(self.discharge_axes)

            self.set_y_label(ax = self.ce_axes, plot_type = "_couleff")
            self.set_y_label(ax = self.discharge_axes, plot_type = "_dischargecap")
            self.set_y_label(ax = self.irdc_axes, plot_type = "_irdischrg")
            #plt.tight_layout()
            self.set_nlocator(self.ce_axes,ny=4)
            self.set_nlocator(self.discharge_axes,ny=8)
            self.set_nlocator(self.irdc_axes,ny=4)

            #list_of_axes = self.fig[1].get_axes()

            #plt.savefig(r"C:\Scripting\MyFiles\tmp_out\test.png", dpi = self.dpi)



        elif canvas == 3:

            self.fig[canvas] = plt.figure(figsize=self.figsize) # using self.fig[1] here for first time
            self.leg[canvas] = [None,None]
            self.figtxt_1[canvas] = "Figure xx%i: Cycling results (galvanostatic) of electrodes (half-cells, coin-cells); " % (canvas)
            self.figtxt_1[canvas] += "showing, left side, from top to bottom: coulombic efficiency and discharge capacity, "
            self.figtxt_1[canvas] += "middle, from top to bottom: internal resistance (after delithiation step) and internal resistance (after lithiation step) "
            self.figtxt_1[canvas] += "and right side, from top to bottom: end voltage during charge, end voltage during discharge, and cumulated charge capacity vs. cycle number."
            self.figtxt_2[canvas] = ""
            my_styles = plotutils.Styles()
            self.styles = my_styles.get_set(self.group)
            self._visible = True

            Hspace = 0.00
            spacer1 = 0.08
#
#            Hspace = 0.00
#            gs1 = gridspec.GridSpec(4,3)
#            gs1.update(hspace = Hspace)
#            self.ce_axes        =  self.fig[canvas].add_subplot(gs1[0,:])

            gs1 = gridspec.GridSpec(3,1)
            #gs1.update(left=0.1, right=0.5-spacer1/2, hspace=Hspace)
            gs1.update(right=0.5-spacer1/2, hspace=Hspace)

            gs2 = gridspec.GridSpec(6,2)
            #gs2.update(left=0.5+spacer1/2, right=0.9, hspace=Hspace, wspace =0.05)
            gs2.update(left=0.5+spacer1/2, hspace=Hspace, wspace =0.05)

            self.ce_axes        =  self.fig[canvas].add_subplot(gs1[0,0])
            print "created axes: self.ce_axes (N=0)"
            self.discharge_axes =  self.fig[canvas].add_subplot(gs1[1:,0], sharex=self.ce_axes)
            print "created axes: self.discharge_axes (N=1)"

            self.cum_axes     =  self.fig[canvas].add_subplot(gs2[4:6,1])
            print "created axes: self.cum_axes (N=2)"
            self.endvc_axes     =  self.fig[canvas].add_subplot(gs2[0:2,1], sharex=self.cum_axes)
            print "created axes: self.endvc_axes (N=3)"
            self.endvdc_axes       =  self.fig[canvas].add_subplot(gs2[2:4,1], sharex=self.cum_axes)
            print "created axes: self.irdc_axes (N=4)"

            self.irc_axes       =  self.fig[canvas].add_subplot(gs2[:3,0])
            print "created axes: self.irc_axes (N=5)"
            self.irdc_axes       =  self.fig[canvas].add_subplot(gs2[3:,0], sharex=self.irc_axes)
            print "created axes: self.irdc_axes (N=6)"

            self.axes_lib[canvas] = {}
            self.axes_lib[canvas]["_couleff"] = 0
            self.axes_lib[canvas]["_dischargecap"] = 1
            self.axes_lib[canvas]["_cumchargecap"] = 2
            self.axes_lib[canvas]["_endvcharge"] = 3
            self.axes_lib[canvas]["_endvdischarge"] = 4
            self.axes_lib[canvas]["_irchrg"] = 5
            self.axes_lib[canvas]["_irdischrg"] = 6



            self.plot_ax("_couleff",self.ce_axes)
            self.plot_ax("_dischargecap",self.discharge_axes)
            self.plot_ax("_cumchargecap",self.cum_axes)
            self.plot_ax("_endvcharge",self.endvc_axes)
            self.plot_ax("_endvdischarge",self.endvdc_axes)
            self.plot_ax("_irchrg",self.irc_axes)
            self.plot_ax("_irdischrg",self.irdc_axes)


            self.scale_ax("_dischargecap",self.discharge_axes)
            self.scale_ax("_irchrg",self.irc_axes)
            self.scale_ax("_cumchargecap",self.cum_axes)

            self.scale_ax_y("_couleff",self.ce_axes)
            self.scale_ax_y("_endvdischarge",self.endvdc_axes)
            self.scale_ax_y("_endvcharge",self.endvc_axes)
            self.scale_ax_y("_irdischrg",self.irdc_axes)


            self.set_x_label(ax = self.discharge_axes, plot_type = "_dischargecap")
            self.set_x_label(ax = self.irdc_axes, plot_type = "_irdischrg")
            self.set_x_label(ax = self.cum_axes, plot_type = "_cumchargecap")

            self.remove_xticklabels(self.ce_axes)
            self.remove_xticklabels(self.endvc_axes)
            self.remove_xticklabels(self.endvdc_axes)
            self.remove_xticklabels(self.irc_axes)


            xcoordL1 = self.ylabel_coord_left_2
            xcoordL2 = 0.5 + spacer1/2 - xcoordL1
            xcoordL2 = xcoordL1
            xcoordR = self.ylabel_coord_right_2 

            self.set_y_label(ax = self.ce_axes, plot_type = "_couleff", xcoord = xcoordL1)
            self.set_y_label(ax = self.discharge_axes, plot_type = "_dischargecap", xcoord = xcoordL1)

            self.set_y_label(ax = self.cum_axes, plot_type = "_cumchargecap", position = "right", xcoord = xcoordR)
            self.set_y_label(ax = self.endvdc_axes, plot_type = "_endvdischarge", position = "right", xcoord = xcoordR)
            self.set_y_label(ax = self.endvc_axes, plot_type = "_endvcharge", position = "right", xcoord = xcoordR)

            self.set_y_label(ax = self.irdc_axes, plot_type = "_irdischrg", xcoord = xcoordL2)
            self.set_y_label(ax = self.irc_axes, plot_type = "_irchrg", xcoord = xcoordL2)



            #plt.tight_layout()
            self.set_nlocator(self.ce_axes,ny=4)
            self.set_nlocator(self.discharge_axes,ny=8, nx=6)

            self.set_nlocator(self.irdc_axes,ny=4, nx=4)
            self.set_nlocator(self.irc_axes,ny=4, nx=4)

            self.set_nlocator(self.cum_axes,ny=3, nx=4)
            self.set_nlocator(self.endvdc_axes,ny=3, nx=4)
            self.set_nlocator(self.endvc_axes,ny=3, nx=4)

            #list_of_axes = self.fig[1].get_axes()

            #plt.savefig(r"C:\Scripting\MyFiles\tmp_out\test.png", dpi = self.dpi)
        elif canvas == 4:
            # multiplot with diagnostics
            fx,fy = self.figsize
            fy = 2.2*fy
            self.fig[canvas] = plt.figure(figsize=(fx,fy)) # using self.fig[4] here for first time
            self.leg[canvas] = [None,None]
            self.figtxt_1[canvas] = "Figure xx%i: Cycling results (galvanostatic) of electrodes (half-cells, coin-cells); " % (canvas)
            self.figtxt_1[canvas]+= "showing, from top to bottom: coulombic efficiency, discharge capacity, end voltage during charge "
            self.figtxt_1[canvas]+= "(the voltage where pre-set capacity-limit terminates the delithiation step (or pre-set voltage cut-off is reached)), "
            self.figtxt_1[canvas]+= "internal resistance (after delithiation step), discharge end-capacity, charge end-capacity, "
            self.figtxt_1[canvas]+= "cummulated relative irreversible capacity (RIC) due to disconnection of active material, "
            self.figtxt_1[canvas]+= "and RIC due to SEI formation (see e.g. Gauthiere et al., Energy Environ. Sci., 2013, 6, 2145 for definitions) "
            self.figtxt_1[canvas]+= "vs. cycle number."

            self.figtxt_2[canvas] = ""

            my_styles = plotutils.Styles()
            self.styles = my_styles.get_set(self.group)
            self._visible = True

            Hspace = 0.00
            gs1 = gridspec.GridSpec(9,3)
            gs1.update(hspace = Hspace)
            self.ce_axes        =  self.fig[canvas].add_subplot(gs1[0,:])
            print "created axes: self.ce_axes (N=0)"
            self.discharge_axes =  self.fig[canvas].add_subplot(gs1[1:3,:], sharex=self.ce_axes)
            print "created axes: self.discharge_axes (N=1)"
            self.endvc_axes     =  self.fig[canvas].add_subplot(gs1[3,:], sharex=self.ce_axes)
            print "created axes: self.endvc_axes (N=2)"            
            self.irdc_axes       =  self.fig[canvas].add_subplot(gs1[4,:], sharex=self.ce_axes)
            print "created axes: self.irdc_axes (N=3)"   
            self.shifteddcap_axes     =  self.fig[canvas].add_subplot(gs1[5,:], sharex=self.ce_axes)
            print "created axes: self.shifteddcap_axes (N=4)"
            self.shiftedcap_axes     =  self.fig[canvas].add_subplot(gs1[6,:], sharex=self.ce_axes)
            print "created axes: self.shiftedcap_axes (N=5)"
            self.ric_disconn_axes     =  self.fig[canvas].add_subplot(gs1[7,:], sharex=self.ce_axes)
            print "created axes: self.ric_disconn_axes (N=6)"
            self.ric_sei_axes     =  self.fig[canvas].add_subplot(gs1[8,:], sharex=self.ce_axes)
            print "created axes: self.ric_sei_axes (N=7)"
            
            self.axes_lib[canvas] = {}
            self.axes_lib[canvas]["_couleff"] = 0
            self.axes_lib[canvas]["_dischargecap"] = 1
            self.axes_lib[canvas]["_endvcharge"] = 2
            self.axes_lib[canvas]["_irdischrg"] = 3
            self.axes_lib[canvas]["d_shifted_dischargecap"] = 4
            self.axes_lib[canvas]["d_shifted_chargecap"] = 5
            self.axes_lib[canvas]["d_ric_disconnect"] = 6
            self.axes_lib[canvas]["d_ric_sei"] = 7

            self.plot_ax(plot_type="_couleff",ax=self.ce_axes)
            self.plot_ax(plot_type="_dischargecap",ax=self.discharge_axes)
            self.plot_ax(plot_type="_endvcharge",ax=self.endvc_axes)
            self.plot_ax(plot_type="_irdischrg",ax=self.irdc_axes)
            self.plot_ax(plot_type="d_shifted_dischargecap",ax=self.shifteddcap_axes)
            self.plot_ax(plot_type="d_shifted_chargecap",ax=self.shiftedcap_axes)
            self.plot_ax(plot_type="d_ric_disconnect",ax=self.ric_disconn_axes)
            self.plot_ax(plot_type="d_ric_sei",ax=self.ric_sei_axes)

            
            self.scale_ax_y(plot_type="_couleff",ax=self.ce_axes)
            self.scale_ax(plot_type="_dischargecap",ax=self.discharge_axes)
            self.scale_ax_y(plot_type="_endvcharge",ax=self.endvc_axes)
            self.scale_ax_y(plot_type="_irdischrg",ax=self.irdc_axes)
            self.scale_ax_y(plot_type="d_shifted_dischargecap",ax=self.shifteddcap_axes)
            self.scale_ax_y(plot_type="d_shifted_chargecap",ax=self.shiftedcap_axes)
            self.scale_ax_y(plot_type="d_ric_disconnect",ax=self.ric_disconn_axes)
            self.scale_ax_y(plot_type="d_ric_sei",ax=self.ric_sei_axes)

            self.set_x_label(plot_type="d_ric_sei",ax=self.ric_sei_axes)

            self.remove_xticklabels(self.ce_axes)
            self.remove_xticklabels(self.discharge_axes)
            self.remove_xticklabels(self.endvc_axes)
            self.remove_xticklabels(self.irdc_axes)
            self.remove_xticklabels(self.shifteddcap_axes)
            self.remove_xticklabels(self.shiftedcap_axes)
            self.remove_xticklabels(self.ric_disconn_axes)


            xcoordR = self.ylabel_coord_right_1
            
            self.set_y_label(plot_type="_couleff",ax=self.ce_axes)
            self.set_y_label(plot_type="_dischargecap",ax=self.discharge_axes, position = "right", xcoord = xcoordR)
            self.set_y_label(plot_type="_endvcharge",ax=self.endvc_axes)
            self.set_y_label(plot_type="_irdischrg",ax=self.irdc_axes, position = "right", xcoord = xcoordR)
            self.set_y_label(plot_type="d_shifted_dischargecap",ax=self.shifteddcap_axes)
            self.set_y_label(plot_type="d_shifted_chargecap",ax=self.shiftedcap_axes, position = "right", xcoord = xcoordR)
            self.set_y_label(plot_type="d_ric_disconnect",ax=self.ric_disconn_axes)
            self.set_y_label(plot_type="d_ric_sei",ax=self.ric_sei_axes, position = "right", xcoord = xcoordR)            
            
            self.set_nlocator(self.ce_axes, ny=4)
            self.set_nlocator(self.discharge_axes, ny=8)
            self.set_nlocator(self.endvc_axes, ny=4)
            self.set_nlocator(self.irdc_axes, ny=4)
            self.set_nlocator(self.shifteddcap_axes, ny=4)
            self.set_nlocator(self.shiftedcap_axes, ny=4)
            self.set_nlocator(self.ric_disconn_axes, ny=4)
            self.set_nlocator(self.ric_sei_axes, ny=4)


# ---------- Load and generate data -------------------------------------------
    
    def make_diagnostics_plots(self, _exts = None):
        #TODO: fix this
        column_names = []
        diagnostics = []
        tests_status = self.d.tests_status
        for testnumber, test in enumerate(self.d.tests):
            status = tests_status[testnumber]
            try:
                firstname,extension=os.path.splitext(test.loaded_from)
            except AttributeError as e:
                print "Empty set?"
                print e
                print "Status:",
                print status
            else:
                cn = os.path.basename(firstname)
                cn = self.make_legend_txt(cn)
                column_names.append(cn)
                out = self.d.get_diagnostics_plots(test_number = testnumber)
                diagnostics.append(out)

        if _exts is None:
            _exts = ["d_shifted_chargecap","d_shifted_dischargecap","d_ric",
                      "d_ric_disconnect", "d_ric_sei"]
        for _ext in _exts:
            datasets = []
            for out in diagnostics:
                _sel = self.plotTypes[_ext].label
                datasets.append(out[_sel])
#                print "added: %s" % (_sel)
#                print out[_sel]
            self.plotdata[_ext]=[column_names,datasets]

    def make_datasets(self,_ext):
        if _ext[0] == "d":
            return
        _sel = self.plotTypes[_ext].columntxt
        column_names = []
        datasets = []
        for status,test in zip(self.d.tests_status,self.d.tests):
            if not status:
                print "test missing"
            else:
            # check if test is empty
                if _sel  in test.dfsummary.columns:
                    if len(test.dfsummary[_sel])>0:
                        firstname,extension=os.path.splitext(test.loaded_from)
                        cn = os.path.basename(firstname)
                        cn = self.make_legend_txt(cn)
                        column_names.append(cn)
                        datasets.append(test.dfsummary[_sel])
                    else:
                        print test.loaded_from,
                        print "is empty"
                else:
                    print test.loaded_from,
                    print "is missing",
                    print _sel
        self.plotdata[_ext]=[column_names,datasets]
    
    
    def load_cells(self, sort = True):
        self.d = arbinreader.arbindata(verbose = self.verbose,fetch_onliners=self.fetch_onliners)
        self.d.set_hdf5_datadir(self.prms.hdf5datadir)
        self.d.set_res_datadir(self.prms.resdatadir)
        force_res = self.force_res
        if sort is True:
            self.sort_cells()
        if self.only_first:
            self.d.loadcell(names = self.allfiles, masses = self.allmasses, counter_max = 1, res = force_res)
        else:
            self.d.loadcell(names = self.allfiles, masses = self.allmasses, res = force_res)
        self.number_of_tests = self.d.get_number_of_tests()
        
    def get_info(self,):
        self._get_info()
        self._get_refs_info()
        
    
    def sort_cells(self,set_seqv = True):
        # convinience function for sorting
        sorted_indexes = argsort(array(self.group))
        counter = 0
        group1 = []
        allfiles2  = []
        allmasses2 = []
        labels2    = []
        loadings2  = []
        hdf5_fixed_files2 = []

        # sorting
        print "\nsorting"
        for indx in sorted_indexes:
            g = self.group[indx]
            f = self.allfiles[indx]
            label = self.labels[indx]
            m = self.allmasses[indx]
            loading = self.loadings[indx]
            fixed = self.hdf5_fixed_files[indx]
            txt = "old: g=%i, file=%s\nnew: g=%i, file=%s" % (self.group[counter], self.allfiles[counter],
                                                              g, f)
            print txt
            group1.append(g)
            allfiles2.append(f)
            allmasses2.append(m)
            labels2.append(label)
            loadings2.append(loading)
            hdf5_fixed_files2.append(fixed)
            counter += 1

        if set_seqv is True:
        # setting seq. g
            numbers = range(1,1000)
            max_g   = -1000000
            max_i   = -1
            group2 = []
            for g in group1:
                if not g in self.refgroup:
                    if g>max_g:
                        max_g  = g
                        max_i += 1
                    group2.append(numbers[max_i])
                else:
                    group2.append(g)
            print "old group:"
            print self.group
            print "old group sorted:"
            print group1
            print "new group:"
            print group2
        else:
            group2 = group1

        self.allfiles = allfiles2
        self.labels   = labels2
        self.allmasses= allmasses2
        self.loadings = loadings2
        self.group    = group2
        self.hdf5_fixed_files = hdf5_fixed_files2


    def _make_group_list_txt(self):
        g_txt = []
        used_g = {}
        ref = 0
        for g in self.group:
            if g in self.refgroup:
                ref+=1
                if len(self.refgroup)>1:
                    t = "ref.%i" % (ref)
                else:
                    t = "ref"
            else:
                g = int(g)
                if g in used_g.keys():
                    used_g[g] += 1

                else:
                    used_g[g]=1
                t = "%i.%i" % (g, used_g[g])
            g_txt.append(t)

        return g_txt


    def _get_info(self,):
        for srno in self.a:
            filenames = self.reader.get_cell_name(srno)
            if not filenames: # Errorlog: encountered error here when having duplicate in srnos (i.e. when having two experiments-sets/rows in the log with same srno)
                print "could not find any files"
            else:
                mass = self.reader.get_mass(srno)
                tmass = self.reader.get_total_mass(srno)
                loading = self.reader.get_loading(srno)
                fixed = self.reader.inspect_hd5f_fixed(srno)
                try:
                    g = int(self.reader.get_group(srno))
                except:
                    print "could not find group number"
                    g = 100
                label = self.reader.get_label(srno)
                if self.use_total_mass:
                    print "using total mass"
                    print "Si mass = %f" % mass
                    mass = tmass
                    print "WARNING: if loading from hdf5-file, total mass will not be used (error to be fixed later)"
                print "mass = %f" % mass

                self.allfiles.append(filenames)
                self.group.append(g)
                self.labels.append(label)
                self.allmasses.append(mass)
                self.loadings.append(loading)
                self.hdf5_fixed_files.append(fixed)


    def _get_refs_info(self,):
        for refno,srno in enumerate(self.refs):
            filenames = self.reader.get_cell_name(srno)
            if not filenames:
                print "could not find any files for ref"
            else:
                mass = self.reader.get_mass(srno)
                tmass = self.reader.get_total_mass(srno)
                loading = self.reader.get_loading(srno)
                g = self.refno + refno
                label = "ref_%i" % (refno)
                if self.use_total_mass:
                    mass = tmass

                self.allfiles.append(filenames)
                self.group.append(g)
                self.refgroup.append(g)
                self.labels.append(label)
                self.allmasses.append(mass)
                self.loadings.append(loading)

# --------- References tools --------------------------------------------------

    def add_ref(self, srno):
        self.refs.append(srno)


    def print_refs(self):
        print "A proper reference library will be included on a later stage"
        print "Here is a print-out of the ones used in the old script:"

        print """
        #------------------------------------------------------------------------------
        graphite_reference = RefElectrode()
        graphite_reference.srno = 63
        graphite_reference.label = "ref. graphite (es018, bm 5 min)"

        eSi_reference = RefElectrode()
        eSi_reference.srno = 46
        eSi_reference.label = "ref. eSi (es015)"
        eSi_reference.use = False

        milled_reference = RefElectrode()
        milled_reference.srno  = 26
        milled_reference.label = "ref. milled (es010, bm 5 min)"
        milled_reference.use = False

        mixed_milled_reference = RefElectrode()
        mixed_milled_reference.srno  = 38
        mixed_milled_reference.label = "ref. mix (es013, bm 5 min)"
        mixed_milled_reference.use = False

        mixed_milled_reference_cc = RefElectrode()
        mixed_milled_reference_cc.srno  = 193
        mixed_milled_reference_cc.label = "ref. mix (es027 cc, bm 5 min)"
        mixed_milled_reference_cc.use = False

        mixed_milled_reference_cc_vc = RefElectrode()
        mixed_milled_reference_cc_vc.srno  = 196
        mixed_milled_reference_cc_vc.label = "ref. mix w/VC (es027 cc, bm 5 min)"
        mixed_milled_reference_cc_vc.use = False

        buffer_reference_cc = RefElectrode()
        buffer_reference_cc.srno  = 267 # thicker electrode (0.79)
        buffer_reference_cc.srno  = 268 # thin electrode (0.54)
        buffer_reference_cc.label = "ref. buffer (es030 cc, bm 5 min)"
        buffer_reference_cc.use = False

        buffer_ife_reference_cc = RefElectrode()
        buffer_ife_reference_cc.srno  = 318
        buffer_ife_reference_cc.label = "ref. buffer F3 (is014 cc)"
        buffer_ife_reference_cc.use = False
        """




# --------- Plotting tools ----------------------------------------------------

    def cplot_ax(self, plot_type, ax):
        pass

    def plot_ax(self, plot_type, ax):

        labels = self.plotdata[plot_type][0]
        y_values = self.plotdata[plot_type][1]
        if plot_type == "_cumchargecap" and self.cumcharge_AhUnits is True:
            y2_values = []
            for y in y_values:
                y = y/1000.0
                y2_values.append(y)
            y_values = y2_values
        styles = self.styles
        self._visible = True
        x_limits,y_limits = self.__plot(labels,y_values,styles,ax)
        print "\n-----------------------------\nplotting %s" % plot_type
        print "on axes:",
        print ax
        print "x limits:",
        print x_limits
        print "y limits:",
        print y_limits
        print "labels:"
        print labels
        print "-----------------------------"
        self.plotTypes[plot_type].x_range = x_limits
        self.plotTypes[plot_type].y_range = y_limits
        

    def __plot(self, labels, y_values, styles, ax):
        x_min = []
        x_max = []
        y_min = []
        y_max = []
        group = self.group
        refgroup = self.refgroup
        for label,values,line_style,g in zip(labels, y_values, styles, group):
            x_values = range(1,len(values)+1)
            # TODO: get proper x-values from real data
            # print label
            if g in refgroup:
                j = refgroup.index(g)
                v = self._visible
                ls = self.refstyles[min(j,len(self.refstyles))]
                lw = line_style.linewidth
                lc = self.refcolor
                m = None
                me = None
                mw = None
                mf = None
                ms = None
                mevery = 1
            else:
                v = self._visible
                ls = line_style.linestyle
                lw = line_style.linewidth
                lc = line_style.color
                m = line_style.marker
                me = line_style.markeredgecolor
                mw = line_style.markeredgewidth
                mf = line_style.markerfacecolor
                ms = line_style.markersize
                mevery = 1

            ax.plot(x_values,values, label=label,visible = v,linestyle = ls,
                                   linewidth = lw, color = lc,
                                   #dashes = line_style.dashes, # on, off, on, off, etc
                                   marker = m, markeredgecolor = me,
                                   markeredgewidth = mw, markerfacecolor = mf,
                                   markersize = ms, markevery = mevery,
                                   #markevery = line_style.markevery, # 1 for all, 2 for each second, etc
                                   )
            if not g in refgroup:
                x_min.append(amin(x_values))
                x_max.append(amax(x_values))
            y_min.append(amin(values))
            y_max.append(amax(values))

        x_limits = [amin(x_min), amax(x_max)]
        y_limits = [amin(y_min), amax(y_max)]
        return x_limits,y_limits

#

    def drawfig(self, fignum=0):
        if fignum > 0:
            self.fig[fignum].canvas.draw()
        else:
            plt.draw()

    def showfig(self, fignum=0):
        if fignum > 0:
            self.fig[fignum].canvas.draw()
            self.fig[fignum].show()
        else:
            "Note! For interactive use: xxx.showfig(number)"
            plt.show()

    def closefigs(self,):
        for figure in self.fig.values:
            plt.close(figure)

# --------- Reporting tools ---------------------------------------------------

    def _export_dqdv(self, savedir, sep):
        """internal function for running dqdv script """
        from cellpy.utils.dqdv import dQdV
        dqdv_numbermultiplyer = self.dqdv_numbermultiplyer
        #print dqdv_numbermultiplyer
        dqdv_method = self.dqdv_method
        #print dqdv_method
        dqdv_finalinterpolation = self.dqdv_finalinterpolation
        #print dqdv_finalinterpolation
        
        max_cycles  = self.max_cycles
        
        test_number = -1
        for data in self.d.tests:
            test_number+=1
            print test_number
            if data is None:
                print "NoneType - dataset missing"
            else:
                filename = data.loaded_from
                no_merged_sets=""
                firstname,extension=os.path.splitext(filename)
                firstname+=no_merged_sets
                if savedir:
                    firstname = os.path.join(savedir,os.path.basename(firstname))
                outname_charge=firstname+"_dqdv_charge.csv"
                outname_discharge=firstname+"_dqdv_discharge.csv"
                
                print outname_charge
                print outname_discharge
                
                list_of_cycles = self.d.get_cycle_numbers(test_number=test_number)
                number_of_cycles = len(list_of_cycles)
                print "you have %i cycles" % (number_of_cycles)
                    
                # extracting charge
                out_data = []    
                for cycle in list_of_cycles:
                    try:
                        #if max_cycles is not None and cycle <= max_cycles:
                        c,v = self.d.get_ccap(cycle,test_number=test_number )
                        v,dQ = dQdV(v,c,
                                    NumberMultiplyer=dqdv_numbermultiplyer,
                                    Method=dqdv_method,
                                    FinalInterpolation = dqdv_finalinterpolation)
                        #dc,dv = self.dget_cap(cycle,test_number=test_number )
                        v = v.tolist()
                        dQ = dQ.tolist()
                        
                        
                        header_x = "dQ cycle_no %i" % cycle
                        header_y = "voltage cycle_no %i" % cycle
                        dQ.insert(0,header_x)
                        v.insert(0,header_y)
                        
                        out_data.append(v)  
                        out_data.append(dQ)
                    except:
                        print "could not extract cycle %i" % (cycle)
                        
                
                # Saving cycles in one .csv file (x,y,x,y,x,y...)
                #print "saving the file with delimiter '%s' " % (sep)
                print "Trying to save dqdv charge data to"
                print outname_charge
                with open(outname_charge, "wb") as f:
                    writer=csv.writer(f,delimiter=sep)
                    writer.writerows(itertools.izip_longest(*out_data))
                    # star (or asterix) means transpose (writing cols instead of rows)
    
                # extracting discharge
                out_data = []    
                for cycle in list_of_cycles:
                    try:
                        dc,v = self.d.get_dcap(cycle,test_number=test_number )
                        v,dQ = dQdV(v,dc,
                                    NumberMultiplyer=dqdv_numbermultiplyer,
                                    Method=dqdv_method,
                                    FinalInterpolation = dqdv_finalinterpolation)
                        #dc,dv = self.dget_cap(cycle,test_number=test_number )
                        v = v.tolist()
                        dQ = dQ.tolist()
                        
                        
                        header_x = "dQ cycle_no %i" % cycle
                        header_y = "voltage cycle_no %i" % cycle
                        dQ.insert(0,header_x)
                        v.insert(0,header_y)
                        
                        out_data.append(v)  
                        out_data.append(dQ)
                        
                    except:
                        print "could not extract cycle %i" % (cycle)
                        
                
                # Saving cycles in one .csv file (x,y,x,y,x,y...)
                #print "saving the file with delimiter '%s' " % (sep)
                print "Trying to save dqdv discharge data to"
                print outname_discharge
                with open(outname_discharge, "wb") as f:
                    writer=csv.writer(f,delimiter=sep)
                    writer.writerows(itertools.izip_longest(*out_data))
                    # star (or asterix) means transpose (writing cols instead of rows)

        
 
    def save_datasets(self,_ext):
        sort_method = self.sort_method
        try:
            column_names, datasets = self.plotdata[_ext]
        except:
            print "could not find self.plotdata for %s" % (_ext)
            return -1

        outfile=self.prename+_ext+self.postname
        try:
            a = pd.concat(datasets, axis = 1)
        except:
            # not pandas
            print "\nNote! Probably not pandas"
            print "(%s)" % (outfile)
            
            new_datasets = []
            for dataset in datasets:
                new_datasets.append(pd.Series(dataset))
            print "added %i datasets to newlist" % len(new_datasets)
            try: # TODO should check that it is not empty here somewhere
                print "merging them..."
                a = pd.concat(new_datasets, axis = 1)
            except:
                print "Error: could not concatenate:\n  ", sys.exc_info()[0]
                return -1
                
        try:
            a.columns = column_names
        except:
            print "error in a.columns = column_names"
            print "a.columns:"
            print a.columns
            print "column_names:"
            print column_names
        a.index = range(1,len(a.index)+1)
        if sort_method is not None:
            try:
                a.sort_index(axis = 1, inplace = True)
            except:
                print "ERROR sort_index in save_datasets"
                print a
                if self.exit_on_sort_error:
                    print "exiting...."
                    sys.exit(-1)
                else:
                    print "data not sorted - continuing"
            #a.reindex_axis(sorted(df.columns), axis=1)
        a.to_csv(outfile,sep=self.sep)
   

    def save_raw(self):
        if self.export_raw:
            print "---saving raw-data---"
            savedir = self.savedir_raw
            try:
                self.d.exportcsv(savedir, sep=self.sep)
            except:
                print "Error in exporting raw data"
                
    def save_cycles(self):        
        if self.export_cycles:
            print "---saving cycles----"
            savedir = self.savedir_raw
            try:
                self.d.exportcsv(savedir, sep=self.sep, cycles = True , raw = False)
                
            except:
                print "Error in exporting cycles"
                
    def save_dqdv(self):
        if self.export_dqdv:
            print "---saving dqdv-data--"
            savedir = self.savedir_raw
#            try:
            self._export_dqdv(savedir, sep=self.sep)
#            except:
#                print "Error in exporting dqdv"
                
    def save_hdf5(self):
        if self.export_hdf5:
            datadir = self.prms.hdf5datadir           
            for f,test_number,name in zip(self.hdf5_fixed_files,range(len(self.d.tests)),self.allfiles):
                filename =  os.path.join(datadir,name)
                if f:
                    print "fixed hdf5 - not saved (%s)" % (name)
                    
                else:
                    #needs_updating = xxxx
                    #if needs_updating:
                    try:
                        if self.ensure_step_table:
                            self.d.ensure_step_table = True
                            
                        self.d.save_test(filename,test_number=test_number)
                    except:
                        print "Could not save",
                        print filename+".h5"
                    
#            fixed = self.hdf5_fixed_files
#            d.save_test(hdf5file, test_number = test_number))
                    
            # should do an export for each test in arbindata
            # should check if hdf5 file exists and if it needs updating
            # should check if they are marked as freezed (database)
            # need to implement freeze in database
            # need to load freeze from database


    def save_figs(self,):
        for canvas in self.fig.keys():
            self.save_fig(canvas = canvas)

    def save_fig(self,canvas = 1, filename = None):
        pickle_implemented = False # requires newer matplotlib veresion
        if filename is None:
            savedir = self.savedir
            prename = self.prename
            midname = "_canvas%s" % (str(canvas).zfill(3))
            
            lastname_log = ".txt"
            filename_log = prename + midname + lastname_log
            filename_log = os.path.join(savedir, filename_log)
            
            lastname_png = ".png"
            filename_png = prename + midname + lastname_png
            filename_png = os.path.join(savedir, filename_png)
        else:
            filename_png = filename
            filename_log = os.path.splitext(filename_png)[0]+".txt"

        self.fig[canvas].savefig(filename_png, dpi=self.dpi)
        self.figname[canvas]=filename_png
        print "saved file to:"
        print filename_png
        #---saving-figure-txt----
        txt_1 = self.figtxt_1[canvas]
        txt_2 = self.figtxt_2[canvas]
        with open(filename_log,'w') as f:
            f.write(txt_1)
            f.write(txt_2)
        print filename_log

        if pickle_implemented:
            lastname_pkl = ".pkl"
            filename_pkl = prename + midname + lastname_pkl
            filename_pkl = os.path.join(savedir, filename_pkl)
            pl.dump(self.fig[canvas],file(filename_pkl,'w'))
            print "pickled figure to:"
            print filename_pkl
            print "you can retrive figure later by loading from disk"
            print "e.g."
            print """"
                import pickle as pl
                import numpy as np

                # Load figure from disk and display"""

            print "            filename = %s" % filename_pkl
            print """
                fig_handle = pl.load(open('sinus.pickle','rb'))
                fig_handle.show()

                # get data
                fig_handle.axes[0].lines[0].get_data()
                """
        print


# --------- Axis tools --------------------------------------------------------

    def make_ticklabels_invisible(self,fig):
        for i, ax in enumerate(fig.axes):
            ax.text(0.5, 0.5, "ax%d" % (i+1), va="center", ha="center")
            for tl in ax.get_xticklabels() + ax.get_yticklabels():
                tl.set_visible(False)


    def set_nlocator(self, ax, ny = 4,nx = 6,prunex="both",pruney="both"):
        my_xlocator = MaxNLocator(nx, prune = prunex)
        my_ylocator = MaxNLocator(ny, prune = pruney)
        ax.xaxis.set_major_locator(my_xlocator)
        ax.yaxis.set_major_locator(my_ylocator)

    def remove_xticklabels(self, ax):
        for tl in ax.get_xticklabels():
            tl.set_visible(False)
            
    
    def get_axis(self, axis = None, canvas = None):

#        self.axes_lib[canvas] = {}
#        self.axes_lib[canvas]["_couleff"] = 0
#        self.axes_lib[canvas]["_dischargecap"] = 1
#        self.axes_lib[canvas]["_cumchargecap"] = 2
#        self.axes_lib[canvas]["_endvcharge"] = 3
#        self.axes_lib[canvas]["_endvdischarge"] = 4
#        self.axes_lib[canvas]["_irchrg"] = 5
#        self.axes_lib[canvas]["_irdischrg"] = 6


        if canvas is None:
            canvas = self.current_canvas
        try:
            if axis == "dischargecap":
                x = "_dischargecap"

            elif axis == "couleff":
                x = "_couleff"

            elif axis == "cumchargecap":
                x = "_cumchargecap"

            elif axis == "endvcharge":
                x = "_endvcharge"

            elif axis == "endvdischarge":
                x = "_endvdischarge"

            elif axis == "irchrg":
                x = "_irchrg"

            elif axis == "irdischrg":
                x = "_irdischrg"

            else:
                print "selecting dischargecap"
                x = "_dischargecap"


            ax_no = self.axes_lib[canvas][x]
            axis = self.fig[canvas].get_axes()[ax_no]
        except:
            print "could not retrieve axes for x = %s" % x
            try:
                print "axes in canvas %i:" % canvas
                print self.axes_lib[canvas]
            except:
                print "canvas not found"

            axis = None

        return axis

    def set_x_label(self, ax, plot_type = None, label = None, ycoord = None):
        if plot_type is not None:
            label = self.plotTypes[plot_type].x_label
        if label is not None:
            if ycoord is None:
                ycoord = self.xlabel_coord_down
            ax.set_xlabel(label)
            ax.yaxis.set_label_coords(0.5, ycoord)


    def set_y_label(self, ax, plot_type = None, label = None, position = "left",
                    xcoord = None):
        if plot_type is not None:
            label = self.plotTypes[plot_type].y_label

            
        if label is not None:

            if position == "right":
                if xcoord is None:
                    xcoord = self.ylabel_coord_right_1
                ax.set_ylabel(label, rotation = -90)
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")
                ax.yaxis.set_label_coords(xcoord, 0.5)

            elif position == "right_split":
                if xcoord is None:
                    xcoord = 1.1
                ax.set_ylabel(label, rotation = -90)
                ax.yaxis.set_label_position("right")
                ax.yaxis.set_label_coords(xcoord, 0.5)
            else:
                 if xcoord is None:
                     xcoord = self.ylabel_coord_left_1
                 ax.set_ylabel(label)
                 ax.yaxis.set_label_coords(xcoord, 0.5)
                 #ax.set_ylabel(label, labelpad=0.5)
                 #x_pos = ax.yaxis.get_label_coords() #does this exist?
                 #ax.get_yaxis().set_label_coords(-0.1,0.5)


    def scale_ax(self, plot_type, ax):
        self.scale_ax_x(plot_type, ax)
        self.scale_ax_y(plot_type, ax)

    def scale_ax_x(self, plot_type, ax):
        x0,x1 = self.plotTypes[plot_type].x_range
        delta = (x1-x0)*self.delta_ax
        ax.set_xlim([x0-delta,x1+delta])

    def scale_ax_y(self, plot_type, ax):
        y0,y1 = self.plotTypes[plot_type].y_range
        delta = (y1-y0)*self.delta_ax
        ax.set_ylim([y0-delta,y1+delta])

    def set_ylims(self, ax = "couleff", lim = [0.0,100.0]):
        for figno in self.fig.keys():
            print "setting ylims for canvas %i, ax = %s" % (figno, ax)
            print "lim:"
            print lim
            try:
                axis = self.get_axis(axis = ax, canvas = figno)
                axis.set_ylim(lim)
            except:
                "axis probably not found"
                
    def set_xlims(self, ax = "couleff", lim = [0.0,200.0]):
        for figno in self.fig.keys():
            print "setting ylims for canvas %i, ax = %s" % (figno, ax)
            print "lim:"
            print lim
            try:
                axis = self.get_axis(axis = ax, canvas = figno)
                axis.set_xlim(lim)
            except:
                "axis probably not found"

# --------- legend tools ------------------------------------------------------
    def get_legend(self,canvas=1):
        return self.leg[canvas][0]


    def get_legend_axes(self,canvas=1):
        ax_no = self.leg[canvas][1]
        return self.fig[canvas].get_axes()[ax_no]
        
    def print_legend_loc(self, canvas=1):
        leg = self.get_legend(canvas)
        ax  = self.get_legend_axes(canvas)
        self.drawfig(canvas) # Draw the figure so you can find the positon of the legend.

        # Get the bounding box of the original legend
        bb = leg.legendPatch.get_bbox().inverse_transformed(ax.transAxes)
        print "Legend position (x0,x1,y0,y1):"
        print bb.x0, bb.x1, bb.y0, bb.y1
        print "loc in set_legend_loc:"
        print "loc = [%f,%f]" % (bb.x0, bb.y0)

    def set_legend_loc(self, canvas=1, loc=[0.7,0.9]):
        # set new legend position
        leg = self.get_legend(canvas)
        ax  = self.get_legend_axes(canvas)
        self.drawfig(canvas) # Draw the figure so you can find the positon of the legend.

        # Get the bounding box of the original legend
        bb = leg.legendPatch.get_bbox().inverse_transformed(ax.transAxes)

        # Change to location of the legend.
        newX0 = loc[0]
        newX1 = loc[0] + bb.x0 - bb.x1
        newY0 = loc[1]
        newY1 = loc[1] + bb.y0 - bb.y1

        print "old legend position:"
        print bb.x0, bb.x1, bb.y0, bb.y1
        print "new legend position:"
        print newX0, newX1, newY0, newY1

        bb.set_points([[newX0, newY0], [newX1, newY1]])
        leg.set_bbox_to_anchor(bb)

    def move_legend(self,canvas=1, offset = [0.0,0.0]):
        # moves an already created legend
        leg = self.get_legend(canvas)
        ax  = self.get_legend_axes(canvas)
        self.drawfig(canvas) # Draw the figure so you can find the positon of the legend.

        # Get the bounding box of the original legend
        bb = leg.legendPatch.get_bbox().inverse_transformed(ax.transAxes)

        # Change to location of the legend.
        newX0 = bb.x0 + offset[0]
        newX1 = bb.x1 + offset[0]
        newY0 = bb.y0 + offset[1]
        newY1 = bb.y1 + offset[1]

        print "old legend position:"
        print bb.x0, bb.x1, bb.y0, bb.y1
        print "new legend position:"
        print newX0, newX1, newY0, newY1

        bb.set_points([[newX0, newY0], [newX1, newY1]])
        leg.set_bbox_to_anchor(bb)

        # Update the plot
        #plt.show()


    def make_legend_txt(self,txt):
        # trying to remove date_stamp
        do_strip = True
    #    if txt == graphite_reference_label:
    #        do_strip = False
    #    if txt == eSi_reference_label:
    #        do_strip = False
    #    if txt == milled_reference_label:
    #        do_strip = False
        if do_strip:
            try:
                t = txt.split("_")
                ntxt = "_".join(t[1:])
            except:
                ntxt = txt
        else:
            ntxt = txt
        return ntxt

    def flip(self,items, ncol):
        return itertools.chain(*[items[i::ncol] for i in range(ncol)])
        

    def create_legend(self,canvas=1, legend_type = None, legend_txt_list = None,
                      axes_no = None, loc = "upper right", shadow = False,
                      max_length = None, flip = False):

        # selecting axes to put legend in
        if axes_no is None:
            axes_no = self.default_legend_axes_number
        ax = self.fig[canvas].get_axes()[axes_no]

        # getting current handles and labels:
        handles, labels = ax.get_legend_handles_labels()
        fig_txt = "\nElectrodes:"

        if legend_type is None:
            legend_type = "minimal"
        if legend_type == "minimal":
            fig_txt+="\n"


        if legend_txt_list is None:
            legend_txt_list = []
            gtxt = self._make_group_list_txt()
            for el,label, mass, loading,g,gt in zip(labels,self.labels,self.allmasses,
                                                 self.loadings,
                                                 self.group,
                                                 gtxt):
                if legend_type == "full":
                    txt = "%s (%s) %4.2f mg %4.2f mg/cm2 (g %i)" % (el,label, float(mass),
                                                   float(loading), g)
                    fig_txt += txt

                elif legend_type == "minimal":
                    txt = "%s" % (gt)
                    fig_txt += "\t%s: ['%s'] (mass: %4.2f mg, loading: %4.2f mg/cm2)\n" % (txt, el,
                                            float(mass), float(loading))

                elif legend_type == "electrode_label":
                    txt = "%s (%s) " % (el,label)
                    fig_txt += " %s: (mass: %4.2f mg, loading: %4.2f mg/cm2);" % (txt,
                                                float(mass), float(loading))

                elif legend_type == "electrode":
                    txt = "%s" % (el)
                    fig_txt += " %s: (mass: %4.2f mg, loading: %4.2f mg/cm2);" % (txt,
                                                float(mass), float(loading))

                elif legend_type == "label":
                    txt = "%s" % (label)
                    fig_txt +=  "%s: [%s] (mass: %4.2f mg, loading: %4.2f mg/cm2);" % (txt, el,
                                            float(mass), float(loading))

                legend_txt_list.append(txt)


        #plt.legend(flip(handles, 2), flip(labels, 2), loc=9, ncol=2)

        #plt.grid('on')
        #plt.show()

        if max_length is None:
            self.leg[canvas][0] = ax.legend(handles,legend_txt_list, loc=loc, shadow = shadow)
            self.leg[canvas][1] = axes_no
        else:
            no_legends = len(legend_txt_list)
            ncol = no_legends/max_length
            remainder = no_legends%max_length
            if remainder > 0:
                ncol += 1
            if no_legends > max_length:
                print "here we should add a function to split into several columns"
                # use self.leg[canvas] = []
            if flip:
                self.leg[canvas][0] = ax.legend(self.flip(handles,ncol),self.flip(legend_txt_list,ncol), loc=loc, shadow = shadow,
                                            ncol = ncol)
            else:
                self.leg[canvas][0] = ax.legend(handles,legend_txt_list, loc=loc, shadow = shadow,
                                            ncol = ncol)
            self.leg[canvas][1] = axes_no

        self.figtxt_2[canvas] = fig_txt
        print "\nlegend object: self.leg[%i]" % (canvas)
        print "axes number: %i (for use as self.fig[%i].get_axes()[axes_no].do_stuff())" % (axes_no, canvas)

        print
        print "printing figure txt"
        print
        ftxt = self.figtxt_1[canvas] + self.figtxt_2[canvas]
        print ftxt




if __name__=="__main__":
    print "***running",
    print sys.argv[0]
#
#    buffer_reference_cc.srno  = 267 # thicker electrode (0.79)
#    buffer_reference_cc.srno  = 268 # thin electrode (0.54)
    # 281 - mixed milled rate
    # 816 - 60%Si CMC buffer
#    plot types:
#    1 - with end-voltage
#    2 - without end-voltage
#    3 - old    
#    4 - with all (including shifted cap and irc etc)
    
    """
    WARNING: total mass cannot be used if loading from hdf5 (should rewrite arbinreader -> hdf5)
    """    
    
    Refs = [816]
    Refs = None
    plot_type = 2
    legend_stack = 3
    a = summaryplot("sic_tem", bcol=5, refs = Refs, plot_type=plot_type,predirname="SiCAnode",
                    legend_stack = legend_stack,use_total_mass = False, only_first=False,
                    verbose = False, axis_txt_sub="Si",
                    dbc = False, export_raw = True, export_hdf5 = True, force_res = False,
                    ensure_step_table = True, # This ensures that files exported to hdf5 also includes step table
                    export_cycles = True,
                    export_dqdv = True,
                    fetch_onliners = False,
                    
                    )
    print "plotting"
    #plt.show()
    #a.set_ylims("couleff",[30.0,120])
    #a.set_ylims("dischargecap",[400,5000])
#    a.set_ylims("irdischrg",[])
    
    #a.ce_axes.set_ylim([97.0, 102.0])
    #a.endvc_axes.set_ylim([0.0, 1.2])
    #a.set_xlims(lim=[0,170])

    a.showfig() # showing individual figures (showfig(fignumber)) does not work in scripts
    print "ended figure"
    print "saving..."
    a.save_figs()

    print a.savedir
    print a.prename

    print "\n***ended",
    print sys.argv[0]
    
