import logging
import os

import pandas as pd

from cellpy.parameters.internal_settings import get_headers_normal, ATTRS_CELLPYFILE

from cellpy.readers.instruments.mixin import Loader
from cellpy.readers.core import FileID, Cell, check64bit, humanize_bytes
from cellpy.parameters import prms

DEFAULT_CONFIG = {
    "structure": {
        "format": "csv",
        "table_name": None,
        "header_definitions": "labels",
        "comment_chars": ("#", "!"),
        "sep": ";",
        "locate_start_data_by": "line_number",
        "locate_end_data_by": "EOF",
        "locate_vars_by": "key_value_pairs",
        "start_data": 19,
        "header_info_line": 1,
        "start_data_offset": 0,
        "header_info_parse": "in_key",
        "header_info_splitter": ";",
        "file_type_id_line": 0,
        "file_type_id_match": None,
    },
    "variables": {
        "mass": "mass",
        "total_mass": "total_mass",
        "schedule_file": "schedule_file",
        "schedule": "schedule",
        "creator": "operator",
        "loaded_from": "loaded_from",
        "channel_index": "channel_index",
        "channel_number": "channel_number",
        "item_ID": "instrument",
        "test_ID": "test_name",
        "cell_name": "cell",
        "material": "material",
        "counter_electrode": "counter",
        "reference_electrode": "reference",
        "start_datetime": "date",
        "fid_last_modification_time": "last_modified",
        "fid_size": "size",
        "fid_last_accessed": "last_accessed",
    },
    "headers": {
        "data_point_txt": "index",
        "charge_capacity_txt": "charge_capacity",
        "current_txt": "current",
        "cycle_index_txt": "cycle",
        "datetime_txt": "date_stamp",
        "discharge_capacity_txt": "discharge_Capacity",
        "step_index_txt": "step",
        "step_time_txt": "step_time",
        "test_time_txt": "test_time",
        "voltage_txt": "voltage",
    },
    "units": {"current": 0.001, "charge": 0.001, "mass": 0.001, "specific": 1.0},
    "limits": {
        "current_hard": 0.0000000000001,
        "current_soft": 0.00001,
        "stable_current_hard": 2.0,
        "stable_current_soft": 4.0,
        "stable_voltage_hard": 2.0,
        "stable_voltage_soft": 4.0,
        "stable_charge_hard": 0.9,
        "stable_charge_soft": 5.0,
        "ir_change": 0.00001,
    },
}


