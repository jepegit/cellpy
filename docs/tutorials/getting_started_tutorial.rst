The getting started with ``cellpy`` tutorial (opinionated version)
==================================================================

This tutorial will help you getting started with ``cellpy`` and
tries to give you a step-by-step recipe. The information in this tutorial
can also (most likely) be found elsewhere. For the novice users,
jump directly to chapter 1.2.

How to install ``cellpy`` - the minimalistic explanation
--------------------------------------------------------

If you know what you are doing, and only need the most basic features
of ``cellpy``, you should be able to get things up and running by
issuing a simple

.. code:: bash

   pip install cellpy

It is recommended that you use a Python environment (or conda
environment) and give it a easy to remember name *e.g.* ``cellpy``.

You also need the typical scientific python pack, including ``numpy``,
``scipy``, and ``pandas``. It is recommended that you at least install
``scipy`` before you install ``cellpy`` (the main benefit being that you
can use ``conda`` so that you don’t have to hassle with missing
C-compilers if you are on an Windows machine).


Install a couple of other dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should also install some additional dependencies:

``pytables`` is needed for working with the hdf5 files (the cellpy-files):

.. code:: bash

   conda install -c conda-forge pytables

If you would like to use some of the fitting routines in ``cellpy``, you
will need to install ``lmfit``:

.. code:: bash

   conda install -c conda-forge lmfit


Another tool that is really handy is Jupyter. And the plotting library
bundle holoviz. You might already have them installed. If not, I recommend
that you look at their documentation (google it) and install them. You can most
likely use the same method as for pytables etc.

Note! In addition to the requirements set in the ``setup.py`` file, you
will also need a Python ODBC bridge for loading .res-files from Arbin
testers. And possible also other *‘too-be-implemented’* file formats. I
recommend `pyodbc <https://github.com/mkleehammer/pyodbc/wiki>`__ that
can be installed from conda forge or using pip.

.. code:: bash

   conda install -c conda-forge pyodbc

For reading .res-files
(which actually are in a Microsoft Access format) you also need a driver
or similar to help your ODBC bridge accessing it. A small hint for
Windows users: if you don’t have one of the most recent Office version,
you might not be allowed to install a driver of different bit than your
office version is using (the installers can be found
`here <https://www.microsoft.com/en-US/download/details.aspx?id=13255>`__).
Also remark that the driver needs to be of the same bit as your Python
(so, if you are using 32 bit Python, you will need the 32 bit driver).

For POSIX systems, I have not found any suitable drivers. Instead,
``cellpy`` will try to use ``mdbtools``\ to first export the data to
temporary csv-files, and then import from those csv-file (using the
``pandas`` library). You can install ``mdbtools`` using your systems
preferred package manager (*e.g.* ``apt-get install mdbtools``).

The tea spoon explanation
-------------------------

If you are used to installing stuff from the command line (or shell),
then things might very well run smoothly. However, a considerable
percentage of us don’t feel exceedingly comfortable installing things by
writing commands inside a small black window. Let’s face it; we belong
to the *point-and-click* (or *double-click*) generation, not the
*write-cryptic-commands* generation. So, hopefully without insulting the
savvy, here is a “tea-spoon explanation”

Install a scientific stack of python 3.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the words “virtual environment” or “miniconda” don’t ring any bells,
you should install the Anaconda scientific Python distribution. Go to
`www.anaconda.com <https://www.anaconda.com/>`__ and select the
Anaconda distribution (press the ``Download Now`` button). And no, don´t
select python 2.7. Use at least python 3.6. And select the 64 bit version
(if you fail at installing the 64 bit version, then you can try the
weaker 32 bit version). Download it and let it install.

Create a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step can be omitted (but its not necessary very smart to do so).
Create a virtual conda environment called ``my_cellpy`` (the name is not
important, but it should be a name you are able to remember).


Open up a command window (you can find a command window on Windows by
*e.g* pressing the Windows button + r and typing ``cmd.exe``), or even better,
open up "anaconda prompt". Then type

.. code:: bash

   conda create -n my_cellpy

Then activate your environment:

.. code:: bash

   conda activate my_cellpy

If you get an error message, then it could be that your Python version is
not available for you (maybe you installed as root?). If you were using
the command window on windows, try to locate the “anaconda prompt” program and run that
instead.

Install ``cellpy``
~~~~~~~~~~~~~~~~~~

.. code:: bash

   conda install -c conda-forge cellpy

