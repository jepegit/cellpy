=======
History
=======


1.0.0 (2023) [under development]
================================

* Unit handling: new unit handling (using pint)
* Unit handling: renaming summary headers
* Unit handling: new cellpy-file-format version
* Unit handling: tool for converting old to new format
* Unit handling: parsing input parameters for units
* Templates: using one repository with sub-folders
* Templates: adding more documentation
* File handling: allow for external raw files (ssh)
* Readers: neware.txt (one version/model)
* Readers: arbin_sql7 (experimental, @jtgibson91)
* Batch plotting: collectors for both data collection, plotting and saving
* OCV-rlx: improvements of the OCV-rlx tools
* Internals: rename main classes (CellpyData -> CellpyCell, Cell -> Data)
* Internals: rename .cell property to .data
* Internals: allow for only one Data-object pr CellpyCell object
* CLI: general improvements and bug fixes
* CLI: move editing of db-file to the edit sub-command



0.4.3 (2023)
============

* Neware txt loader (supports one specific format only, other formats will have to wait for v.1.0)


0.4.2 (2022)
============

* Changed definition of Coulombic Difference (negative of previous)
* Updated loaders with hooks and additional base class TxtLoader with configuration mechanism
* Support for Maccor txt files
* Supports only python 3.8 and up
* Optional parameters through batch and pages
* Several bug fixes and minor improvements / adjustments
* Restrict use of instrument label to only one option
* Fix bug in example file (@kevinsmia1939)


0.4.1 (2021)
============

* Updated documentations
* CLI improvements
* New argument for get_cap: max_cycle
* Reverting from using Documents to user home for location of prm file in windows.
* Easyplot by Amund
* Arbin sql reader by Muhammad


0.4.0 (2020)
============

* Reading arbin .res files with auxiliary data should now work.
* Many bugs have been removed - many new introduced.
* Now on conda-forge (can be installed using conda).


0.4.0 a2 (2020)
===============

* Reading PEC files now updated and should work


0.4.0 a1 (2020)
===============

* New column names (lowercase and underscore)
* New batch concatenating and plotting routines


0.3.3 (2020)
============

* Switching from git-flow to github-flow
* New cli options for running batches
* cli option for creating template notebooks
* Using ruamel.yaml instead of pyyaml
* Using python-box > 4
* Several bug-fixes


0.3.2 (2019)
============

* Starting fixing documentation
* TODO: create conda package
* TODO: extensive tests


0.3.1 (2019)
============

* Refactoring - renaming from dfsummary to summary
* Refactoring - renaming from step_table to steps
* Refactoring - renaming from dfdata to raw
* Refactoring - renaming cellpy.data to cellpy.get
* Updated save and load cellpy files allowing for new naming
* Implemented cellpy new and cellpy serve cli functionality


0.3.0 (2019)
============

* New batch-feature
* Improved make-steps and make-summary functionality
* Improved cmd-line interface for setup
* More helper functions and tools
* Experimental support for other instruments
* invoke tasks for developers

0.2.1 (2018)
============

* Allow for using mdbtools also on win
* Slightly faster find_files using cache and fnmatch
* Bug fix: error in sorting files when using pathlib fixed


0.2.0 (2018-10-17)
==================

* Improved creation of step tables (much faster)
* Default compression on cellpy (hdf5) files
* Bug fixes


0.1.22 (2018-07-17)
===================

* Parameters can be set by dot-notation (python-box).
* The parameter Instruments.cell_configuration is removed.
* Options for getting voltage curves in different formats.
* Fixed python 3.6 issues with Read the Docs.
* Can now also be used on posix (the user must install mdb_tools first).
* Improved logging allowing for custom log-directory.


0.1.21 (2018-06-09)
===================

* No legacy python.


0.1.0 (2016-09-26)
==================

* First release on PyPI.
