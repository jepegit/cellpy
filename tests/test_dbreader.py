import pytest
from . import fdv

# parameters and variables specific for this module
test_serial_number_one = 614
test_serial_number_two = 615
test_serial_number_not_in_batch = 621
test_serial_number_labeled_not_existing = 620
test_serial_number_labeled_eis = 620
slurry_name = "test001"
test_batch_name = "exp001"
test_mass = 0.5103
test_loading = 0.96  # 0.29
test_total_mass = 2.831
test_areal_loading = 0.0


@pytest.fixture(scope="module")
def db_reader():
    from cellpy.readers import dbreader
    from cellpy.parameters import prms

    prms.Paths["outdatadir"] = fdv.output_dir
    prms.Paths["rawdatadir"] = fdv.raw_data_dir
    prms.Paths["cellpydatadir"] = fdv.cellpy_data_dir
    prms.Paths["db_path"] = fdv.db_dir
    prms.Paths["db_filename"] = fdv.db_file_name
    return dbreader.Reader()


@pytest.fixture
def clean_db_reader():  # remove this?
    from cellpy.readers import dbreader

    return dbreader.Reader()


def test_filter_select_col_numbers_true_false(db_reader):
    column_names = ["finished", "freeze"]
    assert db_reader.filter_by_col(column_names) == test_serial_number_one


def test_filter_select_col_numbers_true(db_reader):
    column_numbers = ["freeze"]
    serial_numbers = db_reader.filter_by_col(column_numbers)
    assert serial_numbers.min() == test_serial_number_one
    assert len(serial_numbers) == 1


def test_filter_select_col_numbers_true_true(db_reader):
    column_numbers = ["finished", "freeze"]
    serial_numbers = db_reader.filter_by_col(column_numbers)
    assert len(serial_numbers) == 1
    assert serial_numbers == [test_serial_number_one]


def test_select_serial_number_row(db_reader):
    row = db_reader.select_serial_number_row(test_serial_number_one)
    assert row.iloc[:, 1].values[0] == 45


def test_print_serial_number_info(db_reader):
    output = db_reader.print_serial_number_info(
        test_serial_number_one, print_to_screen=False
    )
    test_serial_number_one_txt = str(test_serial_number_one)
    assert output.find(test_serial_number_one_txt) > -1


def test_filter_by_slurry(db_reader):
    output = db_reader.filter_by_slurry(slurry_name)
    assert test_serial_number_one in output


def test_filter_by_col_value(db_reader):
    output = db_reader.filter_by_col_value(
        db_reader.db_sheet_cols.active_material, min_val=0.5, max_val=0.6
    )
    assert test_serial_number_one in output
    assert test_serial_number_two not in output


def test_select_batch(db_reader):
    output = db_reader.select_batch(test_batch_name, db_reader.db_sheet_cols.batch)
    print(test_batch_name)
    assert test_serial_number_not_in_batch not in output
    assert test_serial_number_one in output
    assert test_serial_number_labeled_not_existing not in output


def test_select_batch_extra(db_reader):
    output = db_reader.select_batch(
        test_batch_name, db_reader.db_sheet_cols.sub_batch_01
    )
    assert test_serial_number_one not in output
    assert test_serial_number_two in output
    assert test_serial_number_labeled_not_existing not in output


# def test_get_raw_filenames(db_reader):
#     output = db_reader.get_raw_filenames(test_serial_number_one)
#     assert test_res_file_full == output[0]
#     assert os.path.isfile(output[0])
#
#
# def test_get_cellpy_filename(db_reader):
#     output = db_reader.get_cellpy_filename(test_serial_number_one)
#     assert test_cellpy_file_full == output[0]
#     assert os.path.isfile(output[0])
#
#
# def test_get_filenames(db_reader):
#     output = db_reader.get_filenames(test_serial_number_one)
#     assert test_cellpy_file_full == output[0]
#     assert os.path.isfile(output[0])
#     output = db_reader.get_filenames(test_serial_number_one, use_hdf5=False)
#     assert not test_cellpy_file_full == output[0]
#     assert test_res_file_full == output[0]


def test_filter_selected(db_reader):
    selected = [test_serial_number_one, test_serial_number_two]
    output = db_reader.filter_selected(selected)
    assert test_serial_number_two in output


#    assert test_serial_number_one not in output


def test_inspect_hd5f_fixed(db_reader):
    assert db_reader.inspect_hd5f_fixed(test_serial_number_one)
    assert not db_reader.inspect_hd5f_fixed(test_serial_number_two)


def test_inspect_exists(db_reader):
    assert db_reader.inspect_exists(test_serial_number_one)
    assert not db_reader.inspect_exists(test_serial_number_labeled_not_existing)


def test_get_label(db_reader):
    output = db_reader.get_label(test_serial_number_one)
    assert output == "test"


def test_get_cell_name(db_reader):
    output = db_reader.get_cell_name(test_serial_number_one)
    assert output == fdv.run_name


def test_get_comment(db_reader):
    output = db_reader.get_comment(test_serial_number_one)
    assert output == "test comment general"


def test_get_group(db_reader):
    output = db_reader.get_group(test_serial_number_one)
    assert int(output) == 1


def test_get_loading(db_reader):
    output = db_reader.get_loading(test_serial_number_one)
    assert pytest.approx(output, 0.1) == test_loading


def test_get_areal_loading(db_reader):
    try:
        output = db_reader.get_areal_loading(test_serial_number_one)
        assert False
    except NotImplementedError:
        assert True
    # assert pytest.approx(output, 0.1) == test_areal_loading


def test_get_mass(db_reader):
    output = db_reader.get_mass(test_serial_number_one)
    assert pytest.approx(output, 0.1) == test_mass


def test_get_total_mass(db_reader):
    output = db_reader.get_total_mass(test_serial_number_one)
    assert pytest.approx(output, 0.1) == test_total_mass


#
# def test_get_all(db_reader):
#     assert True
#
#
# def test_get_fileid(db_reader):
#     assert True
#
#
# def test_intersect(db_reader):
#     assert True
#
#
# def test_union(db_reader):
#     assert True
#
#
# def test_substract(db_reader):
#     assert True
#
#
# def test_substract_many(db_reader):
#     assert True
