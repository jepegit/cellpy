# Different data formats

This notebook shows some examples for loading file formats from different battery testers as well as some "tweaking" possibilites provided by `cellpy`. We hope that, as time goes, a more complete set of instruments will be fully supported. Loading non-supported ("custom") file formats is explained in more detail [here](./07_custom_loaders.ipynb).


```python
from rich import print

import cellpy
from cellpy.utils import example_data, plotutils
```

## Overview

To get an overview on all the implemented instruments/loaders:


```python
from cellpy.readers import core

print(core.find_all_instruments().keys())
```


    [1;35mdict_keys[0m[1m([0m[1m[[0m[32m'arbin_res'[0m, [32m'arbin_sql'[0m, [32m'arbin_sql_7'[0m, [32m'arbin_sql_csv'[0m, [32m'arbin_sql_h5'[0m, [32m'arbin_sql_xlsx'[0m, 
    [32m'biologics_mpr'[0m, [32m'custom'[0m, [32m'ext_nda_reader'[0m, [32m'local_instrument'[0m, [32m'maccor_txt'[0m, [32m'neware_txt'[0m, [32m'neware_xlsx'[0m, 
    [32m'pec_csv'[0m[1m][0m[1m)[0m
    


Some instruments have different types of `models` - for more details on those, have a look at the section on reading of *Maccor* data below.

Defining a simple utility-function to get a peek of the file in question:


```python
def head(f, n=5):
    print(f" {f.name} ".center(80, "-"))
    with open(f) as datafile:
        for j in range(n):
            line = datafile.readline()
            print(f"[{j + 1:02}] {line.strip()}")
```

## PEC CSV data

PEC testers do not seem to allow direct access to the raw data (database). However, data can be exported to csv-files from the graphical user interface. There might exist other solutions as well (let us know). 

`cellpy` contains a limited set of example data sets, among others, a csv-file exported from a run performed at a PEC tester. The example data can be downloaded to your PC using the `utils.example_data` module:


```python
p = example_data.pec_file_path()
print(f"{p.name=}")
```


    p.[33mname[0m=[32m'pec.csv'[0m
    


Below we take a look at the first 35 lines of the example PEC csv-files.

If the file you want to load is not similar to this, either a custom loader must be made, or you can create an issue on GitHub (and maybe help in implementing the necessery modifications?). 


```python
head(p, 35)
```


    ----------------------------------- pec.csv ------------------------------------
    



    [1m[[0m[1;36m01[0m[1m][0m Request Year:,[1;36m2019[0m
    



    [1m[[0m[1;36m02[0m[1m][0m Test:,[1;36m187[0m
    



    [1m[[0m[1;36m03[0m[1m][0m Test Description:,
    



    [1m[[0m[1;36m04[0m[1m][0m TestRegime Name:,FirstCell dQdV C/[1;36m25[0m
    



    [1m[[0m[1;36m05[0m[1m][0m TestRegime Suffix:,HWL
    



    [1m[[0m[1;36m06[0m[1m][0m TestRegime CellSize:,Default cellsize
    



    [1m[[0m[1;36m07[0m[1m][0m TestRegime Version:,[1;36m1[0m
    



    [1m[[0m[1;36m08[0m[1m][0m Project Group Name:,Immediate
    



    [1m[[0m[1;36m09[0m[1m][0m Project Group Description:,Immediate
    



    [1m[[0m[1;36m10[0m[1m][0m Project Group Memo:,
    



    [1m[[0m[1;36m11[0m[1m][0m Project Group Storage Environment:,R.T.[35m/[0m[95mAMB[0m
    



    [1m[[0m[1;36m12[0m[1m][0m Project Group Test Environment:,R.T.[35m/[0m[95mAMB[0m
    



    [1m[[0m[1;36m13[0m[1m][0m Number Of Cells:,[1;36m1[0m
    



    [1m[[0m[1;36m14[0m[1m][0m Parameter names:,
    



    [1m[[0m[1;36m15[0m[1m][0m Parameter values:,
    



    [1m[[0m[1;36m16[0m[1m][0m Variable names:
    



    [1m[[0m[1;36m17[0m[1m][0m LotID:,
    



    [1m[[0m[1;36m18[0m[1m][0m Lot Description:,
    



    [1m[[0m[1;36m19[0m[1m][0m Date Made:,[1;36m1[0m/[1;36m21[0m/[1;36m2003[0m [1;92m0:00[0m
    



    [1m[[0m[1;36m20[0m[1m][0m Origin:,Other
    



    [1m[[0m[1;36m21[0m[1m][0m Requestor:,Admin
    



    [1m[[0m[1;36m22[0m[1m][0m Product ID:,Default product
    



    [1m[[0m[1;36m23[0m[1m][0m Storage Temp:,R.T.[35m/[0m[95mAMB[0m
    



    [1m[[0m[1;36m24[0m[1m][0m Storage Delay:,[1;36m0[0m days
    



    [1m[[0m[1;36m25[0m[1m][0m Test Temp:,R.T.[35m/[0m[95mAMB[0m
    



    [1m[[0m[1;36m26[0m[1m][0m Start Time:,[1;36m02[0m/[1;36m22[0m/[1;36m2019[0m [1;92m16:21:35[0m
    



    [1m[[0m[1;36m27[0m[1m][0m End Time:,[1;36m1[0m/[1;36m1[0m/[1;36m0001[0m [1;92m0:00[0m
    



    [1m[[0m[1;36m28[0m[1m][0m Operator Instructions:,Also connect cell temp to channel TC-K and ambient temp to NTC
    



    [1m[[0m[1;36m29[0m[1m][0m #RESULTS CHECK
    



    [1m[[0m[1;36m30[0m[1m][0m ReqYear,Test,CellNr,Type,Value,Reason,
    



    [1m[[0m[1;36m31[0m[1m][0m [1;36m2019[0m,[1;36m187[0m,[1;36m1[0m,[1;36m1[0m,[1;36m3272[0m,[1;36m3[0m,
    



    [1m[[0m[1;36m32[0m[1m][0m #END RESULTS CHECK
    



    [1m[[0m[1;36m33[0m[1m][0m Test,Cell,Rack,Shelf,Position,Cell ID,Step,Cycle,Total Time [1m([0mSeconds[1m)[0m,Load On Time [1m([0mSeconds[1m)[0m,Step Time 
    [1m([0mSeconds[1m)[0m,Cycle Charge Time [1m([0mSeconds[1m)[0m,Cycle Discharge Time [1m([0mSeconds[1m)[0m,Real Time,Position Start Time,Voltage 
    [1m([0mmV[1m)[0m,Current [1m([0mmA[1m)[0m,Charge Capacity [1m([0mmAh[1m)[0m,Discharge Capacity [1m([0mmAh[1m)[0m,Charge Capacity [1m([0mmWh[1m)[0m,Discharge Capacity 
    [1m([0mmWh[1m)[0m,ReasonCode,[1;36m50[0m% DoD [1m([0mmV[1m)[0m,PeakPower [1;36m1[0m [1m([0mW[1m)[0m,PeakPower [1;36m2[0m [1m([0mW[1m)[0m,Open Circuit Voltage [1;36m1[0m [1m([0mV[1m)[0m,Open Circuit Voltage [1;36m2[0m 
    [1m([0mV[1m)[0m,Internal Resistance [1;36m1[0m [1m([0mmOhm[1m)[0m,Internal Resistance [1;36m2[0m [1m([0mmOhm[1m)[0m,Ambient temperature [1m([0mÂ°C[1m)[0m,Cell surface temperature 
    [1m([0mÂ°C[1m)[0m,DC Internal Resistance [1m([0mmOhm[1m)[0m,AC Internal Resistance [1m([0mmOhm[1m)[0m,Station Temperature [1m([0mÂ°C[1m)[0m,
    



    [1m[[0m[1;36m34[0m[1m][0m [1;36m187[0m,[1;36m1[0m,SBT0550,[1;36m001[0m,[1;36m1[0m,,[1;36m0[0m,[1;36m0[0m,[1;36m1[0m,[1;36m0[0m,[1;36m1[0m,[1;36m0[0m,[1;36m0[0m,[1;36m02[0m/[1;36m22[0m/[1;36m2019[0m [1;92m16:23:27[0m,[1;36m02[0m/[1;36m22[0m/[1;36m2019[0m 
    [1;92m16:23:26[0m,[1;36m3272.632[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m30[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m25.83[0m,[1;36m24.9[0m,,,,
    



    [1m[[0m[1;36m35[0m[1m][0m [1;36m187[0m,[1;36m1[0m,SBT0550,[1;36m001[0m,[1;36m1[0m,,[1;36m0[0m,[1;36m0[0m,[1;36m5[0m,[1;36m0[0m,[1;36m5[0m,[1;36m0[0m,[1;36m0[0m,[1;36m02[0m/[1;36m22[0m/[1;36m2019[0m [1;92m16:23:31[0m,[1;36m02[0m/[1;36m22[0m/[1;36m2019[0m 
    [1;92m16:23:26[0m,[1;36m3272.2776[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m30[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m0[0m,[1;36m25.83[0m,[1;36m24.9[0m,,,,
    


### Loading the file

You can load the file using the `.get` method as usual. However, you will have to provide `cellpy` the name of the instrument (for this case it will be "pec_csv").


```python
c = cellpy.get(p, instrument="pec_csv", cycle_mode="full_cell")
plotutils.raw_plot(c, width=1200, height=400)
```





Once you have loaded the files, you can use all the common functionalities of `cellpy` (as described in other example notebooks), such as, e.g., looking at a summary plot:


```python
plotutils.summary_plot(c, y="capacities", width=1200, height=400)
```



## MACCOR

The implemented loader for exported data from Maccor is able to load several "file-morphologies" (so-called `models`). This illustrates one of the main weaknesses of not having direct access to the raw-data: the operator/user typically has the possibility select (consciously or not) how the final exported data file will look. This can be, for example, what to name the columns, what to use as delimiter, or what symbol to use as thousand seperator.

### Different models

You can get information about the different models for the loaders by looking at the instrument configurations. Here is an example of how to do it "programmatically":

1. Check which loaders are available for Maccor files:


```python
config = core.instrument_configurations("maccor")
print(config.keys())
```


    [1;35mdict_keys[0m[1m([0m[1m[[0m[32m'maccor_txt'[0m[1m][0m[1m)[0m
    


2. Check which *models* are available for Maccor:


```python
print(config["maccor_txt"]["__all__"])
```


    [1m[[0m[32m'default'[0m, [32m'ZERO'[0m, [32m'ONE'[0m, [32m'TWO'[0m, [32m'THREE'[0m, [32m'S4000-UBHAM'[0m, [32m'S4000-KIT'[0m, [32m'S4000-WMG'[0m[1m][0m
    


3. Have a closer look at a selected model configuration, here for model `THREE`:


```python
print(config["maccor_txt"]["THREE"])
```


    [1m{[0m
        [32m'config_params'[0m: [1;35mModelParameters[0m[1m([0m
            [33mname[0m=[32m'THREE'[0m,
            [33mfile_info[0m=[1m{[0m[32m'raw_extension'[0m: [32m'txt'[0m[1m}[0m,
            [33munit_labels[0m=[1m{[0m
                [32m'resistance'[0m: [32m'Ohms'[0m,
                [32m'time'[0m: [32m's'[0m,
                [32m'current'[0m: [32m'mA'[0m,
                [32m'voltage'[0m: [32m'mV'[0m,
                [32m'power'[0m: [32m'mW'[0m,
                [32m'capacity'[0m: [32m'mAh'[0m,
                [32m'energy'[0m: [32m'mWh'[0m,
                [32m'temperature'[0m: [32m'C'[0m
            [1m}[0m,
            [33mincremental_unit_labels[0m=[1m{[0m[1m}[0m,
            [33mnormal_headers_renaming_dict[0m=[1m{[0m
                [32m'data_point_txt'[0m: [32m'Rec#'[0m,
                [32m'cycle_index_txt'[0m: [32m'Cyc#'[0m,
                [32m'step_index_txt'[0m: [32m'Step'[0m,
                [32m'test_time_txt'[0m: [32m'TestTime'[0m,
                [32m'step_time_txt'[0m: [32m'StepTime'[0m,
                [32m'charge_capacity_txt'[0m: [32m'mAmp-hr'[0m,
                [32m'charge_energy_txt'[0m: [32m'mWatt-hr'[0m,
                [32m'current_txt'[0m: [32m'mAmps'[0m,
                [32m'voltage_txt'[0m: [32m'Volts'[0m,
                [32m'datetime_txt'[0m: [32m'DPt Time'[0m
            [1m}[0m,
            [33mnot_implemented_in_cellpy_yet_renaming_dict[0m=[1m{[0m[1m}[0m,
            [33mcolumns_to_keep[0m=[1m[[0m[1m][0m,
            [33mstates[0m=[1m{[0m[32m'column_name'[0m: [32m'State'[0m, [32m'charge_keys'[0m: [1m[[0m[32m'C'[0m[1m][0m, [32m'discharge_keys'[0m: [1m[[0m[32m'D'[0m[1m][0m, [32m'rest_keys'[0m: [1m[[0m[32m'R'[0m[1m][0m[1m}[0m,
            [33mraw_units[0m=[1m{[0m[32m'current'[0m: [32m'mA'[0m, [32m'charge'[0m: [32m'mAh'[0m, [32m'mass'[0m: [32m'g'[0m, [32m'voltage'[0m: [32m'mV'[0m[1m}[0m,
            [33mraw_limits[0m=[1m{[0m
                [32m'current_hard'[0m: [1;36m1e-13[0m,
                [32m'current_soft'[0m: [1;36m1e-05[0m,
                [32m'stable_current_hard'[0m: [1;36m2.0[0m,
                [32m'stable_current_soft'[0m: [1;36m4.0[0m,
                [32m'stable_voltage_hard'[0m: [1;36m2.0[0m,
                [32m'stable_voltage_soft'[0m: [1;36m4.0[0m,
                [32m'stable_charge_hard'[0m: [1;36m0.001[0m,
                [32m'stable_charge_soft'[0m: [1;36m5.0[0m,
                [32m'ir_change'[0m: [1;36m1e-05[0m
            [1m}[0m,
            [33mformatters[0m=[1m{[0m
                [32m'skiprows'[0m: [1;36m2[0m,
                [32m'sep'[0m: [32m'\t'[0m,
                [32m'header'[0m: [1;36m0[0m,
                [32m'encoding'[0m: [32m'ISO-8859-1'[0m,
                [32m'decimal'[0m: [32m','[0m,
                [32m'thousands'[0m: [3;35mNone[0m
            [1m}[0m,
            [33mmeta_keys[0m=[1m{[0m[1m}[0m,
            [33mpre_processors[0m=[1m{[0m[32m'remove_empty_lines'[0m: [3;92mTrue[0m[1m}[0m,
            [33mpost_processors[0m=[1m{[0m
                [32m'split_capacity'[0m: [3;92mTrue[0m,
                [32m'split_current'[0m: [3;92mTrue[0m,
                [32m'set_index'[0m: [3;92mTrue[0m,
                [32m'rename_headers'[0m: [3;92mTrue[0m,
                [32m'set_cycle_number_not_zero'[0m: [3;92mTrue[0m,
                [32m'remove_last_if_bad'[0m: [3;92mTrue[0m,
                [32m'convert_date_time_to_datetime'[0m: [3;92mTrue[0m,
                [32m'convert_step_time_to_timedelta'[0m: [3;92mTrue[0m,
                [32m'convert_test_time_to_timedelta'[0m: [3;92mTrue[0m
            [1m}[0m,
            [33mprefixes[0m=[1m{[0m[1m}[0m
        [1m)[0m,
        [32m'doc'[0m: [32m'Class for loading data from Maccor txt files.'[0m
    [1m}[0m
    


Especially the `formatters` give valuable hints if a model is promising for your specific file or not:


```python
print(config["maccor_txt"]["THREE"]["config_params"].formatters)
```


    [1m{[0m[32m'skiprows'[0m: [1;36m2[0m, [32m'sep'[0m: [32m'\t'[0m, [32m'header'[0m: [1;36m0[0m, [32m'encoding'[0m: [32m'ISO-8859-1'[0m, [32m'decimal'[0m: [32m','[0m, [32m'thousands'[0m: [3;35mNone[0m[1m}[0m
    


Note that "config_params" is not a dictionary, but an instance of the ModelParameters class (so dot notation is needed).

### Loading the file
Now we are ready to look into loading an example Maccor file (included within cellpy's `utils.example_data` module):


```python
p = example_data.maccor_file_path()
print(f"{p.name=}")
```


    p.[33mname[0m=[32m'maccor_three.txt'[0m
    



```python
head(p, 10)
```


    ------------------------------- maccor_three.txt -------------------------------
    



    [1m[[0m[1;36m01[0m[1m][0m Today''s Date      [1;36m03[0m/[1;36m28[0m/[1;36m2022[0m [1;92m12:50:27[0m PM
    



    [1m[[0m[1;36m02[0m[1m][0m 
    



    [1m[[0m[1;36m03[0m[1m][0m Date of Test:      [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:04:18[0m PM
    



    [1m[[0m[1;36m04[0m[1m][0m 
    



    [1m[[0m[1;36m05[0m[1m][0m Rec#       Cyc#    Step    TestTime        StepTime        mAmp-hr mWatt-hr        mAmps   Volts   State   ES 
    DPt Time        Unnamed: [1;36m12[0m
    



    [1m[[0m[1;36m06[0m[1m][0m [1;36m1[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:00:00[0m.[1;36m00[0m          0d [1;92m00:00:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.8186[0m       R  
    [1;36m0[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:04:18[0m PM
    



    [1m[[0m[1;36m07[0m[1m][0m [1;36m2[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:01:00[0m.[1;36m00[0m          0d [1;92m00:01:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:05:18[0m PM
    



    [1m[[0m[1;36m08[0m[1m][0m [1;36m3[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:02:00[0m.[1;36m00[0m          0d [1;92m00:02:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:06:18[0m PM
    



    [1m[[0m[1;36m09[0m[1m][0m [1;36m4[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:03:00[0m.[1;36m00[0m          0d [1;92m00:03:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:07:18[0m PM
    



    [1m[[0m[1;36m10[0m[1m][0m [1;36m5[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:04:00[0m.[1;36m00[0m          0d [1;92m00:04:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:08:18[0m PM
    


The file format for this file is handled by the model `THREE` in `cellpy`. Both, information on the instrument ("maccor_txt") and on the *model* ("THREE") has to be included when loading the data using the standard  `cellpy.get` method:


```python
c = cellpy.get(p, instrument="maccor_txt", model="THREE", cycle_mode="full_cell")
```

    (cellpy) - running pre-processor: remove_empty_lines
    (cellpy) - self.sep='\t', self.skiprows=2, self.header=0, self.encoding='ISO-8859-1', self.decimal=','
    (cellpy) - running post-processor: rename_headers
    Index(['Rec#', 'Cyc#', 'Step', 'TestTime', 'StepTime', 'mAmp-hr', 'mWatt-hr',
           'mAmps', 'Volts', 'State', 'ES', 'DPt Time', 'Unnamed: 12'],
          dtype='object')
    (cellpy) - running post-processor: remove_last_if_bad
    (cellpy) - running post-processor: split_capacity
    (cellpy) - running post-processor: split_current
    (cellpy) - running post-processor: set_index
    (cellpy) - running post-processor: set_cycle_number_not_zero
    (cellpy) - running post-processor: convert_date_time_to_datetime
    (cellpy) - running post-processor: convert_step_time_to_timedelta
    (cellpy) - running post-processor: convert_test_time_to_timedelta
    

After loading the file, you are ready to use all common `cellpy` functionalities:


```python
print(f"Available cycles in the file: {c.get_cycle_numbers()}")
plotutils.raw_plot(c, width=1200, height=400)
```


    Available cycles in the file: [1m[[0m [1;36m1[0m  [1;36m2[0m  [1;36m3[0m  [1;36m4[0m  [1;36m5[0m  [1;36m6[0m  [1;36m7[0m  [1;36m8[0m  [1;36m9[0m [1;36m10[0m [1;36m11[0m [1;36m12[0m [1;36m13[0m [1;36m14[0m [1;36m15[0m[1m][0m
    





```python
plotutils.summary_plot(c, y="capacities", width=1200, height=400, y_range=[0, 1000])
```



## NEWARE

Data from Neware testers will be improved soon. Currently, one `model` is implemented ("ONE"). Using the method described above for getting information, currently you will see three model names appear. The "default" is the one that will be picked if no model name is provided ("ONE" for now), while "UIO" is just a nick-name for the "ONE" model.


```python
config = core.instrument_configurations("neware")
print(config["neware_txt"]["__all__"])
```


    [1m[[0m[32m'default'[0m, [32m'ONE'[0m, [32m'UIO'[0m[1m][0m
    


Check the configuration for *model* `ONE`:


```python
print(config["neware_txt"]["ONE"])
```


    [1m{[0m
        [32m'config_params'[0m: [1;35mModelParameters[0m[1m([0m
            [33mname[0m=[32m'ONE'[0m,
            [33mfile_info[0m=[1m{[0m[32m'raw_extension'[0m: [32m'csv'[0m[1m}[0m,
            [33munit_labels[0m=[1m{[0m[1m}[0m,
            [33mincremental_unit_labels[0m=[1m{[0m[1m}[0m,
            [33mnormal_headers_renaming_dict[0m=[1m{[0m
                [32m'data_point_txt'[0m: [32m'DataPoint'[0m,
                [32m'cycle_index_txt'[0m: [32m'Cycle Index'[0m,
                [32m'step_index_txt'[0m: [32m'Step Index'[0m,
                [32m'current_txt'[0m: [32m'Current[0m[32m([0m[32mA[0m[32m)[0m[32m'[0m,
                [32m'voltage_txt'[0m: [32m'Voltage[0m[32m([0m[32mV[0m[32m)[0m[32m'[0m,
                [32m'charge_capacity_txt'[0m: [32m'Chg. Cap.[0m[32m([0m[32mAh[0m[32m)[0m[32m'[0m,
                [32m'charge_energy_txt'[0m: [32m'Chg. Energy[0m[32m([0m[32mWh[0m[32m)[0m[32m'[0m,
                [32m'discharge_capacity_txt'[0m: [32m'DChg. Cap.[0m[32m([0m[32mAh[0m[32m)[0m[32m'[0m,
                [32m'discharge_energy_txt'[0m: [32m'DChg. Energy[0m[32m([0m[32mWh[0m[32m)[0m[32m'[0m,
                [32m'datetime_txt'[0m: [32m'Date'[0m,
                [32m'step_time_txt'[0m: [32m'Time'[0m,
                [32m'dq_dv_txt'[0m: [32m'dQ/dV[0m[32m([0m[32mmAh/V[0m[32m)[0m[32m'[0m,
                [32m'internal_resistance_txt'[0m: [32m'Contact resistance[0m[32m([0m[32mmO[0m[32m)[0m[32m'[0m,
                [32m'power_txt'[0m: [32m'Power[0m[32m([0m[32mW[0m[32m)[0m[32m'[0m,
                [32m'test_time_txt'[0m: [32m'Cumulative Time'[0m
            [1m}[0m,
            [33mnot_implemented_in_cellpy_yet_renaming_dict[0m=[1m{[0m[1m}[0m,
            [33mcolumns_to_keep[0m=[1m[[0m[1m][0m,
            [33mstates[0m=[1m{[0m
                [32m'column_name'[0m: [32m'Step Type'[0m,
                [32m'charge_keys'[0m: [1m[[0m[32m'CC Chg'[0m[1m][0m,
                [32m'discharge_keys'[0m: [1m[[0m[32m'CC DChg'[0m[1m][0m,
                [32m'rest_keys'[0m: [1m[[0m[32m'Rest'[0m[1m][0m
            [1m}[0m,
            [33mraw_units[0m=[1m{[0m
                [32m'current'[0m: [32m'A'[0m,
                [32m'charge'[0m: [32m'Ah'[0m,
                [32m'mass'[0m: [32m'g'[0m,
                [32m'voltage'[0m: [32m'V'[0m,
                [32m'energy'[0m: [32m'Wh'[0m,
                [32m'power'[0m: [32m'W'[0m,
                [32m'resistance'[0m: [32m'Ohm'[0m
            [1m}[0m,
            [33mraw_limits[0m=[1m{[0m
                [32m'current_hard'[0m: [1;36m1e-13[0m,
                [32m'current_soft'[0m: [1;36m1e-05[0m,
                [32m'stable_current_hard'[0m: [1;36m2.0[0m,
                [32m'stable_current_soft'[0m: [1;36m4.0[0m,
                [32m'stable_voltage_hard'[0m: [1;36m2.0[0m,
                [32m'stable_voltage_soft'[0m: [1;36m4.0[0m,
                [32m'stable_charge_hard'[0m: [1;36m0.001[0m,
                [32m'stable_charge_soft'[0m: [1;36m5.0[0m,
                [32m'ir_change'[0m: [1;36m1e-05[0m
            [1m}[0m,
            [33mformatters[0m=[1m{[0m
                [32m'skiprows'[0m: [1;36m0[0m,
                [32m'sep'[0m: [3;35mNone[0m,
                [32m'header'[0m: [1;36m0[0m,
                [32m'encoding'[0m: [32m'ISO-8859-1'[0m,
                [32m'decimal'[0m: [32m'.'[0m,
                [32m'thousands'[0m: [3;35mNone[0m
            [1m}[0m,
            [33mmeta_keys[0m=[1m{[0m[1m}[0m,
            [33mpre_processors[0m=[1m{[0m[1m}[0m,
            [33mpost_processors[0m=[1m{[0m
                [32m'split_capacity'[0m: [3;91mFalse[0m,
                [32m'split_current'[0m: [3;91mFalse[0m,
                [32m'cumulate_capacity_within_cycle'[0m: [3;92mTrue[0m,
                [32m'set_index'[0m: [3;92mTrue[0m,
                [32m'rename_headers'[0m: [3;92mTrue[0m,
                [32m'set_cycle_number_not_zero'[0m: [3;91mFalse[0m,
                [32m'convert_date_time_to_datetime'[0m: [3;92mTrue[0m,
                [32m'convert_step_time_to_timedelta'[0m: [3;92mTrue[0m,
                [32m'convert_test_time_to_timedelta'[0m: [3;92mTrue[0m
            [1m}[0m,
            [33mprefixes[0m=[1m{[0m[1m}[0m
        [1m)[0m,
        [32m'doc'[0m: [32m'Class for loading data from Neware txt files.'[0m
    [1m}[0m
    



```python
p = example_data.neware_file_path()
print(f"{p.name=}")
```


    p.[33mname[0m=[32m'neware_uio.csv'[0m
    



```python
c = cellpy.get(p, instrument="neware_txt", mass=2.09)
```

    auto-formatting
    (cellpy) - auto-formatting:
      self.sep=','
      self.skiprows=-1
      self.header=0
      self.encoding='UTF-8'
    
    (cellpy) - self.sep=',', self.skiprows=-1, self.header=0, self.encoding='UTF-8', self.decimal='.'
    (cellpy) - running post-processor: rename_headers
    Index(['DataPoint', 'Cycle Index', 'Step Index', 'Step Type', 'Time',
           'Cumulative Time', 'Current(A)', 'Voltage(V)', 'Capacity(Ah)',
           'Spec. Cap.(mAh/g)', 'Chg. Cap.(Ah)', 'Chg. Spec. Cap.(mAh/g)',
           'DChg. Cap.(Ah)', 'DChg. Spec. Cap.(mAh/g)', 'Energy(Wh)',
           'Spec. Energy(mWh/g)', 'Chg. Energy(Wh)', 'Chg. Spec. Energy(mWh/g)',
           'DChg. Energy(Wh)', 'DChg. Spec. Energy(mWh/g)', 'Date', 'Power(W)',
           'dQ/dV(mAh/V)', 'dQm/dV(mAh/V.g)', 'Contact resistance(mO)',
           'Module start-stop switch'],
          dtype='object')
    (cellpy) - running post-processor: cumulate_capacity_within_cycle
    (cellpy) - running post-processor: set_index
    (cellpy) - running post-processor: convert_date_time_to_datetime
    (cellpy) - running post-processor: convert_step_time_to_timedelta
    (cellpy) - running post-processor: convert_test_time_to_timedelta
    

Notice that this loader (with the default model) uses the auto-formatting method. The method tries to find out type of delimiter and number of header rows automatically. You can override this by providing the values in the call yourself, for example `c.get(p, instrument="neware_txt", sep=",")`


```python
plotutils.raw_plot(c, width=1200, height=400)
```




```python
plotutils.summary_plot(
    c, y="capacities_gravimetric", width=1200, height=400, y_range=[0, 4000]
)
```



## Other

The `cellpy` team is working actively on implementing support for more instruments. If the file format is not too challenging, consider using a custom loader (see [custom loaders](07_custom_loaders.ipynb)).
