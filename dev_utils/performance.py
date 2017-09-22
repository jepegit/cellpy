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



# print(prms.Paths)
# print(prms.Reader)
# print(prms.Instruments)
# print(prms.Materials)




d = cellreader.CellpyData()

prms.Instruments["chunk_size"] = 10000  # size pr chunk used by pandas when loading
prms.Instruments["max_chunks"] = 1  # stops loading when reaching this


current_chunk = 0
# prms._res_chunk = current_chunk


t1 = time.time()

load_it(d)
# set new current chunk
# append_to_it(d)

t2 = time.time()


# d.make_step_table()
# d.make_summary()
# info(d)



print("------------------finished------------------")
report_time(t1,t2)




def test_load_res(cellpy_data_instance):
    cellpy_data_instance.loadcell(test_res_file_full)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.datasets[run_number]


    # cellpy_data_instance.make_summary(find_ir=True)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.save(test_cellpy_file_full)
