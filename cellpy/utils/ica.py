"""ica contains routines for creating and working with incremental capacity analysis data"""

import os
import numpy as np
from scipy import stats
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.integrate import simps
from scipy.ndimage.filters import gaussian_filter1d


METHODS = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']

# TODO: documentation and tests
# TODO: fitting of o-c curves and differentiation
# TODO: modeling and fitting
# TODO: full-cell


class Converter:
    def __init__(self):
        self.capacity = None
        self.voltage = None

        self.capacity_preprocessed = None
        self.voltage_preprocessed = None
        self.capacity_inverted = None
        self.voltage_inverted = None

        self.incremental_capacity = None
        self._incremental_capacity = None  # before smoothing
        self.voltage_processed = None

        self.voltage_inverted_step = None

        self.points_pr_split = 10
        self.minimum_splits = 3
        self.interpolation_method = 'linear'
        self.pre_smoothing = True
        self.smoothing = True
        self.post_smoothing = True
        self.savgol_filter_window_divisor_default = 50
        self.savgol_filter_window_order = 3
        self.voltage_fwhm = 0.01  # res voltage (peak-width)
        self.gaussian_order = 0
        self.gaussian_mode = "reflect"
        self.gaussian_cval = 0.0
        self.gaussian_truncate = 4.0
        self.normalise = True

        self.normalising_factor = None
        self.d_capacity_mean = None
        self.d_voltage_mean = None
        self.len_capacity = None
        self.len_voltage = None
        self.min_capacity = None
        self.max_capacity = None
        self.start_capacity = None
        self.end_capacity = None
        self.number_of_points = None
        self.std_err_median = None
        self.std_err_mean = None

        self.errors = []

    def set_data(self, capacity, voltage):
        self.capacity = capacity
        self.voltage = voltage

    def inspect_data(self, capacity=None, voltage=None):
        if capacity is None:
            capacity = self.capacity
        if voltage is None:
            voltage = self.voltage

        d_capacity = np.diff(capacity)
        d_voltage = np.diff(voltage)
        self.d_capacity_mean = np.mean(d_capacity)
        self.d_voltage_mean = np.mean(d_voltage)

        self.len_capacity = len(capacity)
        self.len_voltage = len(voltage)

        self.min_capacity, self.max_capacity = value_bounds(capacity)
        self.start_capacity, self.end_capacity = index_bounds(capacity)

        self.number_of_points = len(capacity)

        splits = int(self.number_of_points / self.points_pr_split)
        rest = self.number_of_points % self.points_pr_split

        if splits < self.minimum_splits:
            print "no point in splitting, too little data"
            self.errors.append("splitting: to few points")
        else:
            if rest > 0:
                _cap = capacity[:-rest]
                _vol = voltage[:-rest]
            else:
                _cap = capacity
                _vol = voltage

            c_pieces = np.split(_cap, splits)
            v_pieces = np.split(_vol, splits)
            # c_middle = int(np.amax(c_pieces) / 2)

            std_err = []
            c_pieces_avg = []
            for c, v in zip(c_pieces, v_pieces):
                _slope, _intercept, _r_value, _p_value, _std_err = stats.linregress(c, v)
                std_err.append(_std_err)
                c_pieces_avg.append(np.mean(c))

            self.std_err_median = np.median(std_err)
            self.std_err_mean = np.mean(std_err)

        if not self.start_capacity == self.min_capacity:
            self.errors.append("capacity: start<>min")
        if not self.end_capacity == self.max_capacity:
            self.errors.append("capacity: end<>max")
        self.normalising_factor = self.end_capacity

    def pre_process_data(self):
        capacity = self.capacity
        voltage = self.voltage
        len_capacity = self.len_capacity
        # len_voltage = self.len_voltage

        f = interp1d(capacity, voltage, kind=self.interpolation_method)
        c1, c2 = index_bounds(capacity)
        self.capacity_preprocessed = np.linspace(c1, c2, len_capacity)
        # capacity_step = (c2-c1)/(len_capacity-1)
        self.voltage_preprocessed = f(self.capacity_preprocessed)

        if self.pre_smoothing:
            savgol_filter_window_divisor = np.amin((self.savgol_filter_window_divisor_default, len_capacity/5))
            savgol_filter_window_length = int(len_capacity/savgol_filter_window_divisor)

            if savgol_filter_window_length % 2 == 0:
                savgol_filter_window_length -= 1
            self.voltage_preprocessed = savgol_filter(self.voltage_preprocessed,
                                                      np.amax([3, savgol_filter_window_length]),
                                                      self.savgol_filter_window_order)

    def increment_data(self):
        # ---- shifting to y-x ----------------------------------------
        len_voltage = len(self.voltage_preprocessed)
        v1, v2 = value_bounds(self.voltage_preprocessed)
        f = interp1d(self.voltage_preprocessed, self.capacity_preprocessed, kind=self.interpolation_method)

        self.voltage_inverted = np.linspace(v1, v2, len_voltage)
        self.voltage_inverted_step = (v2 - v1) / (len(self.voltage_inverted, ) - 1)
        self.capacity_inverted = f(self.voltage_inverted)

        if self.smoothing:
            savgol_filter_window_divisor = np.amin((self.savgol_filter_window_divisor_default, len_voltage / 5))
            savgol_filter_window_length = int(len(self.voltage_inverted) / savgol_filter_window_divisor)
            if savgol_filter_window_length % 2 == 0:
                savgol_filter_window_length -= 1

            self.capacity_inverted = savgol_filter(self.capacity_inverted,
                                                   np.amax([3, savgol_filter_window_length]),
                                                   self.savgol_filter_window_order)

        # ---  diff --------------------
        self.incremental_capacity = np.ediff1d(self.capacity_inverted) / self.voltage_inverted_step
        self._incremental_capacity = self.incremental_capacity
        # --- need to adjust voltage ---
        self.voltage_processed = self.voltage_inverted[1:] + 0.5 * self.voltage_inverted_step  # sentering

    def post_process_data(self, voltage=None, incremental_capacity=None, voltage_step=None):
        if voltage is None:
            voltage = self.voltage_processed
            incremental_capacity = self.incremental_capacity
            voltage_step = self.voltage_inverted_step

        if self.post_smoothing:
            points_fwhm = int(self.voltage_fwhm / voltage_step)
            sigma = np.amax([2, points_fwhm/2])
            # gives OverflowError: cannot fit 'long' into an index-sized integer sometimes!
            incremental_capacity = gaussian_filter1d(incremental_capacity,sigma=sigma,order=self.gaussian_order,
                                                     output=None, mode=self.gaussian_mode,
                                                     cval=self.gaussian_cval, truncate=self.gaussian_truncate)

        if self.normalise:
            area = simps(incremental_capacity, voltage)
            self.incremental_capacity = incremental_capacity * self.normalising_factor / abs(area)


