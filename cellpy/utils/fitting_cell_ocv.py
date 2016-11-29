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

from lmfit import Parameters, report_fit, Model, report_ci
from cell_ocv import *
from matplotlib.ticker import MaxNLocator

# import StringIO
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import copy

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
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


def plot_voltage(t, v, best, subfigure, ms=10, ti_lb_s=35):
    """Making a plot with given voltage data.

    Args:
        t (nd.array): Points in time [s].
        v (nd.array): Measured voltage [V].
        best (ModelResult): All fitted data in lmfit object Model.
        subfigure (list): Subfigures with length 2
        ms (int): Markersize of plots.
        ti_lb_s (int): Ticks and labels size.

    Returns:
        None: Making a plot with matplotlib.pyplot

    """
    result_params = best.params
    measured_err = (1. / best.weights)
    result_residual = best.best_fit - v
    # result_residual = best.residual

    ext_t = np.arange(2 * t[-1])
    ocv = result_params['ocv'] * np.ones(len(ext_t))

    residual_figure = subfigure[0]
    result_figure = subfigure[1]

    residual_figure.errorbar(t, result_residual, yerr=measured_err,
                             label='Fit - Measured', linewidth=6,
                             elinewidth=0.2)
    result_figure.errorbar(t, v, yerr=measured_err, fmt='ob',
                           label='Measured', ms=ms+3)
    result_figure.plot(t, best.init_fit, '--k', label='Initial guess',
                       linewidth=ms)
    result_figure.plot(t, best.best_fit, '-r', label='Best fit', linewidth=ms)
    result_figure.plot(ext_t, ocv, '--c', label='ocv', linewidth=ms)

    residual_figure.set_ylabel('Residual (V)', size=ti_lb_s)
    residual_figure.legend(loc='best', prop={'size': ti_lb_s})
    residual_figure.set_xlabel('Time (s)', size=ti_lb_s)

    for tick_resi in residual_figure.xaxis.get_major_ticks():
        tick_resi.label.set_fontsize(ti_lb_s)
    for tick_resi in residual_figure.yaxis.get_major_ticks():
        tick_resi.label.set_fontsize(ti_lb_s)
    residual_figure.grid()

    result_figure.set_ylabel('Voltage (V)', size=ti_lb_s)
    result_figure.legend(loc='best', prop={'size': ti_lb_s})
    result_figure.set_xlim(-1, t[-1] + 300)

    for tick_res in result_figure.xaxis.get_major_ticks():
        tick_res.label.set_fontsize(ti_lb_s)
    for tick_res in result_figure.yaxis.get_major_ticks():
        tick_res.label.set_fontsize(ti_lb_s)

    result_figure.grid()

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


def plot_rc(t, best, ms=10, ti_lb_s=35):
    result_params = best.params
    tau_rc = {tau_key: tau_val for tau_key, tau_val in result_params.items()
              if tau_key.startswith('tau')}
    v0_rc = {v0_key: v0_val for v0_key, v0_val in result_params.items()
             if v0_key.startswith('v0')}

    rc_circuits = {rc[4:]: relaxation_rc(t, v0_rc['v0_%s' % rc[4:]], tau_rc[rc])
                   for rc in tau_rc.keys()}
    for rc_name, rc in rc_circuits.items():
        plt.plot(t, rc, label='%s rc-circuit' % rc_name, linewidth=ms)
    plt.legend(loc='best', prop={'size': ti_lb_s})
    plt.xlabel('Time (s)', size=ti_lb_s)
    plt.ylabel('Voltage(V)', size=ti_lb_s)
    plt.grid()


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
    ocv_arr = np.ones(len(t)) * params['ocv']
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

