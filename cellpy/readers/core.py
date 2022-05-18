""" This module contains several of the most important classes used in cellpy.

It also contains functions that are used by readers and utils. And it has the file-
version definitions.
"""

import collections
import datetime
import importlib
import logging
import os
import pathlib
import pickle
import sys
import time
import warnings
from functools import wraps

import numpy as np
import pandas as pd
from scipy import interpolate

from cellpy.exceptions import NullData
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import (
    ATTRS_CELLPYFILE,
    cellpy_limits,
    cellpy_units,
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
)

CELLPY_FILE_VERSION = 6
MINIMUM_CELLPY_FILE_VERSION = 4
STEP_TABLE_VERSION = 5
RAW_TABLE_VERSION = 5
SUMMARY_TABLE_VERSION = 5
PICKLE_PROTOCOL = 4

HEADERS_NORMAL = get_headers_normal()
HEADERS_SUMMARY = get_headers_summary()
HEADERS_STEP_TABLE = get_headers_step_table()


# https://stackoverflow.com/questions/60067953/
# 'is-it-possible-to-specify-the-pickle-protocol-when-writing-pandas-to-hdf5
class PickleProtocol:
    def __init__(self, level):
        self.previous = pickle.HIGHEST_PROTOCOL
        self.level = level

    def __enter__(self):
        importlib.reload(pickle)
        pickle.HIGHEST_PROTOCOL = self.level

    def __exit__(self, *exc):
        importlib.reload(pickle)
        pickle.HIGHEST_PROTOCOL = self.previous


def pickle_protocol(level):
    return PickleProtocol(level)


class FileID:
    """class for storing information about the raw-data files.

    This class is used for storing and handling raw-data file information.
    It is important to keep track of when the data was extracted from the
    raw-data files so that it is easy to know if the hdf5-files used for
    @storing "treated" data is up-to-date.

    Attributes:
        name (str): Filename of the raw-data file.
        full_name (str): Filename including path of the raw-data file.
        size (float): Size of the raw-data file.
        last_modified (datetime): Last time of modification of the raw-data
            file.
        last_accessed (datetime): last time of access of the raw-data file.
        last_info_changed (datetime): st_ctime of the raw-data file.
        location (str): Location of the raw-data file.

    """

    def __init__(self, filename=None):
        make_defaults = True
        if filename:
            if os.path.isfile(filename):
                fid_st = os.stat(filename)
                self.name = os.path.abspath(filename)
                self.full_name = filename
                self.size = fid_st.st_size
                self.last_modified = fid_st.st_mtime
                self.last_accessed = fid_st.st_atime
                self.last_info_changed = fid_st.st_ctime
                self.location = os.path.dirname(filename)
                self.last_data_point = 0  # used later when updating is implemented
                make_defaults = False

        if make_defaults:
            self.name = None
            self.full_name = None
            self.size = 0
            self.last_modified = None
            self.last_accessed = None
            self.last_info_changed = None
            self.location = None
            self._last_data_point = 0  # to be used later when updating is implemented

    def __str__(self):
        txt = "\n<fileID>\n"
        txt += f"full name: {self.full_name}\n"
        txt += f"name: {self.name}\n"
        txt += f"location: {self.location}\n"
        if self.last_modified is not None:
            txt += f"modified: {self.last_modified}\n"
        else:
            txt += "modified: NAN\n"
        if self.size is not None:
            txt += f"size: {self.size}\n"
        else:
            txt += "size: NAN\n"

        txt += f"last data point: {self.last_data_point}\n"
        return txt

    @property
    def last_data_point(self):
        # TODO: consider including a method here to find the last data point (raw data)
        # ideally, this value should be set when loading the raw data before
        # merging files (if it consists of several files)
        return self._last_data_point

    @last_data_point.setter
    def last_data_point(self, value):
        self._last_data_point = value

    def populate(self, filename):
        """Finds the file-stats and populates the class with stat values.

        Args:
            filename (str): name of the file.
        """

        if os.path.isfile(filename):
            fid_st = os.stat(filename)
            self.name = os.path.abspath(filename)
            self.full_name = filename
            self.size = fid_st.st_size
            self.last_modified = fid_st.st_mtime
            self.last_accessed = fid_st.st_atime
            self.last_info_changed = fid_st.st_ctime
            self.location = os.path.dirname(filename)

    def get_raw(self):
        """Get a list with information about the file.

        The returned list contains name, size, last_modified and location.
        """
        return [self.name, self.size, self.last_modified, self.location]

    def get_name(self):
        """Get the filename."""
        return self.name

    def get_size(self):
        """Get the size of the file."""
        return self.size

    def get_last(self):
        """Get last modification time of the file."""
        return self.last_modified


