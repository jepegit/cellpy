"""

"""

import os
import glob
import collections
from cellpy.parametres import prmreader


def search_for_files(run_name, raw_extension=None, cellpy_file_extension=None,
                     raw_file_dir=None, cellpy_file_dir=None, prm_filename = None,
                     file_name_format = None):

    hdf5_extension = ".h5"
    res_extension = ".res"

    if raw_extension is None:
        raw_extension = res_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = hdf5_extension

    if not all([raw_file_dir,cellpy_file_dir,file_name_format]):
        prms = prmreader.read(prm_filename)

    if raw_file_dir is None:
        raw_file_dir = prms.resdatadir

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.hdf5datadir

    print "run_name:", run_name
    print "raw_extension:", raw_extension
    print "cellpy_file_extension:", cellpy_file_extension
    print "raw_file_dir:", raw_file_dir
    print "cellpy_file_dir:", cellpy_file_dir

    if file_name_format is None:
        try:
            file_name_format = prms.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"
            print "Could not read file_name_format from _cellpy_prms_xxx.ini."
            print "Using:"
            print "file_name_format:", file_name_format
            file_format_explanation = "YYYYMMDD is date, EEE is electrode number "
            file_format_explanation += "CC is cell number, TT is cell_type, RR is run number."
            print file_format_explanation

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        glob_text = "%s_*_"
    else:
        glob_text = file_name_format

    # # TODO: regular expression / glob , instead of looping
    # files = collections.OrderedDict()
    # for name in names:
    #     files[name] = []
    #     for j in range(counter_min, counter_max + 1):
    #         if counter_pos.lower() == "last":
    #             lookFor = "%s%s%s%s" % (name, counter_sep,
    #                                     str(j).zfill(counter_digits),
    #                                     res_extension)
    #         elif counter_pos.lower() == "first":
    #             lookFor = "%s%s%s%s" % (str(j).zfill(counter_digits), counter_sep,
    #                                     name, res_extension)
    #         else:
    #             lookFor = "%s%s%s%s" % (name, counter_sep,
    #                                     str(j).zfill(counter_digits),
    #                                     res_extension)
    #
    #         lookFor = os.path.join(res_dir, lookFor)
    #         if os.path.isfile(lookFor):
    #             files[name].append(lookFor)
    #
    # list_of_files = []
    # res_loading = False
    # masses_needed = []
    # test_number = 0
    # res_test_numbers = []
    # res_masses = []
    # counter = -1
    # for name, resfiles in files.items():
    #     counter += 1
    #     this_mass_needed = False
    #     missingRes = False
    #     missingHdf5 = False
    #
    #     #            print "checking",
    #     #            print name,
    #     #            print ":",
    #     #            print resfiles
    #
    #     if len(resfiles) == 0:
    #         wtxt = "WARNING (loadcell): %s - %s" % (name, "could not find any res-files")
    #         print wtxt
    #         missingRes = True
    #
    #     hdf5 = os.path.join(hdf5_dir, name + hdf5_extension)
    #
    #     if not os.path.isfile(hdf5) and not res:
    #         wtxt = "WARNING (loadcell): %s - %s" % (name, "hdf5-file not found")
    #         print wtxt
    #
    #         missingHdf5 = True
    #
    #     if missingRes and missingHdf5:
    #         print "WARNING (loadcell):",
    #         print "could not load %s" % (name)
    #         # have to skip this cell
    #     else:
    #         if missingRes:
    #             list_of_files.append([hdf5, ])
    #         elif missingHdf5:
    #             list_of_files.append(resfiles)
    #             res_loading = True
    #             this_mass_needed = True
    #         else:
    #             if not res:
    #                 similar = self.check_file_ids(hdf5, resfiles, return_res=False)
    #             else:
    #                 similar = False
    #             if not similar:
    #                 # print "FILES ARE NOT SIMILAR"
    #                 list_of_files.append(resfiles)
    #                 res_loading = True
    #                 this_mass_needed = True
    #             else:
    #                 list_of_files.append(hdf5)
    #         masses_needed.append(this_mass_needed)
    #
    #         if this_mass_needed:
    #             res_test_numbers.append(test_number)
    #             try:
    #                 res_masses.append(masses[counter])
    #             except:
    #                 if summary_on_res:
    #                     print "WARNING (loadcell): ",
    #                     print "mass missing for cell %s" % (name)
    #                 res_masses.append(None)
    #         test_number += 1


if __name__ == '__main__':
    print "searching for files"
    my_run_name = "20160805_test001_45_cc"
    my_raw_file_dir = os.path.abspath("../testdata")
    my_cellpy_file_dir = os.path.abspath("../testdata")
    search_for_files(my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir)
