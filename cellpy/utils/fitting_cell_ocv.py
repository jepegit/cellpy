# -*- coding: utf-8 -*-

"""
Fitting ocv parameters with lmfit and plotting.
"""

from lmfit import Minimizer, Parameters
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
    def make_data(data):
        """
        This function will split xy-xy-xy-xy... pandas data pd.read_csv to
        numpy array with only x and one with only y.
        :param data: pandas DataFrame that has multi xy data as column info
        :return: a list with number of cycles as length. Each cycle
        has its pandas DataFrame with time-voltage for that cycle.
        """
        # extracting time data
        time_data = [t for t_col in range(len(data.iloc[0, :])) for t in
                     data.iloc[:, t_col] if not t_col % 2]
        # extracting voltage data. The "if .. and t, v <950 will only
        # extract three first columns. This is temper as the first data only
        # had 3 ok set.
        voltage_data = [v for v_col in range(0, len(data.iloc[0, :]))
                        for v in data.iloc[:, v_col] if v_col % 2]
        num_cycles = len(time_data)/len(data)
        sorted_data = []
        key = 0
        for _ in range(0, num_cycles):
            _time = time_data[key:key + len(data)]
            _volt = voltage_data[key:key + len(data)]
            key += len(data)
            sorted_data.append(pd.DataFrame(zip(_time, _volt), columns=['time',
                                                                        'voltage'
                                                                        ]))
        return pd.Series(sorted_data)

    manipulate = make_data(read_data)

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
    return manipulate


def ocv_user_adjust(par, t, meas_volt):

    p = par.valuesdict()
    r_rc = {key[2:]: val for key, val in p.items() if key.startswith('r')}
    c_rc = {key[2:]: val for key, val in p.items() if key.startswith('c')}
    return ocv_relax_func(t, r_rc=r_rc, c_rc=c_rc, ocv=p['ocv'],
                          v_rlx=p['v_rlx']) - meas_volt


def plot_voltage(t, v, best, sub_fig):

    res_dict = best.params.valuesdict()
    # print 'Guessed parameters: ', best.init_values
    # print 'Best fitted parameters: ', res_dict
    # print '\t'
    # print '------------------------------------------------------------'
    best_fit = best.residual + v
    ocv = np.array([res_dict['ocv'] for _ in range(len(t))])
    sub_fig.plot(t, v, 'ob', t, best_fit, '-y', t, ocv, '--c')
    sub_fig.set_xlabel('Time (s)')
    sub_fig.set_ylabel('Voltage (V)')
    sub_fig.legend(['Measured', 'Best fit', 'ocv - relaxed'], loc='center left',
                   bbox_to_anchor=(1, 0.5), prop={'size': 10})
    # sub.set_yticks(np.arange(v[0] - v[0] * 0.05, ocv[0] + ocv[0] * 0.05,
    #                          ocv[0] * 0.2))


def print_params(ini, fit):

    for key, value in fit.items():
        print 'Guessed: %-9 Fitted Parameters:'
        print '\t'
        print '%s: %-9f %f' % (key, ini[key], value)


if __name__ == '__main__':
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

    v_start_down = 1.   # all start variables are taken from fitting_ocv_003.py
    v_start_up = 0.01
    i_cut_off = 0.000751
    contri = {'ct': 0.2, 'd': 0.8}   # taken from "x" in fitting_ocv_003.py,
    # function "GuessRC2"
    tau_guessed = {'ct': 50, 'd': 400}

    # Preparations for fitting
    time = []
    voltage = []
    for i, sort_up in data_up.iteritems():
        time.append(np.array(sort_up[:]['time']))
        voltage.append(np.array(sort_up[:]['voltage']))
        # removing nan is inspired by:
# http://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array
        time[i] = time[i][~np.isnan(time[i])]
        voltage[i] = voltage[i][~np.isnan(voltage[i])]
    init_guess = [guessing_parameters(v_start_up, i_cut_off,
                                      voltage[0], contri, tau_guessed)]
    initial_param = Parameters()
    initial_param.add('r_ct', value=init_guess[0]['r_rc']['ct'], min=0)
    initial_param.add('r_d', value=init_guess[0]['r_rc']['d'], min=0)
    initial_param.add('c_ct', value=init_guess[0]['c_rc']['ct'], min=0)
    initial_param.add('c_d', value=init_guess[0]['c_rc']['d'], min=0)
    initial_param.add('ocv', value=init_guess[0]['ocv'])
    initial_param.add('v_rlx', value=init_guess[0]['v_rlx'])
    guessed_voltage = ocv_relax_func(time[0], init_guess[0]['ocv'],
                                     init_guess[0]['v_rlx'],
                                     init_guess[0]['r_rc'],
                                     init_guess[0]['c_rc'])
    # Fitting data
    result = [Minimizer(ocv_user_adjust, params=initial_param,
                        fcn_args=(time[0], voltage[0])).minimize()]
    best_para = [result[0].params]
    fitted_voltage = [result[0].residual + voltage[0]]

    for cycle_i in range(1, len(time)):
        result.append(Minimizer(ocv_user_adjust, params=best_para[cycle_i - 1],
                                fcn_args=(time[cycle_i],
                                          voltage[cycle_i])).minimize())
        best_para.append(result[cycle_i].params)
        fitted_voltage.append(result[cycle_i].residual + voltage[cycle_i])


    # Printing parameters
    for cyc in range(1, len(result)):
        print 'cycle number %i' % cyc
        print_params(ini=best_para[cyc - 1], fit=best_para[cyc])
        print '--------------------------------------------------------'

    # Plotting voltage
    fig_up = plt.figure(figsize=(20, 13))
    plt.suptitle('OCV-relaxation data from cell "sic006_cc_45_01" with best '
                 'fitted and guessed parameters',
                 size=20)
    if len(result) % 2 == 0:   # Even number of cycles
        gs = gridspec.GridSpec(len(result) / 2, 3)
        gs.update(left=0.1, right=0.6, wspace=0.1)
        subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]
    else:
        gs = gridspec.GridSpec((len(result) + 1) / 2, 3)
        gs.update(left=0.05, right=0.8, wspace=0.8)
        subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]

    lines = []
    for cycle_nr, sub_up in enumerate(subs_up):
        if not lines:
            lines = [voltage[cycle_nr], fitted_voltage[cycle_nr],
                     np.array([best_para[cycle_nr]['ocv']
                              for _ in range(len(time[cycle_nr]))])]

        plot_voltage(time[cycle_nr], voltage[cycle_nr], result[cycle_nr],
                     sub_up)

    # Plot parameters
    fig_params = plt.figure(figsize=(20, 13))
    plt.suptitle('Initial and fitted parameters in every cycle', size=20)
    if len(best_para[0]) % 2 == 0:   # Even number of cycles
        gs = gridspec.GridSpec(len(best_para[0]) / 2, 3)
        gs.update(left=0.05, right=0.9, wspace=1)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para[0]))]
    else:
        gs = gridspec.GridSpec((len(best_para[0]) + 1) / 2, 3)
        gs.update(left=0.05, right=0.9, wspace=1)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para[0]))]

    cycle_array = np.array([c for c in range(len(result))])

    for _, name in enumerate(result[0].var_names):
        para_array = np.array([best_para[step][name]
                               for step in range(len(result))])
        subs_params[_].plot(cycle_array, para_array, 'or')
        subs_params[_].legend([name], loc='center left',
                              bbox_to_anchor=(1, 0.5))

    # fig_up.legend(lines, ['Measured', 'Best fit', 'ocv - relaxed'],
                  # loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show()
