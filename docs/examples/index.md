---
icon: material/school
---

# Tutorials

Worked examples you can run from start to finish. Each page is a Jupyter
notebook with its outputs. At the top of each page you'll find what it covers,
which data it uses, and a link to the notebook.

!!! tip "Get the notebooks and their data"

    ```console
    cellpy pull --examples
    ```

    This downloads the `examples/` folder (notebooks + `data/`) into the
    examples folder `cellpy setup` configured (`cellpy info --config` shows
    where). Needs `git`. You can also browse it
    [on GitHub](https://github.com/jepegit/cellpy/tree/master/examples).

New to cellpy? Do [Your first hour](../getting_started/first_hour.md) first.
It needs no files of your own.

## The core path

Work through these in order. Each one builds on the one before.

| Tutorial | You will learn to | Level |
| --- | --- | --- |
| [Loading and saving data](01_loading_data.md) | load raw files into a cell object, look at the summary and step table, save and export | beginner |
| [First look at your data](02_Initial_data_inspection.md) | plot raw traces, cycle information and summary plots | beginner |
| [Capacity vs voltage](03_capacity_vs_voltage.md) | pull out capacity–voltage curves for chosen cycles | beginner |
| [Incremental capacity analysis](04_incremental_capacity_analysis.md) | compute and plot dQ/dV and dV/dQ | intermediate |
| [GITT analysis](05_GITT.md) | read (pseudo-)OCV points out of a GITT test | intermediate |
| [Batch processing](batch_utility/cellpy_batch_processing.md) | process and compare many cells as one job (the sheet it reads is described in [Set up the cellpy database](../guides/batch_database.md)) | intermediate |
| [Project templates](templates/tutorial_templates.md) | start a new analysis project from a template | intermediate |

## Loading data from other instruments

Pick the one for your tester.

| Tutorial | Instrument |
| --- | --- |
| [Other file formats](06_loading_different_formats.md) | PEC, Maccor, Neware — and how to choose an instrument name |
| [BatMo BDF files](08_batmo_bdf.md) | BatMo / Battery Data Format CSV |
| [PEC CSV data](09_loading_pec_data.md) | PEC exports, including several tests of one cell |
| [Writing a custom loader](07_custom_loaders.md) | a file layout cellpy does not know yet, described in YAML |

Want to add your instrument to cellpy for good? See
[Write an instrument loader plugin](../guides/writing_a_loader_plugin.md).

!!! note
    The tutorials use the 2.1 API (`c.schema`, `potential` / `cycle_num` /
    `step_type`, registered `summary_plot` families). If something doesn't
    work, [let us know](https://github.com/jepegit/cellpy/issues).
    [More example notebooks](../contributing/contributing.md) are welcome.
    How the pages are made is described in
    [Documentation](../contributing/developers_guide/dev_docs.md#example-notebooks-jupyter).
