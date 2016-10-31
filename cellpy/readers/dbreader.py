# -*- coding: utf-8 -*-
"""simple 'db-reader' for excel
"""

import os
import sys
import types
import pandas as pd


from cellpy.parametres import prmreader


class DbSheetCols:
    def __init__(self, sheetname="db_table"):
        # type: (str) -> None
        if sheetname == "db_table":
            n = 6  # rev 09.05.2014 - inserted 6 new batch-name columns
            self.serial_number_position = 0
            self.exists = 3
            self.exists_txt = 4
            self.fileid = 11 + n
            self.batch = 1
            self.b01 = 5
            self.b02 = 6
            self.b03 = 7
            self.b04 = 8
            self.b05 = 9
            self.b06 = 10
            self.b07 = 11
            self.b08 = 12

            self.label = 7 + n
            self.group = 8 + n
            self.selected = 9 + n
            self.cell_name = 10 + n
            self.fi = 11 + n
            self.file_name_indicator = 11 + n
            self.comment_slurry = 12 + n
            self.finished_run = 13 + n
            self.F = 13 + n
            self.merged_files = 14 + n  # remove
            self.hd5f_exists = 14 + n  # remove
            self.hd5f_fixed = 14 + n
            self.M = 14 + n
            self.VC = 15 + n
            self.FEC = 16 + n
            self.LS = 17 + n
            self.IPA = 18 + n
            self.B = 19 + n
            self.RATE = 20 + n
            self.LC = 21 + n
            self.SINODE = 22 + n

            self.am = 29 + n
            self.active_material = 29 + n
            self.tm = 33 + n
            self.total_material = 33 + n
            self.wtSi = 34 + n
            self.weight_percent_Si = 34 + n
            self.Si = 34 + n
            self.loading = 36 + n
            self.general_comment = 37 + n

        elif sheetname == "db_filenames":
            self.serialno = 0
            self.fileid = 1
            self.files = 2

    def __str__(self):
        txt = """
        look into the source code
        """
        return txt


