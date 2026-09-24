=== "pip"

    ```console
    python -m pip install "cellpy[batch]"
    ```

    The `[batch]` part adds plotting and Jupyter. Plain `pip install cellpy`
    also works, but it can't draw plots.

=== "conda"

    ```console
    conda install -c conda-forge cellpy
    ```

    The conda-forge package already includes plotting and Jupyter, and handles
    awkward native dependencies such as HDF5 for you.
