# Understand the step table

Before cellpy can tell you a charge capacity, it has to decide which parts of
the run *were* a charge. That decision lives in the **step table**, and every
per-cycle number is built on top of it.

Most of the time it is right and you never think about it. When a capacity
looks wrong and the mass is fine, this is the next place to look.

```python
c.data.steps          # one row per step, 64 columns
c.data.steps[c.schema.steps.step_type].value_counts()
```

```text
ir             33
ocvrlx_down    18
discharge      18
ocvrlx_up      17
charge         17
```

## What a row is

One row per (cycle, step, sub-step). The identity columns are:

| Column | Meaning |
| --- | --- |
| `cycle_num` | cycle number |
| `step_num` | the tester's step number within the cycle |
| `sub_step_num` | sub-step, when the tester splits one step |
| `step_type` | what cellpy decided this step is |
| `c_rate` | C-rate estimate for the step |

Everything else is a statistic, named `<quantity>_<stat>`:

```text
current_mean   current_std   current_min   current_max   current_first   current_last
potential_mean potential_std potential_min potential_max potential_first potential_last
charge_capacity_mean  …  charge_capacity_delta
step_time_mean …
```

`_delta` (last − first) is the one the classifier leans on.

## The step types

| `step_type` | Meaning |
| --- | --- |
| `charge` | current positive, charge capacity increasing |
| `discharge` | current negative, discharge capacity increasing |
| `cv_charge` | constant-voltage part of a charge |
| `cv_discharge` | constant-voltage part of a discharge |
| `ocvrlx_up` | open-circuit relaxation, potential rising |
| `ocvrlx_down` | open-circuit relaxation, potential falling |
| `rest` | no current, potential stable |
| `ir` | nothing changed at all — an internal-resistance point |
| `""` (empty) | **uncategorized** — no rule matched |

The schema also defines `taper_charge`, `taper_discharge`, `charge_cv`,
`discharge_cv` and `not_known`. The built-in classifier never emits those; they
only appear if you supply them yourself, or in data written by an older cellpy.

!!! note "Uncategorized is `\"\"`, not `\"not_known\"`"
    A step that matched no rule gets the empty string. Filter for it with
    `c.data.steps[c.schema.steps.step_type] == ""`.

## How cellpy decides

Each step is classified from its own aggregates, against thresholds in
`c.data.raw_limits`. In order — **later rules win**:

| Condition | Label |
| --- | --- |
| no current, potential stable | `rest` |
| no current, potential rose | `ocvrlx_up` |
| no current, potential fell | `ocvrlx_down` |
| discharge capacity changed, current negative | `discharge` |
| charge capacity changed, current positive | `charge` |
| potential stable, current negative and falling | `cv_discharge` |
| potential stable, current positive and falling | `cv_charge` |
| nothing changed at all | `ir` |

"No current", "stable" and "changed" are all threshold questions, because no
instrument reads exactly zero:

```python
print(c.data.raw_limits)
```

```text
CellpyLimits(current_hard=1e-13, current_soft=1e-05,
             stable_current_hard=2.0, stable_current_soft=4.0,
             stable_voltage_hard=2.0, stable_voltage_soft=4.0,
             stable_charge_hard=0.9, stable_charge_soft=5.0,
             ir_change=1e-05)
```

| Limit | Used for |
| --- | --- |
| `current_hard` | below this, the current counts as zero |
| `stable_voltage_hard` | potential change smaller than this counts as stable |
| `stable_current_soft` | current drop larger than this counts as falling (CV) |
| `stable_charge_hard` | capacity change larger than this counts as real |

## Looking at what it decided

The quickest check is visual — raw traces with the step labels drawn on:

```python
from cellpy.utils.plotutils import cycle_info_plot

cycle_info_plot(c, cycle=3)
```

Or count them, and look at the ones that fell through:

```python
sc = c.schema.steps
steps = c.data.steps

print(steps[sc.step_type].value_counts())
steps[steps[sc.step_type] == ""]        # uncategorized
```

To pull out one kind of step:

```python
discharges = c.data.steps.query(f"{c.schema.steps.step_type}=='discharge'")
```

## Fixing a misclassification

Three tools, in increasing order of bluntness.

### 1. Nudge the thresholds

If a whole class of steps is wrong — a low-current cell whose CV tails read as
rests, say — the thresholds are the honest fix:

```python
c.make_step_table(override_raw_limits={"current_hard": 1e-9})
c.make_summary()          # the summary is built on the step table
```

Only the limits you name are overridden; the rest keep their values. Note that
`0` is respected as an override rather than falling back to the default.

### 2. Override individual step numbers

If the tester's step 5 is always a rest but cellpy reads it as a relaxation:

```python
c.make_step_table(override_step_types={5: "rest"})
c.make_summary()
```

The key is the **step number**, and it applies in every cycle.

### 3. Declare the whole schedule

If you know the schedule, you can hand cellpy the answer and skip the
classifier entirely:

```python
import pandas as pd

spec = pd.DataFrame({
    "step": [1, 2, 3],
    "type": ["charge", "rest", "discharge"],
})

c.make_step_table(step_specifications=spec, short=True)
```

!!! warning "Specifications replace the classifier — they do not extend it"
    Any step you do not list ends up **uncategorized** (`""`), not classified
    by the usual rules. On a cell whose steps run 1–8, a three-row
    specification leaves the other five blank, and the summary that follows
    will be missing capacities. List every step you have.

    `short=True` matches by step number alone. Leave it out to match on
    `(cycle, step)` pairs, and add a `cycle` column.

    An optional `info` column is carried through to the step table as free text.

### Always rebuild the summary

`make_step_table` does not touch `c.data.summary`. After any of the three:

```python
c.make_step_table(...)
c.make_summary()
```

## Repeated steps in one cycle — GITT

A GITT cycle has the same tester step number many times over. By default cellpy
collapses them; `usteps=True` keeps them apart and adds a `ustep` column:

```python
c.make_step_table(usteps=True)
c.data.steps["ustep"]
```

See the [GITT tutorial](../examples/05_GITT.md) for the full workflow.

## Other `make_step_table` options

| Argument | Effect |
| --- | --- |
| `add_c_rate` | include the `c_rate` estimate (default `True`) |
| `sort_rows` | sort the resulting rows (default `True`) |
| `from_data_point` | start from this raw data point |
| `nom_cap_specifics` | `"gravimetric"` / `"areal"` / `"absolute"` for the C-rate basis |
| `profiling` | print timings |

## See also

- [Summary columns](../reference/summary_columns.md) — what the step table
  feeds into
- [The data structure](../fundamentals/data_structure.md) — all three frames
- [Plot one cell](plotting.md) — `cycle_info_plot` and the rest
- [GITT](../examples/05_GITT.md) — the main user of `usteps`
