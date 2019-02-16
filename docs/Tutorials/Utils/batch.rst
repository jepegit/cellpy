Using the batch utilities
-------------------------

The steps given in this tutorial describes how to use the new version of the
batch utility. The part presented here is chosen such that it resembles how
the old utility worked. However, under the hood, the new batch utility is very
different from the old. A more detailed guide will come soon.

So, with that being said, here is the promised description.

Starting (setting things up)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jupyter Notebooks is the recommended "tool" for running the cellpy batch
feature. The first step is to import the ``cellpy.utils.batch.Batch`` class from
``cellpy``.  The ``Batch`` class is a utility class for
pipe-lining batch processing of cell cycle data.


.. code-block:: python

    from cellpy.utils import batch
    from cellpy import prms
    from cellpy import prmreader


The next step is to initialize it:

.. code-block:: python

    project = "experiment_set_01"
    name = "new_exiting_chemistry"
    batch_col = "b01"
    b = batch.init(name, project, batch_col=batch_col)

and set some parameters that `Batch` needs:

.. code-block:: python

    # setting additional parameters if the defaults are not to your liking:
    b.experiment.export_raw = True
    b.experiment.export_cycles = True
    b.experiment.export_ica = True
    b.experiment.all_in_memory = True  # store all data in memory, defaults to False
    b.save_cellpy_file = True

    b.force_raw_file = False
    b.force_cellpy_file = True

Extracting meta-data
~~~~~~~~~~~~~~~~~~~~

The next step is to extract and collect the information needed from your data-base into a DataFrame,
and create an appropriate folder structure (`outdir/project_name/batch_name/raw_data`)

.. code-block:: python

    # load info from your db and write the journal pages
    b.create_info_df()
    b.create_folder_structure()


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
