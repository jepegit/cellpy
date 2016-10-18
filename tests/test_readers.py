from unittest import TestCase
import os
from cellpy import cellreader

import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_data_dir_out = os.path.join(test_data_dir, "out")


class TestDataReaders(TestCase):
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    @pytest.mark.unfinished
    def test_set_res_datadir(self):
        assert True

    @pytest.mark.unfinished
    def test_set_hdf5_datadir(self):
        assert True

    @pytest.mark.unfinished
    def test_check_file_ids(self):
        assert True

    @pytest.mark.unfinished
    def test__check_res(self):
        assert True

    @pytest.mark.unfinished
    def test__check_hdf5(self):
        assert True

    @pytest.mark.unfinished
    def test__compare_ids(self):
        assert True

    @pytest.mark.unfinished
    def test__find_resfiles(self):
        assert True

    @pytest.mark.unfinished
    def test_loadcell(self):
        assert True

    @pytest.mark.unfinished
    def test_loadres(self):
        assert True

    @pytest.mark.unfinished
    def test__validate_tests(self):
        assert True

    @pytest.mark.unfinished
    def test__is_not_empty_test(self):
        assert True

    @pytest.mark.unfinished
    def test__report_empty_test(self):
        assert True

    @pytest.mark.unfinished
    def test__empty_test(self):
        assert True

    @pytest.mark.unfinished
    def test__check64bit(self):
        assert True

    @pytest.mark.unfinished
    def test__loadh5(self):
        assert True

    @pytest.mark.unfinished
    def test__convert2fid_list(self):
        assert True

    @pytest.mark.unfinished
    def test__clean_up_loadres(self):
        assert True

    @pytest.mark.unfinished
    def test__loadres(self):
        assert True

    @pytest.mark.unfinished
    def test_merge(self):
        assert True

    @pytest.mark.unfinished
    def test__append(self):
        assert True

    @pytest.mark.unfinished
    def test__validate_test_number(self):
        assert True

    @pytest.mark.unfinished
    def test__validata_step_table(self):
        assert True

    @pytest.mark.unfinished
    def test_print_step_table(self):
        assert True

    @pytest.mark.unfinished
    def test_get_step_numbers(self):
        assert True

    @pytest.mark.unfinished
    def test__extract_step_values(self):
        assert True

    @pytest.mark.unfinished
    def test_create_step_table(self):
        assert True

    @pytest.mark.unfinished
    def test__percentage_change(self):
        assert True

    @pytest.mark.unfinished
    def test_select_steps(self):
        assert True

    @pytest.mark.unfinished
    def test__select_step(self):
        assert True

    @pytest.mark.unfinished
    def test_populate_step_dict(self):
        assert True

    @pytest.mark.unfinished
    def test_find_C_rates(self):
        assert True

    @pytest.mark.unfinished
    def test_find_C_rates_old(self):
        assert True

    @pytest.mark.unfinished
    def test__export_cycles(self):
        assert True

    @pytest.mark.unfinished
    def test__export_normal(self):
        assert True

    @pytest.mark.unfinished
    def test__export_stats(self):
        assert True

    @pytest.mark.unfinished
    def test__export_steptable(self):
        assert True

    @pytest.mark.unfinished
    def test_exportcsv(self):
        assert True

    @pytest.mark.unfinished
    def test_save_test(self):
        assert True

    @pytest.mark.unfinished
    def test__create_infotable(self):
        assert True

    @pytest.mark.unfinished
    def test__cap_mod_summary(self):
        assert True

    @pytest.mark.unfinished
    def test__cap_mod_normal(self):
        assert True

    @pytest.mark.unfinished
    def test_get_number_of_tests(self):
        assert True

    @pytest.mark.unfinished
    def test_get_mass(self):
        assert True

    @pytest.mark.unfinished
    def test_get_test(self):
        assert True

    @pytest.mark.unfinished
    def test_sget_voltage(self):
        assert True

    @pytest.mark.unfinished
    def test_get_voltage(self):
        assert True

    @pytest.mark.unfinished
    def test_get_current(self):
        assert True

    @pytest.mark.unfinished
    def test_sget_steptime(self):
        assert True

    @pytest.mark.unfinished
    def test_sget_timestamp(self):
        assert True

    @pytest.mark.unfinished
    def test_get_timestamp(self):
        assert True

    @pytest.mark.unfinished
    def test_get_dcap(self):
        assert True

    @pytest.mark.unfinished
    def test_get_ccap(self):
        assert True

    @pytest.mark.unfinished
    def test_get_cap(self):
        assert True

    @pytest.mark.unfinished
    def test__polarization(self):
        assert True

    @pytest.mark.unfinished
    def test__get_cap(self):
        assert True

    @pytest.mark.unfinished
    def test_get_ocv(self):
        assert True

    @pytest.mark.unfinished
    def test__get_ocv(self):
        assert True

    @pytest.mark.unfinished
    def test_get_number_of_cycles(self):
        assert True

    @pytest.mark.unfinished
    def test_get_cycle_numbers(self):
        assert True

    @pytest.mark.unfinished
    def test_get_ir(self):
        assert True

    @pytest.mark.unfinished
    def test_get_diagnostics_plots(self):
        assert True

    @pytest.mark.unfinished
    def test_get_cycle(self):
        assert True

    @pytest.mark.unfinished
    def test_set_mass(self):
        assert True

    @pytest.mark.unfinished
    def test_set_col_first(self):
        assert True

    @pytest.mark.unfinished
    def test_set_testnumber_force(self):
        assert True

    @pytest.mark.unfinished
    def test_set_testnumber(self):
        assert True

    @pytest.mark.unfinished
    def test_get_summary(self):
        assert True

    @pytest.mark.unfinished
    def test_is_empty(self):
        assert True

    @pytest.mark.unfinished
    def test__is_listtype(self):
        assert True

    @pytest.mark.unfinished
    def test__check_file_type(self):
        assert True

    @pytest.mark.unfinished
    def test__bounds(self):
        assert True

    @pytest.mark.unfinished
    def test__roundup(self):
        assert True

    @pytest.mark.unfinished
    def test__rounddown(self):
        assert True

    @pytest.mark.unfinished
    def test__reverse(self):
        assert True

    @pytest.mark.unfinished
    def test__select_y(self):
        assert True

    @pytest.mark.unfinished
    def test__select_last(self):
        assert True

    @pytest.mark.unfinished
    def test__extract_from_dict(self):
        assert True

    @pytest.mark.unfinished
    def test__modify_cycle_number_using_cycle_step(self):
        assert True

    @pytest.mark.unfinished
    def test_make_summary(self):
        assert True

    @pytest.mark.unfinished
    def test__make_summary(self):
        assert True


