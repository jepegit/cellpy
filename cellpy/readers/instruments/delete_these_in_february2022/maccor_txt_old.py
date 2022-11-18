"""Maccor txt data"""
import logging
import pathlib
import shutil
import sys
import tempfile
from pprint import pprint
from typing import Union

import pandas as pd

from cellpy import prms
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import Data, FileID
from cellpy.readers.instruments.base import BaseLoader
from cellpy.readers.instruments.configurations import (
    ModelParameters,
    register_configuration_from_module,
)
from cellpy.readers.instruments.processors import post_processors, pre_processors

DEBUG_MODE = prms.Reader.diagnostics  # not used

SUPPORTED_MODELS = {
    "zero": "maccor_txt_zero",
    "one": "maccor_txt_one",
    "two": "maccor_txt_two",
}


def configuration(name) -> ModelParameters:
    """Register and load model configuration"""
    model_module_name = SUPPORTED_MODELS.get(name, None)
    if model_module_name is None:
        raise Exception(f"the model {name} does not have any defined configuration")
    return register_configuration_from_module(name, model_module_name)


# TODO: create a class that is a general CSV loader that can be subclassed
class MaccorTxtLoader(BaseLoader):
    """Class for loading data from Maccor txt files."""

    def __init__(self, **kwargs):
        """initiates the MaccorTxtLoader class.

        Several attributes can be set during initialization of the class as **kwargs. Remark that some also
        can be provided as arguments to the `loader` method and will then automatically be "transparent"
        to the `cellpy.get` function. So if you would like to give the user access to modify these arguments,
        you should implement them in the `loader` method.

        Key word attributes:
            model (str): short name of the (already implemented) sub-model.
            sep (str): delimiter.
            skiprows (int): number of lines to skip.
            header (int): number of the header lines.
            encoding (str): encoding, defaults 'to ISO--8859-1'.
            decimal (str): character used for decimal in the raw data, defaults to '.'.
            processors (dict): pre-processing steps to take (before loading with pandas).
            post_processors (dict): post-processing steps to make after loading the data, but before
                returning them to the caller.
            include_aux (bool): also parse so-called auxiliary columns / data. Defaults to False.
            keep_all_columns (bool): load all columns, also columns that are not 100% necessary for `cellpy` to work.
                Remark that the configuration settings for the sub-model must include a list of column header names
                that should be kept if keep_all_columns is False (default).
        """
        model = kwargs.pop("model", prms.Instruments.Maccor.default_model)
        self.config_params = configuration(model)
        self.name = None
        self._file_path = None

        if not self.config_params.formatters:
            # check for "over-rides" from arguments in class initialization
            self.sep = kwargs.pop("sep", None)
            self.skiprows = kwargs.pop("skiprows", 3)
            self.header = kwargs.pop("header", 0)
            self.encoding = kwargs.pop("encoding", "ISO-8859-1")
            self.decimal = kwargs.pop("decimal", "..")

        else:
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

        self.pre_processors = kwargs.pop(
            "../processors", self.config_params.pre_processors
        )
        self.include_aux = kwargs.pop("include_aux", False)
        self.keep_all_columns = kwargs.pop("keep_all_columns", False)
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings"""
        headers = HeaderDict()
        for col in df.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()

        return headers

    # not updated yet
    # Should be moved to self.config_params and implemented in the parent class
    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        # return self.config_params.raw_units
        return raw_units

    # not updated yet
    # Should be moved to self.config_params and implemented in the parent class
    @staticmethod
    def get_raw_limits():
        """returns a dictionary with resolution limits"""
        raw_limits = dict()
        raw_limits["current_hard"] = 0.000_000_000_000_1
        raw_limits["current_soft"] = 0.000_01
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 0.001
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        # return self.config_params.raw_limits
        return raw_limits

    def _auto_formatter(self):
        separator, first_index = find_delimiter_and_start(
            self.name,
            separators=None,
            checking_length_header=100,
            checking_length_whole=200,
        )
        self.encoding = "ISO-8859-1"  # consider adding a find_encoding function
        self.sep = separator
        self.skiprows = first_index - 1  # consider adding a find_rows_to_skip function
        self.header = 0  # consider adding a find_header function

        logging.critical(
            f"auto-formatting:\n  {self.sep=}\n  {self.skiprows=}\n  {self.header=}\n  {self.encoding=}\n"
        )

    def _pre_process(self):
        # create a copy of the file and set file_path attribute
        temp_dir = pathlib.Path(tempfile.gettempdir())
        temp_filename = temp_dir / self.name.name
        shutil.copy2(self.name, temp_dir)
        logging.debug(f"tmp file: {temp_filename}")
        self._file_path = temp_filename

        # pre-processors to run self.pre_processors
        # pre-processors available: pre_processors

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

    def loader(self, name: Union[str, pathlib.Path], **kwargs: str) -> list:
        """returns a Cell object with loaded data.

        Loads data from Maccor txt file (csv-ish).

        Args:
            name (str, pathlib.Path): name of the file.
            kwargs (dict): key-word arguments from raw_loader.

        **kwargs:
            sep (str): the delimiter (also works as a switch to turn on/off automatic detection of delimiter and
                start of data (skiprows).

        Returns:
            new_tests (list of data objects)
        """
        self._file_path = pathlib.Path(name)
        self.name = pathlib.Path(name)
        new_tests = []
        sep = kwargs.get("sep", None)

        if self.pre_processors:
            self._pre_process()
        if sep is not None:
            self.sep = sep
        if self.sep is None:
            self._auto_formatter()

        data_df = self._query_csv(self._file_path)
        if not self.keep_all_columns:
            data_df = data_df[self.config_params.columns_to_keep]

        data = Data()

        # metadata is unfortunately not available for csv dumps
        data.loaded_from = name
        data.channel_index = None
        data.test_ID = None
        data.test_name = name  # should fix this
        data.channel_number = None
        data.creator = None
        data.item_ID = None
        data.schedule_file_name = None
        data.start_datetime = None

        # Generating a FileID project:
        fid = FileID(name)
        data.raw_data_files.append(fid)

        data.raw = data_df
        # data.raw.to_clipboard()
        data.raw_data_files_length.append(len(data_df))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet
        data = self._post_process(data)
        data = self.identify_last_data_point(data)
        new_tests.append(data)

        return new_tests

    def _post_process(self, data):
        # TODO: implement post_processor methodology from processors
        #  (similar as pre-processing)
        split_caps = True
        split_current = True
        set_index = True
        rename_headers = True
        set_cycle_number_not_zero = True
        convert_date_time_to_datetime = True
        convert_step_time_to_timedelta = True
        convert_test_time_to_timedelta = True
        if rename_headers:
            columns = {}
            for key in self.cellpy_headers_normal:

                if key in self.config_params.normal_headers_renaming_dict:

                    old_header = self.config_params.normal_headers_renaming_dict[key]
                    new_header = self.cellpy_headers_normal[key]
                    # print(f"renaming {old_header} to {new_header}")
                    columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)

            if self.include_aux:
                new_aux_headers = self.get_headers_aux(data.raw)
                data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

            data.raw.rename(
                index=str,
                columns=self.config_params.not_implemented_in_cellpy_yet_renaming_dict,
                inplace=True,
            )

        if split_current:
            data.raw = current_splitter(data.raw, self.config_params.states)

        if split_caps:
            data.raw = capacity_splitter(data.raw, self.config_params.states)

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(hdr_data_point, drop=False)

        if set_cycle_number_not_zero:
            data.raw[self.cellpy_headers_normal.cycle_index_txt] += 1

        hdr_date_time = self.cellpy_headers_normal.datetime_txt
        if convert_date_time_to_datetime:
            data.raw[hdr_date_time] = pd.to_datetime(data.raw[hdr_date_time])

        if convert_step_time_to_timedelta:
            hdr_step_time = self.cellpy_headers_normal.step_time_txt
            data.raw[hdr_step_time] = pd.to_timedelta(
                data.raw[hdr_step_time]
            ).dt.total_seconds()

        if convert_test_time_to_timedelta:
            hdr_test_time = self.cellpy_headers_normal.test_time_txt
            x = pd.to_timedelta(data.raw[hdr_test_time])
            data.raw[hdr_test_time] = x.dt.total_seconds()

        data.start_datetime = data.raw[hdr_date_time].iat[0]

        return data

    def _query_csv(
        self, name, sep=None, skiprows=None, header=None, encoding=None, decimal=None
    ):
        logging.debug(f"parsing with pandas.read_csv: {name}")
        sep = sep or self.sep
        skiprows = skiprows or self.skiprows
        header = header or self.header
        encoding = encoding or self.encoding
        decimal = decimal or self.decimal
        logging.critical(f"{sep=}, {skiprows=}, {header=}, {encoding=}, {decimal=}")
        data_df = pd.read_csv(
            name,
            sep=sep,
            skiprows=skiprows,
            header=header,
            encoding=encoding,
            decimal=decimal,
        )
        return data_df


def state_splitter(
    raw,
    base_col_name="charge_capacity",
    n_charge=1,
    n_discharge=1,
    new_col_name_charge="charge_capacity",
    new_col_name_discharge="discharge_capacity",
    temp_col_name_charge="tmp_charge",
    temp_col_name_discharge="tmp_discharge",
    states=None,
):
    """Split states.

    Args:
        raw: the raw data dataframe
        base_col_name: what column to split
        n_charge: sign of charge (e.g. 1 for positive)
        n_discharge: sign of discharge (e.g. -1 for negative)
        new_col_name_charge: str
        new_col_name_discharge: str
        temp_col_name_charge: str
        temp_col_name_discharge: str
        states: dictionary defining the state identification character/string

    Returns: raw data

    """
    headers = get_headers_normal()
    cycle_index_hdr = headers["cycle_index_txt"]
    data_point = headers["data_point_txt"]
    if states is None:
        states = {
            "column_name": "State",
            "charge_keys": ["C"],
            "discharge_keys": ["D"],
            "rest_keys": ["R"],
        }
    state_column = states["column_name"]
    charge_keys = states["charge_keys"]
    rest_keys = states["rest_keys"]
    discharge_keys = states["discharge_keys"]

    raw[temp_col_name_charge] = 0
    if temp_col_name_charge != temp_col_name_discharge:
        raw[temp_col_name_discharge] = 0

    cycle_numbers = raw[cycle_index_hdr].unique()
    # cell_type = prms.Reader.cycle_mode
    good_cycles = []
    bad_cycles = []
    for i in cycle_numbers:
        try:
            charge = raw.loc[
                (raw[state_column].isin(charge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            discharge = raw.loc[
                (raw[state_column].isin(discharge_keys)) & (raw[cycle_index_hdr] == i),
                [data_point, base_col_name],
            ]

            if not charge.empty:
                charge_last_index, charge_last_val = charge.iloc[-1]
                raw[temp_col_name_charge].update(n_charge * charge[base_col_name])

                raw.loc[
                    (raw[data_point] > charge_last_index) & (raw[cycle_index_hdr] == i),
                    temp_col_name_charge,
                ] = charge_last_val

            if not discharge.empty:
                (discharge_last_index, discharge_last_val) = discharge.iloc[-1]
                raw[temp_col_name_discharge].update(
                    n_discharge * discharge[base_col_name]
                )

                raw.loc[
                    (raw[data_point] > discharge_last_index)
                    & (raw[cycle_index_hdr] == i),
                    temp_col_name_discharge,
                ] = discharge_last_val

            good_cycles.append(i)
        except Exception:
            bad_cycles.append(i)
    if bad_cycles:
        logging.critical(f"The data contains bad cycles: {bad_cycles}")

    raw[new_col_name_charge] = raw[temp_col_name_charge]
    raw = raw.drop([temp_col_name_charge], axis=1)
    if temp_col_name_charge != temp_col_name_discharge:
        raw[new_col_name_discharge] = raw[temp_col_name_discharge]
        raw = raw.drop([temp_col_name_discharge], axis=1)
    return raw


def current_splitter(raw, states):
    """Split current into positive and negative"""
    raw.to_clipboard()
    headers = get_headers_normal()
    return state_splitter(
        raw,
        base_col_name="current",
        n_charge=1,
        n_discharge=-1,
        temp_col_name_charge="tmp_charge",
        new_col_name_charge=headers["current_txt"],
        new_col_name_discharge=headers["current_txt"],
        temp_col_name_discharge="tmp_charge",
        states=states,
    )


def capacity_splitter(raw, states):
    """split capacity into charge and discharge"""
    headers = get_headers_normal()
    return state_splitter(
        raw,
        base_col_name="charge_capacity",
        n_charge=1,
        n_discharge=1,
        new_col_name_charge=headers["charge_capacity_txt"],
        new_col_name_discharge=headers["discharge_capacity_txt"],
        temp_col_name_charge="tmp_charge",
        temp_col_name_discharge="tmp_discharge",
        states=states,
    )


def find_delimiter_and_start(
    file_name,
    separators=None,
    checking_length_header=100,
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

    with open(file_name, "r") as fin:
        lines = []
        for j in range(checking_length_whole):
            line = fin.readline()
            if not line:
                break
            lines.append(line.strip())

    separator, number_of_hits = _find_separator(
        checking_length_whole - checking_length_header, lines, separators
    )

    if separator is not None:
        first_index = _find_first_line_whit_delimiter(
            checking_length_header, lines, number_of_hits, separator
        )
        logging.debug(f"First line with delimiter: {first_index}")
        return separator, first_index
    else:
        raise IOError(f"could not decide delimiter in {file_name}")


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

    for indx, value in unique_sep_counts.items():
        value_as_list = list(value)
        number_of_hits = value_as_list[0]
        if len(value_as_list) == 1 and number_of_hits > 0:
            separator = separators[indx]
            break

    return separator, number_of_hits


def check_retrieve_file(n=1):
    import pathlib

    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"
    data_root = pathlib.Path(r"C:\scripting\cellpy_dev_resources")
    data_dir = data_root / r"2021_leafs_data\Charge-Discharge\Maccor series 4000"
    if n == 2:
        name = data_dir / "KIT-Full-cell-PW-HC-CT-cell016.txt"
    else:
        name = data_dir / "01_UBham_M50_Validation_0deg_01.txt"
    print(name)
    print(f"Exists? {name.is_file()}")
    if name.is_file():
        return name
    else:
        raise IOError(f"could not locate the file {name}")


def check_find_delimiter():
    file_name = check_retrieve_file()
    separator, first_index = find_delimiter_and_start(file_name)
    if separator == "\t":
        sep = "TAB"
    elif separator == " ":
        sep = "SPACE"
    else:
        sep = separator
    print(f"Found delimiter ({sep}) and start line {first_index} in {file_name}")


def check_dev_loader(name=None, model=None):
    if name is None:
        name = check_retrieve_file()

    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"

    sep = "\t"
    loader1 = MaccorTxtLoader(sep=sep, model=model)
    loader2 = MaccorTxtLoader(model="one")
    loader3 = MaccorTxtLoader(model="zero")
    loader4 = MaccorTxtLoader(model="zero")
    dd = loader1.loader(name)
    dd = loader2.loader(name)
    dd = loader3.loader(name)
    dd = loader4.loader(name)
    raw = dd[0].raw
    print(len(raw))


def check_dev_loader2(name=None, model=None, sep=None, number=2):
    if name is None:
        name = check_retrieve_file(number)

    pd.options.display.max_columns = 100

    if sep is not None and sep != "none":
        loader3 = MaccorTxtLoader(sep=sep, model=model)
    elif sep == "none":
        loader3 = MaccorTxtLoader(sep=None, model=model)
    else:
        loader3 = MaccorTxtLoader(model=model)

    dd = loader3.loader(name)

    raw = dd[0].raw
    print(len(raw))
    print(raw)


def check_loader(name=None, number=1, model="one"):
    import matplotlib.pyplot as plt

    if name is None:
        name = check_retrieve_file(number)
    print(name)
    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"

    loader = MaccorTxtLoader(sep="\t", model=model)
    dd = loader.loader(name)
    raw = dd[0].raw
    raw.plot(x="data_point", y="current", title="current vs data-point")
    raw.plot(
        x="data_point",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs data-point",
    )
    raw.plot(
        x="test_time",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs test-time",
    )
    raw.plot(
        x="step_time",
        y=["charge_capacity", "discharge_capacity"],
        title="capacity vs step-time",
    )
    print(raw.head())
    plt.show()


def check_loader_from_outside():
    # NOT EDITED YET!!!
    import pathlib

    import matplotlib.pyplot as plt

    from cellpy import cellreader

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripts\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    print(f"Exists? {name.is_file()}")

    c = cellreader.CellpyCell()
    c.set_instrument("maccor_txt", sep="\t")

    c.from_raw(name)
    c.set_mass(1000)

    c.make_step_table()
    c.make_summary()

    raw = c.data.raw
    steps = c.data.steps
    summary = c.data.summary
    raw.to_csv(r"C:\scripts\notebooks\Div\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripts\notebooks\Div\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripts\notebooks\Div\trash\summary.csv", sep=";")

    fig_1, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 10))
    raw.plot(x="test_time", y="voltage", ax=ax1)
    raw.plot(x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3)
    raw.plot(x="test_time", y="current", ax=ax2)

    n = c.get_number_of_cycles()
    print(f"number of cycles: {n}")

    cycle = c.get_cap(1, method="forth-and-forth")
    print(cycle.head())

    fig_2, (ax4, ax5, ax6) = plt.subplots(1, 3)
    cycle.plot(x="capacity", y="voltage", ax=ax4)
    s = c.get_step_numbers()
    t = c.sget_timestamp(1, s[1])
    v = c.sget_voltage(1, s[1])
    steps = c.sget_step_numbers(1, s[1])

    print("step numbers:")
    print(s)
    print("sget step numbers:")
    print(steps)
    print("\ntesttime:")
    print(t)
    print("\nvoltage")
    print(v)

    ax5.plot(t, v, label="voltage")
    ax6.plot(t, steps, label="steps")

    fig_3, (ax7, ax8) = plt.subplots(2, sharex=True)
    raw.plot(x="test_time", y="voltage", ax=ax7)
    raw.plot(x="test_time", y="step_index", ax=ax8)

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


def check_loader_from_outside_with_get():
    import pathlib

    import matplotlib.pyplot as plt

    import cellpy

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripting\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripting\trash")
    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    c = cellpy.get(filename=name, instrument="maccor_txt", sep="\t", mass=1.0)

    raw = c.data.raw
    steps = c.data.steps
    summary = c.data.summary

    raw.to_csv(r"C:\scripting\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripting\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripting\trash\summary.csv", sep=";")

    fig_1, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 10))
    raw.plot(x="test_time", y="voltage", ax=ax1)
    raw.plot(x="test_time", y=["charge_capacity", "discharge_capacity"], ax=ax3)
    raw.plot(x="test_time", y="current", ax=ax2)

    n = c.get_number_of_cycles()
    print(f"number of cycles: {n}")

    cycle = c.get_cap(1, method="forth-and-forth")
    print(cycle.head())

    fig_2, (ax4, ax5, ax6) = plt.subplots(1, 3)
    cycle.plot(x="capacity", y="voltage", ax=ax4)
    s = c.get_step_numbers()
    t = c.sget_timestamp(1, s[1])
    v = c.sget_voltage(1, s[1])
    steps = c.sget_step_numbers(1, s[1])

    print("step numbers:")
    print(s)
    print("sget step numbers:")
    print(steps)
    print("\ntesttime:")
    print(t)
    print("\nvoltage")
    print(v)

    ax5.plot(t, v, label="voltage")
    ax6.plot(t, steps, label="steps")

    fig_3, (ax7, ax8) = plt.subplots(2, sharex=True)
    raw.plot(x="test_time", y="voltage", ax=ax7)
    raw.plot(x="test_time", y="step_index", ax=ax8)

    plt.legend()
    plt.show()

    outfile = out / "test_out"
    c.save(outfile)


if __name__ == "__main__":
    # check_dev_loader2(model="two")
    check_loader(number=2, model="two")
    # check_find_delimiter()
    # check_loader_from_outside_with_get()
