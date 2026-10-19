---
name: cellpy
description: >-
  Loads battery-tester cycling files with cellpy into raw, step, and summary
  tables, and computes capacity retention, coulombic efficiency, incremental
  capacity (dQ/dV), and differential voltage (dV/dQ). Use when the user has
  Arbin, Maccor, Neware, Biologics, PEC, or .cellpy files, or asks for cycle
  life, capacity fade, coulombic efficiency, ICA, DVA, or a measured
  voltage curve to compare with a PyBaMM simulation.
license: MIT
compatibility: >-
  Requires Python 3.13+ with cellpy installed. Arbin .res on Linux needs
  mdbtools. Network is needed only to download example fixtures. No API key.
metadata:
  version: "1.0"
  skill-author: Jan Petter Maehlen
  upstream-version: "2.1"
  last-reviewed: "2026-10-16"
---

# cellpy cycling data

## When to use

Use this skill to read measured battery cycling data and report cycle-level
quantities. Electrochemical simulation (SPM, DFN, C-rate protocols as a
model) belongs to the PyBaMM skill. This skill can export a measured curve
for that comparison. It does not control a cycler and it does not decide
whether a cell passed a specification.

## Runtime

Use the cellpy the researcher already installed. This skill analyzes their
cycling files. It does not build or test the cellpy source tree.

```bash
python -c "import cellpy; print(cellpy.__version__)"
```

If that import fails:

```bash
pip install cellpy
```

`conda install -c conda-forge cellpy` is the same install from conda-forge.
The worked example was checked on cellpy 2.1. If the installed version is
older than 2.1, stop and say so. Do not upgrade their environment unless
they ask.

Smoke path when the user has no file yet (first call may download a small
Arbin fixture):

```python
from cellpy.utils import example_data

c = example_data.raw_file()
```

That run produced 18 cycles, a non-empty summary, and an ICA frame with
columns `cycle`, `direction`, `voltage`, `capacity`, `dqdv`.

## Workflow

1. Pick the loader. Call `cellpy.list_instruments()` and use an `id` whose
   `available` is true. For raw `.h5` or `.hdf5`, a set `instrument=` wins
   over the suffix guess. Common ids: `arbin_res`, `arbin_sql`,
   `maccor_txt`, `neware_txt`, `neware_xlsx`, `biologics_mpr`, `pec_csv`.
   If `available` is false, stop and report `reason` (often missing
   mdbtools).
2. Get active-material mass before reporting any specific capacity. Pass
   `mass` in milligrams (`0.704` or `"0.704 mg"`). Area is cm². Nominal
   capacity is mAh/g unless the user attaches a unit string. If the file
   and the user both omit mass, cellpy uses **1.0 mg** and every
   gravimetric number is wrong. Say so and ask for the mass. Do not invent
   one.
3. Load. Write derived files under an output directory. Leave the raw file
   unchanged.

   ```python
   import cellpy

   c = cellpy.get(
       "data/my_cell.res",
       mass=0.704,
       instrument="arbin_res",
   )
   c.save("output/my_cell.cellpy")
   ```

4. Read columns through `c.schema`. `c.schema.summary.charge_capacity` is
   the absolute charge column (`charge_capacity`, default unit mAh). The
   specific capacity is the separate column `charge_capacity_gravimetric`
   (default mAh/g). On the example cell those were about 0.0016 mAh and
   2309 mAh/g. Label the column you actually used. Confirm
   `c.cellpy_units.charge` and `c.data.mass` before quoting a unit.
5. Check the summary before interpreting fade. Follow
   [references/checks.md](references/checks.md). A `UserWarning` about
   capacity carry-over means a forgotten tester reset was rebased on load.
   Quote that warning. `.cellpy` files written by cellpy 2.1.5 or earlier
   keep the un-rebased raw; regenerate them from the raw file.
6. For ICA or DVA, use `cellpy.ica`. Do not call the removed 1.x helpers
   (`Converter`, `dqdv_cycle`, `dqdv_cycles`, `dqdv_np`).

   ```python
   from cellpy import ica

   opts = ica.IcaOptions(voltage_resolution=0.005, voltage_fwhm=0.015)
   frame = ica.dqdv(c, cycles=[1, 2], options=opts)
   charge = frame[frame.direction == "charge"]
   ```

   `IcaOptions` is frozen. Change a recipe with `opts.replace(...)`.
   Default `post_smoothing` is on and `normalize` is `"area"`, so a plotted
   peak height is not a raw dQ/dV unless you set `normalize=False` and
   `post_smoothing=False`. Say which recipe you used.
7. For many cells, prefer one batch over a hand-rolled loop.

   ```python
   from cellpy import batch

   b = batch.load(name="my_experiment", project="my_project")
   cell = b.cells["my_cell_01"]
   ```

   An existing `cellpy_batch_<name>.json` in the working directory is
   reused and the database is not re-read. Pass `allow_from_journal=False`
   to rebuild. Cells whose raw file was missing are `FAILED`; read
   `b.result.report()`. `executor="threads"` helps when reopening local
   `.cellpy` files. The first remote raw load stays serial on the wire.

## Measured curve for PyBaMM

Export seconds, volts, and amps. Convert from `c.data.raw_units` when those
are not already `sec`, `V`, and `A`. Keep the tester's current sign and
state it. The PyBaMM skill treats positive simulation current as discharge.
Do not flip the measured current to match that convention without saying so.

```python
raw = c.data.raw
curve = raw[
    [c.schema.raw.test_time, c.schema.raw.potential, c.schema.raw.current]
].rename(
    columns={
        c.schema.raw.test_time: "time_s",
        c.schema.raw.potential: "voltage_V",
        c.schema.raw.current: "current_A",
    }
)
curve.to_csv("output/measured.csv", index=False)
```

A small voltage residual does not identify kinetic parameters. Compare
curves only after current, time origin, temperature, and capacity basis
match.

## Report

State the file, instrument id, cellpy version, mass (mg), and the summary
columns with units. Include cycle count, first and last discharge specific
capacity, and coulombic efficiency when those columns exist. Quote warnings.
If mass was the 1.0 mg default, withhold gravimetric claims.
