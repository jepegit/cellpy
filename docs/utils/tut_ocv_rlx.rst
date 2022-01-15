Plotting selected Open Circuit Relaxation points
------------------------------------------------

.. code:: python

    # assuming b is a cellpy.utils.batch.Batch object

    from cellpy.utils.batch_tools.batch_analyzers import OCVRelaxationAnalyzer
    # help(OCVRelaxationAnalyzer)

    print(" analyzing ocv relaxation data ".center(80, "-"))
    analyzer = OCVRelaxationAnalyzer()
    analyzer.assign(b.experiment)
    analyzer.direction = "down"
    analyzer.do()
    dfs = analyzer.last
    df_file_one, _df_file_two = dfs

    # keeping only the columns with voltages
    ycols = [col for col in df_file_one.columns if col.find("point")>=0]

    # removing the first ocv rlx (relaxation before starting cycling)
    df = df_file_one.iloc[1:, :]
    # tidy format
    df = df.melt(
        id_vars = "cycle", var_name="point", value_vars=ycols,
        value_name="voltage"
    )

    # using holoviews for plotting
    curve = hv.Curve(
        df, kdims=["cycle", "point"],
        vdims="voltage"
    ).groupby("point").overlay().opts(xlim=(1,10), width=800)



Open Circuit Relaxation modeling
--------------------------------

TODO.
