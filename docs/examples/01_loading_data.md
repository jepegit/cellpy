# Loading, saving and exporting data


```python
import pathlib

import numpy as np
import pandas as pd
from rich import print

import cellpy
```

Set the paths and filename(s).
You can either load a single file ``filename``, or add a list of filenames ``filenamelist`` (if several files belong to the same experiment):


```python
filedir = pathlib.Path("data")  # foldername within the same directory

# single filename
filename = "20210210_FC_01_cc_01.res"
# list of files (continuations within same experiment)
filenamelist = [
    "20210210_FC_01_cc_01.res",
    "20210210_FC_01_cc_02.res",
    "20210210_FC_01_cc_03.res",
    "20210210_FC_01_cc_04.res",
]

filepaths = [filedir / file for file in filenamelist]
```

## Loading data

Use `cellpy.get()` to load the rawdatafile(s):


```python
c = cellpy.get(filepaths, mass=1.2, cycle_mode="full-cell")
```

**Note:** Without any further specifications, ``cellpy.get()`` will use the standard instrument loader as defined in your config file (here the one for loading arbin .res files). For loading different data formats, have a look at [Loading different formats](06_loading_different_formats.ipynb) or [Custom loaders](07_custom_loaders.ipynb).

Now you have created your **CellpyCell** object and can start to explore it further. The ``cellpy.get()`` function conveniently created a so-called *step-table* and a *summary* for you (both are pandas dataframes):

### Data inspection


```python
c.data.summary.head(5)
```




                 data_point     test_time                  date_time  \
    cycle_index                                                        
    1                  5797  1.743286e+05 2021-05-12 10:40:11.000000   
    2                  7188  3.171618e+05 2021-05-14 02:20:47.000000   
    3                  7218  3.189618e+05 2021-05-14 02:50:47.000000   
    4                 34207  9.954903e+05 2021-05-22 17:30:55.000000   
    5                 60493  1.508876e+06 2021-05-27 21:23:41.999999   
    
                 end_voltage_charge  end_voltage_discharge  charge_capacity  \
    cycle_index                                                               
    1                      4.200052               3.129170         0.003819   
    2                      4.200052               3.188442         0.003422   
    3                      0.000000               0.000000         0.000000   
    4                      4.200052               2.999878         0.003331   
    5                      4.200052               2.999878         0.003358   
    
                 discharge_capacity  coulombic_efficiency  \
    cycle_index                                             
    1                      0.003324             87.049469   
    2                      0.003234             94.510786   
    3                      0.000000                   NaN   
    4                      0.003288             98.693739   
    5                      0.003392            101.021637   
    
                 cumulated_coulombic_efficiency  cumulated_charge_capacity  ...  \
    cycle_index                                                             ...   
    1                                 87.049469                   0.003819  ...   
    2                                181.560255                   0.007241  ...   
    3                                       NaN                   0.007241  ...   
    4                                280.253993                   0.010572  ...   
    5                                381.275630                   0.013930  ...   
    
                 cumulated_charge_capacity_areal  \
    cycle_index                                    
    1                                   3.818560   
    2                                   7.240795   
    3                                   7.240795   
    4                                  10.571992   
    5                                  13.929539   
    
                 cumulated_discharge_capacity_areal  coulombic_difference_areal  \
    cycle_index                                                                   
    1                                      3.324036                    0.494524   
    2                                      6.558417                    0.187854   
    3                                      6.558417                    0.000000   
    4                                      9.846100                    0.043514   
    5                                     13.237949                   -0.034302   
    
                 cumulated_coulombic_difference_areal  \
    cycle_index                                         
    1                                        0.494524   
    2                                        0.682378   
    3                                        0.682378   
    4                                        0.725892   
    5                                        0.691590   
    
                 discharge_capacity_loss_areal  charge_capacity_loss_areal  \
    cycle_index                                                              
    1                                      NaN                         NaN   
    2                                 0.089654                    0.396324   
    3                                 3.234381                    3.422235   
    4                                -3.287683                   -3.331197   
    5                                -0.104166                   -0.026350   
    
                 cumulated_discharge_capacity_loss_areal  \
    cycle_index                                            
    1                                                NaN   
    2                                           0.089654   
    3                                           3.324036   
    4                                           0.036353   
    5                                          -0.067813   
    
                 cumulated_charge_capacity_loss_areal  \
    cycle_index                                         
    1                                             NaN   
    2                                        0.396324   
    3                                        3.818560   
    4                                        0.487362   
    5                                        0.461013   
    
                 shifted_charge_capacity_areal  shifted_discharge_capacity_areal  
    cycle_index                                                                   
    1                                 0.494524                          4.313083  
    2                                 0.682378                          4.104613  
    3                                 0.682378                          0.682378  
    4                                 0.725892                          4.057089  
    5                                 0.691590                          4.049137  
    
    [5 rows x 49 columns]




