# -*- coding: utf-8 -*-

"""
Simulation of utils
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cell_ocv import Cell

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


if __name__ == '__main__':
    # had to use r'system path to file' to read the csv. Don't know why,
    # but that's how it is right now...
    data_down = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University '
                            r'of Life '
                            r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils\data\20160805_sic006_45_cc_01_ocvrlx_down.csv',
                            sep=';', index_col=0)
    data_up = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University '
                          r'of Life Sciences\Documents\NMBU\master\ife\python\cellpy\utils\data\20160805_sic006_45_cc_01_ocvrlx_up.csv',
                          sep=';', index_col=0)

    # need to separate time and voltage so
    # they can be plotted together as y(x)
    def make_data(data):
        time_data = [t for i in range(len(data.iloc[0, :])) for t in
                     data.iloc[:, i] if i == 0 or i % 2]

        voltage_data = [v for k in range(0, len(data.iloc[0, :]))
                        for v in data.iloc[:, k] if not k % 2]
        print len(time_data), len(voltage_data)
        print zip(time_data, voltage_data)

        data_df = pd.DataFrame(zip(time_data, voltage_data),
                               columns=['time', 'voltage'])
        data_df.set_index('time', inplace=True)
        return data_df

    print make_data(data_down).head()

    # Splitting the data so that they are in intervals of amount of cycles and
    # putting them into a dictionary for easier tracking. First cycle is the
    # first list. To call: ocv_dic['time/voltage'][0] etc.

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
    # ocv_down = Cell(data_down).ocv_dic
    # ocv_up = Cell(data_up).ocv_dic
    #
    # # plotting all curves in same plot. Inspiration from matplotlib,
    # # section "legend guide"
    # plt.figure(figsize=(15, 13))
    # plt.subplot(221)
    # for _ in range(len(ocv_down['time'])):
    #     plt.plot(ocv_down['time'][_], ocv_down['voltage'][_])
    # plt.legend(legend_down, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})
    # plt.subplot(223)
    # for _ in range(len(ocv_down['time'])):
    #     plt.plot(ocv_up['time'][_], ocv_up['voltage'][_])
    # plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=2,
    #            borderaxespad=0, prop={'size': 13})
    # plt.show()

