""" This module contains several of the most important classes used in cellpy.

It also contains functions that are used by readers and utils. And it has the file-
version definitions.
"""
import abc
import datetime
import fnmatch
import importlib
import io
import getpass
import logging
import os
import pathlib
import pickle
import shutil
import sys
import tempfile
import time
import warnings
from typing import Any, Tuple, Dict, Optional, List, Union

import dotenv
import fabric
import numpy as np
import pandas as pd
import pint
from scipy import interpolate

from cellpy.exceptions import NullData, UnderDefined
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import (
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
    get_default_raw_units,
    get_default_raw_limits,
    CELLPY_FILE_VERSION,
    STEP_TABLE_VERSION,
    RAW_TABLE_VERSION,
    SUMMARY_TABLE_VERSION,
    CellpyMetaCommon,
    CellpyMetaIndividualTest,
)

HEADERS_NORMAL = get_headers_normal()  # TODO @jepe refactor this (not needed)
HEADERS_SUMMARY = get_headers_summary()  # TODO @jepe refactor this (not needed)
HEADERS_STEP_TABLE = get_headers_step_table()  # TODO @jepe refactor this (not needed)
URI_PREFIXES = ["ssh:", "sftp:", "scp:", "http:", "https:", "ftp:", "ftps:", "smb:"]
IMPLEMENTED_PROTOCOLS = ["ssh:", "sftp:", "scp:"]

# pint (https://pint.readthedocs.io/en/stable/)
ureg = pint.UnitRegistry()
Q = ureg.Quantity


# TODO: in future versions (maybe 1.1.0) we should "copy-paste" the whole pathlib module
#  from CPython and add the functionality we need to it. This will make
#  it easier to keep up with changes in the pathlib module.
def _clean_up_original_path_string(path_string):
    logging.debug(f"cleaning up path: {path_string}")
    if not isinstance(path_string, str):
        if isinstance(path_string, OtherPath):
            path_string = path_string.original
        elif isinstance(path_string, pathlib.PosixPath):
            path_string = "/".join(path_string.parts)
        elif isinstance(path_string, pathlib.WindowsPath):
            parts = list(path_string.parts)
            if not parts:
                parts = [""]
            parts[0] = parts[0].replace("\\", "")
            path_string = "/".join(parts)
        else:
            path_string = str(path_string)
    return path_string


def _check_external(path_string: str) -> Tuple[str, bool, str, str]:
    # path_sep = "\\" if os.name == "nt" else "/"
    _is_external = False
    _location = ""
    _uri_prefix = ""
    for prefix in URI_PREFIXES:
        if path_string.startswith(prefix):
            path_string = path_string.replace(prefix, "")
            path_string = path_string.lstrip("/")
            _is_external = True
            _uri_prefix = prefix + "//"
            _location, *rest = path_string.split("/")
            path_string = "/" + "/".join(rest)
            break
    path_string = path_string or "."
    # fix for windows paths:
    path_string = path_string.replace("\\", "/")
    # fix for posix paths:
    path_string = path_string.replace("//", "/")
    return path_string, _is_external, _uri_prefix, _location


