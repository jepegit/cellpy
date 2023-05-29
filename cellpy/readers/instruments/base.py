"""
When you make a new loader you have to subclass the Loader class.
Remember also to register it in cellpy.cellreader.

(for future development, not used very efficiently yet).
"""

import abc
import logging
import pathlib
import shutil
import tempfile
from abc import ABC
from typing import List, Union

import pandas as pd

import cellpy.internals.core
import cellpy.readers.core as core
from cellpy.parameters.internal_settings import headers_normal
from cellpy.readers.instruments.configurations import (
    ModelParameters,
    register_configuration_from_module,
)
from cellpy.readers.instruments.processors import post_processors, pre_processors
from cellpy.readers.instruments.processors.post_processors import (
    ORDERED_POST_PROCESSING_STEPS,
)

MINIMUM_SELECTION = [
    "Data_Point",
    "Test_Time",
    "Step_Time",
    "DateTime",
    "Step_Index",
    "Cycle_Index",
    "Current",
    "Voltage",
    "Charge_Capacity",
    "Discharge_Capacity",
    "Internal_Resistance",
]


# TODO: move this to another module (e.g. inside processors):
def find_delimiter_and_start(
    file_name,
    separators=None,
    checking_length_header=30,
    checking_length_whole=200,
):
    """function to automatically detect the delimiter and what line the first data appears on.

    Remark! This function is rather simple, it splits the data into to parts
        (possible header part (checking_length_header) and the rest of the data). Then it counts the appearances of
        the different possible delimiters in the rest of the data part, and then selects a delimiter if it has unique
        counts for all the lines.

        The first line is defined as where the delimiter is used same number of times (probably a header line).
    """

    if separators is None:
        separators = [";", "\t", "|", ","]
    logging.debug(f"checking internals of the file {file_name}")

    empty_lines = 0
    with open(file_name, "r") as fin:
        lines = []
        for j in range(checking_length_whole):
            line = fin.readline()
            if not line:
                break
            if len(line.strip()):
                lines.append(line)
            else:
                empty_lines += 1

    checking_length_whole -= empty_lines
    if checking_length_header - empty_lines < 1:
        checking_length_header = checking_length_whole // 2
    separator, number_of_hits = _find_separator(
        checking_length_whole - checking_length_header, lines, separators
    )

    if separator is None:
        raise IOError(f"could not decide delimiter in {file_name}")

    if separator == "\t":
        logging.debug("seperator = TAB")
    elif separator == " ":
        logging.debug("seperator = SPACE")
    else:
        logging.debug(f"seperator = {separator}")

    first_index = _find_first_line_whit_delimiter(
        checking_length_header, lines, number_of_hits, separator
    )
    logging.debug(f"First line with delimiter: {first_index}")
    return separator, first_index


def _find_first_line_whit_delimiter(
    checking_length_header, lines, number_of_hits, separator
):
    first_part = lines[:checking_length_header]
    if number_of_hits is None:
        # remark! if number of hits (i.e. how many separators pr line) is not given, we set it to the amount of
        # separators we find in the third last line.
        number_of_hits = lines[-3].count(separator)
    return [
        line_number
        for line_number, line in enumerate(first_part)
        if line.count(separator) == number_of_hits
    ][0]


def _find_separator(checking_length, lines, separators):
    logging.debug("searching for separators")
    separator = None
    number_of_hits = None
    last_part = lines[
        checking_length:-1
    ]  # don't include last line since it might be corrupted
    check_sep = dict()

    for i, v in enumerate(separators):
        check_sep[i] = [line.count(v) for line in last_part]

    unique_sep_counts = {i: set(v) for i, v in check_sep.items()}

    for index, value in unique_sep_counts.items():
        value_as_list = list(value)
        number_of_hits = value_as_list[0]
        if len(value_as_list) == 1 and number_of_hits > 0:
            separator = separators[index]
            break

    return separator, number_of_hits


def query_csv(
    self,
    name,
    sep=None,
    skiprows=None,
    header=None,
    encoding=None,
    decimal=None,
    thousands=None,
):
    logging.debug(f"parsing with pandas.read_csv: {name}")
    sep = sep or self.sep
    skiprows = skiprows or self.skiprows
    header = header or self.header
    encoding = encoding or self.encoding
    decimal = decimal or self.decimal
    thousands = thousands or self.thousands
    logging.critical(f"{sep=}, {skiprows=}, {header=}, {encoding=}, {decimal=}")
    data_df = pd.read_csv(
        name,
        sep=sep,
        skiprows=skiprows,
        header=header,
        encoding=encoding,
        decimal=decimal,
        thousands=thousands,
    )
    return data_df


