# -*- coding: utf-8 -*-

"""Simulation of Open Circuit Voltage (ocv) - relaxation with a rc - model.

This script calculate ocv-relaxation voltage with a resistance-capacitance (rc)-
model. The rc-model is based on a simplified 'Randles circuit'_.

Use "fitting_cell_ocv.py" to start fitting your parameters with this model.

Todo:
    * Make tests

.. _Randles circuit:
    http://www.gamry.com/application-notes/EIS/basics-of-electrochemical-impedance-spectroscopy/

"""

import numpy as np

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def tau(time, r, c, slope):
    """Calculates the time constant based on resistance and capacitance.

    The time constant can vary linearly with the time.
    Args:
        time (nd.array): Points in time [s].
        r (float): Resistance [Ohm].
        c (float): Capacitance [F].
        slope (float): Slope of the time constant [s].

    Returns:
        float: The rc-circuit's time constant.

    """
    if slope:
        return slope * time + np.array([r * c for _ in range(len(time))])
    else:
        return r * c


def relaxation_rc(time, v0, tau_rc):
    """
    Calculates the relaxation function of an rc-circuit.

    Args:
        time (nd.array): Points in time [s].
        v0 (float): The initial voltage across the rc-circuit at t = 0 [V].
        tau_rc (float): The rc-circuit's resistance [Ohm].

    Returns:
        nd.array: The rc-circuit's relaxation voltage.

    """
    # Don't know what modify is suppose to be for ...
    # if the time constant isn't constant, but linear, modify will be made.
    # if slope:
    #     modify = np.array([(-v0 * np.exp(-1. / slope)) for _ in range(len(
    #         time))])
    # else:
    #     modify = np.zeros(len(time))
    # return v0 * (modify + np.exp(-time / tau(time, r, c, slope)))

    return v0 * np.exp(-time / tau_rc)


def ocv_relax_func(time, ocv, v0_rc, tau_rc, slope=None):
    """Calculates the cell's relaxation voltage.

    Args:
        time (nd.array): Points in time [s].
        ocv (nd.array): Open circuit voltage [V].
        v0_rc (dict): Initial relaxation voltage for each rc-circuits [V].
        tau_rc (dict): The rc-circuit's time constant [s].
        slope (dict): Slope of the rc's time constants [s].

    Returns:
        nd.array: The relaxation voltage of the model
    """
    # if not slope:
    #     m = {key: None for key in tau_rc.keys()}
    # else:
    #     m = slope

    # # Initial voltage across rc_circuits
    # v_initial = {key: v_rlx * r / sum(r_rc.values()) for key, r in r_rc.items()}
    volt_rc = [relaxation_rc(time, v0_rc[rc], tau_rc[rc])
               for rc in tau_rc.keys()]
    return sum(volt_rc) + ocv


def guessing_parameters(v_start, i_start, v_0, v_ocv, contribute, tau_rc):
    """
    Initial parameter guess.

    Args:
        v_start (float): Voltage before IR-drop [V].
        i_start (float): Current right before open circuit [A].
        v_0 (float): Voltage after IR-drop [V].
        v_ocv (float): Guessed voltage at full relaxation [V].
        contribute (dict): The rc-circuits contributed part of v_0.
        tau_rc (dict): Guessed time constants across each rc-circuit

    Returns:
        dict: Guessed parameters.
    """

    if sum(contribute.values()) != 1.0:
        raise ValueError('The sum of contribute does not add up to 1.')
    v_rlx = v_0 - v_ocv   # voltage over the rc-circuits without a reference
    if len(contribute) == 1:
        v0_rc = {contribute.keys()[0]: v_rlx}
    else:
        v0_rc = {rc: v_rlx * rc_contri for rc, rc_contri in contribute.items()}

    r_rc = {key: abs(v0 / i_start) for key, v0 in v0_rc.items()}
    r_ir = abs(v_start / i_start - sum(r_rc.values()))
    # r_ir_2 = (v_start - v_0) / i_start   # This one is different than r_ir...?
    c_rc = {k: t / r for k, r in r_rc.items() for i, t in tau_rc.items()
            if i == k}
    return\
        {'r_rc': r_rc, 'r_ir': r_ir, 'c_rc': c_rc, 'v0_rc': v0_rc}


