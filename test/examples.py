# -*- coding: utf-8 -*-

"""
This file is made for doing examples. The examples are just to see how the
equation look in a plot, so that it's easier to evaluate.
"""

import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def tau_calc(c, r):
    """
    Calculates the time constant tau = r*c
    :param c: capacity [F]
    :param r: resistance [ohm]
    :return: time constant [s]
    """
    return r*c

def RC_circuit(tau, t):
    """
    Giving ocv voltage from the charge-transfer process.
    :param tau: time constant of the contributing RC-circuit [s]
    :param t: time of measurement [s]
    :return: voltage contributed from the RC-circuit [V]
    """
    return math.exp(-t/tau)


def RC_relax(v_co, rc_circuits):
    """
    Add up all voltages during ocv on the cell.
    :param v_co: cut-off voltage (initial value)[V]
    :param rc_circuits: Voltages contributing to the ocv cell-circuit [V]
    :type rc_circuits: list
    :param t: time of measurement[s]
    :return: ocv voltage at given time, t [V]
    """
    sum_rc_circuits = sum(rc_circuits)
    return v_co*sum_rc_circuits


if __name__ == "__main__":
    """
    ======Variables======
    Variables are based on results from "fitting_ocv_003.py" by JPM
    :param c_d: diffusion capacity [F]
    :param c_ct: charge-transfer capacity [F]
    :param r_d: diffusion resistance [ohm]
    :param r_ct: charge-transfer capacity [ohm]
    :param v_co: cut-off voltage (assuming initial value) [V]
    v_co is actually not initial value in this case because the of ohmic
    resistance, r_0, isn't incorporated in this example. r_0 will make the v_co
    jump almost instant to a higher value. In real applications, r_0 need to be
    properly incorporated in ocv voltage. It's basically just to add a voltage
    v_0 that will add to the final ocv voltage.
    """

    c_d = 20       # guessing 20F as diffusion capacity in this example
    c_ct = 3       # guessing 3F as charge-transfer capacity
    r_d = 35       # guessing 35 ohms as diffusion resistance
    r_ct = 10      # guessing 10 ohms as charge-transfer resistance
    v_co = -0.008  # guessing 0.7 V as initial voltage. Based on constant "A_ct"
    time = 100     # duration of simulation [s]
    tau_ct = tau_calc(c_ct, r_ct)
    tau_d = tau_calc(c_d, r_d)
    for t in range(1, time):
        rc_circuits = [RC_circuit(tau_d, t), RC_circuit(tau_ct, t)]
        