Note that the bin version matters some times, so try
to make a mental note of what you selected (for
example, if you plan to use the Microsoft Access odbc driver, and it is
32-bit, you probably should chose to install an 32-bit python version
(see next sub-chapter)).

If you don't have the newest office suit, you might need to install
the Microsoft Access odbc driver which can be downloaded from `this
page <https://www.microsoft.com/en-US/download/details.aspx?id=13255>`__


Check your installation
~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to check if ``cellpy`` has been installed, is to issue
the command for printing the version number to the screen

.. code:: bash

   cellpy info --version

If the program prints the expected version number, you probably
succeeded. If it crashes, then you will have to retrace your steps, redo
stuff and hope for the best. If it prints an older (lower) version
number than you expect, it is a big chance that you have installed it
earlier, and what you would like to do is to do an ``upgrade`` instead
of an ``install``

.. code:: bash

   pip install --upgrade cellpy

It could also be that you want to install a pre-release (a version that
is so bleeding edge that it ends with a alpha or beta release
identification, *e.g.* ends with .b2). Then you will need to add the
–pre modifier

.. code:: bash

   pip install --pre cellpy

To run a more complete check of your installation, there exist a
``cellpy`` sub-command than can be helpful

.. code:: bash

   cellpy info --check


The ``cellpy`` command to your rescue
-------------------------------------

To help installing and controlling your ``cellpy`` installation, a CLI
is provided with four main commands, including ``info`` for getting
information about your installation, and ``setup`` for helping you to
set up your installation and writing a configuration file.

To get more information, you can issue

.. code:: bash

   cellpy --help

This will out-put some (hopefully) helpful text

.. code:: bash

   Usage: cellpy [OPTIONS] COMMAND [ARGS]...

   Options:
     --help  Show this message and exit.

   Commands:
      edit   Edit your cellpy config file.
      info   This will give you some valuable information about your cellpy.
      new    Will in the future be used for setting up a batch experiment.
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

Using the ``cellpy`` command for your first time setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you have installed ``cellpy`` it is highly recommended that you
create an appropriate configuration file and create folders for raw
data, cellpy-files, logs, databases and output data (and inform
``cellpy`` about it)

.. code:: bash

   cellpy setup -i

The ``-i`` option makes sure that the setup is done interactively.
The program will ask you about where specific folders are, *e.g.* where
you would like to put your outputs and where your cell data files are
located. If the folders don’t exist, ``cellpy`` will try to create them.a

If you want to specify a root folder different from the default (your HOME
folder), you can use the ``-d`` option *e.g.*
``cellpy setup -i -d /Users/kingkong/cellpydir``

.. note::

    If you don't choose the ``-i`` option, you can always edit your configurations
    directly in the cellpy configuration file (that should be located inside your
    home directory on posix or Documents folder on windows).

When you have answered all your questions, a configuration file will be
made and saved to your home directory. You can always issue
``cellpy info -l`` to find out where your configuration file is located
(it’s written in YAML format and it should be relatively easy to edit it
in a text editor)

Running your first script
-------------------------

As with most software, you are encouraged to play a little with it. I
hope there are some useful stuff in the code repository (for example in
the `examples
folder <https://github.com/jepegit/cellpy/tree/master/examples>`__).

.. note::
    The ``cellpy pull`` command can assist in downloading
    both examples and tests.

Let's start by a trying to import ``cellpy`` in an interactive Python session.
If you have an icon to press to start up the Python in interactive mode,
do that (it could also be for example an ipython console or a
Jupyter Notebook).
You can also start an interactive Python session
if you are in your terminal window of command window by just writing ``python``
and pressing enter.

Once inside Python, try issuing ``import cellpy``. Hopefully you should not see
any error-messages.

.. code-block:: python

    Python 3.6.7 |Anaconda, Inc.| (default, Oct 23 2018, 14:01:38)
    [GCC 4.2.1 Compatible Clang 4.0.1 (tags/RELEASE_401/final)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import cellpy
    >>>

Nothing bad happened this time. If you got an error message, try to interpret
it and check if you have skipped any steps in this tutorial. Maybe you are
missing the ``box`` package? if so, go out of the Python interpreter if you
started it in your command window, or open another command window and write

.. code:: bash

    pip install python-box

and try again.

Now let's try to be a bit more ambitious. Start up python again if you not
still running it and try this:

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

For example: If you want to use the highly popular ``cellpy.utils.batch``
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
