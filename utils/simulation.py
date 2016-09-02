# -*- coding: utf-8 -*-

"""
Simulation of utils
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from cell_ocv import Cell

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def fitting(time, voltage, vstart, istart, contribute, err=None, slope=None):
    """
    Using measured data and scipy's "curve_fit" (non-linear least square,
    check it up with "curve_fit?" in console) to find the best fitted ocv
    relaxation curve.
    :return: dictionary of best fitted parameters and error between
    measured data and the fitting.
    """
    # popt are the "parameters, optimal" based on initial guess and
    # theoretical
    #  function. pcov is "parameters, covariance", which is a matrix with
    #  the variance of popt on the diagonal. To get the standard
    # derivation errors, compute: perr = np.sqrt(diag(pcov)),
    # where perr is of course "parameters error"
    cell = Cell(time, voltage, vstart, istart, contribute, slope)
    cell.guessing_parameters()
    params = [cell.v_0, cell.ocv, cell.r_ct, cell.r_d, cell.r_ir, cell.c_ct,
              cell.c_d]
    return curve_fit(cell.ocv_relax_func(), time, voltage, p0=params,
                     sigma=err)


if __name__ == '__main__':
    datafolder = r'.\data'   # make sure you're in folder \utils. If not,
    # activate os.getcwd() to find current folder and extend datafolder
    # with [.]\utils\data
    # print os.getcwd()
    filename_down = r'20160805_sic006_45_cc_01_ocvrlx_down.csv'
    filename_up = r'20160805_sic006_45_cc_01_ocvrlx_up.csv'
    down = os.path.join(datafolder, filename_down)
    up = os.path.join(datafolder, filename_up)
    data_down = pd.read_csv(down, sep=';')
    data_up = pd.read_csv(up, sep=';')

    # need to separate time and voltage so
    # they can be plotted together as y(x)
    def make_data(data):
        """
        This function will split xy-xy-xy-xy... pandas data pd.read_csv to
        numpy array with only x and one with only y.
        :param data: pandas DataFrame that has multi xy data as column info
        :return: a list with number of cycles as length. Each cycle
        has its pandas DataFrame with time-voltage for that cycle.
        """
        # extracting time data
        time_data = [t for i in range(len(data.iloc[0, :])) for t in
                     data.iloc[:, i] if not i % 2]
        # extracting voltage data. The "if .. and t, v <950 will only
        # extract three first columns. This is temper as the first data only
        # had 3 ok set.
        voltage_data = [v for k in range(0, len(data.iloc[0, :]))
                        for v in data.iloc[:, k] if k % 2]
        num_cycles = len(time_data)/len(data)
        sorted_data = []
        key = 0
        for _ in range(0, num_cycles):
            time = time_data[key:key + len(data)]
            volt = voltage_data[key:key + len(data)]
            key += len(data)
            sorted_data.append(pd.DataFrame(zip(time, volt), columns=['time',
                                                                      'voltage'
                                                                      ]))
        return sorted_data
    sort_down = make_data(data_down)
    sort_up = make_data(data_up)
    sort_up_df = pd.Series(sort_up)

    sort_up_df.iloc[0]['time'].iloc[-1] = sort_up_df.iloc[:2]['time'].iloc[-3]
    sort_up_df.iloc[1]['time'].iloc[-1] = sort_up_df.iloc[:2]['time'].iloc[-3]
    sort_up_df.iloc[0]['time'].iloc[-2] = sort_up_df.iloc[:2]['time'].iloc[-3]
    sort_up_df.iloc[1]['time'].iloc[-2] = sort_up_df.iloc[:2]['time'].iloc[-3]

    sort_up_df.iloc[0]['voltage'].iloc[-1] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]
    sort_up_df.iloc[1]['voltage'].iloc[-1] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]
    sort_up_df.iloc[0]['voltage'].iloc[-2] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]
    sort_up_df.iloc[1]['voltage'].iloc[-2] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]


    sort_up_df.iloc[:2]['time'].iloc[-2] = sort_up_df.iloc[:2]['time'].iloc[-3]
    sort_up_df.iloc[:2]['voltage'].iloc[-1] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]
    sort_up_df.iloc[:2]['voltage'].iloc[-2] = sort_up_df.iloc[:2][
        'voltage'].iloc[-3]
    print sort_up_df.iloc[0]
    v_start_down = 1   # all start are taken from fitting_ocv_003.py
    v_start_up = 0.05
    i_start = 0.000751
    contri = 0.2   # taken from "x" in fitting_ocv_003.py, func. GuessRC2

    popt_down = np.zeros(len(sort_down))
    pcov_down = np.zeros(len(sort_down))
    popt_up = np.zeros(len(sort_up))
    pcov_up = np.zeros(len(sort_up))
    # print sort_up[0]['voltage']

    # down does not have good enough values yet... When own measurements are
    # done, activate this again.
    # for cycle_down in range(0, len(sort_down)):
    #     popt_down[cycle_down], pcov_down[cycle_down] = fitting(sort_down[
    #                                                                cycle_down]
    #                                                            ['time'],
    #                                                            sort_down[
    #                                                                cycle_down]
    #                                                            ['voltage'],
    #                                                            v_start_down,
    #                                                            i_start, contri)
    for cycle_up in range(0, len(sort_up)):
        popt_down[cycle_up], pcov_down[cycle_up] = fitting(sort_up[cycle_up]
                                                           ['time'],
                                                           sort_up[cycle_up]
                                                           ['voltage'],
                                                           v_start_up,
                                                           i_start, contri)
    # print popt_up[0]



    def define_legends():
        """
        creating a list with legends from both up and down ocv_data
        :return: list of legends for ocv_data
        """
        leg_down = []
        leg_up = []
        count = 0
        for lbl_down in data_down:
            if count % 2:
                leg_down.append(str(lbl_down))
            count += 1
        count = 0
        for lbl_up in data_up:
            if count % 2:
                leg_up.append((str(lbl_up)))
            count += 1
        return leg_down, leg_up

    legend_down, legend_up = define_legends()
    ocv_down = make_data(data_down)
    ocv_up = make_data(data_up)

    plt.figure(figsize=(15, 13))
    for row_up in ocv_up:
        if max(row_up['time']) > 950:
            plt.plot(row_up['time'], row_up['voltage'], '-o')
    plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=4)
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')

    # plotting all curves in same plot. Inspiration from matplotlib,
    # section "legend guide"
    # plt.figure(figsize=(15, 13))
    # plt.subplot(221)
    # plt.xlabel('Time (s)')
    # plt.ylabel('Voltage (V)')
    # for row_down in ocv_down:
    #     plt.plot(row_down['time'], row_down['voltage'], '-o')
    # plt.legend(legend_down, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})
    #
    # plt.subplot(223)
    # plt.xlabel('Time (s)')
    # plt.ylabel('Voltage (V)')
    # for row_up in ocv_up:
    #     plt.plot(row_up['time'], row_up['voltage'], '-o')
    # plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})
    # plt.show()
