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


def plotting_stuff(filename, folder, fig_folder, cell_name, m_s=20, ti_la_s=35):
    """Based on same plot as in perform_fit.save_and_plot_cap().

    Difference is that I can freely change here as run_cellpy is not suppose
    to be a part of cellpy, but instead a user example.

    Make changes in this function to modify plot as you like.

    Args:
        filename (str): Filename of cell.
        folder (str): Folder in which the filename lays.
        fig_folder(str): Which folder to save the figures.
        cell_name (str): Converted cell name to thesis cell name.
        m_s (int): Markersize for plots.
        ti_la_s (int): Ticks and labels font size.

    Returns:
        plt.figure(): A desired plot

    """
    # Title size
    title_s = ti_la_s + 10

    # getting stats and capacity voltage table
    normal = filename[:-4] + '_normal.csv'
    steps = filename[:-4] + '_steps.csv'
    stats = filename[:-4] + '_stats.csv'
    cap_volt = filename + '_cap_voltage.csv'

    data_normal = os.path.join(folder, normal)
    data_normal = pd.read_csv(data_normal, sep=';')
    df_normal = pd.DataFrame(data_normal)

    data_steps = os.path.join(folder, steps)
    data_steps = pd.read_csv(data_steps, sep=';')
    df_steps = pd.DataFrame(data_steps)

    data_stats = os.path.join(folder, stats)
    data_stats = pd.read_csv(data_stats, sep=';')
    df_stats = pd.DataFrame(data_stats)

    data_cap_volt = os.path.join(folder, cap_volt)
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

    plt.figure(figsize=(20, 22))
    plt.plot(x_range, col_eff, '-ok', ms=m_s)
    plt.plot(100*np.ones(2 * len(col_eff)), '-k')
    # plt.gca().invert_yaxis()
    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    plt.xticks(np.arange(1, len(col_eff) + 1, 1.0))
    # plt.gca().set_xlim([-0.1, len(col_eff) + 1])
    # plt.gca().set_ylim([col_eff[1]-0.5, 100.5])
    plt.gca().title.set_position([.5, 1.05])
    plt.title('Coulombic Efficiency ($\eta$) for cell %s' % cell_name,
              size=title_s)
    plt.legend(['$\eta = Q_{out}/Q_{in}$'], loc='center right',
               prop={'size': ti_la_s})
    plt.xlabel('Cycle number', size=ti_la_s)
    plt.ylabel('$\eta$ (%)', size=ti_la_s)
    fig = 'coulombic_eff_%s.pdf' % cell_name
    plt.savefig(os.path.join(fig_folder, fig), dpi=300)

    # Plotting cycle vs. cap
    plt.figure(figsize=(20, 22))
    plt.plot(x_range, cycle_cap_df["Charge_Capacity(mAh/g)"], '^b', ms=m_s)
    plt.plot(x_range, cycle_cap_df["Discharge_Capacity(mAh/g)"], 'or', ms=m_s)

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    plt.gca().title.set_position([.5, 1.05])
    plt.xticks(np.arange(1, len(col_eff) + 1, 1.0))
    plt.legend(['Charge Capacity (Delithiation)',
                'Discharge capacity (Lithiation)'], loc='best',
               prop={'size': ti_la_s})

    plt.title('Capacity vs. Cycle for cell %s' % cell_name, size=title_s)
    plt.xlabel('Cycle number', size=ti_la_s)
    plt.ylabel('Capacity (mAh/g)', size=ti_la_s)

    plt.savefig(os.path.join(fig_folder, 'cap_cycle_%s.pdf' % cell_name),
                dpi=300)

    # Plotting voltage vs. cap
    capacity_sorting = []
    voltage_sorting = []

    for df_name in df_cap_volt:
        if 'cap' in df_name:
            capacity_sorting.append(df_cap_volt[df_name])
        else:
            voltage_sorting.append(df_cap_volt[df_name])

    plt.figure(figsize=(20, 22))
    number_plots = (0, 1, 2, 4, 9, -2)
    for cycle in number_plots:
        plt.plot(capacity_sorting[cycle], voltage_sorting[cycle], linewidth=3)

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    plt.title('Capacity vs. Voltage for cell %s' % cell_name, size=title_s)
    plt.gca().title.set_position([.5, 1.05])
    plt.gca().set_ylim([0.03, 1])
    plt.yticks(np.arange(0, 1.1, 0.1))
    plt.xlabel('Capacity (mAh/g)', size=ti_la_s)
    plt.ylabel('Voltage (V)', size=ti_la_s)
    plt.legend(loc='best', prop={'size': ti_la_s-6})
    plt.savefig(os.path.join(fig_folder, 'cap_volt_%s.pdf' % cell_name),
                dpi=300)


