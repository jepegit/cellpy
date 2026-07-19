# Defining your own custom loaders


```python
from rich import print

import cellpy
from cellpy.utils import example_data, plotutils
```

Defining a simple utility-function to get a peek of the file in question:


```python
def head(f, n=5):
    print(f" {f.name} ".center(80, "="))
    with open(f) as datafile:
        if n > 1:
            for j in range(n):
                line = datafile.readline()
                print(f"[{j + 1:02}] {line.rstrip()}")
        else:
            for j, line in enumerate(datafile.readlines()):
                print(f"[{j + 1:02}] {line.rstrip()}")
    print(f" {f.name} ".center(80, "="))
```

## Using the "custom" instrument

This loader can be used if you have simple but unusual files. It needs an instrument file containing a description of the structure of the data file.
You can load files in csv, xlsx, and xls format using this loader.

Here is an example of a custom data file and a corresponding instrument file (yaml format).


```python
p_csv = example_data.custom_file_path()
instrument_file = example_data.custom_instrument_path()
```


```python
head(p_csv, 30)
```


    =============================== custom_data.csv ================================
    



    [1m[[0m[1;36m01[0m[1m][0m # PRIME INSTRUMENT FILE --- M12X---!! HEAD !!---M13B---;;;;;;;;;
    



    [1m[[0m[1;36m02[0m[1m][0m number of headers ;[1;36m19[0m;;;;;;;;
    



    [1m[[0m[1;36m03[0m[1m][0m operator;Jan Petter Maehlen;;;;;;;;
    



    [1m[[0m[1;36m04[0m[1m][0m date;[1;36m01.01[0m.[1;36m2016[0m;;;;;;;;
    



    [1m[[0m[1;36m05[0m[1m][0m instrument;bobby;;;;;;;;
    



    [1m[[0m[1;36m06[0m[1m][0m schedule;galvanic;;;;;;;;
    



    [1m[[0m[1;36m07[0m[1m][0m cell;ee002;;;;;;;;
    



    [1m[[0m[1;36m08[0m[1m][0m geometry;half-cell;;;;;;;;
    



    [1m[[0m[1;36m09[0m[1m][0m counter;Li-metal;;;;;;;;
    



    [1m[[0m[1;36m10[0m[1m][0m material;si-based;;;;;;;;
    



    [1m[[0m[1;36m11[0m[1m][0m mass;[1;36m0.0012[0m;;;;;;;;
    



    [1m[[0m[1;36m12[0m[1m][0m # PRIME INSTRUMENT FILE ---L01---[32m''[0mLOG'' --[1;36m-0000000[0m-;;;;;;;;;
    



    [1m[[0m[1;36m13[0m[1m][0m [1;36m15[0m;Started collecting auxilary data [1m([0msaved to output.log[1m)[0m;;;;;;;;
    



    [1m[[0m[1;36m14[0m[1m][0m [1;36m773[0m;Problem encountered - reloading config;;;;;;;;
    



    [1m[[0m[1;36m15[0m[1m][0m [1;36m1111[0m;R12;;;;;;;;
    



    [1m[[0m[1;36m16[0m[1m][0m [1;36m6588[0m;R12;;;;;;;;
    



    [1m[[0m[1;36m17[0m[1m][0m [1;36m7712[0m;Problem encountered - reloading config;;;;;;;;
    



    [1m[[0m[1;36m18[0m[1m][0m [1;36m78999[0m;R0;;;;;;;;
    



    [1m[[0m[1;36m19[0m[1m][0m # PRIME INSTRUMENT FILE --[1;36m-268876[0m-;;;;;;;;;
    



    [1m[[0m[1;36m20[0m[1m][0m index;test_time;step_time;date_stamp;step;cycle;current;voltage;charge_capacity;discharge_Capacity
    



    [1m[[0m[1;36m21[0m[1m][0m [1;36m0[0m;[1;36m120.00[0m;[1;36m120.00[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m22[0m[1m][0m [1;36m1[0m;[1;36m240.00[0m;[1;36m240.00[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m23[0m[1m][0m [1;36m2[0m;[1;36m360.00[0m;[1;36m360.00[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m24[0m[1m][0m [1;36m3[0m;[1;36m480.00[0m;[1;36m480.00[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m25[0m[1m][0m [1;36m4[0m;[1;36m600.01[0m;[1;36m600.01[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m26[0m[1m][0m [1;36m5[0m;[1;36m720.01[0m;[1;36m720.01[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m27[0m[1m][0m [1;36m6[0m;[1;36m840.01[0m;[1;36m840.01[0m;[1;36m43374.42[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m28[0m[1m][0m [1;36m7[0m;[1;36m960.01[0m;[1;36m960.01[0m;[1;36m43374.43[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m29[0m[1m][0m [1;36m8[0m;[1;36m1080.01[0m;[1;36m1080.01[0m;[1;36m43374.43[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    [1m[[0m[1;36m30[0m[1m][0m [1;36m9[0m;[1;36m1200.01[0m;[1;36m1200.01[0m;[1;36m43374.43[0m;[1;36m1[0m;[1;36m1[0m;[1;36m0.00[0m;[1;36m1.14[0m;[1;36m0.00[0m;[1;36m0.00[0m
    



    =============================== custom_data.csv ================================
    



```python
head(instrument_file, -1)
```


    ============================ custom_instrument.yml =============================
    



    [1m[[0m[1;36m01[0m[1m][0m ---
    



    [1m[[0m[1;36m02[0m[1m][0m formatters:
    



    [1m[[0m[1;36m03[0m[1m][0m     skiprows: [1;36m19[0m
    



    [1m[[0m[1;36m04[0m[1m][0m     sep: [32m";"[0m
    



    [1m[[0m[1;36m05[0m[1m][0m     header: [1;36m0[0m
    



    [1m[[0m[1;36m06[0m[1m][0m     encoding: ISO-[1;36m8859[0m-[1;36m1[0m  # options: ISO-[1;36m8859[0m-[1;36m1[0m utf-[1;36m8[0m cp1252
    



    [1m[[0m[1;36m07[0m[1m][0m     decimal: .
    



    [1m[[0m[1;36m08[0m[1m][0m     thousands:
    



    [1m[[0m[1;36m09[0m[1m][0m     comment_chars:
    



    [1m[[0m[1;36m10[0m[1m][0m         - [32m'#'[0m
    



    [1m[[0m[1;36m11[0m[1m][0m         - [32m'!'[0m
    



    [1m[[0m[1;36m12[0m[1m][0m post_processors:
    



    [1m[[0m[1;36m13[0m[1m][0m     split_capacity: false
    



    [1m[[0m[1;36m14[0m[1m][0m     split_current: false
    



    [1m[[0m[1;36m15[0m[1m][0m     set_index: false
    



    [1m[[0m[1;36m16[0m[1m][0m     rename_headers: true
    



    [1m[[0m[1;36m17[0m[1m][0m     set_cycle_number_not_zero: false
    



    [1m[[0m[1;36m18[0m[1m][0m     convert_date_time_to_datetime: true
    



    [1m[[0m[1;36m19[0m[1m][0m     convert_step_time_to_timedelta: false
    



    [1m[[0m[1;36m20[0m[1m][0m     convert_test_time_to_timedelta: false
    



    [1m[[0m[1;36m21[0m[1m][0m normal_headers_renaming_dict:
    



    [1m[[0m[1;36m22[0m[1m][0m     data_point_txt: [32m"index"[0m
    



    [1m[[0m[1;36m23[0m[1m][0m     datetime_txt: [32m"date_stamp"[0m
    



    [1m[[0m[1;36m24[0m[1m][0m     test_time_txt: [32m"test_time"[0m
    



    [1m[[0m[1;36m25[0m[1m][0m     step_time_txt: [32m"step_time"[0m
    



    [1m[[0m[1;36m26[0m[1m][0m     cycle_index_txt: [32m"cycle"[0m
    



    [1m[[0m[1;36m27[0m[1m][0m     step_index_txt: [32m"step"[0m
    



    [1m[[0m[1;36m28[0m[1m][0m     current_txt: [32m"current"[0m
    



    [1m[[0m[1;36m29[0m[1m][0m     voltage_txt: [32m"voltage"[0m
    



    [1m[[0m[1;36m30[0m[1m][0m     charge_capacity_txt: [32m"charge_capacity"[0m
    



    [1m[[0m[1;36m31[0m[1m][0m     discharge_capacity_txt: [32m"discharge_Capacity"[0m
    



    [1m[[0m[1;36m32[0m[1m][0m unit_labels:
    



    [1m[[0m[1;36m33[0m[1m][0m     resistance: Ohms
    



    [1m[[0m[1;36m34[0m[1m][0m     time: s
    



    [1m[[0m[1;36m35[0m[1m][0m     current: mA
    



    [1m[[0m[1;36m36[0m[1m][0m     voltage: V
    



    [1m[[0m[1;36m37[0m[1m][0m     power: W
    



    [1m[[0m[1;36m38[0m[1m][0m     capacity: mAh
    



    [1m[[0m[1;36m39[0m[1m][0m     energy: Wh
    



    [1m[[0m[1;36m40[0m[1m][0m     temperature: C
    



    [1m[[0m[1;36m41[0m[1m][0m raw_units:
    



    [1m[[0m[1;36m42[0m[1m][0m     current: A
    



    [1m[[0m[1;36m43[0m[1m][0m     charge: Ah
    



    [1m[[0m[1;36m44[0m[1m][0m     mass: mg
    



    [1m[[0m[1;36m45[0m[1m][0m     time: s
    



    [1m[[0m[1;36m46[0m[1m][0m raw_limits:
    



    [1m[[0m[1;36m47[0m[1m][0m     current_hard: [1;36m1.0e-13[0m
    



    [1m[[0m[1;36m48[0m[1m][0m     current_soft: [1;36m1.0e-05[0m
    



    [1m[[0m[1;36m49[0m[1m][0m     ir_change: [1;36m1.0e-05[0m
    



    [1m[[0m[1;36m50[0m[1m][0m     stable_charge_hard: [1;36m0.9[0m
    



    [1m[[0m[1;36m51[0m[1m][0m     stable_charge_soft: [1;36m5.0[0m
    



    [1m[[0m[1;36m52[0m[1m][0m     stable_current_hard: [1;36m2.0[0m
    



    [1m[[0m[1;36m53[0m[1m][0m     stable_current_soft: [1;36m4.0[0m
    



    [1m[[0m[1;36m54[0m[1m][0m     stable_voltage_hard: [1;36m2.0[0m
    



    [1m[[0m[1;36m55[0m[1m][0m     stable_voltage_soft: [1;36m4.0[0m
    



    ============================ custom_instrument.yml =============================
    



```python
c = cellpy.get(p_csv, instrument="custom", instrument_file=instrument_file)
```

    (cellpy) - self.sep=';', self.skiprows=19, self.header=0, self.encoding='ISO-8859-1', self.decimal='.'
    (cellpy) - running post-processor: rename_headers
    Index(['index', 'test_time', 'step_time', 'date_stamp', 'step', 'cycle',
           'current', 'voltage', 'charge_capacity', 'discharge_Capacity'],
          dtype='object')
    (cellpy) - running post-processor: convert_date_time_to_datetime
    


```python
plotutils.raw_plot(c, width=1200, height=400)
```




    
![png](07_custom_loaders_files/07_custom_loaders_9_1.png)
    


## Using the "local_instrument" loader

This loader is used for loading data using the corresponding local yaml file with definitions on how the data should be loaded. This loader
is based on the ``TxtLoader`` and can only be used to load csv-type files.
As a "short-cut", this loader will be used if you set the ``instrument`` to the name of the instrument file (with the ``.yml`` extension) e.g.
``c = cellpy.get(rawfile, instrument="instrumentfile.yml")``.
The default instrument file is defined in your cellpy configuration file:
```
Instruments:
  custom_instrument_definitions_file: my_local_instrument.yml
```

As an example, let us see how we could load one of the example Maccor files using a local instrument definition file instead of the implemented "maccor_txt" loader.


```python
p = example_data.maccor_file_path()
print(f"{p.name=}")
```


    p.[33mname[0m=[32m'maccor_three.txt'[0m
    



```python
local_instrument = example_data.local_instrument_path()
print(f"{local_instrument.name=}")
```


    local_instrument.[33mname[0m=[32m'local_instrument.yml'[0m
    



```python
head(local_instrument, -1)
```


    ============================= local_instrument.yml =============================
    



    [1m[[0m[1;36m01[0m[1m][0m ---
    



    [1m[[0m[1;36m02[0m[1m][0m formatters:
    



    [1m[[0m[1;36m03[0m[1m][0m     skiprows: [1;36m2[0m
    



    [1m[[0m[1;36m04[0m[1m][0m     sep: [32m"\t"[0m
    



    [1m[[0m[1;36m05[0m[1m][0m     header: [1;36m0[0m
    



    [1m[[0m[1;36m06[0m[1m][0m     encoding: ISO-[1;36m8859[0m-[1;36m1[0m
    



    [1m[[0m[1;36m07[0m[1m][0m     decimal: .
    



    [1m[[0m[1;36m08[0m[1m][0m     thousands:
    



    [1m[[0m[1;36m09[0m[1m][0m     comment_chars:
    



    [1m[[0m[1;36m10[0m[1m][0m         - [32m'#'[0m
    



    [1m[[0m[1;36m11[0m[1m][0m         - [32m'!'[0m
    



    [1m[[0m[1;36m12[0m[1m][0m pre_processors:
    



    [1m[[0m[1;36m13[0m[1m][0m     remove_empty_lines: true
    



    [1m[[0m[1;36m14[0m[1m][0m post_processors:
    



    [1m[[0m[1;36m15[0m[1m][0m     split_capacity: true
    



    [1m[[0m[1;36m16[0m[1m][0m     split_current: true
    



    [1m[[0m[1;36m17[0m[1m][0m     set_index: true
    



    [1m[[0m[1;36m18[0m[1m][0m     rename_headers: true
    



    [1m[[0m[1;36m19[0m[1m][0m     set_cycle_number_not_zero: true
    



    [1m[[0m[1;36m20[0m[1m][0m     remove_last_if_bad: true
    



    [1m[[0m[1;36m21[0m[1m][0m     convert_date_time_to_datetime: true
    



    [1m[[0m[1;36m22[0m[1m][0m     convert_step_time_to_timedelta: true
    



    [1m[[0m[1;36m23[0m[1m][0m     convert_test_time_to_timedelta: true
    



    [1m[[0m[1;36m24[0m[1m][0m normal_headers_renaming_dict:
    



    [1m[[0m[1;36m25[0m[1m][0m     data_point_txt: [32m"Rec#"[0m
    



    [1m[[0m[1;36m26[0m[1m][0m     datetime_txt: [32m"DPt Time"[0m
    



    [1m[[0m[1;36m27[0m[1m][0m     test_time_txt: [32m"TestTime"[0m
    



    [1m[[0m[1;36m28[0m[1m][0m     step_time_txt: [32m"StepTime"[0m
    



    [1m[[0m[1;36m29[0m[1m][0m     cycle_index_txt: [32m"Cyc#"[0m
    



    [1m[[0m[1;36m30[0m[1m][0m     step_index_txt: [32m"Step"[0m
    



    [1m[[0m[1;36m31[0m[1m][0m     current_txt: [32m"mAmps"[0m
    



    [1m[[0m[1;36m32[0m[1m][0m     voltage_txt: [32m"Volts"[0m
    



    [1m[[0m[1;36m33[0m[1m][0m #    power_txt: [32m"Watt-hr"[0m
    



    [1m[[0m[1;36m34[0m[1m][0m     charge_capacity_txt: [32m"mAmp-hr"[0m
    



    [1m[[0m[1;36m35[0m[1m][0m     charge_energy_txt: [32m"mWatt-hr"[0m
    



    [1m[[0m[1;36m36[0m[1m][0m #    ac_impedance_txt: [32m"ACImp/Ohms"[0m
    



    [1m[[0m[1;36m37[0m[1m][0m #    internal_resistance_txt: [32m"DCIR/Ohms"[0m
    



    [1m[[0m[1;36m38[0m[1m][0m unit_labels:
    



    [1m[[0m[1;36m39[0m[1m][0m     resistance: Ohms
    



    [1m[[0m[1;36m40[0m[1m][0m     time: s
    



    [1m[[0m[1;36m41[0m[1m][0m     current: mA
    



    [1m[[0m[1;36m42[0m[1m][0m     voltage: mV
    



    [1m[[0m[1;36m43[0m[1m][0m     power: mW
    



    [1m[[0m[1;36m44[0m[1m][0m     capacity: mAh
    



    [1m[[0m[1;36m45[0m[1m][0m     energy: mWh
    



    [1m[[0m[1;36m46[0m[1m][0m     temperature: C
    



    [1m[[0m[1;36m47[0m[1m][0m states:
    



    [1m[[0m[1;36m48[0m[1m][0m     column_name: State
    



    [1m[[0m[1;36m49[0m[1m][0m     charge_keys:
    



    [1m[[0m[1;36m50[0m[1m][0m         - C
    



    [1m[[0m[1;36m51[0m[1m][0m     discharge_keys:
    



    [1m[[0m[1;36m52[0m[1m][0m         - D
    



    [1m[[0m[1;36m53[0m[1m][0m     rest_keys:
    



    [1m[[0m[1;36m54[0m[1m][0m         - R
    



    [1m[[0m[1;36m55[0m[1m][0m raw_units:
    



    [1m[[0m[1;36m56[0m[1m][0m     current: [32m"mA"[0m
    



    [1m[[0m[1;36m57[0m[1m][0m     charge: [32m"mAh"[0m
    



    [1m[[0m[1;36m58[0m[1m][0m     mass: [32m"g"[0m
    



    [1m[[0m[1;36m59[0m[1m][0m     voltage: [32m"mV"[0m
    



    [1m[[0m[1;36m60[0m[1m][0m raw_limits:
    



    [1m[[0m[1;36m61[0m[1m][0m     current_hard: [1;36m1.0e-13[0m
    



    [1m[[0m[1;36m62[0m[1m][0m     current_soft: [1;36m1.0e-05[0m
    



    [1m[[0m[1;36m63[0m[1m][0m     ir_change: [1;36m1.0e-05[0m
    



    [1m[[0m[1;36m64[0m[1m][0m     stable_charge_hard: [1;36m0.9[0m
    



    [1m[[0m[1;36m65[0m[1m][0m     stable_charge_soft: [1;36m5.0[0m
    



    [1m[[0m[1;36m66[0m[1m][0m     stable_current_hard: [1;36m2.0[0m
    



    [1m[[0m[1;36m67[0m[1m][0m     stable_current_soft: [1;36m4.0[0m
    



    [1m[[0m[1;36m68[0m[1m][0m     stable_voltage_hard: [1;36m2.0[0m
    



    [1m[[0m[1;36m69[0m[1m][0m     stable_voltage_soft: [1;36m4.0[0m
    



    ============================= local_instrument.yml =============================
    



```python
head(p, 20)
```


    =============================== maccor_three.txt ===============================
    



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
    



    [1m[[0m[1;36m11[0m[1m][0m [1;36m6[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:05:00[0m.[1;36m00[0m          0d [1;92m00:05:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:09:18[0m PM
    



    [1m[[0m[1;36m12[0m[1m][0m [1;36m7[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:06:00[0m.[1;36m00[0m          0d [1;92m00:06:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:10:18[0m PM
    



    [1m[[0m[1;36m13[0m[1m][0m [1;36m8[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:07:00[0m.[1;36m00[0m          0d [1;92m00:07:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:11:18[0m PM
    



    [1m[[0m[1;36m14[0m[1m][0m [1;36m9[0m  [1;36m0[0m       [1;36m1[0m         0d [1;92m00:08:00[0m.[1;36m00[0m          0d [1;92m00:08:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1852.903[0m        R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:12:18[0m PM
    



    [1m[[0m[1;36m15[0m[1m][0m [1;36m10[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:09:00[0m.[1;36m00[0m          0d [1;92m00:09:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:13:18[0m PM
    



    [1m[[0m[1;36m16[0m[1m][0m [1;36m11[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:10:00[0m.[1;36m00[0m          0d [1;92m00:10:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:14:18[0m PM
    



    [1m[[0m[1;36m17[0m[1m][0m [1;36m12[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:11:00[0m.[1;36m00[0m          0d [1;92m00:11:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:15:18[0m PM
    



    [1m[[0m[1;36m18[0m[1m][0m [1;36m13[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:12:00[0m.[1;36m00[0m          0d [1;92m00:12:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.0556[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:16:18[0m PM
    



    [1m[[0m[1;36m19[0m[1m][0m [1;36m14[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:13:00[0m.[1;36m00[0m          0d [1;92m00:13:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.2082[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:17:18[0m PM
    



    [1m[[0m[1;36m20[0m[1m][0m [1;36m15[0m [1;36m0[0m       [1;36m1[0m         0d [1;92m00:14:00[0m.[1;36m00[0m          0d [1;92m00:14:00[0m.[1;36m00[0m        [1;36m0.0[0m     [1;36m0.0[0m     [1;36m0.0[0m     [1;36m1853.3608[0m       R  
    [1;36m1[0m       [1;36m08[0m/[1;36m23[0m/[1;36m2021[0m [1;92m6:18:18[0m PM
    



    =============================== maccor_three.txt ===============================
    



```python
from cellpy import log

c = cellpy.get(p, instrument=local_instrument)
```

    (cellpy) - running pre-processor: remove_empty_lines
    (cellpy) - self.sep='\t', self.skiprows=2, self.header=0, self.encoding='ISO-8859-1', self.decimal='.'
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
    


```python
plotutils.raw_plot(c, width=1200, height=400)
```




```python
plotutils.summary_plot(c, width=1200, height=400)
```


