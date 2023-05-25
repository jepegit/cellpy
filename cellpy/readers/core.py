""" This module contains several of the most important classes used in cellpy.

It also contains functions that are used by readers and utils.
And it has the file version definitions.
"""
import abc
import datetime
import importlib
import logging
import os
import pathlib
import pickle
import sys
import time
import warnings
from typing import Any, Tuple, Dict, List, Union, TypeVar

import numpy as np
import pandas as pd
import pint
from scipy import interpolate

from cellpy.exceptions import NullData
from cellpy.internals.core import OtherPath
from cellpy.parameters.internal_settings import (
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
    get_default_raw_units,
    get_default_raw_limits,
    CellpyMetaCommon,
    CellpyMetaIndividualTest,
)

HEADERS_NORMAL = get_headers_normal()  # TODO @jepe refactor this (not needed)
HEADERS_SUMMARY = get_headers_summary()  # TODO @jepe refactor this (not needed)
HEADERS_STEP_TABLE = get_headers_step_table()  # TODO @jepe refactor this (not needed)


# pint (https://pint.readthedocs.io/en/stable/)
ureg = pint.UnitRegistry()
ureg.default_format = "~P"
Q = ureg.Quantity


# TODO: in future versions (maybe 1.1.0) we should "copy-paste" the whole pathlib module
#  from CPython and add the functionality we need to it. This will make
#  it easier to keep up with changes in the pathlib module.


# https://stackoverflow.com/questions/60067953/
# 'is-it-possible-to-specify-the-pickle-protocol-when-writing-pandas-to-hdf5
class PickleProtocol:
    """Context for using a specific pickle protocol."""

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