def define_model(filepath, filename, guess_tau, contribution, c_rate=0.05,
                 ideal_cap=3.579, mass=0.86, v_start=None):
    """Reading data, creating Model object from relax_model and set param_hints.

    Reading the .csv file with all the cycling data.
    The user may initialise the use of lmfit. If user does not know the
    parameters, some defaults are set. Filepath and filename has to be given.

    Removing "nan" is inspired by 'stackoverflow'_

    Args:
        filepath (str): The exact path to the folder where the data lies.
        filename (str): The ocv relaxation filename for up- or downwards relax.
        guess_tau (:obj: 'dict' of :obj: 'float'): User guessing what the time
        constant for each rc-circuit might be.
        contribution (:obj: 'dict' of :obj: 'float'): Assumed contribution
        from each rc-circuit. Help guessing the initial start voltage value
        of the rc-circuit.
        c_rate (float): C-rate of discharge or charge.
        ideal_cap (float): Theoretical capacity of the cell.
        mass (float): Mass of the active material. Given in [mg].
        v_start (float): Cut-off voltage (before IR-drop).

    Returns:
        :obj: 'Model' of :obj: 'relax_model', :obj: 'list' of :obj:
        'nd.array', :obj: 'list' of :obj: 'nd.array': Model of relax_model
        with it's guessed parameters as hints. One list of time, and one of
        voltage, both with len equal to number of cycles. Each element in
        list represent number of cycle - 1.

    .._stackoverflow:
        http://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array

    """
    try:
        r_filepath = r'%s' % filepath
        r_filename = r'%s' % filename
        data_write = os.path.join(r_filepath, r_filename)
        data_read = pd.read_csv(data_write, sep=';')
        data = manipulate_data(data_read)
    except ImportError:
        print "Folder- or filename not found."
        raise
    if not guess_tau:
        guess_tau = {'d': 500, 'ct': 50}
    if not contribution:
        contribution = {'d': 0.8, 'ct': 0.2}

    if not (isinstance(guess_tau, dict) or isinstance(contribution, dict)):
        raise TypeError('guess_tau and contribution has to be dictionaries.')
    if sum(contribution.values()) != 1:
        raise ValueError('The sum of contribution values has to sum up to 1.')
    if len(guess_tau) != len(contribution):
        raise AttributeError('len(guess_tau) has to be equal to len('
                             'contribution).')
    for key_name in guess_tau.keys():
        if key_name not in contribution.keys():
            raise AttributeError('guess_tau and contribution need to have same '
                                 'rc-names. That is, both need to have the '
                                 'same keyword arguments.')

    # Extracting time and voltage from data.
    time = []
    voltage = []
    for i, sort in data.iteritems():
        sort_t = np.array(sort[:]['time'])
        sort_v = np.array(sort[:]['voltage'])
        sort_t = sort_t[~np.isnan(sort_t)]
        sort_v = sort_v[~np.isnan(sort_v)]
        sort_time = np.sort(sort_t)
        # checking if relaxation down or up
        if sort_v[-1] > sort_v[0]:
            sort_volt = np.sort(sort_v)
        else:
            sort_volt = np.sort(sort_v)
            sort_volt[:] = sort_volt[::-1]
        time.append(sort_time)
        voltage.append(sort_volt)
    v_ocv = voltage[0][-1]
    v_0 = voltage[0][0]

    i_start = (c_rate * ideal_cap * mass) / 1000
    if v_ocv < v_0:
        # After charge
        if not v_start:
            v_start = 1.
    else:
        # After discharge
        if not v_start:
            v_start = 0.01

    init_guess = guessing_parameters(v_start, i_start, v_0, v_ocv, contribution,
                                     guess_tau)

    r_model = Model(relax_model, missing='raise')

    for name in guess_tau.keys():
        r_model.set_param_hint('tau_%s' % name, value=guess_tau[name], min=0)

        if v_ocv < v_0:
            # After charge (relax downwards)
            r_model.set_param_hint('v0_%s' % name,
                                   value=init_guess['v0_rc'][name], min=0)
        else:
            r_model.set_param_hint('v0_%s' % name,
                                   value=init_guess['v0_rc'][name], max=0)
    r_model.set_param_hint('ocv', value=v_ocv)
    r_model.make_params()
    print "Initial parameter hints are based on first cycle"
    r_model.print_param_hints()
    print "To define more boundaries: >>> " \
          "example_model.set_param_hint('name_of_parameter', min=min_value, " \
          "max=max_value)"
    return r_model, time, voltage