class OtherPath(pathlib.Path):
    """A pathlib.Path subclass that can handle external paths.

    Additional attributes:
        is_external (bool): is True if the path is external.
        location (str): the location of the external path (e.g. a server name).
        uri_prefix (str): the prefix of the external path (e.g. ssh:// or sftp://).
        raw_path (str): the path without any uri_prefix or location.
        original (str): the original path string.
        full_path (str): the full path (including uri_prefix and location).
    Additional methods:
        copy (method): a method for copying the file to a local path.
    Overrides (only if is_external is True):
        glob (method): a method for globbing external paths.
        rglob (method): a method for recursive globbing external paths.
    """

    _flavour = pathlib._windows_flavour if os.name == "nt" else pathlib._posix_flavour

    def __new__(cls, *args, **kwargs):
        logging.debug("Running __new__ for OtherPath")
        logging.debug(f"args: {args}")
        logging.debug(f"kwargs: {kwargs}")
        if args:
            path, *args = args
        else:
            path = "."
            logging.debug("initiating OtherPath without any arguments")
        if not path:
            logging.debug("initiating OtherPath with empty path")
            path = "."
        logging.debug(f"path: {path}")
        if isinstance(path, OtherPath):
            logging.debug(f"path is OtherPath")
            path = path._original
        logging.debug(f"checked if path is OtherPath")
        path = _clean_up_original_path_string(path)
        cls.__original = path
        path = _check_external(path)[0]
        return super().__new__(cls, path, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        logging.debug("Running __init__ for OtherPath")
        _path_string, *args = args
        if not _path_string:
            path_string = "."
        else:
            path_string = self.__original
        self._original = self.__original
        self._check_external(path_string)
        # pathlib.PurePath and Path for Python 3.12 seems to have an __init__ method
        # where it sets self._raw_path from the input argument, but this is not the case
        # for Python 3.11, 10, and 9. Those do not have their own __init__ method (and
        # does not have a self._raw_path attribute).
        # Instead of running e.g. super().__init__(self._raw_other_path) we do this
        # instead (which is what the __init__ method does in Python 3.12):
        super().__init__()
        self._raw_path = self._raw_other_path

    def _check_external(self, path_string):
        (
            path_string,
            self._is_external,
            self._uri_prefix,
            self._location,
        ) = _check_external(path_string)
        self._raw_other_path = path_string

    def glob(self, glob_str, *args, **kwargs):
        testing = kwargs.pop("testing", False)
        if self.is_external:
            warnings.warn(f"Cannot glob external paths. Returning empty list.")
            connect_kwargs, host = self._get_connection_info(testing)
            paths = self._glob_with_fabric(host, connect_kwargs, glob_str, *args, **kwargs)
            return {OtherPath(f"{self._original.rstrip('/')}/{p}") for p in paths}
        paths = pathlib.Path(self._original).glob(glob_str)
        return {OtherPath(p) for p in paths}

    def __div__(self, other):
        if self.is_external:
            path = self._original + "/" + other
            return OtherPath(path)
        path = pathlib.Path(self._original).__truediv__(other)
        return OtherPath(path)

    def __truediv__(self, other):
        if self.is_external:
            path = self._original + "/" + other
            return OtherPath(path)
        path = pathlib.Path(self._original).__truediv__(other)
        return OtherPath(path)

    def __rtruediv__(self, key):
        if self.is_external:
            raise TypeError(f"Cannot use rtruediv on external paths.")
        path = pathlib.Path(self._original).__rtruediv__(key)
        return OtherPath(path)

    # TODO 249: implement recursive globbing for external paths (ala glob above):
    def rglob(self, glob_str, *args, **kwargs):
        if self.is_external:
            warnings.warn(f"Cannot rglob external paths.  Returning empty list.")
            return []
        paths = pathlib.Path(self._original).glob(glob_str)
        return {OtherPath(p) for p in paths}

    def resolve(self, *args, **kwargs):
        if self.is_external:
            # warnings.warn(f"Cannot resolve external paths. Returning self. ({self})")
            return self
        resolved_path = pathlib.Path(self._original).resolve(*args, **kwargs)
        return OtherPath(resolved_path)

    def is_dir(self, *args, **kwargs):
        if self.is_external:
            warnings.warn(f"Cannot check if dir exists for external paths!")
            return True
        return super().is_dir()

    @property
    def original(self) -> str:
        return self._original

    @property
    def raw_path(self) -> str:
        # this will return a leading slash for some edge cases
        return self._raw_other_path

    @property
    def full_path(self) -> str:
        if self.is_external:
            return f"{self._uri_prefix}{self._location}{self._raw_other_path}"
        return self._original

    @property
    def is_external(self) -> bool:
        return self._is_external

    @property
    def uri_prefix(self) -> str:
        return self._uri_prefix

    @property
    def location(self) -> str:
        return self._location

    def as_uri(self) -> str:
        if self._is_external:
            return f"{self._uri_prefix}{self._location}/{'/'.join(list(super().parts)[1:])}"
        return super().as_uri()

    def copy(self, destination: pathlib.Path = None, testing=False) -> pathlib.Path:
        """Copy the file to a destination."""
        if destination is None:
            destination = pathlib.Path(tempfile.gettempdir())
        else:
            destination = pathlib.Path(destination)

        path_of_copied_file = destination / self.name
        if not self.is_external:
            shutil.copy2(self, destination)
        else:
            connect_kwargs, host = self._get_connection_info(testing)
            self._copy_with_fabric(host, connect_kwargs, destination)

        return path_of_copied_file

    def _get_connection_info(self, testing):
        host = self.location
        uri_prefix = self.uri_prefix.replace("//", "")
        if uri_prefix not in URI_PREFIXES:
            raise ValueError(f"uri_prefix {uri_prefix} not recognized")
        if uri_prefix not in IMPLEMENTED_PROTOCOLS:
            raise ValueError(
                f"uri_prefix {uri_prefix.replace(':', '')} not implemented yet"
            )
        password = os.getenv("CELLPY_PASSWORD", None)
        key_filename = os.getenv("CELLPY_KEY_FILENAME", None)
        if password is None and key_filename is None:
            raise UnderDefined(
                "You must define either CELLPY_PASSWORD "
                "or CELLPY_KEY_FILENAME environment variables."
            )
        if key_filename is not None:
            connect_kwargs = {"key_filename": key_filename}
            logging.debug(f"got key_filename")
            if not testing:
                if not pathlib.Path(key_filename).is_file():
                    raise FileNotFoundError(f"Could not find key file {key_filename}")
        else:
            connect_kwargs = {"password": password}
        return connect_kwargs, host

    def _copy_with_fabric(self, host, connect_kwargs, destination):
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                conn.get(self.raw_path, str(destination / self.name))
                logging.debug(f"copying took {time.time() - t1:.2f} seconds")
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not find file {self.raw_path} on {host}"
                ) from e

    def _glob_with_fabric(self, host, connect_kwargs, glob_str, *args, **kwargs):
        with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
            try:
                t1 = time.time()
                sftp_conn = conn.sftp()
                sftp_conn.chdir(self.raw_path)
                files = sftp_conn.listdir()
                filtered_files = fnmatch.filter(files, glob_str)
                logging.debug(f"globbing took {time.time() - t1:.2f} seconds")
                return filtered_files
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"Could not find file {self.raw_path} on {host}"
                ) from e


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

    def __init__(self, filename=None, is_db=False):
        """Initialize the FileID class."""
        self.is_db = is_db
        if self.is_db:
            self._from_db(filename)
            return

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
        if self.is_db:
            txt = "\n<fileID><is_db>\n"
        else:
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

    def create(self, key: str, **kwargs):
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
        sys.modules[module_name] = loader_module
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

    Input: CellpyCell
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


