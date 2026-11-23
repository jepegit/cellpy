<img src="https://raw.githubusercontent.com/jepegit/cellpy/master/docs/_static/cellpy-icon-long.svg" height="100" alt="cellpy-icon">

# **cellpy** - *a library for assisting in analysing batteries and cells*


[![cellpy](https://img.shields.io/pypi/v/cellpy.svg)](https://pypi.python.org/pypi/cellpy)
[![cellpy](https://readthedocs.org/projects/cellpy/badge/?version=latest)](https://cellpy.readthedocs.io/en/latest/?badge=latest)
[![cellpy](https://static.pepy.tech/badge/cellpy)](https://pepy.tech/project/cellpy)

This Python Package was developed to help the
researchers at IFE, Norway, in their cumbersome task of
interpreting and handling data from cycling tests of batteries and cells.

## Features

* Convert testing data into a common format
* Summarize and compare data
* Filter out the steps of interest
* Process and plot the data
* Do simple and advanced analysis on single datasets as well as collections of datasets
* And more!

## Documentation

The documentation for ``cellpy`` is hosted on [Read the Docs](https://cellpy.readthedocs.io).

## Installation and dependencies

We recommend installing ``cellpy`` with [uv](https://docs.astral.sh/uv/). It needs no
admin rights, can download Python for you, and installs everything from ready-built
wheels, including HDF5 support for the old `.h5` cellpy format:

```
uv venv --python 3.13
uv pip install "cellpy[batch,legacy-files]"
```

Or with pip (Python 3.13 or newer):

```
python -m pip install "cellpy[batch,legacy-files]"
```

Or with conda:

```
conda install -c conda-forge cellpy
```

`[batch]` adds plotting and Jupyter; `[legacy-files]` adds PyTables (HDF5) for
reading and writing cellpy 1.x `.h5` files. Have a look at the
[installation guide](https://cellpy.readthedocs.io/en/latest/getting_started/installation/)
for platform details (Arbin `.res` drivers, system packages).

## License

``cellpy`` is free software made available under the MIT License.

## Citing cellpy

If you use ``cellpy`` in your work, please cite our paper:

> Wind J., Ulvestad A., Abdelhamid M., Mæhlen J.P. (2024). Cellpy – an open-source library for processing and analysis of battery testing data. _Journal of Open Source Software, 9(97), 6236_.

[![DOI](https://joss.theoj.org/papers/10.21105/joss.06236/status.svg)](https://doi.org/10.21105/joss.06236)

## Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. If you want to contribute,
please have a look at [Contributing Guidelines](CONTRIBUTING.md).
