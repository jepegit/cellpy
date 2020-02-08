from pathlib import Path
from cellpy import prms
import cellpy

files = [
    "/Users/jepe/scripting/cellpy/testdata/hdf5/20160805_test001_45_cc.h5",
    "/Users/jepe/scripting/cellpy/testdata/hdf5/20160805_test001_47_cc.h5",
]


def main():
    for f in files:
        print(Path(f).is_file())
        # prms._cellpyfile_step = '/step'
        c = cellpy.get(f)
        # prms._cellpyfile_step = '/steps'
        # c.save(f)


if __name__ == "__main__":
    main()