def fit_with_model(model, time, voltage, guess_tau, contribution, c_rate,
                   change_i, ideal_cap=3.579, mass=0.86, v_start=None,
                   v_err=0.01):
    """Fitting measured data to model.

    Args:
        model (Model): The cell model.
        time (:obj: 'list' of :obj: 'nd.array'): Element in list equals the time
        of cycle number - 1.
        voltage (:obj: 'list' of :obj: 'nd.array'): Element in list equals
        the voltage of cycle number - 1.
        guess_tau (:obj: 'dict' of :obj: 'float'): User guessing what the time
        constant for each rc-circuit might be.
        contribution (:obj: 'dict' of :obj: 'float'): Assumed contribution
        from each rc-circuit. Help guessing the initial start voltage value
        of the rc-circuit.
        c_rate (:obj: 'list' of :obj: 'float'): The C-rate which the cell was
        discharged or charged with before cycle = change_i.
        change_i (:obj: 'list' of :obj: 'int'): The cycle number where the
        C-rate (AKA Current) is changed. len(c_rate) = len(change_i) + 1
        ideal_cap (float): Theoretical capacity of the cell.
        mass (float): Mass of the active material. Given in [mg].
        v_err (float): Voltage measurement accuracy in V. Default: Arbin BT2000.
        v_start (float): Cut-off voltage (potential before IR-drop).

    Returns:
        :obj: 'list' of :obj: 'ModelResult', :obj: 'list' of :obj:
        'dict': Results of fitting from each cycle in a list with and
        calculated R and C parameters based on fit from result.
    """
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

    # making a class Minimizer that contain fitting methods and attributes
    # Mini_initial_up = Minimizer(ocv_user_adjust, params=initial_param_up,
    #                             fcn_args=(time[0], voltage[0]),)
    # minimize() perform the minimization on Minimizer's attributes
    # result = [Mini_initial_up.minimize()]
    # Creating an lmfit Model object out of function "relax_model".
    i_start = []
    step = 0
    for i in range(len(time)):
        # Checking if cycle number i is in change_i
        if i in change_i:
            step += 1
        i_start.append((c_rate[step] * ideal_cap * mass) / 1000)
    if not guess_tau:
        guess_tau = {'d': 500, 'ct': 50}
    if not contribution:
        contribution = {'d': 0.8, 'ct': 0.2}

    if not (isinstance(guess_tau, dict) or isinstance(contribution, dict)):
        raise TypeError('guess_tau and contribution has to be dictionaries.')
    if not(isinstance(c_rate, list) or isinstance(change_i, list)):
        raise TypeError('c_rate and change_i has to be tuples.')

    if len(c_rate) != len(change_i) + 1:
        raise AttributeError('len(c_rate) must be equal to len(change_i) + 1')

    if sum(contribution.values()) != 1:
        raise ValueError('The sum of contribution values has to sum up to 1.')

    if len(guess_tau) != len(contribution):
        raise AttributeError('len(guess_tau) has to be equal to len('
                             'contribution).')
    for key_name in guess_tau.keys():
        if key_name not in contribution.keys():
            raise AttributeError('guess_tau and contribution need to have '
                                 'same rc-names. That is, both need to have '
                                 'the same keyword arguments.')

    result_initial = model.fit(voltage[0], t=time[0], weights=1./v_err)
    # result_initial.conf_interval()
    result = [result_initial]

    best_para = [result[0].params]
    r_ir_0 = abs(voltage[0][0] - v_start) / i_start[0]
    r_ir = {'IR': r_ir_0}

    best_rc_ini = {'r_%s' % key[3:]: abs(v0_rc / i_start[0])
                   for key, v0_rc in best_para[0].valuesdict().items()
                   if key.startswith('v0')}

    best_c_ini = {'c_%s' % key[4:]: tau_rc / best_rc_ini['r_%s' % key[4:]]
                  for key, tau_rc in best_para[0].valuesdict().items()
                  if key.startswith('tau')}
    best_rc_ini.update(best_c_ini)
    best_rc_ini.update(r_ir)
    best_rc_para = [best_rc_ini]

    for cycle_i in range(1, len(time)):
        temp_start_voltage = voltage[cycle_i][0]
        temp_end_voltage = voltage[cycle_i][-1]
        # Guessing new values when current has changed.
        if i_start[cycle_i] is not i_start[cycle_i - 1]:
            temp_initial_guess = guessing_parameters(v_start,
                                                     i_start[cycle_i],
                                                     temp_start_voltage,
                                                     temp_end_voltage,
                                                     contribution, guess_tau)
            for name in guess_tau.keys():
                model.set_param_hint('tau_%s' % name, value=guess_tau[name])
                if temp_end_voltage < temp_start_voltage:
                    # After charge (relax downwards)
                    model.set_param_hint('v0_%s' % name,
                                         value=temp_initial_guess[
                                             'v0_rc'][name], min=0)
                else:
                    model.set_param_hint('v0_%s' % name,
                                         value=temp_initial_guess[
                                             'v0_rc'][name], max=0)
            model.set_param_hint('ocv', value=temp_end_voltage)
            model.make_params()
            result_cycle = model.fit(voltage[cycle_i], t=time[cycle_i],
                                     weights=1. / v_err)
        else:
            result_cycle = model.fit(voltage[cycle_i],
                                     params=best_para[cycle_i - 1],
                                     t=time[cycle_i], weights=1. / v_err)
        # result_cycle.conf_interval()
        result.append(result_cycle)
        copied_parameters = copy.deepcopy(result_cycle.params)
        best_para.append(copied_parameters)

        # calculating r and c from fit
        r_ir_temp = abs(temp_start_voltage - v_start) / i_start[cycle_i]
        best_rc_cycle = {'r_%s' % key[3:]:
                         abs(v_rc / i_start[cycle_i])
                         for key, v_rc in
                         best_para[cycle_i].valuesdict().items()
                         if key.startswith('v0')}
        best_c_cycle = {'c_%s' % key[4:]:
                        tau_rc / best_rc_cycle['r_%s' % key[4:]]
                        for key, tau_rc in
                        best_para[cycle_i].valuesdict().items()
                        if key.startswith('tau')}
        best_rc_cycle.update({'IR': r_ir_temp})
        best_rc_cycle.update(best_c_cycle)
        best_rc_para.append(best_rc_cycle)
    return result, best_rc_para, i_start


