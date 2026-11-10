# Issue #1193: Cannot filter summary plot in _life for charge and discharge

Source: https://github.com/jepegit/cellpy/issues/1193

## Original issue text

**Describe the bug**
I plot a summaryplot using collectors in _life (see code below), but cannot filter the plot on charge and discharge. 

* cellpy version: 2.1.5.post8
* Python version: 3.14.9
* Operating System: windows

**To Reproduce**
Steps to reproduce the behavior.

```
Paste the command(s) you ran and the output.
If there was a crash, please include the traceback here.

from cellpy.collect import summary_collector, normalize_column

export_coll = summary_collector(
    b,
    max_cycle=100,
    group_it=True,
    partition_by_cv=False,
    average_method="mean",

    columns=(
        "discharge_capacity_gravimetric",
        "charge_capacity_gravimetric",
        "coulombic_efficiency",
    ),

fig = export_coll.plot(
    width=1000,
    height=900,
    markers=True,
    spread=True,
    order_variables=[
        "coulombic_efficiency",
        "discharge_capacity_gravimetric",
    #    "discharge_capacity_retention_norm",
    ],
)

# Show every cycle number on the x-axis
fig.update_xaxes(
    dtick=1,
    tick0=1
)

fig.show()

```

**Expected behavior**
I can show plots personally. Can filter the different experiments but not charge/discharge. 



**Desktop (please complete the following information):**
 - OS: [e.g. iOS]
 - Version [e.g. 22]

**Additional context**
Add any other context about the problem here.

## Comments (curated summary)

- **Clarifications / constraints**:
  - Direction filter only applies to charge. Selecting both charge and discharge still filters charge only.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @marteosk on 2026-11-05._
