"""ica contains routines for creating and working with incremental capacity analysis data"""

import os
import numpy as np
from scipy import stats
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.integrate import simps
from scipy.ndimage.filters import gaussian_filter1d
import logging
from cellpy.exceptions import NullData
import warnings

METHODS = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']


# TODO: documentation and tests
# TODO: fitting of o-c curves and differentiation
# TODO: modeling and fitting
# TODO: full-cell


class Converter(object):
    """Class for dq-dv handling.

    Typical usage is to  (1) set the data,  (2) inspect the data, (3) pre-process the data,
    (4) perform the dq-dv transform, and finally (5) post-process the data.
    """

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
        self.increment_method = 'diff'
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

        self.fixed_voltage_range = False

        self.errors = []

    def set_data(self, capacity, voltage):
        """Set the data"""

        self.capacity = capacity
        self.voltage = voltage

    def inspect_data(self, capacity=None, voltage=None):
        """check and inspect the data"""

        if capacity is None:
            capacity = self.capacity
        if voltage is None:
            voltage = self.voltage

        if capacity is None or voltage is None:
            raise NullData

        self.len_capacity = len(capacity)
        self.len_voltage = len(voltage)

        if self.len_capacity <= 1:
            raise NullData
        if self.len_voltage <= 1:
            raise NullData

        d_capacity = np.diff(capacity)
        d_voltage = np.diff(voltage)
        self.d_capacity_mean = np.mean(d_capacity)
        self.d_voltage_mean = np.mean(d_voltage)

        self.min_capacity, self.max_capacity = value_bounds(capacity)
        self.start_capacity, self.end_capacity = index_bounds(capacity)

        self.number_of_points = len(capacity)

        splits = int(self.number_of_points / self.points_pr_split)
        rest = self.number_of_points % self.points_pr_split

        if splits < self.minimum_splits:
            txt = "no point in splitting, too little data"
            logging.info(txt)
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
        """perform some pre-processing of the data (i.e. interpolation)"""
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
            savgol_filter_window_divisor = np.amin((self.savgol_filter_window_divisor_default, len_capacity / 5))
            savgol_filter_window_length = int(len_capacity / savgol_filter_window_divisor)

            if savgol_filter_window_length % 2 == 0:
                savgol_filter_window_length -= 1
            self.voltage_preprocessed = savgol_filter(self.voltage_preprocessed,
                                                      np.amax([3, savgol_filter_window_length]),
                                                      self.savgol_filter_window_order)

    def increment_data(self):
        """perform the dq-dv transform"""

        # NOTE TO ASBJOERN: Probably insert method for "binning" instead of differentiating here
        # (use self.increment_method as the variable for selecting method for)

        # ---- shifting to y-x ----------------------------------------
        len_voltage = len(self.voltage_preprocessed)
        v1, v2 = value_bounds(self.voltage_preprocessed)

        # ---- interpolating ------------------------------------------
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
        if self.increment_method == "diff":
            self.incremental_capacity = np.ediff1d(self.capacity_inverted) / self.voltage_inverted_step
            self._incremental_capacity = self.incremental_capacity
            # --- need to adjust voltage ---
            self.voltage_processed = self.voltage_inverted[1:] + 0.5 * self.voltage_inverted_step  # centering

    def post_process_data(self, voltage=None, incremental_capacity=None,
                          voltage_step=None):
        """perform post-processing (smoothing, normalisation, interpolation) of
        the data"""

        if voltage is None:
            voltage = self.voltage_processed
            incremental_capacity = self.incremental_capacity
            voltage_step = self.voltage_inverted_step

        if self.post_smoothing:
            points_fwhm = int(self.voltage_fwhm / voltage_step)
            sigma = np.amax([2, points_fwhm / 2])
            self.incremental_capacity = gaussian_filter1d(incremental_capacity, sigma=sigma, order=self.gaussian_order,
                                                     output=None, mode=self.gaussian_mode,
                                                     cval=self.gaussian_cval, truncate=self.gaussian_truncate)

        if self.normalise:
            area = simps(incremental_capacity, voltage)
            self.incremental_capacity = incremental_capacity * self.normalising_factor / abs(area)

        fixed_range = False
        if isinstance(self.fixed_voltage_range, np.ndarray):
            fixed_range = True
        else:
            if self.fixed_voltage_range:
                fixed_range = True
        if fixed_range:
            v1, v2, number_of_points = self.fixed_voltage_range
            v = np.linspace(v1, v2, number_of_points)
            f = interp1d(x=self.voltage_processed, y=self.incremental_capacity,
                         kind=self.interpolation_method, bounds_error=False,
                         fill_value=np.NaN)

            self.incremental_capacity = f(v)
            self.voltage_processed = v


def value_bounds(x):
    """returns tuple with min and max in x"""
    return np.amin(x), np.amax(x)


def index_bounds(x):
    """returns tuple with first and last item in pandas Series x"""
    return x.iloc[0], x.iloc[-1]


def dqdv(voltage, capacity):
    """Convenience functions for creating dq-dv data from given capacity and
    voltage data"""

    converter = Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()
    return converter.voltage_processed, converter.incremental_capacity


def check_class_ica():
    print(40 * "=")
    print("running check_class_ica")
    print(40 * "-")
    from cellpy import cellreader
    import matplotlib.pyplot as plt

    # -------- defining overall path-names etc ----------
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    print(current_file_path)
    relative_test_data_dir = "../../testdata/hdf5"
    test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
    test_data_dir_out = os.path.join(test_data_dir, "out")
    test_cellpy_file = "20160805_test001_45_cc.h5"
    test_cellpy_file_full = os.path.join(test_data_dir, test_cellpy_file)
    mass = 0.078609164

    # ---------- loading test-data ----------------------
    cell = cellreader.CellpyData()
    cell.load(test_cellpy_file_full)
    list_of_cycles = cell.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print("you have %i cycles" % number_of_cycles)
    cycle = 5
    print("looking at cycle %i" % cycle)

    # ---------- processing and plotting ----------------
    fig, (ax1, ax2) = plt.subplots(2, 1)
    capacity, voltage = cell.get_ccap(cycle)
    ax1.plot(capacity, voltage, "b.-", label="raw")
    converter = Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    ax1.plot(converter.capacity_preprocessed, converter.voltage_preprocessed,
             "r.-", alpha=0.3, label="pre-processed")

    converter.increment_data()
    ax2.plot(converter.voltage_processed, converter.incremental_capacity,
             "b.-", label="incremented")

    converter.fixed_voltage_range = False
    converter.post_smoothing = True
    converter.normalise = False
    converter.post_process_data()
    ax2.plot(converter.voltage_processed, converter.incremental_capacity,
             "y-", alpha=0.3, lw=4.0, label="smoothed")

    converter.fixed_voltage_range = np.array((0.1, 1.2, 100))
    converter.post_smoothing = False
    converter.normalise = False
    converter.post_process_data()
    ax2.plot(converter.voltage_processed, converter.incremental_capacity,
             "go", alpha=0.7,
             label="fixed voltage range")
    ax1.legend(numpoints=1)
    ax2.legend(numpoints=1)
    ax1.set_ylabel("Voltage (V)")
    ax1.set_xlabel("Capacity (mAh/g)")
    ax2.set_xlabel("Voltage (V)")
    ax2.set_ylabel("dQ/dV (mAh/g/V)")
    plt.show()


if __name__ == '__main__':
    check_class_ica()
