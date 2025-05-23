"""Files, Directories, and Variables to be used in the tests.

Notes:
    This only works for running the test-runner (pytest) on the test-files!

"""

import os
from pathlib import Path
from cellpy.internals.core import OtherPath


def get_cellpy_file_path(raw_path):
    cellpy_extension = ".h5"
    raw_path = OtherPath(raw_path)
    raw_name = raw_path.stem + cellpy_extension
    p = os.path.join(cellpy_data_dir, raw_name)
    return p


# -------- defining cellpy environment vars ---------
# used in the conftest.py file for creating the mock environment
# note! these should be the same as the ones in the .env_cellpy_test file
env_cellpy_user = "cellpy"
env_cellpy_password = "cellpy!test!password"
env_cellpy_key_filename = ".ssh/id_rsa"
env_cellpy_host = "cellpy.test.host"

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
_relative_data_dir = "../testdata"
data_dir = os.path.abspath(os.path.join(current_file_path, _relative_data_dir))
raw_data_dir = os.path.join(data_dir, "data")
output_dir = os.path.join(data_dir, "out")
cellpy_data_dir = os.path.join(data_dir, "hdf5")
db_dir = os.path.join(data_dir, "db")
journal_dir = os.path.join(data_dir, "journal")
batch_file_dir = os.path.join(data_dir, "batchfiles")
log_dir = os.path.join(data_dir, "log")
instrument_dir = os.path.join(data_dir, "instruments")
template_dir = os.path.join(data_dir, "templates")
examples_dir = os.path.join(data_dir, "examples")
default_prm_file = os.path.abspath(os.path.join(data_dir, ".cellpy_prms_default.conf"))
env_file = os.path.abspath(os.path.join(data_dir, ".env_cellpy_test"))

# -------- common files -----------------------------
cellpy_file_name = "20160805_test001_45_cc.h5"
cellpy_file_path = os.path.join(cellpy_data_dir, cellpy_file_name)

cellpy_file_path_external = "scp://jepe@server.no/home/jepe/data/20160805_test001_45_cc.h5"

# old format (to check compatibility when upgrading cellpy format)
cellpy_file_name_v4 = "20160805_test001_45_cc_v0.h5"
cellpy_file_path_v4 = os.path.join(cellpy_data_dir, cellpy_file_name_v4)

cellpy_file_name_v5 = "20160805_test001_45_cc_v6.h5"
cellpy_file_path_v5 = os.path.join(cellpy_data_dir, cellpy_file_name_v5)

cellpy_file_name_v6 = "20160805_test001_45_cc_v6.h5"
cellpy_file_path_v6 = os.path.join(cellpy_data_dir, cellpy_file_name_v6)

temporary_cellpy_file_name = "tmpfile.h5"
temporary_cellpy_file_path = os.path.join(cellpy_data_dir, temporary_cellpy_file_name)

db_file_name = "cellpy_db.xlsx"
db_file_path = os.path.join(db_dir, db_file_name)

step_table_file_name = "steps.csv"
step_table_file_path = os.path.join(raw_data_dir, step_table_file_name)

short_step_table_file_name = "steps_short.csv"
short_step_table_file_path = os.path.join(raw_data_dir, short_step_table_file_name)

run_name = "20160805_test001_45_cc"
run_name_2 = "20160805_test001_46_cc"
run_name_maccor = "maccor_001"

# -------- experiment specific files ----------------

full_cell_name = "full_cell.res"
full_cell_path = os.path.join(raw_data_dir, full_cell_name)

constant_voltage_cell_name = "constant_voltage_cell.res"
constant_voltage_cell_path = os.path.join(raw_data_dir, constant_voltage_cell_name)

taper_cell_name = "taper_cell.res"
taper_cell_path = os.path.join(raw_data_dir, taper_cell_name)

gitt_cell_name = "gitt_cell.res"
gitt_cell_path = os.path.join(raw_data_dir, gitt_cell_name)

rate_cell_name = "20231115_rate_cc.h5"
rate_cell_path = os.path.join(raw_data_dir, rate_cell_name)

# -------- mock data files  -------------------------

mock_file_name = "mock_data_001.xlsx"
mock_file_path = os.path.join(raw_data_dir, mock_file_name)

# -------- arbin specific files ---------------------

