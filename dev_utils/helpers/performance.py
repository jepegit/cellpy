import os
import sys
import time
print(f"running {sys.argv[0]}")

import cellpy
from cellpy import log
from cellpy import cellreader
from cellpy.parameters import prms

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_data_dir_raw = os.path.join(test_data_dir, "data")

test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir_raw,test_res_file)

test_data_dir_out = os.path.join(test_data_dir, "out")
test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy,test_cellpy_file_tmp)

test_run_name = "20160805_test001_45_cc"
log.setup_logging(default_level="DEBUG")


new_arbin_file = r"C:\Scripting\Processing\Celldata\indata\NewArbin\20170907_sic024_01_cc_01.res"
new_arbin_mass = 0.824098422


def load_it(cellpy_data_instance):
    # cellpy_data_instance.loadcell(test_res_file_full)
    raw_file_loader = cellpy_data_instance.loader
    test = raw_file_loader(test_res_file_full)
    cellpy_data_instance.datasets.append(test[0])


def append_to_it(cellpy_data_instance):
    raw_file_loader = cellpy_data_instance.loader
    test = raw_file_loader(test_res_file_full)
    cellpy_data_instance.datasets.append(test[0])


def info(cellpy_data_instance):
    print(f"\nINFO ON {cellpy_data_instance}")
    for dataset in cellpy_data_instance.datasets:
        print(dataset)


def report_time(t1,t2):
    txt = f"used: {t2-t1} seconds"
    print(txt)


def time_routine():
    d = cellreader.CellpyData()

    prms.Instruments["chunk_size"] = 10000  # size pr chunk used by pandas when loading
    prms.Instruments["max_chunks"] = 1  # stops loading when reaching this
    t1 = time.time()

    load_it(d)
    # set new current chunk
    # append_to_it(d)

    t2 = time.time()

    # d.make_step_table()
    # d.make_summary()
    # info(d)

    print("------------------finished------------------")
    report_time(t1, t2)


def missing_stats_file():
    d = cellreader.CellpyData()
    raw_file_loader = d.loader
    test = raw_file_loader(new_arbin_file)
    d.datasets.append(test[0])
    d.set_mass(new_arbin_mass)
    d.make_summary(use_cellpy_stat_file=False)


if __name__ == "__main__":
    missing_stats_file()
