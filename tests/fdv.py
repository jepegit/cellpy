"""Files, Directories, and Variables to be used in the tests.

This works only for the running pytest on the test-files!"""

import os

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
_relative_data_dir = "../testdata"
data_dir = os.path.abspath(os.path.join(current_file_path, _relative_data_dir))

raw_data_dir = os.path.join(data_dir, "data")
output_dir = os.path.join(data_dir, "out")
cellpy_data_dir = os.path.join(data_dir, "hdf5")
db_dir = os.path.join(data_dir, "db")
log_dir = os.path.join(data_dir, "log")

# -------- common files -----------------------------

cellpy_file_name = "20160805_test001_45_cc.h5"
cellpy_file_path = os.path.join(cellpy_data_dir, cellpy_file_name)

temporary_cellpy_file_name = "tmpfile.h5"
temporary_cellpy_file_path = os.path.join(cellpy_data_dir, temporary_cellpy_file_name)

db_file_name = "cellpy_db.xlsx"
db_file_path = os.path.join(db_dir, db_file_name)

step_table_file_name = "steps.csv"
step_table_file_path = os.path.join(raw_data_dir, step_table_file_name)

short_step_table_file_name = "steps_short.csv"
short_step_table_file_path = os.path.join(raw_data_dir, short_step_table_file_name)

run_name = "20160805_test001_45_cc"

# -------- arbin specific files ---------------------

res_file_name = "20160805_test001_45_cc_01.res"
res_file_path = os.path.join(raw_data_dir, res_file_name)

# -------- biologics specific files -----------------
mpr_file_name = "geis.mpr"
mpr_file_path = os.path.join(raw_data_dir, mpr_file_name)

mpr_cellpy_file_name = "geis.h5"
mpr_cellpy_file_path = os.path.join(cellpy_data_dir, mpr_cellpy_file_name)
