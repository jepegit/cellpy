# -*- coding: utf-8 -*-

"""
Fitting parameters with 'lmfit'_ using non-linear least square.

By using 'lmfit'_, you are more freely to freeze parameters and set
boundaries than with 'scipy's curve_fit'_. This script import the model from::
    $ python cell_ocv.py'

Example:
    Call guessing_parameters(). Use these parameters to give 'lmfit'_'s
    Parameter an initial parameter value. Call ocv_relax_func() and subtract
    from measured data to get residual.
    For relaxation of a single rc-circuit, call relaxation_rc().
    >>> ex_time = np.array(range(5))
    >>> ex_voltage = np.array([0.05 * np.exp(-float(t)/100) for t in ex_time])
    >>> ex_v_s = 1.
    >>> ex_i_s = 0.005
    >>> ex_v0 = ex_voltage[0]
    >>> ex_v_oc = ex_voltage[-1]
    >>> ex_contribute = {'d': 1}
    >>> ex_tau = {'d': 100}
    >>> ex_guess = guessing_parameters(v_start=ex_v_s, i_start=ex_i_s,
    >>> v_0=ex_v0, v_ocv=ex_v_oc, contribute=ex_contribute, tau_rc=ex_tau)
    >>> Ex_para = Parameters()
    >>> Ex_para.add('tau_d', value=ex_tau['d'], min=0)
    >>> Ex_para.add('ocv', value=ex_guess['ocv'])
    >>> Ex_para.add('v0_d', value=ex_guess['v0_rc']['d'])
    >>> ex_Minimizer = Minimizer(ocv_user_adjust, params=Ex_para,
    >>> fcn_args=(ex_time, ex_voltage))
    >>> ex_mini = ex_Minimizer.minimize()
    >>> print ex_mini.residual
    >>> print '\t'
    >>> print ex_mini.params.valuesdict()
    [0, 0, 0, 0, 0]
    OrderedDict([('tau_d', 100), ('ocv', 0.04803947), ('v0_d', 0.04803947])

Todo:
    * Not plot in fitting_cell_ocv, but create an other script for that.
    * Check if example above works and give expected values.
    * Make tests.
    * Implement r_ir
    * Implement relaxation downwards (after charge)

.._lmfit:
https://github.com/lmfit/lmfit-py
.._scipy's curve_fit:
http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html
"""

from lmfit import Parameters, report_fit, Model
from cell_ocv import *

import StringIO
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import os
import copy

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

# from fitting_ocv_003.py
# ocv_ex = """0.857999938	0.067619018
# 11.40338493	0.072845809
# 42.92991797	0.078072593
# 99.15056006	0.083299384
# 159.1619675	0.086373962
# 219.1732833	0.089141086
# 279.1847434	0.090985835
# 339.1961105	0.092830583
# 399.2077133	0.094060414
# 459.2190174	0.095290251
# 519.2302308	0.096520081
# 579.2416535	0.097135
# 639.2529781	0.09836483
# 699.2644135	0.098979741
# 759.2757954	0.09959466
# 819.2871618	0.099902116
# 879.2985487	0.100517035
# 939.3099087	0.101439409
# 999.3213345	0.101439409
# 1059.333063	0.102054328
# 1119.344104	0.102669239
# 1179.355458	0.102976702
# 1239.366895	0.103591613
# 1299.378221	0.103899077
# 1359.389606	0.104513988
# 1419.400967	0.104513988
# 1479.412349	0.104821451
# 1539.42414	0.105128907
# 1599.435153	0.105436362
# 1659.446518	0.106051281
# 1719.457927	0.106051281
# 1779.469299	0.106358737
# 1800.01385	0.106358737
# """
#
# ocv_ex = StringIO.StringIO(ocv_ex)
# t = []   # time list
# u = []   # voltage list
#
# cut_off = None
# for line in ocv_ex:
#     t1, u1 = line.split('\t')
#     t.append(float(t1))
#     u.append(float(u1))
#     if cut_off and float(t1) > cut_off:
#         print "cut at t = %s" % t1
#         break
# t = np.array(t)
# u = np.array(u)


