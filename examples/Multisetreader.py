from pathlib import Path
import os
import cellpy
from cellpy import cellreader
from cellpy.readers.instruments.arbin_res import ArbinLoader as RawLoader




raw_data_dir = r"C:\Users\mkolen\Google Drive\PhD\Python\res files"
out_data_dir = r"C:\Users\mkolen\Google Drive\PhD\Python\results"
#out_data_dir = r"O:\Data\Arbin"
cellpy_data_dir = r"C:\Users\mkolen\Google Drive\PhD\Python\cellpy"
cycle_mode = "cathode" # default is usually "anode", but...
# These can also be set in the configuration file

p=Path(raw_data_dir)

electrode_mass = 0.658 # active mass of electrode in mg

# list of files to read (Arbin .res type):
raw_file = ["MK-Ag-prelectrolysis-500uA.res"]
# the second file is a 'continuation' of the first file...

# list consisting of file names with full path
raw_files = [os.path.join(raw_data_dir, f) for f in raw_file]

# creating the CellpyData object and sets the cycle mode:
d = cellreader.CellpyData()
d.cycle_mode = cycle_mode



#print(type (l))



for resFile in p.glob('*.res'):
    d.from_raw(resFile)
    #d.make_summary()
    #d.make_step_table()
    d.to_csv(out_data_dir, sep=",")
