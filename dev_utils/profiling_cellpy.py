from pathlib import Path
import os

from cellpy import cellreader
from cellpy import log

from line_profiler import LineProfiler

log.setup_logging(default_level="DEBUG")

current_file_path = os.path.dirname(os.path.realpath(__file__))
_relative_data_dir = "../testdata"
data_dir = os.path.abspath(os.path.join(current_file_path, _relative_data_dir))

raw_data_dir = os.path.join(data_dir, "data")
res_file_name = "20160805_test001_45_cc_01.res"
res_file_path = Path(raw_data_dir) / res_file_name


def make_a_step_table(cellpy_data_instance):
    cellpy_data_instance.make_step_table()


cellpy_data_instance = cellreader.CellpyData()
cellpy_data_instance.from_raw(res_file_path)
cellpy_data_instance.set_mass(1.0)

lp = LineProfiler()
lp_wrapper = lp(make_a_step_table)
lp_wrapper(cellpy_data_instance)
lp.print_stats()
