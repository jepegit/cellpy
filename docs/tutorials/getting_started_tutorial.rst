The getting started with ``cellpy`` tutorial (opinionated version)
==================================================================

This tutorial will help you getting started with ``cellpy`` and
tries to give you a step-by-step recipe.

How to install ``cellpy`` - the minimalistic explanation
--------------------------------------------------------

If you know what you are doing, and only need the most basic features
of ``cellpy``, you should be able to get things up and running by
issuing a simple

  .. code:: bash
  
    pip install cellpy

It is recommended that you use a Python environment (or conda
environment) and give it an easy-to-remember name *e.g.* ``cellpy``.

To make sure your environment contains the correct packages and
dependencies, you can create the environment based on the available
`environment.yml <https://github.com/jepegit/cellpy/blob/master/environment.yml>`_
file. For further information on depencencies and requirements for setting up
``cellpy`` to read .res (Arbin) files, have a look at the *Install depencencies*
part of the next section.

For the installation of specific versions and pre-releases, see
`Check your cellpy installation`_.


How to install ``cellpy`` - the tea spoon explanation
-----------------------------------------------------

If you are used to installing stuff from the command line (or shell),
then things might very well run smoothly. However, a considerable
percentage of us don’t feel exceedingly comfortable installing things by
writing commands inside a small black window. Let’s face it; we belong
to the *point-and-click* (or *double-click*) generation, not the
*write-cryptic-commands* generation. So, hopefully without insulting the
savvy, here is a “tea-spoon explanation”:

1. Install a scientific stack of python 3.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the words “virtual environment” or “miniconda” do not ring any bells,
you should install the Anaconda scientific Python distribution. Go to
`www.anaconda.com <https://www.anaconda.com/>`__ and select the
Anaconda distribution (press the ``Download Now`` button).
Use at least python 3.6, and select the 64 bit version
(if you fail at installing the 64 bit version, then you can try the
weaker 32 bit version). Download it and let it install.

*Note:* The bin version matters sometimes, so try to make a mental note
of what you selected. E.g., if you plan to use the Microsoft Access odbc
driver (see below), and it is 32-bit, you probably should chose to install
a 32-bit python version).

2. Create a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step can be omitted (but its not necessarily smart to do so).
Create a virtual conda environment called ``cellpy`` (the name is not
important, but it should be a name you are able to remember) by following
the steps below:

Open up the "Anaconda Prompt" (or use the command window) and type

  .. code:: bash
  
    conda create -n cellpy

This creates your virtual environment (here called *cellpy*) in which ``cellpy``
will be installed and used.

To make sure your environment contains the correct packages and dependencies
required for running cellpy, you can create an environment based on the available
``environment.yml`` file. Download the
`environment.yml <https://github.com/jepegit/cellpy/blob/master/environment.yml>`_
file and place it in the directory shown in your Anaconda Prompt. If you want to
change the name of the environment, you can do this by changing the first line of
the file. Then type (in the Anaconda Prompt):

  .. code:: bash
  
    	conda env create -f environment.yml

Then activate your environment:

  .. code:: bash
  
     conda activate cellpy

3. Install depencencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``cellpy`` relies on a number of other python package and these need
to be installed. Most of these packages are included when creating the environment
based on the ``environment.yml`` file as outlined above.

Basic dependencies
::::::::::::::::::

In general, you need the typical scientific python pack, including

- ``numpy``
- ``scipy``
- ``pandas``.

It is recommended that you at least install ``scipy`` before you install
``cellpy`` (the main benefit being that you can use ``conda`` so that you
do not have to hassle with missing C-compilers if you are on an Windows
machine).
Additional dependencies are:

- ``pytables`` is needed for working with the hdf5 files (the cellpy-files):
  
    .. code:: bash
    
       conda install -c conda-forge pytables

- ``lmfit`` is required to use some of the fitting routines in ``cellpy``:

    .. code:: bash
  
     conda install -c conda-forge lmfit

- ``holoviz``: plotting library used in several of our example notebooks.

- *Jupyter*: used for tutorial notebooks and in general very useful tool
   for working with and sharing your ``cellpy`` results.

