import os
import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/data_ex"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir,test_res_file)
test_data_dir_out = os.path.join(test_data_dir, "out")
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir,test_cellpy_file_tmp)
test_run_name = "20160805_test001_45_cc"


def test_empty():
    r = None
    assert r is None

# Travis needs to have the requirements_travis.txt and be able to install scipy for this to work:
# def test_import_cellpy():
#     import cellpy
    #