class Cell:
    """Object to store data for a test.

    This class is used for storing all the relevant data for a 'run', i.e. all
    the data collected by the tester as stored in the raw-files.

    Attributes:
        test_no (int): test number.
        mass (float): mass of electrode [mg].
        dfdata (pandas.DataFrame): contains the experimental data points.
        dfsummary (pandas.DataFrame): contains summary of the data pr. cycle.
        step_table (pandas.DataFrame): information for each step, used for
            defining type of step (charge, discharge, etc.)

    """

    def _repr_html_(self):
        obj = f"<b>Cell-object</b> id={hex(id(self))}"
        txt = "<p>"
        for p in dir(self):
            if not p.startswith("_"):
                if p not in ["raw", "summary", "steps", "logger"]:
                    value = self.__getattribute__(p)
                    txt += f"<b>{p}</b>: {value}<br>"
        txt += "</p>"
        try:
            raw_txt = f"<p><b>raw data-frame (summary)</b><br>{self.raw.describe()._repr_html_()}</p>"
            raw_txt += f"<p><b>raw data-frame (head)</b><br>{self.raw.head()._repr_html_()}</p>"
        except AttributeError:
            raw_txt = "<p><b>raw data-frame </b><br> not found!</p>"
        except ValueError:
            raw_txt = "<p><b>raw data-frame </b><br> does not contain any columns!</p>"

        try:
            summary_txt = f"<p><b>summary data-frame (summary)</b><br>{self.summary.describe()._repr_html_()}</p>"
            summary_txt += f"<p><b>summary data-frame (head)</b><br>{self.summary.head()._repr_html_()}</p>"
        except AttributeError:
            summary_txt = "<p><b>summary data-frame </b><br> not found!</p>"
        except ValueError:
            summary_txt = (
                "<p><b>summary data-frame </b><br> does not contain any columns!</p>"
            )

        try:
            steps_txt = f"<p><b>steps data-frame (summary)</b><br>{self.steps.describe()._repr_html_()}</p>"
            steps_txt += f"<p><b>steps data-frame (head)</b><br>{self.steps.head()._repr_html_()}</p>"
        except AttributeError:
            steps_txt = "<p><b>steps data-frame </b><br> not found!</p>"
        except ValueError:
            steps_txt = (
                "<p><b>steps data-frame </b><br> does not contain any columns!</p>"
            )

        return obj + txt + summary_txt + steps_txt + raw_txt

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("created DataSet instance")

        # meta-data
        self.cell_no = None
        self.mass = prms.Materials.default_mass  # active material (in mg)
        self.tot_mass = prms.Materials.default_mass  # total material (in mg)
        self.no_cycles = 0.0
        self.charge_steps = None
        self.discharge_steps = None
        self.ir_steps = None
        self.ocv_steps = None
        self.nom_cap = prms.DataSet.nom_cap  # mAh/g (for finding c-rates)
        self.mass_given = False
        self.material = prms.Materials.default_material
        self.merged = False
        self.file_errors = None  # not in use at the moment
        self.loaded_from = None  # loaded from (can be list if merged)
        self.channel_index = None
        self.channel_number = None
        self.creator = None
        self.item_ID = None
        self.schedule_file_name = None
        self.start_datetime = None
        self.test_ID = None
        self.name = None

        # new meta data
        self.cycle_mode = prms.Reader.cycle_mode
        self.active_electrode_area = None  # [cm2]
        self.active_electrode_thickness = None  # [micron]
        self.electrolyte_type = None  #
        self.electrolyte_volume = None  # [micro-liter]
        self.active_electrode_type = None
        self.counter_electrode_type = None
        self.reference_electrode_type = None
        self.experiment_type = None
        self.cell_type = None
        self.separator_type = None
        self.active_electrode_current_collector = None
        self.reference_electrode_current_collector = None
        self.comment = None

        # custom meta-data
        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])

        # methods in CellpyData to update if adding new attributes:
        # ATTRS_CELLPYFILE

        # place to put "checks" etc:
        # _extract_meta_from_cellpy_file
        # _create_infotable()

        self.raw_data_files = []
        self.raw_data_files_length = []
        self.raw_units = cellpy_units
        self.raw_limits = cellpy_limits

        # self.data = collections.OrderedDict()  # not used
        # self.summary = collections.OrderedDict()  # not used

        self.raw = pd.DataFrame()
        self.summary = pd.DataFrame()
        # self.summary_made = False  # Should be removed
        self.steps = pd.DataFrame()  # is this used? - check!
        # self.step_table_made = False  # Should be removed
        # self.parameter_table = collections.OrderedDict()
        self.summary_table_version = SUMMARY_TABLE_VERSION
        self.step_table_version = STEP_TABLE_VERSION
        self.cellpy_file_version = CELLPY_FILE_VERSION
        self.raw_table_version = RAW_TABLE_VERSION

    @staticmethod
    def _header_str(hdr):
        txt = "\n"
        txt += 80 * "-" + "\n"
        txt += f" {hdr} ".center(80) + "\n"
        txt += 80 * "-" + "\n"
        return txt

    def __str__(self):
        txt = "<DataSet>\n"
        txt += "loaded from file\n"
        if isinstance(self.loaded_from, (list, tuple)):
            for f in self.loaded_from:
                txt += str(f)
                txt += "\n"

        else:
            txt += str(self.loaded_from)
            txt += "\n"
        txt += "\n* GLOBAL\n"
        txt += f"material:            {self.material}\n"
        txt += f"mass (active):       {self.mass}\n"
        txt += f"test ID:             {self.test_ID}\n"
        txt += f"mass (total):        {self.tot_mass}\n"
        txt += f"nominal capacity:    {self.nom_cap}\n"
        txt += f"channel index:       {self.channel_index}\n"
        txt += f"DataSet name:        {self.name}\n"
        txt += f"creator:             {self.creator}\n"
        txt += f"schedule file name:  {self.schedule_file_name}\n"

        try:
            if self.start_datetime:
                start_datetime_str = xldate_as_datetime(self.start_datetime)
            else:
                start_datetime_str = "Not given"
        except AttributeError:
            start_datetime_str = "NOT READABLE YET"

        txt += f"start-date:         {start_datetime_str}\n"

        txt += self._header_str("DATA")
        try:
            txt += str(self.raw.describe())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("SUMMARY")
        try:
            txt += str(self.summary.describe())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("STEP TABLE")
        try:
            txt += str(self.steps.describe())
            txt += str(self.steps.head())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("RAW UNITS")
        try:
            txt += str(self.raw.describe())
            txt += str(self.raw.head())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"
        return txt

    @property
    def summary_made(self):
        """check if the summary table exists"""
        try:
            empty = self.summary.empty
        except AttributeError:
            empty = True
        return not empty

    @property
    def steps_made(self):
        """check if the step table exists"""
        try:
            empty = self.steps.empty
        except AttributeError:
            empty = True
        return not empty

    @property
    def no_data(self):
        # TODO: @jepe should consider renaming this to be in-line with "steps_made" etc. (or renaming steps_made and
        #   summary_made to e.g. no_steps, no_summary)
        try:
            empty = self.raw.empty
        except AttributeError:
            empty = True
        return empty


