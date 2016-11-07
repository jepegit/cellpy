# -*- coding: utf-8 -*-

"""Performing a fit using cellpy's utils tool "fitting_cell_ocv.py".

Importing all functions from fitting_cell_ocv and creating ocv_up and down

TODO:
    -Make nicer volt_cap plots with proper legends
"""

from fitting_cell_ocv import define_model, fit_with_model, user_plot_voltage,\
    plot_params, print_params
# from cellpy.readers import cellreader
from scripts.reading_cycle_data import making_csv

# import sys, os, csv, itertools
# import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def fitting_cell(filename, outfolder, cell_mass, contri, tau_guessed,
                 v_start, c_rate, change_i, cell_capacity=3.579):
    """Fitting measured data from cell with cellpy.

    Args:
        filename (str): The ocv relaxation filename for up- or downwards relax.
        outfolder (str): Exact path where to save .csv data
        cell_mass(float): The mass of the active material in mg.
        contri (:obj: 'dict' of :obj: 'float'): Assumed contribution
        from each rc-circuit. Help guessing the initial start voltage value
        of the rc-circuit.
        tau_guessed (:obj: 'dict' of :obj: 'float'): User guessing what the time
        constant for each rc-circuit might be.
        v_start (float): Starting voltage for ocv-relaxation after IR-drop.
        c_rate (:obj: 'list' of :obj: 'float'): The C-rate which the cell was
        discharged or charged with before cycle = change_i.
        change_i (:obj: 'list' of :obj: 'int'): The cycle number where the
        C-rate (AKA Current) is changed. len(c_rate) = len(change_i) + 1
        cell_capacit (float): Theoretical specific capacity of the cell [Ah/g].

    Returns:
        Fitted data and plots
    """

    model, time, voltage = define_model(filepath=outfolder,
                                        filename=filename,
                                        guess_tau=tau_guessed,
                                        contribution=contri,
                                        c_rate=c_rate[0],
                                        ideal_cap=cell_capacity,
                                        mass=cell_mass,
                                        v_start=v_start)

    fit, rc_para = fit_with_model(model, time, voltage, tau_guessed,
                                  contri, c_rate, change_i, cell_capacity,
                                  cell_mass, v_start)
    plot_params(voltage, fit, rc_para)
    user_plot_voltage(time, voltage, fit)
    print_params(fit, rc_para)


def save_and_plot_cap(filepath, filename, outfolder, mass_celll):
    """Making capacity vs. voltage and capacity vs. cycle data.

    Args:
        filepath (str): The exact path to the folder where the data lies.
        filename (str): The ocv relaxation filename for up- or downwards relax.
        outfolder (str): Exact path where to save .csv data
        mass_celll (float): Mass of active material in cell [mg]

    Returns:
        Fitted data and plots
    """
    # imported cycle data from arbin and saved in "outdata" folder as .csv
    data = os.path.join(filepath, filename)
    making_csv(data, outfolder, mass_celll)

    normal = filename[:-4] + '_normal.csv'
    stats = filename[:-4] + '_stats.csv'
    steps = filename[:-4] + '_steps.csv'
    cap_volt = filename + '_cap_voltage.csv'

    data_stats = os.path.join(outfolder, stats)
    data_stats = pd.read_csv(data_stats, sep=';')
    df_stats = pd.DataFrame(data_stats)

    data_cap_volt = os.path.join(outfolder, cap_volt)
    data_cap_volt = pd.read_csv(data_cap_volt, sep=';')
    df_cap_volt = pd.DataFrame(data_cap_volt)

    charge_cap = df_stats["Charge_Capacity(mAh/g)"]
    discharge_cap = df_stats["Discharge_Capacity(mAh/g)"]
    cycle_cap = zip(charge_cap, discharge_cap)
    cycle_cap_df = pd.DataFrame(cycle_cap, columns=["Charge_Capacity(mAh/g)",
                                                    "Discharge_Capacity(mAh/g)"])

    # Plotting cycle vs. cap
    plt.figure()
    plt.plot(cycle_cap_df["Charge_Capacity(mAh/g)"], '^b',
             cycle_cap_df["Discharge_Capacity(mAh/g)"], 'or')
    plt.legend(['Charge Capacity', 'Discharge capacity'], loc='best')
    plt.title('Capacity vs. Cycle')
    plt.xlabel('# Cycle')
    plt.ylabel('Capacity (mAh/g)')
    # plt.savefig(os.path.join(fig_folder, 'cap_cycle_sic006_74.pdf'))

    # Plotting voltage vs. cap
    capacity_sorting = []
    voltage_sorting = []
    for name in df_cap_volt:
        if 'cap' in name:
            capacity_sorting.append(df_cap_volt[name])
        else:
            voltage_sorting.append(df_cap_volt[name])

    plt.figure()
    number_plots = len(capacity_sorting)
    for cycle in range(number_plots):
        plt.plot(capacity_sorting[cycle], voltage_sorting[cycle])
    plt.title('Capacity vs. Voltage')
    plt.xlabel('Capacity (mAh/g)')
    plt.ylabel('Voltage (V)')
    plt.legend(loc='best')

    # plt.savefig(os.path.join(fig_folder, 'volt_cap_sic006_74.pdf'))

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

