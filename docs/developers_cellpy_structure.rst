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


Readers
-------


Instrument readers
..................


Internal basic readers
______________________


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


