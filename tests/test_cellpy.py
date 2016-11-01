#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cellpy
----------------------------------

Tests for `cellpy` module.
"""

import os
import pytest
import tempfile

current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/data_ex"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_data_dir_out = os.path.join(test_data_dir, "out_cellpytester")


@pytest.fixture(scope="module")
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.cellpydata()


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def setup_module():
    import os
    try:
        os.mkdir(test_data_dir_out)
    except:
        print "could not make directory"


@pytest.mark.smoketest
def test_extract_ocvrlx(clean_dir):
    import os
    from cellpy import cellreader
    f_in = os.path.join(test_data_dir, test_res_file)
    f_out = os.path.join(clean_dir, "out_")
    assert cellreader.extract_ocvrlx(f_in, f_out) == True


def test_load_and_save_resfile(clean_dir):
    import os
    from cellpy import cellreader
    f_in = os.path.join(test_data_dir, test_res_file)
    new_file = cellreader.load_and_save_resfile(f_in, None, clean_dir)
    assert os.path.isfile(new_file)


def test_su_cellpy_instance():
    # somehow pytest fails to find the test if it is called test_setup_xxx
    from cellpy import cellreader
    cellreader.setup_cellpy_instance()


@pytest.mark.slowtest
@pytest.mark.smoketest
def test_just_load_srno():
    from cellpy import cellreader
    assert cellreader.just_load_srno(614) is True


@pytest.mark.smoketest
def test_setup_cellpy_instance():
    from cellpy import cellreader
    d = cellreader.setup_cellpy_instance()


@pytest.mark.unimportant
def test_humanize_bytes():
    from cellpy import cellreader
    assert cellreader.humanize_bytes(1) == '1 byte'
    assert cellreader.humanize_bytes(1024) == '1.0 kB'
    assert cellreader.humanize_bytes(1024 * 123) == '123.0 kB'
    assert cellreader.humanize_bytes(1024 * 12342) == '12.0 MB'
    assert cellreader.humanize_bytes(1024 * 12342, 2) == '12.00 MB'
    assert cellreader.humanize_bytes(1024 * 1234, 2) == '1.00 MB'
    assert cellreader.humanize_bytes(1024 * 1234 * 1111, 2) == '1.00 GB'
    assert cellreader.humanize_bytes(1024 * 1234 * 1111, 1) == '1.0 GB'


def teardown_module():
    import shutil
    shutil.rmtree(test_data_dir_out)
