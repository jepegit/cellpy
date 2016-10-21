

import sys
import os

from cellpy import cellreader, dbreader, prmreader, filefinder

print "Reading parametres"
prms = prmreader.read()
excel_reader = dbreader.reader()
b_name = "ocvrlx1"
serial_numbers = excel_reader.select_batch(b_name,5)
print " - serial_numbers: "
print serial_numbers
out_dir = r"C:\Cell_data\tmp"

cell_data_dict = {}
for n in serial_numbers:
    my_run_name = excel_reader.get_cell_name(n)

    print "\n - processing: %s" % (my_run_name)
    mass = excel_reader.get_mass(n)
    rawfiles, cellpyfile = filefinder.search_for_files(my_run_name)
    print "   mass: %f" % (mass)
    cell_data_dict[my_run_name] = [mass, rawfiles, cellpyfile]
    print "cellpyfile:", cellpyfile

    cell_data = cellreader.cellpydata()
    try:
        cell_data.loadcell(raw_files=rawfiles, cellpy_file=cellpyfile)
        cell_data.set_mass(mass)
        if not cell_data.summary_exists:
            cell_data.make_summary()
            cell_data.save_test(cellpyfile)
        cell_data_dict[my_run_name].append(True)
    except IOError as e:
        print "ERROR - Could not load (IOError)"
        print e
        cell_data_dict[my_run_name].append(False)
    except MemoryError as e:
        print "ERROR - Could not load (MemoryError)"
        print e
        cell_data_dict[my_run_name].append(False)

for x,y in cell_data_dict.iteritems():
    print x, y




#excel_reader.print_serial_number_info(1759)



# self.a = self.reader.select_batch(self.batch, self.bcol)
#         lena = len(self.a)
#         if lena < 1:
#             print "no experimental runs found"
#             return -1
#         print "list of experimental runs:"
#         print self.a
#
#         print "PROCESSING..."
#         self.get_info()
#         self.load_cells()
#
#         print "EXPORTING..."
#         self.make_diagnostics_plots()
#         for ex in self.plotlist:
#             self.make_datasets(ex)
#             self.save_datasets(ex)
#
#         self.save_raw()
#         self.save_cycles()
#         self.save_dqdv()
#         self.save_hdf5()
