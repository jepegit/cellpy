Structure of the ``cellpy`` package
===================================


.. code-block:: batch

    +---cellpy
    |   |   cli.py
    |   |   exceptions.py
    |   |   log.py
    |   |   logging.json
    |   |   _version.py
    |   |   __init__.py
    |   |
    |   +---parameters
    |   |   |   .cellpy_prms_default.conf
    |   |   |   internal_settings.py
    |   |   |   internal_settings_old.py
    |   |   |   prmreader.py
    |   |   |   prms.py
    |   |   |   __init__.py
    |   |   |
    |   |   +---legacy
    |   |   |   |   internal_settings.py
    |   |   |   |   __init__.py
    |   |   |   |
    |   |   |   \---__pycache__
    |   |   |           internal_settings.cpython-310.pyc
    |   |   |           internal_settings.cpython-39.pyc
    |   |   |           __init__.cpython-310.pyc
    |   |   |           __init__.cpython-39.pyc
    |   |
    |   +---readers
    |   |   |   cellreader.py
    |   |   |   core.py
    |   |   |   dbreader.py
    |   |   |   filefinder.py
    |   |   |   __init__.py
    |   |   |
    |   |   +---instruments
    |   |   |   |   arbin_res.py
    |   |   |   |   arbin_sql.py
    |   |   |   |   arbin_sql_csv.py
    |   |   |   |   backup_arbin.py
    |   |   |   |   base.py
    |   |   |   |   biologics_mpr.py
    |   |   |   |   biologic_file_format.py
    |   |   |   |   custom.py
    |   |   |   |   custom_instrument.py
    |   |   |   |   ext_nda_reader.py
    |   |   |   |   local_instrument.py
    |   |   |   |   maccor_txt.py
    |   |   |   |   pec.py
    |   |   |   |   __init__.py
    |   |   |   |
    |   |   |   +---configurations
    |   |   |   |   |   maccor_txt_four.py
    |   |   |   |   |   maccor_txt_one.py
    |   |   |   |   |   maccor_txt_three.py
    |   |   |   |   |   maccor_txt_two.py
    |   |   |   |   |   maccor_txt_zero.py
    |   |   |   |   |   __init__.py
    |   |   |   +---processors
    |   |   |   |   |   post_processors.py
    |   |   |   |   |   pre_processors.py
    |   |   |   |   |   __init__.py
    |   |   |   |
    |   +---utils
    |   |   |   batch.py
    |   |   |   diagnostics.py
    |   |   |   easyplot.py
    |   |   |   example_data.py
    |   |   |   helpers.py
    |   |   |   ica.py
    |   |   |   live.py
    |   |   |   ocv_rlx.py
    |   |   |   plotutils.py
    |   |   |   run_easyplot.py
    |   |   |   __init__.py
    |   |   |
    |   |   +---batch_tools
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
    |   |   |   |   __init__.py
    |   |   |
    |   |   +---data
    |   |   |   |   20160805_test001_45_cc.h5
    |   |   |   |
    |   |   |   \---raw
    |   |   |           20160805_test001_45_cc_01.res




