# -*- coding: utf-8 -*-

"""Using cellpy.

Importing all cell files and functions from perform_fit.py.
This script is an example of how cellpy can be used.

"""

from perform_fit import fitting_cell, save_cap_ocv
from matplotlib.pyplot import MaxNLocator
from textwrap import wrap
from math import pi

import fitting_cell_ocv as fco
import sys, os, csv, itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def plotting_stuff(filename, folder, fig_folder, cell_name, c_rate, mass,
                   i_change, i_err, ideal_cap=3.579, m_s=20, ti_la_s=35,
                   zoom=False):
    """Based on same plot as in perform_fit.save_and_plot_cap().

    Difference is that I can freely change here as run_cellpy is not suppose
    to be a part of cellpy, but instead a user example.

    Make changes in this function to modify plot as you like.

    Args:
        filename (str): Filename of cell.
        folder (str): Folder in which the filename lays.
        fig_folder(str): Which folder to save the figures.
        cell_name (str): Converted cell name to thesis cell name.
        c_rate (list): List of c_rates under cycling.
        mass(float): Mass of the cell
        i_change (list): A list including cycle index for when current change.
        i_err (float): Current error from Arbin in +/- mA.
        ideal_cap (float): Theoretical capacity for LixSi, x = 3.75 in [mAh/mg].
        m_s (int): Markersize for plots.
        ti_la_s (int): Ticks and labels font size.
        zoom (bool): True if want to zoom in on coulombic efficiency.

    Returns:
        plt.figure(): Desired plots and save coulombic differences in xlsx

    Note:
        c-rates in the list c_rate has to be ordered so that the c_rate with
        index 0 is the first c-rate and c_rate[1] is the c-rate after
        cycle = i_change[0].

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

    n_cycles = max(df_normal['Cycle_Index'] - 1)
    frac = []
    step = 0
    for i in range(n_cycles):
        # Checking if cycle number i is in change_i
        if i in i_change:
            step += 1
        i_start = (c_rate[step] * ideal_cap * mass) / 1000
        i_frac = i_err / i_start
        frac.append(i_frac)

    data_steps = os.path.join(folder, steps)
    data_steps = pd.read_csv(data_steps, sep=';')
    df_steps = pd.DataFrame(data_steps)

    data_stats = os.path.join(folder, stats)
    data_stats = pd.read_csv(data_stats, sep=';')
    df_stats = pd.DataFrame(data_stats)

    first_cycle_diff = df_stats['Coulombic_Difference(mAh/g)']
    cumulated_coulombic_diff = df_stats['Cumulated_Coulombic_Difference(mAh/g)']
    C_err_first = []
    C_err_cum = []
    for key_C, C in enumerate(first_cycle_diff):
        C_err_first.append(C * frac[key_C])
        C_err_cum.append(cumulated_coulombic_diff[key_C] * frac[key_C])
    first_cycle_diff = pd.DataFrame(zip(first_cycle_diff, C_err_first),
                                    columns=['Coulombic diff (mAh/g)',
                                             'err'])
    cumulated_coulombic_diff = pd.DataFrame(zip(cumulated_coulombic_diff,
                                                C_err_cum),
                                            columns=['Cum coul diff (mAh/g)',
                                                     'err'])

    cum_coulombic = pd.ExcelWriter('../outdata/coulombic_difference_%s.xlsx'
                                   % cell_name)
    first_cycle_diff.to_excel(cum_coulombic, 'coul_diff_first')
    cumulated_coulombic_diff.to_excel(cum_coulombic, 'cumu_coul_diff')

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

    plt.figure(figsize=(40, 42))
    col_eff_err = [2 * f * col_eff[f_i] for f_i, f in enumerate(frac)]
    plt.errorbar(x_range, col_eff, yerr=col_eff_err, fmt='-ok', ms=m_s,
                 elinewidth=5)
    plt.plot(100*np.ones(len(col_eff)), '-k')
    # plt.gca().invert_yaxis()
    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    # plt.xticks(np.arange(1, len(col_eff) + 1, 8.0))
    plt.gca().yaxis.set_major_locator(MaxNLocator(6))
    plt.gca().xaxis.set_major_locator(MaxNLocator(4))

    plt.gca().title.set_position([.5, 1.05])
    plt.title('Coulombic Efficiency ($\eta$) for cell %s' % cell_name,
              size=title_s)
    plt.legend(['$\eta = Q_{out}/Q_{in}$'], loc='best',
               prop={'size': ti_la_s})
    plt.xlabel('Cycle number', size=ti_la_s)
    plt.ylabel('$\eta$ (%)', size=ti_la_s)
    if zoom:
        plt.gca().set_xlim([-0.1, len(col_eff) + 1])
        plt.gca().set_ylim([col_eff[1]-0.5, 100.5])
        fig = 'coulombic_eff_zoom_%s.pdf' % cell_name
        plt.savefig(os.path.join(fig_folder, fig), dpi=100)
    else:
        fig = 'coulombic_eff_%s.pdf' % cell_name
        plt.savefig(os.path.join(fig_folder, fig), dpi=100)

    # Plotting cycle vs. cap #############################################
    plt.figure(figsize=(40, 42))
    discharge_err = [di_e * cycle_cap_df["Discharge_Capacity(mAh/g)"][di_e_i]
                     for di_e_i, di_e in enumerate(frac)]
    charge_err = [ch_e * cycle_cap_df["Charge_Capacity(mAh/g)"][ch_e_i] for
                  ch_e_i, ch_e in enumerate(frac)]
    plt.errorbar(x_range, cycle_cap_df["Charge_Capacity(mAh/g)"],
                 yerr=charge_err, fmt='^b', ms=m_s, elinewidth=5)
    plt.errorbar(x_range, cycle_cap_df["Discharge_Capacity(mAh/g)"],
                 yerr=discharge_err, fmt='or', ms=m_s, elinewidth=5)

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    plt.gca().title.set_position([.5, 1.05])
    plt.gca().yaxis.set_major_locator(MaxNLocator(6))
    plt.gca().xaxis.set_major_locator(MaxNLocator(4))
    # plt.xticks(np.arange(1, len(col_eff) + 1, 8.0))
    plt.legend(['Charge Capacity (Delithiation)',
                'Discharge capacity (Lithiation)'], loc='best',
               prop={'size': ti_la_s})

    plt.title('Capacity vs. Cycle for cell %s' % cell_name, size=title_s)
    plt.xlabel('Cycle number', size=ti_la_s)
    plt.ylabel('Capacity (mAh/g)', size=ti_la_s)

    plt.savefig(os.path.join(fig_folder, 'cap_cycle_%s.pdf' % cell_name),
                dpi=100)

    # Plotting voltage vs. cap
    capacity_sorting = []
    voltage_sorting = []

    for df_name in df_cap_volt:
        if 'cap' in df_name:
            capacity_sorting.append(df_cap_volt[df_name])
        else:
            voltage_sorting.append(df_cap_volt[df_name])

    plt.figure(figsize=(40, 42))
    number_plots = (0, 1, 2, 4, 9, 24, -2)
    max_cap = max(capacity_sorting[0])
    for cycle in number_plots:
        plt.plot(capacity_sorting[cycle], voltage_sorting[cycle], linewidth=5)
        max_cap_cycle = max(capacity_sorting[cycle])
        if max_cap_cycle > max_cap:
            max_cap = max_cap_cycle

    for tick_rc in plt.gca().xaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    for tick_rc in plt.gca().yaxis.get_major_ticks():
        tick_rc.label.set_fontsize(ti_la_s)
    plt.title('Capacity vs. Voltage for cell %s' % cell_name, size=title_s)
    plt.gca().title.set_position([.5, 1.05])
    plt.gca().set_ylim([0.03, 1])
    plt.gca().set_xlim([0, max_cap + 100])
    # plt.yticks(np.arange(0, 1.1, 0.1))
    plt.gca().yaxis.set_major_locator(MaxNLocator(6))
    plt.gca().xaxis.set_major_locator(MaxNLocator(4))
    plt.xlabel('Capacity (mAh/g)', size=ti_la_s)
    plt.ylabel('Voltage (V)', size=ti_la_s)
    plt.legend(loc='best', prop={'size': ti_la_s-6})
    plt.savefig(os.path.join(fig_folder, 'cap_volt_%s.pdf' % cell_name),
                dpi=100)


if __name__ == '__main__':
    plt.rcParams['xtick.major.pad'] = 8
    plt.rcParams['ytick.major.pad'] = 8

    # ms = markersize
    ms = 40
    tick_and_label_s = 90
    title_s = tick_and_label_s + 40

    contri = {'ct': 0.2, 'd': 0.8}
    tau_guessed = {'ct': 50, 'd': 800}
    cell_mass = {'20160805_test001_45_cc_01.res': 0.85,
                 '20160830_sic006_74_cc_01.res': 0.86,
                 '20161101_bec01_01_cc_01.res': 0.38,
                 '20161101_bec01_02_cc_01.res': 0.36,
                 '20161101_bec01_03_cc_01.res': 0.38,
                 '20161101_bec01_07_cc_01.res': 0.42,
                 '20161101_bec01_08_cc_01.res': 0.36,
                 '20161101_bec01_09_cc_01.res': 0.35}   # [mg]
    c_rate = [0.05, 0.1]   # 1/[h]
    change_i = [3]   # What cycle the current is changed
    cell_capacity = 3.579   # [mAh / mg]
    v_start_up = 0.05
    v_start_down = 1.

    disk_diameter = 5.2   # micron
    disk_dia_frac_err = (0.1) / disk_diameter   # +/- frac error
    disk_area = (disk_diameter / 2) ** 2 * pi   # square micron
    conf = False
    copp_err = 0.2   # in %. std/best_estimate. best_estimate = 28.7, std. = 0.0634
    mass_err_scale = 0.01   # In mg. What is the uncertainty of the scale?
    i_err_accuracy = 0.1   # % of full scale range
    v_err_accuracy = 0.1   # % of full scale range
    v_range = 20   # full scale ==> +/- 10 V
    i_range = 2* 10**(-3)   # full scale ==> +/- 10mA
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
    # save_cap_ocv(datafolder, filenames[0], datafolder_out,
    #                   cell_mass['bec01_01'])
    #
    # save_cap_ocv(datafolder, r'20160830_sic006_74_cc_01.res',
    #                   datafolder_out, cell_mass['sic006_74'])
    #
    # making plots HERE !!!! Change cell mass name

    # for name in cell_mass:
    #     if not 'bec01_02' in name:
    #         save_cap_ocv(datafolder, name, datafolder_out, cell_mass[name])
    #         save_cap_ocv(datafolder, name, datafolder_out, cell_mass[name],
    #                      type_data=ocv_down[:-4])
    plots = (1, 2, 4, 8, 9, 10)
    zoom = False
    name_plots = [filenames[p] for p in plots]
    up = True
    name = filenames[2]
    # plotting_stuff(name, datafolder_out, figure_folder, names[name],
    #                c_rate=c_rate, mass=cell_mass[name], i_change=change_i,
    #                i_err=i_err, ti_la_s=tick_and_label_s, m_s=ms, zoom=zoom)
    # for name in name_plots:
    print name
    # plotting_stuff(name, datafolder_out, figure_folder,
    #                cell_name=names[name], c_rate=c_rate,
    #                mass=cell_mass[name], i_change=change_i,
    #                i_err=i_err, ti_la_s=tick_and_label_s, zoom=zoom, m_s=ms)
    if up:
        rlx_text = 'after lithiation'
        time, voltage, fit, rc_para, i_start = \
            fitting_cell(filename=name[:-3]+ocv_up, filefolder=datafolder_out,
                         cell_mass=cell_mass[name], contri=contri,
                         tau_guessed=tau_guessed, v_start=v_start_up,
                         c_rate=c_rate, change_i=change_i,
                         cell_capacity=cell_capacity, conf=conf, v_err=v_err)
    else:
        rlx_text = 'after delithiation'
        time, voltage, fit, rc_para, i_start = \
            fitting_cell(filename=name[:-3]+ocv_down, filefolder=datafolder_out,
                         cell_mass=cell_mass[name], contri=contri,
                         tau_guessed=tau_guessed, v_start=v_start_down,
                         c_rate=c_rate, change_i=change_i,
                         cell_capacity=cell_capacity, conf=conf, v_err=v_err)

    # cycles_number = (0, 1, 2, 4, 9, 24, len(voltage) - 2)
    # leg = []
    # plt.figure(figsize=(60, 62))
    # for volt_i in cycles_number:
    #     if 'S' in names[name] or 'A3' in names[name]:
    #         ocv = voltage[volt_i][::30]
    #         time_ocv = time[volt_i][::30]
    #     else:
    #         ocv = voltage[volt_i][::10]
    #         time_ocv = time[volt_i][::10]
    #     if volt_i == cycles_number[-1]:
    #         plt.errorbar(time_ocv, ocv, yerr=v_err, fmt='-^b', ms=ms,
    #                      elinewidth=2)
    #     else:
    #         plt.errorbar(time_ocv, ocv, yerr=v_err, fmt='-o', ms=ms,
    #                      elinewidth=2)
    #     leg.append('OCV-relaxation for cycle %s' % (volt_i + 1))
    # for tick_volt in plt.gca().xaxis.get_major_ticks():
    #     tick_volt.label.set_fontsize(tick_and_label_s)
    # for tick_volt in plt.gca().yaxis.get_major_ticks():
    #     tick_volt.label.set_fontsize(tick_and_label_s)
    #
    # plt.gca().title.set_position([.5, 1.05])
    # plt.title(
    #     '\n'.join(wrap('Open Circuit Voltage Relaxation for Cell %s (%s)', 30))
    #     % (names[name], rlx_text), size=title_s)
    # plt.xlabel('Time (s)', size=tick_and_label_s)
    # plt.ylabel('Relaxation voltage (V)', size=tick_and_label_s)
    # plt.gca().yaxis.set_major_locator(MaxNLocator(6))
    # plt.gca().xaxis.set_major_locator(MaxNLocator(6))
    # plt.legend(leg, loc='best', prop={'size': tick_and_label_s})
    # if up:
    #     plt.savefig(os.path.join(figure_folder, 'arbin_relax_%s_%s.pdf'
    #                              % (names[name], 'lith')), dpi=100)
    # else:
    #     plt.savefig(os.path.join(figure_folder, 'arbin_relax_%s_%s.pdf'
    #                              % (names[name], 'delith')), dpi=100)

    fco.user_plot_voltage(time, voltage, fit, conf, name=names[name], ms=ms,
                          ti_la_s=tick_and_label_s, tit_s=title_s,
                          figfolder=figure_folder)
    # fco.plot_params(voltage, fit, rc_para, i_start, names[name],
    #                 mass_frac_err[name], figure_folder, i_err=i_err, ms=ms,
    #                 ti_la_s=tick_and_label_s, tit_s=title_s, single=True,
    #                 outfolder=datafolder_out, sur_area=disk_area,
    #                 sur_area_err=disk_dia_frac_err)
    # fco.plot_params_area(voltage, fit, rc_para, i_start, names[name],
    #                      mass_frac_err[name], figure_folder, i_err=i_err, ms=ms,
    #                      ti_la_s=tick_and_label_s, tit_s=title_s, single=True,
    #                      outfolder=datafolder_out, sur_area=disk_area,
    #                      sur_area_err=disk_dia_frac_err)

        # fco.print_params(fit, rc_para)

    pass


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
