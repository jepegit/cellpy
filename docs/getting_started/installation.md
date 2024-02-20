```{highlight} shell
```

# Installation

`cellpy` is available on [Windows](#cellpy_install_windows) and [Linux](#cellpy_install_linux) and can be installed using `pip`
or `conda`, or [installed from sources](#cellpy_install_sources).

For more details on dependencies, have a look at [cellpy dependencies](#cellpy_dependencies).

For a tea-spoon explanation on how to install `cellpy` on Windows, including the
installation of Python and setup of virtual environments, [see below](#cellpy_setup_teaspoon).

After installing `cellpy`, continue to
- [Setup and configuration](configuration.md)
- [Check your cellpy installation](checkup.md)

(cellpy_install_windows)=
## Installation on Windows

### Conda
The easiest way to install cellpy is by using conda:

```console
$ conda install -c conda-forge cellpy
```

This will also install all of the critical dependencies, as well as `jupyter`
that comes in handy when working with cellpy.

In general, we recommend to install cellpy in a virtual environment (if
you do not know what this means, have a look the [teaspoon explanation](#cellpy_setup_teaspoon)).

### Pip

If you would like to install 'only' cellpy, you can use pip:

```console
$ pip install cellpy
```

Note that `cellpy` uses several packages that are a bit cumbersome to install
on windows (e.g. `pytables`) and when using pip, you have to take care of this yourself.

:::{hint}
You can take care of most of the dependencies by creating a virtual environment
based on the provided [environment.yml](https://github.com/jepegit/cellpy/blob/master/environment.yml) file.
:::

(cellpy_install_linux)=
## Installation on Linux

### Conda

This is how to install `cellpy` using conda on Linux.
Be aware that you might have to install additional packages.

This includes, e.g., `libobdc`, that can be installed on Ubuntu like this:

```console
$ sudo apt update
$ sudo apt install unixodbc-dev
```

### Pip

This is how to install `cellpy` using pip on Linux.
Be aware that you might have to install additional packages.

(cellpy-install-sources)=

## Installation from sources

The sources for `cellpy` can be downloaded from the [Github repo].

You can clone the public repository by:

```console
$ git clone git://github.com/jepegit/cellpy
```

To make sure to install all the required dependencies, we recommend
to create an environment based the provided
[environment.yml](https://github.com/jepegit/cellpy/blob/master/environment.yml) file:

```console
$ conda env create -f environment.yml
```

Once you have a copy of the source, you can install cellpy using pip:

```console
$ pip install -e .
```

(assuming that you are in the project folder, *i.e.* the folder that
contains the setup.py file)

(cellpy_dependencies)=
## Dependencies

`cellpy` relies on a number of other python package and these need
to be installed. Most of these packages are included when installing
`cellpy` using conda or when creating the environment based on the
[environment.yml](https://github.com/jepegit/cellpy/blob/master/environment.yml) file.

Here is an additional overview on the required dependencies:

### Basic dependencies

In general, you need the typical scientific python pack, including

- `numpy`
- `scipy`
- `pandas`

Additional dependencies are:

- `pytables` is needed for working with the HDF5 files (the cellpy-files):

```console
conda install -c conda-forge pytables
```

- `lmfit` is required to use some of the fitting routines in `cellpy`:

```console
conda install -c conda-forge lmfit
```

- `holoviz` and `plotly`: plotting library used in several of our example notebooks.
- `jupyter`: used for tutorial notebooks and in general very useful tool
  for working with and sharing your `cellpy` results.

For more details, have a look at the documentation of these packages.

### Additional requirements for .res files

:::{note}
Note! .res files from Arbin testers are actually in a Microsoft Access format.
:::

- **For Windows users:** if you do not have one of the most recent Office
  versions, you might not be allowed to install a driver
  of different bit than your office version is using (the installers can be found
  [here](https://www.microsoft.com/en-US/download/details.aspx?id=13255)).
  Also remark that the driver needs to be of the same bit as your Python
  (so, if you are using 32 bit Python, you will need the 32 bit driver).

If you run into issues when trying to load .res files, try to install
`sqlalchemy-access`:

```console
pip install sqlalchemy-access
```

- **For POSIX systems:** I have not found any suitable drivers. Instead,
  `cellpy` will try to use `mdbtools` to first export the data to
  temporary csv-files, and then import from those csv-file (using the
  `pandas` library). You can install `mdbtools` using your systems
  preferred package manager (*e.g.* `apt-get install mdbtools`).

(cellpy_setup_teaspoon)=
## The tea-spoon explanation including installation of Python

This guide provides step-by-step instructions for installing cellpy on a Windows system,
especially tailored for beginners.

### 1. Install a scientific stack of Python 3.x

If the words “virtual environment” or “miniconda” do not ring any bells,
you should install the Anaconda scientific Python distribution. Go to
[www.anaconda.com](https://www.anaconda.com/) and select the
Anaconda distribution (press the `Download Now` button).
Use at least python 3.9, and select the 64 bit version
(if you fail at installing the 64 bit version, then you can try the
weaker 32 bit version). Download it and let it install.

:::{caution}
The bin version matters sometimes, so try to make a mental note
of what you selected. E.g., if you plan to use the Microsoft Access odbc
driver (see below), and it is 32-bit, you probably should chose to install
a 32-bit python version).
:::

Python should now be available on your computer, as well as
a huge amount of python packages. And Anaconda is kind enough
to also install an alternative command window called "Anaconda Prompt"
that has the correct settings ensuring that the conda command works
as it should.

### 2. Create a virtual environment

A virtual environment is a tool that helps to keep dependencies required by different projects separate by creating isolated
Python environments for them.

Create a virtual conda environment called `cellpy` (the name is not
important, but it should be a name you are able to remember) by following
the steps below:

Open up the "Anaconda Prompt" (or use the command window) and type

```console
conda create -n cellpy
```

This creates your virtual environment (here called *cellpy*) in which `cellpy`
will be installed and used.

You then have to activate the environment:

```console
conda activate cellpy
```

### 3. Install cellpy

To finally install `cellpy` in your activated `cellpy` environment in the Anaconda Prompt run:

```console
conda install -c conda-forge cellpy
```

Congratulations, you have (hopefully) successfully installed cellpy.

If you run into problems, doublecheck that all your dependencies are
installed (see [here](#cellpy_dependencies)) and check your Microsoft Access odbc drivers.
