# -*- coding: utf-8 -*-

"""
Adaption of OCV-relaxation data.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from scipy.optimize import curve_fit

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def tau(time, r, c, slope):
    """
    Calculate the time constant based on which resistance and capacitance
    it receives.
    :param time: an array of points in time [s]
    :param slope: slope of the time constant [s]
    :param r: resistance [Ohm]
    :param c: capacity [F]
    :return: self._slope * self._time + r * c
    """
    if slope:
        # return slope * self._time + abs(self._time[-1] /
        # math.log(v_rc_0/v_rc[-1]))
        return slope * time + np.array([r * c for _ in range(len(time))])
    else:
        # return abs(self._time[-1] / math.log(v_rc_0/v_rc[-1]))
        return r * c


def guessing_parameters(v_start, i_start, voltage, contribute, tau_rc):
    """
    Guessing likely parameters that will fit best to the measured data.
    Guessed parameters are to be used when fitting a curve to measured data.
    :param v_start: voltage before IR-drop [V]
    :type v_start: float
    :param i_start: start current, calculated from current rate, mass of
    batteries and c_cap ?
    :type i_start: float
    :param voltage: measured voltage data
    :type voltage: 1d numpy array
    :param contribute: contributed partial voltage from each rc-circuit (over
    the relaxation voltage after IR-drop and ocv-level)
    :type contribute: list
    :param tau_rc: guessed time constants across each rc-circuit
    :type tau_rc: list
    :return: list of calculated parameters from guessed input parameters
    """
    # Say we know v_0 (after IR-drop). We also know C_cap and C_rate (
    # whatever they are). I have to assume that the charge-transfer rate
    # is 0.2 times the voltage across the relaxation circuits (0.2 is an
    # example of what self._contribute is guessed to be). So 0.2 *
    # self._v_rlx (which is self.v_0 - self.ocv. This means that 1-0.2 =
    #  0.8 times v_rlx is from the diffusion part.
    if sum(contribute) is not 1:
        raise ValueError('The sum of contribute does not add up to 1.')
    ocv = voltage[-1]
    # if (ocv - voltage[-2]) / ocv < 0.01:
    #     print 'WARNING: Possibly too few data points measured for optimal fit.'
    v_0 = voltage[0]
    v_rlx = v_0 - ocv
    if not isinstance(contribute, list):
        v_rc = [v_rlx]
    else:
        v_rc = [v_rlx * rc_contri for rc_contri in contribute]

    r_rc = [v / i_start for v in v_rc]
    r_ir = v_start / i_start - sum(r_rc)
    # r_ir = (v_start - v_0) / i_start
    c_rc = [t / r for t, r in tau_rc, r_rc]
    return [r_rc, r_ir, c_rc, v_rlx, ocv]


def relaxation_rc(time, v0, r, c, slope):
    """
    Calculate the relaxation function with a np.array of time, self._time
    Make a local constant, modify (for modifying a rc-circuit so that
    guessing is easier).
    modify = -self._start_volt * exp(-1. / self._slope)
    if self._slope of self.tau() is 0, then -exp(-1./self._slope) = 0
    :param time: an array of points in time [s]
    :param v0: the initial voltage across the rc-circuit at t = 0,
    i.e. v_ct_0
    :param r: the resistance over the rc-circuit
    :param c: the capacitance over the rc-circuit
    :param slope: the slope of the time constant in the rc-circuit
    :return: start_volt(modify + exp(-self._time / self.tau()))
    :type: Numpy array with relax data with same length as self._time
    """
    if slope:
        modify = np.array([(-v0 * np.exp(-1. / slope)) for _ in range(len(
            time))])
    else:
        modify = np.zeros(len(time))
    return v0 * (modify + np.exp(-time / tau(time, r, c, slope)))


def ocv_relax_func(time, r_ct, r_d, c_ct, c_d, v_rlx, ocv, slope=None):
    """
    To use self.relaxation_rc() for calculating complete ocv relaxation
    over the cell. Guessing parameters
    :return: self.v_0 =  voltage_d + voltage_ct + voltage_ocv
    """
    if not slope:
        # m is slope of time constant as a dictionary
        m = {'d': None, 'ct': None}
    else:
        m = slope
    v_initial = []
    v_d_0 = v_rlx * r_d / (r_ct + r_d)   # start voltage across diffusion
    # circuit
    v_ct_0 = v_rlx * r_ct / (r_ct + r_d)   # start voltage across
    # charge-transfer
    # need ocv to be a numpy array with the length of time
    if not isinstance(ocv, type(time)):
        ocv = np.array([ocv for _ in range((len(time)))])

    voltage_d = relaxation_rc(time, v_d_0, r_d, c_d, m['d'])
    voltage_ct = relaxation_rc(time, v_ct_0, r_ct, c_ct, m['ct'])
    return voltage_d + voltage_ct + ocv


def fitting(time, voltage, vstart, istart, contribute, tau_ct, tau_d,
            err=None, slope=None):
    """
    Using measured data and SciPy's "curve_fit" (non-linear least square,
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
    guessed_prms = guessing_parameters(vstart, istart, voltage, contribute,
                                       tau_ct, tau_d)
    print guessed_prms
    popt, pcov = curve_fit(ocv_relax_func, time, voltage, p0=guessed_prms,
                           sigma=err)
    return popt, pcov

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
        return pd.Series(sorted_data)

    sort_down = make_data(data_down)
    sort_up = make_data(data_up)

    # setting NaN (very manually) to be the last real number
    sort_up.loc[:1][0]['time'].iloc[-2] = sort_up.loc[:1][0]['time'].iloc[-3]
    sort_up.loc[:1][0]['time'].iloc[-1] = sort_up.loc[:1][0]['time'].iloc[-3]
    sort_up.loc[:1][1]['time'].iloc[-2] = sort_up.loc[:1][1]['time'].iloc[-3]
    sort_up.loc[:1][1]['time'].iloc[-1] = sort_up.loc[:1][1]['time'].iloc[-3]

    sort_up.loc[:1][0]['voltage'].iloc[-2] = sort_up.loc[:1][0][
        'voltage'].iloc[-3]
    sort_up.loc[:1][0]['voltage'].iloc[-1] = sort_up.loc[:1][0][
        'voltage'].iloc[-3]
    sort_up.loc[:1][1]['voltage'].iloc[-2] = sort_up.loc[:1][1][
        'voltage'].iloc[-3]
    sort_up.loc[:1][1]['voltage'].iloc[-1] = sort_up.loc[:1][1][
        'voltage'].iloc[-3]

    ocv_add = 0.002
    v_start_down = 1.   # all start are taken from fitting_ocv_003.py
    v_start_up = 0.01
    i_cut_off = 0.000751
    contri = 0.2   # taken from "x" in fitting_ocv_003.py, func. GuessRC2
    # print np.array(sort_up[0][:]['voltage'])[-1]
    tau_ct_guess = 50
    tau_d_guess = 400

    popt_down = []
    pcov_down = []
    popt_up = []
    pcov_up = []

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
    for cycle_up in range(3):
        optimal, covariance = \
            fitting(np.array(sort_up[cycle_up][:]['time']),
                    np.array(sort_up[cycle_up][:]['voltage']),
                    v_start_up, i_cut_off, contri, tau_ct_guess, tau_d_guess)
        popt_up.append(optimal)
        pcov_up.append(covariance)
        print popt_up[cycle_up]
        print np.diag(np.sqrt(pcov_up[cycle_up]))
        print '======================='


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

    fig = plt.figure(figsize=(20, 13))
    plt.suptitle('OCV-relaxation data from cell "sic006_cc_45" with best '
                 'fitted and guessed parameters',
                 size=20)
    subs = [fig.add_subplot(3, 1, 1), fig.add_subplot(3, 1, 2),
            fig.add_subplot(3, 1, 3)]
    #Gridspec!!
    # subs = [fig.add_subplot(6, 1, 1), fig.add_subplot(6, 1, 3),
    #         fig.add_subplot(6, 1, 5)]
    # res = [fig.add_subplot(6, 1, 2), fig.add_subplot(6, 1, 4),
    #        fig.add_subplot(6, 1, 6)]
    for cycle_plot_up in range(3):
        t_up = np.array(sort_up[cycle_plot_up][:]['time'])
        v_up = np.array(sort_up[cycle_plot_up][:]['voltage'])
        guess = guessing_parameters(v_start_up, i_cut_off, v_up, contri,
                                    tau_ct_guess, tau_d_guess)
        guessed_fit = ocv_relax_func(t_up, *guess)
        best_fit = ocv_relax_func(t_up, *popt_up[cycle_plot_up])
        ocv_relax = np.array([guess[-1] + ocv_add for _ in range((len(t_up)))])
        subs[cycle_plot_up].plot(t_up, v_up, 'ob', t_up, guessed_fit, '--r',
                                 t_up, best_fit, '-y',
                                 t_up, ocv_relax, '--c')
        subs[cycle_plot_up].set_xlabel('Time (s)')
        subs[cycle_plot_up].set_ylabel('Voltage (V)')
        subs[cycle_plot_up].legend(['Measured', 'Guessed', 'Best fit',
                                    'ocv - relaxed'])
        # residuals. Don't know how to yet.. Check out gridspec
        # diff = v_up - best_fit
        # res[cycle_plot_up].plot(t_up, diff, 'or')
        # res[cycle_plot_up].legend(['Residuals'])

    plt.show()