class TestDBReader(TestCase):
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_filter_selected(self):
        from cellpy import dbreader
        assert True

    @pytest.mark.unfinished
    def test__pick_info(self):
        from cellpy import dbreader
        assert True

    def test__open_sheet(self):
        assert True

    def test_select_serial_number_row(self):
        assert True

    def test_print_serial_number_info(self):
        assert True

    def test_filter_by_slurry(self):
        assert True

    def test_filter_by_col(self):
        assert True

    def test_filter_by_col_value(self):
        assert True

    def test_select_batch(self):
        assert True

    def test_help_pandas(self):
        assert True

    def test_select_col(self):
        assert True

    def test_get_resfilenames(self):
        assert True

    def test_get_hdf5filename(self):
        assert True

    def test_get_filenames(self):
        assert True

    def test_filter_selected(self):
        assert True

    def test_inspect_finished(self):
        assert True

    def test_inspect_hd5f_fixed(self):
        assert True

    def test_inspect_hd5f_exists(self):
        assert True

    def test_inspect_exists(self):
        assert True

    def test_get_label(self):
        assert True

    def test_get_cell_name(self):
        assert True

    def test_get_comment(self):
        assert True

    def test_get_group(self):
        assert True

    def test_get_loading(self):
        assert True

    def test_get_mass(self):
        assert True

    def test_get_total_mass(self):
        assert True

    def test_get_all(self):
        assert True

    def test_get_fileid(self):
        assert True

    def test_intersect(self):
        assert True

    def test_union(self):
        assert True

    def test_substract(self):
        assert True

    def test_substract_many(self):
        assert True
