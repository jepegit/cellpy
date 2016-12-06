# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 10:18:59 2014
@author: Jan Petter Maehlen, IFE, Kjeller, Norway
"""


import sys
#from cellpy import cellreader, dbreader, prmreader
#import itertools
#import matplotlib.pyplot as plt
#import csv
from scipy.interpolate import interp1d
from scipy.integrate import simps
from scipy.optimize import curve_fit
#import numpy as np
from numpy import ediff1d, amax, amin, linspace, zeros, polyfit, array, pi, abs, take, less
from numpy import arange, average
# ediff1d, amax, amin, linspace


def dQdV(v,q,NumberMultiplyer=1,
         Method="linear",
         FinalInterpolation=True,
         Norm2Cap=True,
         Norm2CapConstant = None,
         Type = None,
         resolution = None,
         verbose = False):
    # finding dQ/dV
    number_of_points = len(v)
#    print "number_of_points:"
#    print number_of_points

    Number_of_points=number_of_points*NumberMultiplyer

    if Norm2Cap:
        if Norm2CapConstant is not None:
            NormQ = Norm2CapConstant
        else:
            try:
                # ------- checking the data and selecting normalization constant -----
                if Type in ["positive", "charge"]:
                    NormQ = amax(q)
                if Type in ["negative", "discharge"]:
                    NormQ = -amax(q)
                else:
                    # Need to find out if it is positive or negative dqdv


                    LastV = take(v, [-1,])
                    FirstV = take(v, [0,])
                    # print LastV
                    # print FirstV

                    if less(LastV, FirstV).all(): # discharge
                        NormQ = -amax(q)
                    else:              # charge
                        NormQ = amax(q)

                    if verbose:
                        MaxQ    = amax(q)
                        MinQ = amin(abs(q))
                        LastQ = take(q,[-1,])
                        FirstQ = take(q,[0,])

                        txt = "-------------------------------------------\n"
                        txt+= "Number of points: %i\n" % (number_of_points)
                        txt+= " * %i =\n" % (NumberMultiplyer)
                        txt+= "Number of points: %i\n" % (Number_of_points)
                        txt+= "Max:              %f\n" % (MaxQ)
                        txt+= "Min (abs):        %f\n" % (MinQ)
                        txt+= "First:            %f\n" % (FirstQ)
                        txt+= "Last:             %f\n" % (LastQ)
                        txt+= "Max (abs):        %i\n" % (MaxQ)
                        txt+= "-------------------------------------------"
                        print txt
            except:
                print "Warning! Could not find normalization constant (data will not be normalized)!"
                Norm2Cap = False

    if Method=="raw":
        v_start = voltage.iget(0)
        v_end   = voltage.iget(-1)
        length_v = v_end-v_start
        s = length_voltage/(number_of_points-1)
        dv = ediff1d(v)
        dQ = ediff1d(q)/dv
        v=v[1:]
    else:
        v,q,s=interpolate_line(v,q,Number_of_points,Method=Method, print_it=verbose, resolution = resolution)
        dQ=ediff1d(q)/s
        v=v[1:]
        if FinalInterpolation:
            FinalInterpolation_denom = 2.0
            if Number_of_points is not None:
                NP = Number_of_points/FinalInterpolation_denom
            else:
                NP = None
            if resolution is not None:
                RS = resolution/FinalInterpolation_denom
            else:
                RS = None
            v,dQ,s=interpolate_line(v,dQ,NP,Method=Method, print_it=verbose,
                                    resolution = RS)
        if Norm2Cap:
            AdQ = _integrate(dQ,v)
            dQ = dQ* NormQ /AdQ
            if verbose:
                print "Change in area: %f" % (NormQ-AdQ)
                print "(change in percentage: %f %%" % (100*(NormQ-AdQ)/NormQ)
    return v,dQ

def _integrate(dQ,v):
    result = simps(dQ,v)
    return result

def interpolate_line(x,y,number_of_points=None,
                Method = None,
                print_it = False,
                reverse = False,
                resolution = None):
    r"""interpolation"""

    if not Method:
        Method="linear"

    x_max = amax(x)
    x_min = amin(x)

    try:
        x_start = x[0]
        x_end = x[-1]
    except:  # numpy array
        # depreciation warning TODO: shift to .iloc[0]
        x_start = x.iloc[0]
        x_end = x.iloc[-1]
    if x_start > x_end:
        # need to reverse
        reverse = True
    if not number_of_points:
        number_of_points = len(x)


    ErrorInPoints=False
    if reverse:
        if x_min>x_start:
            ErrorInPoints=True
        if x_max<x_end:
            ErrorInPoints=True
    else:
        if x_min<x_start:
            ErrorInPoints=True
        if x_max>x_end:
            ErrorInPoints=True

    if not ErrorInPoints:
        if resolution is not None:
            x_interpolated=arange(x_min,x_max,resolution)
        else:
            x_interpolated=linspace(x_min,x_max,number_of_points)
    else:
        if resolution is not None:
            x_interpolated=arange(x_start,x_end,resolution)
        else:
            x_interpolated=linspace(x_start,x_end,number_of_points)

    x_step = (x_interpolated[-1]-x_interpolated[0])/(number_of_points-1)

    if reverse:
        x = (-1)*x
        x_interpolated = (-1)*x_interpolated
    f=interp1d(x,y,kind=Method)

    if print_it:
        print "----interpolate-function-----"
        if reverse:
            print "reversed"
        print "x first and last of raw-data:"
        print x_start, x_end
        print "x min and max of raw-data:"
        print x_min, x_max
        print "x max and min of new-data:"
        print x_interpolated[0], x_interpolated[-1]
        if ErrorInPoints:
            print "-error-in-points"
            if reverse:
                if x_min>x_start:
                    print "x min > x start"
                if x_max<x_end:
                    print "x max < x end"
            else:
                if x_min<x_start:
                    print "x min < x start"
                if x_max>x_end:
                    print "x max > x end"

    y_interpolated=f(x_interpolated)
    if reverse:
        x_interpolated = (-1)*x_interpolated

    if print_it:
        print "ok"
        print
    return x_interpolated, y_interpolated, x_step



def get_vdq(cycle,
            points_multiplyer = 1.1,
            intp_method = "slinear",
            ):
    from cellpy import cellreader
    voltage = cellreader.get_voltage(cycle)
    capacity = arbinreader.get_discharge_capacity(cycle)
    v,dQ = dQdV(voltage,capacity,points_multiplyer,Method=intp_method)
    return v,dQ



def is_something(x):
    something_iterable = True
    something_else = True
    if not hasattr(x, "__len__"):
        something_iterable = False
        if not x:
            something_else = False
    return something_else

# Specialized functions

def xalt():
    dqdv_numbermultiplyer = 0.5
    dqdv_method = 'slinear'
    dqdv_finalinterpolation = True
    dqdv_resolution = 0.001 # V

    import csv, os
    import numpy as np
    import matplotlib.pyplot as plt
    inDir  = r"I:\Org\ensys\EnergyStorageMaterials\Data\Xalt_dQ_dV\dQdV_raw_data"
    outDir = r"I:\Org\ensys\EnergyStorageMaterials\Data\Xalt_dQ_dV\dQdV_processed_data"
    if not os.path.isdir(outDir):
        os.mkdir(outDir)
        print "made directory"
    curDir = os.getcwd()
    Filenames = os.listdir(inDir)
    Filenames.sort()
    for filename in Filenames:
        rname = os.path.basename(filename).split(".")[0]
        oname = rname+"_processed.csv"
        outfile = os.path.join(outDir,oname)
        with open(os.path.join(inDir,filename)) as f:
            firstline = True
            reader = csv.reader(f,delimiter = ",")
            for row in reader:
                if firstline:
                    firstline = False
                    c = []
                    v = []
                else:
                    c.append(float(row[0]))
                    v.append(float(row[1]))
        plt.subplot(2,1,1)
        plt.plot(c,v)
        #plt.show()
        v = np.array(v)
        c = np.array(c)
        dv,dQ = dQdV(v,c,
                NumberMultiplyer=dqdv_numbermultiplyer,
                Method=dqdv_method,
                FinalInterpolation = dqdv_finalinterpolation,
                Norm2Cap = True,
                #resolution = None,
                verbose =True)
        plt.subplot(2,1,2)
        plt.plot(dv,dQ)
        with open(outfile,'w') as of:
            writer = csv.writer(of)
            writer.writerow(("dv","dQ"))
            for x,y in zip(dv,dQ):
                writer.writerow((x,y))
    plt.show()




#    Filename = "Cell_ID_SM1035071302412017_Test_5553_Cycles_2_Steps_25.csv"
#    with open(os.path.join(Dir,Filename),'r') as infile:
#        lines = infile.readlines()
#        print lines


def test():
    from cellpy import cellreader
    cathode_file = r"I:\Org\ensys\EnergyStorageMaterials\Data-backup\Arbin\20141030_HP_1_cc_01.res"
    cathode_mass = 13.8610

    dqdv_numbermultiplyer = 0.4
    dqdv_method = 'slinear'
    dqdv_finalinterpolation = True
    dqdv_resolution = 0.001 # V

#    dqdv_method: Specifies the kind of interpolation as a string (‘linear’, ‘nearest’, ‘zero’, ‘slinear’, ‘quadratic, ‘cubic’ where ‘slinear’, ‘quadratic’ and ‘cubic’ refer to a spline interpolation of first, second or third order)
#    or as an integer specifying the order of the spline interpolator to use. Default is ‘linear’.

    d = cellreader.cellpydata()
    d.loadres(cathode_file)
    d.set_mass(cathode_mass)
    list_of_cycles = d.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print "you have %i cycles" % (number_of_cycles)
    print "looking at cycle 1"
    cycle = 1

    c1,v1 = d.get_ccap(cycle)

    dv1,dQ1 = dQdV(v1,c1,
                NumberMultiplyer=dqdv_numbermultiplyer,
                Method=dqdv_method,
                FinalInterpolation = dqdv_finalinterpolation,
                Norm2Cap = True,
                resolution = None,
                verbose =True)

    dv2,dQ2 = dQdV(v1,c1,
                NumberMultiplyer=dqdv_numbermultiplyer,
                Method=dqdv_method,
                FinalInterpolation = dqdv_finalinterpolation,
                resolution = None,
                Norm2Cap = False,
                verbose =True)

    dv3,dQ3 = dQdV(v1,c1,
                NumberMultiplyer=dqdv_numbermultiplyer,
                Method=dqdv_method,
                FinalInterpolation = dqdv_finalinterpolation,
                resolution = dqdv_resolution,
                Norm2Cap = True,
                verbose =True)

    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(c1,v1)

    plt.figure()
    plt.plot(dv1,dQ1, label = "normalized to cap")
    plt.plot(dv2,dQ2, label = "not normalized")
    plt.plot(dv3,dQ3, label = "normalized to cap - with res. %f V" % (dqdv_resolution))
    plt.legend()
    plt.show()

if __name__=="__main__":
    #test()
    xalt()
