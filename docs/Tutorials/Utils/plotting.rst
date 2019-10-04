Have a look at the data
-----------------------

Here are some examples how to get a peak at the data. If we need an
interactive plot of the raw-data, we can use the ``plotutils.raw_plot``
function. If we would like to see some statistics for some of the
cycles, the ``plotutils.cycle_info_plot`` is your friend. Let´s start by
importing cellpy and the ``plotutils`` utility:

.. code:: ipython3

    import cellpy
    from cellpy.utils import plotutils

Let´s load some data first:

.. code:: ipython3

    cell = cellpy.get("../testdata/hdf5/20160805_test001_45_cc.h5", mass=0.8)

Here we used the convenience method ``cellpy.get`` to load some
example data. If everything went well, you will see an output approximately
like this:

.. parsed-literal::

    (cellpy) - Making CellpyData class and setting prms
    (cellpy) - Loading cellpy-file: ../testdata/hdf5/20160805_test001_45_cc.h5
    (cellpy) - Setting mass: 0.8
    (cellpy) - Creating step table
    (cellpy) - Creating summary data
    (cellpy) - assuming cycling in anode half-cell (discharge before charge) mode
    (cellpy) - Created CellpyData object


If you have ``holoviews`` installed, you can conjure an
interactive figure:

.. code:: ipython3

    plotutils.raw_plot(cell)


.. image:: Tutorials/Utils/figures/tutorials_utils_plotting_fig1.png


Sometimes it is necessary to have a look at some statistics for each
cycle and step. This can be done using the ``cycle_info_plot`` method:

.. code:: ipython3

    fig = plotutils.cycle_info_plot(
        cell,
        cycle=3,
        use_bokeh=False,
    )



.. image:: Tutorials/Utils/figures/tutorials_utils_plotting_fig2.png

.. note::

    If you chose to work within a Jupyter Notebook, you are advised to
    try some of the web-based plotting tools. For example, you might consider
    installing `holoviz suite. <https://holoviz.org>`_

