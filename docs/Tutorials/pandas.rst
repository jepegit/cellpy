Working with the pandas.DataFrame objects directly
==================================================

The ``CellpyData`` object stores the data in several pandas.DataFrame objects.
The easies way to get to the DataFrames is by the following procedure:

.. code-block:: python

    # Assumed name of the CellpyData object: cellpy_data

    # get the 'test':
    cellpy_test = cell_data.dataset
    # cellpy_test is now a cellpy DataSet object (cellpy.readers.cellreader.DataSet)

    # pandas.DataFrame with data vs cycle number (e.g. coulombic efficiency):
    summary = cellpy_test.dfsummary
    # or
    summary = cell_data.dataset_summary

    # pandas.DataFrame with the raw data:
    rawdata = cellpy_test.dfdata
    # or
    raw_data = cellpy_data.dataset_normal

    # pandas.DataFrame with statistics on each step and info about step type:
    step_table = cellpy_test.step_table

    # run_summary = cellpy_test.run_summary
    # This is not implemented yet (overall information like cycle life-time)


You can then manipulate your data with the standard pandas.DataFrame methods
(and pandas methods in general).

.. note::
    At the moment, **CellpyData** objects can store several sets of test-data
    (several 'tests'). They are stored
    in a list. It is not recommended to utilise this
    *'possible to store multiple tests'* feature as it might be
    removed very soon (have not decided upon that yet).

Happy pandas-ing!
