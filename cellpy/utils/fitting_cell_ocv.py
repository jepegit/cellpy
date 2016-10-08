# -*- coding: utf-8 -*-

"""
Fitting ocv parameters with lmfit and plotting.
"""

from lmfit import Minimizer, Parameters, report_fit
from cell_ocv import ocv_relax_func, guessing_parameters

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import os

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def manipulate_data(read_data):

    # need to separate time and voltage so they can be combined as y(x)
    """
    This function will split xy-xy-xy-xy... pandas data pd.read_csv to
    numpy array with only x and one with only y.
    :param read_data: pandas DataFrame that has multi xy data as column info
    :return: a list with number of cycles as length. Each cycle
    has its pandas DataFrame with time-voltage for that cycle.
    """
    # extracting time data
    time_data = [t for t_col in range(len(read_data.iloc[0, :])) for t in
                 read_data.iloc[:, t_col] if not t_col % 2]
    # extracting voltage data. The "if .. and t, v <950 will only
    # extract three first columns. This is temper as the first data only
    # had 3 ok set.
    voltage_data = [v for v_col in range(0, len(read_data.iloc[0, :]))
                    for v in read_data.iloc[:, v_col] if v_col % 2]
    num_cycles = len(time_data)/len(read_data)
    sorted_data = []
    key = 0
    for _ in range(0, num_cycles):
        _time = time_data[key:key + len(read_data)]
        _volt = voltage_data[key:key + len(read_data)]
        key += len(read_data)
        sorted_data.append(pd.DataFrame(zip(_time, _volt), columns=['time',
                                                                    'voltage'
                                                                    ]))
    # setting NaN (very manually) to be the last real number
    # manipulate.loc[:1][0]['time'].iloc[-2] = manipulate.loc[:1][0]['time'].iloc[-3]
    # manipulate.loc[:1][0]['time'].iloc[-1] = manipulate.loc[:1][0]['time'].iloc[-3]
    # manipulate.loc[:1][1]['time'].iloc[-2] = manipulate.loc[:1][1]['time'].iloc[-3]
    # manipulate.loc[:1][1]['time'].iloc[-1] = manipulate.loc[:1][1]['time'].iloc[-3]
    #
    # manipulate.loc[:1][0]['voltage'].iloc[-2] = manipulate.loc[:1][0][
    #     'voltage'].iloc[-3]
    # manipulate.loc[:1][0]['voltage'].iloc[-1] = manipulate.loc[:1][0][
    #     'voltage'].iloc[-3]
    # manipulate.loc[:1][1]['voltage'].iloc[-2] = manipulate.loc[:1][1][
    #     'voltage'].iloc[-3]
    # manipulate.loc[:1][1]['voltage'].iloc[-1] = manipulate.loc[:1][1][
    #     'voltage'].iloc[-3]
    return pd.Series(sorted_data)


def ocv_user_adjust(par, t, meas_volt):

    p_dict = par.valuesdict()
    r_rc = {key[2:]: val for key, val in p_dict.items() if key.startswith('r')}
    c_rc = {key[2:]: val for key, val in p_dict.items() if key.startswith('c')}
    return ocv_relax_func(t, r_rc=r_rc, c_rc=c_rc, ocv=par['ocv'],
                          v_rlx=par['v_rlx']) - meas_volt


def plot_voltage(t, v, best):

    # print 'Guessed parameters: ', best.init_values
    # print 'Best fitted parameters: ', res_dict
    # print '\t'
    # print '------------------------------------------------------------'
    res_dict = best.params.valuesdict()
    best_fit = best.residual + v
    ocv = np.array([res_dict['ocv'] for _ in range(len(t))])
    plt.plot(t, v, 'ob', t, best_fit, '-y', t, ocv, '--c')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend(['Measured', 'Best fit', 'ocv - relaxed'], loc='center left',
               bbox_to_anchor=(1, 0.5), prop={'size': 10})


# def print_params(ini, fit):
#
#     for key, value in fit.items():
#         print 'Guessed: %-9 Fitted Parameters:'
#         print '\t'
#         print '%s: %-9f %f' % (key, ini[key], value)