class CustomLoader(Loader):
    """ Class for loading cell data from custom formatted files.

    The file that contains the description of the custom data file
    should be given by issuing the
    pick_definition_file or given in the config file
    (prms.Instruments.custom_instrument_definitions_file)

    The format of the custom data file should be on the form

    ...
        # comment
        # ...
        variable sep value
        variable sep value
        ...
        header1 sep header2 sep ...
        value1  sep value2  sep ...
        ...

    where sep is either defined in the description file or the
    config file.

    The definition file should use the YAML format and it
    must contain

    xxx
    xxx


    """

    def __init__(self):
        """initiates the class"""

        self.logger = logging.getLogger(__name__)
        self.headers_normal = get_headers_normal()
        self.definition_file = self.pick_definition_file()
        self.units = None
        self.limits = None
        self.headers = None
        self.variables = None
        self.structure = None
        self.parse_definition_file()

    @staticmethod
    def pick_definition_file():
        return prms.Instruments.custom_instrument_definitions_file

    # TODO: @jepe - create yaml file example (from DEFAULT_CONFIG)
    # TODO: @jepe - create yaml file parser
    def parse_definition_file(self):
        if self.definition_file is None:
            logging.info("no definition file for custom format")
            logging.info("using default settings")
            settings = DEFAULT_CONFIG
        else:
            raise NotImplementedError

        self.units = settings["units"]
        self.limits = settings["limits"]
        self.headers = settings["headers"]
        self.variables = settings["variables"]
        self.structure = settings["structure"]

    def get_raw_units(self):
        return self.units

    def get_raw_limits(self):
        return self.limits

    def _find_data_start(self, file_name, sep):
        if self.structure["locate_start_data_by"] != "line_number":
            raise NotImplementedError
        if not self.structure["start_data"] is None:
            return self.structure["start_data"] + self.structure["start_data_offset"]

        else:
            logging.debug("searching for line where data starts")
            header_info_line = self.structure["header_info_line"]
            header_info_parse = self.structure["header_info_parse"]
            header_info_splitter = self.structure["header_info_splitter"]
            header_info_line = self.structure["header_info_line"]

            with open(file_name, "rb") as fp:
                for i, line_ in enumerate(fp):
                    if i == header_info_line:
                        line = line_.strip()
                        line = line.decode()
                        break

            if header_info_parse == "in_key":
                _, v = line.split(header_info_splitter)
            else:
                _, v = line.split(sep)
            v = int(v)
            return v

    def loader(self, file_name, **kwargs):
        new_tests = []
        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return

        # find out strategy (based on structure)
        if self.structure["format"] != "csv":
            raise NotImplementedError

        sep = self.structure.get("sep", prms.Reader.sep)
        if sep is None:
            sep = prms.Reader.sep

        locate_vars_by = self.structure.get("locate_vars_by", "key_value_pairs")
        comment_chars = self.structure.get("comment_chars", ["#", "!"])
        header_row = self.structure.get("start_data", None)
        if header_row is None:
            header_row = self._find_data_start(file_name, sep)

        # parse variables
        var_lines = []
        with open(file_name, "rb") as fp:
            for i, line in enumerate(fp):
                if i < header_row:
                    line = line.strip()
                    try:
                        line = line.decode()
                    except UnicodeDecodeError:
                        logging.debug(
                            "UnicodeDecodeError: " "skipping this line: " f"{line}"
                        )
                    else:
                        if line.startswith(comment_chars):
                            logging.debug(f"Comment: {line}")
                        else:
                            var_lines.append(line)
                else:
                    break

        var_dict = dict()
        if locate_vars_by == "key_value_pairs":
            for line in var_lines:
                parts = line.split(sep)
                try:
                    var_dict[parts[0]] = parts[1]
                except IndexError as e:
                    logging.debug(f"{e}\ncould not split var-value\n{line}")

        else:
            raise NotImplementedError

        data = Cell()
        data.loaded_from = file_name
        fid = self._generate_fid(file_name, var_dict)

        # parsing cellpydata attributes
        for attribute in ATTRS_CELLPYFILE:
            key = self.variables.get(attribute, None)
            # print(f"{attribute} -> {key}")
            if key:
                val = var_dict.pop(key, None)
                if key in ["mass"]:
                    val = float(val)
                # print(f"{attribute}: {val}")
                setattr(data, attribute, val)

        data.raw_data_files.append(fid)

        # setting optional attributes (will be implemented later I hope)
        key = self.variables.get("total_mass", None)
        if key:
            total_mass = var_dict.pop(key, None)
            logging.debug("total_mass is given, but not propagated")

        logging.debug(f"unused vars: {var_dict}")

        raw = self._parse_csv_data(file_name, sep, header_row)
        raw = self._rename_cols(raw)
        raw = self._check_cycleno_stepno(raw)
        data.raw_data_files_length.append(raw.shape[0])
        data.summary = None
        data.raw = raw
        new_tests.append(data)
        return new_tests

    def _parse_csv_data(self, file_name, sep, header_row):
        raw = pd.read_csv(file_name, sep=sep, header=header_row, skip_blank_lines=False)
        return raw

    def _rename_cols(self, raw):
        rename_col_dict = dict()

        for col_def in self.headers:
            new_name = self.headers_normal[col_def]
            old_name = self.headers[col_def]
            if old_name in raw.columns:
                rename_col_dict[old_name] = new_name

        raw = raw.rename(columns=rename_col_dict)
        return raw

    # TODO: @jepe - finalize the _check sub-modules

    def _check_cycleno_stepno(self, raw):
        return raw

    def _convert_to_cellpy_units(self, data):
        return data

    def _check_columns(self, data):
        return data

    def _check_dtypes(self, data):
        return data

    def _generate_fid(self, file_name, var_dict):
        fid = FileID()
        last_modified = var_dict.get(self.variables["fid_last_modification_time"], None)
        size = var_dict.get(self.variables["fid_size"], None)
        last_accessed = var_dict.get(self.variables["fid_last_accessed"], None)

        if any([last_modified, size, last_accessed]):
            fid.name = os.path.abspath(file_name)
            fid.full_name = file_name
            fid.location = os.path.dirname(file_name)

            fid.size = size
            fid.last_modified = last_modified
            fid.last_accessed = last_accessed
            fid.last_info_changed = last_accessed
        else:
            fid.populate(file_name)

        return fid

    def inspect(self, data):
        data = self._convert_to_cellpy_units(data)
        data = self._check_columns(data)
        data = self._check_dtypes(data)
        return data

    def load(self, file_name):
        """Load a raw data-file

        Args:
            file_name (path)

        Returns:
            loaded test
        """

        new_rundata = self.loader(file_name)
        new_rundata = self.inspect(new_rundata)
        return new_rundata


if __name__ == "__main__":
    import pathlib
    from pprint import pprint

    print("running this")
    loader = CustomLoader()
    # loader.pick_definition_file()
    datadir = "/Users/jepe/scripting/cellpy/test_data"
    datadir = pathlib.Path(datadir)
    my_file_name = datadir / "custom_data_001.csv"
    # print(help(loader.get_raw_units))
    # print(help(loader.get_raw_limits))
    # print(f"Trying to load {my_file_name}")
    loader.load(my_file_name)