# def fitting(time, voltage, vstart, istart, contribute, tau_rc, err=None,
#             slope=None):
#     """
#     Fitting to measured data by adjusting parameters using SciPy's curve_fit.
#
#     :param time: measured point in time [s]
#     :type time: numpy array
#     :param voltage: measured voltage data [V]
#     :type voltage: numpy array
#     :param vstart: start voltage before IR-drop after charge/discharge [V]
#     :type vstart: float
#     :param istart: start current. Calculated from current rate during [A]
#     charge/discharge, mass of cell and c_cap ?
#     :type istart: float
#     :param contribute: contributed partial voltage from each rc-circuit (over
#     the relaxation voltage after IR-drop and ocv-level)
#     :type contribute: dict
#     :param tau_rc: guessed time constants for each rc-circuit [s]
#     :type tau_rc: dict
#     :param err: measurement error
#     :param slope: slope of the rc time constants
#     :type slope: dict
#     :return: list of best fitted parameters and covariance between measured
#     data and the fitting.
#     """
#     # (time, r_rc, c_rc, v_rlx, ocv, slope=None):
#     guessed_prms = guessing_parameters(vstart, istart, voltage, contribute,
#                                        tau_rc)
#     # print guessed_prms   # Note that guessed_prms are not in right order,
#     # that's why guessed_sorted is done manually...
#     guessed_sorted = guessed_prms['r_rc'].values() + guessed_prms[
#         'c_rc'].values()
#     guessed_sorted.append(guessed_prms['ocv'])
#
#     N_rc = len(guessed_prms['r_rc'].values())
#
#     def adjusted_ocv_relax_function(t, n_rc, *args):
#         """
#         To make SciPy's function curve_fit understand input parameters.
#
#         Heavily inspired by:
#         http://stackoverflow.com/questions/34136737/
#         using-scipy-curve-fit-for-a-variable-number-of-parameters
#
#         :param t: measure points in time [s]
#         :type t: numpy array
#         :param n_rc: total number of rc-circuits in model
#         :type n_rc: int
#         :param args: any wanted parameters
#         :return: function call ocv_relax_func
#         """
#         r_rc, c_rc = list(args[0][0: n_rc]), list(args[0][n_rc:-1])
#         r_rc = {key: r for key, r in zip(guessed_prms['r_rc'], r_rc)}
#         c_rc = {k: c for k, c in zip(guessed_prms['c_rc'], c_rc)}
#         ocv = args[0][-1]
#         return ocv_relax_func(t, r_rc, c_rc, ocv, *args[1:])
#
#     # popt are the "optimal parameters" based on initial guess and
#     # theoretical
#     # function.
#     # pcov is covariance of the parameters. It's a matrix with the variance of
#     # popt on the diagonal. To get the standard derivation error, compute:
#     # perr = np.sqrt(diag(pcov)), where perr is "parameter error".
#     popt, pcov = curve_fit(lambda t, *p:
#                            adjusted_ocv_relax_function(t, N_rc, p,
#                                                        guessed_prms['v_rlx']),
#                            time, voltage, p0=guessed_sorted, sigma=err)
#
#     popt_dict = {'r_rc': {key: value for key, value in
#                           zip(guessed_prms['r_rc'], popt[:N_rc])}}
#     popt_c = {'c_rc': {k: val for k, val in
#                        zip(guessed_prms['c_rc'], popt[N_rc:-1])}}
#     pcov_dict = {'r_rc': {c_key: c_value for c_key, c_value in
#                           zip(guessed_prms['r_rc'], pcov[:N_rc])}}
#     pcov_c = {'c_rc': {c_k: c_val for c_k, c_val in
#                        zip(guessed_prms['c_rc'], pcov[N_rc:-1])}}
#     popt_dict.update(popt_c)
#     popt_dict.update({'ocv': popt[-1]})
#     popt_dict.update({'v_rlx': guessed_prms['v_rlx']})
#     pcov_dict.update(pcov_c)
#     return popt_dict, pcov_dict
#
#
# if __name__ == '__main__':
#     datafolder = r'..\data_ex'   # make sure you're in folder \utils. If not,
#     # activate "print os.getcwd()" to find current folder and extend datafolder
#     # with [.]\utils\data
#     # print os.getcwd()
#     filename_down = r'20160805_test001_45_cc_01_ocvrlx_down.csv'
#     filename_up = r'20160805_test001_45_cc_01_ocvrlx_up.csv'
#     down = os.path.join(datafolder, filename_down)
#     up = os.path.join(datafolder, filename_up)
#     data_down = pd.read_csv(down, sep=';')
#     data_up = pd.read_csv(up, sep=';')
#
#     # need to separate time and voltage so they can be combined as y(x)
#     def make_data(data):
#         """
#         This function will split xy-xy-xy-xy... pandas data pd.read_csv to
#         numpy array with only x and one with only y.
#         :param data: pandas DataFrame that has multi xy data as column info
#         :return: a list with number of cycles as length. Each cycle
#         has its pandas DataFrame with time-voltage for that cycle.
#         """
#         # extracting time data
#         time_data = [t for i in range(len(data.iloc[0, :])) for t in
#                      data.iloc[:, i] if not i % 2]
#         # extracting voltage data. The "if .. and t, v <950 will only
#         # extract three first columns. This is temper as the first data only
#         # had 3 ok set.
#         voltage_data = [v for k in range(0, len(data.iloc[0, :]))
#                         for v in data.iloc[:, k] if k % 2]
#         num_cycles = len(time_data)/len(data)
#         sorted_data = []
#         key = 0
#         for _ in range(0, num_cycles):
#             time = time_data[key:key + len(data)]
#             volt = voltage_data[key:key + len(data)]
#             key += len(data)
#             sorted_data.append(pd.DataFrame(zip(time, volt), columns=['time',
#                                                                       'voltage'
#                                                                       ]))
#         return pd.Series(sorted_data)
#
#     sort_down = make_data(data_down)
#     sort_up = make_data(data_up)
#
#     # setting NaN (very manually) to be the last real number
#     sort_up.loc[:1][0]['time'].iloc[-2] = sort_up.loc[:1][0]['time'].iloc[-3]
#     sort_up.loc[:1][0]['time'].iloc[-1] = sort_up.loc[:1][0]['time'].iloc[-3]
#     sort_up.loc[:1][1]['time'].iloc[-2] = sort_up.loc[:1][1]['time'].iloc[-3]
#     sort_up.loc[:1][1]['time'].iloc[-1] = sort_up.loc[:1][1]['time'].iloc[-3]
#
#     sort_up.loc[:1][0]['voltage'].iloc[-2] = sort_up.loc[:1][0][
#         'voltage'].iloc[-3]
#     sort_up.loc[:1][0]['voltage'].iloc[-1] = sort_up.loc[:1][0][
#         'voltage'].iloc[-3]
#     sort_up.loc[:1][1]['voltage'].iloc[-2] = sort_up.loc[:1][1][
#         'voltage'].iloc[-3]
#     sort_up.loc[:1][1]['voltage'].iloc[-1] = sort_up.loc[:1][1][
#         'voltage'].iloc[-3]
#
#     ocv_add = 0.002   # this is just to set the ocv level a bit higher,
#     # arbitrary addition
#     v_start_down = 1.   # all start variables are taken from fitting_ocv_003.py
#     v_start_up = 0.01
#     i_cut_off = 0.000751
#     contri = {'ct': 0.2, 'd': 0.8}   # taken from "x" in fitting_ocv_003.py,
#     # function "GuessRC2"
#     tau_guessed = {'ct': 50, 'd': 400}
#     popt_down = []
#     pcov_down = []
#     popt_up = []
#     pcov_up = []
#
#     # down does not have good enough values yet... When own measurements are
#     # done, activate this again.
#     # for cycle_down in range(0, len(sort_down)):
#     #    optimal_d, covariance_d = \
#     #            fitting(np.array(sort_down[cycle_down][:]['time']),
#     #                    np.array(sort_down[cycle_down][:]['voltage']),
#     #                    v_start_up, i_cut_off, contri, tau_guessed)
#     #    popt_down.append(optimal_d)
#     #    pcov_down.append(covariance_d)
#
#     for cycle_up in range(3):
#         optimal, covariance = \
#             fitting(np.array(sort_up[cycle_up][:]['time']),
#                     np.array(sort_up[cycle_up][:]['voltage']),
#                     v_start_up, i_cut_off, contri, tau_guessed)
#         popt_up.append(optimal)
#         pcov_up.append(covariance)
#
#
#     def define_legends():
#         """
#         creating a list with legends from both up and down ocv_data
#
#         :return: list of legends for ocv_data
#         """
#         leg_down = []
#         leg_up = []
#         count = 0
#         for lbl_down in data_down:
#             if count % 2:
#                 leg_down.append(str(lbl_down))
#             count += 1
#         count = 0
#         for lbl_up in data_up:
#             if count % 2:
#                 leg_up.append((str(lbl_up)))
#             count += 1
#         return leg_down, leg_up
#
#     legend_down, legend_up = define_legends()
#     fig = plt.figure(figsize=(20, 13))
#     plt.suptitle('OCV-relaxation data from cell "sic006_cc_45_01" with best '
#                  'fitted and guessed parameters',
#                  size=20)
#     subs = [fig.add_subplot(3, 1, 1), fig.add_subplot(3, 1, 2),
#             fig.add_subplot(3, 1, 3)]
#     #Gridspec!!
#     # subs = [fig.add_subplot(6, 1, 1), fig.add_subplot(6, 1, 3),
#     #         fig.add_subplot(6, 1, 5)]
#     # res = [fig.add_subplot(6, 1, 2), fig.add_subplot(6, 1, 4),
#     #        fig.add_subplot(6, 1, 6)]
#
#     for cycle_plot_up in range(3):
#         t_up = np.array(sort_up[cycle_plot_up][:]['time'])
#         v_up = np.array(sort_up[cycle_plot_up][:]['voltage'])
#         guess = guessing_parameters(v_start_up, i_cut_off, v_up, contri,
#                                     tau_guessed)
#         guessed_fit = ocv_relax_func(t_up, r_rc=guess['r_rc'],
#                                      c_rc=guess['c_rc'],
#                                      v_rlx=guess['v_rlx'], ocv=guess['ocv'])
#         p_u = popt_up[cycle_plot_up]
#         best_fit = ocv_relax_func(t_up, r_rc=p_u['r_rc'],
#                                   c_rc=p_u['c_rc'], v_rlx=p_u['v_rlx'],
#                                   ocv=p_u['ocv'])
#         print 'Guessed parameters: ', guess
#         print 'Best fitted parameters: ', p_u
#         print '\t'
#         print '------------------------------------------------------------'
#         # print guessed_fit, best_fit
#         # print '============================================================'
#         ocv_relax = np.array([p_u['ocv'] for _ in range((len(t_up)))])
#         subs[cycle_plot_up].plot(t_up, v_up, 'ob', t_up, guessed_fit, '--r',
#                                  t_up, best_fit, '-y',
#                                  t_up, ocv_relax, '--c')
#         subs[cycle_plot_up].set_xlabel('Time (s)')
#         subs[cycle_plot_up].set_ylabel('Voltage (V)')
#         subs[cycle_plot_up].legend(['Measured', 'Guessed', 'Best fit',
#                                     'ocv - relaxed'])
#         # residuals. Don't know how to yet.. Check out gridspec
#         # diff = v_up - best_fit
#         # res[cycle_plot_up].plot(t_up, diff, 'or')
#         # res[cycle_plot_up].legend(['Residuals'])
#
#     plt.show()
