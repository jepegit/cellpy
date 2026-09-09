# Summary columns explained

`c.data.summary` has one row per cycle and — for a plain Arbin file with no
extra options — **58 columns**. This page says what each one means, how it is
computed, and which units it is in.

```python
print(len(c.data.summary.columns))   # 58
```

For the raw and step frames, see
[the data structure](../fundamentals/data_structure.md).

---

## Read this first: the base column is not in your units

Every capacity-like quantity appears in four forms:

| Column | Normalised by | Units |
| --- | --- | --- |
| `charge_capacity` | nothing | **the tester's units** (`c.data.raw_units`) |
| `charge_capacity_absolute` | nothing | your units (`c.cellpy_units`) |
| `charge_capacity_gravimetric` | active mass | your units, per `specific_gravimetric` |
| `charge_capacity_areal` | electrode area | your units, per `specific_areal` |

The three postfixed columns are the base column multiplied by a conversion
factor that includes the raw → cellpy unit change. The **base column does
not** get that conversion.

For an Arbin `.res` file, which records charge in Ah, with the default cellpy
unit of mAh:

```python
c.data.summary["charge_capacity"]            # 0.00163   <- Ah, the tester's unit
c.data.summary["charge_capacity_absolute"]   # 1.63      <- mAh
c.data.summary["charge_capacity_gravimetric"]# 2308.8    <- mAh/g
```

!!! warning "Use `_absolute`, not the bare name, when you want mAh"
    `charge_capacity` and `charge_capacity_absolute` differ by exactly the
    raw → cellpy unit factor. They happen to be equal only when your tester
    already wrote the unit cellpy is configured for. Reaching for the bare name
    and assuming mAh is the easiest way to be off by a factor of 1000.

Check the factor for your cell:

```python
print(c.data.raw_units.charge, "->", c.cellpy_units.charge)
print(c.get_converter_to_specific(mode="absolute"))     # e.g. 1000.0
```

The columns that come in all four forms are:

`charge_capacity`, `discharge_capacity`, `charge_capacity_loss`,
`discharge_capacity_loss`, `coulombic_difference`,
`test_cumulated_charge_capacity`, `test_cumulated_discharge_capacity`,
`test_cumulated_charge_capacity_loss`,
`test_cumulated_discharge_capacity_loss`,
`test_cumulated_coulombic_difference`.

More on the unit machinery: [Units, mass, area and C-rates](../guides/units.md).

---

## Identity

| Column | Meaning |
| --- | --- |
| `cycle_num` | cycle number |
| `test_id` | which test this cycle belongs to (0 for a single, unmerged run) |
| `datapoint_num_last` | index of the last raw point in the cycle |
| `last_test_time` | test time at the end of the cycle |

`test_id` matters for campaign merges: every cumulated column below is
accumulated **within** a test, so a merged object never carries capacity from
one test into the next.

## Capacities

| Column | Meaning |
| --- | --- |
| `charge_capacity` | capacity delivered on charge in this cycle |
| `discharge_capacity` | capacity delivered on discharge in this cycle |
| `test_cumulated_charge_capacity` | running sum of `charge_capacity` |
| `test_cumulated_discharge_capacity` | running sum of `discharge_capacity` |

Each cycle's capacity starts at zero: cellpy rebases the tester's cumulative
column per cycle on load. A tester that forgot a reset used to look like
doubled capacity in cellpy 1.x; you get a `UserWarning` when this rebasing
actually changed values.

## Efficiency and losses

`coulombic_efficiency` and `coulombic_difference` are referenced to the
**first** step of the cycle, so they depend on `cycle_mode`:

| `cycle_mode` | `coulombic_efficiency` | `coulombic_difference` |
| --- | --- | --- |
| `anode` (half cell — starts on discharge) | `100 · charge / discharge` | `discharge − charge` |
| `full_cell` / `cathode` / `normal` | `100 · discharge / charge` | `charge − discharge` |