if __name__ == '__main__':
    # ms = markersize
    ms = 30
    tick_and_label_s = 70
    title_s = tick_and_label_s + 30

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
    mass_err_scale = 0.01   # In mg. What is the uncertainty of the scale?

    # mass_frac_err = copp_err + mass_err_scale   # In %. cell_mass=mass_tot-mass_copp
    i_err_accuracy = 0.1   # % in full scale range
    v_err_accuracy = 0.1   # % in full scale range
    v_range = 10   # full scale ==> 0-10 V
    i_range = 20**(-3)   # full scale ==> +/- 10mA
    i_err = i_err_accuracy / 100 * i_range
    mass_frac_err = {}
    for n, m in cell_mass.items():
        mass_frac_err[n] = mass_err_scale/m + copp_err / 100

    v_err = v_err_accuracy / 100 * v_range   # [V]

    figure_folder = r'C:\Users\torkv\OneDrive - Norwegian University of Life '\
                    r'Sciences\Documents\NMBU\master\ife\thesis tor\fig\results'
    ocv_down = r'ocvrlx_down.csv'
    ocv_up = r'ocvrlx_up.csv'
    datafolder = r'..\data_ex'
    datafolder_out = r'..\outdata'
    filenames = [f for f in os.listdir(datafolder)
                 if os.path.isfile(os.path.join(datafolder, f)) and
                 str(f).endswith('.res')]
    filenames.sort()

    names = {}
    counter = 1
    for fil in filenames:
        if 'sic006_74' in fil:
            names[fil] = 'S'
        elif 'bec01_0%i' % counter in fil:
            if 1 <= counter <= 3:
                names[fil] = 'A%i' % counter
                counter += 1
            elif 3 < counter <= 6:
                names[fil] = 'QA%i' % (counter - 3)
                counter += 1
            elif 6 < counter <= 9:
                names[fil] = '%i' % (counter - 6)
                counter += 1
            elif 9 < counter <= 12:
                names['20161101_bec01_%i_cc_01.res'] = 'Q%i' % (counter - 9)
                counter += 1

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

    name = filenames[9]
    up = False
    if up:
        rlx_text = 'after lithiation'
    else:
        rlx_text = 'after delithiation'
    print name

    # plotting_stuff(name, datafolder_out, figure_folder, names[name],
    #                ti_la_s=tick_and_label_s)

    if up:
        time, voltage, fit, rc_para, i_start = \
            fitting_cell(filename=name[:-3]+ocv_up, filefolder=datafolder_out,
                         cell_mass=cell_mass[name], contri=contri,
                         tau_guessed=tau_guessed, v_start=v_start_up,
                         c_rate=c_rate, change_i=change_i,
                         cell_capacity=cell_capacity, conf=conf, v_err=v_err)
    else:
        time, voltage, fit, rc_para, i_start = \
            fitting_cell(filename=name[:-3]+ocv_down, filefolder=datafolder_out,
                         cell_mass=cell_mass[name], contri=contri,
                         tau_guessed=tau_guessed, v_start=v_start_down,
                         c_rate=c_rate, change_i=change_i,
                         cell_capacity=cell_capacity, conf=conf, v_err=v_err)

    cycles_number = (0, 1, 2, 4, 7, 9, 11, len(voltage) - 1)
    leg = []
    plt.figure(figsize=(40, 42))
    for volt_i in cycles_number:
        ocv = voltage[volt_i][::300]
        time_ocv = time[volt_i][::300]
        if volt_i == cycles_number[-1]:
            plt.errorbar(time_ocv, ocv, yerr=v_err, fmt='-^b', ms=ms,
                         elinewidth=3)
        else:
            plt.errorbar(time_ocv, ocv, yerr=v_err, fmt='-o', ms=ms,
                         elinewidth=3)
        leg.append('OCV-relaxation for cycle %s' % (volt_i + 1))
    for tick_volt in plt.gca().xaxis.get_major_ticks():
        tick_volt.label.set_fontsize(tick_and_label_s)
    for tick_volt in plt.gca().yaxis.get_major_ticks():
        tick_volt.label.set_fontsize(tick_and_label_s)

    plt.gca().title.set_position([.5, 1.05])
    plt.title('Open Circuit Voltage Relaxation for Cell %s (%s)'
              % (names[name], rlx_text), size=title_s)
    plt.xlabel('Time (s)', size=tick_and_label_s)
    plt.ylabel('Relaxation voltage (V)', size=tick_and_label_s)
    plt.legend(leg, loc='best', prop={'size': tick_and_label_s - 15})
    if up:
        plt.savefig(os.path.join(figure_folder, 'arbin_relax_%s_%s.pdf'
                                 % (names[name], 'lith')), dpi=200)
    else:
        plt.savefig(os.path.join(figure_folder, 'arbin_relax_%s_%s.pdf'
                                 % (names[name], 'delith')), dpi=200)

    pass

    # fco.user_plot_voltage(time, voltage, fit, conf, ms=ms,
    #                       ti_la_s=tick_and_label_s, tit_s=title_s,
    #                       name=names[name])
    fco.plot_params(voltage, fit, rc_para, i_start, names[name],
                    mass_frac_err[name], figure_folder, i_err=i_err, ms=ms,
                    ti_la_s=tick_and_label_s, tit_s=title_s)
    # fco.print_params(fit, rc_para)


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
    # plt.show()