class BaseDbReader(metaclass=abc.ABCMeta):
    """Base class for database readers."""

    @abc.abstractmethod
    def select_batch(self, batch: str) -> List[int]:
        pass

    @abc.abstractmethod
    def get_mass(self, pk: int) -> float:
        pass

    @abc.abstractmethod
    def get_area(self, pk: int) -> float:
        pass

    @abc.abstractmethod
    def get_loading(self, pk: int) -> float:
        pass

    @abc.abstractmethod
    def get_nom_cap(self, pk: int) -> float:
        pass

    @abc.abstractmethod
    def get_total_mass(self, pk: int) -> float:
        pass

    @abc.abstractmethod
    def get_cell_name(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_cell_type(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_label(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_comment(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_group(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_args(self, pk: int) -> dict:
        pass

    @abc.abstractmethod
    def get_experiment_type(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def get_instrument(self, pk: int) -> str:
        pass

    @abc.abstractmethod
    def inspect_hd5f_fixed(self, pk: int) -> int:
        pass

    @abc.abstractmethod
    def get_by_column_label(self, pk: int, name: str) -> Any:
        pass

    @abc.abstractmethod
    def from_batch(
        self,
        batch_name: str,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        pass


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

    def __init__(self, filename: Union[str, OtherPath] = None, is_db: bool = False):
        """Initialize the FileID class."""

        self.is_db: bool = is_db
        self._last_data_point: Optional[int] = None
        self.name: Optional[str] = None
        self.full_name: Optional[str] = None
        self.size: Optional[int] = None
        self.last_modified: Optional[int] = None
        self.last_accessed: Optional[int] = None
        self.last_info_changed: Optional[int] = None
        self.location: Optional[int] = None

        if self.is_db:
            self._from_db(filename)
            return

        make_defaults = True
        if filename is not None:
            if not isinstance(filename, OtherPath):
                logging.debug("filename is not an OtherPath object")
                filename = OtherPath(filename)

            if filename.is_file():
                self.populate(filename)
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
        """Return a string representation of the FileID object."""
        try:
            if self.is_db:
                txt = "\n<fileID><is_db>\n"
            else:
                txt = "\n<fileID><is_file>\n"
        except AttributeError:
            txt = "\n<fileID><is_file>\n"

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

    def _from_db(self, filename):
        self.name = filename
        self.full_name = filename
        self.size = 0
        self.last_modified = None
        self.last_accessed = None
        self.last_info_changed = None
        self.location = None
        self._last_data_point = 0

    @property
    def last_data_point(self):
        # TODO: consider including a method here to find the last data point (raw data)
        # ideally, this value should be set when loading the raw data before
        # merging files (if it consists of several files)
        return self._last_data_point

    @last_data_point.setter
    def last_data_point(self, value):
        self._last_data_point = value

    def populate(self, filename: Union[str, OtherPath]):
        """Finds the file-stats and populates the class with stat values.

        Args:
            filename (str, OtherPath): name of the file.
        """
        if not isinstance(filename, OtherPath):
            logging.debug("filename is not an OtherPath object")
            filename = OtherPath(filename)

        if filename.is_file():
            fid_st = filename.stat()
            self.name = filename.name
            self.full_name = filename.full_path
            self.size = fid_st.st_size
            self.last_modified = fid_st.st_mtime
            self.last_accessed = fid_st.st_atime
            self.last_info_changed = fid_st.st_ctime
            self.location = str(filename.parent)

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


class Data:
    """Object to store data for a cell-test.

    This class is used for storing all the relevant data for a cell-test, i.e. all
    the data collected by the tester as stored in the raw-files, and user-provided
    metadata about the cell-test.
    """

    def _repr_html_(self):
        txt = f"<h2>Data-object</h2> id={hex(id(self))}"
        txt += "<p>"
        for p in dir(self):
            if not p.startswith("_"):
                if p not in ["raw", "summary", "steps", "logger"]:
                    value = self.__getattribute__(p)
                    txt += f"<b>{p}</b>: {value}<br>"
        txt += "</p>"
        try:
            raw_txt = f"<p><b>raw data-frame (summary)</b><br>{self.raw.describe()._repr_html_()}</p>"  # noqa
            raw_txt += f"<p><b>raw data-frame (head)</b><br>{self.raw.head()._repr_html_()}</p>"  # noqa
        except AttributeError:
            raw_txt = "<p><b>raw data-frame </b><br> not found!</p>"
        except ValueError:
            raw_txt = "<p><b>raw data-frame </b><br> does not contain any columns!</p>"

        try:
            summary_txt = f"<p><b>summary data-frame (summary)</b><br>{self.summary.describe()._repr_html_()}</p>"  # noqa
            summary_txt += f"<p><b>summary data-frame (head)</b><br>{self.summary.head()._repr_html_()}</p>"  # noqa
        except AttributeError:
            summary_txt = "<p><b>summary data-frame </b><br> not found!</p>"
        except ValueError:
            summary_txt = (
                "<p><b>summary data-frame </b><br> does not contain any columns!</p>"
            )

        try:
            steps_txt = f"<p><b>steps data-frame (summary)</b><br>{self.steps.describe()._repr_html_()}</p>"  # noqa
            steps_txt += f"<p><b>steps data-frame (head)</b><br>{self.steps.head()._repr_html_()}</p>"  # noqa
        except AttributeError:
            steps_txt = "<p><b>steps data-frame </b><br> not found!</p>"
        except ValueError:
            steps_txt = (
                "<p><b>steps data-frame </b><br> does not contain any columns!</p>"
            )

        return txt + summary_txt + steps_txt + raw_txt

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("created DataSet instance")

        self.raw_data_files = []
        self.raw_data_files_length = []
        self.loaded_from = None
        self._raw_id = None
        self.raw_units = get_default_raw_units()
        self.raw_limits = get_default_raw_limits()

        self.raw = pd.DataFrame()
        self.summary = pd.DataFrame()
        self.steps = pd.DataFrame()

        self.meta_common = CellpyMetaCommon()
        self.meta_test_dependent = CellpyMetaIndividualTest()

        # custom meta-data
        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])

    # ---------------- left-over-properties v7 -> v8 -----------------
    # these now belong to the CellpyMeta attributes
    #   however, since they are extensively used in the instrument
    #   loaders and cellreader, they are also accessible here as properties

    @property
    def raw_id(self):
        return self.meta_common.raw_id

    @property
    def start_datetime(self):
        return self.meta_common.start_datetime

    @start_datetime.setter
    def start_datetime(self, n):
        self.meta_common.start_datetime = n

    @property
    def material(self):
        return self.meta_common.material

    @material.setter
    def material(self, n):
        self.meta_common.material = n

    @property
    def mass(self):
        return self.meta_common.mass

    @mass.setter
    def mass(self, n):
        self.meta_common.mass = n

    @property
    def tot_mass(self):
        return self.meta_common.tot_mass

    @tot_mass.setter
    def tot_mass(self, n):
        self.meta_common.tot_mass = n

    @property
    def active_electrode_area(self):
        return self.meta_common.active_electrode_area

    @active_electrode_area.setter
    def active_electrode_area(self, area):
        self.meta_common.active_electrode_area = area

    @property
    def cell_name(self):
        return self.meta_common.cell_name

    @cell_name.setter
    def cell_name(self, cell_name):
        self.meta_common.cell_name = cell_name

    @property
    def nom_cap(self):
        return self.meta_common.nom_cap

    @nom_cap.setter
    def nom_cap(self, value):
        if value < 1.0:
            warnings.warn(
                f"POSSIBLE BUG: NOMINAL CAPACITY LESS THAN 1.0 ({value}).",
                DeprecationWarning,
                stacklevel=2,
            )
        self.meta_common.nom_cap = value  # nominal capacity

    @staticmethod
    def _header_str(hdr):
        txt = "\n"
        txt += 80 * "-" + "\n"
        txt += f" {hdr} ".center(80) + "\n"
        txt += 80 * "-" + "\n"
        return txt

    def __str__(self):
        txt = "<Data>\n"
        txt += "loaded from file(s)\n"
        if isinstance(self.loaded_from, (list, tuple)):
            for f in self.loaded_from:
                txt += str(f)
                txt += "\n"

        else:
            txt += str(self.loaded_from)
            txt += "\n"
        txt += "\n* GLOBAL\n"
        txt += f"material:            {self.meta_common.material}\n"
        txt += f"mass (active):       {self.meta_common.mass}\n"
        txt += f"mass (total):        {self.meta_common.tot_mass}\n"
        txt += f"nominal capacity:    {self.meta_common.nom_cap}\n"
        txt += f"test ID:             {self.meta_test_dependent.test_ID}\n"
        txt += f"channel index:       {self.meta_test_dependent.channel_index}\n"
        txt += f"creator:             {self.meta_test_dependent.creator}\n"
        txt += f"schedule file name:  {self.meta_test_dependent.schedule_file_name}\n"

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

    def populate_defaults(self):
        # modify this method upon need
        logging.debug("checking and populating defaults for the cell")

        if not self.active_electrode_area:
            self.active_electrode_area = 1.0
            logging.debug(
                f"active_electrode_area not set -> setting to: {self.active_electrode_area}"
            )

        if not self.mass:
            self.mass = 1.0
            logging.debug(f"mass not set -> setting to: {self.mass}")

        if not self.tot_mass:
            self.tot_mass = self.mass
            logging.debug(
                f"total mass not set -> setting to same as mass: {self.tot_mass}"
            )

        return True

    @property
    def empty(self):
        if self.has_data:
            return False
        return True

    @property
    def has_summary(self):
        """check if the summary table exists"""
        try:
            empty = self.summary.empty
            # TODO: check if the summary has the expected columns
            #  (since it can be unprocessed directly from the raw data)
        except AttributeError:
            empty = True
        return not empty

    @property
    def has_steps(self):
        """check if the step table exists"""
        try:
            empty = self.steps.empty
        except AttributeError:
            empty = True
        return not empty

    @property
    def has_data(self):
        try:
            empty = self.raw.empty
        except AttributeError:
            empty = True
        return not empty


class InstrumentFactory:
    def __init__(self):
        self._builders = {}
        self._kwargs = {}

    def register_builder(self, key: str, builder: Tuple[str, Any], **kwargs) -> None:
        """register an instrument loader module.

        Args:
            key: instrument id
            builder: (module_name, module_path)
            **kwargs: stored in the factory (will be used in the future for allowing to set
               defaults to the builders to allow for using .query).
        """

        logging.debug(f"Registering instrument {key}")
        self._builders[key] = builder
        self._kwargs[key] = kwargs

    def create(self, key: Union[str, None], **kwargs):
        """Create the instrument loader module and initialize the loader class.

        Args:
            key: instrument id
            **kwargs: sent to the initializer of the loader class.

        Returns:
            instance of loader class.
        """

        module_name, module_path = self._builders.get(key, (None, None))

        # constant:
        instrument_class = "DataLoader"

        if not module_name:
            raise ValueError(key)

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        loader_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = loader_module  # noqa
        spec.loader.exec_module(loader_module)
        cls = getattr(loader_module, instrument_class)

        # TODO: get stored kwargs from self.__kwargs and merge them with the supplied kwargs
        #  (supplied should have preference)

        return cls(**kwargs)

    def query(self, key: str, variable: str) -> Any:
        """performs a get_params lookup for the instrument loader.

        Args:
            key: instrument id.
            variable: the variable you want to lookup.

        Returns:
            The value of the variable if the loaders get_params method supports it.
        """
        loader = self.create(key)
        try:
            value = loader.get_params(variable)
            logging.debug(f"GOT {variable}={value} for {key}")
            return value

        except (AttributeError, NotImplementedError, KeyError):
            logging.debug(f"COULD NOT RETRIEVE {variable} for {key}")
        return


def generate_default_factory():
    """This function searches for all available instrument readers
    and registers them in an InstrumentFactory instance.

    Returns:
        InstrumentFactory
    """
    instrument_factory = InstrumentFactory()
    instruments = find_all_instruments()
    for instrument_id, instrument in instruments.items():
        instrument_factory.register_builder(instrument_id, instrument)
    return instrument_factory


def find_all_instruments() -> Dict[str, Tuple[str, pathlib.Path]]:
    """finds all the supported instruments"""

    import cellpy.readers.instruments as hard_coded_instruments_site

    instruments_found = {}
    logging.debug("Searching for modules in base instrument folder:")

    hard_coded_instruments_site = pathlib.Path(
        hard_coded_instruments_site.__file__
    ).parent
    modules_in_hard_coded_instruments_site = [
        s
        for s in hard_coded_instruments_site.glob("*.py")
        if not (
            str(s.name).startswith("_")
            or str(s.name).startswith("dev_")
            or str(s.name).startswith("base")
            or str(s.name).startswith("backup")
            or str(s.name).startswith("registered_loaders")
        )
    ]

    for module_path in modules_in_hard_coded_instruments_site:
        module_name = module_path.name.rstrip(".py")
        logging.debug(module_name)
        instruments_found[module_name] = (
            module_name,
            module_path,
        )
        logging.debug(" -> added")

    logging.debug("Searching for module configurations in user instrument folder:")
    # These are only yaml-files and should ideally import the appropriate
    #    custom loader class
    # Might not be needed.
    logging.debug("- Not implemented yet")

    logging.debug("Searching for modules through plug-ins:")
    # Not sure how to do this yet. Probably also some importlib trick.
    logging.debug("- Not implemented yet")
    return instruments_found


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


# TODO: move this to internals/core
def check64bit(current_system="python"):
    """checks if you are on a 64-bit platform"""
    if current_system == "python":
        return sys.maxsize > 2147483647
    elif current_system == "os":
        import platform

        pm = platform.machine()
        if pm != ".." and pm.endswith("64"):  # recent Python (not Iron)
            return True
        else:
            if "PROCESSOR_ARCHITEW6432" in os.environ:
                return True  # 32 bit program running on 64-bit Windows
            try:
                # 64-bit Windows 64 bit program
                return os.environ["PROCESSOR_ARCHITECTURE"].endswith("64")
            except IndexError:
                pass  # not Windows
            try:
                # this often works in Linux
                return "64" in platform.architecture()[0]
            except Exception:  # noqa
                # is an older version of Python, assume also an older os@
                # (best we can guess)
                return False


# TODO: move this to internals/core
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
    return "%.*f %s" % (precision, b // factor, suffix)  # noqa


# TODO: move this to internals/core
def xldate_as_datetime(xldate, datemode=0, option="to_datetime"):
    """Converts a xls date stamp to a more sensible format.

    Args:
        xldate (str, int): date stamp in Excel format.
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
            # Excel cannot cope with this!
            if option == "to_string":
                date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
                d = d.strftime(date_format)
        except TypeError:
            logging.info(f"The date is not of correct type [{xldate}]")
            d = xldate
    return d


def collect_capacity_curves(
    cell,
    direction="charge",
    trim_taper_steps=None,
    steps_to_skip=None,
    steptable=None,
    max_cycle_number=None,
    **kwargs,
):
    """Create a list of pandas.DataFrames, one for each charge step.

    The DataFrames are named by its cycle number.

    Args:
        cell (``CellpyCell``):  object
        direction (str):
        trim_taper_steps (integer): number of taper steps to skip (counted
            from the end, i.e. 1 means skip last step in each cycle).
        steps_to_skip (list): step numbers that should not be included.
        steptable (``pandas.DataFrame``): optional steptable.
        max_cycle_number (int): only select cycles up to this value.

    Returns:
        list of pandas.DataFrames,
        list of cycle numbers,
        minimum voltage value,
        maximum voltage value

    """

    # TODO: should allow for giving cycle numbers as input (e.g. cycle=[1, 2, 10]
    #  or cycle=2), not only max_cycle_number. Intermediate solution:
    #  The cycle keyword will not break the method but raise a warning:
    for arg in kwargs:
        if arg in ["cycle", "cycles"]:
            logging.warning(
                f"{arg} is not implemented yet, but might exist in newer versions of cellpy."
            )
        else:
            logging.warning(
                f"collect_capacity_curve received unknown key-word argument: {arg=}"
            )

    minimum_v_value = np.Inf
    maximum_v_value = -np.Inf
    charge_list = []
    cycles = kwargs.pop("cycle", None)

    if cycles is None:
        cycles = cell.get_cycle_numbers()

    if max_cycle_number is None:
        max_cycle_number = max(cycles)

    for cycle in cycles:
        if cycle > max_cycle_number:
            break
        try:
            if direction == "charge":
                q, v = cell.get_ccap(
                    cycle,
                    trim_taper_steps=trim_taper_steps,
                    steps_to_skip=steps_to_skip,
                    steptable=steptable,
                    return_dataframe=False,
                )
            else:
                q, v = cell.get_dcap(
                    cycle,
                    trim_taper_steps=trim_taper_steps,
                    steps_to_skip=steps_to_skip,
                    steptable=steptable,
                    return_dataframe=False,
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
        **kwargs: arguments passed to ``scipy.interpolate.interp1d``

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
        # check if it makes sense
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


def convert_from_simple_unit_label_to_string_unit_label(k, v):
    old_raw_units = {
        "current": 1.0,
        "charge": 1.0,
        "voltage": 1.0,
        "time": 1.0,
        "resistance": 1.0,
        "power": 1.0,
        "energy": 1.0,
        "frequency": 1.0,
        "mass": 0.001,
        "nominal_capacity": 1.0,
        "specific_gravimetric": 1.0,
        "specific_areal": 1.0,
        "specific_volumetric": 1.0,
        "length": 1.0,
        "area": 1.0,
        "volume": 1.0,
        "temperature": 1.0,
        "pressure": 1.0,
    }
    old_unit = old_raw_units[k]
    value = v / old_unit
    default_units = get_default_raw_units()

    new_unit = default_units[k]
    value = Q(value, new_unit)
    str_value = str(value)
    return str_value


# ---------------- LOCAL DEV TESTS ----------------


def check_convert_from_simple_unit_label_to_string_unit_label():
    k = "resistance"
    v = 1.0
    n = convert_from_simple_unit_label_to_string_unit_label(k, v)
    print(n)


def check_path_things():
    p = "//jepe@mymachine.my.no/./path/file.txt"
    p2 = pathlib.Path(p)
    print(f"{p2=}")
    print(f"{p2.resolve()=}")
    print(f"{p2.drive=}")
    print(f"{p2.as_uri()=}")
    print(f"{p2.root=}")
    print(f"{p2.anchor=}")
    print(f"{p2.parent=}")
    print(f"{p2.name=}")
    print(f"{p2.stem=}")
    print(f"{p2.suffix=}")
    print(f"{p2.suffixes=}")
    print(f"{p2.parts=}")
    print(f"{p2.is_absolute()=}")
    print(f"{p2.is_reserved()=}")
    print(f"{p2.is_dir()=}")
    print(f"{p2.is_file()=}")

    try:
        print(f"{p2.is_socket()=}")
    except NotImplementedError as e:
        print(f"{e}")
    try:
        print(f"{p2.is_mount()=}")
    except NotImplementedError as e:
        print(f"{e}")
    try:
        print(f"{p2.is_symlink()=}")
    except NotImplementedError as e:
        print(f"{e}")

    try:
        print(f"{p2.owner()=}")
    except NotImplementedError as e:
        print(f"{e}")

    try:
        print(f"{p2.group()=}")
    except NotImplementedError as e:
        print(f"{e}")

    print(f"{p2.exists()=}")


def check_another_path_things():
    p01 = r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res"
    p02 = r"ssh://jepe@server.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res"
    p03 = r"scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res"
    p04 = r"..\data\20160805_test001_45_cc_01.res"
    p05 = pathlib.Path(p01)
    p06 = pathlib.Path(p02)
    for p in [p01, p02, p03, p04, p05, p06]:
        print(f"{p}".center(110, "-"))
        p2 = OtherPath(p)
        print(f"{p2=}")
        print(p2)
        print(f"{p2.resolve()=}")
        print(f"{p2.drive=}")
        print(f"{p2.exists()=}")
        print(f"{p2._is_external=}")  # noqa
        print(f"{p2._location=}")  # noqa
        print(f"{p2._uri_prefix=}")  # noqa
        print(f"{p2.resolve()=}")
        if p2.is_absolute():
            print(f"{p2.as_uri()=}")
        print(f"{p2.is_external=}")
        print(f"{p2.location=}")
        print(f"{p2.uri_prefix=}")
        print(f"{p2.root=}")
        print(f"{p2.anchor=}")
        print(f"{p2.parent=}")
        print(f"{p2.name=}")
        print(f"{p2.stem=}")
        print(f"{p2.suffix=}")
        print(f"{p2.suffixes=}")
        print(f"{p2.parts=}")
        print(f"{type(p2)}")
        print(f"{isinstance(p2, pathlib.Path)=}")
        print(f"{isinstance(p2, OtherPath)=}")
        print()


def check_how_other_path_works():
    p01 = r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res"
    p02 = r"ssh://jepe@somewhere.else.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res"
    p03 = None
    p03b = OtherPath(p03)
    p05 = pathlib.Path(p01)
    p06 = pathlib.Path(p02)
    p07 = OtherPath(p01)
    p08 = OtherPath(p02)
    print(80 * "=")
    for p in [p01, p02, p03, p03b, p05, p06, p07, p08]:
        print(f"{p}".center(110, "-"))
        print(f"{type(p)}".center(110, "*"))
        p2 = OtherPath(p)
        print(f"{p2=}")
        print(p2)
        print(f"{p2.raw_path=}")
        print(f"{p2.is_external=}")
        print(f"{p2.location=}")
        print(f"{p2.uri_prefix=}")
        print(f"{p2._original=}")  # noqa
        print(f"{p2.full_path=}")
        print(f"{p2.parts=}")


def check_copy_external_file():
    from cellpy import prms

    prms.Paths.env_file = r"C:\scripting\cellpy\local\.env_cellpy"
    dst = r"C:\scripting\cellpy\tmp\20210629_moz_cat_02_cc_01.res"
    src = "ssh://jepe@not.in.no/home/jepe@ad.ife.no/Temp/20210629_moz_cat_02_cc_01.res"
    copy_external_file(src, dst)


if __name__ == "__main__":
    check_how_other_path_works()
