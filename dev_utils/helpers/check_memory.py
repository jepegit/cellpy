import os
from psutil import Process
from pathlib import Path

import pytest
import tempfile
import os
import logging
import time

import cellpy.readers.core
import cellpy.utils.helpers
from cellpy import log
from cellpy import prms
from cellpy.readers.core import humanize_bytes

f_in = Path("../testdata/data/20160805_test001_45_cc_01.res")
# /Users/jepe/scripting/cellpy/dev_utils/check_memory.py
# /Users/jepe/scripting/cellpy/testdata/data/20160805_test001_45_cc_01.res
log.setup_logging(default_level="INFO")


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.mark.timeout(1.0)
def test_load_big_file(clean_dir):
    # TODO: make test that reads a big file
    pass


def main():
    print("running memory leak detection")
    _proc = Process(os.getpid())
    print(_proc)

    def get_consumed_ram():
        return _proc.memory_info().rss

    def run_cellpy_command():
        from cellpy import cellreader

        clean_dir = tempfile.mkdtemp()
        return cellpy.utils.helpers.load_and_save_resfile(f_in, None, clean_dir)

    g0 = get_consumed_ram()
    cum_g = 0
    print(80 * "=")
    print(f"Memory usage start: {humanize_bytes(g0)} ({g0} b)")
    print(80 * "=")
    for j in range(20):
        run_cellpy_command()
        g = get_consumed_ram()
        cum_g += g - g0
        print(80 * "=")
        print(
            f"Memory usage [{j}]: {humanize_bytes(g)} ({g} b) "
            f"[delta: {humanize_bytes(g - g0)} ({g - g0}) b]"
        )
        print(80 * "=")
        g0 = g

    print(f"Total memory leak: {humanize_bytes(cum_g)}")


if __name__ == "__main__":
    main()
