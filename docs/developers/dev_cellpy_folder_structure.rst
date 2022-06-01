===================================
Structure of the ``cellpy`` package
===================================

Folder structure
----------------

.. code-block:: batch

    +---tests
    +---test_data
    +---docs
    +---examples
    +---cellpy
    |   |   __init__.py
    |   |   cli.py
    |   |   exceptions.py
    |   |   log.py
    |   |   logging.json
    |   |   _version.py
    |   |
    |   +---parameters
    |   |   |   __init__.py
    |   |   |   .cellpy_prms_default.conf
    |   |   |   internal_settings.py
    |   |   |   prmreader.py
    |   |   |   prms.py
    |   |
    |   +---readers
    |   |   |   __init__.py
    |   |   |   cellreader.py
    |   |   |   core.py
    |   |   |   dbreader.py
    |   |   |   filefinder.py
    |   |   |
    |   |   +---instruments
    |   |   |   |   __init__.py
    |   |   |   |   arbin_res.py
    |   |   |   |   arbin_sql.py
    |   |   |   |   arbin_sql_csv.py
    |   |   |   |   base.py
    |   |   |   |   custom_instrument.py
    |   |   |   |   local_instrument.py
    |   |   |   |   maccor_txt.py
    |   |   |   |   pec.py
    |   |   |   |
    |   |   |   +---configurations
    |   |   |   |   |   __init__.py
    |   |   |   |   |   maccor_txt_four.py
    |   |   |   |   |   maccor_txt_one.py
    |   |   |   |   |   maccor_txt_three.py
    |   |   |   |   |   maccor_txt_two.py
    |   |   |   |   |   maccor_txt_zero.py
    |   |   |   +---processors
    |   |   |   |   |   __init__.py
    |   |   |   |   |   post_processors.py
    |   |   |   |   |   pre_processors.py
    |   |   |   |
    |   +---utils
    |   |   |   __init__.py
    |   |   |   diagnostics.py
    |   |   |   easyplot.py
    |   |   |   example_data.py
    |   |   |   helpers.py
    |   |   |   ica.py
    |   |   |   ocv_rlx.py
    |   |   |   plotutils.py
    |   |   |   batch.py
    |   |   |
    |   |   +---batch_tools
    |   |   |   |   __init__.py
    |   |   |   |   batch_analyzers.py
    |   |   |   |   batch_core.py
    |   |   |   |   batch_experiments.py
    |   |   |   |   batch_exporters.py
    |   |   |   |   batch_helpers.py
    |   |   |   |   batch_journals.py
    |   |   |   |   batch_plotters.py
    |   |   |   |   batch_reporters.py
    |   |   |   |   dumpers.py
    |   |   |   |   engines.py
    |   |   |
    |   |   +---data
    |   |   |   |   20160805_test001_45_cc.h5
    |   |   |   |
    |   |   |   \---raw
    |   |   |           20160805_test001_45_cc_01.res
    setup.py
    ...


Handling of parameters
----------------------


Logging
-------

``cellpy`` uses the standard python ``logging`` module.

Readers
-------


Instrument readers
..................

Each reader is a subclass of ``Loader`` (in ``base.py``). It must implement
at least the following methods: ``get_raw_units``, ``get_raw_limits``, and ``loader``.

During loading (for example using ``cellpy.get``), ``cellpy`` uses ``loader`` method.
In addition, the ``Loader`` class already has the method ``identify_last_data_point"
implemented.

(Note to self: change name from ``loader`` to for example ``read`` in a future version.)

The ``base.py`` also contain two levels of subclasses of ``Loader`` that are sutiable
for more generic loaders.
The ``AutoLoader`` class (subclass of ``Loader``) implements loading a configuration
from a configuration module of file (see below), and performs pre- and post-processing
of the data/raw-file (the processors are turned on or off in the configuration).
Subclasses of the ``AutoLoader`` class must implement the following methods:
``parse_loader_parameters``, ``parse_formatter_parameters``, and ``query_file``.

The ``query_file`` method must return a ``pandas.DataFrame`` and accept a filename as argument,
e.g.::

    def query_file(self, name):
        return pd.read_csv(name)

You can´t provide additional arguments to the ``query_file`` method, but instead
promote them to instance variables using the ``parse_formatter_parameter`` method::

    def parse_loader_parameters(self, **kwargs):
        self.warn_bad_lines = kwargs.get("warn_bad_lines", None)

and then use the instance variables in the ``query_file`` method::

    def query_file(self, name):
        return pd.read_csv(name, warn_bad_lines=self.warn_bad_lines)


The ``TxtLoader`` class (subclass of ``AutoLoader``, also located in ``base.py``) uses ``pandas.read_csv`` as its query method,
and reads configurations from modules in ``cellpy.readers.instruments.configuration`` (or config file). It also implements
the `model` keyword. ``MaccorTxtLoader`` and ``LocalTxtLoader`` is a subclass of ``TxtLoader``.

The ``LocalTxtLoader`` gets its configuration from a configuration yaml file.

The ``CustomTxtLoader`` subclasses ``AutoLoader`` and is a bit more flexible than
``LocalTxtLoader`` and can for example chose between several file querying methods (
csv, xls, xlsx).


Internal basic readers
______________________

The following readers are implemented in the source code as subclasses of ``Loader``:
  - ``ArbinLoader`` in the ``arbin_res`` module
  - ``ArbinSQLLoader`` in the ``arbin_sql`` module
  - ``ArbinCsvLoader`` in the ``arbin_csv`` module
  - ``PECLoader`` in the ``pec`` module


Internal txt-readers
____________________


Custom readers
______________


Database readers
................


Other
.....


Utilities
---------