class AtomicLoad:
    """Atomic loading class"""

    instrument_name = "atomic_loader"

    _name = None
    _temp_file_path = None
    _fid = None
    _is_db: bool = False
    _copy_also_local: bool = True
    _refuse_copying: bool = False

    @property
    def is_db(self):
        """Is the file stored in the database"""
        return self._is_db

    @is_db.setter
    def is_db(self, value: bool):
        """Is the file stored in the database"""
        self._is_db = value

    @property
    def refuse_copying(self):
        """Should the file be copied to a temporary file"""
        return self._refuse_copying

    @refuse_copying.setter
    def refuse_copying(self, value: bool):
        """Should the file be copied to a temporary file"""
        self._refuse_copying = value

    @property
    def name(self):
        """The name of the file to be loaded"""
        return self._name

    @name.setter
    def name(self, value):
        """The name of the file to be loaded"""
        if not self.is_db and not isinstance(value, cellpy.internals.core.OtherPath):
            logging.debug("converting to OtherPath")
            value = cellpy.internals.core.OtherPath(value)
        self._name = value

    @property
    def temp_file_path(self):
        """The name of the file to be loaded if copied to a temporary file"""
        return self._temp_file_path

    @temp_file_path.setter
    def temp_file_path(self, value):
        """The name of the file to be loaded if copied to a temporary file"""
        self._temp_file_path = value

    @property
    def fid(self):
        """The unique file id"""
        if self._fid is None:
            self.generate_fid()
        return self._fid

    def generate_fid(self, value=None):
        """Generate a unique file id"""
        if self.is_db:
            self._fid = core.FileID(self.name, is_db=True)
        elif self._temp_file_path is not None:
            self._fid = core.FileID(self.name)
        elif self._name is not None:
            self._fid = core.FileID(self.name)
        elif value is not None:
            self._fid = core.FileID(value)
        else:
            raise ValueError("could not generate fid")

    def copy_to_temporary(self):
        """Copy file to a temporary file"""

        logging.debug(f"external file received? {self.name.is_external=}")
        if self.name is None:
            raise ValueError("no file name given to loader class (self.name is None)")

        if self._refuse_copying:
            logging.debug("refusing copying")
            self._temp_file_path = self.name
            return

        if not self._copy_also_local and not self.name.is_external:
            self._temp_file_path = self.name
            return

        self._temp_file_path = self.name.copy()

    def loader_executor(self, *args, **kwargs):
        """Load the file"""
        name = args[0]
        self.refuse_copying = kwargs.pop("refuse_copying", False)
        self.name = name
        if not self.is_db:
            self.copy_to_temporary()
        cellpy_data = self.loader(*args, **kwargs)
        return cellpy_data

    def loader(self, *args, **kwargs):
        """The method that does the actual loading.

        This method should be overwritten by the specific loader class.
        """
        ...


class BaseLoader(AtomicLoad, metaclass=abc.ABCMeta):
    """Main loading class"""

    instrument_name = "base_loader"

    # TODO: should also include the functions for getting cellpy headers etc
    #  here

    @staticmethod
    @abc.abstractmethod
    def get_raw_units() -> dict:
        """Include the settings for the units used by the instrument.

        This is needed for example when converting the capacity to a specific capacity.
        So far, it has been difficult to get any kind of consensus on what the most optimal
        units are for storing cycling data. Therefore, cellpy implements three levels of units:
        1) the raw units that the data is loaded in already has and 2) the cellpy units used by cellpy
        when generating summaries and related information, and 3) output units that can be set to get the data
        in a specif unit when exporting or creating specific outputs such as ICA.

        Comment 2022.09.11::

            still not sure if we should use raw units or cellpy units in the cellpy-files (.h5/ .cellpy).
            Currently, the summary is in cellpy units and the raw and step data is in raw units. If
            you have any input on this topic, let us know.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        The internal cellpy units are given in the ``cellpy_units`` attribute.

        Returns:
            dictionary of units (str)

        Example:
            A minimum viable implementation::

                @staticmethod
                def get_raw_units():
                    raw_units = dict()
                    raw_units["current"] = "A"
                    raw_units["charge"] = "Ah"
                    raw_units["mass"] = "g"
                    raw_units["voltage"] = "V"
                    return raw_units

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_raw_limits(self) -> dict:
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        If the (accumulated) change is less than 'epsilon', then cellpy interpret it to be stable.
        It is expected that different instruments (with different resolution etc.) have different
        resolutions and noice levels, thus different 'epsilons'.

        Returns: the raw limits (dict)

        """
        raise NotImplementedError

    @classmethod
    def get_params(cls, parameter: Union[str, None]) -> dict:
        """Retrieves parameters needed for facilitating working with the
        instrument without registering it.

        Typically, it should include the name and raw_ext.

        Return: parameters or a selected parameter
        """

        return getattr(cls, parameter)

    @abc.abstractmethod
    def loader(self, *args, **kwargs) -> list:
        """Loads data into a Data object and returns it"""
        # This method is used by cellreader through the AtomicLoad.loader_executor method.
        # It should be overwritten by the specific loader class.
        #
        # Notice that it is highly recommended that you don't try to implement .loader_executor yourself
        # in your subclass!
        pass

    @staticmethod
    def identify_last_data_point(data: core.Data) -> core.Data:
        """This method is used to find the last record in the data."""
        return core.identify_last_data_point(data)


