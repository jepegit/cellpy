# -*- coding: utf-8 -*-

"""
Reading raw data and reporting and analysing fitted data from fitting_cell_ocv.
"""
from lmfit import Minimizer, Parameters, report_fit
from cell_ocv import *
from fitting_cell_ocv import *

import Tkinter as tk
import ttk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import os

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

class
    """Reading data.

    Reading the .csv file with all the cycling data.

    Make sure you're in folder \utils. If not::
        >>>print os.getcwd()

    to find current folder and extend datafolder with [.]\utils\data
    ----------------------------------------------------------------------------
    """
    datafolder = r'..\testdata'

    filename_down = r'20160805_test001_45_cc_01_ocvrlx_down.csv'
    filename_up = r'20160805_test001_45_cc_01_ocvrlx_up.csv'
    down = os.path.join(datafolder, filename_down)
    up = os.path.join(datafolder, filename_up)
    data_down = pd.read_csv(down, sep=';')
    data_up = pd.read_csv(up, sep=';')
    data_up = manipulate_data(data_up)

    """Preparations for fitting parameters.

        Write boundary conditions and initial guesses.
        Removing "nan" is inspired by 'stackoverflow'_

        .._stackoverflow:
            http://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array
    ----------------------------------------------------------------------------

    """
    v_start_down = 1.
    v_start_up = 0.01
    cell_mass = 0.8   # [g]
    c_rate = 0.1   # [1 / h]
    cell_capacity = 3.579   # [mAh / g]
    i_start = (cell_mass * c_rate * cell_capacity) / 1000   # [A]
    # i_start = 0.000751
    contri = {'ct': 0.2, 'd': 0.8}
    tau_guessed = {'ct': 50, 'd': 400}

    time_up = []
    voltage_up = []
    for i, sort_up in data_up.iteritems():
        time_up.append(np.array(sort_up[:]['time']))
        voltage_up.append(np.array(sort_up[:]['voltage']))
        time_up[i] = time_up[i][~np.isnan(time_up[i])]
        voltage_up[i] = voltage_up[i][~np.isnan(voltage_up[i])]
    v_ocv_up = voltage_up[0][-1]
    v_0_up = voltage_up[0][0]

    init_guess_up = guessing_parameters(v_start_up, i_start, v_0_up,
                                        v_ocv_up, contri, tau_guessed)
    initial_param_up = Parameters()
    # r_ct and r_d are actually tau_ct and tau_d when fitted because c = 1 (fix)
    initial_param_up.add('r_ct', value=tau_guessed['ct'], min=0)
    initial_param_up.add('r_d', value=tau_guessed['d'], min=0)
    initial_param_up.add('c_ct', value=1., vary=False)
    initial_param_up.add('c_d', value=1., vary=False)
    initial_param_up.add('ocv', value=v_ocv_up, min=v_ocv_up)
    initial_param_up.add('v0_ct', value=init_guess_up['v0_rc']['ct'],
                         min=0, max=v_0_up - v_ocv_up)
    initial_param_up.add('v0_d', value=init_guess_up['v0_rc']['d'],
                         min=0, max=v_0_up - v_ocv_up)

    """Fitting parameters.
    ----------------------------------------------------------------------------

    """
    # making a class Minimizer that contain fitting methods and attributes
    Mini_initial_up = Minimizer(ocv_user_adjust, params=initial_param_up,
                                fcn_args=(time_up[0], voltage_up[0]))
    # minimize() perform the minimization on Minimizer's attributes
    result_up = [Mini_initial_up.minimize()]
    best_para_up = [result_up[0].params]
    best_fit_voltage_up = [result_up[0].residual + voltage_up[0]]

    best_rc = {'r_%s' % key[3:]: abs(v0_rc / i_start)
               for key, v0_rc in best_para_up[0].valuesdict().items()
               if key.startswith('v0')}

    best_c = {'c_%s' % key[2:]: tau_rc / best_rc['r_%s' % key[2:]]
              for key, tau_rc in best_para_up[0].valuesdict().items()
              if key.startswith('r')}
    best_rc.update(best_c)
    best_rc_para_up = [best_rc]
    report_fit(result_up[0])

    for cycle_up_i in range(1, len(time_up)):
        # best_para_up[cycle_up_i - 1]['v_rlx'].set(
        #     min=start_voltage_up-end_voltage_up)
        # start_voltage_up = voltage_up[cycle_up_i][0]
        end_voltage_up = voltage_up[cycle_up_i][-1]
        temp_para_up = best_para_up[cycle_up_i - 1].copy()
        temp_para_up['ocv'].set(value=end_voltage_up, min=end_voltage_up)
        Temp_mini = Minimizer(ocv_user_adjust,
                              params=temp_para_up,
                              fcn_args=(time_up[cycle_up_i],
                                        voltage_up[cycle_up_i]))
        result_up.append(Temp_mini.minimize())
        best_para_up.append(result_up[cycle_up_i].params)
        best_fit_voltage_up.append(result_up[cycle_up_i].residual
                                   + voltage_up[cycle_up_i])
        best_rc_cycle = {'r_%s' % key[3:]: abs(v_rc / i_start)
                         for key, v_rc in
                         best_para_up[cycle_up_i].valuesdict().items()
                         if key.startswith('v0')}
        best_c_cycle = {'c_%s' % key[2:]:
                            tau_rc / best_rc_cycle['r_%s' % key[2:]]
                        for key, tau_rc in
                        best_para_up[cycle_up_i].valuesdict().items()
                        if key.startswith('r')}
        best_rc_cycle.update(best_c_cycle)
        best_rc_para_up.append(best_rc_cycle)

    """User decides which cycles to plot.
    ----------------------------------------------------------------------------
    """
    question = 'Cycles after discharge you want to plot, separated with ' \
               'space. If you don'"'"'t want to plot any press ' \
               'enter. Write "a" for all plots: -->'
    user_cycles_up = raw_input(question)
    if not user_cycles_up:
        # no cycles
        user_cycles_up_list = []

    elif user_cycles_up == 'a':
        # all cycles
        user_cycles_up_list = range(0, len(result_up))
    else:
        # specified cycles
        user_cycles_up_list = [int(usr) - 1 for usr in user_cycles_up.split()]
        # if any(user_cycles_up_list) not in range(len(result_up)) or len(
        #         user_cycles_up_list) > len(result_up):
        #     raise AttributeError(
        #         'You have asked for more plots than number of cycles or for a '
        #         'cycle that does not exist. Specify less than %i plots'
        #         % len(result_up))

    for cycle_nr in user_cycles_up_list:
        plt.figure(figsize=(20, 13))
        plt.suptitle('Measured and fitted voltage of cycle %i' % (cycle_nr + 1))
        plot_voltage(time_up[cycle_nr], voltage_up[cycle_nr],
                     result_up[cycle_nr], best_rc_para_up[cycle_nr])
        print 'Report for cycle %i' % (cycle_nr + 1)
        report_fit(result_up[cycle_nr])
        print '----------------------------------------------------------------'


    # sub plotting voltage
    ############################################################################
    # fig_up = plt.figure(figsize=(20, 13))
    # plt.suptitle('OCV-relaxation data from cell "sic006_cc_45_01" with best '
    #              'fitted and guessed parameters',
    #              size=20)
    #
    # # making odd or even amount of subfigures inside fig_up
    # if len(result) % 2 == 0:   # Even number of cycles
    #     gs = gridspec.GridSpec(len(result) / 2, 3)
    #     gs.update(left=0.1, right=0.6, wspace=0.1)
    #     subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]
    # else:
    #     gs = gridspec.GridSpec((len(result) + 1) / 2, 3)
    #     gs.update(left=0.05, right=0.8, wspace=0.8)
    #     subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]
    #
    # for cycle_nr, sub_up in enumerate(subs_up):
    #     plot_voltage(time[cycle_nr], voltage[cycle_nr], result[cycle_nr],
    #                  sub_up)
    """Plotting parameters
    ----------------------------------------------------------------------------
    """
    # printing parameters
    # for cyc in range(1, len(result)):
    #     print 'cycle number %i' % cyc
    #     print_params(ini=best_para[cyc - 1], fit=best_para[cyc])
    #     print '--------------------------------------------------------'
    fig_params = plt.figure(figsize=(20, 13))
    plt.suptitle('Initial and fitted parameters in every cycle', size=20)
    cycle_array = np.arange(1, len(result_up) + 1, 1)

    if len(best_para_up[0]) % 2 == 0:   # Even number of cycles
        gs = gridspec.GridSpec(len(best_para_up[0]) / 2, 3)
        gs.update(left=0.05, right=0.9, wspace=1)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para_up[0]))]
    else:
        gs = gridspec.GridSpec((len(best_para_up[0]) + 1) / 2, 3)
        gs.update(left=0.05, right=0.9, wspace=1)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para_up[0]))]

    plt.setp(subs_params, xlabel='Cycle number', xticks=cycle_array)
    for _, name in enumerate(result_up[0].var_names):
        para_array = np.array([best_para_up[step][name]
                               for step in range(len(result_up))])
        subs_params[_].plot(cycle_array, para_array, 'or')
        subs_params[_].legend([name], loc='center left',
                              bbox_to_anchor=(1, 0.5))
        subs_params[_].set_xlabel('Cycles')
        if 'r' == name[0]:
            subs_params[_].set_ylabel('Resistance [Ohm]')
        elif 'c' == name[0]:
            subs_params[_].set_ylabel('Capacitance [F]')
        else:
            subs_params[_].set_ylabel('Voltage [V]')

    fig_rc = plt.figure(figsize=(20, 13))
    fig_rc.suptitle('R and C for each rc-circuit in all cycles')
    gs_rc = gridspec.GridSpec(2, 2)
    gs_rc.update(left=0.05, right=0.9, wspace=1)
    subs_rc = [fig_rc.add_subplot(gs_rc[pr])
               for pr in range(len(best_rc_para_up[0].keys()))]
    for idx, key_value in enumerate(best_rc_para_up[0].keys()):
        temp_array = np.array([best_rc_para_up[cyc][key_value]
                               for cyc in range(len(best_rc_para_up))])
        subs_rc[idx].plot(cycle_array, temp_array, 'og')
        subs_rc[idx].legend([key_value], loc='center left',
                            bbox_to_anchor=(1, 0.5))
        subs_rc[idx].set_xlabel('Cycles')
        if key_value.startswith('r'):
            subs_rc[idx].set_ylabel('Resistance [Ohm]')
        else:
            subs_rc[idx].set_ylabel('Capacitance [F]')

    plt.show()

