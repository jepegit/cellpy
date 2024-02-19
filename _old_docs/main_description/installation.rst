.. highlight:: shell

============
Installation
============
``cellpy`` is available on Windows and Linux and can be installed using ``pip`` or ``conda``, or can be installed from source.


To make sure all the dependencies are installed correctly

If you are (relatively) new to installing python packages, please jump to the
getting started tutorial (:ref:`getting-started`)
for an opinionated step-by-step procedure.

Stable release
==============

Conda
-----

Usually, the easiest way to install ``cellpy`` is by using conda:

.. code-block:: console

    $ conda install cellpy --channel conda-forge


This will also install all of the critical dependencies, as well as ``jupyter``
that comes in handy when working with ``cellpy``.


Pip
---

If you would like to install only ``cellpy``, you should install using pip.
A small warning if you are on Windows: ``cellpy`` uses several packages
that are a bit cumbersome to install on windows (e.g. ``scipy``, ``numpy`` and ``pytables`` ).

Install ``cellpy`` by running this command in your terminal:

.. code-block:: console

    $ python -m pip install cellpy


You can install pre-releases by adding the ``--pre`` flag.

If you are on Windows and plan to work with Arbin files,
we recommend that you try to install `pyodbc`_ (Python ODBC bridge).
Either by using pip or from conda-forge:

.. code-block:: console

    $ python -m pip install pyodbc

or:

.. code-block:: console

    $ conda install -c conda-forge pyodbc

.. _pyodbc: https://github.com/mkleehammer/pyodbc/

Some of the utilities in ``cellpy`` have additional dependencies:

- Using the ``ocv_rlx`` utilities requires ``lmfit`` and ``matplotlib``.
- For using the ``batch`` utilities efficiently, you should install
  ``bokeh``, ``plotly``, and ``matplotlib`` for plotting. Also, ``holoviews``
  is a good tool to have.

If this is the first time you install ``cellpy``, it is recommended
that you run the setup script:

.. code-block:: console

    $ cellpy setup -i

This will install a ``.cellpy_prms_USER.conf`` file in your home directory
(USER = your user name).
Feel free to edit this to fit your needs.

If you are OK with letting ``cellpy`` select your settings, you can omit
the `-i` (interactive mode).

.. hint:: Since ``cellpy`` uses several packages that are a bit cumbersome to
    install on windows, you circumvent this by install one of the ``anaconda`` python
    packages (python 3.9 or above) before installing ``cellpy``.
    Remark, that if you chose ``miniconda``, you need to manually install
    ``scipy``, ``numpy`` and ``pytables`` using ``conda``:

    .. code-block:: console

        $ conda install scipy numpy pytables

.. hint:: It is recommended to run the ``cellpy setup`` command also after
    each time you upgrade ``cellpy``. It will keep the settings you already
    have in your prms-file and, if the newer version
    has introduced some new parameters, it will add those too.

.. hint:: You can restore your prms-file by running ``cellpy setup -r`` if needed
    (*i.e.* get a copy of the default file copied to your user folder).

.. caution:: Since Arbin (at least some versions) uses access database files, you
    will need to install ``pyodbc``, a python ODBC bridge that can talk to database
    files. On windows, at least if you don´t have a newer version of office 365,
    you  most likely need to use Microsoft's dll for handling access
    database formats, and you might run into 32bit *vs.* 64bit issues.
    The simplest solution is to have the same "bit" for python and
    the access dll (or office). More advanced options are explained in more details
    in the getting-started tutorial. For Posix-type systems, you will need to download
    and install ``mdbtools``. If you are on Windows and you cannot get your
    ``pyodbc`` to work, you can try the same there also (search for Windows
    binaries and set the appropriate settings in your ``cellpy`` config file).


From sources
============

The sources for ``cellpy`` can be downloaded from the `Github repo`_.

You can clone the public repository by:

.. code-block:: console

    $ git clone git://github.com/jepegit/cellpy


Once you have a copy of the source, you can install in development
mode using pip:

.. code-block:: console

    $ pip install -e .

(assuming that you are in the project folder, *i.e.* the folder that
contains the setup.py file)

Further reading
===============

You can find more information in the Tutorials, particularly
in ':ref:`getting-started`'.

.. _Github repo: https://github.com/jepegit/cellpy



