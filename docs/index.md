---
hide:
  - navigation
---

<img src="_static/cellpy-icon-long.svg" alt="cellpy logo" style="width: 320px; max-width: 70%; height: auto;">

# cellpy { .cellpy-visually-hidden }

*A library for analysing data from battery and cell cycling tests.*

[![cellpy package](https://img.shields.io/pypi/v/cellpy.svg)](https://pypi.python.org/pypi/cellpy)
[![Documentation Status](https://readthedocs.org/projects/cellpy/badge/?version=latest)](https://cellpy.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://pepy.tech/badge/cellpy)](https://pepy.tech/project/cellpy)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.06236/status.svg)](https://doi.org/10.21105/joss.06236)

**cellpy** reads data from battery cycling instruments and turns it into one
consistent format. It also calculates the derived quantities for you
(capacities, coulombic efficiencies, incremental capacity), so you don't have
to write that bookkeeping yourself.

=== "Try it now"

    ```python
    import cellpy
    from cellpy.utils import example_data

    c = example_data.raw_file()  # a small Arbin file, downloaded once
    c.data.summary["charge_capacity_gravimetric"]  # mAh/g, one row per cycle
    ```

=== "With your own file"

    ```python
    import cellpy

    c = cellpy.get("my_cell.res", instrument="arbin_res", mass=0.85)  # mass in mg
    c.data.summary["charge_capacity_gravimetric"]  # mAh/g, one row per cycle
    ```

## Where to start

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **New to cellpy?**

    ---

    Install it and take a guided tour on data that ships with cellpy: load,
    plot and export a cell, then do the same with your own file.

    [:octicons-arrow-right-24: Your first hour](getting_started/first_hour.md)

-   :material-file-upload:{ .lg .middle } **Have data to load?**

    ---

    Worked examples from a single file to a whole batch, and one page for each
    of the other instruments.

    [:octicons-arrow-right-24: Tutorials](examples/index.md)

-   :material-help-circle:{ .lg .middle } **Know what you want to do?**

    ---

    One page of tasks phrased as questions ("how do I get areal capacity?"),
    each with a short answer.

    [:octicons-arrow-right-24: How do I…?](how_do_i.md)

-   :material-alert-circle:{ .lg .middle } **Something not working?**

    ---

    A file won't load, or a number looks wrong: fixes listed by symptom and
    error message.

    [:octicons-arrow-right-24: Troubleshooting](troubleshooting.md)

</div>

You can also look up [what the frames and columns mean](fundamentals/index.md)
or the [API reference](api/index.md), or
[use cellpy from an AI agent](agents/index.md).

## Supported instruments

| Tester | `instrument=` |
| --- | --- |
| Arbin | `arbin_res` (`.res`), `arbin_sql`, `arbin_sql_7`, `arbin_sql_csv`, `arbin_sql_xlsx`, `arbin_sql_h5` |
| Maccor | `maccor_txt` (several export `model`s) |
| Neware | `neware_nda`, `neware_txt`, `neware_xlsx` |
| PEC | `pec_csv` |
| BioLogic | `biologics_mpr` |
| Battery Data Format (BatMo) | `batmo_bdf` |
| Anything else | `custom` (describe the layout in a YAML file) |

`cellpy.print_instruments()` prints the list for your installed version. If
your tester isn't on it, see [Other file formats](examples/06_loading_different_formats.md),
[Writing a custom loader](examples/07_custom_loaders.md), or
[write an instrument loader plugin](guides/writing_a_loader_plugin.md) from
your own package.

## Upgrading from cellpy 1.x

Version 2 changed the frames, the column names and the file format. What you
already know still applies, but some names are different now. The
[migration guide](getting_started/migration_v1_to_v2.md) covers what changed
and what to do about it. The [release history](other/project-history.md)
lists every change.

## Citing cellpy

If cellpy saved you time in a paper, thesis or report, please
[cite it](other/citing.md). Citations are how open-source tools like this stay
visible and funded. More about the project is under [About](other/index.md).
