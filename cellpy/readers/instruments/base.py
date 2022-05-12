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
    pass


class Loader(AtomicLoad, metaclass=abc.ABCMeta):
    """Main loading class"""

    # TODO: should also include the functions for getting cellpy headers etc
    #  here

    @staticmethod
    @abc.abstractmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        raise NotImplementedError

    @staticmethod
    def get_params(parameter: Union[str, None]) -> dict:
        """Retrieves parameters needed for facilitating working with the instrument without registering it.

        Typically, it should include the raw_ext.

        Return: parameters or a selected parameter
        """
        raise NotImplementedError

    @abc.abstractmethod
    def loader(self, *args, **kwargs) -> list:
        """Loads data into a Cell object and returns it"""
        pass

    @staticmethod
    def identify_last_data_point(data: core.Cell) -> core.Cell:
        """This method is used to find the last record in the data."""
        return core.identify_last_data_point(data)


class AutoLoader(Loader):
    """Main autoload class.

    This class can be sub-classed if you want to make a data-reader for different type of "easily parsed" files
    (for example csv-files). The subclass needs to have at least one
    associated CONFIGURATION_MODULE defined and must have the following attributes as minimum:

        default_model: str = NICK_NAME_OF_DEFAULT_CONFIGURATION_MODULE
        supported_models: dict = SUPPORTED_MODELS

    where SUPPORTED_MODELS is a dictionary with {NICK_NAME : CONFIGURATION_MODULE_NAME}  key-value pairs.
    Remark! the NICK_NAME must be in upper-case!

    It is also possible to set these in a custom pre_init method:

        @classmethod
        def pre_init(cls):
            cls.default_model: str = NICK_NAME_OF_DEFAULT_CONFIGURATION_MODULE
            cls.supported_models: dict = SUPPORTED_MODELS

    or turn off automatic registering of configuration:
        @classmethod
        def pre_init(cls):
            cls.auto_register_config = False  # defaults to True

    During initialisation of the class, if auto_register_config == True,  it will dynamically load the definitions
    provided in the CONFIGURATION_MODULE.py located in the cellpy.readers.instruments.configurations folder/package.

    """

    def __init__(self, *args, **kwargs):
        """Attributes can be set during initialization of the class as **kwargs that are then handled by the
        ``parse_formatter_parameters`` method.

        Remark that some also can be provided as arguments to the ``loader`` method and will then automatically
        be "transparent" to the ``cellpy.get`` function. So if you would like to give the user access to modify
        these arguments, you should implement them in the ``parse_loader_parameters`` method.
        """

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
        self.model = kwargs.pop(
            "model", self.default_model
        )
        if self.auto_register_config:
            self.config_params = self.register_configuration()

        self.name = None
        self._file_path = None

        self.parse_formatter_parameters(**kwargs)

        self.pre_processors = kwargs.pop(
            "pre_processors", self.config_params.pre_processors
        )
        self.post_processors = kwargs.pop(
            "post_processors", self.config_params.post_processors
        )
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
    def query_file(self, file_path:  Union[str, pathlib.Path]) -> pd.DataFrame:
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

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        return self.config_params.raw_units

    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        return self.config_params.raw_limits

    @staticmethod
    def get_headers_aux(raw: pd.DataFrame) -> dict:
        raise NotImplementedError(
            f"missing method in sub-class of TxtLoader: get_headers_aux"
        )

    def _pre_process(self):
        # create a copy of the file and set file_path attribute
        temp_dir = pathlib.Path(tempfile.gettempdir())
        temp_filename = temp_dir / self.name.name
        shutil.copy2(self.name, temp_dir)
        logging.debug(f"tmp file: {temp_filename}")
        self._file_path = temp_filename

        for processor_name in self.pre_processors:
            if self.pre_processors[processor_name]:
                if hasattr(pre_processors, processor_name):
                    logging.critical(f"running pre-processor: {processor_name}")
                    processor = getattr(pre_processors, processor_name)
                    self._file_path = processor(self._file_path)
                else:
                    raise NotImplementedError(
                        f"{processor_name} is not currently supported - aborting!"
                    )

    def loader(self, name: Union[str, pathlib.Path], **kwargs: str) -> List[core.Cell]:
        """returns a Cell object with loaded data.

        Loads data from Maccor txt file (csv-ish).

        Args:
            name (str, pathlib.Path): name of the file.
            kwargs (dict): key-word arguments from raw_loader.

        Returns:
            new_tests (list of data objects)
        """
        self._file_path = pathlib.Path(name)
        self.name = pathlib.Path(name)
        pre_processor_hook = kwargs.pop("pre_processor_hook", None)
        new_tests = []

        if self.pre_processors:
            self._pre_process()

        self.parse_loader_parameters(**kwargs)

        data_df = self.query_file(self._file_path)

        if pre_processor_hook is not None:
            logging.debug("running pre-processing-hook")
            data_df = pre_processor_hook(data_df)

        data = core.Cell()

        # metadata
        meta = self.parse_meta()
        data.loaded_from = name
        data.channel_index = meta.get("channel_index", None)
        data.test_ID = meta.get("test_ID", None)
        data.test_name = meta.get("test_name", None)
        data.channel_number = meta.get("channel_number", None)
        data.creator = meta.get("creator", None)
        data.item_ID = meta.get("item_ID", None)
        data.schedule_file_name = meta.get("schedule_file_name", None)
        data.start_datetime = meta.get("start_datetime", None)

        # Generating a FileID project:
        fid = core.FileID(name)
        data.raw_data_files.append(fid)

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
        new_tests.append(data)
        return new_tests

    def validate(self, data: core.Cell) -> core.Cell:
        """validation of the loaded data, should raise an appropriate exception if it fails."""

        logging.debug(f"no validation of defined in this sub-class of TxtLoader")
        return data

    def parse_meta(self) -> dict:
        """method that parses the data for meta-data (e.g. start-time, channel number, ...)"""

        logging.debug(
            f"no parsing method for meta-data defined in this sub-class of TxtLoader"
        )
        return dict()

    # copy-paste from custom loader in an effort to combine the classes
    # def _parse_xls_data(self, file_name):
    #     sheet_name = self.structure["table_name"]
    #
    #     raw_frame = pd.read_excel(
    #         file_name, engine="xlrd", sheet_name=None
    #     )  # TODO: replace this with pd.ExcelReader
    #     matching = [s for s in raw_frame.keys() if s.startswith(sheet_name)]
    #     if matching:
    #         return raw_frame[matching[0]]
    #
    # def _parse_xlsx_data(self, file_name):
    #     sheet_name = self.structure["table_name"]
    #     raw_frame = pd.read_excel(
    #         file_name, engine="openpyxl", sheet_name=None
    #     )  # TODO: replace this with pd.ExcelReader
    #     matching = [s for s in raw_frame.keys() if s.startswith(sheet_name)]
    #     if matching:
    #         return raw_frame[matching[0]]
    #
    # def _parse_csv_data(self, file_name, sep, header_row):
    #     raw = pd.read_csv(file_name, sep=sep, header=header_row, skip_blank_lines=False)
    #     return raw

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

    The subclass of a TxtLoader gets its information by loading model specifications from its respective module
    (``cellpy.readers.instruments.configurations.<module>``) or configuration file (yaml).

    Remark that if you implement automatic loading of the formatter, the module / yaml-file must include all
    the required formatter parameters (sep, skiprows, header, encoding, decimal, thousands).

    If you need more flexibility, try using the CustomTxtLoader or subclass directly from AutoLoader or Loader.

    Constructor **kwargs:
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

    Module - loader **kwargs:
        sep (str): the delimiter (also works as a switch to turn on/off automatic detection of delimiter and
            start of data (skiprows)).

        """

    # override this if needed
    def parse_loader_parameters(self, **kwargs):
        sep = kwargs.get("sep", None)
        if sep is not None:
            self.sep = sep
        if self.sep is None:
            self._auto_formatter()

    # override this if needed
    def parse_formatter_parameters(self, **kwargs):
        if not self.config_params.formatters:
            # Setting defaults if formatter is not loaded
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

    def _auto_formatter(self):
        separator, first_index = find_delimiter_and_start(
            self.name,
            separators=None,
            checking_length_header=100,
            checking_length_whole=200,
        )
        self.encoding = "UTF-8"  # consider adding a find_encoding function
        self.sep = separator
        self.skiprows = first_index - 1  # consider adding a find_rows_to_skip function
        self.header = 0  # consider adding a find_header function

        logging.critical(
            f"auto-formatting:\n  {self.sep=}\n  {self.skiprows=}\n  {self.header=}\n  {self.encoding=}\n"
        )

    # override this if using other query functions
    def query_file(self, name):
        logging.debug(f"parsing with pandas.read_csv: {name}")
        logging.critical(f"{self.sep=}, {self.skiprows=}, {self.header=}, {self.encoding=}, {self.decimal=}")
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
