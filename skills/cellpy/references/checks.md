# Checks before reporting cycling results

Read this after `cellpy.get` returns and before quoting capacities, fade,
or an ICA peak.

## Load

- `c.data.raw`, `c.data.steps`, and `c.data.summary` are non-empty.
- `c.get_cycle_numbers()` is strictly increasing and starts where the file
  starts. Do not renumber cycles to begin at 1 unless the user asked.
- `c.data.mass` is the active mass in mg. The default **1.0 mg** applies
  when neither the file nor `mass=` set it. Gravimetric capacity is then
  not interpretable.
- Instrument `available` was true. For `arbin_res`, a false
  `list_instruments()` row means the Access reader is missing (mdbtools on
  Linux, the Access driver on Windows).

## Which capacity column

| Column | What it is under default units |
| --- | --- |
| `c.schema.summary.charge_capacity` → `charge_capacity` | Absolute charge, mAh |
| `charge_capacity_gravimetric` | Specific charge capacity, mAh/g |
| `charge_capacity_areal` | Areal charge capacity, mAh/cm² |
| `c.schema.summary.coulombic_efficiency` | Coulombic efficiency |

Discharge columns follow the same pattern. Print
`c.cellpy_units.charge` before labeling an axis. Do not divide
`charge_capacity` by mass again; `*_gravimetric` is already specific.
Mass is mg and the gravimetric denominator is g, so a hand-rolled
`mAh / mass_mg` is off by 1000.

On the bundled Arbin example (`example_data.raw_file()`, mass 0.704 mg)
cycle 1 was about 0.00163 mAh absolute and about 2309 mAh/g gravimetric.
Those two numbers describe the same charge.

## Capacity rebase

After a raw load, each cycle's raw capacity starts at 0. A tester that
forgot to reset capacity is rebased on load. A `UserWarning` names the
columns and how many cycles carried over. Include that warning in the
report. Files saved by cellpy 2.1.5 or earlier can still hold the
un-rebased raw. Rebuild them from the original tester file.

## ICA / DVA

- Use `ica.dqdv` / `ica.dvdq` with an explicit `IcaOptions` when smoothing
  or normalization matters.
- Record `voltage_resolution`, `voltage_fwhm`, `post_smoothing`, and
  `normalize`. Default normalization is `"area"`, so peak height is not
  physical dQ/dV.
- Split on `direction` (`"charge"` or `"discharge"`). Cell-centric labels
  are already on the frame. Do not infer electrode polarity from the sign
  of dQ/dV.
- A noisy derivative with the default smoother still on is a smoothing
  choice, not a materials result. Re-run with `post_smoothing=False` before
  describing a shoulder as real.

## Batch

- Missing raw files are `FAILED`, not quietly empty. Read
  `b.result.report()`.
- `mark_as_bad` only flags a cell. `drop` removes it from plots and
  summaries in this session. An unknown name raises `ValueError` on
  `mark_as_bad`.
- `from_cells` takes cells. `example_data.rate_file()` returns a path, not
  a cell.

## What not to claim

- A summary table is not a passed specification.
- One voltage-curve overlay is not a fitted parameter set.
- Coulombic efficiency near 100% on a short file is not evidence of a
  stable cell. Report the cycle window it was computed on.
