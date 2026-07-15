# Structure of the cellpy package

## Folder structure

The `cellpy` repository is structured as follows:

```
📂 cellpy               # the main folder for the cellpy repository
├── 📂 .github          # github specific files (e.g. github actions)
├── 📂 bin              # binary files (mdbtools for win)
├── 📂 cellpy           # the main folder for the cellpy package
├── 📂 docs             # the main folder for the cellpy documentation
├── 📂 examples
├── 📂 test_journal     # data etc for the tests
├── 📂 testdata         # data etc for the tests
├── 📂 tests            # here are the tests
├── 📄 .coverage
├── 📄 .env_example
├── 📄 .gitattributes
├── 📄 .gitignore
├── 📄 .readthedocs.yaml
├── 📄 bumpver.toml
├── 📄 AUTHORS.rst        <-- picked up by sphinx (in docs)
├── 📄 README.rst         <-- picked up by sphinx (in docs)
├── 📄 CODE_OF_CONDUCT.md
├── 📄 CONTRIBUTING.rst   <-- picked up by sphinx (in docs)
├── 📄 HISTORY.rst        <-- picked up by sphinx (in docs)
├── 📄 LICENSE            <-- picked up by sphinx (in docs)
├── 📄 MANIFEST.in
├── 📄 pyproject.toml
├── 📄 dev_environment.yml
├── 📄 environment.yml
├── 📄 requirements_dev.txt
├── 📄 requirements.txt
├── 🐍 noxfile.py
├── 🐍 setup.py
```

The `cellpy` source code is structured as follows:

```
📂 cellpy\cellpy
├── 📂 internals
│   ├── 🐍 __init__.py
│   └── 🐍 core.py
├── 📂 parameters
│   ├── 📂 legacy
│   │   ├── 🐍 __init__.py
│   │   └── 🐍 update_headers.py
│   ├── 📄 .cellpy_prms_default.conf
│   ├── 🐍 __init__.py
│   ├── 🐍 internal_settings.py
│   ├── 🐍 prmreader.py
│   └── 🐍 prms.py
├── 📂 readers
│   ├── 📂 instruments
│   │   ├── 📂 .benchmarks
│   │   ├── 📂 configurations
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 maccor_txt_four.py
│   │   │   ├── 🐍 maccor_txt_one.py
│   │   │   ├── 🐍 maccor_txt_three.py
│   │   │   ├── 🐍 maccor_txt_two.py
│   │   │   ├── 🐍 maccor_txt_zero.py
│   │   │   └── 🐍 neware_txt_zero.py
│   │   ├── 📂 loader_specific_modules
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 biologic_file_format.py
│   │   ├── 📂 processors
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 post_processors.py
│   │   │   └── 🐍 pre_processors.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 arbin_res.py
│   │   ├── 🐍 arbin_sql.py
│   │   ├── 🐍 arbin_sql_7.py
│   │   ├── 🐍 arbin_sql_csv.py
│   │   ├── 🐍 arbin_sql_h5.py
│   │   ├── 🐍 arbin_sql_xlsx.py
│   │   ├── 🐍 base.py
│   │   ├── 🐍 biologics_mpr.py
│   │   ├── 🐍 custom.py
│   │   ├── 🐍 ext_nda_reader.py
│   │   ├── 🐍 local_instrument.py
│   │   ├── 🐍 maccor_txt.py
│   │   ├── 🐍 neware_txt.py
│   │   ├── 🐍 pec_csv.py
│   │   └── 📄 SQL Table IDs.txt
│   ├── 🐍 __init__.py
│   ├── 🐍 cellreader.py
│   ├── 🐍 core.py
│   ├── 🐍 dbreader.py
│   ├── 🐍 filefinder.py
│   └── 🐍 sql_dbreader.py
└── 📂 utils
    ├── 📂 batch_tools
    │   ├── 🐍 __init__.py
    │   ├── 🐍 batch_analyzers.py
    │   ├── 🐍 batch_core.py
    │   ├── 🐍 batch_experiments.py
    │   ├── 🐍 batch_exporters.py
    │   ├── 🐍 batch_helpers.py
    │   ├── 🐍 batch_journals.py
    │   ├── 🐍 batch_plotters.py
    │   ├── 🐍 batch_reporters.py
    │   ├── 🐍 dumpers.py
    │   ├── 🐍 engines.py
    │   └── 🐍 sqlite_from_excel_db.py
    ├── 📂 data
    │   ├── 📂 raw
    │   │   └── 📄 20160805_test001_45_cc_01.res
    │   └── 📄 20160805_test001_45_cc.h5
    ├── 🐍 __init__.py
    ├── 🐍 batch.py
    ├── 🐍 collectors.py
    ├── 🐍 collectors_old.py
    ├── 🐍 diagnostics.py
    ├── 🐍 easyplot.py
    ├── 🐍 example_data.py
    ├── 🐍 helpers.py
    ├── 🐍 ica.py
    ├── 🐍 live.py
    ├── 🐍 ocv_rlx.py
    ├── 🐍 plotutils.py
    └── 🐍 processor.py
    ...
```

## Handling of parameters

TODO: explain how parameters are handled

`.cellpy_prms_{user}.conf`

`.env_cellpy` and environment variables.

`cellpy.prms`

`cellpy.parameters.internal_settings`

## Logging

`cellpy` uses the standard python `logging` module.

## Utilities
