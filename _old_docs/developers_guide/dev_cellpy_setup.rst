Getting ready to develop
========================

Get the code
------------

Details of how to get the code can be found in the ``contributing`` chapter.
If you are reading this, you have probably already done this step.

You also need to work a little bit within the terminal. If you are not familiar with
this, you should try to get some basic knowledge on that before you continue.

And, you will need to have a IDE (integrated development environment) installed.
Good alternatives are
PyCharm (https://www.jetbrains.com/pycharm/) and
VSCode (https://code.visualstudio.com/).

Install python 3.9 or higher
----------------------------

There are many ways to install python. We recommend using the Miniconda distribution.
You can download it from here: https://docs.conda.io/en/latest/miniconda.html

    From the conda website:
    *"Miniconda is a free minimal installer for conda. It is a small, bootstrap version of Anaconda
    that includes only conda, Python, the packages they depend on, and a small number of other useful
    packages, including pip, zlib and a few others."*

The main benefit of using conda is that it makes it easy to install and manage packages and
environments. It also makes it easy to install packages that are not available on PyPI (the
Python Package Index), including for example ``pandoc`` which is needed to build the documentation.


Create a development environment
--------------------------------

Once you have installed conda, you should create a new environment for developing ``cellpy``. Take a
look at the `documentation for conda`_ to learn more about environments and how to use them if you
are not familiar with this concept.

The easiest way to create a working environment is to use the ``dev_environment.yml`` file in the
root of the ``cellpy`` repository. This will generate an environment called ``cellpy_dev`` with all the
packages needed to develop ``cellpy``.
You can create the environment by running the following command in a terminal::

    conda env create -f dev_environment.yml

You can then activate the environment by running::

    conda activate cellpy_dev

Next, you need to install ``cellpy`` in development mode. This is done by running the following from
the root folder of ``cellpy``::

    python -m pip install -e . # the dot is important!

Installing ``cellpy`` in development mode means that you can edit the code and the changes
will be reflected when you import ``cellpy`` in python. This is very useful when developing code,
since you can test your changes without having to reinstall the package every time you make a change.

As a final check, you should check if the tests don't fail (still being in the root directory of ``cellpy``)::

    pytest .

Fingers crossed! If the tests pass, you are ready to start developing!

.. links

.. _documentation for conda: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

