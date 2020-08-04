=======
History
=======

0.4.0 a2 (2020)
---------------

* Reading PEC files now updated and should work


0.4.0 a1 (2020)
---------------

* New column names (lowercase and underscore)
* New batch concatenating and plotting routines


0.3.3 (2020)
------------

* Switching from git-flow to github-flow
* New cli options for running batches
* cli option for creating template notebooks
* Using ruamel.yaml instead of pyyaml
* Using python-box > 4
* Several bug-fixes


0.3.2 (2019)
------------

* Starting fixing documentation
* TODO: create conda package
* TODO: extensive tests


0.3.1 (2019)
------------

* Refactoring - renaming from dfsummary to summary
* Refactoring - renaming from step_table to steps
* Refactoring - renaming from dfdata to raw
* Refactoring - renaming cellpy.cell to cellpy.get
* Updated save and load cellpy files allowing for new naming
* Implemented cellpy new and cellpy serve cli functionality


0.3.0 (2019)
------------

* New batch-feature
* Improved make-steps and make-summary functionality
* Improved cmd-line interface for setup
* More helper functions and tools
* Experimental support for other instruments
* invoke tasks for developers

0.2.1 (2018)
------------

* Allow for using mdbtools also on win
* Slightly faster find_files using cache and fnmatch
* Bug fix: error in sorting files when using pathlib fixed


0.2.0 (2018-10-17)
------------------

* Improved creation of step tables (much faster)
* Default compression on cellpy (hdf5) files
* Bug fixes


0.1.22 (2018-07-17)
-------------------

* Parameters can be set by dot-notation (python-box).
* The parameter Instruments.cell_configuration is removed.
* Options for getting voltage curves in different formats.
* Fixed python 3.6 issues with Read the Docs.
* Can now also be used on posix (the user must install mdb_tools first).
* Improved logging allowing for custom log-directory.


0.1.21 (2018-06-09)
-------------------

* No legacy python.


0.1.0 (2016-09-26)
------------------

* First release on PyPI.