def fit_with_conf(model, time, voltage, guess_tau, contribution, c_rate,
                  change_i, ideal_cap=3.579, mass=0.86, v_start=None,
                  v_err=0.002):
    """Fitting measured data to model with more than one decay exponential func.

    First using the more robust Nelder-Mead Method to calculate the
    parameters, then use Levenberg-Marquardt using nelder solution as initial.
    This will help generate a confidential interval that will check if the
    unceratinty is good or not.

    Args:
        model (Model): The cell model.
        time (:obj: 'list' of :obj: 'nd.array'): Element in list equals the time
        of cycle number - 1.
        voltage (:obj: 'list' of :obj: 'nd.array'): Element in list equals
        the voltage of cycle number - 1.
        guess_tau (:obj: 'dict' of :obj: 'float'): User guessing what the time
        constant for each rc-circuit might be.
        contribution (:obj: 'dict' of :obj: 'float'): Assumed contribution
        from each rc-circuit. Help guessing the initial start voltage value
        of the rc-circuit.
        c_rate (:obj: 'list' of :obj: 'float'): The C-rate which the cell was
        discharged or charged with before cycle = change_i.
        change_i (:obj: 'list' of :obj: 'int'): The cycle number where the
        C-rate (AKA Current) is changed. len(c_rate) = len(change_i) + 1
        ideal_cap (float): Theoretical capacity of the cell.
        mass (float): Mass of the active material. Given in [mg].
        v_err (float): Voltage measurement accuracy in %. Default: Arbin BT2000.
        v_start (float): Cut-off voltage (potential before IR-drop).

    Returns:
        :obj: 'list' of :obj: 'ModelResult', :obj: 'list' of :obj:
        'dict': Results of fitting from each cycle in a list with and
        calculated R and C parameters based on fit from result.
    """
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

    # making a class Minimizer that contain fitting methods and attributes
    # Mini_initial_up = Minimizer(ocv_user_adjust, params=initial_param_up,
    #                             fcn_args=(time[0], voltage[0]),)
    # minimize() perform the minimization on Minimizer's attributes
    # result = [Mini_initial_up.minimize()]
    # Creating an lmfit Model object out of function "relax_model".
    i_start = []
    step = 0
    for i in range(len(time)):
        # Checking if cycle number i is in change_i
        if i in change_i:
            step += 1
        i_start.append((c_rate[step] * ideal_cap * mass) / 1000)
    if not guess_tau:
        guess_tau = {'d': 500, 'ct': 50}
    if not contribution:
        contribution = {'d': 0.8, 'ct': 0.2}

    if not (isinstance(guess_tau, dict) or isinstance(contribution, dict)):
        raise TypeError('guess_tau and contribution has to be dictionaries.')
    if not(isinstance(c_rate, list) or isinstance(change_i, list)):
        raise TypeError('c_rate and change_i has to be tuples.')

    if len(c_rate) != len(change_i) + 1:
        raise AttributeError('len(c_rate) must be equal to len(change_i) + 1')

    if sum(contribution.values()) != 1:
        raise ValueError('The sum of contribution values has to sum up to 1.')

    if len(guess_tau) != len(contribution):
        raise AttributeError('len(guess_tau) has to be equal to len('
                             'contribution).')
    for key_name in guess_tau.keys():
        if key_name not in contribution.keys():
            raise AttributeError('guess_tau and contribution need to have '
                                 'same rc-names. That is, both need to have '
                                 'the same keyword arguments.')

    result_initial_nelder = model.fit(voltage[0], t=time[0],
                                      weights=1./v_err, method='Nelder')

    result_initial = model.fit(voltage[0], t=time[0], weights=1./(v_err),
                               params=result_initial_nelder.params,
                               method='leastsq')
    result_initial.conf_interval(trace=True)
    result = [result_initial]
    best_para = [result[0].params]

    r_ir_0 = abs(voltage[0][0] - v_start) / i_start[0]
    r_ir = {'IR': r_ir_0}
    best_rc_ini = {'r_%s' % key[3:]: abs(v0_rc / i_start[0])
                   for key, v0_rc in best_para[0].valuesdict().items()
                   if key.startswith('v0')}

    best_c_ini = {'c_%s' % key[4:]: tau_rc / best_rc_ini['r_%s' % key[4:]]
                  for key, tau_rc in best_para[0].valuesdict().items()
                  if key.startswith('tau')}
    best_rc_ini.update(r_ir)
    best_rc_ini.update(best_c_ini)
    best_rc_para = [best_rc_ini]

    for cycle_i in range(1, len(time)):
        temp_start_voltage = voltage[cycle_i][0]
        temp_end_voltage = voltage[cycle_i][-1]
        # Guessing new values when current has changed.
        if i_start[cycle_i] is not i_start[cycle_i - 1]:
            temp_initial_guess = guessing_parameters(v_start,
                                                     i_start[cycle_i],
                                                     temp_start_voltage,
                                                     temp_end_voltage,
                                                     contribution, guess_tau)
            for name in guess_tau.keys():
                model.set_param_hint('tau_%s' % name, value=guess_tau[name])
                if temp_end_voltage < temp_start_voltage:
                    # After charge (relax downwards)
                    model.set_param_hint('v0_%s' % name,
                                         value=temp_initial_guess[
                                             'v0_rc'][name], min=0)
                else:
                    model.set_param_hint('v0_%s' % name,
                                         value=temp_initial_guess[
                                             'v0_rc'][name], max=0)
            model.set_param_hint('ocv', value=temp_end_voltage)
            model.make_params()
            result_cycle_nelder = model.fit(voltage[cycle_i], t=time[cycle_i],
                                            weights=1. / (v_err),
                                            method='Nelder')
            result_cycle = model.fit(voltage[cycle_i], t=time[cycle_i],
                                            weights=1. / (v_err),
                                     params=result_cycle_nelder.params,
                                     method='leastsq')
        else:
            result_cycle_nelder = model.fit(voltage[cycle_i],
                                            params=best_para[cycle_i - 1],
                                            t=time[cycle_i],
                                            weights=1. / (v_err),
                                            method='Nelder')
            result_cycle = model.fit(voltage[cycle_i],
                                     params=result_cycle_nelder.params,
                                     t=time[cycle_i],
                                     weights=1. / (v_err),
                                     method='leastsq')

        result_cycle.conf_interval(trace=True)
        result.append(result_cycle)
        copied_parameters = copy.deepcopy(result_cycle.params)
        best_para.append(copied_parameters)
        # calculating r and c from fit
        r_ir_temp = abs(temp_start_voltage - v_start) / i_start[cycle_i]
        best_rc_cycle = {'r_%s' % key[3:]:
                         abs(v_rc / i_start[cycle_i])
                         for key, v_rc in
                         best_para[cycle_i].valuesdict().items()
                         if key.startswith('v0')}
        best_c_cycle = {'c_%s' % key[4:]:
                        tau_rc / best_rc_cycle['r_%s' % key[4:]]
                        for key, tau_rc in
                        best_para[cycle_i].valuesdict().items()
                        if key.startswith('tau')}
        best_rc_cycle.update({'IR': r_ir_temp})
        best_rc_cycle.update(best_c_cycle)
        best_rc_para.append(best_rc_cycle)
    return result, best_rc_para, i_start


