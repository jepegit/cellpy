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




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>test_id</th>
      <th>cycle_num</th>
      <th>datapoint_num_last</th>
      <th>last_test_time</th>
      <th>charge_capacity</th>
      <th>discharge_capacity</th>
      <th>coulombic_efficiency</th>
      <th>coulombic_difference</th>
      <th>charge_capacity_loss</th>
      <th>discharge_capacity_loss</th>
      <th>...</th>
      <th>discharge_capacity_absolute</th>
      <th>charge_capacity_absolute</th>
      <th>test_cumulated_charge_capacity_absolute</th>
      <th>test_cumulated_discharge_capacity_absolute</th>
      <th>coulombic_difference_absolute</th>
      <th>test_cumulated_coulombic_difference_absolute</th>
      <th>discharge_capacity_loss_absolute</th>
      <th>charge_capacity_loss_absolute</th>
      <th>test_cumulated_discharge_capacity_loss_absolute</th>
      <th>test_cumulated_charge_capacity_loss_absolute</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>1</td>
      <td>5797</td>
      <td>1.743286e+05</td>
      <td>0.003819</td>
      <td>0.003324</td>
      <td>87.049469</td>
      <td>0.000495</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>3.324036</td>
      <td>3.818560</td>
      <td>3.818560</td>
      <td>3.324036</td>
      <td>0.494524</td>
      <td>0.494524</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2</td>
      <td>7188</td>
      <td>3.171618e+05</td>
      <td>0.003422</td>
      <td>0.003234</td>
      <td>94.510786</td>
      <td>0.000188</td>
      <td>0.000396</td>
      <td>0.000090</td>
      <td>...</td>
      <td>3.234381</td>
      <td>3.422235</td>
      <td>7.240795</td>
      <td>6.558417</td>
      <td>0.187854</td>
      <td>0.682378</td>
      <td>0.089654</td>
      <td>0.396324</td>
      <td>0.089654</td>
      <td>0.396324</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>3</td>
      <td>7218</td>
      <td>3.189618e+05</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>NaN</td>
      <td>0.000000</td>
      <td>0.003422</td>
      <td>0.003234</td>
      <td>...</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>7.240795</td>
      <td>6.558417</td>
      <td>0.000000</td>
      <td>0.682378</td>
      <td>3.234381</td>
      <td>3.422235</td>
      <td>3.324036</td>
      <td>3.818560</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>4</td>
      <td>34207</td>
      <td>9.954903e+05</td>
      <td>0.003331</td>
      <td>0.003288</td>
      <td>98.693739</td>
      <td>0.000044</td>
      <td>-0.003331</td>
      <td>-0.003288</td>
      <td>...</td>
      <td>3.287683</td>
      <td>3.331197</td>
      <td>10.571992</td>
      <td>9.846100</td>
      <td>0.043514</td>
      <td>0.725892</td>
      <td>-3.287683</td>
      <td>-3.331197</td>
      <td>0.036353</td>
      <td>0.487362</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>5</td>
      <td>60493</td>
      <td>1.508876e+06</td>
      <td>0.003358</td>
      <td>0.003392</td>
      <td>101.021637</td>
      <td>-0.000034</td>
      <td>-0.000026</td>
      <td>-0.000104</td>
      <td>...</td>
      <td>3.391849</td>
      <td>3.357547</td>
      <td>13.929539</td>
      <td>13.237949</td>
      <td>-0.034302</td>
      <td>0.691590</td>
      <td>-0.104166</td>
      <td>-0.026350</td>
      <td>-0.067813</td>
      <td>0.461013</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 58 columns</p>
</div>




