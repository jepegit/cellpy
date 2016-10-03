# -*- coding: utf-8 -*-

"""
Fitting ocv parameters with lmfit and plotting.
"""

from lmfit import Minimizer, Parameters
from cell_ocv import ocv_relax_func, guessing_parameters

import matplotlib.pyplot as plt
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


def plotting(t, v, best, sub):

    # Defining legends, but no need
    # def define_legends():
    #     """
    #     creating a list with legends from both up and down ocv_data
    #
    #     :return: list of legends for ocv_data
    #     """
    #     leg_down = []
    #     leg_up = []
    #     count = 0
    #     for lbl_down in data_down:
    #         if count % 2:
    #             leg_down.append(str(lbl_down))
    #         count += 1
    #     count = 0
    #     for lbl_up in data_up:
    #         if count % 2:
    #             leg_up.append((str(lbl_up)))
    #         count += 1
    #     return leg_down, leg_up
    #
    # legend_down, legend_up = define_legends()

    res_dict = best.params.valuesdict()
    print 'Guessed parameters: ', best.init_values
    print 'Best fitted parameters: ', res_dict
    print '\t'
    print '------------------------------------------------------------'
    best_fit = best.residual + v
    ocv = np.array([res_dict['ocv'] for _ in range(len(t))])
    sub.plot(t, v, 'ob', t, best_fit, '-y', t, ocv, '--c')
    sub.set_xlabel('Time (s)')
    sub.set_ylabel('Voltage (V)')
    sub.legend(['Measured', 'Best fit', 'ocv - relaxed'])
    # residuals. Don't know how to yet.. Check out gridspec
    # diff = v_up - best_fit
    # res[cycle_plot_up].plot(t_up, diff, 'or')
    # res[cycle_plot_up].legend(['Residuals'])


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
    para = Parameters()
    para.add('r_ct', value=init_guess[0]['r_rc']['ct'], min=0)
    para.add('r_d', value=init_guess[0]['r_rc']['d'], min=0)
    para.add('c_ct', value=init_guess[0]['c_rc']['ct'], min=0)
    para.add('c_d', value=init_guess[0]['c_rc']['d'], min=0)
    para.add('ocv', value=init_guess[0]['ocv'])
    para.add('v_rlx', value=init_guess[0]['v_rlx'])
    guessed_voltage = ocv_relax_func(time[0], init_guess[0]['ocv'],
                                     init_guess[0]['v_rlx'],
                                     init_guess[0]['r_rc'],
                                     init_guess[0]['c_rc'])



    # Fitting data
    result = [Minimizer(ocv_user_adjust, params=para,
                        fcn_args=(time[0], voltage[0])).minimize()]
    for cycle_i in range(1, len(time)):
        para = result[cycle_i - 1].params
        result.append(Minimizer(ocv_user_adjust, params=para,
                                fcn_args=(time[cycle_i],
                                          voltage[cycle_i])).minimize())

    # Plotting
    fig_up = plt.figure(figsize=(20, 13))
    plt.suptitle('OCV-relaxation data from cell "sic006_cc_45_01" with best '
                 'fitted and guessed parameters',
                 size=20)
    # ####################################################################
    # general for all cycles.
    # subs_up = [fig_up.add_subplot(3, 1, i) for i in range(len(data_up))]
    # ####################################################################
    # for sic006_45 with the 3 first cycles only
    subs_up = [fig_up.add_subplot(3, 1, j+1) for j in range(3)]

    for cycle_nr, sub_up in enumerate(subs_up):
        plotting(time[cycle_nr], voltage[cycle_nr], result[cycle_nr], sub_up)
    fig_up2 = plt.figure(figsize=(20, 13))
    subs_up2 = [fig_up2.add_subplot(3, 1, w+1) for w in range(3)]
    for cycle_nr2, sub_up2 in enumerate(subs_up2):
        plotting(time[cycle_nr + cycle_nr2], voltage[cycle_nr + cycle_nr2],
        result[cycle_nr + cycle_nr2], sub_up2)
    plt.show()
