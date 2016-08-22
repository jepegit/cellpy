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
                   r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv',
                   sep=';', header=None)
df = pd.DataFrame(data[1:])
time_data = np.transpose(np.array(df.loc[:, :: 2]))
voltage_data = np.transpose(np.array(df.loc[:, 1::2]))

xy_data = {'time': [], 'voltage': []}
for time, volt in zip(time_data, voltage_data):
    xy_data['time'].append(time)
    xy_data['voltage'].append(volt)

xy_df = pd.DataFrame(xy_data)
# plt.plot(xy_data['time'], xy_data['voltage'])  # Show's all graphs, but in
# a poor matter.
plt.plot(xy_df['time'][0], xy_df['voltage'][0])   # First cycle
plt.show()


# ===============Data analysis with Pandas from youtube video, sentdex=========
# IO - input output
#If I want to export, then write: df.to_csv('new_name.csv')

# df3 = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
#                    r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
#                    r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv', sep=';')
# df3.to_csv('new_csv.csv')
# df3 = pd.read_csv('new_csv.csv')
# # print df.head()
# df3.rename(columns={'time (s) cycle_no 1': 'time (s)'}, inplace=True)
# print df3.head()