class reader:
    def __init__(self, db_file=None,
                 db_datadir=None,
                 db_datadir_processed=None,
                 prm_file=None):
        prms = prmreader.read(prm_file)
        if not db_file:
            self.db_path = prms.db_path
            self.db_filename = prms.db_filename
            self.db_file = os.path.join(self.db_path, self.db_filename)
        else:
            self.db_path = os.path.dirname(db_file)
            self.db_filename = os.path.basename(db_file)
            self.db_file = db_file
        if not db_datadir:
            self.db_datadir = prms.rawdatadir
        else:
            self.db_datadir = db_datadir
        if not db_datadir_processed:
            self.db_datadir_processed = prms.cellpydatadir
        else:
            self.db_datadir_processed = db_datadir_processed

        self.db_sheet_table = "db_table"
        self.db_sheet_filenames = "db_filenames"
        self.db_sheet_cols = DbSheetCols()
        self.db_sheet_filename_cols = DbSheetCols(self.db_sheet_filenames)
        self.skiprows = None
        self.header = 0  # row that will be used to define headers
        self.remove_row = [0]  # removing this row
        self.string_cols = [3, 4, 5, 6, 7, 8]

        self.table = self._open_sheet("table")
        self.ftable = self._open_sheet("file_names")

    def _pick_info(self, serial_number, column_number):
        row = self.select_serial_number_row(serial_number)
        x = self.select_col(row, column_number)
        x = x.values
        if len(x) == 1:
            x = x[0]
        return x

    def _open_sheet(self, sheet=None):
        """Opens sheets and returns it"""
        if not sheet:
            sheet = self.db_sheet_table
        elif sheet == "table":
            sheet = self.db_sheet_table
        elif sheet == "file_names":
            sheet = self.db_sheet_filenames
        header = self.header
        rows_to_skip = self.skiprows
        work_book = pd.ExcelFile(self.db_file)
        sheet = work_book.parse(sheet, header=header, skiprows=rows_to_skip)
        if self.remove_row:
            remove_index = sheet.index[self.remove_row]
            sheet = sheet.drop(remove_index)
            sheet.reindex(range(0, len(sheet.index)))
        return sheet

    def select_serial_number_row(self, serial_number):
        """Select row for identification number serial_number

        Args:
            serial_number: serial number

        Returns:
            pandas.DataFrame
        """

        sheet = self.table
        column_number_serial_number_position = self.db_sheet_cols.serial_number_position
        col_serial_number_position = sheet.iloc[:, column_number_serial_number_position]
        # col_serial_number_position = sheet.ix[:,column_number_serial_number_position] # decrp
        return sheet[col_serial_number_position == serial_number]

    def print_serial_number_info(self, serial_number):
        """print information about the run

        Args:
            serial_number: serial number
        """
        r = self.select_serial_number_row(serial_number)
        for label, value in zip(r.columns, r.values[0]):
            txt = ""
            if label:
                txt += "%s" % str(label)
            txt += ":\t %s\n" % str(value)
            print txt,

    def filter_by_slurry(self, slurry, appender="_"):
        """Filters sheet/table by slurry name.

        Input is slurry name or list of slurry names, for example 'es030' or ["es012","es033","es031"].

        Args:
            slurry (str or list of strings): slurry names.
            appender (chr): char that surrounds slurry names.

        Returns:
            List of serial_number (ints).
        """

        sheet = self.table
        column_number_serial_number_position = self.db_sheet_cols.serial_number_position
        exists_col_number = self.db_sheet_cols.exists
        column_number_cellname = self.db_sheet_cols.cell_name

        if not isinstance(slurry, (list, tuple)):
            slurry = [slurry, ]

        first = True
        for slur in slurry:
            s_s = appender + slur + appender
            if first:
                search_string = s_s
                first = False
            else:
                search_string += "|"
                search_string += s_s

        criterion = sheet.iloc[:, column_number_cellname].str.contains(search_string)
        exists = sheet.iloc[:, exists_col_number] > 0
        sheet = sheet[criterion & exists]

        return sheet.iloc[:, column_number_serial_number_position].values.astype(int)

    def filter_by_col(self, column_numbers):
        """filters sheet/table by columns (input is column numbers)

        The routine returns the serial numbers with values>1 in the selected
        columns.

        Args:
            column_numbers (list): the column numbers.

        Returns:
            pandas.DataFrame
        """

        if not isinstance(column_numbers, (list, tuple)):
            column_numbers = [column_numbers, ]
        sheet = self.table
        column_number_serial_number_position = self.db_sheet_cols.serial_number_position
        exists_col_number = self.db_sheet_cols.exists
        for column_number in column_numbers:
            criterion = sheet.iloc[:, column_number] > 0  # this does not work all the time
            exists = sheet.iloc[:, exists_col_number] > 0
            sheet = sheet[criterion & exists]
        return sheet.iloc[:, column_number_serial_number_position].values.astype(int)

    def filter_by_col_value(self, column_number,
                            min_val=None, max_val=None):
        """filters sheet/table by column.

        The routine returns the serialnos with min_val <= values >= max_val in the selected
        column.

        Args:
            column_number (int): column number (min 0).
            min_val (int): minimum value of serial number.
            max_val (int): maximum value of serial number.

        Returns:
            pandas.DataFrame
        """
        sheet = self.table
        column_number_serial_number_position = self.db_sheet_cols.serial_number_position
        exists_col_number = self.db_sheet_cols.exists

        exists = sheet.iloc[:, exists_col_number] > 0

        if min_val is not None and max_val is not None:

            criterion1 = sheet.iloc[:, column_number] >= min_val
            criterion2 = sheet.iloc[:, column_number] <= max_val
            sheet = sheet[criterion1 & criterion2 & exists]

        elif min_val is not None or max_val is not None:

            if min_val is not None:
                criterion = sheet.iloc[:, column_number] >= min_val

            if max_val is not None:
                criterion = sheet.iloc[:, column_number] <= max_val

            sheet = sheet[criterion & exists]
        else:
            sheet = sheet[exists]

        return sheet.iloc[:, column_number_serial_number_position].values.astype(int)

    def select_batch(self, batch, batch_col_number=None):
        """selects the batch batch in column batch_col_number (default: DbSheetCols.batch)"""

        if not batch_col_number:
            batch_col_number = self.db_sheet_cols.batch

        sheet = self.table
        column_number_serial_number_position = self.db_sheet_cols.serial_number_position
        exists_col_number = self.db_sheet_cols.exists

        if batch_col_number in self.string_cols:
            batch = str(batch)
        # possible problem: some cols have objects (that are compared as the type they look like (i.e. int then str))
        # this does not apply for cols that in excel were defined as string
        # there only string values can be found

        criterion = sheet.iloc[:, batch_col_number] == batch
        exists = sheet.iloc[:, exists_col_number] > 0
        sheet = sheet[criterion & exists]
        return sheet.iloc[:, column_number_serial_number_position].values.astype(int)

    @staticmethod
    def select_col(df, no):
        """select specific column"""
        return df.iloc[:, no]

    def get_resfilenames(self, serialno, full_path=True, non_sensitive=False):
        """returns a list of the data file-names for experiment with serial number serialno.

        Args:
            serialno (int): serial number
            full_path (bool): return filename(s) with full path if True
            non_sensitive (bool): dont stop even if file names are missing if True

        Returns:
            list of file_names
        """
        files = self.get_filenames(serialno, full_path=full_path, use_hdf5=False,
                                   non_sensitive=non_sensitive)
        return files

    def get_hdf5filename(self, serialno, full_path=True, non_sensitive=False):
        """returns a list of the hdf5 file-name for experiment with serial number serialno.

        Args:
            serialno (int): serial number
            full_path (bool): return filename(s) with full path if True
            non_sensitive (bool): dont stop even if file names are missing if True

        Returns:
            [filename]
        """
        files = self.get_filenames(serialno, full_path=full_path,
                                   use_hdf5=True, non_sensitive=non_sensitive,
                                   only_hdf5=True)
        return files

    def get_filenames(self, serial_number, full_path=True, use_hdf5=True,
                      non_sensitive=False, only_hdf5=False):
        """returns a list of the data file-names for experiment with serial number serialno.

        Args:
            serial_number (int): serial number.
            full_path (bool): return filename(s) with full path if True.
            use_hdf5 (bool): if True, return hdf5 filename if it exists (existence is checked
                             only in the db).
            non_sensitive (bool): dont stop even if file names are missing if True.
            only_hdf5 (bool): return hdf5 filename if True.

        Returns:
            list of file names (str)
        """
        fsheet = self.ftable
        column_number_serial_number_position = self.db_sheet_filename_cols.serial_number_position
        column_number_start_filenames = self.db_sheet_filename_cols.files
        column_number_hdf5 = self.db_sheet_cols.hd5f_exists
        column_number_filename = self.db_sheet_cols.fileid
        if full_path:
            datadir = self.db_datadir
            datadir_processed = self.db_datadir_processed
        else:
            datadir = None
            datadir_processed = None
        col_serialno = fsheet.iloc[:, column_number_serial_number_position]  # selecting the row with serial numbers in it
        criterion_serialno = col_serialno == serial_number
        row_filenames = fsheet[criterion_serialno]  # now we pick out the row(s) with correct serial number
        if use_hdf5:
            select_hdf5 = True
            if not only_hdf5:
                # need to check table if col_hdf5 is ticked
                select_hdf5 = self._pick_info(serial_number, column_number_hdf5)
        else:
            select_hdf5 = False

        # now I think it is time to convert the values to a list
        filenames = []
        if not select_hdf5:
            try:
                for filename in row_filenames.values[0][column_number_start_filenames:]:
                    if filename and type(filename) in types.StringTypes:
                        # TODO: find a better way to filter out nan-values
                        # alternaive filename = str(filename)
                        # if filename == "nan": (is empty)
                        if full_path:
                            filename = os.path.join(datadir, filename)
                        filenames.append(filename)
            except:
                if not non_sensitive:
                    print "error reading file_names-row (res)"
                    sys.exit(-1)
        else:
            try:
                filename = self._pick_info(serial_number, column_number_filename)
                if full_path:
                    filename = os.path.join(datadir_processed, filename) + ".h5"
                else:
                    filename += ".h5"
                filenames.append(filename)
            except:
                if not non_sensitive:
                    print "error reading file_names-row (hdf5)"
                    sys.exit(-1)
        return filenames

    def filter_selected(self, serial_numbers):
        if isinstance(serial_numbers, (int, float)):
            serial_numbers = [serial_numbers, ]
        new_serial_numbers = []
        column_number = self.db_sheet_cols.selected
        for serial_number in serial_numbers:
            insp = self._pick_info(serial_number, column_number)
            if insp > 0:
                new_serial_numbers.append(serial_number)
        return new_serial_numbers

    def inspect_finished(self, serial_number):
        column_number = self.db_sheet_cols.finished_run
        insp = self._pick_info(serial_number, column_number)
        return insp

    def inspect_hd5f_fixed(self, serial_number):
        column_number = self.db_sheet_cols.hd5f_fixed
        insp = self._pick_info(serial_number, column_number)
        return insp

    def inspect_hd5f_exists(self, serial_number):
        column_number = self.db_sheet_cols.hd5f_exists
        insp = self._pick_info(serial_number, column_number)
        return insp

    def inspect_exists(self, serial_number):
        column_number = self.db_sheet_cols.exists
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_label(self, serial_number):
        column_number = self.db_sheet_cols.label
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_cell_name(self, serial_number):
        column_number = self.db_sheet_cols.cell_name
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_comment(self, serial_number):
        column_number = self.db_sheet_cols.general_comment
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_group(self, serial_number):
        column_number = self.db_sheet_cols.group
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_loading(self, serial_number):
        column_number = self.db_sheet_cols.loading
        insp = self._pick_info(serial_number, column_number)
        return insp

    def get_mass(self, serial_number):
        column_number_mass = self.db_sheet_cols.active_material
        mass = self._pick_info(serial_number, column_number_mass)
        return mass

    def get_total_mass(self, serial_number):
        column_number_mass = self.db_sheet_cols.total_material
        total_mass = self._pick_info(serial_number, column_number_mass)
        return total_mass

    def get_all(self):
        return self.filter_by_col([self.db_sheet_cols.serial_number_position, self.db_sheet_cols.exists])

    def get_fileid(self, serialno, full_path=True):
        column_number_fileid = self.db_sheet_cols.fileid
        if not full_path:
            filename = self._pick_info(serialno, column_number_fileid)
        else:
            filename = os.path.join(self.db_datadir_processed, self._pick_info(serialno, column_number_fileid))
        return filename

    @staticmethod
    def intersect(lists):
        # find serial_numbers that to belong to all snro-lists in lists
        # where lists = [serial_numberlist1, snrolist2, ....]
        if not isinstance(lists[0], (list, tuple)):
            lists = [lists, ]
        serial_numbers = [set(a) for a in lists]
        serial_numbers = set.intersection(*serial_numbers)
        return serial_numbers

    @staticmethod
    def union(lists):
        serial_numbers = [set(a) for a in lists]
        serial_numbers = set.union(*serial_numbers)
        return serial_numbers

    @staticmethod
    def substract(list1, list2):
        list1 = set(list1)
        list2 = set(list2)
        serial_numbers = set.difference(list1, list2)
        return serial_numbers

    @staticmethod
    def substract_many(list1, lists):
        slists = [set(a) for a in lists]
        list1 = set(list1)
        serial_numbers = set.difference(list1, *slists)
        return serial_numbers

    @staticmethod
    def _help_pandas():
        txt = """pandas help:
        Assuming the dataframe has row indexes a,b,c,...
        Assuming the dataframe has column indexes A,B,C

        general rules
        .loc[[rows],[cols]] selects (first) on index names
        .iloc[[rows],[cols]] selects on index numbers (i.e. position 0,1,2,etc)
        df[ criterion ] where criterion is a boolean array with same dim as df
        selects the row/cols where criterion is True

        selecting columns on index-name
        df.A        - selects col A
        df[:,"A]"     - selects col A
        df[:,"B":]     - selects col B and higher
        df[:,["A","C"]] - selects col A and C
        df.loc[:,"A"]   - selects col A (see also selecting on row)

        selecting rows on index-name (.loc[row,col])
        df.loc["a"]   - selects row a
        df.loc["b:"]   - selects row b and higher
        df.loc[["b","e"]   - selects row b and c
        df.loc["a"] > 0 - returns bool df where filtered on values in row a > 0

        same applies for iloc

        For fast scalar value setting and getting, use
        .at (name) or
        .iat (position)

        other methods
        .isin
        .map
            criterion = df["A"].map(lambda x: x<12.2) (only series)
            df[criterion]
        """
        print txt



