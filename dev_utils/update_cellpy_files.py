import pathlib
import os
import sys

import cellpy
from cellpy import cellreader
from cellpy import log

log.setup_logging(default_level="DEBUG")


def load_c_file(filename):
    c = cellreader.CellpyData()
    c.load(filename)
    return c


def load_r_file(filename):
    c = cellreader.CellpyData()
    c.from_raw(filename)
    return c


def update(c):
    c.make_step_table()
    c.make_summary(find_ir=True)
    return c


print("updating cellpy files")
hdf_dir = pathlib.Path("../testdata/hdf5").resolve()
res_dir = pathlib.Path("../testdata/data").resolve()

print(f"cellpy file directory: {hdf_dir.is_dir()}")
files = os.listdir(hdf_dir)
print(f"content: {files}")

print(f"raw file directory: {res_dir.is_dir()}")
files = os.listdir(res_dir)
print(f"content: {files}")

standard_file = hdf_dir / "20160805_test001_45_cc.h5"
extra_file = hdf_dir / "20160805_test001_47_cc.h5"
standard_raw_file = res_dir / "20160805_test001_45_cc_01.res"

updated_standard_file = hdf_dir / "20160805_test001_45_cc.h5"
updated_extra_file = hdf_dir / "20160805_test001_45_cc.h5"

c = load_r_file(standard_raw_file)
print(f"{c.cell.raw.columns}")
c.make_step_table()
c.make_summary(find_ir=True)


print(f"loading standard file {standard_file}")
c = load_c_file(standard_file)
print("updating")
c = update(c)
print(f"saving")
c.save(updated_standard_file)


print(f"loading standard file {extra_file}")
c = load_c_file(extra_file)
print("updating")
c = update(c)
print(f"saving")
c.save(updated_extra_file)
