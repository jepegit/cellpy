import os
import pathlib
import sys
import time

import cellpy
from cellpy import log
from cellpy import cellreader
from cellpy.parameters import prms

print(f"running {sys.argv[0]}")

h5 = pathlib.Path("../testdata/hdf5/20160805_test001_45_cc_01.h5")
res = pathlib.Path("../testdata/data/20160805_test001_45_cc_01.res")


def get_res_cell():
    p = pathlib.Path(res)
    print(f"Loading file from {p} (exists={p.is_file()})")
    d = cellpy.get(p)
    return d


def get_cellpy_cell():
    p = pathlib.Path(h5)
    print(f"Loading file from {p} (exists={p.is_file()})")
    d = cellpy.get(p)
    return d


def from_res_to_h5():
    d = get_res_cell()
    d.save(h5)


def check_splitting():
    d = get_cellpy_cell()
    list_of_all_cycles = d.get_cycle_numbers()
    c1, c2 = d.split(10)

    print(list_of_all_cycles)
    print(" split ".center(80, "="))
    print("c1".center(80, "-"))
    print(c1.get_cycle_numbers())
    print("c2".center(80, "-"))
    print(c2.get_cycle_numbers())

    c1, c2 = d.split_many(10)

    print(" split many ".center(80, "="))
    print("c1".center(80, "-"))
    print(c1.get_cycle_numbers())
    print("c2".center(80, "-"))
    print(c2.get_cycle_numbers())

    print(" drop_to ".center(80, "="))
    c1 = d.drop_to(10)
    print("c1".center(80, "-"))
    print(c1.get_cycle_numbers())

    print(" drop_from ".center(80, "="))
    c1 = d.drop_from(10)
    print("c1".center(80, "-"))
    print(c1.get_cycle_numbers())

    print(" drop_edges ".center(80, "="))
    c1 = d.drop_edges(8, 12)
    print("c1".center(80, "-"))
    print(c1.get_cycle_numbers())

    print("empty split".center(80, "="))
    print(d.split())


def investigate_cols(d):
    summary = d.cell.summary
    steps = d.cell.steps
    raw = d.cell.raw

    for n, s in zip(["summary", "steps", "raw"], [summary, steps, raw]):
        print(n.center(80, "-"))
        print(s.index.name)
        print(s.columns[0:3])


def main():
    d = get_cellpy_cell()
    r = get_res_cell()

    print("\n", "FROM CELLPY FILE".center(80, "="))
    investigate_cols(d)

    print("\n", "FROM RAW FILE".center(80, "="))
    investigate_cols(r)

    print("\n", "FROM RAW FILE AFTER MAKE STP".center(80, "="))
    r.make_step_table()
    investigate_cols(r)

    print("\n", "FROM RAW FILE AFTER MAKE SUMMARY".center(80, "="))
    r.make_summary()
    investigate_cols(r)


if __name__ == "__main__":
    main()