if __name__ == '__main__':
    # importing data
    ############################################################################
    datafolder = r'..\testdata'   # make sure you're in folder \utils. If not,
    # activate "print os.getcwd()" to find current folder and extend datafolder
    # with [.]\utils\data
    # print os.getcwd()
    filename_down = r'20160805_sic006_45_cc_01_ocvrlx_down.csv'
    filename_up = r'20160805_sic006_45_cc_01_ocvrlx_up.csv'
    down = os.path.join(datafolder, filename_down)
    up = os.path.join(datafolder, filename_up)
    data_down = pd.read_csv(down, sep=';')
    data_up = pd.read_csv(up, sep=';')
    data_up = manipulate_data(data_up)

    # preparations for fitting
    ############################################################################
    v_start_down = 1.   # all start variables are taken from fitting_ocv_003.py
    v_start_up = 0.01
    i_cut_off = 0.000751
    # taken from "x" in fitting_ocv_003.py, function "GuessRC2"
    contri = {'ct': 0.2, 'd': 0.8}
    tau_guessed = {'ct': 50, 'd': 400}

    time_up = []
    voltage_up = []
    for i, sort_up in data_up.iteritems():
        time_up.append(np.array(sort_up[:]['time']))
        voltage_up.append(np.array(sort_up[:]['voltage']))
        # removing nan is inspired by:
# http://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array
        time_up[i] = time_up[i][~np.isnan(time_up[i])]
        voltage_up[i] = voltage_up[i][~np.isnan(voltage_up[i])]
    init_guess_up = guessing_parameters(v_start_up, i_cut_off,
                                        voltage_up[0], contri, tau_guessed)
    initial_param_up = Parameters()
    # r_ct and r_d are actually tau_ct and tau_d when fitted because c = 1 (fix)
    initial_param_up.add('r_ct', value=tau_guessed['ct'], min=0)
    initial_param_up.add('r_d', value=tau_guessed['d'], min=0)
    initial_param_up.add('c_ct', value=1., vary=False)
    initial_param_up.add('c_d', value=1., vary=False)
    initial_param_up.add('ocv', value=init_guess_up['ocv'],
                         min=voltage_up[0][-1])
    initial_param_up.add('v_rlx', value=init_guess_up['v_rlx'],
                         max=init_guess_up['ocv'])

    #  fitting data
    ############################################################################
    # making a class Minimizer that contain fitting methods and attributes
    Mini_initial_up = Minimizer(ocv_user_adjust, params=initial_param_up,
                                fcn_args=(time_up[0], voltage_up[0]))
    # minimize() perform the minimization on Minimizer's attributes
    result_up = [Mini_initial_up.minimize()]
    best_para_up = [result_up[0].params]
    best_fit_voltage_up = [result_up[0].residual + voltage_up[0]]
    report_fit(result_up[0])

    for cycle_up_i in range(1, len(time_up)):
        start_voltage_up = voltage_up[cycle_up_i][0]
        end_voltage_up = voltage_up[cycle_up_i][-1]
        best_para_up[cycle_up_i - 1]['ocv'].set(min=end_voltage_up)
        # best_para_up[cycle_up_i - 1]['v_rlx'].set(
        #     min=start_voltage_up-end_voltage_up)
        Temp_mini = Minimizer(ocv_user_adjust,
                              params=best_para_up[cycle_up_i - 1],
                              fcn_args=(time_up[cycle_up_i],
                                        voltage_up[cycle_up_i]))
        result_up.append(Temp_mini.minimize())
        best_para_up.append(result_up[cycle_up_i].params)
        best_fit_voltage_up.append(result_up[cycle_up_i].residual
                                   + voltage_up[cycle_up_i])

    # plotting cycle's voltage at user's wish
    ############################################################################
    # making odd or even amount of figures
    question = 'Cycles after discharge you want to plot, separated with ' \
               'space. If you don'"'"'t want to plot any press ' \
               'enter. Write "a" for all plots: -->'
    user_cycles_up = raw_input(question)
    if not user_cycles_up:
        # no cycles
        user_cycles_up_list = []

    elif user_cycles_up == 'a':
        # all cycles
        user_cycles_up_list = range(len(result_up))
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
                     result_up[cycle_nr])
        report_fit(result_up[cycle_nr])


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

    # plot parameters
    ############################################################################
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
        if 'r' == name[0]:
            subs_params[_].set_ylabel('Resistance [ohm]')
        elif 'c' == name[0]:
            subs_params[_].set_ylabel('Capacitance [F]')
        else:
            subs_params[_].set_ylabel('Voltage [V]')

    plt.show()