def _investigate_excel_dbreader_0():
    """Used for testing"""
    print sys.argv[0]
    t0 = time.time()
    print "t0: %f" % t0
    Reader = reader()
    Reader.print_serial_number_info(12)


def _investigate_excel_dbreader_1():
    """Used for testing"""
    print sys.argv[0]
    t0 = time.time()
    print "t0: %f" % t0
    Reader = reader()
    serial_numbers = Reader.get_all()
    print "dt: %f" % (time.time() - t0)
    for j in serial_numbers:
        print
        print "checking file",
        print j
        print "Filenames:"
        filenames = Reader.get_filenames(j)
        for fi in filenames:
            print fi
    print "dt: %f" % (time.time() - t0)
    print "finished"


def _investigate_excel_dbreader_2():
    """Used for testing"""
    print sys.argv[0]
    Reader = reader()
    print "testing filtering"
    column_numbers = [Reader.db_sheet_cols.FEC, Reader.db_sheet_cols.VC]
    # column_numbers.append(reader.db_sheet_cols.LS)
    o = Reader.filter_by_col(column_numbers)
    print o
    print "testing selecting batch"
    batch_col = Reader.db_sheet_cols.b01
    batch = "my best"
    a = Reader.select_batch(batch, batch_col)
    print a
    batch = "l1"
    a = Reader.select_batch(batch)
    print a
    print "finished"


