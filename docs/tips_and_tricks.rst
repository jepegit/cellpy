====================
Some tips and tricks
====================

Overriding settings
-------------------
If you would like to override some of the standard settings, then
the route of less friction is to import the prms class and set
new values directly.

Below is a simple example where we set an option so that we can load
arbin-files (.res) using mdbtools (i.e. spawning a subprocess that
converts the .res-file to .csv-files, then loading and deleting the
.csv-files):

.. code-block:: python

    from cellpy import prms

    # use mdbtools even though you are on windows
    prms.Instruments.use_subprocess = True

Another typical value you might want to change (but not permanently by setting
its value in the config file) is the cell-type ("anode" or something else) and
informing about the "quality" of your raw-data.


.. code-block:: python

    from cellpy import prms

    # I have set "anode" as default in my config-file, but this time
    # I am going to look at a cathode
    prms.Reader.cycle_mode = "cathode"

    # I don't trust that my data are sorted
    prms.Reader.sorted_data = False

    # I am using a "strange" version of an cell-tester / software setup
    # that don't make any stat file (last "reading" for each cycle).
    prms.Reader.use_cellpy_stat_file = False


Another typical setting you might want to change during a session (and doing
it without having to edit your config file) is the input and output directories.


.. code-block:: python

    from cellpy import prms

    # use an temporary folder for playing around and testing stuff
    prms.Paths.rawdatadir = r"C:\tmp"
    prms.Paths.cellpydatadir = r"C:\tmp"
    prms.Paths.filelogdir = r"C:\tmp"

More tips and tricks will come soon!