def manipulate_data(read_data):
    """Making data in a format, y(x), and saving it in a pandas DataFrame.

    Args:
        read_data (nd.array): pandas.Dataframe with xy data.

    Returns:
        nd.array: A pandas.Series with time-voltage to the cycles.

    """

    time_data = [t for t_col in range(len(read_data.iloc[0, :])) for t in
                 read_data.iloc[:, t_col] if not t_col % 2]
    voltage_data = [v for v_col in range(0, len(read_data.iloc[0, :]))
                    for v in read_data.iloc[:, v_col] if v_col % 2]
    num_cycles = len(time_data)/len(read_data)
    sorted_data = []
    key = 0
    for _ in range(0, num_cycles):
        _time = time_data[key:key + len(read_data)]
        _volt = voltage_data[key:key + len(read_data)]
        key += len(read_data)
        sorted_data.append(pd.DataFrame(zip(_time, _volt), columns=['time',
                                                                    'voltage'
                                                                    ]))
    return pd.Series(sorted_data)


def plot_voltage(t, v, best):
    """Making a plot with given voltage data.

    Args:
        t (nd.array): Points in time [s].
        v (nd.array): Measured voltage [V].
        best (ModelResult): All fitted data in lmfit object Model.
        rc_para (dict): Calculated resistance and capacitance from fit.

    Returns:
        None: Making a plot with matplotlib.pyplot

    """
    # print 'Guessed parameters: ', best.init_values
    # print 'Best fitted parameters: ', result_params
    # print '\t'
    # print '------------------------------------------------------------'
    result_params = best.params
    ocv = np.array([result_params['ocv'] for _ in range(len(t))])
    tau_rc = {tau_key: tau_val for tau_key, tau_val in result_params.items()
              if tau_key.startswith('tau')}
    v0_rc = {v0_key: v0_val for v0_key, v0_val in result_params.items()
             if v0_key.startswith('v0')}

    rc_circuits = {rc[4:]: relaxation_rc(t, v0_rc['v0_%s' % rc[4:]], tau_rc[rc])
                   for rc in tau_rc.keys()}
    plt.plot(t, v, 'ob')
    plt.plot(t, best.init_fit, '--k')
    plt.plot(t, best.best_fit, '-r')
    plt.plot(t, ocv, '--c')
    plt.plot(t, rc_circuits['ct'], '-g')
    plt.plot(t, rc_circuits['d'], '-y')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.legend(['Measured', 'Initial guess', 'Best fit', 'ocv - relaxed',
                'Charge-transfer rc-circuit', 'Diffusion rc-circuit'],
               loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 10})
    plt.grid()

    # Suppose to add a text with the value of the parameters for the fit.

    # mover = 0.1
    # for s_r, res in r.items():
    #     txt = '%s: %i' % (s_r, res)
    #     plt.text(mover, 0.5, txt, bbox=dict(facecolor='red'))
    #     mover += 0.1
    # for s_c, cap in c.items():
    #     txt = '%s: %i' % (s_c, cap)
    #     plt.text(mover, 0.5, txt, bbox=dict(facecolor='red'))
    #     mover += 0.1


# def print_params(ini, fit):
#
#     for key, value in fit.items():
#         print 'Guessed: %-9 Fitted Parameters:'
#         print '\t'
#         print '%s: %-9f %f' % (key, ini[key], value)

# def relax_model(t, **params):
#     """Fitting of parameters with lmfit.
#
#     Not using cell_ocv this time, but integrating it in the function itself.
#
#     Args:
#         params (Parameters): Parameters that user want to fit.
#         t (nd.array): Points in time [s].
#
#     Returns:
#         nd.array: The expected voltage form model.
#     """
#     ocv_arr = np.array([params['ocv'] for _ in range((len(t)))])
#     tau_rc = {key[4:]: val
#               for key, val in params.items() if key.startswith('tau')}
#     v0_rc = {key[3:]: val for key, val in params.items()
#              if key.startswith('v0')}
#     rc_d = v0_rc['d'] * np.exp(-t / tau_rc['d'])
#     rc_ct = v0_rc['ct'] * np.exp(-t / tau_rc['ct'])
#     total = rc_d + rc_ct + ocv_arr
#     return total

