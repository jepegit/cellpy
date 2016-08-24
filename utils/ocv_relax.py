# -*- coding: utf-8 -*-

"""
Adaption of OCV-relaxation data.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


class Ocv(object):
    """
    This class will read observed data and plot fitted observed data.
    It will also calculate theoretical ocv relaxation behavior based on given
    information about the cell.
    """

    def ex():
        # had to use r'system path to file' to read the csv. Don't know why,
        # but that's how it is right now...
        data = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
                           r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
                           r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv',
                           sep=';', index_col=0)
        # need to separate time and voltage so that they can be plotted together as x-y
        time_data = [t for i in range(len(data.iloc[0, :])) for t in data.iloc[:, i]
                     if i == 0 or i % 2]
        voltage_data = [v for k in range(0, len(data.iloc[0, :]))
                        for v in data.iloc[:, k] if not k % 2]

        # Splitting the data so that they are in intervals of amount of cycles and
        # putting them into a dictionary for easier tracking. First cycle is the
        # first list. To call: ocv_dic['time/voltage'][0] etc.
        ocv_dic = {'time': [time_data[w: w + len(data)] for w in
                            xrange(0, len(time_data), len(data))],
                   'voltage': [voltage_data[j: j + len(data)] for j in
                               xrange(0, len(voltage_data), len(data))]}
        return ocv_dic


if __name__ == '__main__':
    ocv_rlx = ex()
    # plotting all curves in same plot
    for _ in range(len(ocv_rlx['time'])):
        plt.plot(ocv_rlx['time'][_], ocv_rlx['voltage'][_])
    plt.show()
