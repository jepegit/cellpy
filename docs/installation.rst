.. highlight:: shell

============
Installation
============


Stable release
--------------

To install ``cellpy``, run this command in your terminal:

.. code-block:: console

    $ pip install cellpy

This is the preferred method to install ``cellpy``, as it will always install the most recent stable release.

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

Several of the requirements are a bit difficult to install, in particular the packages `scipy` `numpy` and `pytables`.
The recommended way is to use conda, e.g.:

.. code-block:: console

    $ conda install scipy numpy pytables


If this is the first time you install ``cellpy``, it is recommended that you run the setup script:

.. code-block:: console

    $ cellpy setup

This will install a ``_cellpy_prms_USER.config`` file in your home directory (USER = your user name).
Edit this file and save it as ``_cellpy_prms_OTHERNAME.conf`` to prevent it from being written
over in case the setup script is run on a later occasion.

You can restore your prms-file by running ``cellpy setup`` if needed (i.e. get a copy of the default file
copied to your user folder).

.. note:: At the moment, I have not really figured out how to implement and install something for reading
    access database files on other operating systems than windows. So, for now, I guess ``cellpy`` only will
    work on windows (and automatic building with Travis gets challenging).


From sources
------------

The sources for ``cellpy`` can be downloaded from the `Github repo`_.

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
