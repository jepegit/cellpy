.. highlight:: shell

============
Installation
============
``cellpy`` is available on (Windows :ref:`_Cellpy_Install_Windows`) and Linux (:ref:`Cellpy_Setup_Linux`)) and can be installed using ``pip``
or ``conda``, or from source (:ref:`_Cellpy_Install_Sources`).

For more details on dependencies, have a look (here :ref:`Cellpy_Dependencies`).

For a tea-spoon explanation on how to install ``cellpy`` on windows, including the
installation of python and setup of virtual environments, (see below
:ref:`Cellpy_Setup_Teaspoon`).

.. _Cellpy_Install_Windows:

Windows
==============

Conda
-----

The easiest way to install ``cellpy`` is by using conda:

.. code-block:: console

    $ conda install cellpy


This will also install all of the critical dependencies, as well as ``jupyter``
that comes in handy when working with ``cellpy``.


In general, we recommend to install ``cellpy`` in a virtual environment.

To make sure your environment contains the correct packages and dependencies
required for running ``cellpy``, you can create an environment based on the available
``environment.yml`` file. Download the
`environment.yml <https://github.com/jepegit/cellpy/blob/master/environment.yml>`_
file and place it in the directory shown in your Anaconda Prompt, and run:

.. code-block:: console

    conda env create -f environment.yml

Then activate your environment:

.. code-block:: console

    conda activate cellpy

and install ``cellpy`` within the environment.


Pip
---

If you would like to install 'only' ``cellpy``, you can use pip:

.. code-block:: console

    $ pip install cellpy


Note that ``cellpy`` uses several packages that are a bit cumbersome to install
on windows (e.g. ``scipy``, ``numpy`` and ``pytables`` ) and when using pip,
you have to take care of this yourself. To make sure to install
all the required dependencies, we recommend to create an environment based
the provided ``environment.yml`` (see installation with conda above):

.. code-block:: console

    $ conda env create -f environment.yml


Pre-releases can be installed by adding the ``--pre`` flag to the installation command:

.. code-block:: console

   python -m pip install --pre cellpy



.. _Cellpy_Install_Linux:


Linux
==============
Conda
-----
This is how to install ``cellpy`` using conda on Linux.
Be aware that you might have to install additional packages.


Pip
---
This is how to install ``cellpy`` using conda on Linux.
Be aware that you might have to install additional packages.

.. _Cellpy_Install_Sources:

Installation from sources
==============

The sources for ``cellpy`` can be downloaded from the `Github repo`_.

You can clone the public repository by:

.. code-block:: console

    $ git clone git://github.com/jepegit/cellpy


To make sure to install all the required dependencies, we recommend
to create an environment based the provided ``environment.yml``:

.. code-block:: console

    $ conda env create -f environment.yml

Once you have a copy of the source, you can install in development
mode using pip:

.. code-block:: console

    $ pip install -e .

(assuming that you are in the project folder, *i.e.* the folder that
contains the setup.py file)


.. _Cellpy_Dependencies:

Fixing dependencies
==============
``cellpy`` relies on a number of other python package and these need
to be installed. Most of these packages are included when installing
``cellpy`` using conda or when creating the environment based on the
``environment.yml`` file as outlined above.

Here is an additional overview on the required dependencies:

Basic dependencies
---

In general, you need the typical scientific python pack, including

- ``numpy``
- ``scipy``
- ``pandas``

Additional dependencies are:

- ``pytables`` is needed for working with the HDF5 files (the cellpy-files):

.. code-block:: console

    conda install -c conda-forge pytables

- ``lmfit`` is required to use some of the fitting routines in ``cellpy``:

.. code-block:: console

    conda install -c conda-forge lmfit

- ``holoviz`` and ``plotly``: plotting library used in several of our example notebooks.

- ``jupyter``: used for tutorial notebooks and in general very useful tool
  for working with and sharing your ``cellpy`` results.

For more details, have a look at the documentation of these packages.

Additional requirements for .res files
---
Note! .res files from Arbin testers are actually in a Microsoft Access format.

**For Windows users:** if you do not have one of the
most recent Office versions, you might not be allowed to install a driver
of different bit than your office version is using (the installers can be found
`here <https://www.microsoft.com/en-US/download/details.aspx?id=13255>`__).
Also remark that the driver needs to be of the same bit as your Python
(so, if you are using 32 bit Python, you will need the 32 bit driver).

**For POSIX systems:** I have not found any suitable drivers. Instead,
``cellpy`` will try to use ``mdbtools``\ to first export the data to
temporary csv-files, and then import from those csv-file (using the
``pandas`` library). You can install ``mdbtools`` using your systems
preferred package manager (*e.g.* ``apt-get install mdbtools``).



.. _Cellpy_Setup_Teaspoon:

The tea-spoon explanation including installation of python
==============

This guide provides step-by-step instructions for installing Cellpy on a Windows system,
especially tailored for beginners.

1. Install a scientific stack of python 3.x
...........................................

If the words “virtual environment” or “miniconda” do not ring any bells,
you should install the Anaconda scientific Python distribution. Go to
`www.anaconda.com <https://www.anaconda.com/>`__ and select the
Anaconda distribution (press the ``Download Now`` button).
Use at least python 3.9, and select the 64 bit version
(if you fail at installing the 64 bit version, then you can try the
weaker 32 bit version). Download it and let it install.

.. caution:: The bin version matters sometimes, so try to make a mental note
    of what you selected. E.g., if you plan to use the Microsoft Access odbc
    driver (see below), and it is 32-bit, you probably should chose to install
    a 32-bit python version).

Python should now be available on your computer, as well as
a huge amount of python packages. And Anaconda is kind enough
to also install an alternative command window called "Anaconda Prompt"
that has the correct settings ensuring that the conda command works
as it should.



2. Create a virtual environment
...............................

A virtual environment is a tool that helps to keep dependencies required by different projects separate by creating isolated
Python environments for them.

Create a virtual conda environment called ``cellpy`` (the name is not
important, but it should be a name you are able to remember) by following
the steps below:

Open up the "Anaconda Prompt" (or use the command window) and type

.. code-block:: console

    conda create -n cellpy

This creates your virtual environment (here called *cellpy*) in which ``cellpy``
will be installed and used.

You then have to activate the environment:

.. code-block:: console

    conda activate cellpy


3. Install ``cellpy``
.....................

To finally install ``cellpy`` in your activated ``cellpy`` environment in the Anaconda Prompt run:

.. code-block:: console

    conda install cellpy

Congratulations, you have (hopefully) successfully installed cellpy.

If you run into problems, doublecheck that all your dependencies are
installed and check your Microsoft Access odbc drivers.






Review and include what is currently written in
https://cellpy.readthedocs.io/en/latest/examples_and_tutorials/basics.html#setting-up-cellpy-on-windows-for-complete-beginners