class ObjectFactory:
    def __init__(self):
        self._builders = {}
        self._kwargs = {}

    def register_builder(self, key, builder, **kwargs):
        logging.debug(f"Registering instrument {key}")
        self._builders[key] = builder
        self._kwargs = kwargs

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


def register_instruments():
    # Example for future use
    # This should be moved to cellreader
    factory = ObjectFactory()
    instruments = find_all_instruments()
    for instrument_id, instrument in instruments.items():
        factory.register_builder(instrument_id, instrument)


def _extract_loader_class_from_module(module):
    # insert some magic here (find sub-class of BaseLoader)
    return module


def find_all_instruments():
    # Example for future use.
    # Keeping imports here so that it will simplify future
    #   refactoring.
    # In addition, this functions needs to implement a way to
    # get appropriate names of the different loaders. Or maybe
    # tweak the base loader etc so that it can get the appropriate
    # name from foo.__name__.

    # This function is not ready for use yet. One important part
    # still missing is to find the actual class inside the module
    # (the .py file) that should be loaded. It is probably not
    # very difficult to implement (since it is a subclass of BaseLoader).

    # Another missing part is how to find externally installed loaders
    # (plugins). Of obvious reasons; plugins are not supported yet.

    # Also, need to properly utilise and propagate the instrument loader
    # names etc (using query_instrument).

    from importlib.machinery import SourceFileLoader
    import cellpy.readers.instruments.configurations as site_1
    import cellpy.readers.instruments as site_2

    instruments = {}
    logging.debug("Searches for modules in configurations folder:")

    site_1 = pathlib.Path(site_1.__file__).parent
    modules_in_site_1 = [
        s
        for s in site_1.glob("*.py")
        if not str(s.name).startswith("_")
    ]

    for module in modules_in_site_1:
        module_name = module.name.rstrip(".py")
        foo = SourceFileLoader(module_name, str(module)).load_module()
        instrument_name = foo.__name__
        instrument_class = _extract_loader_class_from_module(foo)
        instruments[instrument_name] = instrument_class
        logging.debug(instrument_name)

    logging.debug("Searching for modules in base instrument folder:")

    site_2 = pathlib.Path(site_2.__file__).parent
    modules_in_site_2 = [
        s
        for s in site_2.glob("*.py")
        if not (
            str(s.name).startswith("_") or
            str(s.name).startswith("dev_") or
            str(s.name).startswith("base") or
            str(s.name).startswith("backup")
        )
    ]

    for module in modules_in_site_2:
        module_name = module.name.rstrip(".py")
        foo = SourceFileLoader(module_name, str(module)).load_module()
        instrument_name = foo.__name__
        instrument_class = _extract_loader_class_from_module(foo)
        instruments[instrument_name] = instrument_class
        logging.debug(instrument_name)

    logging.debug("Searching for module configurations "
                  "in user instrument folder:")
    # These are only yaml-files and should ideally import the appropriate
    #    custom loader class
    logging.debug("- Not implemented yet")

    logging.debug("Searching for modules through plug-ins:")
    # Not sure how to do this yet. Probably also some importlib trick.
    logging.debug("- Not implemented yet")
    return instruments


