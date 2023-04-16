About loaders
=============

Instrument loaders are used by ``CellpyCell`` to load data from a file into a ``Data`` object.
The instrument loaders are all located in the ``cellpy.readers.instruments`` package (*i.e.* in
the folder `cellpy/readers/instruments`).
They are Python modules (.py files) and are automatically registered when ``CellpyCell`` is
initialized:

``CellpyCell.register_instrument_readers`` -> ``core.generate_default_factory`` -> ``core.find_all_instruments``

(Note that there are some naming conventions for the instrument loaders,
see ``find_all_instruments`` in `cellpy/core.py`)

The specific instrument loader is selected in ``CellpyCell`` through ``CellpyCell._set_instrument``:

`CellpyCell.from_raw` -> `CellpyCell.set_instrument` -> `CellpyCell._set_instrument`

The instrument class is instantiated and bound to the ``CellpyCell`` instance (``CellpyCell.loader_class``).
The actual method (``loader_executor``) that will be executed when loading the data (through ``CellpyCell.from_raw``)
is bound to the attribute ``CellpyCell.loader_method``.

When ``CellpyCell.from_raw`` is called, the ``AtomicLoad.loader_executor`` is in charge of executing the instrument
loaders ``DataLoader.loader`` method. One implication of this, since the ``DataLoader`` is a subclass of
``AtomicLoad``, is that it is very "dangerous" to override ``loader_executor`` in the ``DataLoader``.


Structure of instrument loaders
-------------------------------

The instrument loaders must all have a class named ``DataLoader`` which is a subclasses of ``BaseLoader``
(in `cellpy/readers/instruments/base.py`) or one of its available subclasses (see below).

The following subclasses of ``BaseLoader`` are available (v.1.0): ``AutoLoader`` and ``TxtLoader``.


Subclassing ``BaseLoader``
..........................

The ``BaseLoader`` class is a subclass of ``AtomicLoad`` (in `cellpy/readers/instruments/base.py`)
using ``abc.ABCMeta`` as metaclass.

For databases and similar, it is recommended to subclass ``BaseLoader`` directly. This allows
you to set the class attribute ``_is_db`` to True. This will make the ``loader_executor`` method
in ``AtomicLoad`` to not copy the "file" to a temporary location before issuing the ``loader`` method.


Subclassing ``AutoLoader``
..........................

The ``AutoLoader`` class is a subclass of ``BaseLoader``. This class can be sub-classed
if you want to make a data-reader for different type of "easily parsed" files (for example csv-files).


Subclassing ``TxtLoader``
.........................

The ``TxtLoader`` class is a subclass of ``AutoLoader``. The subclass of
a ``TxtLoader`` gets its information by loading model specifications from
its respective module(``cellpy.readers.instruments.configurations.<module>``) or
configuration file (yaml).

Examples of modules where the loader is subclassing ``TxtLoader`` are ``maccor_txt``,
``neware_txt`` and ``local_instrument``.


The ``local_instrument`` loader
-------------------------------

This module is used for loading data using the corresponding Local
yaml file with definitions on how the data should be loaded. This loader
is based on the ``TxtLoader`` and can only be used to load csv-type files.


The ``custom`` loader
---------------------

This module is used for loading data using the `instrument="custom"` method.
If no `instrument_file` is given (either directly or through the use
of the :: separator), the default instrument file (yaml) will be used.
This loader is based on the ``AutoLoader``. It is more flexible than the
``local_instrument`` loader, but it is also more complicated to use.
