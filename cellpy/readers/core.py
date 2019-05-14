import datetime
import logging
import os
import collections
import sys
import warnings
from functools import wraps

import pandas as pd

from cellpy.parameters import prms
from cellpy.parameters.internal_settings import (
    cellpy_attributes,
    cellpy_limits, cellpy_units,
)

CELLPY_FILE_VERSION = 4
MINIMUM_CELLPY_FILE_VERSION = 1
STEP_TABLE_VERSION = 3
NORMAL_TABLE_VERSION = 3
SUMMARY_TABLE_VERSION = 3


class FileID(object):
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
                make_defaults = False

        if make_defaults:
            self.name = None
            self.full_name = None
            self.size = 0
            self.last_modified = None
            self.last_accessed = None
            self.last_info_changed = None
            self.location = None

    def __str__(self):
        txt = "\n<fileID>\n"
        txt += "full name: %s\n" % self.full_name
        txt += "name: %s\n" % self.name
        if self.last_modified is not None:
            txt += f"modified: {self.last_modified}\n"
        else:
            txt += "modified: NAN\n"
        if self.size is not None:
            txt += f"size: {self.size}\n"
        else:
            txt += "size: NAN\n"
        return txt

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


class DataSet(object):
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

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("created DataSet instance")

        self.test_no = None
        self.mass = prms.Materials["default_mass"]  # active material (in mg)
        self.tot_mass = prms.Materials["default_mass"]  # total material (in mg)
        self.no_cycles = 0.0
        self.charge_steps = None  # not in use at the moment
        self.discharge_steps = None  # not in use at the moment
        self.ir_steps = None  # dict # not in use at the moment
        self.ocv_steps = None  # dict # not in use at the moment
        self.nom_cap = prms.DataSet["nom_cap"]  # mAh/g (for finding c-rates)
        self.mass_given = False
        self.material = prms.Materials["default_material"]
        self.merged = False
        self.file_errors = None  # not in use at the moment
        self.loaded_from = None  # loaded from (can be list if merged)
        self.raw_data_files = []
        self.raw_data_files_length = []
        self.raw_units = cellpy_units
        self.raw_limits = cellpy_limits
        self.channel_index = None
        self.channel_number = None
        self.creator = None
        self.item_ID = None
        self.schedule_file_name = None
        self.start_datetime = None
        self.test_ID = None
        self.name = None
        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])

        # methods in CellpyData to update if adding new attributes:
        #  _load_infotable()
        # _create_infotable()

        self.data = collections.OrderedDict()  # not used
        self.summary = collections.OrderedDict()  # not used

        self.dfdata = pd.DataFrame()
        self.dfsummary = pd.DataFrame()
        # self.dfsummary_made = False  # Should be removed
        self.step_table = collections.OrderedDict()
        # self.step_table_made = False  # Should be removed
        # self.parameter_table = collections.OrderedDict()
        self.summary_version = SUMMARY_TABLE_VERSION
        self.step_table_version = STEP_TABLE_VERSION
        self.cellpy_file_version = CELLPY_FILE_VERSION
        self.normal_table_version = NORMAL_TABLE_VERSION
        # ready for use if implementing loading units
        # (will probably never happen).

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
            txt += str(self.dfdata.describe())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("SUMMARY")
        try:
            txt += str(self.dfsummary.describe())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("STEP TABLE")
        try:
            txt += str(self.step_table.describe())
            txt += str(self.step_table.head())
        except (AttributeError, ValueError):
            txt += "EMPTY (Not processed yet)\n"

        txt += self._header_str("RAW UNITS")
        txt += "     Currently defined in the CellpyData-object"
        return txt

    @property
    def dfsummary_made(self):
        """check if the summary table exists"""
        try:
            empty = self.dfsummary.empty
        except AttributeError:
            empty = True
        return not empty

    @property
    def step_table_made(self):
        """check if the step table exists"""
        try:
            empty = self.step_table.empty
        except AttributeError:
            empty = True
        return not empty

    @property
    def no_data(self):
        try:
            empty = self.dfdata.empty
        except AttributeError:
            empty = True
        return empty


