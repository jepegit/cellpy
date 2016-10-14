#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cellpy
----------------------------------

Tests for `cellpy` module.
"""

import os
import pytest

current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_data_dir_out = os.path.join(test_data_dir, "out_cellpytester")


# print test_data_dir

class TestCellpy(object):

    @classmethod
    def setup_class(cls):
        import os
        try:
            os.mkdir(test_data_dir_out)
        except:
            print "could not make directory"

    @pytest.mark.smoketest
    def test_extract_ocvrlx(cls):
        import os
        from cellpy import arbinreader
        f_in = os.path.join(test_data_dir, test_res_file)
        f_out = os.path.join(test_data_dir_out, "out_")
        assert arbinreader.extract_ocvrlx(f_in, f_out) == True

    def test_load_and_save_resfile(cls):
        import os
        from cellpy import arbinreader
        f_in = os.path.join(test_data_dir, test_res_file)
        newfile = arbinreader.load_and_save_resfile(f_in, None, test_data_dir_out)
        assert os.path.isfile(newfile)

    @pytest.mark.slowtest
    @pytest.mark.smoketest
    def test_just_load_srno(cls):
        from cellpy import arbinreader
        assert arbinreader.just_load_srno() == True

    @pytest.mark.smoketest
    def test_setup_cellpy_instance(self):
        from cellpy import arbinreader
        d = arbinreader.setup_cellpy_instance()

    @pytest.mark.unimportant
    def test_humanize_bytes(cls):
        from cellpy import arbinreader
        assert arbinreader.humanize_bytes(1) == '1 byte'
        assert arbinreader.humanize_bytes(1024) == '1.0 kB'
        assert arbinreader.humanize_bytes(1024 * 123) == '123.0 kB'
        assert arbinreader.humanize_bytes(1024 * 12342) == '12.0 MB'
        assert arbinreader.humanize_bytes(1024 * 12342, 2) == '12.00 MB'
        assert arbinreader.humanize_bytes(1024 * 1234, 2) == '1.00 MB'
        assert arbinreader.humanize_bytes(1024 * 1234 * 1111, 2) == '1.00 GB'
        assert arbinreader.humanize_bytes(1024 * 1234 * 1111, 1) == '1.0 GB'

    @classmethod
    def teardown_class(cls):
        import shutil
        shutil.rmtree(test_data_dir_out)
