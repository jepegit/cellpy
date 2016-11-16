# -*- coding: utf-8 -*-

"""Using cellpy.

Importing all cell files and functions from perform_fit.py.
This script is an example of how cellpy can be used.

"""

from perform_fit import fitting_cell, save_and_plot_cap
import fitting_cell_ocv as fco

import sys, os, csv, itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def plotting_stuff(filename, outfolder):
    """Based on same plot as in perform_fit.save_and_plot_cap().

    Difference is that I can freely change here as run_cellpy is not suppose
    to be a part of cellpy, but instead a user example.

    Make changes in this function to modify plot as you like.

    Args:
        filename (str): Filename of cell.
        outfolder (str): Folder in which the filename lays.

    Returns:
        plt.figure(): A desired plot

    """

    # getting stats and capacity voltage table
    normal = filename[:-4] + '_normal.csv'
    steps = filename[:-4] + '_steps.csv'
    stats = filename[:-4] + '_stats.csv'
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
    cycle_cap_df = pd.DataFrame(cycle_cap,
                                columns=["Charge_Capacity(mAh/g)",
                                         "Discharge_Capacity(mAh/g)"])

    # Plotting cycle vs. cap
    plt.figure()
    plt.plot(cycle_cap_df["Charge_Capacity(mAh/g)"], '^b',
             cycle_cap_df["Discharge_Capacity(mAh/g)"], 'or')

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    plt.legend(['Charge Capacity', 'Discharge capacity'], loc='best',
               prop={'size':15})
    plt.title('Capacity vs. Cycle', size=30)
    plt.xlabel('# Cycle', size=15)
    plt.ylabel('Capacity (mAh/g)', size=15)
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

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    plt.title('Capacity vs. Voltage', size=30)
    plt.xlabel('Capacity (mAh/g)', size=15)
    plt.ylabel('Voltage (V)', size=15)
    plt.legend(loc='best', prop={'size': 15})


if __name__ == '__main__':

    contri = {'ct': 0.2, 'd': 0.8}
    tau_guessed = {'ct': 50, 'd': 800}
    v_start_up = 0.01
    v_start_down = 1.
    cell_mass = {'20160805_test001_45_cc_01.res': 0.85,
                 '20160830_sic006_74_cc_01.res': 0.86,
                 '20161101_bec01_01_cc_01.res': 0.38,
                 '20161101_bec01_02_cc_01.res': 0.36,
                 '20161101_bec01_03_cc_01.res': 0.38,
                 '20161101_bec01_07_cc_01.res': 0.42,
                 '20161101_bec01_08_cc_01.res': 0.36,
                 '20161101_bec01_09_cc_01.res': 0.35}   # [mg]
    c_rate = [0.05, 0.1]   # 1/[h]
    change_i = [3]
    cell_capacity = 3.579   # [mAh / mg]

    conf = False
    copp_err = 0.2   # in %. std/best_estimate. best_estimate = 28.7, std. = 0.0634
    mass_err_scale = 0.01   # In %. What is the uncertainty of the scale? 0.00001mg?
    mass_frac_err = copp_err + mass_err_scale   # In %. cell_mass=mass_tot-mass_copp
    i_err = mass_frac_err   # i_err only has mass as error ==> same frac error
    # i_err = 0.1   # % in full scale range
    v_err = 0.00095   # [V}

    # fig_folder = r'C:\Users\torkv\OneDrive - Norwegian University of Life '\
    #              r'Sciences\Documents\NMBU\master\ife\thesis tor\fig\results'
    ocv_down = r'ocv_down.csv'
    ocv_up = r'ocv_up.csv'
    datafolder = r'..\data_ex'
    datafolder_out = r'..\outdata'
    filenames = [f for f in os.listdir(datafolder)
                 if os.path.isfile(os.path.join(datafolder, f)) and
                 str(f).endswith('.res')]
    filenames.sort()

    # bec01_07-09 is without additives and bec01_01-03 with additives
    # save_and_plot_cap(datafolder, filenames[0], datafolder_out,
    #                   cell_mass['bec01_01'])


    # save_and_plot_cap(datafolder, r'20160805_test001_45_cc_01.res',
    #                   datafolder_out, cell_mass['sic006_45'])
    # fitting_cell(r'20160805_test001_45_cc_01.ocv_up.csv', datafolder_out, cell_mass[
    #     'sic006_45'], contri, tau_guessed, v_start_up, c_rate, change_i)

    # save_and_plot_cap(datafolder, r'20160830_sic006_74_cc_01.res',
    #                   datafolder_out, cell_mass['sic006_74'])

    # making plots HERE !!!! Change cell mass name
    name = filenames[1]
    save_and_plot_cap(datafolder, name, datafolder_out,
                      cell_mass[name], type_data=ocv_down[:-4])

    plotting_stuff(name, datafolder_out)

    # time_down, voltage_down, fit_down, rc_para_down = fitting_cell(
    #     filenames[1][:-3]+ocv_down, datafolder_out, cell_mass[filenames[1]],
    #     contri, tau_guessed, v_start_down, c_rate, change_i, conf=conf, v_err=v_err)

    # time_up, voltage_up, fit_up, rc_para_up = fitting_cell(
    #     filenames[1][:-3]+ocv_up, datafolder_out, cell_mass[filenames[1]],
    #     contri, tau_guessed, v_start_up, c_rate, change_i, conf=conf, v_err=v_err)


    # fco.plot_params(voltage_down, fit_down, rc_para_down, i_err=i_err)

    # finding current for all cells. Not very efficient. Consider other methods.
    # i_err_dict = {}
    # for cell, mass in cell_mass.items():
    #     step = 0
    #     i_err_temp = []
    #     for i in range(len(time)):
    #         # Checking if cycle number i is in change_i
    #         if i in change_i:
    #             step += 1
    #         i_s = c_rate[step] * cell_capacity * mass / 1000
    #         c_err = i_s * mass_frac_err   # in A
    #         i_err_temp.append(c_err)
    #     i_err_dict[cell] = i_err_temp
    # for cell_name, i_s in i_start_dict.items():
    #     i_err_temp = []
    #     for c_i, c in enumerate(i_s):
    #         if c_i in change_i:
    #             c_1 = i_s[c_i - 1] * mass_frac_err   # in %
    #             c_current = c * mass_frac_err   # in %
    #             i_err_temp.extend([c_1, c_current])
    #     i_err_dict[cell_name] = i_err_temp

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

    # Calculating current error from error in mass

    # for name_cell, fit in fit.items():
    #     fco.plot_params(voltage[name_cell], fit, rc_para[name_cell],
    #                     i_err=mass_frac_err)
    #     fco.user_plot_voltage(time[name_cell], voltage[name_cell], fit, conf)
    #     fco.print_params(fit, rc_para[name_cell)

    plt.show()
