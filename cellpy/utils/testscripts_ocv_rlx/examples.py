# -*- coding: utf-8 -*-

"""
This file is made for doing examples. The examples are just to see how the
equation look in a plot, so that it's easier to evaluate.
"""

import numpy as np
import matplotlib.pyplot as plt
from math import *
# import pandas as pd
# import pandas.io.data as web  # importing and exporting any kind of data formats

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
    return exp(-float(t)/tau)


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


def ocv_data(dur, tau_ct, tau_d):
        """
        Creating a dataset of ocv points
        :param dur: time of simulation
        :return ocv_t: dataset with ocv points
        :type: numpy array
        """
        ocv_t = np.zeros(dur)
        rc_circuits = None
        for t_ct in range(0, dur/10):
            rc_circuits = [RC_circuit(tau_d, t_ct), RC_circuit(tau_ct, t_ct)]
            ocv_t[t_ct] = RC_relax(v_co, rc_circuits)
        ocv_t[dur/10:] = rc_circuits[1]
        for t in range(dur/10, dur):
            rc_circuits = [RC_circuit(tau_d, t)]
            ocv_t[t] += RC_relax(v_co, rc_circuits)
        return ocv_t


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
    v_co = -0.08    # guessing 0.7 V as initial voltage. Based on constant
    # "A_ct"
    time = 1800     # duration of simulation [s]
    tau_ct = tau_calc(c_ct, r_ct)   # calculating the time
    # constant for
    # charge-transfer RC-circuit
    tau_d = tau_calc(c_d, r_d)   # calculating the time constant for
    # diffusion RC-circuit
    ocv = ocv_data(time, tau_ct, tau_d)
    plt.plot(ocv)
    plt.ylabel('Open circuit voltage')
    plt.show()

