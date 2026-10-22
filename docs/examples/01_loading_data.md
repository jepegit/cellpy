# Loading and saving data

!!! abstract "In this tutorial"

    You will learn how to:

    - load one or several raw files into a cell object with `cellpy.get`
    - look at the summary, step table and metadata
    - save a `.cellpy` file, export to Excel/CSV, and load it again

    **Data:** the bundled example Arbin file (`cellpy.utils.example_data.arbin_file_path`), downloaded automatically.

    [:material-github: Open the notebook on GitHub](https://github.com/jepegit/cellpy/blob/master/examples/01_loading_data.ipynb){ .md-button } — or get every notebook and its data with `cellpy pull --examples`.



```python
import pathlib

import numpy as np
import pandas as pd
from rich import print

import cellpy
from cellpy.utils import example_data

```

    WARNING:root:/home/ubuntu/.cellpy_prms_ubuntu.conf carries instrument credentials (instruments.Arbin.SQL_PWD, instruments.Arbin.SQL_UID); these are ignored — cellpy 2 reads them from the environment only (CELLPY_HOST, CELLPY_KEY_FILENAME, CELLPY_PASSWORD, CELLPY_USER).


    WARNING:root:Configured env_file /agent/repos/cellpy/.env_cellpy resolved to /agent/repos/cellpy/.env_cellpy and was not found. Create that file (or run `cellpy setup`) so those variables can be loaded.


Set the path. The file below is bundled example data: the first call downloads it if you do not already have it. `cellpy.get` also accepts a list of paths when several files belong to the same experiment.



```python
# one raw file (downloaded on first use)
filename = example_data.arbin_file_path()
# several files from the same experiment would be a list of paths
filepaths = [filename]

```

## Loading data

Use `cellpy.get()` to load the rawdatafile(s):


```python
c = cellpy.get(filepaths, mass=1.2, cycle_mode="full_cell")
```

**Note:** Without any further specifications, ``cellpy.get()`` will use the standard instrument loader as defined in your config file (here the one for loading arbin .res files). For loading different data formats, have a look at [Loading different formats](06_loading_different_formats.md) or [Custom loaders](07_custom_loaders.md).

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
      <td>1457</td>
      <td>168686.229691</td>
      <td>0.001625</td>
      <td>0.001755</td>
      <td>107.978778</td>
      <td>-0.000130</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>1.755094</td>
      <td>1.625406</td>
      <td>1.625406</td>
      <td>1.755094</td>
      <td>-0.129688</td>
      <td>-0.129688</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2</td>
      <td>2283</td>
      <td>248276.169907</td>
      <td>0.001700</td>
      <td>0.001567</td>
      <td>92.228088</td>
      <td>0.000132</td>
      <td>-0.000074</td>
      <td>0.000188</td>
      <td>...</td>
      <td>1.567475</td>
      <td>1.699564</td>
      <td>3.324970</td>
      <td>3.322569</td>
      <td>0.132089</td>
      <td>0.002401</td>
      <td>0.187618</td>
      <td>-0.074158</td>
      <td>0.187618</td>
      <td>-0.074158</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>3</td>
      <td>3119</td>
      <td>329048.542626</td>
      <td>0.001732</td>
      <td>0.001586</td>
      <td>91.580350</td>
      <td>0.000146</td>
      <td>-0.000032</td>
      <td>-0.000018</td>
      <td>...</td>
      <td>1.585721</td>
      <td>1.731508</td>
      <td>5.056478</td>
      <td>4.908290</td>
      <td>0.145787</td>
      <td>0.148188</td>
      <td>-0.018246</td>
      <td>-0.031944</td>
      <td>0.169373</td>
      <td>-0.106102</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>4</td>
      <td>3635</td>
      <td>367369.238502</td>
      <td>0.001576</td>
      <td>0.001517</td>
      <td>96.277888</td>
      <td>0.000059</td>
      <td>0.000156</td>
      <td>0.000068</td>
      <td>...</td>
      <td>1.517318</td>
      <td>1.575978</td>
      <td>6.632455</td>
      <td>6.425608</td>
      <td>0.058660</td>
      <td>0.206848</td>
      <td>0.068403</td>
      <td>0.155530</td>
      <td>0.237776</td>
      <td>0.049428</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>5</td>
      <td>4133</td>
      <td>404665.961044</td>
      <td>0.001535</td>
      <td>0.001471</td>
      <td>95.823815</td>
      <td>0.000064</td>
      <td>0.000041</td>
      <td>0.000046</td>
      <td>...</td>
      <td>1.471186</td>
      <td>1.535303</td>
      <td>8.167758</td>
      <td>7.896794</td>
      <td>0.064117</td>
      <td>0.270965</td>
      <td>0.046132</td>
      <td>0.040674</td>
      <td>0.283907</td>
      <td>0.090103</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 60 columns</p>
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
      <td>144.5</td>
      <td>83.282651</td>
      <td>1</td>
      <td>288</td>
      <td>1</td>
      <td>288</td>
      <td>...</td>
      <td>2.869900e+04</td>
      <td>0.000000</td>
      <td>-6.729598</td>
      <td>0.0</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>ocvrlx_down</td>
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
      <td>289.0</td>
      <td>NaN</td>
      <td>289</td>
      <td>289</td>
      <td>289</td>
      <td>289</td>
      <td>...</td>
      <td>0.000000e+00</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>ir</td>
      <td>NaN</td>
      <td></td>
      <td>0.55241</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>1</td>
      <td>3</td>
      <td>1</td>
      <td>662.0</td>
      <td>215.207264</td>
      <td>290</td>
      <td>1034</td>
      <td>290</td>
      <td>1034</td>
      <td>...</td>
      <td>2.590092e+08</td>
      <td>-2.856309</td>
      <td>-98.243109</td>
      <td>0.0</td>
      <td>5.580068e+08</td>
      <td>0.0</td>
      <td>discharge</td>
      <td>NaN</td>
      <td></td>
      <td>126.84280</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>1</td>
      <td>4</td>
      <td>1</td>
      <td>1035.0</td>
      <td>NaN</td>
      <td>1035</td>
      <td>1035</td>
      <td>1035</td>
      <td>1035</td>
      <td>...</td>
      <td>0.000000e+00</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>ir</td>
      <td>NaN</td>
      <td></td>
      <td>0.03637</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>1</td>
      <td>5</td>
      <td>1</td>
      <td>1051.5</td>
      <td>9.380832</td>
      <td>1036</td>
      <td>1067</td>
      <td>1036</td>
      <td>1067</td>
      <td>...</td>
      <td>4.612496e+04</td>
      <td>0.000000</td>
      <td>37.161767</td>
      <td>0.0</td>
      <td>0.000000e+00</td>
      <td>0.0</td>
      <td>ocvrlx_up</td>
      <td>NaN</td>
      <td></td>
      <td>0.00000</td>
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
      <th>cumulative_charge_capacity</th>
      <th>cumulative_charge_energy</th>
      <th>current</th>
      <th>cycle_num</th>
      <th>datapoint_num</th>
      <th>cumulative_discharge_capacity</th>
      <th>cumulative_discharge_energy</th>
      <th>internal_resistance</th>
      <th>step_num</th>
      <th>step_time</th>
      <th>test_time</th>
      <th>potential</th>
      <th>aci_phase_angle</th>
      <th>ac_impedance</th>
      <th>date_time</th>
      <th>is_fc_data</th>
      <th>dv_dt</th>
      <th>epoch_time_utc</th>
      <th>test_id</th>
      <th>mask</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>300.010482</td>
      <td>300.010482</td>
      <td>3.097617</td>
      <td>0</td>
      <td>0</td>
      <td>2016-08-05 16:21:23</td>
      <td>0</td>
      <td>-0.000123</td>
      <td>1470414083000000000</td>
      <td>0</td>
      <td>True</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>2</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>600.014947</td>
      <td>600.014947</td>
      <td>3.100080</td>
      <td>0</td>
      <td>0</td>
      <td>2016-08-05 16:26:23</td>
      <td>0</td>
      <td>-0.000062</td>
      <td>1470414383000000000</td>
      <td>0</td>
      <td>True</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>3</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>900.026371</td>
      <td>900.026371</td>
      <td>3.101312</td>
      <td>0</td>
      <td>0</td>
      <td>2016-08-05 16:31:23</td>
      <td>0</td>
      <td>-0.000123</td>
      <td>1470414683000000000</td>
      <td>0</td>
      <td>True</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>4</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>1200.039773</td>
      <td>1200.039773</td>
      <td>3.102852</td>
      <td>0</td>
      <td>0</td>
      <td>2016-08-05 16:36:23</td>
      <td>0</td>
      <td>0.000062</td>
      <td>1470414983000000000</td>
      <td>0</td>
      <td>True</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>5</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1</td>
      <td>1500.051275</td>
      <td>1500.051275</td>
      <td>3.103160</td>
      <td>0</td>
      <td>0</td>
      <td>2016-08-05 16:41:23</td>
      <td>0</td>
      <td>0.000000</td>
      <td>1470415283000000000</td>
      <td>0</td>
      <td>True</td>
    </tr>
  </tbody>
</table>
</div>



### Metadata

Cellpy fills in some standard values for meta-data for you (based on your config-file), these can be updated and adjusted.

E.g., we can set a new cell name and add a value active electrode area:


```python
c.active_electrode_area = 1.767
c.cell_name = "example"

```

!!! note
    If you change variables that are used in calculating summary values
    (`cycle_mode`, `mass`, `active_electrode_area`), refresh the scaled
    columns. Prefer `c.refresh_after("mass")` (or `"area"` / `"cycle_mode"`)
    when a summary already exists. `c.make_summary()` rebuilds the whole
    table and is the fallback.

    Use `cycle_mode="full_cell"` (underscore). `"full-cell"` is not a
    recognised spelling — cellpy falls back to the default half-cell
    convention and logs a warning.


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

You can easily save all of this in the native `.cellpy` format:


```python
out = pathlib.Path("out")
out.mkdir(exist_ok=True)
c.save(out / "example.cellpy")

```

or export to csv or excel


```python
c.to_csv(out, sep=";", raw=True)

```


```python
c.to_excel(out / "example.xlsx")

```

## Loading saved files

To load saved files, you can use the `cellpy.get()` function again:


```python
c = cellpy.get(out / "example.cellpy")

```


```python
c.data.summary.head()
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
      <td>1457</td>
      <td>168686.229691</td>
      <td>0.001625</td>
      <td>0.001755</td>
      <td>107.978778</td>
      <td>-0.000130</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>...</td>
      <td>1.755094</td>
      <td>1.625406</td>
      <td>1.625406</td>
      <td>1.755094</td>
      <td>-0.129688</td>
      <td>-0.129688</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2</td>
      <td>2283</td>
      <td>248276.169907</td>
      <td>0.001700</td>
      <td>0.001567</td>
      <td>92.228088</td>
      <td>0.000132</td>
      <td>-0.000074</td>
      <td>0.000188</td>
      <td>...</td>
      <td>1.567475</td>
      <td>1.699564</td>
      <td>3.324970</td>
      <td>3.322569</td>
      <td>0.132089</td>
      <td>0.002401</td>
      <td>0.187618</td>
      <td>-0.074158</td>
      <td>0.187618</td>
      <td>-0.074158</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>3</td>
      <td>3119</td>
      <td>329048.542626</td>
      <td>0.001732</td>
      <td>0.001586</td>
      <td>91.580350</td>
      <td>0.000146</td>
      <td>-0.000032</td>
      <td>-0.000018</td>
      <td>...</td>
      <td>1.585721</td>
      <td>1.731508</td>
      <td>5.056478</td>
      <td>4.908290</td>
      <td>0.145787</td>
      <td>0.148188</td>
      <td>-0.018246</td>
      <td>-0.031944</td>
      <td>0.169373</td>
      <td>-0.106102</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>4</td>
      <td>3635</td>
      <td>367369.238502</td>
      <td>0.001576</td>
      <td>0.001517</td>
      <td>96.277888</td>
      <td>0.000059</td>
      <td>0.000156</td>
      <td>0.000068</td>
      <td>...</td>
      <td>1.517318</td>
      <td>1.575978</td>
      <td>6.632455</td>
      <td>6.425608</td>
      <td>0.058660</td>
      <td>0.206848</td>
      <td>0.068403</td>
      <td>0.155530</td>
      <td>0.237776</td>
      <td>0.049428</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>5</td>
      <td>4133</td>
      <td>404665.961044</td>
      <td>0.001535</td>
      <td>0.001471</td>
      <td>95.823815</td>
      <td>0.000064</td>
      <td>0.000041</td>
      <td>0.000046</td>
      <td>...</td>
      <td>1.471186</td>
      <td>1.535303</td>
      <td>8.167758</td>
      <td>7.896794</td>
      <td>0.064117</td>
      <td>0.270965</td>
      <td>0.046132</td>
      <td>0.040674</td>
      <td>0.283907</td>
      <td>0.090103</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 60 columns</p>
</div>




```python

```
