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

    def __init__(self, time, voltage, v_start, i_start, c_cap, c_rate,
                 contribute):
        """
        :param data: observed open circuit voltage (ocv) data in pandas
        :type data: dict
        """
        self._time = time
        self._voltage = voltage
        self._v_cut = v_start   # Before IR-drop, cut-off voltage
        self._i_cut = i_start   # current before cut-off. Will make IR-drop
        self._c_cap = c_cap
        self._c_rate = c_rate
        self._contribute = contribute
        self.ocv = self._voltage[-1]
        self._v_0 = self._voltage[0]  # self._v_start - self._v_ir   # After
        # IR-drop (over v_ct + v_d + ocv)
        self._v_rlx = self._v_0 - self.ocv   # This is the relaxation curve
        # over v_ct + v_d
        self._v_ir = abs(self._v_cut - self._v_0)   # cut-off voltage - v_0
        self._r_ir = self._v_ir / self._i_cut
        # self._r_ct = self._v_ct / self._i_cut   # v_ct = f(v_rlx)(= v_rlx * x)
        # self._r_d = self._v_d / self._i_cut   # v_d = f(v_rlx)
        self._v_ct = None
        self._v_d = None
        self._r_ct = None
        self._r_d = None
        self._c_ct = None
        self._c_d = None
        self._v_ct_0 = None
        self._v_d_0 = None

    def tau(self, v_rc_0, v_rc, r, c, slope):
        """
        Calculate the time constant based on which resistance and capacitance
        it receives.
        :param slope: slope of the time constant [s]
        :param r: resistance [Ohm]
        :param c: capacity [F]
        :return: self._slope * self._time + r * c
        """
        if slope:
            # return tau_measured = slope * self._time + abs(self._time[-1] /
            # math.log(v_rc_0/v_rc[-1]))
            return slope * self._time + r * c
        else:
            # return tau_measured = abs(self._time[-1] / math.log(
            # v_rc_0/v_rc[-1]))
            return r * c

    def guessing_parameters(self):
        """
        Guessing likely parameters that will fit best to the measured data.
        These guessed parameters are to be used when fitting a curve to
        measured data.
        :return: None
        """
        # Say we know v_0 (after IR-drop). We also know C_cap and C_rate (
        # whatever they are). I have to assume that the charge-transfer rate
        # is 0.2 times the voltage across the relaxation circuits (0.2 is an
        # example of what self._contribute is guessed to be). So 0.2 *
        # self._v_rlx (which is self._v_0 - self.ocv. This means that 1-0.2 =
        #  0.8 times v_rlx is from the diffusion part.
        self._v_ct = self._v_rlx * self._contribute
        self._v_d = self._v_rlx * (1 - self._contribute)
        





    def initial_conditions(self):
        """
        Calculate the parameters and initial conditions. Saves the
        calculations in instances. instances that will be calculated:
        self._r_ir, self._c_ct, self._r_ct, self._c_d, self._r_d,
        self._v_ct_0, self._v_d_0
        :return: None
        """
        self._v_ct_0 = self._v_0 * (self._r_ct / (self._r_ct + self._r_d))
        self._v_d_0 = self._v_0 * (self._r_d / (self._r_ct + self._r_d))

        tau_ct = self.tau(self._v_ct_0, self._v_ct, None, None, None)
        tau_d = self.tau(self._v_d_0, self._v_d, None, None, None)
        self._c_ct = tau_ct / self._r_ct
        self._c_d = tau_d / self._r_d


    def relaxation_rc(self, v0, r, c, slope=None):
        """
        Calculate the relaxation function with a np.array of time, self.time
        Make a local constant, modify (for modifying a rc-circuit so that
        guessing is easier).
        modify = -self._start_volt * exp(-1. / self._slope)
        if self._slope of self.tau() is 0, then -exp(-1./self._slope) = 0
        :param v0: the initial voltage across the rc-circuit at t = 0,
        i.e. v_ct_0
        :return: self._start_volt(modify + exp(-self._time / self.tau()))
        """
        if slope:
            modify = -self._v_0 * math.exp(-1. / slope)
        else:
            modify = 0
        return v0 * (modify + math.exp(-self._time
                                       / self.tau(None, None,  r, c, slope)))

    def ocv_relax_cell(self, slope_d=None, slope_ct=None):
        """
        To use self.relaxation_rc() for calculating complete ocv relaxation
        over the cell. Initiate intial conditions
        :return: self._v_0 =  voltage_d + voltage_ct + voltage_ocv
        """
        self.initial_conditions()
        voltage_d = self.relaxation_rc(self._v_d_0, self._r_d, self._c_d,
                                       slope_d)   # This is self._v_d
        voltage_ct = self.relaxation_rc(self._v_ct_0, self._r_ct, self._c_ct,
                                        slope_ct)   # This is self._v_ct
        self._v_0 = voltage_d + voltage_ct + self.ocv

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
