===================================
Structure of the ``cellpy`` package
===================================

Folder structure
----------------

.. code-block:: batch

 cellpy\
    │
    ├── internals\
    │   ├── core.py
    │   └── __init__.py
    │
    ├── parameters\
    │   ├── .cellpy_prms_default.conf
    │   ├── internal_settings.py
    │   ├── prmreader.py
    │   ├── prms.py
    │   └── __init__.py
    │
    ├── readers\
    │   ├── instruments\
    │   │   ├── .benchmarks\
    │   │   │
    │   │   ├── configurations\
    │   │   │   ├── maccor_txt_four.py
    │   │   │   ├── maccor_txt_one.py
    │   │   │   ├── maccor_txt_three.py
    │   │   │   ├── maccor_txt_two.py
    │   │   │   ├── maccor_txt_zero.py
    │   │   │   ├── neware_txt_zero.py
    │   │   │   └── __init__.py
    │   │   │
    │   │   ├── loader_specific_modules\
    │   │   │   ├── biologic_file_format.py
    │   │   │   └── __init__.py
    │   │   │
    │   │   ├── processors\
    │   │   │   ├── post_processors.py
    │   │   │   ├── pre_processors.py
    │   │   │   └── __init__.py
    │   │   │
    │   │   ├── arbin_res.py
    │   │   ├── arbin_sql.py
    │   │   ├── arbin_sql_7.py
    │   │   ├── arbin_sql_csv.py
    │   │   ├── arbin_sql_h5.py
    │   │   ├── arbin_sql_xlsx.py
    │   │   ├── base.py
    │   │   ├── biologics_mpr.py
    │   │   ├── custom.py
    │   │   ├── ext_nda_reader.py
    │   │   ├── local_instrument.py
    │   │   ├── maccor_txt.py
    │   │   ├── neware_txt.py
    │   │   ├── pec_csv.py
    │   │   ├── SQL Table IDs.txt
    │   │   └── __init__.py
    │   │
    │   ├── cellreader.py
    │   ├── core.py
    │   ├── dbreader.py
    │   ├── filefinder.py
    │   ├── sql_dbreader.py
    │   └── __init__.py
    │
    ├── utils\
    │   ├── batch_tools\
    │   │   ├── batch_analyzers.py
    │   │   ├── batch_core.py
    │   │   ├── batch_experiments.py
    │   │   ├── batch_exporters.py
    │   │   ├── batch_helpers.py
    │   │   ├── batch_journals.py
    │   │   ├── batch_plotters.py
    │   │   ├── batch_reporters.py
    │   │   ├── dumpers.py
    │   │   ├── engines.py
    │   │   ├── sqlite_from_excel_db.py
    │   │   └── __init__.py
    │   │
    │   ├── data\
    │   │   ├── raw\
    │   │   │   └── 20160805_test001_45_cc_01.res
    │   │   │
    │   │   └── 20160805_test001_45_cc.h5
    │   │
    │   ├── batch.py
    │   ├── collectors.py
    │   ├── collectors_old.py
    │   ├── diagnostics.py
    │   ├── easyplot.py
    │   ├── example_data.py
    │   ├── helpers.py
    │   ├── ica.py
    │   ├── live.py
    │   ├── ocv_rlx.py
    │   ├── plotutils.py
    │   ├── processor.py
    │   └── __init__.py
    │
    ├── cli.py
    ├── exceptions.py
    ├── log.py
    ├── logging.json
    ├── _version.py
    └── __init__.py
    ...


Handling of parameters
----------------------

TODO: explain how parameters are handled


``.cellpy_prms_{user}.conf``


``.env_cellpy`` and environment variables.


``cellpy.prms``


``cellpy.parameters.internal_settings``


Logging
-------

``cellpy`` uses the standard python ``logging`` module.


Utilities
---------


