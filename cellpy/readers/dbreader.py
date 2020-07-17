import time
import os
import pathlib
import tempfile
import warnings
import logging

import pandas as pd
import numpy as np

from cellpy.parameters import prms

# logger = logging.getLogger(__name__)


class DbSheetCols(object):
    def __init__(self, level=0):
        for table_key in prms.DbCols:
            setattr(self, table_key, prms.DbCols[table_key][level])

    def __repr__(self):
        return f"<DbCols: {self.__dict__}>"


class Reader(object):
    def __init__(self, db_file=None, db_datadir=None, db_datadir_processed=None):

        if not db_file:
            self.db_path = prms.Paths["db_path"]
            self.db_filename = prms.Paths["db_filename"]
            self.db_file = os.path.join(self.db_path, self.db_filename)
        else:
            self.db_path = os.path.dirname(db_file)
            self.db_filename = os.path.basename(db_file)
            self.db_file = db_file

        if not db_datadir:
            self.db_datadir = prms.Paths["rawdatadir"]
        else:
            self.db_datadir = db_datadir

        if not db_datadir_processed:
            self.db_datadir_processed = prms.Paths["cellpydatadir"]
        else:
            self.db_datadir_processed = db_datadir_processed

        self.db_sheet_table = prms.Db.db_table_name
        self.db_header_row = prms.Db.db_header_row
        self.db_unit_row = prms.Db.db_unit_row
        self.db_data_start_row = prms.Db.db_data_start_row
        self.db_search_start_row = prms.Db.db_search_start_row
        self.db_search_end_row = prms.Db.db_search_end_row

        self.db_sheet_cols = DbSheetCols()
        self.db_sheet_cols_units = DbSheetCols(1)

        self.skiprows, self.nrows = self._find_out_what_rows_to_skip()
        self.dtypes_dict = self._create_dtypes_dict()
        self.headers = self.dtypes_dict.keys()
        logging.debug("opening sheet")
        self.table = self._open_sheet()
        logging.debug("got table")
        logging.debug(self.table)

    def __str__(self):
        newline = "\n  - "
        txt = f"<Reader:: \n  - {newline.join(self.__dict__)} \n>\n"
        txt += "Reader.table.head():\n"
        txt += str(self.table.head())
        return txt

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
            "str": np.str,
            "bol": np.bool,
            "cat": np.str,
        }
        return units.get(label.lower(), object)

    def _create_dtypes_dict(self):
        dtypes_dict = dict()
        for attr in self.db_sheet_cols.__dict__:
            header = self.db_sheet_cols.__dict__[attr]
            unit = self._lookup_unit(self.db_sheet_cols_units.__dict__[attr])
            dtypes_dict[header] = unit
        return dtypes_dict

    def pick_table(self):
        """Pick the table and return a pandas.DataFrame."""
        return self.table

    @staticmethod
    def _select_col(df, no):
        """select specific column"""
        return df.loc[:, no]

    def _open_sheet(self, dtypes_dict=None):
        """Opens sheets and returns it"""
        table_name = self.db_sheet_table
        header_row = self.db_header_row
        nrows = self.nrows
        if dtypes_dict is None:
            dtypes_dict = self.dtypes_dict

        rows_to_skip = self.skiprows

        logging.debug(f"Trying to open the file {self.db_file}")
        logging.debug(f"Number of rows (no means all): {nrows}")
        logging.debug(f"Skipping the following rows: {rows_to_skip}")
        logging.debug(f"Declaring the following dtyps: {dtypes_dict}")
        work_book = pd.ExcelFile(self.db_file)
        try:
            sheet = work_book.parse(
                table_name,
                header=header_row,
                skiprows=rows_to_skip,
                dtype=dtypes_dict,
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

    def get_cell_name(self, serial_number):
        column_name = self.db_sheet_cols.cell_name
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_comment(self, serial_number):
        column_name = self.db_sheet_cols.comment_general
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
            import sys

            sys.exit()
            return prms.Reader.cycle_mode

    def get_loading(self, serial_number):
        column_name = self.db_sheet_cols.loading
        insp = self._pick_info(serial_number, column_name)
        return insp

    def get_areal_loading(self, serial_number):
        raise NotImplementedError

    def get_mass(self, serial_number):
        column_name_mass = self.db_sheet_cols.active_material
        mass = self._pick_info(serial_number, column_name_mass)
        return mass

    def get_nom_cap(self, serial_number):
        column_name = self.db_sheet_cols.nom_cap
        return self._pick_info(serial_number, column_name)

    def get_experiment_type(self, serial_number):
        column_name = self.db_sheet_cols.experiment_type
        return self._pick_info(serial_number, column_name)

    def get_total_mass(self, serial_number):
        column_name_mass = self.db_sheet_cols.total_material
        total_mass = self._pick_info(serial_number, column_name_mass)
        return total_mass

    def get_all(self):
        return self.filter_by_col([self.db_sheet_cols.id, self.db_sheet_cols.exists])

    def get_fileid(self, serialno, full_path=True):
        column_name = self.db_sheet_cols.file_name_indicator
        if not full_path:
            filename = self._pick_info(serialno, column_name)
        else:
            filename = os.path.join(
                self.db_datadir_processed, self._pick_info(serialno, column_name)
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

    def select_batch(self, batch, batch_col_name=None):
        """selects the rows  in column batch_col_number
        (default: DbSheetCols.batch)"""

        if not batch_col_name:
            batch_col_name = self.db_sheet_cols.batch
        logging.debug("selecting batch - %s" % batch)
        sheet = self.table
        identity = self.db_sheet_cols.id
        exists_col_number = self.db_sheet_cols.exists

        criterion = sheet.loc[:, batch_col_name] == batch
        exists = sheet.loc[:, exists_col_number] > 0
        # This will crash if the col is not of dtype number
        sheet = sheet[criterion & exists]
        return sheet.loc[:, identity].values.astype(int)


if __name__ == "__main__":
    from cellpy import log, prms

    # check if Paths work:
    filelogdir = "/Users/jepe/cellpy_data/logs"
    db_path = "/Users/jepe/cellpy_data/db"
    filelogdir = pathlib.Path(filelogdir)
    db_path = pathlib.Path(db_path)
    # seems to work OK

    prms.Paths.filelogdir = filelogdir
    prms.Paths.db_path = db_path
    prms.Paths.db_filename = "cellpy_db2.xlsx"
    log.setup_logging(default_level="DEBUG")

    logging.info("-logging works-")
    r = Reader()
    ok = r._validate()
    logging.info(f"db-file is OK: {ok}")
    print(r)
    print()

    print("--------------------------------------------------------")
    print(r.table.id)
    print(r.table.describe())
    print(r.table.dtypes)
    print(r.select_serial_number_row(615))
    r.print_serial_number_info(615)
    tm = r.get_total_mass(615)
    print(tm)
