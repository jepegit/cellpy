"""Maccor txt data"""
import logging
from pprint import pprint

import pandas as pd

from cellpy.readers.core import FileID, Cell
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.instruments.base import Loader
from cellpy.readers.instruments.configurations import register_configuration
from cellpy import prms

DEBUG_MODE = prms.Reader.diagnostics  # not used

SUPPORTED_MODELS = {"one": "maccor_txt_one", "two": "maccor_txt_two"}


def configuration(name):
    """Register and load model configuration"""
    model_module_name = SUPPORTED_MODELS.get(name, None)
    if model_module_name is None:
        raise Exception(f"the model {name} does not have any defined configuration")
    return register_configuration(name, model_module_name)


class MaccorTxtLoader(Loader):
    """Class for loading data from Maccor txt files."""

    def __init__(self, **kwargs):
        """initiates the MaccorTxtLoader class"""
        model = kwargs.pop("model", prms.Instruments.Maccor.default_model)
        self.format_params = prms.Instruments.Maccor[model]
        self.config_params = configuration(model)

        logging.debug(self.format_params)
        self.sep = kwargs.pop("sep", self.format_params["sep"])
        self.skiprows = kwargs.pop("skiprows", self.format_params["skiprows"])
        self.header = kwargs.pop("header", self.format_params["header"])
        self.encoding = kwargs.pop("encoding", self.format_params["encoding"])
        self.include_aux = kwargs.pop("include_aux", False)
        self.keep_all_columns = kwargs.pop("keep_all_columns", False)
        # self.raw_headers_normal = normal_headers_renaming_dict
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    # TODO: Move this away
    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings"""
        # covered by cellpy at the moment
        return get_headers_normal()

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
        return raw_limits

    def loader(self, name, **kwargs):
        """returns a Cell object with loaded data.

        Loads data from arbin SQL server db.

        Args:
            name (str): name of the file
            kwargs (dict): key-word arguments from raw_loader

        Returns:
            new_tests (list of data objects)
        """
        new_tests = []
        sep = kwargs.get("sep", None)
        if sep is not None:
            self.sep = sep
        data_df = self._query_csv(name)
        if not self.keep_all_columns:
            data_df = data_df[self.config_params.columns_to_keep]

        data = Cell()

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
        data.raw_data_files_length.append(len(data_df))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet

        data = self._post_process(data)
        data = self.identify_last_data_point(data)
        new_tests.append(data)

        return new_tests

    def _post_process(self, data):
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

    def _query_csv(self, name, sep=None, skiprows=None, header=None, encoding=None):
        sep = sep or self.sep
        skiprows = skiprows or self.skiprows
        header = header or self.header
        encoding = encoding or self.encoding
        logging.debug(f"{sep=}, {skiprows=}, {header=}, {encoding=}")
        data_df = pd.read_csv(
            name, sep=sep, skiprows=skiprows, header=header, encoding=encoding
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
        separators = [",", ";", "\t", "|", "\n"]
    logging.debug(f"checking internals of the file {file_name}")

    with open(file_name, "r") as fin:
        lines = []
        for j in range(checking_length_whole):
            line = fin.readline().strip()
            if not line:
                break
            lines.append(line)

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
    return [
        line_number
        for line_number, line in enumerate(first_part)
        if line.count(separator) == number_of_hits
    ][0]


def _find_separator(checking_length, lines, separators):
    separator = None
    number_of_hits = 0
    last_part = lines[checking_length:]
    check_sep = dict()
    for i, v in enumerate(separators):
        check_sep[i] = [line.count(v) for line in last_part]
    unique_sep_counts = {i: set(v) for i, v in check_sep.items()}
    for indx, value in unique_sep_counts.items():
        value_as_list = list(value)
        number_of_hits = value_as_list[0]
        if len(value_as_list) == 1 and number_of_hits > 0:
            separator = separators[indx]
    return separator, number_of_hits


def check_retrieve_file():
    import pathlib

    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"
    data_root = pathlib.Path(r"C:\scripting\cellpy_dev_resources")
    data_dir = data_root / r"2021_leafs_data\Charge-Discharge\Maccor series 4000"
    name = data_dir / "01_UBham_M50_Validation_0deg_01.txt"
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


def check_loader(name=None):
    import matplotlib.pyplot as plt

    if name is None:
        name = check_retrieve_file()

    pd.options.display.max_columns = 100
    # prms.Reader.sep = "\t"

    loader = MaccorTxtLoader(sep="\t")
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
    from cellpy import cellreader
    import matplotlib.pyplot as plt
    import pathlib

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripts\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    print(f"Exists? {name.is_file()}")

    c = cellreader.CellpyData()
    c.set_instrument("maccor_txt", sep="\t")

    c.from_raw(name)
    c.set_mass(1000)

    c.make_step_table()
    c.make_summary()

    raw = c.cell.raw
    steps = c.cell.steps
    summary = c.cell.summary
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
    import cellpy
    import matplotlib.pyplot as plt
    import pathlib

    pd.options.display.max_columns = 100
    datadir = pathlib.Path(
        r"C:\scripting\cellpy_dev_resources\2021_leafs_data\Charge-Discharge\Maccor series 4000"
    )
    name = datadir / "01_UBham_M50_Validation_0deg_01.txt"
    out = pathlib.Path(r"C:\scripting\notebooks\Div")
    print(f"File exists? {name.is_file()}")
    if not name.is_file():
        print(f"could not find {name} ")
        return

    c = cellpy.get(filename=name, instrument="maccor_txt", sep="\t", mass=1.0)

    raw = c.cell.raw
    steps = c.cell.steps
    summary = c.cell.summary
    raw.to_csv(r"C:\scripting\notebooks\Div\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripting\notebooks\Div\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripting\notebooks\Div\trash\summary.csv", sep=";")

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
    # check_loader()
    check_find_delimiter()
    # check_loader_from_outside_with_get()
