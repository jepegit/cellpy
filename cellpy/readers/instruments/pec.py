"""pec csv-type data files"""
import os
from dateutil.parser import parse
import logging
import warnings
import numpy as np

import pandas as pd

from cellpy.readers.core import FileID, Cell, humanize_bytes
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.mixin import Loader

pec_headers_normal = dict()

pec_headers_normal["step_index_txt"] = "Step"
pec_headers_normal["cycle_index_txt"] = "Cycle"
pec_headers_normal["test_time_txt"] = "Total_Time_Seconds"
pec_headers_normal["step_time_txt"] = "Step_Time_Seconds"
pec_headers_normal["datetime_txt"] = "Real_Time"
pec_headers_normal["voltage_txt"] = "Voltage_mV"
pec_headers_normal["current_txt"] = "Current_mA"
pec_headers_normal["charge_capacity_txt"] = "Charge_Capacity_mAh"
pec_headers_normal["discharge_capacity_txt"] = "Discharge_Capacity_mAh"
pec_headers_normal["charge_energy_txt"] = "Charge_Capacity_mWh"
pec_headers_normal["discharge_energy_txt"] = "Discharge_Capacity_mWh"
pec_headers_normal["internal_resistance_txt"] = "Internal_Resistance_1_mOhm"
pec_headers_normal["test_id_txt"] = "Test"


# TODO: better reading of first part of the file (comments and headers)
#  1. find the units



#  2. find user-defined variables
#  3. find units
# Hei
# Og hei til deg!
# og hei


