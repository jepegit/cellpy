.. highlight:: shell

============
Installation
============


Stable release
--------------

To install `cellpy`, run this command in your terminal:

.. code-block:: console

    $ pip install cellpy

This is the preferred method to install `cellpy`, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/

 `cellpy` uses `setuptools`_, and the developers of `setuptools` recommend notifying the users
the following:

-  if you would like to install `cellpy` to somewhere other than the main site-packages directory,
   then you should first install setuptools using the instructions for Custom Installation Locations,
   before installing `cellpy`.


.. _setuptools: http://setuptools.readthedocs.io/en/latest/

If this is the first time you install cellpy, it is recommended that you run the setup script:

.. code-block:: console

    $ cellpy setup

This will install a `_cellpy_prms_default.ini` file in your home directory. Edit this file and
save it as `_cellpy_prms_some_other_name.ini` to prevent it from being written over in case
the setup script is run on a later occasion.


From sources
------------

The sources for `cellpy` can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/jepegit/cellpy

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/jepegit/cellpy/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/jepegit/cellpy
.. _tarball: https://github.com/jepegit/cellpy/tarball/master
