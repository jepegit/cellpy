# -*- coding: utf-8 -*-

"""
Reading a csv file with all the relaxation data from cell "sic006_45_cc_01.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

class Read_data(object):
    """
    Receives a .csv data-file and reads it in Pandas. Function "return_ocv"
    will return an numpy array with the extracted data.
    """

    def __init__(self, data):
        self._data = data


    def read_data(self):
        pd.read_csv()
