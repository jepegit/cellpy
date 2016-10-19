def main():
    import os, shutil
    default_prms = """
    [Paths]
    outdatadir: ..\outdata
    rawdatadir: ..\indata
    cellpydatadir: ..\indata
    db_path: ..\databases
    filelogdir: ..\databases

    [FileNames]
    db_filename: cellpy_db.xlsx
    dbc_filename: cellpy_dbc.xlsx
    """

    default_filename = "_cellpy_prms_default.ini"
    here = os.path.abspath(os.path.dirname(__file__))
    prm_default_path = os.path.join(here, "parametres")
    src = os.path.join(prm_default_path, default_filename)
    userdir = os.path.expanduser("~")
    dst = userdir  # might include .cellpy directory here in the future (must then modify prmreader)

    if not os.path.isfile(src):
        print "Could not find (and copy) default prm-file"
        print "You should make your own prm-file"
        print "with a name starting with _cellpy_prms_xxx.ini,"
        print "where xxx could be any name."
        print "The prm-file should be saved either in your user directory,"
        print "or in the folder where you will run the cellpy scripts from."
        print "Content of prm-file:"
        print
        print default_prms
        print

    else:
        print "Copying %s to user directory" % (default_filename)
        print "(%s)" % userdir
        print
        if os.path.isfile(os.path.join(dst,default_filename)):
            print "File already exists!"
            print "Overwriting..."
        shutil.copy(src, dst)
        print "OK! Now you can edit it and save it with another name starting with"
        print "_cellpy_prms and ending with .ins"


if __name__=="__main__":
    main()
