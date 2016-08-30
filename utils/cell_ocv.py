# -*- coding: utf-8 -*-

"""
Adaption of OCV-relaxation data.
"""

import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


class Cell(object):
    """
    This class will read observed data and plot fitted observed data.
    It will also calculate theoretical ocv relaxation behavior based on given
    information about the cell.
    """

    def __init__(self, data):
        """
        :param data: observed open circuit voltage (ocv) data in pandas
        :type data: dict
        """
        self._data = data

    def tau(self, r, c):
        """
        Calculate the time constant based on which resistance and capacitance
        it receives.
        :param r: resistance [Ohm]
        :param c: capacity [F]
        :return: self._slope * self._time + r * c
        """
        pass

    def initial_conditions(self, v_ir, i_ir, r_ir):
        """
        Calculate the initial conditions with given internal resistance
        parameters. Saves the initial conditions in instances.
        instances that will be calculated:
        self._c_ct, self._r_ct, self._c_d, self._r_d, self._v_ct, self._v_d,
        self._ocv
        :param v_ir: voltage drop over internal resistance at start of OC [V]
        :param i_ir: current drop through internal resistance at start of OC [A]
        :param r_ir: internal resistance at start of OC [ohm]
        :return: None
        """
        pass

    def relaxation_rc(self):
        """
        Calculate the relaxation function with a given point in time, self.time
        initiate self.initial_conditions(self._start_volt, self._start_cur,
        self._start_res)   # Not sure about the parameters here...
        Make a local constant, modify (for modifying a rc-circuit so that
        guessing is easier).
        modify = -self._start_volt * exp(-1. / self._slope)
        if self._slope of self.tau() is 0, then -exp(-1./self._slope) = 0
        :return: self._start_volt(modify + exp(-self._time / self.tau()))
        """
        pass

    def ocv_relax_cell(self):
        """
        To use self.relaxation_rc() for calculating complete ocv relaxation
        over the cell.
        :return: voltage_d + voltage_ct + voltage_ocv (initial?) (+ v_ir?)
        """
        pass

    def guess(self):
        """
        Using self.relaxation_rc() and given parameters (coming later) to
        guess how the ocv relaxation is over the cell.
        :return: dictionary with parameters from the guessed ocv relaxation
        """
        pass

    def fitting(self):
        """
        Using measured data and scipy's "curve_fit" (non-linear least square,
        check it up with "curve_fit?" in console) to find the best fitted ocv
        relaxation curve.
        :return: dictionary of best fitted parameters and error between
        measured data and the fitting.
        """
        pass

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
    ocv_down = Cell(data_down).ocv_dic
    ocv_up = Cell(data_up).ocv_dic

    # plotting all curves in same plot. Inspiration from matplotlib,
    # section "legend guide"
    plt.figure(figsize=(15, 13))
    plt.subplot(221)
    for _ in range(len(ocv_down['time'])):
        plt.plot(ocv_down['time'][_], ocv_down['voltage'][_])
    plt.legend(legend_down, bbox_to_anchor=(1.05, 1), loc=2,
               borderaxespad=0, prop={'size': 13})
    plt.subplot(223)
    for _ in range(len(ocv_down['time'])):
        plt.plot(ocv_up['time'][_], ocv_up['voltage'][_])
    plt.legend(legend_up, bbox_to_anchor=(1.05, 1), loc=2,
               borderaxespad=0, prop={'size': 13})
    plt.show()