def __look_up_instrument(instrument):
    if instrument in ["arbin", "arbin_res"]:
        from cellpy.readers.instruments.arbin_res import ArbinLoader as RawLoader
        instrument_id = "arbin"
    elif instrument == "arbin_sql":
        from cellpy.readers.instruments.arbin_sql import ArbinSQLLoader as RawLoader
        instrument_id = "arbin_sql"
    elif instrument == "arbin_sql_csv":
        from cellpy.readers.instruments.arbin_sql_csv import (
            ArbinCsvLoader as RawLoader,
        )
        instrument_id = "arbin_sql_csv"
    elif instrument == "arbin_sql_xlsx":
        from cellpy.readers.instruments.arbin_sql_xlsx import (
            ArbinXLSXLoader as RawLoader,
        )
        instrument_id = "arbin_sql_xlsx"

    elif instrument in ["pec", "pec_csv"]:
        from cellpy.readers.instruments.pec import PECLoader as RawLoader
        instrument_id = "pec"

    elif instrument in ["biologics", "biologics_mpr"]:
        from cellpy.readers.instruments.biologics_mpr import MprLoader as RawLoader
        instrument_id = "biologics"

    elif instrument in ["maccor", "maccor_txt"]:
        from cellpy.readers.instruments.maccor_txt import (
            MaccorTxtLoader as RawLoader,
        )
        instrument_id = "maccor"
        # need more here (model etc)

    elif instrument.startswith("custom"):
        from cellpy.readers.instruments.custom_instrument import (
            CustomTxtLoader as RawLoader,
        )
        instrument_id = "custom"

    elif instrument.startswith("old_custom"):
        print("OLD CUSTOM LOADER")
        from cellpy.readers.instruments.custom import CustomLoader as RawLoader
        instrument_id = "old_custom"

    elif instrument.endswith(".yml"):
        from cellpy.readers.instruments.local_instrument import (
                LocalTxtLoader as RawLoader,
            )
        instrument_id = instrument
        # fix this

    else:
        raise Exception(f"option does not exist: '{instrument}'")

    return RawLoader, instrument_id


