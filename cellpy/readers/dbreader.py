# -*- coding: utf-8 -*-
"""simple 'db-reader' for excell
"""

__version__ = "1.0.2"

import os, sys
import pandas as pd
import types

from cellpy.parametres import prmreader

class DB_sheet_cols:
    def __init__(self,sheetname="db_table"):
        if sheetname=="db_table":
            n = 6 # rev 09.05.2014 - inserted 6 new batch-name columns
            self.serialno = 0
            self.exists   = 3
            self.exists_txt = 4
            self.fileid   = 11 + n
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
            self.fi =11 + n
            self.file_name_indicator=11 + n
            self.comment_slurry = 12 + n
            self.finished_run = 13 + n
            self.F  =13 + n
            self.merged_files=14 + n # remove
            self.hd5f_exists = 14 + n # remove
            self.hd5f_fixed = 14 + n
            self.M  =14 + n
            self.VC =15 + n
            self.FEC=16 + n
            self.LS =17 + n
            self.IPA=18 + n
            self.B  =19 + n
            self.RATE =20 + n
            self.LC =21 + n
            self.SINODE =22 + n

            self.am =29 + n
            self.active_material=29 + n
            self.tm =33 + n
            self.total_material=33 + n
            self.wtSi = 34 + n
            self.weight_percent_Si = 34 + n
            self.Si =34 + n
            self.loading = 36 + n
            self.general_comment = 37 + n

        elif sheetname=="db_filenames":
            self.serialno = 0
            self.fileid = 1
            self.files = 2

    def __str__(self):
        txt = """
        look into the source code
        """
        return txt

