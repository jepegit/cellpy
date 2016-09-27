# -*- coding: utf-8 -*-
"""
Created on Thu Sep 04 15:06:11 2014

@author: jepe
"""

import sys, os, glob, time
from cellpy import prmreader, dbreader
# find all res-files changed last x hours
prms = prmreader.read()
reader = dbreader.reader()
resdatadir = prms.resdatadir


hrs = 100
start_from = 1

dt = 60.0*60*hrs
t = time.time()
srnos = reader.get_all()

c_dir = os.getcwd()
os.chdir(resdatadir)
iterator = start_from
out_txt = ""
screen_txt = ""


def check_dt(f,dt,t):
    dt_actual = None
    statbuf = os.stat(f)
    since_last_mod = t-statbuf.st_mtime

    
    if since_last_mod < dt:
        return since_last_mod
    else:
        return None
        
print "starting...."
print "files changed during the last %i hours:" % int(hrs)

for srno in srnos:
    if srno>=start_from:
        txt =""
        print srno,
        file_exists = reader.inspect_exists(srno)       
        file_id = reader.get_fileid(srno, full_path = False)
        files_log = reader.get_filenames(srno, full_path = False, use_hdf5=False,
                                         non_sensitive = True)
        grep = "*"+file_id+"*.res"
        files_dd=glob.glob(grep)
        
        for f in files_dd:
            since_last_mod = check_dt(f,dt,t)
            if since_last_mod:
                txt = "%i\t%s" % (srno,file_id)
                since_last_mod_hrs = since_last_mod/60.0/60.0

                hours = "%3.2f" % (since_last_mod_hrs)
                txt = "f: " + f + " dt: " + hours
        print txt
        iterator+=1

os.chdir(c_dir)
print "...finnished!"










