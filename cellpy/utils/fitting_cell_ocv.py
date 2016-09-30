# -*- coding: utf-8 -*-

"""
Using lmfit to fit "cell_ocv" model
"""

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

from lmfit import minimize, Minimizer, Parameters, Parameter, Model
from cell_ocv import *

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

datafolder = r'..\testdata'   # make sure you're in folder \utils. If not,
# activate "print os.getcwd()" to find current folder and extend datafolder
# with [.]\utils\data
# print os.getcwd()
filename_down = r'20160805_sic006_45_cc_01_ocvrlx_down.csv'
filename_up = r'20160805_sic006_45_cc_01_ocvrlx_up.csv'
down = os.path.join(datafolder, filename_down)
up = os.path.join(datafolder, filename_up)
data_down = pd.read_csv(down, sep=';')
data_up = pd.read_csv(up, sep=';')

# need to separate time and voltage so they can be combined as y(x)
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


v_start_down = 1.   # all start variables are taken from fitting_ocv_003.py
v_start_up = 0.01
i_cut_off = 0.000751
contri = {'ct': 0.2, 'd': 0.8}   # taken from "x" in fitting_ocv_003.py,
# function "GuessRC2"
tau_guessed = {'ct': 50, 'd': 400}
guess_up = guessing_parameters(v_start_up, i_cut_off,
                               np.array(sort_up[0][:]['voltage']),
                               contri, tau_guessed)


# Trying to make parameters with lmfit Model.make_params()
ocv_model = Model(ocv_relax_func)

# Tell the script how many rc-circuits there are in the model. This is
# automatically done with the guessing of tau.
ocv_model.set_param_hint('n_rc', value=len(tau_guessed))
# Note that it's important to set value of r_# and c_# from the same rc-circuit
# Example: r_1 with the resistance from ct rc-circuit. Then c_1 need to have
# the capacitance from ct too
ocv_model.set_param_hint('r_1', value=guess_up['r_rc']['ct'], min=0)
ocv_model.set_param_hint('r_2', value=guess_up['r_rc']['d'], min=0)
ocv_model.set_param_hint('c_1', value=guess_up['c_rc']['ct'], min=0)
ocv_model.set_param_hint('c_2', value=guess_up['c_rc']['d'], min=0)
ocv_model.set_param_hint('ocv', value=guess_up['ocv'], min=0)
ocv_model.set_param_hint('v_rlx', value=guess_up['v_rlx'], vary=False)
ocv_model.make_params()
print ocv_model.eval()


