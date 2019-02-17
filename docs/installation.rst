============
Installation
============


Stable release
--------------

``cellpy`` uses several packages that are a bit cumbersome to install on windows. It is therefore recommended
to install one of the ``anaconda`` python packages (python 3.6 or above) before installing ``cellpy``.
If you chose ``miniconda``, you should install ``scipy``, ``numpy`` and ``pytables`` using ``conda``:

.. code-block:: console

    $ conda install scipy numpy pytables


To install ``cellpy``, run this command in your terminal:

.. code-block:: console

    $ pip install cellpy

You can install pre-releases by adding the ``--pre`` flag.

If you are on Windows and plan to work with Arbin files, we recommend that you try
to install `pyodbc`_ (Python ODBC bridge). Either by using pip or from conda-forge:

.. code-block:: console

    $ pip install pyodbc

or:

.. code-block:: console

    $ conda install -c conda-forge pyodbc

.. _pyodbc: https://github.com/mkleehammer/pyodbc/

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

``cellpy`` uses `setuptools`_, and the developers of `setuptools` recommend notifying the users
the following:

-  if you would like to install ``cellpy`` to somewhere other than the main site-packages directory,
   then you should first install setuptools using the instructions for Custom Installation Locations,
   before installing ``cellpy``.


.. _setuptools: http://setuptools.readthedocs.io/en/latest/

You can also try to install the ``cellpy`` conda-build package (however, we have not tested
it very well yet). Hopefully, this will be the main installation method in not-too-long.

.. code-block:: console

    $ conda config --add channels conda-forge
    $ conda config --add channels jepegit
    $ conda install cellpy

If this is the first time you install ``cellpy``, it is recommended that you run the setup script:

.. code-block:: console

    $ cellpy setup

This will install a ``_cellpy_prms_USER.config`` file in your home directory (USER = your user name).
Edit this file and save it.

You can restore your prms-file by running ``cellpy setup`` if needed (*i.e.* get a copy of the default file
copied to your user folder).

.. note:: Since Arbin (at least some versions) uses access database files, you
    will need to install something that can talk to them, e.g. ``pyodbc`` or
    similar. These most likely need to use Microsoft's dll for handling access
    database formats, and you might run into 32bit vs. 64bit issues. On Windows,
    the simplest solution is to have the same "bit" for python and
    the access dll (or office). For Posix-type systems, you will need to download
    and install ``mdbtools``. If you are on Windows and you cannot get your
    ``pyodbc`` to work, you can try the same there also (search for Windows
    binaries and set the appropriate settings in your cellpy config file).


From sources
------------

The sources for ``cellpy`` can be downloaded from the `Github repo`_.

You can clone the public repository by:

.. code-block:: console

    $ git clone git://github.com/jepegit/cellpy


Once you have a copy of the source, you can install in development mode using pip:

.. code-block:: console

    $ pip install -e .

(assuming that you are in the project folder, i. e. the folder that contains the setup.py file)

.. _Github repo: https://github.com/jepegit/cellpy