For more details, I recommend that you look at the documentation of these
packages (google it) and install them. You can most
likely use the same method as for pytables etc.

Additional requirments for .res files
:::::::::::::::::::::::::::::::::::::

.res files from Arbin testers actually are in a Microsoft Access format.
For loading .res-files (possible also for other *‘to-be-implemented’* file
formats) you will thus also need a *Python ODBC bridge* (in addition to the
requirements set in the ``setup.py`` file).
I recommend `pyodbc <https://github.com/mkleehammer/pyodbc/wiki>`__ that
can be installed from conda forge or using pip.

  .. code:: bash
  
     conda install -c conda-forge pyodbc

Additionally, you need a driver or similar to help your ODBC bridge
accessing it. 

*For Windows users:* if you do not have one of the 
most recent Office versions, you might not be allowed to install a driver
of different bit than your office version is using (the installers can be found
`here <https://www.microsoft.com/en-US/download/details.aspx?id=13255>`__).
Also remark that the driver needs to be of the same bit as your Python
(so, if you are using 32 bit Python, you will need the 32 bit driver).

*For POSIX systems:* I have not found any suitable drivers. Instead,
``cellpy`` will try to use ``mdbtools``\ to first export the data to
temporary csv-files, and then import from those csv-file (using the
``pandas`` library). You can install ``mdbtools`` using your systems
preferred package manager (*e.g.* ``apt-get install mdbtools``).

4. Install ``cellpy``
~~~~~~~~~~~~~~~~~~~~~
In your activated ``cellpy`` environment in the Anaconda Prompt run:

  .. code:: bash
  
     conda install -c conda-forge cellpy

Congratulations, you have (hopefully) successfully installed cellpy.

If you run into problems, doublecheck that all your dependencies are 
installed and check your Microsoft Access odbc drivers.


Check your cellpy installation
-------------------------------------

The easiest way to check if ``cellpy`` has been installed, is to issue
the command for printing the version number to the screen

.. code:: bash

   cellpy info --version

If the program prints the expected version number, you probably
succeeded. If it crashes, then you will have to retrace your steps, redo
stuff and hope for the best. If it prints an older (lower) version
number than you expect, there is a big chance that you have installed it
earlier, and what you would like to do is to do an ``upgrade`` instead
of an ``install``

.. code:: bash

   pip install --upgrade cellpy

If you want to install a pre-release (a version that is so bleeding edge
that it ends with a alpha or beta release identification, *e.g.* ends
with .b2). Then you will need to add the –pre modifier

.. code:: bash

   pip install --pre cellpy

To run a more complete check of your installation, there exist a
``cellpy`` sub-command than can be helpful

.. code:: bash

   cellpy info --check

Set up ``cellpy``
-----------------

After you have installed ``cellpy`` it is highly recommended that you
create an appropriate configuration file and folders for raw data,
cellpy-files, logs, databases and output data (and inform
``cellpy`` about it).

To do this, run the setup command:

  .. code:: bash
  
       cellpy setup

To run the setup in interactive mode, use -i:

  .. code:: bash
  
       cellpy setup -i

This creates the cellpy configuration file ``_cellpy_prms_USERNAME.conf``
in your home directory (USERNAME = your user name) and creates the standard
cellpy_data folders (if they do not exist).
The ``-i`` option makes sure that the setup is done interactively:
The program will ask you about where specific folders are, *e.g.* where
you would like to put your outputs and where your cell data files are
located. If the folders do not exist, ``cellpy`` will try to create them.

If you want to specify a root folder different from the default (your HOME
folder), you can use the ``-d`` option *e.g.*
``cellpy setup -i -d /Users/kingkong/cellpydir``

.. hint::
   You can always edit your configurations directly in the cellpy configuration
   file ``_cellpy_prms_USER.conf``. This file should be located inside your
   home directory, /~ in posix and c:\users\USERNAME in not-too-old windows.



The cellpy configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The paths to raw data, the cellpy data base file, file locations etc. are set in
the ``_cellpy_prms_USER.conf`` file that is usually located in your home directory.

To get the filepath to your config file (and other cellpy info), run:

  .. code:: bash
  
       cellpy info -l

The config file is written in YAML format and it should be relatively easy to
edit it in a text editor.