def user_plot_voltage(time, voltage, fit, conf, name=None, ms=10, ti_la_s=35,
                      tit_s=45):
    """User decides which cycles to plot and report.

    Args:
        time (:obj: 'list of :obj: 'nd.array'): Points in time for all cycles.
        voltage (:obj: 'list' of :obj: 'nd.array'): Cycles' relaxation voltage.
        fit (:obj: 'list' of :obj: 'ModelResult'): All cycles' best fit results.
        conf (bool): conf_int calculated if True --> amount of rc-ciruits > 1.
        name (str): Name of cell (used in title of plots).
        ms (int): Markersize for plots.
        ti_la_s (int): Ticks and labels font size.
        tit_s (int): Title size of plot.


    Returns:
        None: Plotted figures and reports of requested cycle numbers
    """
    name = 'not specified' if not name else name
    question = "Write the cycles you want to plot separated with space." \
               "If you don't want to plot anything else than the fit " \
               "reports, press enter. " \
               "Write 'a' for all plots: -->"
    user_cycles = raw_input(question)
    if not user_cycles:
        # no cycles
        user_cycles_list = []

    elif user_cycles == 'a':
        # all cycles
        user_cycles_list = range(0, len(fit))

    else:
        # specified cycles
        user_cycles_list = [int(usr) - 1 for usr in user_cycles.split()]
        # if any(user_cycles_list) not in range(len(result)) or len(
        #         user_cycles_list) > len(result):
        #     raise AttributeError(
        #         'You have asked for more plots than number of cycles or for a '
        #         'cycle that does not exist. Specify less than %i plots'
        #         % len(result))

    v_ocv = voltage[0][-1]
    v_0 = voltage[0][0]
    if v_ocv < v_0:
        # After charge
        rlx_txt = "after delithiation"
    else:
        # After discharge
        rlx_txt = "after lithiation"

    if not user_cycles_list:
        for cycle_nr in range(len(fit)):
            print 'Report for cell %s (%s), Cycle %i'\
                  % (name, rlx_txt, (cycle_nr + 1))
            report_fit(fit[cycle_nr])
            if conf > 1:
                report_ci(fit[cycle_nr].ci_out[0])
            print '------------------------------------------------------------'
    else:
        for cycle_nr in user_cycles_list:
            # fig_fit = fit[cycle_nr].plot()
            rc_fig = plt.figure()
            rc_fig.canvas.set_window_title('cycle_%i_bec08_rc_'
                                           % (cycle_nr + 1))
            rc_fig.suptitle('Fitted RC-circuits for cell %s (%s), cycle %i'
                            % (name, rlx_txt, (cycle_nr + 1)), size=tit_s)
            for tick_rc in plt.gca().xaxis.get_major_ticks():
                tick_rc.label.set_fontsize(ti_la_s)
            for tick_rc in plt.gca().yaxis.get_major_ticks():
                tick_rc.label.set_fontsize(ti_la_s)
            plt.gca().title.set_position([.5, 1.05])
            plot_rc(time[cycle_nr], fit[cycle_nr], ms=ms+3, ti_lb_s=ti_la_s)

            plt.figure()
            plt.gca().title.set_position([.5, 1.05])
            gs = gridspec.GridSpec(3, 1)
            gs.update(hspace=0.5)
            ax1 = plt.subplot(gs[-1, 0])
            ax2 = plt.subplot(gs[0:-1, 0], sharex=ax1)
            sub_fig = [ax1, ax2]
            plt.suptitle('Voltage with fit for cell %s (%s), cycle %i'
                         % (name, rlx_txt, (cycle_nr + 1)), size=tit_s)
            plot_voltage(time[cycle_nr], voltage[cycle_nr], fit[cycle_nr],
                         sub_fig, ms=ms, ti_lb_s=ti_la_s)
            plt.gcf().canvas.set_window_title('cycle_%i_bec08_'
                                              % (cycle_nr + 1))

            print 'Report for cell %s (%s), Cycle %i'\
                  % (name, rlx_txt, (cycle_nr + 1))
            report_fit(fit[cycle_nr])
            if conf:
                #     trace = fit[cycle_nr].ci_out[1]
                # ocv_taud, tau_d_ocv, prob_ocv = trace['ocv']['ocv'], \
                #                                 trace['ocv']['tau_d'],\
                #                                 trace['ocv']['prob']
                # plt.scatter(ocv_taud, tau_d_ocv, c=prob_ocv, s=30)
                # plt.xlabel('ocv')
                # plt.ylabel('tau d')

                report_ci(fit[cycle_nr].ci_out[0])
            print '------------------------------------------------------------'


