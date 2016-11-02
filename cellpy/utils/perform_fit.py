# -*- coding: utf-8 -*-

"""Performing a fit using cellpy's utils tool "fitting_cell_ocv.py".

Importing all functions from fitting_cell_ocv and creating ocv_up and down
"""

from fitting_cell_ocv import define_model, fit_with_model, user_plot_voltage,\
    plot_params, print_params
from cellpy.readers import cellreader

import sys, os, csv, itertools
import matplotlib.pyplot as plt
import numpy as np

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

datafolder = r'..\data_ex'
# filename_up = r'20160805_test001_45_cc_01_ocvrlx_up.csv'
# filename_down = r'20160805_test001_45_cc_01_ocvrlx_down.csv'
filename_up = r'74_data_up.csv'
filename_down = r'74_data_down.csv'
filename_74 = r'20160830_sic006_74_cc_01.res'

# i_start_ini_down = 0.000153628   # from cycle 1-3
# i_start_after_down = 0.000305533   # from cycle 4-end
# i_start_down = [i_start_ini_down for _down in range(3)]
# for down_4 in range(len(data_down) - 3):
#     i_start_down.append(i_start_after_down)
#

# i_start_ini_up = 0.0001526552   # from cycle 1-3
# i_start_after_up = 0.0003045602   # from cycle 4-end
# i_start_up = [i_start_ini_up for _up in range(3)]
# for up_4 in range(len(data_up) - 3):
#     i_start_up.append(i_start_after_up)
contri = {'ct': 0.2, 'd': 0.8}
tau_guessed = {'ct': 50, 'd': 800}
v_start_up = 0.01
v_start_down = 1.
cell_mass = 0.86   # [g]
c_rate = [0.1, 0.05]   # 1/[h]
change_i = [3]
cell_capacity = 3.579   # [mAh / g]


def extract_cap(dataloadres):
    cap_vs_volt = []
    cap_vs_cycle = []
    fig_voltage = plt.figure()
    ax_volt = fig_voltage.add_subplot(111)
    ax_volt.set_title('Capacity vs. Voltage')
    ax_volt.set_xlabel('Cap (mAh)')
    ax_volt.set_ylabel('Voltage (V)')
    for cycle in d.get_cycle_numbers():
            if cycle == 48:
                break
            else:
                try:
                    print "getting capacity data for cycle %i" % cycle
                    cap, voltage = dataloadres.get_cap(cycle=cycle)
                    ax_volt.plot(cap, voltage)
                    plt.plot(cycle, cap)
                    cap_vs_cycle.append(cap)
                    cap_vs_cycle.append(cycle)
                    cap = cap.tolist()
                    voltage = voltage.tolist()

                    header_x = "Capacity (mAh) cycle_no %i" % cycle
                    header_y = "Coltage (V) cycle_no %i" % cycle
                    cap.insert(0, header_x)
                    voltage.insert(0, header_y)
                    cap_vs_volt.append(cap)
                    cap_vs_volt.append(voltage)
                except:
                    print "could not extract cycle %i" % cycle
    return np.array(cap_vs_volt), np.array(cap_vs_cycle)

data = os.path.join(datafolder, filename_74)
d = cellreader.cellpydata()
d.loadres(data)
d.set_mass(cell_mass)
volt, cycle = extract_cap(d)
# plt.figure()
# plt.plot(cycle[0], cycle[1])
# plt.title('Capacity vs. Cycles')
# plt.xlabel('Cycles')
# plt.ylabel('Cap (mAh)')


# model_up, time_up, voltage_up = define_model(filepath=datafolder,
#                                              filename=filename_up,
#                                              guess_tau=tau_guessed,
#                                              contribution=contri,
#                                              c_rate=c_rate[0],
#                                              ideal_cap=cell_capacity,
#                                              mass=cell_mass,
#                                              v_start=v_start_up)
# fit_up, rc_para_up = fit_with_model(model_up, time_up, voltage_up, tau_guessed,
#                                     contri, c_rate, change_i, cell_capacity,
#                                     cell_mass, v_start_up)

# model_down, time_down, voltage_down = define_model(filepath=datafolder,
#                                                    filename=filename_down,
#                                                    guess_tau=tau_guessed,
#                                                    contribution=contri,
#                                                    c_rate=c_rate[0],
#                                                    ideal_cap=cell_capacity,
#                                                    mass=cell_mass,
#                                                    v_start=v_start_down)
# fit_down, rc_para_down = fit_with_model(model_down, time_down, voltage_down,
#                                         tau_guessed, contri, c_rate, change_i,
#                                         cell_capacity, cell_mass, v_start_down)
# plot_params(time_up, voltage_up, fit_up, rc_para_up)
# plot_params(time_down, voltage_down, fit_down, rc_para_down)
# user_plot_voltage(time_up, voltage_up, fit_up)
# user_plot_voltage(time_down, voltage_down, fit_down)

# print_params(fit_down, rc_para_down)

# question_ex = 'Cycles after discharge you want to plot, separated with ' \
#               'space. If you don'"'"'t want to plot any press ' \
#               'enter. Write "a" for all plots: -->'
# user_cycle_ex = raw_input(question_ex)
# ex_ocv = pd.Series([pd.DataFrame(zip(t, u), columns=['time', 'voltage'])])
# ocv_cycle(ex_ocv, user_cycle_ex, v_start_up, [0.0007508742])
# question_up = 'Cycles after discharge you want to plot, separated with ' \
#               'space. If you don'"'"'t want to plot any press ' \
#               'enter. Write "a" for all plots: -->'
# user_cycles_up = raw_input(question_up)
# fit_with_model(data_up, user_cycles_up, v_start_up, i_start)
# plt.show()
# question_down = 'Cycles after charge you want to plot, separated with ' \
#                 'space. If you don'"'"'t want to plot any press ' \
#                 'enter. Write "a" for all plots: -->'
# user_cycles_down = raw_input(question_down)
# fit_with_model(data_down, user_cycles_down, v_start_down, i_start)
plt.show()