def check64bit(current_system="python"):
    """checks if you are on a 64 bit platform"""
    if current_system == "python":
        return sys.maxsize > 2147483647
    elif current_system == "os":
        import platform
        pm = platform.machine()
        if pm != ".." and pm.endswith('64'):  # recent Python (not Iron)
            return True
        else:
            if 'PROCESSOR_ARCHITEW6432' in os.environ:
                return True  # 32 bit program running on 64 bit Windows
            try:
                # 64 bit Windows 64 bit program
                return os.environ['PROCESSOR_ARCHITECTURE'].endswith('64')
            except IndexError:
                pass  # not Windows
            try:
                # this often works in Linux
                return '64' in platform.architecture()[0]
            except Exception:
                # is an older version of Python, assume also an older os@
                # (best we can guess)
                return False


def humanize_bytes(b, precision=1):
    """Return a humanized string representation of a number of b.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024*123)
    '123.0 kB'
    >>> humanize_bytes(1024*12342)
    '12.1 MB'
    >>> humanize_bytes(1024*12342,2)
    '12.05 MB'
    >>> humanize_bytes(1024*1234,2)
    '1.21 MB'
    >>> humanize_bytes(1024*1234*1111,2)
    '1.31 GB'
    >>> humanize_bytes(1024*1234*1111,1)
    '1.3 GB'
    """
    # abbrevs = (
    #     (1 << 50L, 'PB'),
    #     (1 << 40L, 'TB'),
    #     (1 << 30L, 'GB'),
    #     (1 << 20L, 'MB'),
    #     (1 << 10L, 'kB'),
    #     (1, 'b')
    # )
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'b')
    )
    if b == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if b >= factor:
            break
    # return '%.*f %s' % (precision, old_div(b, factor), suffix)
    return '%.*f %s' % (precision, b // factor, suffix)


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
            d = datetime.datetime(1899, 12, 30) + \
                datetime.timedelta(days=xldate + 1462 * datemode)
            # date_format = "%Y-%m-%d %H:%M:%S:%f" # with microseconds,
            # excel cannot cope with this!
            if option == "to_string":
                date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
                d = d.strftime(date_format)
        except TypeError:
            logging.info(f'The date is not of correct type [{xldate}]')
            d = xldate
    return d


def Convert2mAhg(c, mass=1.0):
    """Converts capacity in Ah to capacity in mAh/g.

    Args:
        c (float or numpy array): capacity in mA.
        mass (float): mass in mg.

    Returns:
        float: 1000000 * c / mass
    """
    return 1_000_000 * c / mass


class DocInherit(object):
    """Docstring inheriting method descriptor.

    The class itself is also used as a decorator.

    Usage:

        class Foo(object):
            def foo(self):
                "Frobber"
                pass

        class Bar(Foo):
            @doc_inherit
            def foo(self):
                pass

    Reference:
       https://stackoverflow.com/questions/2025562/
       inherit-docstrings-in-python-class-inheritance
    """

    def __init__(self, mthd):
        self.mthd = mthd
        self.name = mthd.__name__

    def __get__(self, obj, cls):
        if obj:
            return self.get_with_inst(obj, cls)
        else:
            return self.get_no_inst(cls)

    def get_with_inst(self, obj, cls):

        overridden = getattr(super(cls, obj), self.name, None)

        @wraps(self.mthd, assigned=('__name__', '__module__'))
        def f(*args, **kwargs):
            return self.mthd(obj, *args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def get_no_inst(self, cls):

        for parent in cls.__mro__[1:]:
            overridden = getattr(parent, self.name, None)
            if overridden: break

        @wraps(self.mthd, assigned=('__name__','__module__'))
        def f(*args, **kwargs):
            return self.mthd(*args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def use_parent_doc(self, func, source):
        if source is None:
            raise NameError("Can't find '%s' in parents" % self.name)
        func.__doc__ = source.__doc__
        return func


doc_inherit = DocInherit
