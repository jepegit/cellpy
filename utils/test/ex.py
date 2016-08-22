# -*- coding: utf-8 -*-

"""
This file is for random examples.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


data = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
                   r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
                   r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv', sep=';')
df = pd.DataFrame(data)

# print df['time (s) cycle_no 1']
# print df[['time (s) cycle_no 1','time (s) cycle_no 2']]
# print np.array(df[['time (s) cycle_no 1','time (s) cycle_no 2']])

df2 = pd.DataFrame(np.array(df[['time (s) cycle_no 1','time (s) cycle_no 2']]))
print df2
# print df.head()
# print df.tail()
# print df.tail(2)


# ===============Data analysis with Pandas from youtube video, sentdex=========
# IO - input output
#If I want to export, then write: df.to_csv('new_name.csv')
# Renaming the coloumns

df3 = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
                   r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
                   r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv', sep=';')
df3.to_csv('new_csv.csv')
df3 = pd.read_csv('')
