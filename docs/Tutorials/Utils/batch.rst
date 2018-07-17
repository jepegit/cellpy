Using the batch utilities
-------------------------

First a short warning. This version of the batch utility should only be considered as an intermediate solution. A new
batch utility is currently under development (jippi?).

So, with that being said, here is a short description of how to use the current utility.

Starting (setting things up)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jupyter Notebooks is the recommended "tool" for running the cellpy batch feature. The first step is to import
the `cellpy.utils.batch.Batch` class from ``cellpy`` and initialize it. The ``Batch`` class is a utility class for pipe-lining
batch processing of cell cycle data.


.. code-block:: python

    from cellpy.utils import batch
    b = batch.init()
    # you can also give the name of the batch, the project name,
    # the log-level, and the batch column number
    # as parameters to the batch.init function, e.g.
    # b = batch.init("batch_name", "project_name",
    # default_log_level="INFO", batch_col=5)

The next step is to set some parameters that `Batch` needs.

.. code-block:: python

    b.name = "experiment_set_01"
    b.project = "new_exiting_chemistry"

    # set additional parameters if the defaults are not ok:
    b.export_raw = True
    b.export_cycles = True
    b.export_ica = True
    b.save_cellpy_file = True
    b.force_raw_file = False
    b.force_cellpy_file = True

    # you also have access to cellpy´s main parameter structure
    b.prms.Reader.cycle_mode = "cathode"

Extracting meta-data
~~~~~~~~~~~~~~~~~~~~

The next step is to extract and collect the information needed from your data-base into a DataFrame,
and create an appropriate folder structure (`outdir/project_name/batch_name/raw_data`)

.. code-block:: python

    b.create_info_df()
    # or load it from a previous run:
    # filename = "../out_data/experiment_set_01/cellpy_batch_new_exiting_chemistry.json"
    # b.load_info_df(filename)

    b.create_folder_structure()

    # You can view your information DataFrame by the pandas head function:

    b.info_df.head()

Processing data
~~~~~~~~~~~~~~~

To run the processing, you should then use the convenience function ``load_and_save_raw``. This function
loads all your data-files and saves csv-files of the results.

.. code-block:: python

    b.load_and_save_raw()

The next step is to create some summary csv-files (*e.g.* containing charge capacities *vs.* cycle number for
all your data-files) and plot the results.

.. code-block:: python

    b.make_summaries()
    b.plot_summaries()

Now it is time to relax and maybe drink a cup of coffee.
