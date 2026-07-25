<img src="_static/cellpy-icon-long.svg" height="300" alt="cellpy-icon">


# - *a library for assisting in analysing batteries and cells*


[![cellpy package](https://img.shields.io/pypi/v/cellpy.svg)](https://pypi.python.org/pypi/cellpy)
[![Documentation Status](https://readthedocs.org/projects/cellpy/badge/?version=latest)](https://cellpy.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://pepy.tech/badge/cellpy)](https://pepy.tech/project/cellpy)


**cellpy** reads data from battery cycling instruments, turns it into one
consistent format, and gives you the derived quantities — capacities,
coulombic efficiencies, incremental capacity — without you writing the
bookkeeping.


```python
import cellpy

c = cellpy.get("my_cell.res", instrument="arbin_res", mass=0.85)
c.data.summary[c.schema.summary.charge_capacity]
```

!!! warning
    This is a release candidate and might not work as expected.
    Let us know if you find some of the hidden bugs we have planted.

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

## History

This Python package was developed to help the researchers at IFE, Norway, in
their cumbersome task of interpreting and handling data from cycling tests of
batteries and cells. Building and maintaining it has taken a lot of work over
many years — loaders, formats, edge cases, and all the bookkeeping that used to
live in one-off scripts.

cellpy often sits *in the background* of an analysis pipeline: you load a file,
get a summary, and move on to the science. That makes it easy for the library
to disappear from the credits even when it did a large share of the grunt work.
If cellpy saved you time in a paper, thesis, or report, please
[cite it](other/citing.md) — a citation is how open-source tools like this stay
visible and fundable.


## License

cellpy is free software under the MIT License.