def relax_model(t, **params):
    """Fitting of parameters with lmfit.

    User must know what the Parameters object, par, looks like and re-arrange
    the parameters into the right format for ocv_relax_func.

    Args:
        params (Parameters): Parameters that user want to fit.
        t (nd.array): Points in time [s].

    Returns:
        nd.array: The expected voltage from model.

    """
    ocv_arr = np.array([params['ocv'] for _ in range((len(t)))])
    tau_rc = {key[4:]: val
              for key, val in params.items() if key.startswith('tau')}
    v0_rc = {key[3:]: val for key, val in params.items()
             if key.startswith('v0')}
    return ocv_relax_func(t, tau_rc=tau_rc, ocv=ocv_arr, v0_rc=v0_rc)


# def ocv_user_adjust(par, t, meas_volt):
#     """Fitting of parameters with lmfit.
#
#     User must know what the Parameters object, par, looks like and re-arrange
#     the parameters into the right format for ocv_relax_func.
#
#     Args:
#         par (Parameters): Parameters that user want to fit.
#         t (nd.array): Points in time [s]
#         meas_volt (nd.array): Measured voltage [s]
#
#     Returns:
#         nd.array: The residual between the expected voltage and measured.
#
#     """
#
#     p_dict = par.valuesdict()
#     r_rc = {key[2:]: val for key, val in p_dict.items() if key.startswith('r')}
#     c_rc = {key[2:]: val for key, val in p_dict.items() if key.startswith('c')}
#     v0_rc = {key[3:]: val for key, val in p_dict.items()
#              if key.startswith('v0')}
#     return ocv_relax_func(t, r_rc=r_rc, c_rc=c_rc, ocv=p_dict['ocv'],
#                           v0_rc=v0_rc) - meas_volt