Get this wrong and your CE is upside down. See
[Troubleshooting](../troubleshooting.md#charge-and-discharge-look-swapped-and-the-coulombic-efficiency-is-upside-down).

| Column | Computed as |
| --- | --- |
| `coulombic_efficiency` | above; a percentage |
| `coulombic_difference` | above |
| `charge_capacity_loss` | `charge_capacity[n−1] − charge_capacity[n]` |
| `discharge_capacity_loss` | `discharge_capacity[n−1] − discharge_capacity[n]` |
| `test_cumulated_coulombic_difference` | running sum of `coulombic_difference` |
| `test_cumulated_charge_capacity_loss` | running sum of `charge_capacity_loss` |
| `test_cumulated_discharge_capacity_loss` | running sum of `discharge_capacity_loss` |
| `cumulated_coulombic_efficiency` | running sum of `coulombic_efficiency` |

The loss columns are per-direction and do **not** depend on `cycle_mode`. The
first cycle's loss is `NaN` — there is no previous cycle.

## Shifted capacities

| Column | Computed as |
| --- | --- |
| `shifted_charge_capacity` | cumulative sum of `charge_capacity − discharge_capacity` |
| `shifted_discharge_capacity` | `shifted_charge_capacity + charge_capacity` |

These offset each cycle's curve by the irreversible capacity accumulated so
far, so that a stack of voltage curves lines up the way the electrode actually
drifted. Handy for silicon and other high-loss electrodes.

## RIC — relative irreversible capacity

Three cumulative ageing indicators, each a running sum over cycles
(`cc` = charge capacity, `dc` = discharge capacity):

| Column | Computed as |
| --- | --- |
| `cumulated_ric` | Σ `(cc[n−1] − dc[n]) / dc[n−1]` |
| `cumulated_ric_sei` | Σ `(cc[n] − dc[n−1]) / dc[n−1]` |
| `cumulated_ric_disconnect` | Σ `(dc[n−1] − dc[n]) / dc[n−1]` |

The split is diagnostic: `_sei` tracks loss consistent with continued
surface-film growth, `_disconnect` tracks loss consistent with material losing
electrical contact, and `cumulated_ric` is the overall figure. They are ratios,
so they carry no unit and get no specific variants.

The first cycle is `NaN` in all three.

## Rate and throughput

| Column | Meaning |
| --- | --- |
| `charge_c_rate` | mean charge current expressed as a C-rate |
| `discharge_c_rate` | mean discharge current expressed as a C-rate |
| `test_cumulated_capacity_throughput` | total charge passed, both directions |
| `equivalent_full_cycles` | `test_cumulated_capacity_throughput / (2 · nominal capacity)` |
| `normalized_cycle_index` | `test_cumulated_charge_capacity / nominal capacity` |

All five need a **nominal capacity** to mean anything:

```python
c = cellpy.get("my_cell.res", mass=0.704, nominal_capacity="3579 mAh/g")
```

Without one, `nom_cap` defaults to 1.0 and these columns come out with
plausible-looking but meaningless values — they are not `NaN`, so nothing warns
you. `equivalent_full_cycles` counts a full charge *and* discharge as one
cycle, which is why the denominator has the factor 2.

## End-of-cycle potentials

| Column | Meaning |
| --- | --- |
| `potential_end_charge` | potential at the end of the charge step |
| `potential_end_discharge` | potential at the end of the discharge step |

Useful as a cheap health check: a drifting end-of-discharge potential often
shows up before capacity fade does.

## Columns you may not see

The schema declares more than the summary engine currently fills in. These are
in `c.schema.summary` but are **not** in a default summary frame:

- per-direction current / potential / power statistics
  (`current_charge_mean`, `potential_discharge_max`, …)
- `cv_share`, `cv_charge_capacity`, `cc_charge_capacity` and the CV/CC split
- `voltage_efficiency`
- `ir_charge` / `ir_discharge` and the four `ir_start_*` / `ir_end_*` columns
- cell-temperature statistics

Always check before you index:

```python
"cv_share" in c.data.summary.columns    # False, for a plain load
```

The CV/non-CV split is available through the plotting families
(`summary_plot(c, y="capacities_gravimetric_split_constant_voltage")`), which
compute it on the way to the figure.

## Listing what you actually have

```python
for name in c.data.summary.columns:
    print(name)
```

and, for the schema-resolved names your code should use:

```python
[a for a in dir(c.schema.summary) if not a.startswith("_")]
```

## See also

- [Units, mass, area and C-rates](../guides/units.md) — the unit and
  normalisation machinery
- [The data structure](../fundamentals/data_structure.md) — the raw and step
  frames
- [Understand the step table](../guides/step_table.md) — where these
  numbers come from
- [Legacy header map](../other/header_migration_map.md) — the 1.x names
- [Troubleshooting](../troubleshooting.md) — when a number looks wrong