```python
c.data.steps.head(5)
```




       index  cycle  step  sub_step  point_avr    point_std  point_min  point_max  \
    0      0      1     1         1     2157.5  1245.488860          1       4314   
    1      1      1     2         1     4315.0          NaN       4315       4315   
    2      2      1     3         1     4645.5   190.669872       4316       4975   
    3      3      1     4         1     5023.0    27.568098       4976       5070   
    4      4      1     5         1     5071.0          NaN       5071       5071   
    
       point_first  point_last  ...  ir_std    ir_min    ir_max  ir_first  \
    0            1        4314  ...     0.0  0.000000  0.000000  0.000000   
    1         4315        4315  ...     NaN  6.650723  6.650723  6.650723   
    2         4316        4975  ...     0.0  6.650723  6.650723  6.650723   
    3         4976        5070  ...     0.0  6.650723  6.650723  6.650723   
    4         5071        5071  ...     NaN  8.664473  8.664473  8.664473   
    
        ir_last  ir_delta   rate_avr    type  sub_type  info  
    0  0.000000       0.0    0.00000    rest      None        
    1  6.650723       0.0    1.75791      ir      None        
    2  6.650723       0.0  150.69784  charge      None        
    3  6.650723       0.0   60.38439  charge      None        
    4  8.664473       0.0    0.29138      ir      None        
    
    [5 rows x 64 columns]



It also contains the raw data:


```python
c.data.raw.head(5)
```




       test_id  data_point  test_time  step_time           date_time  step_index  \
    0        1           1   5.008961   5.008961 2021-05-10 10:14:45           1   
    1        1           2  10.019319  10.019319 2021-05-10 10:14:50           1   
    2        1           3  15.026495  15.026495 2021-05-10 10:14:55           1   
    3        1           4  20.038747  20.038747 2021-05-10 10:15:00           1   
    4        1           5  25.040517  25.040517 2021-05-10 10:15:05           1   
    
       cycle_index  is_fc_data  current   voltage  charge_capacity  \
    0            1           0      0.0  3.051165              0.0   
    1            1           0      0.0  3.051165              0.0   
    2            1           0      0.0  3.051165              0.0   
    3            1           0      0.0  3.050858              0.0   
    4            1           0      0.0  3.050551              0.0   
    
       discharge_capacity  charge_energy  discharge_energy     dv_dt  \
    0                 0.0            0.0               0.0 -0.000061   
    1                 0.0            0.0               0.0  0.000000   
    2                 0.0            0.0               0.0  0.000000   
    3                 0.0            0.0               0.0 -0.000123   
    4                 0.0            0.0               0.0 -0.000061   
    
       internal_resistance  ac_impedance  aci_phase_angle  
    0                  0.0           0.0              0.0  
    1                  0.0           0.0              0.0  
    2                  0.0           0.0              0.0  
    3                  0.0           0.0              0.0  
    4                  0.0           0.0              0.0  



### Metadata

Cellpy fills in some standard values for meta-data for you (based on your config-file), these can be updated and adjusted.

E.g., we can set a new cell name and add a value active electrode area:


```python
c.active_electrode_area = 1.767
c.cell_name = "20210210_FC"
```

!!! note
    If you change variables that are used in calculating summary values (such as for example `cycle_mode`, `mass`, `active_electrode_area`), you need to re-make the summary for it to be updated:

    ```python
    c.make_summary()
    ```

To check the units that are used within cellpy:


