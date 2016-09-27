# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 12:57:02 2014
@author: Jan Petter Maehlen
@affilation: IFE, Kjeller, Norway
Edit the _cellpy_prms_default.ins file in the parametres folder
or create your own file _cellpy_prms_xxx.ins
"""

default_prms = """
[Paths]
outdatadir: ..\outdata
resdatadir: ..\indata
hdf5datadir: ..\indata
db_path: ..\databases
filelogdir: ..\databases

[FileNames]
db_filename: cellpy_db.xlsx
dbc_filename: cellpy_dbc.xlsx
"""



import glob, os
import ConfigParser

class read:
    def __init__(self,prm_filename=None):
        self.scriptdir = os.path.abspath(os.path.dirname(__file__))
        self.prm_default = os.path.join(self.scriptdir,"_cellpy_prms_default.ini")
        self.outdatadir = "..\outdata"
        self.resdatadir = "..\indata"
        self.hdf5datadir = "..\indata"
        self.db_path= "..\databases"
        self.filelogdir = "..\databases"
        self.db_filename = "cellpy_db.xlsx"
        self.dbc_filename = "cellpy_db.xlsx"
        if prm_filename:
            self._readprms(prm_filename)
        else:
            prm_globtxt = "_cellpy_prms*.ini"
            prm_globtxt = os.path.join(self.scriptdir, prm_globtxt)
            prm_filenames = glob.glob(prm_globtxt)

            for f in prm_filenames:
                if f != self.prm_default:
                    self.prm_default = f
                    break

            if not os.path.isfile(self.prm_default):
                print "could not find ini-file"
                no_file = True
            else:
                no_file = False
            self._readprms(no_file=no_file)
            
    def __get(self,parser, opt, name, too):
        try:
            too = parser.get(opt,name)

        except ConfigParser.NoOptionError as e:
            print "error",
            print e
            
            
    def _readprms(self,no_file=False):
        parser = ConfigParser.SafeConfigParser()
        if no_file:
            import StringIO
            parser.readfp(StringIO.StringIO(default_prms))
        else:
            #print self.prm_default
            parser.read(self.prm_default)

        opt = "Paths"
        try:
            self.outdatadir = parser.get(opt,"outdatadir")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e
        try:
            self.resdatadir = parser.get(opt,"resdatadir")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e
        try:
            self.hdf5datadir = parser.get(opt,"hdf5datadir")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e
        try:
            self.db_path = parser.get(opt,"db_path")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e
        try:
            self.filelogdir = parser.get(opt,"filelogdir")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e

        opt = "FileNames"
        try:
            self.db_filename = parser.get(opt,"db_filename")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e
        try:
             self.dbc_filename = parser.get(opt,"dbc_filename")
        except ConfigParser.NoOptionError as e:
            print "prmreader.py:",
            print e

    
    def _writeprms(self):
        print "prmreader.py: _writeprms is not implemented yet"
        
        
    def __str__(self):
        txt = ""
        txt += "prm-file:    \t%s\n" % self.prm_default
        txt += "------------------------------------------------------------\n"
        txt += "NAME          \tVALUE\n"
        txt += "outdatadir:  \t%s\n" % self.outdatadir
        txt += "resdatadir:  \t%s\n" % self.resdatadir
        txt += "hdf5datadir: \t%s\n" % self.hdf5datadir
        txt += "db_path:     \t%s\n" % self.db_path
        txt += "filelogdir:  \t%s\n" % self.filelogdir
        
        txt += "db_filename: \t%s\n" % self.db_filename
        txt += "dbc_filename:\t%s\n" % self.dbc_filename
        
        return txt
        
        
        
        
if __name__=="__main__":
    r = read()
    
    print "\n----------------------Read file-----------------------------"
    print "Prms:"
    print "------------------------------------------------------------"
    print r
    print "------------------------------------------------------------"
    
    errors = False
    if not os.path.isdir(r.db_path):
        print "Error! db_path not found"
        errors = True
    if not os.path.isdir(r.outdatadir):
        print "Error! outdatadir not found"
        errors = True
    if not os.path.isdir(r.resdatadir):
        print "Error! resdatadir not found"
        errors = True
    if not os.path.isdir(r.hdf5datadir):
        print "Error! hdf5datadir not found"
        errors = True
    if not os.path.isdir(r.filelogdir):
        print "Error! filelogdir not found"
        errors = True
        
    if not os.path.isfile(os.path.join(r.db_path,r.db_filename)):
        print "Error! db_filename not found"
        errors = True
    if not os.path.isfile(os.path.join(r.db_path,r.dbc_filename)):
        print "Error! dbc_filename not found"
        errors = True
        
    if errors == False:
        print "All ok"