class AutoLoader(BaseLoader):
    """Main autoload class.

    This class can be sub-classed if you want to make a data-reader for different type of "easily parsed" files
    (for example csv-files). The subclass needs to have at least one
    associated CONFIGURATION_MODULE defined and must have the following attributes as minimum::

        default_model: str = NICK_NAME_OF_DEFAULT_CONFIGURATION_MODULE
        supported_models: dict = SUPPORTED_MODELS

    where SUPPORTED_MODELS is a dictionary with {NICK_NAME : CONFIGURATION_MODULE_NAME}  key-value pairs.
    Remark! the NICK_NAME must be in upper-case!

    It is also possible to set these in a custom pre_init method::

        @classmethod
        def pre_init(cls):
            cls.default_model: str = NICK_NAME_OF_DEFAULT_CONFIGURATION_MODULE
            cls.supported_models: dict = SUPPORTED_MODELS

    or turn off automatic registering of configuration::

        @classmethod
        def pre_init(cls):
            cls.auto_register_config = False  # defaults to True

    During initialisation of the class, if ``auto_register_config == True``,  it will dynamically load the definitions
    provided in the CONFIGURATION_MODULE.py located in the ``cellpy.readers.instruments.configurations``
    folder/package.

    Attributes can be set during initialisation of the class as **kwargs that are then handled by the
    ``parse_formatter_parameters`` method.

    Remark that some also can be provided as arguments to the ``loader`` method and will then automatically
    be "transparent" to the ``cellpy.get`` function. So if you would like to give the user access to modify
    these arguments, you should implement them in the ``parse_loader_parameters`` method.

    """

    instrument_name = "auto_loader"

    def __init__(self, *args, **kwargs):
        self.auto_register_config = True
        self.pre_init()

        if not hasattr(self, "supported_models"):
            raise AttributeError(
                f"missing attribute in sub-class of TxtLoader: supported_models"
            )
        if not hasattr(self, "default_model"):
            raise AttributeError(
                f"missing attribute in sub-class of TxtLoader: default_model"
            )

        # in case model is given as argument
        self.model = kwargs.pop("model", self.default_model)
        if self.auto_register_config:
            self.config_params = self.register_configuration()

        self.parse_formatter_parameters(**kwargs)

        self.pre_processors = self.config_params.pre_processors
        additional_pre_processor_args = kwargs.pop(
            "pre_processors", None
        )  # could replace None with an empty dict to get rid of the if-clause:
        if additional_pre_processor_args:
            for key in additional_pre_processor_args:
                self.pre_processors[key] = additional_pre_processor_args[key]

        self.post_processors = self.config_params.post_processors
        additional_post_processor_args = kwargs.pop(
            "post_processors", None
        )  # could replace None with an empty dict to get rid of the if-clause:
        if additional_post_processor_args:
            for key in additional_post_processor_args:
                self.post_processors[key] = additional_post_processor_args[key]

        self.include_aux = kwargs.pop("include_aux", False)
        self.keep_all_columns = kwargs.pop("keep_all_columns", False)
        self.cellpy_headers_normal = (
            headers_normal  # the column headers defined by cellpy
        )

    @abc.abstractmethod
    def parse_formatter_parameters(self, **kwargs) -> None:
        ...

    @abc.abstractmethod
    def parse_loader_parameters(self, **kwargs):
        ...

    @abc.abstractmethod
    def query_file(self, file_path: Union[str, pathlib.Path]) -> pd.DataFrame:
        ...

    def pre_init(self) -> None:
        ...

    def register_configuration(self) -> ModelParameters:
        """Register and load model configuration"""
        if (
            self.model is None
        ):  # in case None was given as argument (model=None in initialisation)
            self.model = self.default_model
        model_module_name = self.supported_models.get(self.model.upper(), None)
        if model_module_name is None:
            raise Exception(
                f"The model {self.model} does not have any defined configuration."
                f"\nCurrent supported models are {[*self.supported_models.keys()]}"
            )
        return register_configuration_from_module(self.model, model_module_name)

    def get_raw_units(self):
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns:
            dictionary containing the unit-fractions for current, charge, and mass

        """
        return self.config_params.raw_units

    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns:
            the raw limits (dict)

        """
        return self.config_params.raw_limits

    @staticmethod
    def get_headers_aux(raw: pd.DataFrame) -> dict:
        raise NotImplementedError(
            f"missing method in sub-class of TxtLoader: get_headers_aux"
        )

    def _pre_process(self):
        for processor_name in self.pre_processors:
            if self.pre_processors[processor_name]:
                if hasattr(pre_processors, processor_name):
                    logging.critical(f"running pre-processor: {processor_name}")
                    processor = getattr(pre_processors, processor_name)
                    self.temp_file_path = processor(self.temp_file_path)
                else:
                    raise NotImplementedError(
                        f"{processor_name} is not currently supported - aborting!"
                    )

    def loader(self, name: Union[str, pathlib.Path], **kwargs: str) -> core.Data:
        """returns a Data object with loaded data.

        Loads data from a txt file (csv-ish).

        Args:
            name (str, pathlib.Path): name of the file.
            kwargs (dict): key-word arguments from raw_loader.

        Returns:
            new_tests (list of data objects)

        """
        pre_processor_hook = kwargs.pop("pre_processor_hook", None)

        if self.pre_processors:
            self._pre_process()

        self.parse_loader_parameters(**kwargs)

        data_df = self.query_file(self.temp_file_path)

        if pre_processor_hook is not None:
            logging.debug("running pre-processing-hook")
            data_df = pre_processor_hook(data_df)

        data = core.Data()

        # metadata
        meta = self.parse_meta()
        data.loaded_from = name
        data.channel_index = meta.get("channel_index", None)
        data.test_ID = meta.get("test_ID", None)
        data.test_name = meta.get("test_name", None)
        data.creator = meta.get("creator", None)
        data.schedule_file_name = meta.get("schedule_file_name", None)
        data.start_datetime = meta.get("start_datetime", None)

        # Generating a FileID project:
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        data.raw = data_df
        data.raw_data_files_length.append(len(data_df))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented
        data = self._post_process(data)
        data = self.identify_last_data_point(data)
        if data.start_datetime is None:
            data.start_datetime = data.raw[headers_normal.datetime_txt].iat[0]

        data = self.validate(data)
        return data

    def validate(self, data: core.Data) -> core.Data:
        """validation of the loaded data, should raise an appropriate exception if it fails."""

        logging.debug(f"no validation of defined in this sub-class of TxtLoader")
        return data

    def parse_meta(self) -> dict:
        """method that parses the data for meta-data (e.g. start-time, channel number, ...)"""

        logging.debug(
            f"no parsing method for meta-data defined in this sub-class of TxtLoader"
        )
        return dict()

    def _post_rename_headers(self, data):
        if self.include_aux:
            new_aux_headers = self.get_headers_aux(data.raw)
            data.raw.rename(index=str, columns=new_aux_headers, inplace=True)
        return data

    def _post_process(self, data):
        # ordered post-processing steps:
        for processor_name in ORDERED_POST_PROCESSING_STEPS:
            if processor_name in self.post_processors:
                data = self._perform_post_process_step(data, processor_name)

        # non-ordered post-processing steps
        for processor_name in self.post_processors:
            if processor_name not in ORDERED_POST_PROCESSING_STEPS:
                data = self._perform_post_process_step(data, processor_name)
        return data

    def _perform_post_process_step(self, data, processor_name):
        if self.post_processors[processor_name]:
            if hasattr(post_processors, processor_name):
                logging.critical(f"running post-processor: {processor_name}")
                processor = getattr(post_processors, processor_name)
                data = processor(data, self.config_params)
                if hasattr(self, f"_post_{processor_name}"):  # internal addon-function
                    _processor = getattr(self, f"_post_{processor_name}")
                    data = _processor(data)
            else:
                raise NotImplementedError(
                    f"{processor_name} is not currently supported - aborting!"
                )
        return data


