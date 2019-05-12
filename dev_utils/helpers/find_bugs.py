"""utility for finding bugs / fixing edge-cases"""

import os
import sys
import time
from pathlib import Path
print(f"running {sys.argv[0]}")

import cellpy
from cellpy import log
from cellpy import cellreader
from cellpy.parameters import prms

prms.Reader.use_cellpy_stat_file = False
prms.Reader.cycle_mode = "cathode"
prms.Reader.sorted_data = False
log.setup_logging(default_level="DEBUG", custom_log_dir=os.getcwd())
datapath = "/Users/jepe/scripting/cellpy/dev_data/bugfixing"

filename = Path(datapath) / "20180919_FC_LFP2_cen14_01_cc_01.res"

assert os.path.isfile(filename)

d = cellreader.CellpyData()
d.from_raw(filename)
d.set_mass(0.12)
d.make_step_table()
d.make_summary()

# checking extracting cycles
n = d.get_number_of_cycles()
c = d.get_cycle_numbers()

# checking creating dqdv
cc = d.get_cap()

d.to_csv(datapath)