def _investigate_excel_dbreader_3():
    """Used for testing"""
    print "STARTING"
    print sys.argv[0]
    t0 = time.time()
    Reader = reader()
    dt1 = time.time() - t0
    print "first lets filter the db"
    print "testing filtering"
    column_numbers = [Reader.db_sheet_cols.FEC, Reader.db_sheet_cols.VC]
    # column_numbers.append(reader.db_sheet_cols.LS)
    o = Reader.filter_by_col(column_numbers)
    print o
    print "testing selecting batch"
    batch_col = Reader.db_sheet_cols.b01
    batch = "buffer_ss_x"
    # batch = 12
    a = Reader.select_batch(batch, batch_col)
    print a
    print "\nselecting the first serial_number"
    serial_number = a[0]
    print serial_number
    print "testing picking info"
    print "\nfirst give me the file_names for serial_number",
    print serial_number
    filenames = Reader.get_filenames(serial_number)
    for filename in filenames:
        print filename
    print "\nthen print all info for serial_number",
    print serial_number
    Reader.print_serial_number_info(serial_number)
    print "\nNow I want to get the mass for serial_number",
    print serial_number
    mass = Reader.get_mass(serial_number)
    print mass,
    print "mg"
    dt2 = time.time() - t0
    print "The script took %5.3f sec\n(out of this, loading db took %5.3f sec)" % (dt2, dt1)

    print "\nfinished"


