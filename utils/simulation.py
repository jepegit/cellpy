# -*- coding: utf-8 -*-

"""
Simulation of utils
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cell_ocv import Cell

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


if __name__ == '__main__':
    datafolder = r'.\data'   # make sure you're in folder \utils. If not,
    # activate os.getcwd() to find current folder and extend datafolder until
    #  [.]\utils\data
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
        # extracting voltage data
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

    # ocv_dic = {'time': [time_data[w: w + len(data)] for w in
    #                          xrange(0, len(time_data), len(data))],
    #                 'voltage': [voltage_data[j: j + len(data)] for j in
    #                             xrange(0, len(voltage_data),
    #                                    len(data))]}

    def define_legends():
        """
        creating a list with legends from both up and down ocv_data
        :return: list of legends for ocv_data
        """
        leg_down = []
        leg_up = []
        count = 0
        for lbl_down in data_down:
            if not count % 2:
                leg_down.append(str(lbl_down))
            count += 1
        count = 0
        for lbl_up in data_up:
            if not count % 2:
                leg_up.append((str(lbl_up)))
            count += 1
        return leg_down, leg_up

    legend_down, legend_up = define_legends()
    ocv_down = make_data(data_down)
    ocv_up = make_data(data_up)

    # plotting all curves in same plot. Inspiration from matplotlib,
    # section "legend guide"
    # plt.figure(figsize=(15, 13))
    # plt.subplot(221)
    # for row_down in ocv_down:
    #     plt.plot(row_down['time'], row_down['voltage'], '-o')
    # plt.legend(legend_down, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})
    # plt.subplot(223)
    # for row_up in ocv_up:
    #     if max(row_up['time']) > 950:
    #         plt.plot(row_up['time'], row_up['voltage'], '-o')
    # plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})

    plt.figure(figsize=(15, 13))
    for row_up in ocv_up:
        if max(row_up['time']) > 950:
            plt.plot(row_up['time'], row_up['voltage'], '-o')
    plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=4)
    plt.show()