def query_instrument(variable, instrument=None, instrument_file=None, **kwargs):
    """Retrieve information from a loader class without instantiating it.

    Remark! This function uses the .get_params method for the loader class and
        not all loaders have this method implemented. This function will catch
        several exceptions (`AttributeError`, `NotImplementedError`, `KeyError`)
        without propagating it. Thus, it is usually OK to use this function, but
        you might not get anything else than `None` from it.
    """

    RawLoader, instrument_id = __look_up_instrument(instrument)
    try:
        value = RawLoader.get_params(variable)
        logging.debug(f"GOT {variable}={value} for {instrument}")
        return value

    except (AttributeError, NotImplementedError, KeyError):
        logging.debug(f"COULD NOT RETRIEVE {variable} for {instrument}")


def identify_last_data_point(data):
    """Find the last data point and store it in the fid instance"""

    logging.debug("searching for last data point")
    hdr_data_point = HEADERS_NORMAL.data_point_txt
    try:
        if hdr_data_point in data.raw.columns:

            last_data_point = data.raw[hdr_data_point].max()
        else:
            last_data_point = data.raw.index.max()
    except AttributeError:
        logging.debug("AttributeError - setting last data point to 0")
        last_data_point = 0
    if not last_data_point > 0:
        last_data_point = 0
    data.raw_data_files[0].last_data_point = last_data_point
    logging.debug(f"last data point: {last_data_point}")
    return data


def check64bit(current_system="python"):
    """checks if you are on a 64 bit platform"""
    if current_system == "python":
        return sys.maxsize > 2147483647
    elif current_system == "os":
        import platform

        pm = platform.machine()
        if pm != ".." and pm.endswith("64"):  # recent Python (not Iron)
            return True
        else:
            if "PROCESSOR_ARCHITEW6432" in os.environ:
                return True  # 32 bit program running on 64 bit Windows
            try:
                # 64 bit Windows 64 bit program
                return os.environ["PROCESSOR_ARCHITECTURE"].endswith("64")
            except IndexError:
                pass  # not Windows
            try:
                # this often works in Linux
                return "64" in platform.architecture()[0]
            except Exception:
                # is an older version of Python, assume also an older os@
                # (best we can guess)
                return False


