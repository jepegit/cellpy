=== "uv (recommended)"

    [uv](https://docs.astral.sh/uv/) is a single program that installs into your
    user folder (no admin rights) and can fetch Python 3.13 for you. Install it
    once:

    ```console
    # Windows (PowerShell)
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    Then, in the folder you want to work in:

    ```console
    uv venv --python 3.13
    uv pip install "cellpy[batch,legacy-files]"
    ```

    Run commands with `uv run`, for example `uv run cellpy setup`, or activate
    `.venv` first (`.venv\Scripts\activate` on Windows,
    `source .venv/bin/activate` elsewhere).

=== "pip"

    Needs Python 3.13 or newer (for example from [python.org](https://www.python.org/downloads/)).

    ```console
    python -m venv .venv
    .venv\Scripts\activate          # Windows; elsewhere: source .venv/bin/activate
    python -m pip install "cellpy[batch,legacy-files]"
    ```

=== "conda"

    ```console
    conda install -c conda-forge cellpy
    ```

    The conda-forge package already includes plotting, Jupyter and HDF5.

The `[batch]` part adds plotting and Jupyter; `[legacy-files]` adds PyTables so
you can read and write the old `.h5` cellpy format. Both come as ready-built
wheels (HDF5 is bundled), so no compiler or conda is needed. Plain
`cellpy` without extras also works, but it can't plot or open `.h5` cellpy
files.
