# Installation

cellpy is available on Windows, macOS, and Linux. Prefer **conda** when you want
the scientific stack and awkward native deps handled for you; use **pip** when
you want a lean install and can manage system packages yourself.

After installing, continue to [Setup and configuration](configuration.md) and
[Check your installation](checkup.md).

## Install by platform

=== ":fontawesome-brands-windows: Windows"

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

    This pulls in the critical dependencies (and Jupyter, which is handy for the
    tutorials). Install into a virtual environment if you can.

    ??? tip "New to Python? Teaspoon path"

        1. Install [Miniconda or Anaconda](https://www.anaconda.com/) (64-bit,
           Python 3.11+).
        2. Open **Anaconda Prompt** and create an environment:

           ```console
           conda create -n cellpy python=3.13
           conda activate cellpy
           ```

        3. Install cellpy:

           ```console
           conda install -c conda-forge cellpy
           ```

        Bitness matters for Arbin `.res` (Access) drivers: match the driver to
        your Python build (32- vs 64-bit).

    **Pip**

    ```console
    python -m pip install cellpy
    ```

    On Windows, packages such as `tables` (HDF5) can be awkward with pip. Prefer
    conda, or create an env from the repo
    [environment.yml](https://github.com/jepegit/cellpy/blob/master/environment.yml)
    first.

    !!! note "Arbin `.res` files"
        `.res` files are Microsoft Access databases. You need an Access /
        ACE ODBC driver that matches your Python bitness
        ([Microsoft download](https://www.microsoft.com/en-us/download/details.aspx?id=54920)).
        If loading fails, try:

        ```console
        python -m pip install sqlalchemy-access
        ```

=== ":fontawesome-brands-apple: macOS"

    **System packages**

    For Arbin `.res` support, cellpy uses **mdbtools** to export to temporary CSV
    (there is no Access ODBC path like on Windows). Also install HDF5 libs if you
    plan to build `tables` with pip:

    ```console
    brew install mdbtools hdf5 c-blosc
    ```

    Apple Silicon (Homebrew prefixes) — if `tables` fails to build under pip:

    ```console
    export HDF5_DIR=/opt/homebrew/opt/hdf5
    export BLOSC_DIR=/opt/homebrew/opt/c-blosc
    python -m pip install cython tables
    ```

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

    **Pip**

    ```console
    python -m pip install cellpy
    ```

    Use a virtual environment (`python -m venv .venv` or conda env).

=== ":fontawesome-brands-linux: Linux"

    **System packages**

    For Arbin `.res` support, cellpy uses **mdbtools** to export to temporary CSV
    (there is no Access ODBC path like on Windows). Ubuntu/Debian example, plus
    common pip build deps:

    ```console
    sudo apt update
    sudo apt-get install -y mdbtools unixodbc-dev libhdf5-serial-dev
    ```

    Other distros: install the equivalent packages with your package manager.

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

    **Pip**

    ```console
    python -m pip install cellpy
    ```

    Prefer a virtual environment. Without sudo, try the same `apt` packages in a
    user/container image, or stick to conda.

## Installation from sources

Clone the public repository:

```console
git clone https://github.com/jepegit/cellpy.git
cd cellpy
```

Recommended for contributors (see [CONTRIBUTING.md](https://github.com/jepegit/cellpy/blob/master/CONTRIBUTING.md)):

```console
uv sync
```

Or with conda + editable install:

```console
conda env create -f environment.yml
conda activate cellpy
python -m pip install -e .
```

## Dependencies

Conda and `environment.yml` / the project lockfile (`uv.lock`, driven by
`pyproject.toml`) install what you need for normal use. Highlights:

| Need | Packages / notes |
| --- | --- |
| Core science stack | `numpy`, `scipy`, `pandas` |
| cellpy files (HDF5 path) | `tables` (PyTables) |
| Fitting helpers | `lmfit` |
| Templates | `jinja2-time`, and `git` on `PATH` |
| Tutorials / notebooks | `jupyter`, `seaborn`, `plotly` |

Optional extras and plotting backends evolve with the release — prefer the
conda-forge package or the repo env file over hand-picking versions.
