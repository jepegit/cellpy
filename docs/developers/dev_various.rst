=======
Various
=======



Using ``pytest`` fixtures
-------------------------

Retrieve constants during tests
...............................

There is a fixture in ``conftest.py`` aptly named ``parameters`` making all the variables defined in ``fdv.py`` accessible for the
tests. So, please, add additional parameter / constant by editing the ``fdv.py`` file.

Other
.....

You can check the ``conftest.py`` file to see what other fixtures are available.

Example
.......

.. code-block:: python

    from cellpy import prms

    # using the ``parameters`` and the ``cellpy_data_instance`` fixtures.

    def test_set_instrument_selecting_default(cellpy_data_instance, parameters):
        prms.Instruments.custom_instrument_definitions_file = parameters.custom_instrument_definitions_file
        cellpy_data_instance.set_instrument(instrument="custom")

Adding another config parameter
-------------------------------

#. Edit ``prms.py``
#. Check / update the ``internal_settings.py`` file as well to ensure that copying /
   splitting ``cellpy`` objects behaves properly.
#. Check / update the ``.cellpy_prms_default.conf`` file

The relevant files are located in the ``parameters`` folder:

.. code-block:: batch

    cellpy/
        parameters/
            .cellpy_prms_default.conf
            prms.py
            internal_settings.py


Installing `pyodbc` on Mac (no `conda`)
---------------------------------------

If you do not want to use `conda`, you might miss a couple of libraries.

The easiest fix is to install `uniuxodbc` using `brew` as explained in
`Stack Overflow #54302793 <https://stackoverflow.com/questions/54302793/
dyld-library-not-loaded-usr-local-opt-unixodbc-lib-libodbc-2-dylib>`_.