```python
c.data.steps.head(5)
```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>test_id</th>
      <th>cycle_num</th>
      <th>step_num</th>
      <th>sub_step_num</th>
      <th>datapoint_num_mean</th>
      <th>datapoint_num_std</th>
      <th>datapoint_num_min</th>
      <th>datapoint_num_max</th>
      <th>datapoint_num_first</th>
      <th>datapoint_num_last</th>
      <th>...</th>
      <th>step_time_delta</th>
      <th>current_delta</th>
      <th>potential_delta</th>
      <th>charge_capacity_delta</th>
      <th>discharge_capacity_delta</th>
      <th>internal_resistance_delta</th>
      <th>step_type</th>
      <th>sub_step_type</th>
      <th>info</th>
      <th>c_rate</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>2157.5</td>
      <td>1245.488860</td>
      <td>1</td>
      <td>4314</td>
      <td>1</td>
      <td>4314</td>
      <td>...</td>
      <td>4.311272e+05</td>
      <td>0.000000</td>
      <td>-0.271764</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>rest</td>
      <td>NaN</td>
      <td></td>
      <td>0.00000</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>1</td>
      <td>2</td>
      <td>1</td>
      <td>4315.0</td>
      <td>NaN</td>
      <td>4315</td>
      <td>4315</td>
      <td>4315</td>
      <td>4315</td>
      <td>...</td>
      <td>0.000000e+00</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>ir</td>
      <td>NaN</td>
      <td></td>
      <td>1.75791</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>1</td>
      <td>3</td>
      <td>1</td>
      <td>4645.5</td>
      <td>190.669872</td>
      <td>4316</td>
      <td>4975</td>
      <td>4316</td>
      <td>4975</td>
      <td>...</td>
      <td>1.181410e+08</td>
      <td>0.584801</td>
      <td>37.792713</td>
      <td>1.185637e+08</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>charge</td>
      <td>NaN</td>
      <td></td>
      <td>150.69784</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>1</td>
      <td>4</td>
      <td>1</td>
      <td>5023.0</td>
      <td>27.568098</td>
      <td>4976</td>
      <td>5070</td>
      <td>4976</td>
      <td>5070</td>
      <td>...</td>
      <td>1.726822e+04</td>
      <td>0.015646</td>
      <td>0.124449</td>
      <td>3.044886e+00</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>charge</td>
      <td>NaN</td>
      <td></td>
      <td>60.38439</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>1</td>
      <td>5</td>
      <td>1</td>
      <td>5071.0</td>
      <td>NaN</td>
      <td>5071</td>
      <td>5071</td>
      <td>5071</td>
      <td>5071</td>
      <td>...</td>
      <td>0.000000e+00</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>ir</td>
      <td>NaN</td>
      <td></td>
      <td>0.29138</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 64 columns</p>
</div>



It also contains the raw data:


```python
c.data.raw.head(5)
```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>test_id</th>
      <th>datapoint_num</th>
      <th>test_time</th>
      <th>step_time</th>
      <th>date_time</th>
      <th>step_num</th>
      <th>cycle_num</th>
      <th>is_fc_data</th>
      <th>current</th>
      <th>potential</th>
      <th>cumulative_charge_capacity</th>
      <th>cumulative_discharge_capacity</th>
      <th>cumulative_charge_energy</th>
      <th>cumulative_discharge_energy</th>
      <th>dv_dt</th>
      <th>internal_resistance</th>
      <th>ac_impedance</th>
      <th>aci_phase_angle</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>1</td>
      <td>5.008961</td>
      <td>5.008961</td>
      <td>2021-05-10 10:14:45</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0.0</td>
      <td>3.051165</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>-0.000061</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2</td>
      <td>10.019319</td>
      <td>10.019319</td>
      <td>2021-05-10 10:14:50</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0.0</td>
      <td>3.051165</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>3</td>
      <td>15.026495</td>
      <td>15.026495</td>
      <td>2021-05-10 10:14:55</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0.0</td>
      <td>3.051165</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>4</td>
      <td>20.038747</td>
      <td>20.038747</td>
      <td>2021-05-10 10:15:00</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0.0</td>
      <td>3.050858</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>-0.000123</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>5</td>
      <td>25.040517</td>
      <td>25.040517</td>
      <td>2021-05-10 10:15:05</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0.0</td>
      <td>3.050551</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>-0.000061</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>



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

    CellpyUnits(
        current='A',
        charge='mAh',
        voltage='V',
        time='sec',
        resistance='ohm',
        power='W',
        energy='Wh',
        frequency='hz',
        mass='mg',
        nominal_capacity='mAh/g',
        specific_gravimetric='g',
        specific_areal='cm**2',
        specific_volumetric='cm**3',
        length='cm',
        area='cm**2',
        volume='cm**3',
        temperature='C',
        pressure='bar'
    )


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
candidates = [
    filedir / "20210210_FC.h5",
    filedir / "out" / "20210210_FC.h5",
]
cellpy_path = next((p for p in candidates if p.exists()), None)
if cellpy_path is None:
    raise FileNotFoundError(
        "Could not find 20210210_FC.h5 in data/ or data/out/. "
        "Run the save cell above, or place the file in examples/data/."
    )
