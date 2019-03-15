"""pec csv-type data files"""
import os
from dateutil.parser import parse
import tempfile
import shutil
import logging
import platform
import warnings
import numpy as np

import pandas as pd

from cellpy.readers.core import FileID, DataSet, \
    check64bit, humanize_bytes, doc_inherit
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy.parameters import prms


class PECLoader(Loader):
    """Main loading class"""

    def __init__(self):
        self.headers_normal = get_headers_normal()  # should consider to move this to the Loader class
        self.current_chunk = 0  # use this to set chunks to load
        self.pec_data = None
        self.pec_log = None
        self.pec_settings = None
        self.number_of_header_lines = 32
        self.cellpy_headers = get_headers_normal()  # should consider to move this to the Loader class

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raw_units = dict()
        raw_units["voltage"] = 0.001  # V  # TODO: not used yet (so the V column is converted during loading)
        raw_units["current"] = 0.001  # A
        raw_units["charge"] = 0.001  # Ah
        raw_units["mass"] = 0.001  # g
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
        raw_limits["current_hard"] = 0.0000000000001
        raw_limits["current_soft"] = 0.00001
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

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        logging.debug(txt)

        data = DataSet()
        fid = FileID(file_name)

        # div parameters and information (probably load this last)
        test_no = 1
        data.test_no = test_no
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

        # ---------  stats-data (summary-data) -------------------------
        summary_df = self._create_summary_data()

        if summary_df.empty:
            txt = "\nCould not find any summary (stats-file)!"
            txt += " (summary_df.empty = True)"
            txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
            warnings.warn(txt)

        data.dfsummary = summary_df
        data.dfdata = self.pec_data

        data.raw_data_files_length.append(length_of_test)
        new_tests.append(data)

        print("No I should load a file")
        print("but I am not ready yet")

        raise NotImplementedError

        return new_tests

    def _load_pec_data(self, file_name, bad_steps):
        number_of_header_lines = self.number_of_header_lines

        # ----------------- reading the data ---------------------
        df = pd.read_csv(file_name, skiprows=number_of_header_lines)
        # get rid of spaces, parenthesis, and the deg-sign
        new_column_headers = {
            c: c.replace(" ", "_").replace("(", "").replace(")", "").replace("°", "").replace(r"%", "pct")
            for c in df.columns
        }
        df.rename(columns=new_column_headers, inplace=True)

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
            # print(line.strip())

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
        logging.debug("Current columns:")
        logging.debug(self.pec_data.columns)
        logging.debug("Rename to:")
        logging.debug(self.headers_normal)
        # CONTINUE FROM HERE

        self._rename_header("frequency_txt", "freq")

        raise NotImplementedError

    def _create_summary_data(self):
        raise NotImplementedError

    def _rename_header(self, h_old, h_new):
        try:
            self.pec_data.rename(columns={h_new: self.cellpy_headers[h_old]},
                                 inplace=True)
        except KeyError as e:
            logging.info(
                f"Problem during conversion to cellpy-format ({e})"
            )

    def convert_units(self):
        pass
