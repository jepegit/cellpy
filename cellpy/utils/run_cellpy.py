# -*- coding: utf-8 -*-

"""Using cellpy.

Importing all cell files and functions from perform_fit.py.
This script is an example of how to run cellpy by a user.

"""

from perform_fit import fitting_cell, save_and_plot_cap
import fitting_cell_ocv as fco

import sys, os, csv, itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

contri = {'ct': 0.2, 'd': 0.8}
tau_guessed = {'ct': 50, 'd': 800}
v_start_up = 0.01
v_start_down = 1.
cell_mass = {'sic006_45': 0.85, 'sic006_74': 0.86, 'bec01_01': 0.38,
             'bec01_02': 0.36,
             'bec01_03': 0.38, 'bec01_07': 0.42, 'bec01_08': 0.36,
             'bec01_09': 0.35}   # [mg]
c_rate = [0.05, 0.1]   # 1/[h]
change_i = [3]
cell_capacity = 3.579   # [Ah / g]
conf = False

# fig_folder = r'C:\Users\torkv\OneDrive - Norwegian University of Life '\
#              r'Sciences\Documents\NMBU\master\ife\thesis tor\fig\results'
datafolder = r'..\data_ex'
datafolder_out = r'..\outdata'
filenames = [f for f in os.listdir(datafolder)
             if os.path.isfile(os.path.join(datafolder, f)) and
             str(f).endswith('.res') and 'bec' in f]

# bec01_07-09 is without additives and bec01_01-03 with additives
# save_and_plot_cap(datafolder, filenames[0], datafolder_out,
#                   cell_mass['bec01_01'])

# save_and_plot_cap(datafolder, r'20160805_test001_45_cc_01.res',
#                   datafolder_out, cell_mass['sic006_45'])
# fitting_cell(r'20160805_test001_45_cc_01.ocv_up.csv', datafolder_out, cell_mass[
#     'sic006_45'], contri, tau_guessed, v_start_up, c_rate, change_i)

# save_and_plot_cap(datafolder, r'20160830_sic006_74_cc_01.res',
#                   datafolder_out, cell_mass['sic006_74'])

# time, voltage, fit, rc_para = fitting_cell(r'74_data_down.csv', datafolder,
#                                            cell_mass['sic006_45'],
#                                            contri, tau_guessed,
#                                            v_start_down, c_rate,
#                                            change_i, conf=conf)

# Plot trace of confidential interval... Doesn't really make much sense I think
pass
# for cycle_fit in fit[4:5]:
#     plt.figure()
#     trace = cycle_fit.ci_out[1]
#     x1, y1, prob1 = trace['v0_ct']['v0_ct'], trace['v0_ct']['tau_ct'], \
#                     trace['v0_ct']['prob']
#     x2, y2, prob2 = trace['tau_ct']['tau_ct'], trace['tau_ct']['v0_ct'], \
#                     trace['tau_ct']['prob']
#     plt.scatter(x1, y1, prob1)
#     plt.scatter(x2, y2, prob2)
#     plt.xlabel('v0_ct')
#     plt.ylabel('tau_ct')
#     plt.title('Trace from confidential interval after delithiation')
#     fig = plt.gcf()
#     fig.canvas.set_window_title('trace_cycle4_after_delith')
#
# fco.plot_params(voltage, fit, rc_para)
# fco.user_plot_voltage(time, voltage, fit, conf)
# fco.print_params(fit, rc_para)

plt.show()