class TxtLoader(AutoLoader, ABC):
    """Main txt loading class (for sub-classing).

    The subclass of a ``TxtLoader`` gets its information by loading model specifications from its respective module
    (``cellpy.readers.instruments.configurations.<module>``) or configuration file (yaml).

    Remark that if you implement automatic loading of the formatter, the module / yaml-file must include all
    the required formatter parameters (sep, skiprows, header, encoding, decimal, thousands).

    If you need more flexibility, try using the ``CustomTxtLoader`` or subclass directly
    from ``AutoLoader`` or ``Loader``.

    Constructor:
        model (str): short name of the (already implemented) sub-model.
        sep (str): delimiter.
        skiprows (int): number of lines to skip.
        header (int): number of the header lines.
        encoding (str): encoding.
        decimal (str): character used for decimal in the raw data, defaults to '.'.
        processors (dict): pre-processing steps to take (before loading with pandas).
        post_processors (dict): post-processing steps to make after loading the data, but before
        returning them to the caller.
        include_aux (bool): also parse so-called auxiliary columns / data. Defaults to False.
        keep_all_columns (bool): load all columns, also columns that are not 100% necessary for ``cellpy`` to work.
        Remark that the configuration settings for the sub-model must include a list of column header names
        that should be kept if keep_all_columns is False (default).

    Module:
        sep (str): the delimiter (also works as a switch to turn on/off automatic detection of delimiter and
        start of data (skiprows)).

    """

    instrument_name = "txt_loader"
    raw_ext = "*"

    # override this if needed
    def parse_loader_parameters(self, **kwargs):
        sep = kwargs.get("sep", None)
        if sep is not None:
            self.sep = sep
        if self.sep is None:
            self._auto_formatter()

    # override this if needed
    def parse_formatter_parameters(self, **kwargs):
        logging.debug(f"model: {self.model}")
        if not self.config_params.formatters:
            # Setting defaults if formatter is not loaded
            logging.debug("No formatter given - using default values.")
            self.sep = kwargs.pop("sep", None)
            self.skiprows = kwargs.pop("skiprows", 0)
            self.header = kwargs.pop("header", 0)
            self.encoding = kwargs.pop("encoding", "utf-8")
            self.decimal = kwargs.pop("decimal", ".")
            self.thousands = kwargs.pop("thousands", None)

        else:
            # Remark! This will break if one of these parameters are missing
            # (not a keyword argument and not within the configuration):
            self.sep = kwargs.pop("sep", self.config_params.formatters["sep"])
            self.skiprows = kwargs.pop(
                "skiprows", self.config_params.formatters["skiprows"]
            )
            self.header = kwargs.pop("header", self.config_params.formatters["header"])
            self.encoding = kwargs.pop(
                "encoding", self.config_params.formatters["encoding"]
            )
            self.decimal = kwargs.pop(
                "decimal", self.config_params.formatters["decimal"]
            )
            self.thousands = kwargs.pop(
                "thousands", self.config_params.formatters["thousands"]
            )
        logging.debug(
            f"Formatters: self.sep={self.sep} self.skiprows={self.skiprows} self.header={self.header} self.encoding={self.encoding}"
        )
        logging.debug(
            f"Formatters (cont.): self.decimal={self.decimal} self.thousands={self.thousands}"
        )

    def _auto_formatter(self):
        separator, first_index = find_delimiter_and_start(
            self.name,
            separators=None,
            checking_length_header=100,
            checking_length_whole=200,
        )
        self.encoding = "UTF-8"  # consider adding a find_encoding function
        self.sep = separator
        self.skiprows = first_index - 1
        self.header = 0

        logging.critical(
            f"auto-formatting:\n  {self.sep=}\n  {self.skiprows=}\n  {self.header=}\n  {self.encoding=}\n"
        )

    # override this if using other query functions
    def query_file(self, name):
        logging.debug(f"parsing with pandas.read_csv: {name}")
        logging.critical(
            f"{self.sep=}, {self.skiprows=}, {self.header=}, {self.encoding=}, {self.decimal=}"
        )
        data_df = pd.read_csv(
            name,
            sep=self.sep,
            skiprows=self.skiprows,
            header=self.header,
            encoding=self.encoding,
            decimal=self.decimal,
            thousands=self.thousands,
        )
        return data_df