def plot_params(voltage, fit, rc_params, i_start, cell_name, mass_frac_error,
                fig_folder, i_err=0.000000125, ms=10, ti_la_s=35, tit_s=45,
                tx=5, ty=5, single=False, outfolder=None):
    """Calculating parameter errors and plotting them.

    r is found by calculating v0 / i_start --> err(r)= err(v0) + err(i_start).
    c is found from using tau / r --> err(c) = err(r) + err(tau)
    Here err means fractional uncertainty, which means that the uncertainty
    of both r and c are respectively e(r) = err(r) / r and e(c) = err(c) / c.

    Args:
        voltage (:obj: 'list' of :obj: 'nd.array'): Measured voltage.
        fit (:obj: 'list' of :obj: 'ModelResult'): Best fit for each cycle.
        rc_params (:obj: 'list' of :obj: 'dict'): Calculated R and C from fit.
        i_start (list): Discharge current. Used to calculate frac error of I.
        cell_name (str): Name of the cell.
        mass_frac_error (float): Fractional uncertainty of mass measurments.
        fig_folder (str): Which folder the plots should be saved in.
        i_err (float): Current measurement error in A. Standard is Arbin BT2000.
        ms (int): Markersize for plots.
        ti_la_s (int): Ticks and labels font size.
        tit_s (int): Title size of plot.
        tx(int): Number of ticks on x axis.
        ty(int): Number of ticks on y axis.
        single (bool): Plot single plots or not.
        outfolder (str): Folder where to save .csv files.

    Returns:
        None: Plot the parameters with their errors.
    """
    v_ocv = voltage[0][-1]
    v_0 = voltage[0][0]
    if v_ocv < v_0:
        # After charge
        rlx_txt = "delithiation"
    else:
        # After discharge
        rlx_txt = "lithiation"

    best_para = []
    best_para_error = []
    names = fit[0].params.keys()
    for i, cycle_fit in enumerate(fit):
        v_err_cycle = 1. / cycle_fit.weights
        i_err_frac = i_err / i_start[i] + mass_frac_error
        error_para = {para_name: cycle_fit.params[para_name].stderr
                      for para_name in names}
        # err_para = np.sqrt(np.diag(cycle_fit.covar))
        # error_para = {para_name: err_para[err]
        #               for err, para_name in enumerate(names)}
        # Fractional error in percent calculation
        fractional_err = {par_name: (error_para[par_name] /
                                     cycle_fit.params[par_name])
                          for par_name in names}
        r_err = {key: fractional_err['v0_%s' % key[2:]] + i_err_frac
                 for key in rc_params[i].keys() if key.startswith('r_')}
        c_err = {key: fractional_err['tau_%s' % key[2:]] + r_err['r_%s' %
                                                                 key[2:]]
                 for key in rc_params[i].keys() if key.startswith('c_')}
        # ir = (v_start - v_rlx) / i_start
        ir_err = i_err_frac + v_err_cycle

        # Standard deviation error calculated from fractional error
        e_r = {r: frac_err * rc_params[i][r]
               for r, frac_err in r_err.items()}
        e_c = {c: frac_err * rc_params[i][c]
               for c, frac_err in c_err.items()}
        e_ir = {'IR': rc_params[i]['IR'] * ir_err}
        error_para.update(e_r)
        error_para.update(e_c)
        error_para.update(e_ir)
        best_para_error.append(error_para)
        temp_dict = cycle_fit.params.valuesdict()
        rc_params[i].update(temp_dict)
        best_para.append(rc_params[i])

    fig_params = plt.figure(figsize=(85, 70))
    plt.suptitle('Fitted parameters vs. cycles for cell %s (after %s)'
                 % (cell_name, rlx_txt), size=tit_s)
    cycle_array = np.arange(1, len(fit) + 1, 1)
    # cycle_array_ticks = np.arange(1, len(fit) + 1, 4)

    shape_params = len(best_para[0]) - len(fit[0].params)
    if shape_params % 2 == 0:   # Even number of input params
        gs = gridspec.GridSpec(shape_params / 2 + 1, shape_params - 1)
        gs.update(left=0.07, right=0.95, wspace=0.5)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para[0]))]
    else:
        gs = gridspec.GridSpec((shape_params + 1) / 2, shape_params - 1)
        gs.update(left=0.05, right=0.95, wspace=0.5)
        subs_params = [fig_params.add_subplot(gs[p])
                       for p in range(len(best_para[0]))]
    plt.setp(subs_params, xlabel='Cycle number')

    plt.gcf().canvas.set_window_title('param_all_cycles_sic006_74_delith')

    para_df = {}
    for name_i, name in enumerate(best_para[0].keys()):
        para_array = np.array([best_para[step][name]
                               for step in range(len(fit))])
        para_error = np.array([best_para_error[cycle_step][name]
                               for cycle_step in range(len(fit))])
        para_df.update({name: para_array})
        para_df.update({name + '_err': para_error})

        subs_params[name_i].errorbar(cycle_array, para_array, yerr=para_error,
                                     fmt='or', ms=ms, elinewidth=3)
        subs_params[name_i].legend([name], loc='best', prop={'size': ti_la_s})
        subs_params[name_i].set_xlabel('Cycles', size=ti_la_s)
        for tick_para in subs_params[name_i].xaxis.get_major_ticks():
            tick_para.label.set_fontsize(ti_la_s)
        for tick_para in subs_params[name_i].yaxis.get_major_ticks():
            tick_para.label.set_fontsize(ti_la_s)
        subs_params[name_i].yaxis.set_major_locator(MaxNLocator(ty))
        subs_params[name_i].xaxis.set_major_locator(MaxNLocator(tx))

        # min_para = np.min(para_array)
        # max_para = np.max(para_array)
        # donemin = False
        # donemax = False
        # for y in para_array:
        #     if donemin and donemax:
        #         break
        #     if y not in (min_para, max_para):
        #         if min_para * 10 ** -4 > y and not donemin:
        #             min_para = y
        #             donemin = True
        #         elif max_para * 10 ** -3 > y and not donemax:
        #             max_para = y
        #             donemax = True
        # print min_para, max_para
        # subs_params[name_i].set_ylim(min_para - 0.1 * min_para,
        #                              max_para + 0.1 * max_para)

        if 'tau' in name:
            subs_params[name_i].set_ylabel('Time-constant (RC)[s]',
                                           size=ti_la_s)
        elif 'r_' in name or 'IR' in name:
            subs_params[name_i].set_ylabel('Resistance [Ohm]', size=ti_la_s)
        elif 'c_' in name:
            subs_params[name_i].set_ylabel('Capacitance [F]', size=ti_la_s)
        else:
            subs_params[name_i].set_ylabel('Voltage [V]', size=ti_la_s)
        if v_ocv < v_0:
            plt.savefig(os.path.join(fig_folder, 'params_%s_delith.pdf'
                                     % cell_name),
                        bbox_inches='tight', pad_inches=3, dpi=100)
        else:
            plt.savefig(os.path.join(fig_folder, 'params_%s_lith.pdf'
                                     % cell_name),
                        bbox_inches='tight', pad_inches=3, dpi=100)

        if single:
            plt.figure(figsize=(50, 52))
            plt.suptitle('Fitted parameter %s vs. cycles for cell %s (after %s)'
                         % (name, cell_name, rlx_txt), size=tit_s)
            plt.errorbar(cycle_array, para_array, yerr=para_error, fmt='or',
                         ms=ms, elinewidth=3)
            plt.legend([name], loc='best', prop={'size': ti_la_s + 20})
            plt.xlabel('Cycles', size=ti_la_s)
            for tick_para in plt.gca().xaxis.get_major_ticks():
                tick_para.label.set_fontsize(ti_la_s)
            for tick_para in plt.gca().yaxis.get_major_ticks():
                tick_para.label.set_fontsize(ti_la_s)
            plt.gca().yaxis.set_major_locator(MaxNLocator(ty))
            plt.gca().xaxis.set_major_locator(MaxNLocator(tx))

            # min_para = np.min(para_array)
            # max_para = np.max(para_array)
            # donemin = False
            # donemax = False
            # for y in para_array:
            #     if donemin and donemax:
            #         break
            #     if y not in (min_para, max_para):
            #         if min_para * 10 ** -4 > y and not donemin:
            #             min_para = y
            #             donemin = True
            #         elif max_para * 10 ** -3 > y and not donemax:
            #             max_para = y
            #             donemax = True
            # print min_para, max_para
            # subs_params[name_i].set_ylim(min_para - 0.1 * min_para,
            #                              max_para + 0.1 * max_para)

            if 'tau' in name:
                plt.ylabel('Time-constant (RC)[s]', size=ti_la_s)
            elif 'r_' in name or 'IR' in name:
                plt.ylabel('Resistance [Ohm]', size=ti_la_s)
            elif 'c_' in name:
                plt.ylabel('Capacitance [F]', size=ti_la_s)
            else:
                plt.ylabel('Voltage [V]', size=ti_la_s)
            if v_ocv < v_0:
                plt.savefig(os.path.join(fig_folder, '%s_params_%s_delith.pdf'
                                         % (name, cell_name)),
                            bbox_inches='tight', pad_inches=3, dpi=100)
            else:
                plt.savefig(os.path.join(fig_folder, '%s_params_%s_lith.pdf'
                                         % (name, cell_name)),
                            bbox_inches='tight', pad_inches=3, dpi=100)
    if outfolder is not None:
        df = pd.DataFrame(para_df)
        df.to_csv(os.path.join(outfolder, 'rc_params_cell_%s.csv' %
                               cell_name), sep=';')
        print 'saved rc-parameters in csv file to folder %s with ";" as ' \
              'separator' % outfolder


