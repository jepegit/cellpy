# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 18:53:16 2014

@author: jepe
"""

import time
import os, sys

from cellpy import arbinreader, dbreader, prmreader

#import itertools
#import matplotlib.pyplot as plt
#import csv
#import numpy as np

Verbose = False
StartFrom = 264
Debuging = True


# This script needs updating
# use loadcell(f, res=only_res_dont_load_hdf5)


print "-------------------------------------------------------------------------------"
print "running make_hdf5"
print "this might take some time..."
print "-------------------------------------------------------------------------------"
t0 = time.time()
print "opening database"
reader = dbreader.reader()
prms = prmreader.read()
datadir_processed = prms.hdf5datadir
datadir = prms.resdatadir
srnos = reader.get_all()
print "dt: %f" % (time.time()-t0)

Errors = []
print "-------------------------------------------------------------------------------"
skipall=True
counter = 0
srnos = [i for i in srnos if i>= StartFrom]
number_of_srnos = len(srnos)
files_to_process = []
files_changed_but_fixed = []
missing_res_files = []

starttime = time.time()
maxtime = 3600.0
for srno in srnos:
    counter+=1
    print "\n--------------------------------------------------------------------------------------"
    ptxt = "\nprocessing srno %i [%i of %i]:" % (srno, counter, number_of_srnos)
    finnished = reader.inspect_finished(srno) # checks F column in db
    #print " checking log..."
    if finnished:
        ptxt += "\n   marked as 'finnished' in log"
    hdf5_fixed = reader.inspect_hd5f_fixed(srno) # checks M column in db
    if hdf5_fixed:
        ptxt += "\n   marked as 'hdf5_fixed' in log"
    print ptxt

    print " checking files"
    
    hdf5file = reader.get_cell_name(srno) #+".h5" #hdf5 name
    mass = reader.get_mass(srno)
    print "    cell name:", hdf5file
    print "    mass:",
    print mass
    

    d = arbinreader.arbindata(verbose=Verbose)
    d.set_hdf5_datadir(datadir_processed)
    d.set_res_datadir(datadir)
    similar,resfiles = d.check_file_ids(hdf5file, usedir=True, no_extension=True, return_res=True)
    if not resfiles:
        missing_res_files.append(srno)
    print " similar?:"
    print similar
    if similar:
        print "Do not need to make hdf5"
    else:
        if hdf5_fixed:
            files_changed_but_fixed.append(srno)
            print "\nFile is changed but fixed in the log!"
        else:
            files_to_process.append(srno)
            print "\nFile should be processed"
            t1 = time.time()
            print "dt: %f" % (time.time()-t1)
            try:
                print "Processing file..."
                d = arbinreader.arbindata([resfiles]) # will merge automatically
                d.loadres()
                d.set_mass(mass)
                print "mass set"
                d.create_step_table()
                print "created steptable"
                d.make_summary(find_ocv = True,
                               find_ir = True,
                               find_end_voltage = True)
                print "dt: %f" % (time.time()-t1)
                print "(loadres and summary made)"
                d.save_test(os.path.join(datadir_processed,hdf5file))
                print "dt: %f" % (time.time()-t1)
            except:
                print "ERROR - no hdf5-file made"
                e = sys.exc_info()[0]
                print e
                error_txt = "srno %i - NO HDF5 FILE!!!!" % srno
                if Debuging:
                    raise
                Errors.append(error_txt)
            if time.time()-starttime > maxtime:
                print "\n\nMax time reached"
                break


print "finnished all!"
print "dt: %f" % (time.time()-t0)
print "-------------------------------------------------------------------------------"
if Errors:
    print "Errors:"
    for error in Errors:
        print error
if missing_res_files:
    print "Missing res files:"
    for f in missing_res_files:
        print f
print "-------------------------------------------------------------------------------"        
print "bye!"
print "-------------------------------------------------------------------------------"

