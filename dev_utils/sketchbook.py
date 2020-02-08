import os
import pathlib
import sys
import time

import cellpy
from cellpy import log
from cellpy import cellreader
from cellpy.parameters import prms

print(f"running {sys.argv[0]}")

h5 = pathlib.Path('../testdata/hdf5/20160805_test001_45_cc_01.h5')
res = pathlib.Path('../testdata/data/20160805_test001_45_cc_01.res')


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


def check_split(cell):
    list_of_all_cycles = cell.get_cycle_numbers()
    c1, c2 = cell.split(10)
    list_of_first_cycles = c1.get_cycle_numbers()
    list_of_last_cycles = c2.get_cycle_numbers()
    assert all(list_of_first_cycles == range(1, 10))
    assert list_of_all_cycles[-1] == list_of_last_cycles[-1]


def from_res_to_h5():
    d = get_res_cell()
    d.save(h5)


def main():
    d = get_cellpy_cell()
    list_of_all_cycles = d.get_cycle_numbers()
    c1, c2 = d.split(10)
    list_of_first_cycles = c1.get_cycle_numbers()
    list_of_last_cycles = c2.get_cycle_numbers()

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


if __name__ == '__main__':
    main()
