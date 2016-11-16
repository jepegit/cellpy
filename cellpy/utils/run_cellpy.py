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

    data_normal = os.path.join(outfolder, normal)
    data_normal = pd.read_csv(data_normal, sep=';')
    df_normal = pd.DataFrame(data_normal)

    data_steps = os.path.join(outfolder, steps)
    data_steps = pd.read_csv(data_steps, sep=';')
    df_steps = pd.DataFrame(data_steps)

    data_stats = os.path.join(outfolder, stats)
    data_stats = pd.read_csv(data_stats, sep=';')
    df_stats = pd.DataFrame(data_stats)

    data_cap_volt = os.path.join(outfolder, cap_volt)
    data_cap_volt = pd.read_csv(data_cap_volt, sep=';')
    df_cap_volt = pd.DataFrame(data_cap_volt)

    # print df_steps.info()
    # print df_stats.info()
    # print df_steps['V_start']
    # normal_lith_volt = df_normal["Voltage"]
    # normal_current = df_normal["Current"]
    # dvdt = df_normal["dV/dt"]
    # normal_lith_volt.plot()

    charge_cap = df_stats["Charge_Capacity(mAh/g)"]
    discharge_cap = df_stats["Discharge_Capacity(mAh/g)"]
    cycle_cap = zip(charge_cap, discharge_cap)
    cycle_cap_df = pd.DataFrame(cycle_cap,
                                columns=["Charge_Capacity(mAh/g)",
                                         "Discharge_Capacity(mAh/g)"])

    col_eff = df_stats["Coulombic_Efficiency(percentage)"]   # Q_out / Q_inn
    x_range = np.arange(1, len(col_eff) + 1)

    plt.figure()
    plt.plot(x_range, col_eff, '-ok')
    plt.plot(100*np.ones(2 * len(col_eff)), '-k')

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    plt.xticks(np.arange(1, len(col_eff) + 1, 2.0))
    plt.gca().set_xlim([-0.1, len(col_eff) + 1])
    plt.gca().set_ylim([col_eff[1]-0.5, 100.5])
    plt.gca().title.set_position([.5, 1.05])
    plt.title('Coulombic Efficiency ($\eta$)', size=30)
    plt.legend(['$\eta = Q_{out}/Q_{in}$'], loc='best',
               prop={'size': 20})
    plt.xlabel('Cycle number', size=20)
    plt.ylabel('$\eta$ (%)', size=25)

    # Plotting cycle vs. cap
    plt.figure()
    plt.plot(x_range, cycle_cap_df["Charge_Capacity(mAh/g)"], '^b',
             x_range, cycle_cap_df["Discharge_Capacity(mAh/g)"], 'or')

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    plt.gca().title.set_position([.5, 1.05])
    plt.xticks(np.arange(1, len(col_eff) + 1, 2.0))
    plt.legend(['Charge Capacity (Delithiation)',
                'Discharge capacity (Lithiation)'], loc='center right',
               prop={'size': 20})

    plt.title('Capacity vs. Cycle', size=30)
    plt.xlabel('Cycle number', size=15)
    plt.ylabel('Capacity (mAh/g)', size=15)

    # plt.savefig(os.path.join(fig_folder, 'cap_cycle_sic006_74.pdf'))

    # Plotting voltage vs. cap
    capacity_sorting = []
    voltage_sorting = []

    for df_name in df_cap_volt:
        if 'cap' in df_name:
            capacity_sorting.append(df_cap_volt[df_name])
        else:
            voltage_sorting.append(df_cap_volt[df_name])

    plt.figure()
    number_plots = (0, 1, 2, 4, 9, -1)
    for cycle in number_plots:
        plt.plot(capacity_sorting[cycle], voltage_sorting[cycle])

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(15)
    plt.title('Capacity vs. Voltage', size=30)
    plt.gca().title.set_position([.5, 1.05])
    plt.gca().set_ylim([0.03, 1])
    plt.yticks(np.arange(0, 1.1, 0.1))
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
    ocv_down = r'ocvrlx_down.csv'
    ocv_up = r'ocvrlx_up.csv'
    datafolder = r'..\data_ex'
    datafolder_out = r'..\outdata'
    filenames = [f for f in os.listdir(datafolder)
                 if os.path.isfile(os.path.join(datafolder, f)) and
                 str(f).endswith('.res')]
    filenames.sort()

    # bec01_07-09 is without additives and bec01_01-03 with additives
    # save_and_plot_cap(datafolder, filenames[0], datafolder_out,
    #                   cell_mass['bec01_01'])




    # save_and_plot_cap(datafolder, r'20160830_sic006_74_cc_01.res',
    #                   datafolder_out, cell_mass['sic006_74'])

    # making plots HERE !!!! Change cell mass name

    # for name in cell_mass:
    # save_and_plot_cap(datafolder, name,
    #                   datafolder_out, cell_mass[name])
    # save_and_plot_cap(datafolder, name, datafolder_out,
    #                   cell_mass[name], type_data=ocv_down[:-4])

    name = filenames[1]
    up = True
    if up:
        rlx_text = 'after lithiation'
    else:
        rlx_text = 'after delithiation'
    print name
    if up:
        time, voltage, fit, rc_para = \
            fitting_cell(name[:-3]+ocv_up, datafolder_out, cell_mass[name],
                         contri, tau_guessed, v_start_up, c_rate, change_i)
    else:
        time, voltage, fit, rc_para = \
            fitting_cell(name[:-3]+ocv_down, datafolder_out, cell_mass[name],
                         contri, tau_guessed, v_start_down, c_rate, change_i)

    cycles_number = (3, 4, 7, 9, 10, 19, 29, len(voltage) - 1)
    leg = []
    plt.figure()
    for volt_i in cycles_number:
        ocv = voltage[volt_i][::20]
        time_ocv = time[volt_i][::20]
        plt.errorbar(time_ocv, ocv, yerr=v_err, fmt='o')
        leg.append('OCV-relaxation for cycle %s' % (volt_i + 1))
    for tick_volt in plt.gca().xaxis.get_major_ticks():
        tick_volt.label.set_fontsize(15)
    for tick_volt in plt.gca().yaxis.get_major_ticks():
        tick_volt.label.set_fontsize(15)

    plt.gca().title.set_position([.5, 1.05])
    plt.title('Open Circuit Voltage Relaxation ' + rlx_text, size=30)
    plt.xlabel('Time', size=20)
    plt.ylabel('Relaxation voltage (V)', size=20)
    plt.legend(leg, loc='best', prop={'size': 20})


    # plt.xticks(np.arange(1, len(col_eff) + 1, 2.0))
        # plt.gca().set_xlim([-0.1, len(col_eff) + 1])
        # plt.gca().set_ylim([col_eff[1]-0.5, 100.5])
    # fco.plot_params(voltage, fit, rc_para, i_err=mass_frac_err)
    # fco.user_plot_voltage(time, voltage, fit, conf)
    # fco.print_params(fit, rc_para)

    # plotting_stuff(name, datafolder_out)
    # Comment: bec01_01 is the best of the bec files and is closest to sic006_74
    # luckily is bec01_01 with additives --> we can start comparing
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
