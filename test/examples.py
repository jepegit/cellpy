# -*- coding: utf-8 -*-

"""
This file is made for doing examples in
"""

import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

"""
======Global constants======
Constants values are based on results from "fitting_ocv_003.py" by JPM
:param: c_d = diffusion capacity [F]
:param: c_ct = charge-transfer capacity [F]
:param: r_d = diffusion resistance [ohm]
:param: r_ct = charge-transfer capacity [ohm]
:param: v_co = cut-off voltage (assuming initial value) [V]
v_co is actually not initial value in this case because the of ohmic
resistance, r_0, isn't incorporated in this example. r_0 will make the v_co
jump almost instant to a higher value. In real applications, r_0 need to be
properly incorporated in ocv voltage. It's basically just to add a voltage
v_0 that will add to the final ocv voltage.
"""

c_d = 20        # guessing 20F as diffusion capacity in this example
c_ct = 3        # guessing 3F as charge-transfer capacity
r_d = 35        # guessing 35 ohms as diffusion resistance
r_ct = 10       # guessing 10 ohms as charge-transfer resistance
v_co = -0.008   # guessing 0.7 V as initial voltage. Based on constant "a" in