```python
print(c.cellpy_units)
```


    [1;35mCellpyUnits[0m[1m([0m
        [33mcurrent[0m=[32m'A'[0m,
        [33mcharge[0m=[32m'mAh'[0m,
        [33mvoltage[0m=[32m'V'[0m,
        [33mtime[0m=[32m'sec'[0m,
        [33mresistance[0m=[32m'ohm'[0m,
        [33mpower[0m=[32m'W'[0m,
        [33menergy[0m=[32m'Wh'[0m,
        [33mfrequency[0m=[32m'hz'[0m,
        [33mmass[0m=[32m'mg'[0m,
        [33mnominal_capacity[0m=[32m'mAh/g'[0m,
        [33mspecific_gravimetric[0m=[32m'g'[0m,
        [33mspecific_areal[0m=[32m'cm**2'[0m,
        [33mspecific_volumetric[0m=[32m'cm**3'[0m,
        [33mlength[0m=[32m'cm'[0m,
        [33marea[0m=[32m'cm**2'[0m,
        [33mvolume[0m=[32m'cm**3'[0m,
        [33mtemperature[0m=[32m'C'[0m,
        [33mpressure[0m=[32m'bar'[0m
    [1m)[0m
    


Metadata can also be included by the use of a database file containing the required values. The information on database filename and content has to be set in the config file.

## Saving & exporting data

You can easily save all of this in the cellpy .HDF5 format:


```python
c.save(filedir / "out" / "20210210_FC")
```

or export to csv or excel


```python
c.to_csv(filedir / "out", sep=";", raw=True)
```


```python
c.to_excel(filedir / "out" / "20210210_FC.xlsx")
```

## Loading saved files

To load saved files, you can use the `cellpy.get()` function again:


```python
c = cellpy.get(filedir / "out" / "20210210_FC.h5")
```


```python
c.data.summary.head()
```




                 data_point     test_time                  date_time  \
    cycle_index                                                        
    1                  5797  1.743286e+05 2021-05-12 10:40:11.000000   
    2                  7188  3.171618e+05 2021-05-14 02:20:47.000000   
    3                  7218  3.189618e+05 2021-05-14 02:50:47.000000   
    4                 34207  9.954903e+05 2021-05-22 17:30:55.000000   
    5                 60493  1.508876e+06 2021-05-27 21:23:41.999999   
    
                 end_voltage_charge  end_voltage_discharge  charge_capacity  \
    cycle_index                                                               
    1                      4.200052               3.129170         0.003819   
    2                      4.200052               3.188442         0.003422   
    3                      0.000000               0.000000         0.000000   
    4                      4.200052               2.999878         0.003331   
    5                      4.200052               2.999878         0.003358   
    
                 discharge_capacity  coulombic_efficiency  \
    cycle_index                                             
    1                      0.003324             87.049469   
    2                      0.003234             94.510786   
    3                      0.000000                   NaN   
    4                      0.003288             98.693739   
    5                      0.003392            101.021637   
    
                 cumulated_coulombic_efficiency  cumulated_charge_capacity  ...  \
    cycle_index                                                             ...   
    1                                 87.049469                   0.003819  ...   
    2                                181.560255                   0.007241  ...   
    3                                       NaN                   0.007241  ...   
    4                                280.253993                   0.010572  ...   
    5                                381.275630                   0.013930  ...   
    
                 cumulated_charge_capacity_areal  \
    cycle_index                                    
    1                                   3.818560   
    2                                   7.240795   
    3                                   7.240795   
    4                                  10.571992   
    5                                  13.929539   
    
                 cumulated_discharge_capacity_areal  coulombic_difference_areal  \
    cycle_index                                                                   
    1                                      3.324036                    0.494524   
    2                                      6.558417                    0.187854   
    3                                      6.558417                    0.000000   
    4                                      9.846100                    0.043514   
    5                                     13.237949                   -0.034302   
    
                 cumulated_coulombic_difference_areal  \
    cycle_index                                         
    1                                        0.494524   
    2                                        0.682378   
    3                                        0.682378   
    4                                        0.725892   
    5                                        0.691590   
    
                 discharge_capacity_loss_areal  charge_capacity_loss_areal  \
    cycle_index                                                              
    1                                      NaN                         NaN   
    2                                 0.089654                    0.396324   
    3                                 3.234381                    3.422235   
    4                                -3.287683                   -3.331197   
    5                                -0.104166                   -0.026350   
    
                 cumulated_discharge_capacity_loss_areal  \
    cycle_index                                            
    1                                                NaN   
    2                                           0.089654   
    3                                           3.324036   
    4                                           0.036353   
    5                                          -0.067813   
    
                 cumulated_charge_capacity_loss_areal  \
    cycle_index                                         
    1                                             NaN   
    2                                        0.396324   
    3                                        3.818560   
    4                                        0.487362   
    5                                        0.461013   
    
                 shifted_charge_capacity_areal  shifted_discharge_capacity_areal  
    cycle_index                                                                   
    1                                 0.494524                          4.313083  
    2                                 0.682378                          4.104613  
    3                                 0.682378                          0.682378  
    4                                 0.725892                          4.057089  
    5                                 0.691590                          4.049137  
    
    [5 rows x 49 columns]




```python

```
