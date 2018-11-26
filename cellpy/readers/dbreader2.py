import time
import os
import pathlib
import tempfile
import warnings
import logging

import pandas as pd
import numpy as np

from cellpy import prms

logger = logging.getLogger(__name__)


class DbSheetCols(object):
    def __init__(self):
        for table_key in prms.DbCols:
            setattr(self, table_key, prms.DbCols[table_key])

    def __repr__(self):
        return f"<excel_db_cols: {self.__dict__}>"


class Reader(object):
    def __init__(self,
                 db_file=None,
                 db_datadir=None,
                 db_datadir_processed=None):

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
        self.header = 0  # should use this instead: self.db_header_row
        self.db_unit_row = prms.Db.db_unit_row
        self.db_data_start_row = prms.Db.db_data_start_row
        self.db_search_start_row = prms.Db.db_search_start_row
        self.db_search_end_row = prms.Db.db_search_end_row

        self.db_sheet_cols = DbSheetCols()
        self.skiprows = self._find_out_what_rows_to_skip()
        self.dtypes_dict = self._create_dtypes_dict()
        self.skiprows = self._find_out_what_rows_to_skip()
        self.table = self._open_sheet()

    def __str__(self):
        newline = "\n  - "
        txt = f"<Reader:: \n  - {newline.join(self.__dict__)} \n>\n"
        txt += "Reader.table.head():\n"
        txt += str(self.table.head())
        return txt

 # --------not fixed from here -------------------------------

    def _find_out_what_rows_to_skip(self):
        skiprows = [1, ]
        return skiprows

    def _create_dtypes_dict(self):
        dtypes_dict = {"d": np.int32}
        return dtypes_dict

    def pick_table(self):
        """Pick the table and return a pandas.DataFrame."""
        return self.table

    def _pick_info(self, serial_number, column_number):
        row = self.select_serial_number_row(serial_number)
        x = self._select_col(row, column_number)
        x = x.values
        if len(x) == 1:
            x = x[0]
        return x

    @staticmethod
    def _select_col(df, no):
        """select specific column"""
        return df.iloc[:, no]

    def _calculate_rows_to_skip(self):
        pass

    def _open_sheet(self, dtypes_dict=None):
        """Opens sheets and returns it"""
        table_name = self.db_sheet_table
        header_row = self.db_header_row
        if dtypes_dict is None:
            dtypes_dict = self.dtypes_dict

        rows_to_skip = self.skiprows

        logging.debug(f"Trying to open the file {self.db_file}")
        logging.debug(f"Skipping the following rows: {rows_to_skip}")
        logging.debug(f"Declaring the following dtyps: {dtypes_dict}")
        work_book = pd.ExcelFile(self.db_file)
        sheet = work_book.parse(
            table_name, header=header_row, skiprows=rows_to_skip,
            dtype=dtypes_dict
        )

        return sheet

    def _validate(self):
        """Checks that the db-file is ok

        Returns:
            True if OK, False if not.
            """
        probably_good_to_go = True
        sheet = self.table
        id = self.db_sheet_cols.id

        # check if you have unique srnos
        id_col = sheet.loc[:, id]
        if any(id_col.duplicated()):
            warnings.warn(
                "your database is corrupt: duplicates"
                " encountered in the srno-column")
            logger.debug("srno duplicates:\n" + str(
                id_col.duplicated()))
            probably_good_to_go = False
        return probably_good_to_go


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


