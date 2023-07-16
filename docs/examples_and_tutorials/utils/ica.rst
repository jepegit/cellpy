.. _utils-ica:

Extracting ica data
===================

.. note:: This chapter would benefit from some more love and care. Any help
    on that would be highly appreciated.


Example: get dq/dv data for selected cycles
-------------------------------------------

This example shows how to get dq/dv data for a selected cycle. The data is
extracted from the cellpy object using the .get_cap method. The method ``dqdv_cycle``
and the ``dqdv`` methods are *cellpy-agnostic* and should work also for other
data sources (e.g. numpy arrays).

.. code:: python

    import matplotlib.pyplot as plt
    from cellpy.utils import ica

    v4, dqdv4 = ica.dqdv_cycle(
        data.get_cap(
            4,
            categorical_column=True,
            method = "forth-and-forth")
    )

    v10, dqdv10 = ica.dqdv_cycle(
        data.get_cap(
            10,
            categorical_column=True,
            method = "forth-and-forth")
    )

    plt.plot(v4,dqdv4, label="cycle 4")
    plt.plot(v10, dqdv10, label="cycle 10")
    plt.legend()

Example: get dq/dv data for selected cycles
-------------------------------------------

This example shows how to get dq/dv data directly from the cellpy object.
This methodology is more convenient if you want to get the data easily from
the cellpy object in a pandas dataframe format.

.. code:: python

    # assuming that b is a cellpy.utils.batch.Batch object

    c = b.experiment.data["20160805_test001_45_cc"]  # get the cellpy object
    tidy_ica = ica.dqdv_frames(c)  # create the dqdv data
    cycles = list(range(1,3)) + [10, 15]
    tidy_ica = tidy_ica.loc[tidy_ica.cycle.isin(cycles), :]  # select cycles


Fitting ica data
----------------

TODO.
