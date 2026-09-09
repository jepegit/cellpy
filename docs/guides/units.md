# Units, mass, area and C-rates

A capacity is only meaningful once you know what it is divided by. This page
covers the three things that decide the numbers cellpy hands back:

1. the **unit policy** (`mAh` or `Ah`? per `g` or per `mg`?),
2. the **cell metadata** you supply (mass, area, nominal capacity),
3. the **normalisation** you read off the summary (gravimetric, areal,
   absolute).

Get these right once and every downstream plot and table is right too.

## The short version

```python
import cellpy

c = cellpy.get(
    "my_cell.res",
    mass=0.704,                     # mg of active material
    area=1.77,                      # cm² of electrode
    nominal_capacity="3579 mAh/g",  # for C-rates and equivalent full cycles
    cycle_mode="anode",             # "full_cell" for a full cell
)

grav = c.data.summary["charge_capacity_gravimetric"]   # mAh/g
areal = c.data.summary["charge_capacity_areal"]        # mAh/cm²
```

## Two sets of units

cellpy keeps the units the *instrument* wrote separately from the units *you*
want to work in.

| | What it is | Where it comes from |
| --- | --- | --- |
| `c.data.raw_units` | the units in the raw frame, as the tester wrote them | set by the loader |
| `c.cellpy_units` | the units cellpy converts to when it builds the summary | your configuration, or `units=` |

```python
print(c.data.raw_units.charge)   # e.g. "Ah"  — what the Arbin file contained
print(c.cellpy_units.charge)     # "mAh"      — what the summary is in
```

You normally never touch `raw_units`; it is the loader's business. Changing
`cellpy_units` is how you change the output.

### The defaults

| Quantity | Field | Default |
| --- | --- | --- |
| current | `current` | `A` |
| charge / capacity | `charge` | `mAh` |
| potential | `voltage` | `V` |
| time | `time` | `sec` |
| energy | `energy` | `Wh` |
| power | `power` | `W` |
| resistance | `resistance` | `ohm` |
| mass | `mass` | `mg` |
| nominal capacity | `nominal_capacity` | `mAh/g` |
| gravimetric denominator | `specific_gravimetric` | `g` |
| areal denominator | `specific_areal` | `cm**2` |
| length / area / volume | `length` / `area` / `volume` | `cm` / `cm**2` / `cm**3` |
| temperature | `temperature` | `C` |
| pressure | `pressure` | `bar` |

So a gravimetric capacity is `charge / specific_gravimetric` = **mAh/g**, and
an areal capacity is `charge / specific_areal` = **mAh/cm²**, out of the box.

