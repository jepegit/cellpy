---
description: "Install cellpy with uv, pip or conda on Windows, macOS, or Linux."
---

# Installation

cellpy is available on Windows, macOS, and Linux. We recommend **uv**: it needs
no admin rights, fetches Python for you, and installs everything from ready-built
wheels, including HDF5 for the old `.h5` cellpy format. Plain **pip** works the
same way if you already have Python 3.13 or newer. **conda** (conda-forge) is
still supported if that is what you use.

After installing, continue to [Setup and configuration](configuration.md) and
[Check your installation](checkup.md). The `cellpy` command you get with the
package is documented in the [command-line reference](../reference/cli.md).

## Quick install

--8<-- "docs/.snippets/quick-install.md"

Then continue with [Setup and configuration](configuration.md). The sections
below cover platform details: Arbin `.res` drivers, system packages, and a
path for people new to Python.

## Install by platform

=== ":fontawesome-brands-windows: Windows"

    **uv (recommended)**

    No admin rights and no system Python needed. In PowerShell:

    ```console
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    Open a new terminal, go to your work folder, and run:

    ```console
    uv venv --python 3.13
    uv pip install "cellpy[batch,legacy-files]"
    uv run cellpy setup
    ```

    ??? tip "New to Python? Teaspoon path"

        1. Install uv with the PowerShell line above, then close and reopen
           the terminal.
        2. Make a folder for your work and go there:

           ```console
           mkdir cellpy_work
           cd cellpy_work
           ```

        3. Create an environment and install cellpy (uv downloads Python 3.13
           itself):

           ```console
           uv venv --python 3.13
           uv pip install "cellpy[batch,legacy-files]"
           ```

        4. Start Jupyter for the tutorials: `uv run jupyter lab`.

        uv's Python is 64-bit, so you need the 64-bit Access driver for Arbin
        `.res` files (see below).

    **Pip**

    With Python 3.13 or newer from [python.org](https://www.python.org/downloads/):

    ```console
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install "cellpy[batch,legacy-files]"
    ```

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

    This pulls in the critical dependencies (and Jupyter, which is handy for the
    tutorials). Install into a conda environment if you can.

    !!! note "Arbin `.res` files"
        `.res` files are Microsoft Access databases. You need an Access /
        ACE ODBC driver that matches your Python bitness
        ([Microsoft download](https://www.microsoft.com/en-us/download/details.aspx?id=54920)).
        This is the same whether you install with uv, pip or conda.

=== ":fontawesome-brands-apple: macOS"

    **System packages**

    For Arbin `.res` support, cellpy uses **mdbtools** to export to temporary CSV
    (there is no Access ODBC path like on Windows):

    ```console
    brew install mdbtools
    ```

    HDF5 is not needed: the `tables` wheel from PyPI bundles it.

    **uv (recommended)**

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv venv --python 3.13
    uv pip install "cellpy[batch,legacy-files]"
    ```

    **Pip**

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install "cellpy[batch,legacy-files]"
    ```

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

=== ":fontawesome-brands-linux: Linux"

    **System packages**

    For Arbin `.res` support, cellpy uses **mdbtools** to export to temporary CSV
    (there is no Access ODBC path like on Windows). `pyodbc` also needs the
    unixODBC runtime library. Ubuntu/Debian example:

    ```console
    sudo apt update
    sudo apt-get install -y mdbtools unixodbc
    ```

    Other distros: install the equivalent packages with your package manager.
    HDF5 is not needed: the `tables` wheel from PyPI bundles it.

    **uv (recommended)**

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv venv --python 3.13
    uv pip install "cellpy[batch,legacy-files]"
    ```

    **Pip**

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install "cellpy[batch,legacy-files]"
    ```

    **Conda**

    ```console
    conda install -c conda-forge cellpy
    ```

??? note "Behind a company proxy or TLS inspection"
    If uv or pip fails with certificate errors, let it use the operating
    system's certificate store: `uv pip install --system-certs ...` (or set
    `UV_SYSTEM_CERTS=1`; older uv versions call it `--native-tls` /
    `UV_NATIVE_TLS`). For pip, point it at the company CA bundle with
    `pip config set global.cert <path-to-ca.pem>`. The hosts that must be
    reachable are `pypi.org` and `files.pythonhosted.org` (plus
    `github.com` for uv to download Python).

## Installation from sources

Clone the public repository:

```console
git clone https://github.com/jepegit/cellpy.git
cd cellpy
```

Recommended (see [CONTRIBUTING.md](https://github.com/jepegit/cellpy/blob/master/CONTRIBUTING.md)):

```console
uv sync
```

This installs cellpy, the `dev` group and `tables` into `.venv`.

Or with conda + editable install:

```console
conda env create -f environment.yml
conda activate cellpy
python -m pip install -e .
```

## Dependencies

`uv` / `pip` (with the extras below), conda, and the project lockfile
(`uv.lock`, driven by `pyproject.toml`) install what you need for normal use. Highlights:

| Need | Packages / notes |
| --- | --- |
| Core science stack | `numpy`, `scipy`, `pandas` |
| Templates | `jinja2-time`, and `git` on `PATH` |

### Optional extras

A plain `pip install cellpy` is deliberately lean: it reads files and computes
summaries, but it cannot plot, and it cannot open cellpy 1.x HDF5 files. Add
what you need:

```console
uv pip install "cellpy[batch,legacy-files]"     # or: python -m pip install ...
```

| Extra | Installs | You need it for |
| --- | --- | --- |
| `batch` | `plotly`, `seaborn`, `kaleido`, `jupyter`, `ipython`, `cellpy-figure` | plotting (the default backend), saving figures as PNG/SVG/PDF, writing a `.cfz` bundle, and the notebook workflow |
| `plotting-mpl` | `matplotlib`, `cellpy-figure` | the matplotlib plotting backend, and writing a `.cfz` bundle |
| `legacy-files` | `tables` (PyTables) | reading and writing the old `.h5` cellpy file format |
| `notebook` | `ipykernel`, `ipython` | running the tutorial notebooks (a subset of `batch`) |
| `fit` | `lmfit` | the fitting helpers |
| `all` | everything above | the lot |

Extras combine: `uv pip install "cellpy[batch,plotting-mpl]"`.

cellpy raises an `OptionalDependencyError` naming the extra when you reach for
a feature you have not installed, so you can start lean and add as you go. The
conda-forge package ships a fuller set already.

Optional extras and plotting backends evolve with the release — install
through the extras rather than hand-picking package versions.