def value_bounds(x):
    return np.amin(x), np.amax(x)


def index_bounds(x):
    return x.iloc[0], x.iloc[-1]


def dqdv(voltage, capacity):
    converter = Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()
    return converter.voltage_processed, converter.incremental_capacity


def check_class_ica():
    print 40 * "="
    print "running check_class_ica"
    print 40 * "-"
    from cellpy import cellreader
    import matplotlib.pyplot as plt

    # -------- defining overall path-names etc ----------
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    relative_test_data_dir = "../data_ex"
    test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
    test_data_dir_out = os.path.join(test_data_dir, "out")
    test_cellpy_file = "20160805_test001_45_cc.h5"
    test_cellpy_file_full = os.path.join(test_data_dir, test_cellpy_file)
    mass = 0.078609164

    # ---------- loading test-data ----------------------
    cell = cellreader.cellpydata()
    cell.load(test_cellpy_file_full)

    # --A------- checking data --------------------------
    list_of_cycles = cell.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print "you have %i cycles" % number_of_cycles
    print "looking at cycle 1"
    cycle = 5
    fig, (ax1,ax2) = plt.subplots(2,1)
    capacity, voltage = cell.get_ccap(cycle)
    ax1.plot(capacity, voltage, "b-", label="raw")
    converter = Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    ax1.plot(converter.capacity_preprocessed, converter.voltage_preprocessed, "r-", label="pre")
    converter.increment_data()
    converter.post_process_data()
    ax2.plot(converter.voltage_processed, converter._incremental_capacity, "b-", label="inc")
    ax2.plot(converter.voltage_processed, converter.incremental_capacity, "r-", label="post")
    ax1.legend()
    ax2.legend()
    plt.show()

if __name__ == '__main__':
    check_class_ica()
