More about the ``cellpy.get`` method
------------------------------------

The following keyword arguments is current supported by ``cellpy.get``::

    # from the docstring:
    Args:
        filename (str, os.PathLike, OtherPath, or list of raw-file names): path to file(s) to load
        instrument (str): instrument to use (defaults to the one in your cellpy config file)
        instrument_file (str or path): yaml file for custom file type
        cellpy_file (str, os.PathLike, OtherPath): if both filename (a raw-file) and cellpy_file (a cellpy file)
            is provided, cellpy will try to check if the raw-file is has been updated since the
            creation of the cellpy-file and select this instead of the raw file if cellpy thinks
            they are similar (use with care!).
        logging_mode (str): "INFO" or "DEBUG"
        cycle_mode (str): the cycle mode (e.g. "anode" or "full_cell")
        mass (float): mass of active material (mg) (defaults to mass given in cellpy-file or 1.0)
        nominal_capacity (float): nominal capacity for the cell (e.g. used for finding C-rates)
        loading (float): loading in units [mass] / [area]
        area (float): active electrode area (e.g. used for finding the areal capacity)
        estimate_area (bool): calculate area from loading if given (defaults to True)
        auto_pick_cellpy_format (bool): decide if it is a cellpy-file based on suffix.
        auto_summary (bool): (re-) create summary.
        units (dict): update cellpy units (used after the file is loaded, e.g. when creating summary).
        step_kwargs (dict): sent to make_steps
        summary_kwargs (dict): sent to make_summary
        selector (dict): passed to load (when loading cellpy-files).
        testing (bool): set to True if testing (will for example prevent making .log files)
        **kwargs: sent to the loader

Reading a cellpy file:

.. code-block:: python

    c = cellpy.get("my_cellpyfile.cellpy")
    # or
    c = cellpy.get("my_cellpyfile.h5")

Reading anode half-cell data from arbin sql:

.. code-block:: python

    c = cellpy.get("my_cellpyfile", instrument="arbin_sql", cycle_mode="anode")
    # Remark! if sql prms are not set in your config-file you have to set them manually (e.g. setting values in
    #    prms.Instruments.Arbin.VAR)

Reading data obtained by exporting csv from arbin sql using non-default delimiter sign:

.. code-block:: python

    c = cellpy.get("my_cellpyfile.csv", instrument="arbin_sql_csv", sep=";")

Reading data obtained by exporting a csv file from Maccor
using a sub-model (this example uses one of the models already available inside ``cellpy``):

.. code-block:: python

    c = cellpy.get(filename="name.txt", instrument="maccor_txt", model="one", mass=1.0)

Reading csv file using the custom loader where the format definitions are given in a user-supplied
yaml-file:

.. code-block:: python

    c = cellpy.get(filename="name.txt", instrument_file="my_custom_file_format.yml")

REWRITE THIS (should use get instead): For convenience, ``cellpy`` also has a method that can be used to select whether-or-not to load
directly from the raw-file.
Using the ``loadcell`` method, you can specify both the raw
file name(s) and the cellpy file name, and
``cellpy`` will check if the raw file(s) is/are updated since
the last time you saved the cellpy file - if not,
then it will load the cellpy file instead (this is usually much faster
than loading the raw file(s)).
You can also input the masses and enforce that it creates a
summary automatically.

.. code-block:: python

    cell_data.loadcell(raw_files=[raw_files], cellpy_file=cellpy_file,
                           mass=[electrode_mass], summary_on_raw=True,
                           force_raw=False)

    if not cell_data.check():
        print("Could not load the data")



Working with external files
---------------------------
To work with external files you will need to set some environment variables. This can most
easily be done by creating a file called ``.env_cellpy`` in your user directory (e.g. ``C:\Users\jepe``)::

    # content of .env_cellpy
    CELLPY_PASSWORD=1234
    CELLPY_KEY_FILENAME=C:\\Users\\jepe\\.ssh\\id_key
    CELLPY_HOST=myhost.com
    CELLPY_USER=jepe

You can then load the file using the ``cellpy.get`` method by providing the full path to the file,
including the protocol (e.g. ``scp://``) and the user name and host (e.g. ``jepe@myhost.com``):

.. code-block:: python

    # assuming appropriate `.env_cellpy` file is present
    raw_file = "scp://jepe@myhost.com/path/to/file.txt"
    c = cellpy.get(filename=raw_file, instrument="maccor_txt", model="one", mass=1.0)

cellpy will automatically download the file to a temporary directory and read it.

Save / export data
------------------

Saving data to cellpy format is done by the ``CellpyCell.save`` method.
To export data to csv format,
``CellpyCell`` has a method called ``to_csv``.

.. code-block:: python

    # export data to csv
    out_data_directory = r"C:\processed_data\csv"
    # this exports the summary data to a .csv file:
    cell_data.to_csv(out_data_directory, sep=";", cycles=False, raw=False)
    # export also the current voltage cycles by setting cycles=True
    # export also the raw data by setting raw=True