The full list, including everything else that lives in the configuration file,
is in the [configuration reference](../getting_started/configuration_reference.md#units).

### Changing units for one load

Pass `units=` to `cellpy.get`. It is applied before the summary is built, so
the summary comes out in the units you asked for:

```python
c = cellpy.get("my_cell.res", mass=0.704, units=dict(charge="Ah"))

c.data.summary["charge_capacity_gravimetric"]   # now Ah/g, not mAh/g
```

Change the denominator the same way — here, capacity per **milligram**:

```python
c = cellpy.get("my_cell.res", mass=0.704, units=dict(specific_gravimetric="mg"))
```

### Changing units on a cell that is already loaded

The summary does not recompute itself. Update the units, then rebuild the
scaled columns:

```python
c.cellpy_units.update(dict(charge="Ah"))
c.refresh_after()          # or c.make_summary() for a full rebuild
```

Without that second line the numbers stay in the old units while
`c.cellpy_units` claims the new one — a quiet way to mislabel a plot.

### Changing units for every load

Put them in your `cellpy.toml` under `[units]`:

```toml
[units]
charge = "Ah"
specific_gravimetric = "mg"
```

See [Setup and configuration](../getting_started/configuration.md) for where
that file lives.

### Writing the unit on a plot label

Do not build the string by hand — the mode is easy to get wrong, and a wrong
label is a silent error rather than a crash:

```python
from cellpy.units import units_label, with_cellpy_unit

units_label("charge", "gravimetric", units=c.cellpy_units)   # "mAh/g"
units_label("charge", "areal", units=c.cellpy_units)         # "mAh/cm**2"
units_label("charge", units=c.cellpy_units)                  # "mAh"

with_cellpy_unit("Capacity", "charge", "gravimetric", units=c.cellpy_units)
# "Capacity (mAh/g)"
```

Pass `units=c.cellpy_units` whenever the label describes a particular cell.
Without it the helpers use the session default, which may not be what that cell
was built with.

## Mass, area and loading

These three are metadata on the cell, and they are what turn a raw capacity
into a specific one.

```python
c = cellpy.get("my_cell.res", mass=0.704, area=1.77)
```

| Argument | Meaning | Unit (default) |
| --- | --- | --- |
| `mass` | active material mass | mg |
| `area` | active electrode area | cm² |
| `loading` | mass per area | mg/cm² |
| `nominal_capacity` | theoretical / rated capacity | mAh/g |

You can attach the unit to the value as a string, which overrides the
configured unit for that one argument:

```python
c = cellpy.get("my_cell.res", mass="0.704 mg", area="1.77 cm**2")
```

!!! warning "The default mass is 1.0 mg"
    If you do not pass `mass=` and the file does not carry one, cellpy uses
    **1.0 mg**. Every gravimetric number is then wrong by the ratio between
    1.0 mg and your real mass — usually by a factor of a few hundred to a few
    thousand, which is easy to spot, but only if you look.

### `loading` instead of `area`

If you know the loading but not the area, give the loading and cellpy derives
the area as `mass / loading`:

```python
c = cellpy.get("my_cell.res", mass=0.704, loading=1.5)
print(c.data.active_electrode_area)   # 0.4693... cm²
```

If you pass both `area` and `loading`, `area` wins. Pass
`estimate_area=False` to switch the derivation off entirely.

### Changing the metadata after loading

Setting the attribute is not enough — the summary has to be rebuilt:

```python
c.mass = 0.704
c.refresh_after("mass")
```

`refresh_after` accepts `"mass"`, `"area"`, `"nominal_capacity"` and
`"cycle_mode"` (and their aliases), or nothing at all to refresh everything
meta-dependent. It only rebuilds the scaled part of the summary, so it is much
cheaper than a full `make_summary()`.

## Which capacity column?

Every capacity-like quantity in the summary exists in several normalisations,
distinguished by a postfix:

| Column | Normalised by | Unit (defaults) |
| --- | --- | --- |
| `charge_capacity` | nothing | mAh |
| `charge_capacity_gravimetric` | `mass` | mAh/g |
| `charge_capacity_areal` | `area` | mAh/cm² |
| `charge_capacity_absolute` | nothing (explicit name) | mAh |

The same postfixes apply to `discharge_capacity`, the `*_loss` columns, the
`coulombic_difference` columns and their `test_cumulated_*` counterparts.

`c.schema.summary` gives you the **base** name only. Build the specific name
from it:

```python
base = c.schema.summary.charge_capacity        # "charge_capacity"
grav = f"{base}_gravimetric"

c.data.summary[grav].head()
```

An areal column is only meaningful if you gave an `area` (or a `loading`);
otherwise the default area of 1.0 cm² makes it numerically identical to the
absolute column.

## Nominal capacity, C-rates and equivalent full cycles

`nominal_capacity` is what cellpy divides the measured current by to get a
C-rate, and what it divides throughput by to get equivalent full cycles. Give
it when you want either of those to mean something:

```python
c = cellpy.get("my_cell.res", mass=0.704, nominal_capacity="3579 mAh/g")

c.data.summary[["cycle_num", "charge_c_rate", "discharge_c_rate"]].head()
c.data.summary["equivalent_full_cycles"].head()
```

```text
   cycle_num  charge_c_rate  discharge_c_rate
0          1        0.06097           0.06041
1          2        0.06097           0.06045
2          3        0.06096           0.06045
```

By default the nominal capacity is read as **gravimetric** (per mass). If yours
is per area — or an absolute cell capacity — say so with `nom_cap_specifics`:

```python
c = cellpy.get("my_cell.res", area=1.77, nominal_capacity=3.0,
               nom_cap_specifics="areal")            # mAh/cm²

c = cellpy.get("my_cell.res", nominal_capacity=2500,
               nom_cap_specifics="absolute")         # mAh for the whole cell
```

!!! note
    Passing `nominal_capacity` as a string with a unit (`"3579 mAh/g"`) also
    sets `cellpy_units["nominal_capacity"]`, and can therefore override a
    `nom_cap_specifics` you gave alongside it. Pass a plain number together
    with `nom_cap_specifics=` when you want the mode to be unambiguous.

## Checklist

Before you trust a specific capacity, check that:

- [ ] `c.data.mass` is your real mass, not 1.0
- [ ] `c.data.active_electrode_area` is your real area, if you use areal columns
- [ ] `c.cycle_mode` matches your cell (`"anode"` vs `"full_cell"`)
- [ ] `c.data.nom_cap` is set, if you read C-rates or equivalent full cycles
- [ ] you rebuilt the summary (`refresh_after`) after changing any of them

## See also

- [Troubleshooting](../troubleshooting.md) — when the numbers still look wrong
- [The data structure](../fundamentals/data_structure.md) — what else is in the
  frames
- [Configuration reference](../getting_started/configuration_reference.md#units)
  — every unit setting and its default
