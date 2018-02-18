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

    return v0 * np.exp(-time/tau_rc)


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

    volt_rc = [relaxation_rc(time, v0_rc[rc], tau_rc[rc])
               for rc in list(tau_rc.keys())]
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
        v0_rc = {list(contribute.keys())[0]: v_rlx}
    else:
        v0_rc = {rc: v_rlx * rc_contri for rc, rc_contri in list(contribute.items())}
    v_ir = v_start - v_0

    # r_ir = abs(v_start / i_start - sum(r_rc.values()))
    r_ir = old_div(v_ir, i_start)   # This one is different than r_ir...?
    r_rc = {key: old_div(v0, i_start) for key, v0 in list(v0_rc.items())}
    c_rc = {k: old_div(t, r) for k, r in list(r_rc.items()) for i, t in list(tau_rc.items())
            if i == k}
    return\
        {'r_rc': r_rc, 'r_ir': r_ir, 'c_rc': c_rc, 'v0_rc': v0_rc}