def _investigate_excel_dbreader_4():
    """Used for testing"""
    print "STARTING"
    print sys.argv[0]
    t0 = time.time()
    Reader = reader()
    serial_number = 340
    print "inspect_finished",
    print Reader.inspect_finished(serial_number)
    if Reader.inspect_finished(serial_number):
        print "True"
    else:
        print "False"

    print "inspect_hd5f_exists",
    print Reader.inspect_hd5f_exists(serial_number)
    if Reader.inspect_hd5f_exists(serial_number):
        print "True"
    else:
        print "False"

    print "inspect_exists",
    print Reader.inspect_exists(serial_number)
    if Reader.inspect_exists(serial_number):
        print "True"
    else:
        print "False"

    print "get_comment",
    print Reader.get_comment(serial_number)

    print "get_loading",
    print Reader.get_loading(serial_number),
    print "mg/cm2"

    print "get_mass",
    print Reader.get_mass(serial_number),
    print "mg"

    print "get_total_mass",
    print Reader.get_total_mass(serial_number),
    print "mg"

    print "get_fileid",
    print Reader.get_fileid(serial_number)

    print "get_label",
    print Reader.get_label(serial_number)


def _investigate_excel_dbreader_5():
    """Used for testing"""
    print "STARTING (test filter_by_slurry)"
    print sys.argv[0]
    Reader = reader()
    slurries = ["es030", "es031"]
    serial_numbers = Reader.filter_by_slurry(slurries)
    print "serial_number  cell_name    loading(mg/cm2)"

    for serial_number in serial_numbers:
        print serial_number,
        print Reader.get_cell_name(serial_number),
        print Reader.get_loading(serial_number)


