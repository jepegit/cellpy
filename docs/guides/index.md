---
icon: material/wrench
---

# How-to guides

Task-focused recipes for when you already know the basics and need to do
something specific. If you just want the one-liner, start with
[How do I…?](../how_do_i.md).

**Working with one cell**

- [Units, mass, area and C-rates](units.md) — what a capacity is divided
  by, and how to change it
- [Plot one cell](plotting.md) — capacity fade, voltage curves, raw traces,
  and how to save the figure
- [Understand the step table](step_table.md) — how cellpy decides what a
  step is, and how to correct it when it gets it wrong
- [Compute incremental capacity and differential voltage](ica.md) — dQ/dV
  (`dqdv`) and dV/dQ (`dvdq`), plus plot and collect
- [Get your data out](exporting.md) — cellpy files, Excel, CSV, BDF, and
  batch bundles

**Many cells and remote data**

- [Set up the cellpy database](batch_database.md) — the Excel sheet the
  batch utility reads, and which columns you actually have to fill in
- [Work with remote files](remote_paths.md) — load raw data
  and cellpy files over SSH / SFTP

**Extending cellpy**

- [Write an instrument loader plugin](writing_a_loader_plugin.md) —
  add support for a cycler cellpy does not ship
- [Write a CLI plugin](writing_a_cli_plugin.md) — add commands under
  `cellpy` via the `cellpy.cli_plugins` entry-point group
