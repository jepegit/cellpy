from unittest import TestCase
import os
import tempfile
import shutil
import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/data_ex"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir,test_res_file)
test_data_dir_out = os.path.join(test_data_dir, "out")
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir,test_cellpy_file_tmp)
test_run_name = "20160805_test001_45_cc"

# TODO: use only functions where logical (remove TestCase)


class TestDataReaders(TestCase):
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_search_for_files(self):
        import os
        from cellpy import filefinder
        run_files, cellpy_file = filefinder.search_for_files(test_run_name,
                                                             raw_file_dir=test_data_dir,
                                                             cellpy_file_dir=test_data_dir_out)
        assert test_res_file_full in run_files
        assert os.path.basename(cellpy_file) == test_cellpy_file

    def test_set_res_datadir_wrong(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
        d.set_cellpy_datadir(_)
        assert _ != d.cellpy_datadir

    def test_set_res_datadir_none(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.set_cellpy_datadir()
        assert d.cellpy_datadir is None

    def test_set_res_datadir(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.set_cellpy_datadir(test_data_dir)
        assert test_data_dir == d.cellpy_datadir

    def test_load_res(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.loadcell(test_res_file_full)
        run_number = 0
        data_point = 2283
        step_time = 1500.05
        sum_discharge_time = 362198.12
        my_test = d.tests[run_number]
        assert my_test.dfsummary.loc[1,"Data_Point"] == data_point
        assert step_time == pytest.approx(my_test.dfdata.loc[4,"Step_Time"],0.1)
        assert sum_discharge_time == pytest.approx(my_test.dfsummary.loc[:,"Discharge_Time"].sum(),0.1)
        assert my_test.test_no == run_number

        # d.make_summary(find_ir=True)
        # d.create_step_table()
        # d.save_test(test_cellpy_file_full)

    def test_load_cellpyfile(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.load(test_cellpy_file_full)
        run_number = 0
        data_point = 2283
        step_time = 1500.05
        sum_test_time = 9301719.457
        my_test = d.tests[run_number]
        unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        unique_cycles_read = my_test.step_table.loc[:, "cycle"].unique()
        assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
        assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
        assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
        assert sum_test_time == pytest.approx(my_test.dfsummary.loc[:, "Test_Time"].sum(), 0.1)
        assert my_test.test_no == run_number

    def test_save_cellpyfile_with_extension(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.loadcell(test_res_file_full)
        d.make_summary(find_ir=True)
        d.create_step_table()
        tmp_file = next(tempfile._get_candidate_names())+".h5"
        d.save_test(tmp_file)
        assert os.path.isfile(tmp_file)
        os.remove(tmp_file)
        assert not os.path.isfile(tmp_file)

    def test_save_cellpyfile_auto_extension(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.loadcell(test_res_file_full)
        d.make_summary(find_ir=True)
        d.create_step_table()
        tmp_file = next(tempfile._get_candidate_names())
        d.save_test(tmp_file)
        assert os.path.isfile(tmp_file+".h5")
        os.remove(tmp_file+".h5")
        assert not os.path.isfile(tmp_file+".h5")

    def test_save_cvs(self):
        from cellpy import cellreader
        d = cellreader.cellpydata()
        d.loadcell(test_res_file_full)
        d.make_summary(find_ir=True)
        d.create_step_table()
        temp_dir = tempfile.mkdtemp()
        d.exportcsv(datadir=temp_dir)
        shutil.rmtree(temp_dir)
        # d.save_test(tmp_file)
        # assert os.path.isfile(tmp_file)
        # os.remove(tmp_file)
        # assert not os.path.isfile(tmp_file)




    @pytest.mark.unfinished
    def test_set_cellpy_datadir(self):
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
