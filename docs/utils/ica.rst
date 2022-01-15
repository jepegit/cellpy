Extracting ica data
-------------------


Example: get dq/dv data for selected cycles
...........................................

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
...........................................

.. code:: python

    # assuming that b is a cellpy.utils.batch.Batch object

    data = b.experiment.data["20160805_test001_45_cc"]
    tidy_ica = ica.dqdv_frames(data)
    cycles = list(range(1,3)) + [10, 15]
    tidy_ica = tidy_ica.loc[tidy_ica.cycle.isin(cycles), :]


Fitting ica data
----------------

TODO.
