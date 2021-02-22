from pathlib import Path
from cellpy import prms
import cellpy

raw_files = [
    [
        "/Users/jepe/scripting/cellpy/testdata/data/20160805_test001_45_cc_01.res",
        "/Users/jepe/scripting/cellpy/testdata/data/20160805_test001_45_cc_02.res",
    ],
    "/Users/jepe/scripting/cellpy/testdata/data/20160805_test001_47_cc_01.res",
]

files = [
    "/Users/jepe/scripting/cellpy/testdata/hdf5/20160805_test001_45_cc.h5",
    "/Users/jepe/scripting/cellpy/testdata/hdf5/20160805_test001_47_cc.h5",
]


def from_raw():
    for f, fc in zip(raw_files, files):
        print(f)
        print("->")
        print(fc)
        # print(Path(f).is_file())
        # prms._cellpyfile_step = '/step'
        c = cellpy.get(f)
        # prms._cellpyfile_step = '/steps'
        print(c.cell.summary.head())
        c.save(fc)


def from_cellpy():
    for f in files:
        print(f)
        print(Path(f).is_file())
        # prms._cellpyfile_step = '/step'
        c = cellpy.get(f)
        # prms._cellpyfile_step = '/steps'
        print(c.cell.summary.head())
        # c.save(f)


if __name__ == "__main__":
    from_cellpy()
