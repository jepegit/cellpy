# BatMo BDF files

!!! abstract "In this tutorial"

    You will learn how to:

    - load a BatMo BDF CSV file with the `batmo_bdf` loader
    - inspect it, plot voltage–capacity curves and export it

    **Data:** `batmo_bdf.csv` from the cellpy test data (`cellpy pull --tests`).

    [:material-github: Open the notebook on GitHub](https://github.com/jepegit/cellpy/blob/master/examples/08_batmo_bdf.ipynb){ .md-button } — or get every notebook and its data with `cellpy pull --examples`.


This notebook shows how to load a BatMo BDF CSV file with the built-in `batmo_bdf` loader, inspect the resulting cellpy data object, extract useful pandas DataFrames, make a simple voltage-capacity plot, and export the processed data to other formats.


```python
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import cellpy

%matplotlib inline
```

## Locate the example file

The notebook first looks for `batmo_bdf.csv` in `examples/data`. In a source checkout, the same test file is also available in `testdata/data`.


```python
candidates = [
    Path("data/batmo_bdf.csv"),
    Path("examples/data/batmo_bdf.csv"),
    Path("../testdata/data/batmo_bdf.csv"),
    Path("testdata/data/batmo_bdf.csv"),
]

raw_file = next((path for path in candidates if path.exists()), None)
if raw_file is None:
    raise FileNotFoundError("Could not find batmo_bdf.csv in examples/data or testdata/data")

raw_file
```




    PosixPath('../testdata/data/batmo_bdf.csv')



## Load with the BatMo loader

BatMo BDF CSV files are loaded by passing `instrument="batmo_bdf"`. The example data starts with a discharge step, so `cycle_mode="anode"` is used here.


```python
c = cellpy.get(
    raw_file,
    instrument="batmo_bdf",
    cycle_mode="anode",
    mass=1.0,
)

c
```

    (cellpy) - parsing with pandas.read_csv: /tmp/batmo_bdf.csv
    (cellpy) - parameters: self.sep=',', self.skiprows=0, self.header=0, self.encoding='utf-8', self.decimal='.'
    (cellpy) - running post-processor: rename_headers
    (cellpy) - running post-processor: cumulate_capacity_within_cycle
    (cellpy) - running post-processor: set_index





    <CellpyCell> (id=0x7f5910928ce0) [name=batmo_bdf]



## Inspect the processed data

After loading, `cellpy` has generated the raw data table, the step table, and the summary table.


```python
raw = c.data.raw
steps = c.data.steps
summary = c.data.summary

print(f"Raw points: {len(raw):,}")
print(f"Cycles: {len(c.get_cycle_numbers())}")
print(f"Step types: {steps[c.schema.steps.step_type].value_counts().to_dict()}")

```

    Raw points: 21,206
    Cycles: 109
    Step types: {'rest': 117, 'discharge': 110, 'charge': 109, 'ocvrlx_up': 109}



```python
r = c.schema.raw
raw[[
    r.datapoint_num,
    r.test_time,
    r.step_time,
    r.current,
    r.potential,
    r.step_num,
    r.cycle_num,
    r.cumulative_charge_capacity,
    r.cumulative_discharge_capacity,
]].head()

```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>data_point</th>
      <th>test_time</th>
      <th>step_time</th>
      <th>current</th>
      <th>voltage</th>
      <th>step_index</th>
      <th>cycle_index</th>
      <th>charge_capacity</th>
      <th>discharge_capacity</th>
    </tr>
    <tr>
      <th>data_point</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>500.0</td>
      <td>0.0</td>
      <td>-0.006055</td>
      <td>3.311215</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2</td>
      <td>1000.0</td>
      <td>500.0</td>
      <td>-0.006055</td>
      <td>3.310550</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.000841</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3</td>
      <td>1500.0</td>
      <td>1000.0</td>
      <td>-0.006055</td>
      <td>3.309933</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.001682</td>
    </tr>
    <tr>
      <th>4</th>
      <td>4</td>
      <td>2000.0</td>
      <td>1500.0</td>
      <td>-0.006055</td>
      <td>3.309573</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.002523</td>
    </tr>
    <tr>
      <th>5</th>
      <td>5</td>
      <td>2500.0</td>
      <td>2000.0</td>
      <td>-0.006055</td>
      <td>3.309229</td>
      <td>1</td>
      <td>1</td>
      <td>0.0</td>
      <td>0.003364</td>
    </tr>
  </tbody>
</table>
</div>




```python
st = c.schema.steps
steps[[
    st.cycle_num,
    st.step_num,
    st.step_type,
    st.datapoint_num_first,
    st.datapoint_num_last,
    st.potential_first,
    st.potential_last,
]].head(10)

```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>cycle</th>
      <th>step</th>
      <th>type</th>
      <th>point_min</th>
      <th>point_max</th>
      <th>voltage_first</th>
      <th>voltage_last</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>1</td>
      <td>discharge</td>
      <td>1</td>
      <td>140</td>
      <td>3.311215</td>
      <td>2.596938</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>2</td>
      <td>rest</td>
      <td>141</td>
      <td>156</td>
      <td>2.754796</td>
      <td>2.780684</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>3</td>
      <td>charge</td>
      <td>157</td>
      <td>346</td>
      <td>2.818439</td>
      <td>3.595000</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>4</td>
      <td>rest</td>
      <td>347</td>
      <td>362</td>
      <td>3.581786</td>
      <td>3.581428</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1</td>
      <td>5</td>
      <td>discharge</td>
      <td>363</td>
      <td>553</td>
      <td>3.565638</td>
      <td>2.363354</td>
    </tr>
    <tr>
      <th>5</th>
      <td>2</td>
      <td>6</td>
      <td>ocvrlx_up</td>
      <td>554</td>
      <td>568</td>
      <td>2.471637</td>
      <td>2.561520</td>
    </tr>
    <tr>
      <th>6</th>
      <td>2</td>
      <td>7</td>
      <td>charge</td>
      <td>569</td>
      <td>725</td>
      <td>2.984307</td>
      <td>3.581278</td>
    </tr>
    <tr>
      <th>7</th>
      <td>2</td>
      <td>8</td>
      <td>rest</td>
      <td>726</td>
      <td>741</td>
      <td>3.470661</td>
      <td>3.450568</td>
    </tr>
    <tr>
      <th>8</th>
      <td>2</td>
      <td>9</td>
      <td>discharge</td>
      <td>742</td>
      <td>888</td>
      <td>3.336315</td>
      <td>2.619608</td>
    </tr>
    <tr>
      <th>9</th>
      <td>2</td>
      <td>10</td>
      <td>ocvrlx_up</td>
      <td>889</td>
      <td>905</td>
      <td>2.896960</td>
      <td>3.041850</td>
    </tr>
  </tbody>
</table>
</div>




```python
summary.head()
```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>data_point</th>
      <th>test_time</th>
      <th>date_time</th>
      <th>end_voltage_charge</th>
      <th>end_voltage_discharge</th>
      <th>charge_capacity</th>
      <th>discharge_capacity</th>
      <th>coulombic_efficiency</th>
      <th>cumulated_coulombic_efficiency</th>
      <th>cumulated_charge_capacity</th>
      <th>...</th>
      <th>cumulated_charge_capacity_absolute</th>
      <th>cumulated_discharge_capacity_absolute</th>
      <th>coulombic_difference_absolute</th>
      <th>cumulated_coulombic_difference_absolute</th>
      <th>discharge_capacity_loss_absolute</th>
      <th>charge_capacity_loss_absolute</th>
      <th>cumulated_discharge_capacity_loss_absolute</th>
      <th>cumulated_charge_capacity_loss_absolute</th>
      <th>shifted_charge_capacity_absolute</th>
      <th>shifted_discharge_capacity_absolute</th>
    </tr>
    <tr>
      <th>cycle_index</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1</th>
      <td>553</td>
      <td>262420.0</td>
      <td>1970-01-04 00:53:40</td>
      <td>3.595000</td>
      <td>2.363354</td>
      <td>0.158948</td>
      <td>0.276687</td>
      <td>57.446809</td>
      <td>57.446809</td>
      <td>0.158948</td>
      <td>...</td>
      <td>158.947898</td>
      <td>276.687081</td>
      <td>117.739184</td>
      <td>117.739184</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>117.739184</td>
      <td>394.426265</td>
    </tr>
    <tr>
      <th>2</th>
      <td>905</td>
      <td>283300.0</td>
      <td>1970-01-04 06:41:40</td>
      <td>3.581278</td>
      <td>2.619608</td>
      <td>0.155163</td>
      <td>0.146838</td>
      <td>105.670103</td>
      <td>163.116912</td>
      <td>0.314111</td>
      <td>...</td>
      <td>314.111322</td>
      <td>423.524663</td>
      <td>-8.325842</td>
      <td>109.413341</td>
      <td>129.849500</td>
      <td>3.784474</td>
      <td>129.849500</td>
      <td>3.784474</td>
      <td>109.413341</td>
      <td>256.250923</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1248</td>
      <td>303820.0</td>
      <td>1970-01-04 12:23:40</td>
      <td>3.582400</td>
      <td>2.588512</td>
      <td>0.147342</td>
      <td>0.147847</td>
      <td>99.658703</td>
      <td>262.775615</td>
      <td>0.461453</td>
      <td>...</td>
      <td>461.453500</td>
      <td>571.371438</td>
      <td>0.504597</td>
      <td>109.917938</td>
      <td>-1.009193</td>
      <td>7.821246</td>
      <td>128.840307</td>
      <td>11.605720</td>
      <td>109.917938</td>
      <td>257.764712</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1593</td>
      <td>324460.0</td>
      <td>1970-01-04 18:07:40</td>
      <td>3.587022</td>
      <td>2.534302</td>
      <td>0.148351</td>
      <td>0.148856</td>
      <td>99.661017</td>
      <td>362.436632</td>
      <td>0.609805</td>
      <td>...</td>
      <td>609.804871</td>
      <td>720.227405</td>
      <td>0.504597</td>
      <td>110.422534</td>
      <td>-1.009193</td>
      <td>-1.009193</td>
      <td>127.831114</td>
      <td>10.596527</td>
      <td>110.422534</td>
      <td>259.278502</td>
    </tr>
    <tr>
      <th>5</th>
      <td>1939</td>
      <td>345220.0</td>
      <td>1970-01-04 23:53:40</td>
      <td>3.593878</td>
      <td>2.607985</td>
      <td>0.149361</td>
      <td>0.149361</td>
      <td>100.000000</td>
      <td>462.436632</td>
      <td>0.759165</td>
      <td>...</td>
      <td>759.165435</td>
      <td>869.587970</td>
      <td>0.000000</td>
      <td>110.422534</td>
      <td>-0.504597</td>
      <td>-1.009193</td>
      <td>127.326517</td>
      <td>9.587334</td>
      <td>110.422534</td>
      <td>259.783098</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 61 columns</p>
</div>



## Make a quick raw-data plot

The raw table is a normal pandas DataFrame, so you can use pandas, matplotlib, seaborn, plotly, or the cellpy plotting helpers.


```python
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(raw[c.schema.raw.test_time] / 3600, raw[c.schema.raw.potential], lw=0.8)
ax.set_xlabel("Test time / h")
ax.set_ylabel("Voltage / V")
ax.set_title("BatMo BDF raw voltage trace")
ax.grid(alpha=0.25);

```


    
![png](08_batmo_bdf_files/08_batmo_bdf_12_0.png)
    


## Extract voltage-capacity curves

`get_cap()` returns tidy pandas DataFrames that are convenient for plotting or further analysis. Here `mode="absolute"` keeps the capacities in absolute units.


```python
cycles = [6, 10]
curve = c.get_cap(
    cycles=cycles,
    method="forth-and-forth",
    categorical_column=True,
    label_cycle_number=True,
    mode="absolute",
)

curve.head()
```




<div class="cellpy-dataframe">
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>cycle</th>
      <th>voltage</th>
      <th>capacity</th>
      <th>direction</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2735</th>
      <td>10</td>
      <td>3.226422</td>
      <td>0.000000</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>2736</th>
      <td>10</td>
      <td>3.213438</td>
      <td>2.018386</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>2737</th>
      <td>10</td>
      <td>3.209859</td>
      <td>4.036772</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>2738</th>
      <td>10</td>
      <td>3.206538</td>
      <td>6.055158</td>
      <td>-1</td>
    </tr>
    <tr>
      <th>2739</th>
      <td>10</td>
      <td>3.203454</td>
      <td>8.073544</td>
      <td>-1</td>
    </tr>
  </tbody>
</table>
</div>




```python
fig, ax = plt.subplots(figsize=(7, 5))

for (cycle, direction), frame in curve.groupby(["cycle_num", "direction"]):
    label = f"cycle {cycle} {'charge' if direction > 0 else 'discharge'}"
    ax.plot(frame["capacity"], frame["potential"], label=label, lw=1.2)

ax.set_xlabel("Capacity / mAh")
ax.set_ylabel("Voltage / V")
ax.set_title("Selected BatMo voltage-capacity curves")
ax.legend(fontsize=8)
ax.grid(alpha=0.25);

```


    
![png](08_batmo_bdf_files/08_batmo_bdf_15_0.png)
    


## Export to other formats

The processed cellpy object can be saved as a cellpy HDF5 file and exported to CSV or Excel. The CSV export below keeps the output compact by exporting summary and cycle data only.


```python
out_dir = Path("out/batmo_bdf")
csv_dir = out_dir / "csv"
csv_dir.mkdir(parents=True, exist_ok=True)

cellpy_file = out_dir / "batmo_bdf.cellpy"
excel_file = out_dir / "batmo_bdf.xlsx"

c.save(cellpy_file)
c.to_csv(datadir=csv_dir, raw=False, summary=True, cycles=True, last_cycle=5)
c.to_excel(excel_file, cycles=[1, 2, 10], raw=False)

sorted(path.name for path in out_dir.iterdir())
```

    <ApiModule 'cellpy.readers.externals'>





    ['batmo_bdf.cellpy', 'batmo_bdf.xlsx', 'csv']



## Reload the saved cellpy file

Once saved as a cellpy file, loading is faster and does not require specifying the BatMo raw-data loader again.


```python
c2 = cellpy.get(cellpy_file)

print(f"Reloaded raw points: {len(c2.data.raw):,}")
print(f"Reloaded cycles: {len(c2.get_cycle_numbers())}")
```

    Reloaded raw points: 21,206
    Reloaded cycles: 109



```python

```