# contri = {'ct': 0.2, 'd': 0.8}
# tau_guessed = {'ct': 50, 'd': 800}
# v_start_up = 0.01
# v_start_down = 1.
# cell_mass = {'sic006_74': 0.86, 'bec01_07': 0.42, 'bec01_08': 0.36,
#              'bec01_09': 0.35}
# # [mg]
# c_rate = [0.05, 0.1]   # 1/[h]
# change_i = [3]
# cell_capacity = 3.579   # [Ah / g]
#
# fig_folder = r'C:\Users\torkv\OneDrive - Norwegian University of Life '\
#              r'Sciences\Documents\NMBU\master\ife\thesis tor\fig\results'
# datafolder = r'..\data_ex'
# datafolder_out = r'..\outdata'
# filenames = [f for f in os.listdir(datafolder)
#              if os.path.isfile(os.path.join(datafolder, f)) and
#              str(f).endswith('.res') and 'bec' in f]
# # bec01_07-09 is without additives and bec01_01-03 with additives
# save_and_plot_cap(datafolder, filenames[6], datafolder_out,
#                   cell_mass['bec01_07'])
# plt.show()

# filename_up = r'20160805_test001_45_cc_01_ocvrlx_up.csv'
# filename_down = r'20160805_test001_45_cc_01_ocvrlx_down.csv'
# filename_up = r'74_data_up.csv'
# filename_down = r'74_data_down.csv'
# filename_74 = r'20160830_sic006_74_cc_01.res'





# imported cycle data from arbin and saved in "outdata" folder as .csv
# data = os.path.join(datafolder, filename_74)
# datafolder_out = r'..\outdata'
# # making_csv(data, datafolder_out, cell_mass)
#
# normal = filename_74[:-4] + '_normal.csv'
# stats = filename_74[:-4] + '_stats.csv'
# steps = filename_74[:-4] + '_steps.csv'
# cap_volt = filename_74 + '_cap_voltage.csv'
#
# data_stats = os.path.join(datafolder_out, stats)
# data_stats = pd.read_csv(data_stats, sep=';')
# df_stats = pd.DataFrame(data_stats)
#
# data_cap_volt = os.path.join(datafolder_out, cap_volt)
# data_cap_volt = pd.read_csv(data_cap_volt, sep=';')
# df_cap_volt = pd.DataFrame(data_cap_volt)
#
# charge_cap = df_stats["Charge_Capacity(mAh/g)"]
# discharge_cap = df_stats["Discharge_Capacity(mAh/g)"]
# cycle_cap = zip(charge_cap, discharge_cap)
# cycle_cap_df = pd.DataFrame(cycle_cap, columns=["Charge_Capacity(mAh/g)",
#                                                 "Discharge_Capacity(mAh/g)"])
#
# # Plotting cycle vs. cap
# plt.figure()
# plt.plot(cycle_cap_df["Charge_Capacity(mAh/g)"], '^b',
#          cycle_cap_df["Discharge_Capacity(mAh/g)"], 'or')
# plt.legend(['Charge Capacity', 'Discharge capacity'], loc='best')
# plt.title('Capacity vs. Cycle')
# plt.xlabel('# Cycle')
# plt.ylabel('Capacity (mAh/g)')
# # plt.savefig(os.path.join(fig_folder, 'cap_cycle_sic006_74.pdf'))
#
# # Plotting voltage vs. cap
# capacity_sorting = []
# voltage_sorting = []
# for name in df_cap_volt:
#     if 'cap' in name:
#         capacity_sorting.append(df_cap_volt[name])
#     else:
#         voltage_sorting.append(df_cap_volt[name])
#
# plt.figure()
# number_plots = len(capacity_sorting)
# for cycle in range(number_plots):
#     plt.plot(capacity_sorting[cycle], voltage_sorting[cycle])
# plt.title('Capacity vs. Voltage')
# plt.xlabel('Capacity (mAh/g)')
# plt.ylabel('Voltage (V)')
# plt.legend(loc='center left',
#            bbox_to_anchor=(1, 0.5))
#
# plt.savefig(os.path.join(fig_folder, 'volt_cap_sic006_74.pdf'))


# model_up, time_up, voltage_up = define_model(filepath=datafolder,
#                                              filename=filename_up,
#                                              guess_tau=tau_guessed,
#                                              contribution=contri,
#                                              c_rate=c_rate[0],
#                                              ideal_cap=cell_capacity,
#                                              mass=cell_mass,
#                                              v_start=v_start_up)
#
# fit_up, rc_para_up = fit_with_model(model_up, time_up, voltage_up, tau_guessed,
#                                     contri, c_rate, change_i, cell_capacity,
#                                     cell_mass, v_start_up)
# plot_params(voltage_up, fit_up, rc_para_up)
# user_plot_voltage(time_up, voltage_up, fit_up)
#
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
#
# plot_params(voltage_down, fit_down, rc_para_down)
# user_plot_voltage(time_down, voltage_down, fit_down)
#
# print_params(fit_down, rc_para_down)
# print_params(fit_up, rc_para_up)
# plt.show()