def abs_path(path):
    """Converts a path to an absolute pathlib.Path object.

    Args:
        path (str, pathlib.Path): the path to convert.

    Returns:
        pathlib.Path: the converted path.

    """
    if isinstance(path, str):
        path = pathlib.Path(path)

    return path.resolve()


# TODO 249: move this to helpers
def create_connection(
    host=None,
    user=None,
    password=None,
    key_filename=None,
    ask_for_password=False,
    protocol="ssh",
):
    """Creates a connection to a remote host.

    Args:
        host (str): The host to connect to; uses env vars if not given.
        user (str): The user to connect as; uses env vars if not given.
        password (str): The password to use; uses env vars if not given.
        key_filename (str): The key filename to use; uses env vars if not given.
        ask_for_password (bool): If True, will ask for password if no password and key_filename is found.
        protocol (str): The protocol to use. Currently, only "ssh" and "sftp" is supported.

    Notes:
        If no password and no key_filename is found, will try to connect without password.
        Using the key_filename will override the password.

    Returns:
        fabric's implementation of paramiko.SSHClient: The SSH client.
    """
    if protocol not in ["ssh", "sftp"]:
        raise ValueError(f"Protocol {protocol} is not supported.")
    env_file = pathlib.Path(prms.Paths.env_file)
    env_file_in_user_dir = pathlib.Path.home() / prms.Paths.env_file
    if env_file.is_file():
        dotenv.load_dotenv(env_file)
    elif env_file_in_user_dir.is_file():
        dotenv.load_dotenv(env_file_in_user_dir)
    else:
        logging.debug("No .env file found. Using default values.")

    host = host or os.getenv("CELLPY_HOST")
    user = user or os.getenv("CELLPY_USER")
    password = password or os.getenv("CELLPY_PASSWORD", None)
    key_filename = key_filename or os.getenv("CELLPY_KEY_FILENAME", None)

    if password is None and key_filename is None and ask_for_password:
        try:
            password = getpass.getpass()
        except Exception as e:
            logging.debug(f"Could not get password: {e}")
            return

    if key_filename is not None:
        if not pathlib.Path(key_filename).is_file():
            logging.debug(f"Could not find key file: {key_filename}")
            logging.debug(f"Trying to connect without key file.")
            connect_kwargs = {}
        else:
            connect_kwargs = {"key_filename": key_filename}
    elif password is not None:
        connect_kwargs = {"password": password}
    else:
        connect_kwargs = {}
    connection = fabric.Connection(host, user, connect_kwargs=connect_kwargs)
    return connection


# TODO 249: move this to helpers
def copy_external_file(src: OtherPath, dst: OtherPath, *args, **kwargs):
    """Copies a file from src to dst."""
    if not isinstance(src, OtherPath):
        src = OtherPath(src)
    if not isinstance(dst, OtherPath):
        dst = OtherPath(dst)
    if not src.is_external:
        raise ValueError("src must be an external file")
    if dst.is_external:
        raise ValueError("dst must be a local file")
    # TODO 249: currently only supporting sftp and ssh and env variables - should be extended by unpacking src
    if src.uri_prefix.startswith("sftp"):
        c = create_connection(protocol="sftp")
    elif src.uri_prefix.startswith(protocol="ssh"):
        c = create_connection("ssh")
    else:
        raise ValueError(f"Unknown protocol: {src.uri_prefix}")
    c.get(src.raw_path, local=str(dst))
    c.close()


# ---------------- LOCAL DEV TESTS ----------------


def check_convert_from_simple_unit_label_to_string_unit_label():
    k = "resistance"
    v = 1.0
    n = convert_from_simple_unit_label_to_string_unit_label(k, v)
    print(n)


def check_path_things():
    print(abs_path("."))

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
        print(f"{p2._is_external=}")
        print(f"{p2._location=}")
        print(f"{p2._uri_prefix=}")
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
        print(f"{p2._original=}")
        print(f"{p2.full_path=}")
        print(f"{p2.parts=}")


def check_copy_external_file():
    prms.Paths.env_file = r"C:\scripting\cellpy\local\.env_cellpy"
    dst = r"C:\scripting\cellpy\tmp\20210629_moz_cat_02_cc_01.res"
    src = "ssh://jepe@not.in.no/home/jepe@ad.ife.no/Temp/20210629_moz_cat_02_cc_01.res"
    copy_external_file(src, dst)


if __name__ == "__main__":
    check_how_other_path_works()
