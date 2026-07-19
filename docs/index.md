# cellpy

**cellpy** reads data from battery cycling instruments, turns it into one
consistent format, and gives you the derived quantities — capacities,
coulombic efficiencies, incremental capacity — without you writing the
bookkeeping.

```python
import cellpy

c = cellpy.get("my_cell.res", instrument="arbin_res", mass=0.85)
c.data.summary[c.schema.summary.charge_capacity]
```

## Where to start

- **New here?** Install it, point it at a file, and see what comes back —
  [Getting started](getting_started/index.md).
- **Have data to load?** Worked examples, from a single file to a whole batch —
  [Tutorials](examples/index.md).
- **Want to understand the shapes?** What a cell object holds and how the
  frames relate — [Concepts](fundamentals/index.md).
- **Looking for a signature?** Generated from the docstrings —
  [API reference](api/index.md).

## Coming from cellpy 1.x

Version 2 changed the frames, the column names and the file format. Nothing you
know is wasted, but some of it is spelled differently now — the
[migration guide](getting_started/migration_v1_to_v2.md) covers what changed and
what to do about it.

## Support your own instrument

If cellpy does not read your instrument's files yet, you can add a loader from
your own package without patching cellpy: see
[writing an instrument loader plugin](other/writing_a_loader_plugin.md).

## About

--8<-- "docs/adapted_readme.md"

## License

`cellpy` is free software under the MIT License.