res_file_name = "20160805_test001_45_cc_01.res"
res_file_path = os.path.join(raw_data_dir, res_file_name)
res_file_path_external = "scp://jepe@server.no/home/jepe/data/20160805_test001_45_cc_01.res"

res_file_name2 = "20160805_test001_45_cc_02.res"
res_file_path2 = os.path.join(raw_data_dir, res_file_name2)

res_file_name3 = "aux_multi_x.res"
res_file_path3 = os.path.join(raw_data_dir, res_file_name3)

res_file_name4 = "aux_one_x_dx.res"
res_file_path4 = os.path.join(raw_data_dir, res_file_name4)

arbin_sql_h5_name = "20200624_test001_cc_01.h5"
arbin_sql_h5_path = os.path.join(raw_data_dir, arbin_sql_h5_name)


# -------- biologics specific files -----------------
mpr_file_name = "biol.mpr"
mpr_file_path = os.path.join(raw_data_dir, mpr_file_name)

mpr_cellpy_file_name = "biol.h5"
mpr_cellpy_file_path = os.path.join(cellpy_data_dir, mpr_cellpy_file_name)

# -------- maccor specific files -----------------
mcc_file_name = "maccor_001.txt"
mcc_file_path = os.path.join(raw_data_dir, mcc_file_name)

mcc_cellpy_file_name = "maccor_001.h5"
mcc_cellpy_file_path = os.path.join(cellpy_data_dir, mcc_cellpy_file_name)

mcc_file_name2 = "maccor_002.txt"
mcc_file_path2 = os.path.join(raw_data_dir, mcc_file_name2)

mcc_cellpy_file_name2 = "maccor_002.h5"
mcc_cellpy_file_path2 = os.path.join(cellpy_data_dir, mcc_cellpy_file_name2)

# -------- neware specific files --------------------
nw_file_name = "neware_uio.csv"
nw_file_path = os.path.join(raw_data_dir, nw_file_name)

nw_cellpy_file_name = "neware_uio.h5"
nw_cellpy_file_path = os.path.join(cellpy_data_dir, nw_cellpy_file_name)

# -------- pec specific files -----------------------
pec_file_name = "pec.csv"
pec_file_path = os.path.join(raw_data_dir, pec_file_name)

pec_cellpy_file_name = "pec.h5"
pec_cellpy_file_path = os.path.join(cellpy_data_dir, pec_cellpy_file_name)

# -------- some values set used by the old batch ----
example_file_for_batch = "20160805_test001_45_cc_01_cycles.csv"
tot_cycles = 34

# -------- new batch --------------------------------
pages = "cellpy_batch_test.json"
pages = os.path.join(db_dir, pages)

# -------- new journal ------------------------------
journal_file_json = "test_journal.json"
journal_file_xlsx = "test_journal.xlsx"
journal_file_full_xlsx = "test_journal_full.xlsx"

journal_file_json_path = os.path.join(journal_dir, journal_file_json)
journal_file_xlsx_path = os.path.join(journal_dir, journal_file_xlsx)
journal_file_full_xlsx_path = os.path.join(journal_dir, journal_file_full_xlsx)

# -------- custom file format -----------------------
custom_file_name = "custom_data_001.csv"
custom_file_paths = os.path.join(raw_data_dir, custom_file_name)

custom_instrument_1 = "custom_instrument_001.yml"
custom_instrument_definitions_file = os.path.join(raw_data_dir, custom_instrument_1)

custom_instrument_2 = "custom_instrument_002.yml"
custom_file_paths_2 = os.path.join(raw_data_dir, "custom_data_002.csv")

custom_instrument_3 = "custom_instrument_003.yml"
custom_file_paths_3 = os.path.join(raw_data_dir, "custom_data_002.csv")


# -------- custom new file format -------------------
custom_instrument = "maccor_one.yml"
custom_instrument_path = os.path.join(instrument_dir, custom_instrument)


# ---------- gitt data -------------------------------
gitt_file_name = "20210210_FC.h5"
gitt_file_path = os.path.join(raw_data_dir, gitt_file_name)

if __name__ == "__main__":
    files = [
        cellpy_file_path,
        cellpy_file_path_v4,
        res_file_path,
        res_file_path2,
        temporary_cellpy_file_path,
    ]
    print(" Checking existence of test files ".center(80, "-"))
    for file in files:
        print(file, end=": ")
        print(Path(file).is_file())