c = cellpy.get(cellpy_path)

```


```python
c.data.summary.head()
```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>cycle_num</th>
      <th>datapoint_num_last</th>
      <th>last_test_time</th>
      <th>date_time</th>
      <th>potential_end_charge</th>
      <th>potential_end_discharge</th>
      <th>charge_capacity</th>
      <th>discharge_capacity</th>
      <th>coulombic_efficiency</th>
      <th>cumulated_coulombic_efficiency</th>
      <th>...</th>
      <th>test_cumulated_discharge_capacity_areal</th>
      <th>coulombic_difference_areal</th>
      <th>test_cumulated_coulombic_difference_areal</th>
      <th>discharge_capacity_loss_areal</th>
      <th>charge_capacity_loss_areal</th>
      <th>test_cumulated_discharge_capacity_loss_areal</th>
      <th>test_cumulated_charge_capacity_loss_areal</th>
      <th>shifted_charge_capacity_areal</th>
      <th>shifted_discharge_capacity_areal</th>
      <th>test_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>5797</td>
      <td>1.743286e+05</td>
      <td>2021-05-12 10:40:11.000000</td>
      <td>4.200052</td>
      <td>3.129170</td>
      <td>0.003819</td>
      <td>0.003324</td>
      <td>87.049469</td>
      <td>87.049469</td>
      <td>...</td>
      <td>3.324036</td>
      <td>0.494524</td>
      <td>0.494524</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>0.494524</td>
      <td>4.313083</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>7188</td>
      <td>3.171618e+05</td>
      <td>2021-05-14 02:20:47.000000</td>
      <td>4.200052</td>
      <td>3.188442</td>
      <td>0.003422</td>
      <td>0.003234</td>
      <td>94.510786</td>
      <td>181.560255</td>
      <td>...</td>
      <td>6.558417</td>
      <td>0.187854</td>
      <td>0.682378</td>
      <td>0.089654</td>
      <td>0.396324</td>
      <td>0.089654</td>
      <td>0.396324</td>
      <td>0.682378</td>
      <td>4.104613</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>7218</td>
      <td>3.189618e+05</td>
      <td>2021-05-14 02:50:47.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>6.558417</td>
      <td>0.000000</td>
      <td>0.682378</td>
      <td>3.234381</td>
      <td>3.422235</td>
      <td>3.324036</td>
      <td>3.818560</td>
      <td>0.682378</td>
      <td>0.682378</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4</td>
      <td>34207</td>
      <td>9.954903e+05</td>
      <td>2021-05-22 17:30:55.000000</td>
      <td>4.200052</td>
      <td>2.999878</td>
      <td>0.003331</td>
      <td>0.003288</td>
      <td>98.693739</td>
      <td>280.253993</td>
      <td>...</td>
      <td>9.846100</td>
      <td>0.043514</td>
      <td>0.725892</td>
      <td>-3.287683</td>
      <td>-3.331197</td>
      <td>0.036353</td>
      <td>0.487362</td>
      <td>0.725892</td>
      <td>4.057089</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>5</td>
      <td>60493</td>
      <td>1.508876e+06</td>
      <td>2021-05-27 21:23:41.999999</td>
      <td>4.200052</td>
      <td>2.999878</td>
      <td>0.003358</td>
      <td>0.003392</td>
      <td>101.021637</td>
      <td>381.275630</td>
      <td>...</td>
      <td>13.237949</td>
      <td>-0.034302</td>
      <td>0.691590</td>
      <td>-0.104166</td>
      <td>-0.026350</td>
      <td>-0.067813</td>
      <td>0.461013</td>
      <td>0.691590</td>
      <td>4.049137</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 51 columns</p>
</div>




```python

```