class reader:
    def __init__(self,db_file = None,
                 db_datadir=None,
                 db_datadir_processed=None):
        prms = prmreader.read()
        if not db_file:
            self.db_path=prms.db_path
            self.db_filename=prms.db_filename
            self.db_file=os.path.join(self.db_path,self.db_filename)
        else:
            self.db_path=os.path.dirname(db_file)
            self.db_filename=os.path.basename(db_file)
            self.db_file=db_file
        if not db_datadir:
            self.db_datadir = prms.resdatadir
        else:
            self.db_datadir = db_datadir
        if not db_datadir_processed:
            self.db_datadir_processed = prms.hdf5datadir
        else:
            self.db_datadir_processed = db_datadir_processed

        self.db_sheet_table = "db_table"
        self.db_sheet_filenames = "db_filenames"
        self.db_sheet_cols = DB_sheet_cols()
        self.db_sheet_filename_cols = DB_sheet_cols(self.db_sheet_filenames)
        self.skiprows = None
        self.header = 0 # row that will be used to define headers
        self.remove_row = [0] # removing this row
        self.string_cols = [3,4,5,6,7,8]

        self.table = self._open_sheet("table")
        self.ftable =  self._open_sheet("filenames")

    def _pick_info(self,srno,colno):
        row = self.select_srno_row(srno)
        x = self.select_col(row,colno)
        x = x.values
        if len(x)==1:
            x = x[0]
        return x

    def _open_sheet(self,sheet=None):
        """Opens sheets and returns it"""
        if not sheet:
            sheet = self.db_sheet_table
        elif sheet == "table":
            sheet = self.db_sheet_table
        elif sheet == "filenames":
            sheet = self.db_sheet_filenames
        h = self.header
        sr = self.skiprows
        wb = pd.ExcelFile(self.db_file)
        sheet = wb.parse(sheet,header=h, skiprows=sr)
        if self.remove_row:
            remove_index = sheet.index[self.remove_row]
            sheet = sheet.drop(remove_index)
            sheet.reindex(range(0,len(sheet.index)))
        return sheet

    def select_srno_row(self,srno):
        """Select row for identification number srno

        Args:
            srno: serial number

        Returns:
            pandas.DataFrame
        """

        sheet = self.table
        colno_serialno=self.db_sheet_cols.serialno
        col_serialno = sheet.iloc[:,colno_serialno]
        #col_serialno = sheet.ix[:,colno_serialno] # decrp
        return sheet[col_serialno == srno]

    def print_serialno(self,serialno):
        """print information about the run

        Args:
            serialno: serial number
        """
        """print_serialno(serialno) gives all information about run serialno

        """
        r = self.select_srno_row(serialno)
        for label, value in zip(r.columns,r.values[0]):
            txt = ""
            if label:
                txt += "%s" % str(label)
            txt += ":\t %s\n" % str(value)
            print txt,

    def filter_by_slurry(self, slurry, appender="_", only_first = True):
        """filters sheet/tabel by slurry name (input is slurry name or list of slurry names,
        for example 'es030' or ["es012","es033","es031"])
        OBS! the filter appends '_' in front (and after if only_first = False) of slurry names
        The routine returns the filtered serialnos"""

        sheet = self.table
        colno_serialno = self.db_sheet_cols.serialno
        exists_col_number = self.db_sheet_cols.exists
        colno_cellname = self.db_sheet_cols.cell_name

        if not isinstance(slurry, (list,tuple)):
            slurry = [slurry,]

        first = True
        for slur in slurry:
            sS = appender+slur+appender
            if first:
                searchString = sS
                first = False
            else:
                searchString += "|"
                searchString += sS

        criterion = sheet.iloc[:,colno_cellname].str.contains(searchString)
        exists = sheet.iloc[:,exists_col_number]>0
        sheet = sheet[criterion & exists]

        return sheet.iloc[:,colno_serialno].values.astype(int)

    def filter_by_col(self,column_numbers):
        """filters sheet/tabel by columns (input is column numbers)

        The routine returns the serialnos with values>1 in the selected
        coulumns.

        Args:
            column_numbers (int): the column numbers.

        Returns:
            pandas.DataFrame
        """

        if not isinstance(column_numbers, (list,tuple)):
            column_numbers = [column_numbers,]
        # then we access our table/sheet
        sheet = self.table
        colno_serialno = self.db_sheet_cols.serialno
        exists_col_number = self.db_sheet_cols.exists
        for colno in column_numbers:
            criterion = sheet.iloc[:,colno]>0 # this does not work all the time
            exists = sheet.iloc[:,exists_col_number]>0
            sheet = sheet[criterion & exists]
        return sheet.iloc[:,colno_serialno].values.astype(int)

    def filter_by_col_value(self,column_number,
                            min_val = None, max_val = None):
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
        colno_serialno = self.db_sheet_cols.serialno
        exists_col_number = self.db_sheet_cols.exists

        exists = sheet.iloc[:,exists_col_number]>0

        if min_val is not None and max_val is not None:

            criterion1 = sheet.iloc[:,column_number]>=min_val
            criterion2 = sheet.iloc[:,column_number]<=max_val
            sheet = sheet[criterion1 & criterion2 &exists]

        elif min_val is not None or max_val is not None:

            if min_val is not None:
                criterion = sheet.iloc[:,column_number]>=min_val

            if max_val is not None:
                criterion = sheet.iloc[:,column_number]<=max_val

            sheet = sheet[criterion & exists]
        else:
            sheet = sheet[exists]

        return sheet.iloc[:,colno_serialno].values.astype(int)


    def select_batch(self,batch,batch_col_number=None):
        """selects the batch batch in column batch_col_number"""
        if not batch_col_number:
            batch_col_number=self.db_sheet_cols.batch
        sheet = self.table
        colno_serialno = self.db_sheet_cols.serialno
        exists_col_number = self.db_sheet_cols.exists
        if batch_col_number in self.string_cols:
            batch = str(batch)
        # possible problem: some cols have objects (that are compared as the type they look like (i.e. int then str))
        # this does not apply for cols that in excel were defined as string
        # there only string values can be found

        criterion = sheet.iloc[:,batch_col_number]==batch
        exists = sheet.iloc[:,exists_col_number]>0
        sheet = sheet[criterion & exists]
        return sheet.iloc[:,colno_serialno].values.astype(int)



    def help_pandas(self):
        txt="""pandas help:
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

    def select_col(self,df,no):
        """select specific column"""
        return df.iloc[:,no]

    def get_resfilenames(self,serialno,full_path=True,non_sensitive = False):
        """returns a list of the data file-names for experiment with serial number serialno.

        Args:
            serialno (int): serial number
            full_path (bool): return filename(s) with full path if True
            non_sensitive (bool): dont stop even if file names are missing if True

        Returns:
            list of filenames
        """
        files = self.get_filenames(serialno,full_path=full_path, use_hdf5=False,
                                   non_sensitive = non_sensitive)
        return files

    def get_hdf5filename(self,serialno,full_path=True, non_sensitive = False):
        """returns a list of the hdf5 file-name for experiment with serial number serialno.

        Args:
            serialno (int): serial number
            full_path (bool): return filename(s) with full path if True
            non_sensitive (bool): dont stop even if file names are missing if True

        Returns:
            [filename]
        """
        files = self.get_filenames(serialno,full_path=full_path,
                                   use_hdf5=True,non_sensitive = non_sensitive,
                                   only_hdf5=True)
        return files

    def get_filenames(self,serialno,full_path=True, use_hdf5=True,
                      non_sensitive = False, only_hdf5=False):
        """returns a list of the data file-names for experiment with serial number serialno.

        Args:
            serialno (int): serial number.
            full_path (bool): return filename(s) with full path if True.
            use_hdf5 (bool): if True, return hdf5 filename if it exists (existence is checked
                             only in the db).
            non_sensitive (bool): dont stop even if file names are missing if True.
            only_hdf5 (bool): return hdf5 filename if True.

        Returns:
            list of file names (str)
        """
        sheet = self.table
        fsheet = self.ftable
        colno_serialno=self.db_sheet_filename_cols.serialno
        colno_start_filenames=self.db_sheet_filename_cols.files
        colno_hdf5 = self.db_sheet_cols.hd5f_exists
        colno_filename=self.db_sheet_cols.fileid
        if full_path:
            datadir=self.db_datadir
            datadir_processed=self.db_datadir_processed
        else:
            datadir=None
            datadir_processed=None
        col_serialno = fsheet.iloc[:,colno_serialno]        # selecting the row with serial numbers in it
        criterion_serialno = col_serialno == serialno
        row_filenames = fsheet[criterion_serialno]  # now we pick out the row(s) with correct serial number
        if use_hdf5:
            select_hdf5 = True
            if not only_hdf5:
                # need to check table if col_hdf5 is ticked
                select_hdf5 = self._pick_info(serialno, colno_hdf5)
        else:
            select_hdf5 = False

        # now I think it is time to convert the values to a list
        filenames=[]
        if not select_hdf5:
            try:
                for filename in row_filenames.values[0][colno_start_filenames:]:
                    if filename and type(filename) in types.StringTypes:
                        # TODO: find a better way to filter out nan-values
                        # alternaive filename = str(filename)
                        # if filename == "nan": (is empty)
                        if full_path:
                           filename = os.path.join(datadir,filename)
                        filenames.append(filename)
            except:
                if not non_sensitive:
                    print "error reading filenames-row (res)"
                    sys.exit(-1)
        else:
            try:
                filename = self._pick_info(serialno, colno_filename)
                if full_path:
                    filename = os.path.join(datadir_processed,filename)+".h5"
                else:
                    filename = filename + ".h5"
                filenames.append(filename)
            except:
                if not non_sensitive:
                    print "error reading filenames-row (hdf5)"
                    sys.exit(-1)
        return filenames

    def filter_selected(self,srnos):
        if isinstance(srnos, (int,float)):
            srnos = [srnos,]
        new_srnos = []
        colno   = self.db_sheet_cols.selected
        for srno in srnos:
            insp    = self._pick_info(srno,colno)
            if insp>0:
                new_srnos.append(srno)
        return new_srnos

    def inspect_finished(self,srno):
        colno   = self.db_sheet_cols.finished_run
        insp    = self._pick_info(srno,colno)
        return insp

    def inspect_hd5f_fixed(self,srno):
        colno   = self.db_sheet_cols.hd5f_fixed
        insp    = self._pick_info(srno,colno)
        return insp

    def inspect_hd5f_exists(self,srno):
        colno   = self.db_sheet_cols.hd5f_exists
        insp    = self._pick_info(srno,colno)
        return insp

    def inspect_exists(self,srno):
        colno   = self.db_sheet_cols.exists
        insp    = self._pick_info(srno,colno)
        return insp

    def get_label(self,srno):
        colno   = self.db_sheet_cols.label
        insp    = self._pick_info(srno,colno)
        return insp

    def get_cell_name(self,srno):
        colno   = self.db_sheet_cols.cell_name
        insp    = self._pick_info(srno,colno)
        return insp

    def get_comment(self,srno):
        colno   = self.db_sheet_cols.general_comment
        insp    = self._pick_info(srno,colno)
        return insp

    def get_group(self,srno):
        colno   = self.db_sheet_cols.group
        insp    = self._pick_info(srno,colno)
        return insp

    def get_loading(self,srno):
        colno   = self.db_sheet_cols.loading
        insp    = self._pick_info(srno,colno)
        return insp

    def get_mass(self,srno):
        colno_mass     = self.db_sheet_cols.active_material
        mass = self._pick_info(srno,colno_mass)
        return mass

    def get_total_mass(self,srno):
        colno_mass     = self.db_sheet_cols.total_material
        total_mass = self._pick_info(srno,colno_mass)
        return total_mass

    def get_all(self):
        return self.filter_by_col([self.db_sheet_cols.serialno,self.db_sheet_cols.exists])

    def get_fileid(self,serialno,full_path = True):
        colno_fileid = self.db_sheet_cols.fileid
        if not full_path:
            filename = self._pick_info(serialno, colno_fileid)
        else:
            filename = os.path.join(self.db_datadir_processed,self._pick_info(serialno, colno_fileid))
        return filename

    def intersect(self,lists):
        # find srnos that to belong to all snro-lists in lists
        # where lists = [srnolist1, snrolist2, ....]
        if not isinstance(lists[0], (list,tuple)):
            lists = [lists,]
        srnos = [set(a) for a in lists]
        srnos = set.intersection(*srnos)
        return srnos

    def union(self,lists):
        srnos = [set(a) for a in lists]
        srnos = set.union(*srnos)
        return srnos

    def substract(self,list1, list2):
        list1 = set(list1)
        list2 = set(list2)
        srnos = set.difference(list1,list2)
        return srnos

    def substract_many(self, list1, lists):
        slists = [set(a) for a in lists]
        list1 = set(list1)
        srnos = set.difference(list1, *slists)
        return snros


def _investigate_excel_dbreader_0():
    print sys.argv[0]
    t0=time.time()
    print "t0: %f" % t0
    Reader = reader()
    Reader.print_serialno(12)

def _investigate_excel_dbreader_1():
    print sys.argv[0]
    t0=time.time()
    print "t0: %f" % t0
    Reader = reader()
    srnos = Reader.get_all()
    print "dt: %f" % (time.time()-t0)
    for j in srnos:
        print
        print "checking file",
        print j
        print "Filenames:"
        filenames = Reader.get_filenames(j)
        for fi in filenames:
            print fi
    print "dt: %f" % (time.time()-t0)
    print "finished"

def _investigate_excel_dbreader_2():
    print sys.argv[0]
    Reader = reader()
    print "testing filtering"
    column_numbers = []
    column_numbers.append(reader.db_sheet_cols.FEC)
    column_numbers.append(reader.db_sheet_cols.VC)
    #column_numbers.append(reader.db_sheet_cols.LS)
    o = Reader.filter_by_col(column_numbers)
    print o
    print "testing selecting batch"
    batch_col = Reader.db_sheet_cols.b01
    batch = "my best"
    batch = 12 # will not work, need to use strings for these columns
    a = Reader.select_batch(batch,batch_col)
    print a
    batch = 12
    batch = "l1"
    a = Reader.select_batch(batch)
    print a
    print "finished"


def _investigate_excel_dbreader_3():
    print "STARTING"
    print sys.argv[0]
    t0 = time.time()
    Reader = reader()
    dt1 = time.time()-t0
    print "first lets filter the db"
    print "testing filtering"
    column_numbers = []
    column_numbers.append(Reader.db_sheet_cols.FEC)
    column_numbers.append(Reader.db_sheet_cols.VC)
    #column_numbers.append(reader.db_sheet_cols.LS)
    o = Reader.filter_by_col(column_numbers)
    print o
    print "testing selecting batch"
    batch_col = Reader.db_sheet_cols.b01
    batch = "buffer_ss_x"
    #batch = 12
    a = Reader.select_batch(batch,batch_col)
    print a
    print "\nselecting the first srno"
    srno = a[0]
    print srno
    print "testing picking info"
    print "\nfirst give me the filenames for srno",
    print srno
    filenames = Reader.get_filenames(srno)
    for filename in filenames:
        print filename
    print "\nthen print all info for srno",
    print srno
    Reader.print_serialno(srno)
    print "\nNow I want to get the mass for srno",
    print srno
    mass = Reader.get_mass(srno)
    print mass,
    print "mg"
    dt2 = time.time()-t0
    print "The script took %5.3f sec\n(out of this, loading db took %5.3f sec)" % (dt2,dt1)

    print "\nfinished"


def _investigate_excel_dbreader_4():
    print "STARTING"
    print sys.argv[0]
    t0 = time.time()
    Reader = reader()
    dt1 = time.time()-t0
    srno = 340
    print "inspect_finished",
    print Reader.inspect_finished(srno)
    if Reader.inspect_finished(srno):
        print "True"
    else:
        print "False"

    print "inspect_hd5f_exists",
    print Reader.inspect_hd5f_exists(srno)
    if Reader.inspect_hd5f_exists(srno):
        print "True"
    else:
        print "False"

    print "inspect_exists",
    print Reader.inspect_exists(srno)
    if Reader.inspect_exists(srno):
        print "True"
    else:
        print "False"

    print "get_comment",
    print Reader.get_comment(srno)

    print "get_loading",
    print Reader.get_loading(srno),
    print "mg/cm2"

    print "get_mass",
    print Reader.get_mass(srno),
    print "mg"

    print "get_total_mass",
    print Reader.get_total_mass(srno),
    print "mg"

    print "get_fileid",
    print Reader.get_fileid(srno)

    print "get_label",
    print Reader.get_label(srno)



def _investigate_excel_dbreader_5():
    print "STARTING (test filter_by_slurry)"
    print sys.argv[0]
    Reader = reader()
    slurries = ["es030", "es031"]
    srnos = Reader.filter_by_slurry(slurries)
    print "srno  cell_name    loading(mg/cm2)"

    for srno in srnos:
        print srno,
        print Reader.get_cell_name(srno),
        print Reader.get_loading(srno)

def _investigate_excel_dbreader_6():
    print "STARTING  (test filter_by_col_value)"
    print sys.argv[0]
    Reader = reader()
    n = 6
    col_no = 36 + n
    min_val = None
    max_val = 0.5
    srnos = Reader.filter_by_col_value(col_no, min_val = min_val, max_val = max_val)
    print
    print "filtering within (%s - %s)" % (str(min_val), str(max_val))
    print "srno  cell_name    loading(mg/cm2)"
    for srno in srnos:
        print srno,
        print Reader.get_cell_name(srno),
        print Reader.get_loading(srno)

def _investigate_excel_dbreader_7():
    print "STARTING  (test mixed filtering)"
    print sys.argv[0]
    Reader = reader()
    n = 6
    col_no = 36 + n # should be loading (30.10.2014)
    print "using col_no %i for finding loading" % (col_no)
    min_val = None
    max_val = 0.7

    srnos1 = Reader.filter_by_col_value(col_no, min_val = min_val, max_val = max_val)

    slurries = ["es030", "es031"]
    srnos2 = Reader.filter_by_slurry(slurries, only_first=False)

    print
    print srnos1
    print
    print srnos2

    srnos = [set(a) for a in [srnos1,srnos2]]
    srnos = set.intersection(*srnos)

    print
    print "filtering within (%s - %s)" % (str(min_val), str(max_val))
    print "with cell_names containing"
    txt =""
    for s in slurries:
        txt+= "   _%s" % (s)
    print txt
    print
    print "srno  cell_name    loading(mg/cm2)"
    for srno in srnos:
        print srno,
        print Reader.get_cell_name(srno),
        print Reader.get_loading(srno)

def _investigate_excel_dbreader_8():
    print "STARTING  (test print srno info)"



    print sys.argv[0]
    Reader = reader()
    print "path",
    print Reader.db_path
    print Reader.db_filename
    print Reader.db_file

    srno = 695
    print "printing"
    Reader.print_serialno(srno)



if __name__== "__main__":
    import time
    from pylab import *
    _investigate_excel_dbreader_8()