class PECLoader(Loader):
    """Main loading class"""

    def __init__(self):
        self.headers_normal = (
            get_headers_normal()
        )  # should consider to move this to the Loader class
        self.current_chunk = 0  # use this to set chunks to load
        self.pec_data = None
        self.pec_log = None
        self.pec_settings = None
        self.variable_header_keywords = ['Voltage (V)', 'Current (A)']  # The unit of these will be read from file
        self.last_header_line = "#END RESULTS CHECK\n" # This is the last line of the header, used to find the length
        self.number_of_header_lines = self._find_header_length(filename)  # Number of header lines is not constant
        self.filename = None
        self.cellpy_headers = (
            get_headers_normal()
        )  # should consider to move this to the Loader class

    #@staticmethod
    #def _get_pec_units():
    #    pec_units = dict()
    #    pec_units["voltage"] = 0.001  # V
    #    pec_units["current"] = 0.001  # A
    #    pec_units["charge"] = 0.001  # Ah
    #    pec_units["mass"] = 0.001  # g
    #    pec_units["energy"] = 0.001  # Wh

    #    return pec_units

    def _get_pec_units(self):  # Fetches units from a csv file
        # Mapping prefixes to values
        prefix = {
            'µ': 10 ** -6,
            'm': 10 ** -3,
            '': 1
        }

        # Adding the non-variable units to the return value
        pec_units = {
            'charge': 0.001,  # Ah
            'mass': 0.001,  # g
            'energy': 0.001  # Wh
        }

        # A list with all the variable keywords without any prefixes, used as search terms
        header = self.variable_header_keywords

        data = pd.read_csv(self.filename, skiprows=self.number_of_header_lines, nrows=1)

        # Searching for the prefix for all the variable units
        for item in data.keys():
            for unit in header:
                x = unit.find('(') - len(unit)
                if unit[:x + 1] in item:
                    y = item[x].replace('(', '')
                    # Adding units conversion factor to return value
                    if header.index(unit) == 0:
                        pec_units['voltage'] = prefix.get(y)
                    elif header.index(unit) == 1:
                        pec_units['current'] = prefix.get(y)

        return pec_units

    def _get_pec_times(self):
        # Mapping units to their conversion values
        units = {
            '(Hours in hh:mm:ss.xxx)': self.timestamp_to_seconds,
            '(Decimal Hours)': 3600,
            '(Minutes)': 60,
            '(Seconds)': 1

        }

        data = pd.read_csv(filename, skiprows=find_header_length(filename), nrows=1)
        pec_times = dict()

        # Adds the time variables and their units to the pec_times dictonary return value
        for item in data.keys():
            for unit in units:
                if unit in item:
                    x = item.find('(')
                    var = item[:x - 1].lower().replace(' ', '_')
                    its_unit = item[x:]
                    pec_times[var] = units.get(its_unit)

        return pec_times

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """

        raw_units = dict()
        raw_units["voltage"] = 1.0  # V
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        raw_units["energy"] = 1.0  # Wh
        raw_units["total_time"] = 1.0  # s
        raw_units["step_time"] = 1.0  # s

        return raw_units

    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        warnings.warn("raw limits have not been subject for testing yet")
        raw_limits = dict()
        raw_limits["current_hard"] = 0.1  # There is a bug in PEC
        raw_limits["current_soft"] = 1.0
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 2.0
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def loader(self, file_name, bad_steps=None, **kwargs):
        new_tests = []
        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return None

        self.filename = file_name
        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        logging.debug(txt)

        data = Cell()
        fid = FileID(file_name)

        # div parameters and information (probably load this last)
        test_no = 1
        data.cell_no = test_no
        data.loaded_from = file_name

        # some overall prms
        data.channel_index = None
        data.channel_number = None
        data.creator = None
        data.item_ID = None
        data.schedule_file_name = None
        data.test_ID = None
        data.test_name = None
        data.raw_data_files.append(fid)

        # --------- read raw-data (normal-data) -------------------------

        self._load_pec_data(file_name, bad_steps)
        data.start_datetime = self.pec_settings["start_time"]
        length_of_test = self.pec_data.shape[0]
        logging.debug(f"length of test: {length_of_test}")

        logging.debug("renaming columns")
        self._rename_headers()
        self._convert_units()

        data.raw = self.pec_data

        data.raw_data_files_length.append(length_of_test)
        new_tests.append(data)

        return new_tests

    def _load_pec_data(self, file_name, bad_steps):
        number_of_header_lines = self.number_of_header_lines

        # ----------------- reading the data ---------------------
        df = pd.read_csv(file_name, skiprows=number_of_header_lines)

        # get rid of unnamed columns
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        # get rid of spaces, parenthesis, and the deg-sign
        new_column_headers = {
            c: c.replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("°", "")
            .replace(r"%", "pct")
            for c in df.columns
        }
        df.rename(columns=new_column_headers, inplace=True)

        # add missing columns
        df.insert(0, self.headers_normal.data_point_txt, range(len(df)))
        df[self.headers_normal.sub_step_index_txt] = 0
        df[self.headers_normal.sub_step_time_txt] = 0

        self.pec_data = df

        # ----------------  reading the parameters ---------------
        with open(file_name, "r") as ofile:
            counter = 0
            lines = []
            for line in ofile:
                counter += 1
                if counter > number_of_header_lines:
                    break
                lines.append(line)
        self._extract_variables(lines)

    def _extract_variables(self, lines):
        header_comments = dict()
        comment_loop = False
        for line_number, line in enumerate(lines):

            if line.startswith("#"):
                if not comment_loop:
                    comment_loop = True
                else:
                    comment_loop = False

            else:
                if not comment_loop:
                    parts = line.split(",")
                    variable = parts[0].strip()
                    variable = variable.strip(":")
                    variable = variable.replace(" ", "_")
                    try:
                        value = parts[1].strip()
                    except IndexError:
                        value = None

                    if not value:
                        value = np.nan
                    header_comments[variable] = value
        logging.debug(" Headers Dict ")
        logging.debug(header_comments)

        headers = dict()

        start_time = parse(header_comments["Start_Time"])
        end_time = parse(header_comments["End_Time"])

        headers["start_time"] = start_time
        headers["end_time"] = end_time
        headers["test_regime_name"] = header_comments["TestRegime_Name"]

        self.pec_settings = headers

    def _rename_headers(self):
        logging.debug("Trying to rename the columns")
        # logging.debug("Current columns:")
        # logging.debug(self.pec_data.columns)
        # logging.debug("Rename to:")
        # logging.debug(self.headers_normal)

        for key in pec_headers_normal:
            self._rename_header(key, pec_headers_normal[key])

        # logging.debug("New cols:")
        # logging.debug(self.pec_data.columns)

    def _convert_units(self):
        logging.debug("Trying to convert all data into correct units")
        logging.debug("- dtypes")
        self.pec_data[self.headers_normal.datetime_txt] = pd.to_datetime(
            self.pec_data[self.headers_normal.datetime_txt]
        )

        self.pec_data["Position_Start_Time"] = pd.to_datetime(
            self.pec_data["Position_Start_Time"]
        )

        self.pec_data["Rack"] = self.pec_data["Rack"].astype("category")

        logging.debug("- cellpy units")
        pec_units = self._get_pec_units()
        pec_times = self._get_pec_times()
        raw_units = self.get_raw_units()

        _v = pec_units["voltage"] / raw_units["voltage"]
        _i = pec_units["current"] / raw_units["current"]
        _c = pec_units["charge"] / raw_units["charge"]
        _w = pec_units["energy"] / raw_units["energy"]
        _tt = pec_times["total_time"] / raw_units["total_time"]
        _st = pec_times["step_time"] / raw_units["step_time"]

        v_txt = self.headers_normal.voltage_txt
        i_txt = self.headers_normal.current_txt

        self.pec_data[v_txt] *= _v
        self.pec_data[i_txt] *= _i

        self.pec_data[self.headers_normal.charge_capacity_txt] *= _c
        self.pec_data[self.headers_normal.discharge_capacity_txt] *= _c
        self.pec_data[self.headers_normal.charge_energy_txt] *= _w
        self.pec_data[self.headers_normal.discharge_energy_txt] *= _w

    def _rename_header(self, h_old, h_new):
        try:
            self.pec_data.rename(
                columns={h_new: self.cellpy_headers[h_old]}, inplace=True
            )
        except KeyError as e:
            logging.info(f"Problem during conversion to cellpy-format ({e})")

    def _find_header_length(self):
        skiprows = 0
        with open(self.filename, 'r') as header:
            for line in header:
                skiprows += 1
                if line == self.last_header_line:
                    break

        return skiprows

    @staticmethod
    def timestamp_to_seconds(timestamp):
        return (datetime.datetime.strptime(timestamp, "%H:%M:%S.%f") -
                datetime.datetime(1900, 1, 1)).total_seconds()


if __name__ == "__main__":
    pass