if __name__ == '__main__':
    """Reading data.

    Reading the .csv file with all the cycling data.

    Make sure you're in folder \utils. If not::
        >>>print os.getcwd()

    to find current folder and extend datafolder with [.]\utils\data
    ----------------------------------------------------------------------------
    """
    datafolder = r'..\data_ex'

    # filename_down = r'20160805_test001_45_cc_01_ocvrlx_down.csv'
    # filename_up = r'20160805_test001_45_cc_01_ocvrlx_up.csv'
    filename_up = r'74_data_up.csv'
    filename_down = r'74_data_down.csv'
    down = os.path.join(datafolder, filename_down)
    up = os.path.join(datafolder, filename_up)
    data_down = pd.read_csv(down, sep=';')
    data_up = pd.read_csv(up, sep=';')
    data_up = manipulate_data(data_up)
    data_down = manipulate_data(data_down)

    """Defining model.

    Tell the script how the model looks like. How many RC-circuits are there?
    Make initial guesses for the time constant and voltage-contribute from each
    RC-circuit. "contri_..." is your guessed percentage of voltage which the
    RC-circuit contribute to over the total relaxation.
    """
    contri_ct = 0.2
    contri_d = 1 - contri_ct
    tau_ct = 50
    tau_d = 550
    contri = {'ct': contri_ct, 'd': contri_d}
    tau_guessed = {'ct': tau_ct, 'd': tau_d}


    def ocv_cycle(ocv_data, user_cycles, v_start, i_start):
        """Fitting, plotting and reporting user defined ocv relaxation cycles.

        Args:
            ocv_data (pd.Series): Time-voltage DataFrames of ocv - relaxation.
            user_cycles (str): Number of cycles to report and plot.
            v_start (float): Start voltage before IR-drop.
            i_start (list): Current before ocv for each cycle.

        Returns:
            None: Fitting data with model.
        """

        """Preparations for fitting parameters.

        Write boundary conditions and initial guesses.
        Removing "nan" is inspired by 'stackoverflow'_

        .._stackoverflow:
            http://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array
        ------------------------------------------------------------------------

        """
        time = []
        voltage = []
        for i, sort in ocv_data.iteritems():
            time.append(np.array(sort[:]['time']))
            voltage.append(np.array(sort[:]['voltage']))
            time[i] = time[i][~np.isnan(time[i])]
            voltage[i] = voltage[i][~np.isnan(voltage[i])]
        v_ocv = voltage[0][-1]
        v_0 = voltage[0][0]

        if v_ocv < v_0:
            # after charge
            rlx_txt = "delithiation (downwards relaxation)"
        else:
            rlx_txt = "lithiation (upward relaxation)"

        init_guess = guessing_parameters(v_start, i_start[0], v_0,
                                         v_ocv, contri, tau_guessed)
        # initial_param_up = Parameters()
        # # r_ct and r_d are actually tau_ct and tau_d when fitted because c = 1 (fix)
        # initial_param_up.add('r_ct', value=tau_guessed['ct'], min=0)
        # initial_param_up.add('r_d', value=tau_guessed['d'], min=0)
        # # initial_param_up.add('r_sei', value=tau_guessed['sei'], min=0)
        # initial_param_up.add('c_ct', value=1., vary=False)
        # initial_param_up.add('c_d', value=1., vary=False)
        # # initial_param_up.add('c_sei', value=1, vary=False)
        # initial_param_up.add('ocv', value=v_ocv, min=v_ocv)
        # initial_param_up.add('v0_ct', value=init_guess['v0_rc']['ct'])
        # initial_param_up.add('v0_d', value=init_guess['v0_rc']['d'])
        # # initial_param_up.add('v0_sei', value=init_guess['v0_rc']['sei'])

        """Fitting parameters.
        ------------------------------------------------------------------------

        """
        # making a class Minimizer that contain fitting methods and attributes
        # Mini_initial_up = Minimizer(ocv_user_adjust, params=initial_param_up,
        #                             fcn_args=(time[0], voltage[0]),)
        # minimize() perform the minimization on Minimizer's attributes
        # result = [Mini_initial_up.minimize()]
        # Creating an lmfit Model object out of function "relax_model".
        r_model = Model(relax_model, missing='raise')
        r_model.set_param_hint('tau_ct', value=tau_guessed['ct'], min=0,
                               max=tau_guessed['d'])
        r_model.set_param_hint('tau_d', value=tau_guessed['d'],
                               min=tau_guessed['ct'])
        r_model.set_param_hint('ocv', value=v_ocv)
        if v_ocv < v_0:
            # after charge (relax downwards)
            r_model.set_param_hint('v0_ct', value=init_guess['v0_rc']['ct'],
                                   min=0)
            r_model.set_param_hint('v0_d', value=init_guess['v0_rc']['d'],
                                   min=0)
        else:
            r_model.set_param_hint('v0_ct', value=init_guess['v0_rc']['ct'],
                                   max=0)
            r_model.set_param_hint('v0_d', value=init_guess['v0_rc']['d'],
                                   max=0)
        r_model.make_params()
        result_initial = r_model.fit(voltage[0], t=time[0])
        # result_initial.conf_interval()
        result = [result_initial]

        best_para = [result[0].params]
        err_para = np.sqrt(np.diag(result_initial.covar))
        error_para = {para_name: err_para[err]
                      for err, para_name in enumerate(r_model.param_names)}
        best_para_error = [error_para]

        best_rc_ini = {'r_%s' % key[3:]: abs(v0_rc / i_start[0])
                       for key, v0_rc in best_para[0].valuesdict().items()
                       if key.startswith('v0')}

        best_c_ini = {'c_%s' % key[4:]: tau_rc / best_rc_ini['r_%s' % key[4:]]
                      for key, tau_rc in best_para[0].valuesdict().items()
                      if key.startswith('tau')}
        best_rc_ini.update(best_c_ini)
        best_rc_para = [best_rc_ini]
        # report_fit(result[0])
        #
        # """Plotting initial fit to see if it is the same as what minimize() give.
        # """
        # best_para_dict = best_para[0].valuesdict()
        # v0_rc = {key[3:]: val for key, val in best_para_dict.items() if
        #          key.startswith('v0')}
        # r_rc_up = {key[2:]: val for key, val in best_rc_ini.items() if
        #            key.startswith('r')}
        # c_rc_up = {key[2:]: val for key, val in best_c_ini.items()}
        # # tau_rc_up has keys r_ct and r_d, but since c was fixed at 1. Therefore tau
        # tau_rc_up = {key[2:]: val for key, val in best_para_dict.items()
        #              if key.startswith('r')}
        # c_fixed = {key[2:]: 1. for key in best_c_ini.keys()}
        # relax_with_best_rc_calc = ocv_relax_func(time=time[0],
        #                                          ocv=best_para_dict['ocv'],
        #                                          v0_rc=v0_rc, r_rc=tau_rc_up,
        #                                          c_rc=c_fixed)
        # relax_with_best_tau = ocv_relax_func(time=time[0],
        #                                      ocv=best_para_dict['ocv'],
        #                                      v0_rc=v0_rc,
        #                                      r_rc=r_rc_up,
        #                                      c_rc=c_rc_up)
        # plt.figure(figsize=(20, 13))
        # ocv_up_ini = np.array([best_para_dict['ocv'] for nothing in range(len(
        #     time[0]))])
        # plt.plot(time[0], voltage[0], 'ob', time[0],
        #          best_fit_voltage_up[0], '-g', time[0],
        #          relax_with_best_rc_calc, '-r', time[0], relax_with_best_tau,
        #          '-y', time[0], ocv_up_ini, '--c')
        # plt.legend(['Measured', 'lmfit plot', 'Best with calculated rc',
        #             'Best with fitted tau'])
        # plt.show()

        for cycle_i in range(1, len(time)):
            temp_start_voltage = voltage[cycle_i][0]
            temp_end_voltage = voltage[cycle_i][-1]
            # best_para[cycle_i - 1]['v_rlx'].set(
            #     min=temp_start_voltage-temp_end_voltage)
            # temp_para_up = best_para[cycle_i - 1].copy.deepcopy()
            # temp_para_up['ocv'].set(value=temp_end_voltage, min=temp_end_voltage)
            # Temp_mini = Minimizer(ocv_user_adjust,
            #                       params=temp_para_up,
            #                       fcn_args=(time[cycle_i],
            #                                 voltage[cycle_i]))
            # result.append(Temp_mini.minimize())
            if i_start[cycle_i] is not i_start[cycle_i - 1]:
                temp_initial_guess = guessing_parameters(v_start,
                                                         i_start[cycle_i],
                                                         temp_start_voltage,
                                                         temp_end_voltage,
                                                         contri, tau_guessed)
                r_model.set_param_hint('ocv', value=temp_end_voltage)
                if v_ocv < v_0:
                    # after charge (relax downwards)
                    r_model.set_param_hint('v0_ct',
                                           value=temp_initial_guess[
                                               'v0_rc']['ct'],
                                           min=0)
                    r_model.set_param_hint('v0_d',
                                           value=temp_initial_guess[
                                               'v0_rc']['d'],
                                           min=0)
                else:
                    r_model.set_param_hint('v0_ct',
                                           value=temp_initial_guess[
                                               'v0_rc']['ct'],
                                           max=0)
                    r_model.set_param_hint('v0_d',
                                           value=temp_initial_guess[
                                               'v0_rc']['d'],
                                           max=0)
                r_model.make_params()
                result_cycle = r_model.fit(voltage[cycle_i],
                                           t=time[cycle_i])
            else:
                result_cycle = r_model.fit(voltage[cycle_i],
                                           params=best_para[cycle_i - 1],
                                           t=time[cycle_i])
            # result_cycle.conf_interval()
            result.append(result_cycle)
            copied_parameters = copy.deepcopy(result_cycle.params)
            best_para.append(copied_parameters)
            err_para = np.sqrt(np.diag(result_cycle.covar))
            error_para = {para_name: err_para[err]
                          for err, para_name in enumerate(r_model.param_names)}
            best_para_error.append(error_para)
            # calculating r and c from fit
            best_rc_cycle = {'r_%s' % key[3:]: abs(v_rc / i_start[cycle_i])
                             for key, v_rc in
                             best_para[cycle_i].valuesdict().items()
                             if key.startswith('v0')}
            best_c_cycle = {'c_%s' % key[4:]:
                            tau_rc / best_rc_cycle['r_%s' % key[4:]]
                            for key, tau_rc in
                            best_para[cycle_i].valuesdict().items()
                            if key.startswith('tau')}
            best_rc_cycle.update(best_c_cycle)
            best_rc_para.append(best_rc_cycle)

        """User decides which cycles to plot.
        -------------------------------------------------------------------------
        """
        if not user_cycles:
            # no cycles
            user_cycles_list = []

        elif user_cycles == 'a':
            # all cycles
            user_cycles_list = range(0, len(result))
        else:
            # specified cycles
            user_cycles_list = [int(usr) - 1 for usr in user_cycles.split()]
            # if any(user_cycles_list) not in range(len(result)) or len(
            #         user_cycles_list) > len(result):
            #     raise AttributeError(
            #         'You have asked for more plots than number of cycles or for a '
            #         'cycle that does not exist. Specify less than %i plots'
            #         % len(result))

        for cycle_nr in user_cycles_list:
            # fig = result[cycle_nr].plot()
            plt.figure()
            plt.suptitle('Measured and fitted voltage of cycle %i after %s' %
                         ((cycle_nr + 1), rlx_txt))
            plot_voltage(time[cycle_nr], voltage[cycle_nr],
                         result[cycle_nr])
            print 'Report for cycle %i. After %s' % (cycle_nr + 1, rlx_txt)
            report_fit(result[cycle_nr])
            print '------------------------------------------------------------'

        # sub plotting voltage
        ############################################################################
        # fig_up = plt.figure(figsize=(20, 13))
        # plt.suptitle('OCV-relaxation data from cell "sic006_cc_45_01" with best '
        #              'fitted and guessed parameters',
        #              size=20)
        #
        # # making odd or even amount of subfigures inside fig_up
        # if len(result) % 2 == 0:   # Even number of cycles
        #     gs = gridspec.GridSpec(len(result) / 2, 3)
        #     gs.update(left=0.1, right=0.6, wspace=0.1)
        #     subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]
        # else:
        #     gs = gridspec.GridSpec((len(result) + 1) / 2, 3)
        #     gs.update(left=0.05, right=0.8, wspace=0.8)
        #     subs_up = [fig_up.add_subplot(gs[j]) for j in range(len(result))]
        #
        # for cycle_nr, sub_up in enumerate(subs_up):
        #     plot_voltage(time[cycle_nr], voltage[cycle_nr], result[cycle_nr],
        #                  sub_up)
        """Plotting parameters
        ------------------------------------------------------------------------
        """
        # printing parameters
        # for cyc in range(1, len(result)):
        #     print 'cycle number %i' % cyc
        #     print_params(ini=best_para[cyc - 1], fit=best_para[cyc])
        #     print '--------------------------------------------------------'
        fig_params = plt.figure()
        plt.suptitle('Initial and fitted parameters in every cycle after %s'
                     % rlx_txt, size=20)
        cycle_array = np.arange(1, len(result) + 1, 1)
        cycle_array_ticks = np.arange(1, len(result) + 1, 3)

        if len(best_para[0]) % 2 == 0:   # Even number of cycles
            gs = gridspec.GridSpec(len(best_para[0]) / 2, 3)
            gs.update(left=0.05, right=0.9, wspace=1)
            subs_params = [fig_params.add_subplot(gs[p])
                           for p in range(len(best_para[0]))]
        else:
            gs = gridspec.GridSpec((len(best_para[0]) + 1) / 2, 3)
            gs.update(left=0.05, right=0.9, wspace=1)
            subs_params = [fig_params.add_subplot(gs[p])
                           for p in range(len(best_para[0]))]

        plt.setp(subs_params, xlabel='Cycle number', xticks=cycle_array_ticks)
        for _, name in enumerate(result[0].var_names):
            para_array = np.array([best_para[step][name]
                                   for step in range(len(result))])
            para_error = np.array([best_para_error[cycle_step][name]
                                   for cycle_step in range(len(result))])
            subs_params[_].errorbar(cycle_array, para_array, yerr=para_error,
                                    fmt='or')
            subs_params[_].legend([name], loc='center left',
                                  bbox_to_anchor=(1, 0.5))
            subs_params[_].set_xlabel('Cycles')
            if 'tau' in name:
                subs_params[_].set_ylabel('Time-constant (RC)[s]')
            else:
                subs_params[_].set_ylabel('Voltage [V]')

        """Plotting RC parameters
        ------------------------------------------------------------------------
        """
        fig_rc = plt.figure()
        fig_rc.suptitle('R and C for each rc-circuit in all cycles after %s'
                        % rlx_txt)
        n_para = len(best_rc_para[0])
        if n_para % 2 == 1:
            gs_rc = gridspec.GridSpec(n_para / 2 + 1, n_para / 2)
        else:
            gs_rc = gridspec.GridSpec(n_para / 2, n_para / 2)
        gs_rc.update(left=0.05, right=0.9, wspace=1)
        subs_rc = [fig_rc.add_subplot(gs_rc[pr])
                   for pr in range(len(best_rc_para[0].keys()))]
        plt.setp(subs_rc, xlabel='Cycle number', xticks=cycle_array_ticks)

        for idx, key_value in enumerate(best_rc_para[0].keys()):
            temp_array = np.array([best_rc_para[cyc][key_value]
                                   for cyc in range(len(best_rc_para))])
            subs_rc[idx].plot(cycle_array, temp_array, 'og')
            subs_rc[idx].legend([key_value], loc='center left',
                                bbox_to_anchor=(1, 0.5))
            if key_value.startswith('r'):
                subs_rc[idx].set_ylabel('Resistance [Ohm]')
            else:
                subs_rc[idx].set_ylabel('Capacitance [F]')


    v_start_down = 1.
    # i_start_ini_down = 0.000153628   # from cycle 1-3
    # i_start_after_down = 0.000305533   # from cycle 4-end
    # i_start_down = [i_start_ini_down for _down in range(3)]
    # for down_4 in range(len(data_down) - 3):
    #     i_start_down.append(i_start_after_down)
    #
    v_start_up = 0.01
    # i_start_ini_up = 0.0001526552   # from cycle 1-3
    # i_start_after_up = 0.0003045602   # from cycle 4-end
    # i_start_up = [i_start_ini_up for _up in range(3)]
    # for up_4 in range(len(data_up) - 3):
    #     i_start_up.append(i_start_after_up)

    cell_mass = 0.86   # [g]
    c_rate_3 = 0.05   # [1 / h]
    c_rate = 0.1
    cell_capacity = 3.579   # [mAh / g]
    i_start_ini = (cell_mass * c_rate_3 * cell_capacity) / 1000   # [A]
    i_start_after = (cell_mass * c_rate * cell_capacity) / 1000   # [A]
    i_start = [i_start_ini for _down in range(3)]
    for down_4 in range(len(data_down) - 3):
        i_start.append(i_start_after)
    pass
    # question_ex = 'Cycles after discharge you want to plot, separated with ' \
    #               'space. If you don'"'"'t want to plot any press ' \
    #               'enter. Write "a" for all plots: -->'
    # user_cycle_ex = raw_input(question_ex)
    # ex_ocv = pd.Series([pd.DataFrame(zip(t, u), columns=['time', 'voltage'])])
    # ocv_cycle(ex_ocv, user_cycle_ex, v_start_up, [0.0007508742])

    question_up = 'Cycles after discharge you want to plot, separated with ' \
                  'space. If you don'"'"'t want to plot any press ' \
                  'enter. Write "a" for all plots: -->'
    user_cycles_up = raw_input(question_up)
    ocv_cycle(data_up, user_cycles_up, v_start_up, i_start)
    plt.show()
    question_down = 'Cycles after charge you want to plot, separated with ' \
                    'space. If you don'"'"'t want to plot any press ' \
                    'enter. Write "a" for all plots: -->'
    user_cycles_down = raw_input(question_down)
    ocv_cycle(data_down, user_cycles_down, v_start_down, i_start)
    plt.show()

