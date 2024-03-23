import abc
import logging
import os
import pathlib
import re
import tempfile
import time
import warnings
from dataclasses import asdict
from datetime import datetime

import numpy as np
import pandas as pd
from typing import List
from typing import Optional

from cellpy.parameters import prms
from cellpy.readers.core import BaseDbReader

# logger = logging.getLogger(__name__)


class DbSheetCols:
    # Note to developers: this should only be used for this Excell reader
    # (it works, and that is its only reason to still exist)
    def __init__(self):
        db_cols_from_prms = asdict(prms.DbCols)
        self.keys = []
        self.headers = []
        for table_key, value in db_cols_from_prms.items():
            if isinstance(value, (list, tuple)):
                value = value[0]
            setattr(self, table_key, value)
            self.keys.append(table_key)
            self.headers.append(value)

    def __repr__(self):
        return f"<DbCols: {self.__dict__}>"


class Reader(BaseDbReader):
    def __init__(
        self,
        db_file=None,
        db_datadir=None,
        db_datadir_processed=None,
        db_frame=None,
        batch=None,
        batch_col_name=None,
    ):
        """Simple excel reader.

        Args:
            db_file (str, pathlib.Path): xlsx-file to read.
            db_datadir(str, pathlib.Path): path where raw date is located.
            db_datadir_processed (str, pathlib.Path): path where cellpy files are located.
            db_frame (pandas.DataFrame): use this instead of reading from xlsx-file.
            batch (str): batch name to use.
            batch_col_name (str): name of the column in the db-file that contains the batch name.
        """

        self.db_sheet_table = prms.Db.db_table_name
        self.db_header_row = prms.Db.db_header_row
        self.db_unit_row = prms.Db.db_unit_row
        self.db_data_start_row = prms.Db.db_data_start_row
        self.db_search_start_row = prms.Db.db_search_start_row
        self.db_search_end_row = prms.Db.db_search_end_row

        self.db_sheet_cols = DbSheetCols()
        self.selected_batch = None

        if not db_datadir:
            self.db_datadir = prms.Paths.rawdatadir
        else:
            self.db_datadir = db_datadir

        if not db_datadir_processed:
            self.db_datadir_processed = prms.Paths.cellpydatadir
        else:
            self.db_datadir_processed = db_datadir_processed

        if not db_file:
            self.db_path = prms.Paths.db_path
            self.db_filename = prms.Paths.db_filename
            self.db_file = os.path.join(self.db_path, self.db_filename)
        else:
            self.db_path = os.path.dirname(db_file)
            self.db_filename = os.path.basename(db_file)
            self.db_file = db_file

        self.headers = self.db_sheet_cols.headers

        if db_frame is not None:
            print("Using frame instead of file")
            self.table = db_frame.copy()
        else:
            self.skiprows, self.nrows = self._find_out_what_rows_to_skip()
            logging.debug("opening sheet")

            self.table = self._open_sheet()

        if batch:
            self.selected_batch = self.select_batch(
                batch, batch_col_name=batch_col_name
            )
        logging.debug("got table")
        logging.debug(self.table)

    def __str__(self):
        return (
            f"<ExcelReader> (rows: {len(self.table)}, cols: {len(self.table.columns)})"
        )

    def _repr_html_(self):
        return f"<b>ExcelReader</b> (rows: {len(self.table)}, cols: {len(self.table.columns)})"

    def select_batch(
        self,
        batch,
        batch_col_name=None,
        case_sensitive=True,
        drop=True,
        clean=False,
        **kwargs,
    ) -> List[int]:
        """Selects the rows in column batch_col_number.

        Args:
            batch: batch to select
            batch_col_name: column name to use for batch selection (default: DbSheetCols.batch).
            case_sensitive: if True, the batch name must match exactly (default: True).
            drop: if True, all un-selected rows are dropped from the table (default: True).
            clean: if True and drop is True, the table is cleaned from duplicates and NaNs (default: False).

        Returns:
            List of row indices
        """

        # including kwargs to avoid breaking if new kwargs are added

        if self.selected_batch is None:
            return self._select_batch(
                batch,
                batch_col_name=batch_col_name,
                case_sensitive=case_sensitive,
                drop=drop,
                clean=clean,
            )
        else:
            return self.selected_batch

    def _select_batch(
        self, batch, batch_col_name=None, case_sensitive=True, drop=True, clean=False
    ):
        if not batch_col_name:
            batch_col_name = self.db_sheet_cols.batch
        logging.debug("selecting batch - %s" % batch)
        sheet = self.table
        identity = self.db_sheet_cols.id
        exists_col_number = self.db_sheet_cols.exists

        if case_sensitive:
            criterion = sheet.loc[:, batch_col_name] == batch
        else:
            criterion = (sheet.loc[:, batch_col_name]).upper() == batch.upper()

        exists = sheet.loc[:, exists_col_number] > 0
        # This will crash if the col is not of dtype number
        sheet = sheet[criterion & exists]
        if drop:
            self.table = sheet
            if clean:
                sheet = sheet.loc[:, identity]
                sheet.drop_duplicates(inplace=True)
                sheet.dropna(inplace=True)
                return sheet.values.astype(int)
        return sheet.loc[:, identity].values.astype(int)

    def from_batch(
        self,
        batch_name: str,
        include_key: bool = False,
        include_individual_arguments: bool = False,
    ) -> dict:
        raise NotImplementedError("This method is not implemented for this reader")

    @staticmethod
    def _parse_argument_str(argument_str: str) -> Optional[dict]:
        # the argument str must be on the form:
        # "keyword-1=value-1;keyword-2=value2"
        if argument_str is None:
            return
        sep = ";"
        parts = [part.strip() for part in argument_str.split(sep=sep)]
        sep = "="
        arguments = {}
        for p in parts:
            k, v = p.split(sep=sep)
            arguments[k.strip()] = v.strip()
        return arguments

    @staticmethod
    def _extract_date_from_cell_name(
        cell_name, strf="%Y%m%d", regexp=None, splitter="_", position=0, start=0, end=12
    ):
        """Extract date given a cell name (or filename).

        Uses regexp if given to find date txt, if not it uses splitter if splitter is not None or "",
        else start-stop. Uses strf to parse for date in date txt.
        if regexp is "auto", regexp is interpreted from strf

        Args:
            cell_name (str): extract date from.
            strf (str): datetime string formatter.
            regexp (str | "auto"): regular expression.
            splitter (str): split parts into sub-parts.
            position (int): selected sub-part.
            start (int): number of first character in the date part.
            end (int): number of last character in the date part.

        Returns:
            datetime.datetime object
        """

        if regexp is not None:
            if regexp == "auto":
                year_r = r"%Y"
                month_r = r"%m"
                day_r = r"%d"

                regexp = strf.replace("\\", "\\\\").replace("-", r"\-")
                regexp = (
                    regexp.replace(year_r, "[0-9]{4}")
                    .replace(month_r, "[0-9]{2}")
                    .replace(day_r, "[0-9]{2}")
                )
                regexp = f"({regexp})"

            m = re.search(regexp, cell_name)
            datestr = m[0]

        elif splitter:
            datestr = cell_name.split(splitter)[position]

        else:
            datestr = cell_name[start:end]

        try:
            date = datetime.strptime(datestr, strf)
        except ValueError as e:
            logging.debug(e)
            return None

        return date

    def extract_date_from_cell_name(self, force=False):
        if force or "date" not in self.table.columns:
            self.table = self.table.assign(
                date=self.table.file_name_indicator.apply(
                    self._extract_date_from_cell_name
                )
            )

    # --------not fixed from here -------------------------------

    def _find_out_what_rows_to_skip(self):
        if self.db_search_start_row >= self.db_data_start_row:
            start_row = self.db_search_start_row
        else:
            start_row = self.db_data_start_row

        skiprows = set(range(start_row))

        try:
            skiprows.remove(self.db_header_row)
        except KeyError:
            logging.debug(
                "Trying to remove header row number"
                " from skiprow, but it is not in skiprow"
            )
        skiprows.union((self.db_unit_row,))
        if self.db_search_end_row <= 0 or self.db_search_end_row is None:
            nrows = None
        else:
            nrows = self.db_search_end_row - start_row

        return skiprows, nrows

    def _lookup_unit(self, label):
        units = {
            "int": np.int32,
            "float": np.float64,
            "str": str,
            "bol": bool,
            "cat": str,
        }
        return units.get(label.lower(), object)

    def pick_table(self):
        """Pick the table and return a pandas.DataFrame."""
        return self.table

    @staticmethod
    def _select_col(df, no):
        """select specific column"""
        return df.loc[:, no]

    def _open_sheet(self):
        """Opens sheets and returns it"""

        # Note 14.12.2020: xlrd has explicitly removed support for anything other than xls files
        # Solution: install openpyxl
        # df1=pd.read_excel(
        #      os.path.join(APP_PATH, "Data", "aug_latest.xlsm"),
        #      sheet_name=None,
        #      engine='openpyxl',
        # )

        table_name = self.db_sheet_table
        header_row = self.db_header_row
        nrows = self.nrows
        rows_to_skip = self.skiprows

        logging.debug(f"Trying to open the file {self.db_file}")
        logging.debug(f"Number of rows (no means all): {nrows}")
        logging.debug(f"Skipping the following rows: {rows_to_skip}")
        work_book = pd.ExcelFile(self.db_file, engine="openpyxl")
        try:
            sheet = work_book.parse(
                table_name,
                header=header_row,
                skiprows=rows_to_skip,
                nrows=nrows,
            )
        except ValueError as e:
            logging.debug(
                "Could not parse all the columns (ValueError) "
                "using given dtypes. Trying without dtypes."
            )
            logging.debug(str(e))
            sheet = work_book.parse(
                table_name, header=header_row, skiprows=rows_to_skip, nrows=nrows
            )

        return sheet

    def _validate(self):
        """Checks that the db-file is ok

        Returns:
            True if OK, False if not.
        """
        probably_good_to_go = True
        sheet = self.table
        identity = self.db_sheet_cols.id

        # check if you have unique srnos
        id_col = sheet.loc[:, identity]
        if any(id_col.duplicated()):
            warnings.warn(
                "your database is corrupt: duplicates" " encountered in the srno-column"
            )
            logging.debug("srno duplicates:\n" + str(id_col.duplicated()))
            probably_good_to_go = False
        return probably_good_to_go

    def _pick_info(self, serial_number, column_name):
        row = self.select_serial_number_row(serial_number)
        try:
            x = self._select_col(row, column_name)
        except KeyError:
            warnings.warn(f"your database is missing the following key: {column_name}")
            return None
        else:
            x = x.values
            if len(x) == 1:
                x = x[0]
            return x

    def select_serial_number_row(self, serial_number):
        """Select row for identification number serial_number

        Args:
            serial_number: serial number

        Returns:
            pandas.DataFrame
        """
        sheet = self.table
        col = self.db_sheet_cols.id
        rows = sheet.loc[:, col] == serial_number
        return sheet.loc[rows, :]

    def select_all(self, serial_numbers):
        """Select rows for identification for a list of serial_number.

        Args:
            serial_numbers: list (or ndarray) of serial numbers

        Returns:
            pandas.DataFrame
        """
        sheet = self.table
        col = self.db_sheet_cols.id
        rows = sheet.loc[:, col].isin(serial_numbers)
        return sheet.loc[rows, :]

    def print_serial_number_info(self, serial_number, print_to_screen=True):
        """Print information about the run.

        Args:
            serial_number: serial number.
            print_to_screen: runs the print statement if True,
                returns txt if not.

        Returns:
            txt if print_to_screen is False, else None.
        """
        r = self.select_serial_number_row(serial_number)
        if r.empty:
            warnings.warn("missing serial number")
            return

        txt1 = 80 * "="
        txt1 += "\n"
        txt1 += f"   serial number {serial_number}\n"
        txt1 = 80 * "-"
        txt1 += "\n"
        txt2 = ""
        for label, value in zip(r.columns, r.values[0]):
            if label in self.headers:
                txt1 += f"{label}:    \t {value}\n"
            else:
                txt2 += f"({label}:    \t {value})\n"
        if print_to_screen:
            print(txt1)
            print(80 * "-")
            print(txt2)
            print(80 * "=")
            return
        else:
            return txt1

    def inspect_hd5f_fixed(self, serial_number):
        column_name = self.db_sheet_cols.freeze
        insp = self._pick_info(serial_number, column_name)
        return insp

    def inspect_exists(self, serial_number):
        column_name = self.db_sheet_cols.exists
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_label(self, serial_number):
        column_name = self.db_sheet_cols.label
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_area(self, serial_number):
        column_name = self.db_sheet_cols.area
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_cell_name(self, serial_number):
        column_name = self.db_sheet_cols.cell_name
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_comment(self, serial_number):
        column_name = self.db_sheet_cols.comment_general
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_by_column_label(self, column_name, serial_number):
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_group(self, serial_number):
        column_name = self.db_sheet_cols.group
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_cell_type(self, serial_number):
        try:
            column_name = self.db_sheet_cols.cell_type
            insp = self._pick_info(serial_number, column_name)
            return insp
        except KeyError:
            logging.warning(
                "Could not read the cycle mode (using value from prms instead)"
            )
            logging.debug(f"cycle mode: {prms.Reader.cycle_mode}")
            return prms.Reader.cycle_mode

    def get_loading(self, serial_number):
        column_name = self.db_sheet_cols.loading
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_areal_loading(self, serial_number):
        raise NotImplementedError

    def get_args(self, serial_number: int) -> dict:
        column_name = self.db_sheet_cols.argument
        argument_str = self._pick_info(serial_number, column_name)
        try:
            argument = self._parse_argument_str(argument_str)
        except Exception as e:
            logging.warning(f"could not parse argument str:")
            logging.warning(f"{argument_str}")
            logging.warning(f"Error message: {e}")
            return {}

        return argument

    def get_mass(self, serial_number):
        column_name_mass = self.db_sheet_cols.mass_active
        mass = self._pick_info(serial_number, column_name_mass)
        return mass

    def get_nom_cap(self, serial_number):
        column_name = self.db_sheet_cols.nom_cap
        return self._pick_info(serial_number, column_name)

    def get_experiment_type(self, serial_number):
        column_name = self.db_sheet_cols.experiment_type
        return self._pick_info(serial_number, column_name)

    def get_instrument(self, serial_number):
        column_name = self.db_sheet_cols.instrument
        return self._pick_info(serial_number, column_name)

    def get_total_mass(self, serial_number):
        column_name_mass = self.db_sheet_cols.mass_total
        total_mass = self._pick_info(serial_number, column_name_mass)
        return total_mass

    def get_all(self):
        return self.filter_by_col([self.db_sheet_cols.id, self.db_sheet_cols.exists])

    def get_fileid(self, serial_number, full_path=True):  # NOT USED
        column_name = self.db_sheet_cols.file_name_indicator
        if not full_path:
            filename = self._pick_info(serial_number, column_name)
        else:
            filename = os.path.join(
                self.db_datadir_processed, self._pick_info(serial_number, column_name)
            )
        return filename

    @staticmethod
    def intersect(lists):
        # find serial_numbers that to belong to all snro-lists in lists
        # where lists = [serial_numberlist1, snrolist2, ....]
        if not isinstance(lists[0], (list, tuple)):
            lists = [lists]
        serial_numbers = [set(a) for a in lists]
        serial_numbers = set.intersection(*serial_numbers)
        return serial_numbers

    @staticmethod
    def union(lists):
        serial_numbers = [set(a) for a in lists]
        serial_numbers = set.union(*serial_numbers)
        return serial_numbers

    @staticmethod
    def subtract(list1, list2):
        list1 = set(list1)
        list2 = set(list2)
        serial_numbers = set.difference(list1, list2)
        return serial_numbers

    @staticmethod
    def subtract_many(list1, lists):
        list_of_sets = [set(a) for a in lists]
        list1 = set(list1)
        serial_numbers = set.difference(list1, *list_of_sets)
        return serial_numbers

    def filter_selected(self, serial_numbers):
        if isinstance(serial_numbers, (int, float)):
            serial_numbers = [serial_numbers]
        new_serial_numbers = []
        column_name = self.db_sheet_cols.selected
        for serial_number in serial_numbers:
            insp = self._pick_info(serial_number, column_name)
            if insp:
                new_serial_numbers.append(serial_number)
        return new_serial_numbers

    def filter_by_slurry(self, slurry, appender="_"):
        """Filters sheet/table by slurry name.

        Input is slurry name or list of slurry names, for example 'es030' or
        ["es012","es033","es031"].

        Args:
            slurry (str or list of strings): slurry names.
            appender (chr): char that surrounds slurry names.

        Returns:
            List of serial_number (ints).
        """

        sheet = self.table
        identity = self.db_sheet_cols.id
        exists = self.db_sheet_cols.exists
        cellname = self.db_sheet_cols.cell_name
        search_string = ""

        if not isinstance(slurry, (list, tuple)):
            slurry = [slurry]

        first = True
        for slur in slurry:
            s_s = appender + slur + appender
            if first:
                search_string = s_s
                first = False
            else:
                search_string += "|"
                search_string += s_s

        criterion = sheet.loc[:, cellname].str.contains(search_string)
        exists = sheet.loc[:, exists] > 0
        sheet = sheet[criterion & exists]

        return sheet.loc[:, identity].values.astype(int)

    def filter_by_col(self, column_names):
        """filters sheet/table by columns (input is column header)

        The routine returns the serial numbers with values>1 in the selected
        columns.

        Args:
            column_names (list): the column headers.

        Returns:
            pandas.DataFrame
        """

        if not isinstance(column_names, (list, tuple)):
            column_names = [column_names]

        sheet = self.table
        identity = self.db_sheet_cols.id
        exists = self.db_sheet_cols.exists
        criterion = True

        for column_name in column_names:
            _criterion = sheet.loc[:, column_name] > 0
            _exists = sheet.loc[:, exists] > 0
            criterion = criterion & _criterion & _exists

        return sheet.loc[criterion, identity].values.astype(int)

    def filter_by_col_value(self, column_name, min_val=None, max_val=None):
        """filters sheet/table by column.

        The routine returns the serial-numbers with min_val <= values >= max_val
        in the selected column.

        Args:
            column_name (str): column name.
            min_val (int): minimum value of serial number.
            max_val (int): maximum value of serial number.

        Returns:
            pandas.DataFrame
        """
        sheet = self.table
        identity = self.db_sheet_cols.id
        exists_col_number = self.db_sheet_cols.exists

        exists = sheet.loc[:, exists_col_number] > 0

        if min_val is not None and max_val is not None:
            criterion1 = sheet.loc[:, column_name] >= min_val
            criterion2 = sheet.loc[:, column_name] <= max_val
            sheet = sheet[criterion1 & criterion2 & exists]

        elif min_val is not None or max_val is not None:
            if min_val is not None:
                criterion = sheet.loc[:, column_name] >= min_val

            if max_val is not None:
                criterion = sheet.loc[:, column_name] <= max_val

            # noinspection PyUnboundLocalVariable
            sheet = sheet[criterion & exists]
        else:
            sheet = sheet[exists]

        return sheet.loc[:, identity].values.astype(int)
