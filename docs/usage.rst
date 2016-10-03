=====
Usage
=====

To use cellpy in a project::
.. highlight:: python

    import sys,os,csv,itertools
    from cellpy import arbinreader

    FileName  = r"C:\Scripting\MyFiles\dev_arbindata\abdel\20141030_LBCM5_6_cc_01.res"
    Mass      = 0.982
    OutFolder = r"C:\Scripting\MyFiles\dev_arbindata\abdel\processed"

    try:
        os.chdir(OutFolder)
        print "Output will be sent to folder:"
        print OutFolder
    except:
        print "OutFolder does not exits"
        sys.exit(-1)

    # Loading arbin-data
    d = arbinreader.arbindata(FileName)
    d.loadres()
    d.set_mass(Mass)
    d.make_summary()
    d.create_step_table()
    print "\nexporting raw-data and summary"
    d.exportcsv(OutFolder)

    # Extracting cycles
    list_of_cycles = d.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print "you have %i cycles" % (number_of_cycles)

    FileName0 = os.path.basename(FileName)
    outfile = "%s_cycles.csv" % (FileName0)
    out_data = []

    for cycle in list_of_cycles:
        try:
            c,v = d.get_cap(cycle)
            c = c.tolist()
            v = v.tolist()
            header_x = "cap cycle_no %i" % cycle
            header_y = "voltage cycle_no %i" % cycle
            c.insert(0,header_x)
            v.insert(0,header_y)
            out_data.append(c)
            out_data.append(v)
        except:
            print "could not extract cycle %i" % (cycle)


    # Saving cycles in one .csv file (x,y,x,y,x,y...)
    delimiter = ";"
    print "saving the file with delimiter '%s' " % (delimiter)
    with open(outfile, "wb") as f:
        writer=csv.writer(f,delimiter=delimiter)
        writer.writerows(itertools.izip_longest(*out_data))
        # star (or asterix) means transpose (writing cols instead of rows)

    print "saved the file",
    print outfile
    print "bye!"
    import cellpy
        def extract_ocvrlx():
        import itertools
        import csv
        import matplotlib.pyplot as plt

        filename = r"I:\Org\ensys\EnergyStorageMaterials\Data-backup\Arbin\20160805_sic006_45_cc_01.res"
        mass = 0.853
        type_of_data = "ocvrlx_up"
        fileout = r"C:\Scripting\MyFiles\dev_cellpy\outdata\20160805_sic006_45_cc_01_"+type_of_data
        d_res = setup_cellpy_instance()
        d_res.loadres(filename)
        d_res.set_mass(mass)
        d_res.create_step_table()
        d_res.print_step_table()
        out_data = []
        for cycle in d_res.get_cycle_numbers():
            try:
                if type_of_data == 'ocvrlx_up':
                    print "getting ocvrlx up data for cycle %i" % (cycle)
                    t, v = d_res.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
                else:
                    print "getting ocvrlx down data for cycle %i" % (cycle)
                    t, v = d_res.get_ocv(ocv_type='ocvrlx_down', cycle_number=cycle)
                plt.plot(t,v)
                t = t.tolist()
                v = v.tolist()

                header_x = "time (s) cycle_no %i" % cycle
                header_y = "voltage (V) cycle_no %i" % cycle
                t.insert(0,header_x)
                v.insert(0,header_y)
                out_data.append(t)
                out_data.append(v)

            except:
                print "could not extract cycle %i" % (cycle)


        # Saving cycles in one .csv file (x,y,x,y,x,y...)
        endstring = ".csv"
        outfile = fileout+endstring

        delimiter = ";"
        print "saving the file with delimiter '%s' " % (delimiter)
        with open(outfile, "wb") as f:
            writer=csv.writer(f,delimiter=delimiter)
            writer.writerows(itertools.izip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)

        print "saved the file",
        print outfile
        plt.show()
        print "bye!"
