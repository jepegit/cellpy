"""Files, Directories, and Variables to be used in the tests."""

import os

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))

test_data_dir_raw = os.path.join(test_data_dir, "data")
test_data_dir_out = os.path.join(test_data_dir, "out")
test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_data_dir_db = os.path.join(test_data_dir, "db")

# -------- common files -----------------------------

test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy, test_cellpy_file)

test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy, test_cellpy_file_tmp)

test_db_filename = "cellpy_db.xlsx"
test_db_filename_full = os.path.join(test_data_dir_db, test_db_filename)

test_run_name = "20160805_test001_45_cc"

test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir_raw, test_res_file)

# -------- biologics specific files -----------------
test_mpr_file = "geis.mpr"
test_mpr_file_full = os.path.join(test_data_dir_raw, test_mpr_file)

test_mpr_cellpy_file = "geis.h5"
test_mpr_cellpy_file_full = os.path.join(test_data_dir_cellpy, test_mpr_cellpy_file)