def humanize_bytes(b, precision=1):
    """Return a humanized string representation of a number of b."""

    abbrevs = (
        (1 << 50, "PB"),
        (1 << 40, "TB"),
        (1 << 30, "GB"),
        (1 << 20, "MB"),
        (1 << 10, "kB"),
        (1, "b"),
    )
    if b == 1:
        return "1 byte"
    for factor, suffix in abbrevs:
        if b >= factor:
            break
    # return '%.*f %s' % (precision, old_div(b, factor), suffix)
    return "%.*f %s" % (precision, b // factor, suffix)


def xldate_as_datetime(xldate, datemode=0, option="to_datetime"):
    """Converts a xls date stamp to a more sensible format.

    Args:
        xldate (str): date stamp in Excel format.
        datemode (int): 0 for 1900-based, 1 for 1904-based.
        option (str): option in ("to_datetime", "to_float", "to_string"),
            return value

    Returns:
        datetime (datetime object, float, or string).

    """

    # This does not work for numpy-arrays

    if option == "to_float":
        d = (xldate - 25589) * 86400.0
    else:
        try:
            d = datetime.datetime(1899, 12, 30) + datetime.timedelta(
                days=xldate + 1462 * datemode
            )
            # date_format = "%Y-%m-%d %H:%M:%S:%f" # with microseconds,
            # excel cannot cope with this!
            if option == "to_string":
                date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
                d = d.strftime(date_format)
        except TypeError:
            logging.info(f"The date is not of correct type [{xldate}]")
            d = xldate
    return d


def convert_to_mAhg(c, mass=1.0):
    """Converts capacity in Ah to capacity in mAh/g.

    Args:
        c (float or numpy array): capacity in mA.
        mass (float): mass in mg.

    Returns:
        float: 1000000 * c / mass
    """
    return 1_000_000 * c / mass


def collect_ocv_curves():
    raise NotImplementedError


def collect_capacity_curves(
    data,
    direction="charge",
    trim_taper_steps=None,
    steps_to_skip=None,
    steptable=None,
    max_cycle_number=None,
    **kwargs,
):
    """Create a list of pandas.DataFrames, one for each charge step.

    The DataFrames are named by its cycle number.

    Input: CellpyData
    Returns: list of pandas.DataFrames,
        list of cycle numbers,
        minimum voltage value,
        maximum voltage value"""

    # TODO: should allow for giving cycle numbers as input (e.g. cycle=[1, 2, 10]
    #  or cycle=2), not only max_cycle_number

    minimum_v_value = np.Inf
    maximum_v_value = -np.Inf
    charge_list = []
    cycles = kwargs.pop("cycle", None)

    if cycles is None:
        cycles = data.get_cycle_numbers()

    if max_cycle_number is None:
        max_cycle_number = max(cycles)

    for cycle in cycles:
        if cycle > max_cycle_number:
            break
        try:
            if direction == "charge":
                q, v = data.get_ccap(
                    cycle,
                    trim_taper_steps=trim_taper_steps,
                    steps_to_skip=steps_to_skip,
                    steptable=steptable,
                )
            else:
                q, v = data.get_dcap(
                    cycle,
                    trim_taper_steps=trim_taper_steps,
                    steps_to_skip=steps_to_skip,
                    steptable=steptable,
                )

        except NullData as e:
            logging.warning(e)
            d = pd.DataFrame()
            d.name = cycle
            charge_list.append(d)
        else:
            d = pd.DataFrame({"q": q, "v": v})
            # d.name = f"{cycle}"
            d.name = cycle
            charge_list.append(d)
            v_min = v.min()
            v_max = v.max()
            if v_min < minimum_v_value:
                minimum_v_value = v_min
            if v_max > maximum_v_value:
                maximum_v_value = v_max
    return charge_list, cycles, minimum_v_value, maximum_v_value


def interpolate_y_on_x(
    df,
    x=None,
    y=None,
    new_x=None,
    dx=10.0,
    number_of_points=None,
    direction=1,
    **kwargs,
):
    """Interpolate a column based on another column.

    Args:
        df: DataFrame with the (cycle) data.
        x: Column name for the x-value (defaults to the step-time column).
        y: Column name for the y-value (defaults to the voltage column).
        new_x (numpy array or None): Interpolate using these new x-values
            instead of generating x-values based on dx or number_of_points.
        dx: step-value (defaults to 10.0)
        number_of_points: number of points for interpolated values (use
            instead of dx and overrides dx if given).
        direction (-1,1): if direction is negative, then invert the
            x-values before interpolating.
        **kwargs: arguments passed to scipy.interpolate.interp1d

    Returns: DataFrame with interpolated y-values based on given or
        generated x-values.

    """

    # TODO: allow for giving a fixed interpolation range (x-values).
    #  Remember to treat extrapolation properly (e.g. replace with NaN?).

    if x is None:
        x = df.columns[0]
    if y is None:
        y = df.columns[1]

    xs = df[x].values
    ys = df[y].values

    if direction > 0:
        x_min = xs.min()
        x_max = xs.max()
    else:
        x_max = xs.min()
        x_min = xs.max()
        dx = -dx

    bounds_error = kwargs.pop("bounds_error", False)
    f = interpolate.interp1d(xs, ys, bounds_error=bounds_error, **kwargs)
    if new_x is None:
        if number_of_points:
            new_x = np.linspace(x_min, x_max, number_of_points)
        else:
            new_x = np.arange(x_min, x_max, dx)

    new_y = f(new_x)

    new_df = pd.DataFrame({x: new_x, y: new_y})

    return new_df


def group_by_interpolate(
    df,
    x=None,
    y=None,
    group_by=None,
    number_of_points=100,
    tidy=False,
    individual_x_cols=False,
    header_name="Unit",
    dx=10.0,
    generate_new_x=True,
):
    """Do a pandas.DataFrame.group_by and perform interpolation for all groups.

    This function is a wrapper around an internal interpolation function in
    cellpy (that uses scipy.interpolate.interp1d) that combines doing a group-by
    operation and interpolation.

    Args:
        df (pandas.DataFrame): the dataframe to morph.
        x (str): the header for the x-value
            (defaults to normal header step_time_txt) (remark that the default
            group_by column is the cycle column, and each cycle normally
            consist of several steps (so you risk interpolating / merging
            several curves on top of each other (not good)).
        y (str): the header for the y-value
            (defaults to normal header voltage_txt).
        group_by (str): the header to group by
            (defaults to normal header cycle_index_txt)
        number_of_points (int): if generating new x-column, how many values it
            should contain.
        tidy (bool): return the result in tidy (i.e. long) format.
        individual_x_cols (bool): return as xy xy xy ... data.
        header_name (str): name for the second level of the columns (only
            applies for xy xy xy ... data) (defaults to "Unit").
        dx (float): if generating new x-column and number_of_points is None or
            zero, distance between the generated values.
        generate_new_x (bool): create a new x-column by
            using the x-min and x-max values from the original dataframe where
            the method is set by the number_of_points key-word:

            1)  if number_of_points is not None (default is 100):

                ```
                new_x = np.linspace(x_max, x_min, number_of_points)
                ```
            2)  else:
                ```
                new_x = np.arange(x_max, x_min, dx)
                ```


    Returns: pandas.DataFrame with interpolated x- and y-values. The returned
        dataframe is in tidy (long) format for tidy=True.

    """
    # TODO: @jepe - create more tests
    time_00 = time.time()
    if x is None:
        x = HEADERS_NORMAL.step_time_txt
    if y is None:
        y = HEADERS_NORMAL.voltage_txt
    if group_by is None:
        group_by = [HEADERS_NORMAL.cycle_index_txt]

    if not isinstance(group_by, (list, tuple)):
        group_by = [group_by]

    if not generate_new_x:
        # check if it makes sence
        if (not tidy) and (not individual_x_cols):
            logging.warning("Unlogical condition")
            generate_new_x = True

    new_x = None

    if generate_new_x:
        x_max = df[x].max()
        x_min = df[x].min()
        if number_of_points:
            new_x = np.linspace(x_max, x_min, number_of_points)
        else:
            new_x = np.arange(x_max, x_min, dx)

    new_dfs = []
    keys = []

    for name, group in df.groupby(group_by):
        keys.append(name)
        if not isinstance(name, (list, tuple)):
            name = [name]

        new_group = interpolate_y_on_x(
            group, x=x, y=y, new_x=new_x, number_of_points=number_of_points, dx=dx
        )

        if tidy or (not tidy and not individual_x_cols):
            for i, j in zip(group_by, name):
                new_group[i] = j
        new_dfs.append(new_group)

    if tidy:
        new_df = pd.concat(new_dfs)
    else:
        if individual_x_cols:
            new_df = pd.concat(new_dfs, axis=1, keys=keys)
            group_by.append(header_name)
            new_df.columns.names = group_by
        else:
            new_df = pd.concat(new_dfs)
            new_df = new_df.pivot(index=x, columns=group_by[0], values=y)

    time_01 = time.time() - time_00
    logging.debug(f"duration: {time_01} seconds")
    return new_df


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    register_instruments()
    # find_all_instruments()
