import os
from psutil import Process


import pytest
import tempfile
import os
import logging
import time

import cellpy.readers.core
from cellpy import log
from cellpy import prms
from cellpy.readers.core import humanize_bytes


log.setup_logging(default_level="DEBUG")


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
        # TODO: fix this
        clean_dir = "xxx"
        f_in = "xxx"
        # new_file = cellreader.load_and_save_resfile(f_in, None, clean_dir)

    g = get_consumed_ram()
    print(humanize_bytes(g))
    run_cellpy_command()
    g = get_consumed_ram()
    print(humanize_bytes(g))


if __name__ == "__main__":
    main()
