# -*- coding: utf-8 -*-

"""
Adaption of OCV-relaxation data.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


class Cell(object):
    """
    This class will read observed data and plot fitted observed data.
    It will also calculate theoretical ocv relaxation behavior based on given
    information about the cell.
    """

    def __init__(self, data, time, v0, v_ir, i_ir, r_ir):
        """
        :param data: observed open circuit voltage (ocv) data in pandas
        :type data: dict
        """
        self._data = data
        self._time = time
        self._v0 = v0
        self._c_ct = 0
        self._r_ct = 0
        self._c_d = 0
        self._r_d = 0
        self._v_ct = 0
        self._v_d = 0
        self._v_ir = v_ir
        self._i_ir = i_ir
        self._r_ir = r_ir

    def tau(self, r, c, slope):
        """
        Calculate the time constant based on which resistance and capacitance
        it receives.
        :param slope: slope of the time constant [s]
        :param r: resistance [Ohm]
        :param c: capacity [F]
        :return: self._slope * self._time + r * c
        """
        if slope:
            return slope * self._time + r * c
        else:
            return r * c

    def initial_conditions(self):
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

    def relaxation_rc(self, r, c, slope):
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
        if slope:
            modify = -self._v0 * math.exp(-1. / slope)
        else:
            modify = 0
        return self._v0 * (modify + math.exp(-self._time
                                             / self.tau(slope, r, c)))

    def ocv_relax_cell(self):
        """
        To use self.relaxation_rc() for calculating complete ocv relaxation
        over the cell. Initiate intial conditions
        :return: voltage_d + voltage_ct + voltage_ocv (initial?) (+ v_ir?)
        """
        slope_d, slope_ct = self.initial_conditions()
        voltage_d = self.relaxation_rc(self._r_d, self._c_d, slope_d)
        voltage_ct = self.relaxation_rc(self._r_ct, self._c_ct, slope_ct)
        return voltage_d + voltage_ct + self._v_ir

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