def print_params(fit, rc_params, i_start, mass_frac_error, i_err=0.000000125):
    best_para = []
    best_para_error = []
    names = fit[0].params.keys()
    for i, cycle_fit in enumerate(fit):
        v_err_cycle = 1. / cycle_fit.weights
        i_err_frac = i_err / i_start[i] + mass_frac_error
        best_para.append(rc_params[i])
        error_para = {para_name: cycle_fit.params[para_name].stderr
                      for para_name in names}
        # err_para = np.sqrt(np.diag(cycle_fit.covar))
        # error_para = {para_name: err_para[err]
        #               for err, para_name in enumerate(names)}
        # Fractional error in percent calculation
        fractional_err = {par_name: (error_para[par_name] /
                                     cycle_fit.params[par_name])
                          for par_name in names}

        r_err = {key: fractional_err['v0_%s' % key[2:]] + i_err_frac
                 for key in rc_params[i].keys() if key.startswith('r_')}
        c_err = {key: fractional_err['tau_%s' % key[2:]] + r_err['r_%s' %
                                                                 key[2:]]
                 for key in rc_params[i].keys() if key.startswith('c_')}
        # ir = (v_start - v_rlx) / i_start
        ir_err = i_err_frac + v_err_cycle
        fractional_err.update(r_err)
        fractional_err.update(c_err)
        # Standard deviation error calculated from fractional error
        e_r = {r: frac_err * rc_params[i][r] / 100
               for r, frac_err in r_err.items()}
        e_c = {c: frac_err * rc_params[i][c] / 100
               for c, frac_err in c_err.items()}
        e_ir = {'IR': rc_params[i]['IR'] * ir_err}
        error_para.update(e_ir)
        error_para.update(e_r)
        error_para.update(e_c)
        best_para_error.append(error_para)
        temp_dict = cycle_fit.params.valuesdict()
        rc_params[i].update(temp_dict)
        print "============================================================"
        print "Cycle number %i" % (i + 1)
        for key_name, par_val in rc_params[i].items():
            if 'c_' in key_name:
                unit_text = 'F'
            elif 'tau_' in key_name:
                unit_text = 's'
            elif 'r_' in key_name or 'IR' in key_name:
                unit_text = 'Ohms'
            else:
                unit_text = 'V'
            if par_val > 10:
                print "Best parameter: \t %s \t %10.0f %s \t +/- %6.0f %s \t" \
                      "(%3.1f%%)" % (key_name, par_val, unit_text,
                                     error_para[key_name], unit_text,
                                     fractional_err[key_name])
            elif 10 > par_val > 1:
                print "Best parameter: \t %s \t %10.1f %s  \t +/- %6.1e %s \t " \
                      "(%3.1f%%)" % (key_name, par_val, unit_text,
                                     error_para[key_name], unit_text,
                                     fractional_err[key_name])
            else:
                print "Best parameter: \t %s \t %10.3f %s \t +/- %6.2e %s \t" \
                      "(%3.1f%%)" % (key_name, par_val, unit_text,
                                     error_para[key_name], unit_text,
                                     fractional_err[key_name])

