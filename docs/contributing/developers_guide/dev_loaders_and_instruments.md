# About loaders

Instrument loaders are used by `CellpyCell` to load data from a file into a `Data` object.

This page covers the **built-in** loaders shipped in `cellpy.readers.instruments` — the
module-scanning factory below is how they are discovered and instantiated internally.
If you are adding support for a cycler from *outside* cellpy (your own package, no
cellpy base class), that goes through the newer entry-point contract instead — see
[Write an instrument loader plugin](../../other/writing_a_loader_plugin.md) and the
[Instruments API reference](../../api/instruments.md). The two coexist: built-in
loaders have not been ported to the contract yet (`cellpy.readers.instruments.registry`
documents the current scope), so this factory remains the way to add or change one of
them.

The instrument loaders are all located in the `cellpy.readers.instruments` package (*i.e.* in
the folder `cellpy/readers/instruments`).
They are Python modules (.py files), discovered by scanning that package:

`CellpyCell.register_instrument_readers` -> `data_structures.generate_default_factory` -> `data_structures.find_all_instruments`

`register_instrument_readers` builds the default factory only when the `CellpyCell` does not
already have one — an injected `instrument_factory` is kept as-is. Set
`self.instrument_factory = None` first if you need to force a rebuild.

(Note that there are some naming conventions for the instrument loaders,
see `find_all_instruments` in `cellpy/readers/data_structures.py`)

The specific instrument loader is selected in `CellpyCell` through `CellpyCell._set_instrument`:

`CellpyCell.from_raw` -> `CellpyCell.set_instrument` -> `CellpyCell._set_instrument`

The instrument class is instantiated and bound to the `CellpyCell` instance (`CellpyCell.loader_class`).
The actual method (`loader_executor`) that will be executed when loading the data (through `CellpyCell.from_raw`)
is bound to the attribute `CellpyCell.loader`.

When `CellpyCell.from_raw` is called, the `AtomicLoad.loader_executor` is in charge of executing the instrument
loader's `loader` method. One implication of this, since `BaseLoader` is a subclass of
`AtomicLoad`, is that it is very "dangerous" to override `loader_executor` in a loader.

## Structure of instrument loaders

Each instrument module must define a class named `DataLoader`, subclassing `BaseLoader`
(in `cellpy/readers/instruments/base.py`) or one of its subclasses (see below). Note that
`DataLoader` is the required *name* of the class in each module — it is not itself defined
in `base.py`.

It must implement at least the following methods: `get_raw_units`, `get_raw_limits`,
and `loader`.

Two subclasses of `BaseLoader` are available to build on: `AutoLoader`, and `TxtLoader`
(which is in turn a subclass of `AutoLoader`).

### Subclassing `BaseLoader`

The `BaseLoader` class is a subclass of `AtomicLoad` (in `cellpy/readers/instruments/base.py`)
using `abc.ABCMeta` as metaclass.

For databases and similar, it is recommended to subclass `BaseLoader` directly. This allows
you to set the class attribute `_is_db` to True. This will make the `loader_executor` method
in `AtomicLoad` to not copy the "file" to a temporary location before issuing the `loader` method.

### Subclassing `AutoLoader`

The `AutoLoader` class is a subclass of `BaseLoader`. This class can be sub-classed
if you want to make a data-reader for different type of "easily parsed" files (for example csv-files).

The `AutoLoader` class implements loading a configuration
from a configuration module or a file (see below), and performs pre- and post-processing
of the data/raw-file (the processors are turned on or off in the configuration).
Subclasses of the `AutoLoader` class must implement the following methods:
`parse_loader_parameters`, `parse_formatter_parameters`, and `query_file`.

The `query_file` method must return a `pandas.DataFrame` and accept a filename as argument,
e.g.:

```python
def query_file(self, name):
    return pd.read_csv(name)
```

You can't provide additional arguments to the `query_file` method, but instead
promote them to instance variables using the `parse_loader_parameters` method
(use `parse_formatter_parameters` for the file-format knobs such as separator,
decimal marker and encoding):

```python
def parse_loader_parameters(self, **kwargs):
    self.on_bad_lines = kwargs.get("on_bad_lines", "error")
```

and then use the instance variables in the `query_file` method:

```python
def query_file(self, name):
    return pd.read_csv(name, on_bad_lines=self.on_bad_lines)
```

### Subclassing `TxtLoader`

The `TxtLoader` class is a subclass of `AutoLoader`. The subclass of
a `TxtLoader` gets its information by loading model specifications from
its respective module(`cellpy.readers.instruments.configurations.<module>`) or
configuration file (yaml).

The `TxtLoader` class uses `pandas.read_csv` as its query method,
and reads configurations from modules in `cellpy.readers.instruments.configurations` (or config file).
It also implements the `model` keyword.

Examples of modules where the loader is subclassing `TxtLoader` are `maccor_txt`,
`neware_txt` and `local_instrument`.

## The `local_instrument` loader

This module is used for loading data using the corresponding Local
yaml file with definitions on how the data should be loaded. This loader
is based on the `TxtLoader` and can only be used to load csv-type files.

## The `custom` loader

This module is used for loading data using the `instrument="custom"` method.
If no `instrument_file` is given (either directly or through the use
of the :: separator), the default instrument file (yaml) will be used.
This loader is based on the `AutoLoader`. It is more flexible than the loader
in `local_instrument` and can for example chose between several file querying methods (
csv, xls, xlsx), but it is also more complicated to use.
