"""ica contains routines for creating and working with incremental capacity analysis data"""

import os
import numpy as np
from scipy import stats
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.integrate import simps

print "running ica"


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    import numpy as np
    from math import factorial

    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order + 1)
    half_window = (window_size - 1) // 2
    # precompute coefficients
    b = np.mat([[k ** i for i in order_range] for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate ** deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def get_cycle():
    return None


def smooth_data():
    return None


def inspect_data():
    return None


def increment_data():
    return None


def value_bounds(x):
    return np.amin(x), np.amax(x)


def index_bounds(x):
    return x.iloc[0], x.iloc[-1]


def check_get_and_plot_ica():
    print 40*"="
    print "running check_get_and_plot_ica"
    print 40*"-"
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
    # TODO: define if it is increasing etc (discharge vs charge etc)
    list_of_cycles = cell.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print "you have %i cycles" % number_of_cycles
    print "looking at cycle 1"
    cycle = 1
    capacity, voltage = cell.get_ccap(cycle)


    # look at the data
    # find "error" by fitting 1% points to a straight line and find deviations pr point

    number_of_points = len(capacity)
    points_pr_split = 10
    splits = int(number_of_points/points_pr_split)

    print number_of_points
    c_pieces = np.split(capacity,splits)
    v_pieces = np.split(voltage, splits)
    c_middle = int(np.amax(c_pieces)/2)

    std_err = []
    c_pieces_avg = []
    #
    # fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    for c, v in zip(c_pieces, v_pieces):
        _slope, _intercept, _r_value, _p_value, _std_err = stats.linregress(c, v)
        std_err.append(_std_err)
        c_pieces_avg.append(np.mean(c))

        # ax1.plot(c,v, ".-")

    print "std_err:"
    # ax2.plot(c_pieces_avg, std_err)
    print "std_err median:"
    std_err_median = np.median(std_err)
    std_err_mean = np.mean(std_err)
    # ax2.plot(c_middle, std_err_median, "ro")
    # ax2.plot(c_middle, std_err_mean, "go")

    d_capacity = np.diff(capacity)
    d_voltage = np.diff(voltage)
    d_capacity_mean = np.mean(d_capacity)
    d_voltage_mean = np.mean(d_voltage)

    len_capacity = len(capacity)
    len_voltage = len(voltage)

    print value_bounds(capacity)
    print index_bounds(capacity)
    print value_bounds(voltage)
    print index_bounds(voltage)

    print std_err_median
    print number_of_points, len_capacity, len_voltage

    print d_capacity_mean
    print d_voltage_mean

    # ax1.plot(capacity[1:], d_capacity)
    # ax1.plot(capacity[1:], d_voltage)
    # ax1.plot(c_middle, d_capacity_mean, "go")
    # ax1.plot(c_middle, d_voltage_mean, "ro")


    # plt.show()
    # --B----------------interpolation/smoothing of "raw" data--------------------
    # - using 1d interpol

    methods = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']
    fig, (ax3,ax4) = plt.subplots(1, 2)
    ax3.plot(capacity, voltage, ".")
    for method in methods:
        f = interp1d(capacity, voltage, kind=method)
        c1,c2 = index_bounds(capacity)
        capacity_new = np.linspace(c1,c2,360/5)
        voltage_new = f(capacity_new)
        #ax3.plot(capacity_new, voltage_new, label=method)



    # using window
    # savgol_filter - xy
    f = interp1d(capacity, voltage, kind='linear')
    c1, c2 = index_bounds(capacity)
    capacity_new = np.linspace(c1, c2, len_capacity)
    capacity_step = (c2-c1)/(len_capacity-1)
    voltage_new = f(capacity_new)
    ax3.plot(capacity_new, voltage_new, label="interpolated")
    voltage_new_sg = savitzky_golay(voltage_new, np.amax([3, len_capacity/50]), 3)
    ax3.plot(capacity_new, voltage_new_sg, "r.-", label="savgol_1")


    # ---C- creating dq/dv
    # ---- shifting to y-x ----------------------------------------

    f = interp1d(voltage_new_sg, capacity_new, kind='linear')
    v1, v2 = value_bounds(voltage_new_sg)
    voltage_new_2 = np.linspace(v1, v2, len(voltage_new_sg))
    voltage_step = (v2 - v1) / (len(voltage_new_sg) - 1)
    capacity_new_2 = f(voltage_new_2)

    capacity_new_sg = savitzky_golay(capacity_new_2, np.amax([3, len(voltage_new_2) / 50]), 3)
    ax4.plot(voltage, capacity, ".")
    ax4.plot(voltage_new, capacity_new)
    ax4.plot(voltage_new_2, capacity_new_sg, "r.-", label="savgol_2")

    # ---diff
    incremental_capacity = np.ediff1d(capacity_new_sg) / voltage_step
    print len(voltage_new_2)
    print len(incremental_capacity)
    ax4.plot(voltage_new_2[1:], incremental_capacity, "g.", label="incremental capacity")

    # --- need to adjust voltage

    voltage_new_3 = voltage_new_2[1:] + 0.5*voltage_step  # sentering
    ax4.plot(voltage_new_3, incremental_capacity, "b.", label="incremental capacity2")


    # --D--- smoothing final data etc-------------

    # smooth

    # reverse?

    # "normalize" etc.





    plt.legend()
    plt.show()
    print "ok"

if __name__ == '__main__':
    check_get_and_plot_ica()