def _investigate_excel_dbreader_6():
    """Used for testing"""
    print "STARTING  (test filter_by_col_value)"
    print sys.argv[0]
    Reader = reader()
    n = 6
    col_no = 36 + n
    min_val = None
    max_val = 0.5
    serial_numbers = Reader.filter_by_col_value(col_no, min_val=min_val, max_val=max_val)
    print
    print "filtering within (%s - %s)" % (str(min_val), str(max_val))
    print "serial_number  cell_name    loading(mg/cm2)"
    for serial_number in serial_numbers:
        print serial_number,
        print Reader.get_cell_name(serial_number),
        print Reader.get_loading(serial_number)


def _investigate_excel_dbreader_7():
    """Used for testing"""
    print "STARTING  (test mixed filtering)"
    print sys.argv[0]
    Reader = reader()
    n = 6
    col_no = 36 + n  # should be loading (30.10.2014)
    print "using col_no %i for finding loading" % (col_no)
    min_val = None
    max_val = 0.7

    serial_numbers1 = Reader.filter_by_col_value(col_no, min_val=min_val, max_val=max_val)

    slurries = ["es030", "es031"]
    serial_numbers2 = Reader.filter_by_slurry(slurries, only_first=False)

    print
    print serial_numbers1
    print
    print serial_numbers2

    serial_numbers = [set(a) for a in [serial_numbers1, serial_numbers2]]
    serial_numbers = set.intersection(*serial_numbers)

    print
    print "filtering within (%s - %s)" % (str(min_val), str(max_val))
    print "with cell_names containing"
    txt = ""
    for s in slurries:
        txt += "   _%s" % (s)
    print txt
    print
    print "serial_number  cell_name    loading(mg/cm2)"
    for serial_number in serial_numbers:
        print serial_number,
        print Reader.get_cell_name(serial_number),
        print Reader.get_loading(serial_number)


def _investigate_excel_dbreader_8():
    """Used for testing"""
    print "STARTING  (test print serial_number info)"

    print sys.argv[0]
    Reader = reader()
    print "path",
    print Reader.db_path
    print Reader.db_filename
    print Reader.db_file

    serial_number = 620
    print "printing"
    Reader.print_serial_number_info(serial_number)


if __name__ == "__main__":
    import time
    from pylab import *

    _investigate_excel_dbreader_8()
