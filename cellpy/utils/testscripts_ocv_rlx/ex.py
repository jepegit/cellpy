# -*- coding: utf-8 -*-

"""
This file is for random examples.
"""
import pandas as pd
# import numpy as np
import matplotlib.pyplot as plt

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

def main():
    # had to use r'system path to file' to read the csv. Don't know why,
    # but that's how it is right now...
    data = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
                       r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
                       r'\data\20160805_sic006_45_cc_01_ocvrlx_down.csv',
                       sep=';', index_col=0)
    # need to separate time and voltage so that they can be plotted together as x-y
    time_data = [t for i in range(len(data.iloc[0, :])) for t in data.iloc[:, i]
                 if i == 0 or i % 2]
    voltage_data = [v for k in range(0, len(data.iloc[0, :]))
                    for v in data.iloc[:, k] if not k % 2]

    # Splitting the data so that they are in intervals of amount of cycles and
    # putting them into a dictionary for easier tracking. First cycle is the
    # first list. To call: ocv_dic['time/voltage'][0] etc.
    ocv_dic = {'time': [time_data[w: w + len(data)] for w in
                        xrange(0, len(time_data), len(data))],
               'voltage': [voltage_data[j: j + len(data)] for j in
                           xrange(0, len(voltage_data), len(data))]}

    # plotting all curves in same plot
    for _ in range(len(ocv_dic['time'])):
        plt.plot(ocv_dic['time'][_], ocv_dic['voltage'][_])

    # ===================================end=======================================
    #  df.plot()

    # t = []
    # v = []
    # for i in range(len(data.iloc[0, :])):
    #     for column in data.iloc[:, i]:
    #         if i % 2:
    #             v.append(column)
    #         else:
    #             t.append(column)

    # print data.iloc[0]
    # time = df.loc[:, ::2]
    # voltage = df.loc[:, 1::2]
    # print time
    # print voltage.tail()

    # time_data = np.transpose(np.array(df.loc[:, :: 2]))
    # voltage_data = np.transpose(np.array(df.loc[:, 1::2]))

    #
    # xy_data = {'time': [], 'voltage': []}
    # for time, volt in zip(time_data, voltage_data):
    #     xy_data['time'].append(time)
    #     xy_data['voltage'].append(volt)
    # xy_df = pd.DataFrame(xy_data)
    # xy_df.to_csv('time_voltage_down')
    # time_volt = pd.read_csv('time_voltage_down')

    # for i in range(len(time_volt)):
    #     plt.plot(time_volt['time'][0][i], time_volt['voltage'][0][i])
    # plt.plot(xy_data['time'][0], xy_data['voltage'][0])  # Show's all graphs,
    # but in
    # a poor matter.

    # plt.plot(xy_df['time'][0], xy_df['voltage'][0])   # First cycle
    plt.show()

    # ===============Data analysis with Pandas from youtube video, sentdex=========
    # IO - input output
    # If I want to export, then write: df.to_csv('new_name.csv')

    # df3 = pd.read_csv(r'C:\Users\torkv\OneDrive - Norwegian University of Life '
    #                    r'Sciences\Documents\NMBU\master\ife\python\cellpy\utils'
    #                    r'\data\20160805_test001_45_cc_01_ocvrlx_down.csv', sep=';')
    # df3.to_csv('new_csv.csv')
    # df3 = pd.read_csv('new_csv.csv')
    # # print df.head()
    # df3.rename(columns={'time (s) cycle_no 1': 'time (s)'}, inplace=True)
    # print df3.head()
if __name__ == "__main__":
    main()