Within the config file, the paths are the most important parts that need to
be set up correctly. This tells ``cellpy`` where to find (and save) different files,
such as the database file and raw data.

Furthermore, the config file contains details about the databasefile to be
used for cell info and metadata (i.e. type and structure of the database file such
as column headers etc.)


The database file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The database file should contain information (cell name, type, mass loading etc.)
on your cells, so that cellpy can find and link the test data to the provided
metadata.

The database file is also useful when working with the ``cellpy`` batch routine.


Useful ``cellpy`` commands
-------------------------------------

To help installing and controlling your ``cellpy`` installation, a CLI
(command-line-interface) is provided with several commands (including the already
mentioned ``info`` for getting information about your installation, and 
``setup`` for helping you to set up your installation and writing a configuration file).

To get a list of these commands including some basic information, you can issue

.. code:: bash

   cellpy --help

This will output some (hopefully) helpful text

.. code:: bash

    Usage: cellpy [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      edit   Edit your cellpy config file.
      info   This will give you some valuable information about your cellpy.
      new    Set up a batch experiment.
      pull   Download examples or tests from the big internet.
      run    Run a cellpy process.
      serve  Start a Jupyter server
      setup  This will help you to setup cellpy.

You can get information about the sub-commands by issuing –-help after
them also. For example, issuing

.. code:: bash

   cellpy info --help

gives

.. code:: bash

   Usage: cellpy info [OPTIONS]

   Options:
     -v, --version    Print version information.
     -l, --configloc  Print full path to the config file.
     -p, --params     Dump all parameters to screen.
     -c, --check      Do a sanity check to see if things works as they should.
     --help           Show this message and exit.



Running your first script
-------------------------

As with most software, you are encouraged to play a little with it. I
hope there are some useful stuff in the code repository (for example in
the `examples
folder <https://github.com/jepegit/cellpy/tree/master/examples>`__).

.. hint::
    The ``cellpy pull`` command can assist in downloading
    both examples and tests.

Start by trying to import ``cellpy`` in an interactive Python session.
If you have an icon to press to start up the Python in interactive mode,
do that (it could also be for example an ipython console or a Jupyter
Notebook). 
You can also start an interactive Python session if you are in your
terminal window of command window by just writing ``python`` and pressing
enter.
*Hint:* Remember to activate your cellpy (or whatever name you
chose) environment.

Once inside Python, try issuing ``import cellpy``. Hopefully you should not see
any error-messages.

.. code-block:: python

    Python 3.9.9 | packaged by conda-forge | (main, Dec 20 2021, 02:36:06)
    [MSC v.1929 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import cellpy
    >>>

Nothing bad happened this time. If you got an error message, try to interpret
it and check if you have skipped any steps in this tutorial. Maybe you are
missing the ``box`` package? If so, go out of the Python interpreter if you
started it in your command window, or open another command window and write

.. code:: bash

    pip install python-box

and try again.

Now let's try to be a bit more ambitious. Start up python again if you are
not still running it and try this:

.. code-block:: python

    >>> from cellpy import prmreader
    >>> prmreader.info()

The ``prmreader.info()`` command should print out information about your
cellpy settings. For example where you selected to look for your input
raw files (``prms.Paths.rawdatadir``).

Try scrolling to find your own ``prms.Paths.rawdatadir``. Does it look
right? These settings can be changed by either re-running the
``cellpy setup -i`` command (not in Python, but in the command window /
terminal window). You probably need to use the ``--reset`` flag this time
since it is not your first time running it).


What next?
----------

For example: If you want to use the highly popular (?) ``cellpy.utils.batch``
utility, you
need to make (or copy from a friend) the "database" (an excel-file with
appropriate headers in the first row) and make sure that all the paths
are set up correctly in you cellpy configuration file.

Or, for example: If you would like to do some interactive plotting of your
data, try to install holoviz and use Jupyter Lab to make some fancy plots
and dash-boards.

And why not: make a script that goes through all your thousands of measured
cells, extracts the life-time (e.g. number of cycles until the capacity
has dropped below 80% of the average of the three first cycles), and plot
this versus time the cell was put. And maybe color the data-points based
on who was doing the experiment?
