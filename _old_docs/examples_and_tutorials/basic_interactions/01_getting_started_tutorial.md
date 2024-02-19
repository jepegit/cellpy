(getting-started)=

# The getting started with `cellpy` tutorial (opinionated version)

This tutorial will help you getting started with `cellpy` and
tries to give you a step-by-step recipe. It starts with installation, and you
should select the installation method that best suits your needs (or your level).

(cellpy-setup-standard)=

## How to install and run `cellpy` - the tea spoon explanation for standard users

If you are used to installing stuff from the command line (or shell),
then things might very well run smoothly. If you are not, then you
might want to read through the guide for complete beginners first (see below
{ref}`Cellpy_Setup_Windows`).

### 1. Install a scientific stack of python 3.x

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

This step can be omitted (but its not necessarily smart to do so).
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

### 3. Install `cellpy`

In your activated `cellpy` environment in the Anaconda Prompt if you
chose to make one, or in the base environment if you chose not to, run:

```console
conda install -c conda-forge cellpy
```

Congratulations, you have (hopefully) successfully installed cellpy.

If you run into problems, doublecheck that all your dependencies are
installed and check your Microsoft Access odbc drivers.

(check-cellpy)=

### 4. Check your cellpy installation

The easiest way to check if `cellpy` has been installed, is to issue
the command for printing the version number to the screen

```console
cellpy info --version
```

If the program prints the expected version number, you probably
succeeded. If it crashes, then you will have to retrace your steps, redo
stuff and hope for the best. If it prints an older (lower) version
number than you expect, there is a big chance that you have installed it
earlier, and what you would like to do is to do an `upgrade` instead
of an `install`

```console
python -m pip install --upgrade cellpy
```

If you want to install a pre-release (a version that is so bleeding edge
that it ends with a alpha or beta release identification, *e.g.* ends
with .b2). Then you will need to add the –pre modifier

```console
python -m pip install --pre cellpy
```

To run a more complete check of your installation, there exist a
`cellpy` sub-command than can be helpful

```console
cellpy info --check
```

### 5. Set up `cellpy`

After you have installed `cellpy` it is highly recommended that you
create an appropriate configuration file and folders for raw data,
cellpy-files, logs, databases and output data (and inform `cellpy` about it).

To do this, run the setup command:

```console
cellpy setup
```

To run the setup in interactive mode, use -i:

```console
cellpy setup -i
```

This creates the cellpy configuration file `.cellpy_prms_USERNAME.conf`
in your home directory (USERNAME = your user name) and creates the standard
cellpy_data folders (if they do not exist).
The `-i` option makes sure that the setup is done interactively:
The program will ask you about where specific folders are, *e.g.* where
you would like to put your outputs and where your cell data files are
located. If the folders do not exist, `cellpy` will try to create them.

If you want to specify a root folder different from the default (your HOME
folder), you can use the `-d` option *e.g.*
`cellpy setup -i -d /Users/kingkong/cellpydir`

:::{hint}
You can always edit your configurations directly in the cellpy configuration
file `.cellpy_prms_USER.conf`. This file should be located inside your
home directory, /. in posix and c:usersUSERNAME in not-too-old windows.
:::

### 6. Create a notebook and run `cellpy`

Inside your Anaconda Prompt window, write:

```console
jupyter notebook  # or jupyter lab
```

Your browser should then open and you are ready to write your first cellpy script.

There are many good tutorials on how to work with jupyter.
This one by Real Python is good for beginners:
[Jupyter Notebook: An Introduction](https://realpython.com/jupyter-notebook-introduction/)

(cellpy-setup-windows)=

## Setting up `cellpy` on Windows for complete beginners

This guide provides step-by-step instructions for installing Cellpy on a Windows system,
especially tailored for beginners.

### 1. Installing Python

- First, download Python from the [official website](https://www.python.org/downloads/). Choose the latest version for Windows.

- Run the downloaded installer. On the first screen of the setup, ensure to check the box
  : saying "Add Python to PATH" before clicking "Install Now".

- After installation, you can verify it by opening the Command Prompt (see below) and typing:

  ```
  python --version
  ```

  This command should return the version of Python that you installed.

### 2. Opening Command Prompt

- Press the Windows key, usually located at the bottom row of your keyboard, between the Ctrl and Alt keys.
- Type "Command Prompt" into the search bar that appears at the bottom of the screen when you press the Windows key.
- Click on the "Command Prompt" application to open it.

### 3. Creating a Virtual Environment

A virtual environment is a tool that helps to keep dependencies required by different projects separate by creating isolated
Python environments for them. Here's how to create one:

- Open Command Prompt.

- Navigate to the directory where you want to create your virtual environment using the `cd` command. For example:

  ```
  cd C:\Users\YourUsername\Documents
  ```

- Type the following command and press enter to create a new virtual environment (replace `envname` with the name you want to give to your virtual environment):

  ```
  python -m venv envname
  ```

- To activate the virtual environment, type the following command and press enter:

  ```
  envname\Scripts\activate
  ```

  You'll know it worked if you see `(envname)` before the prompt in your Command Prompt window.

### 4. Installing Jupyter Notebook and matplotlib

Jupyter Notebook is an open-source web application that allows you to create documents containing live code, equations, visualizations,
and text. It's very useful, especially for beginners. To install Jupyter Notebook:

- Make sure your virtual environment is activated.

- Type the following command and press enter:

  ```
  python -m pip install jupyter matplotlib
  ```

### 5. Installing `cellpy`

Next, you need to install `cellpy`. You can install it via pip (Python's package manager).
To install `cellpy`:

- Make sure your virtual environment is activated.

- Type the following command and press enter:

  ```
  python -m pip install cellpy
  ```

### 6. Launching Jupyter Notebook

- Make sure your virtual environment is activated.

- Type the following command and press enter:

  ```
  jupyter notebook
  ```

- This will open a new tab in your web browser with the Jupyter's interface. From there,
  create a new Python notebook by clicking on "New" > "Python 3".

### 7. Trying out `cellpy`

Here's a simple example of how to use Cellpy in a Jupyter notebook:

- In the first cell of the notebook, import Cellpy by typing:

  ```
  import cellpy
  ```

  Press `Shift + Enter` to run the cell.

- In the new cell, load your data file (replace "datafile.res" and "/path/to/your/data" with your actual filename and path):

  ```
  filepath = "/path/to/your/data/datafile.res"

  c = cellpy.get(filepath)  # create a new cellpy object
  ```

  Press `Shift + Enter` to run the cell and load the data.

- To see a summary of the loaded data, create a new cell and type:

  ```
  print(c.data.summary.head())
  ```

  Press `Shift + Enter` to run the cell and print the summary.

Congratulations! You've successfully set up Cellpy in a virtual environment on your Windows PC and loaded your first data file.
For more information and examples, check out the [official Cellpy documentation](https://cellpy.readthedocs.io/en/latest/).

Cellpy includes convenient functions for accessing the data. Here's a basic example of how to plot voltage vs. capacity.

- In a new cell in your Jupyter notebook, first, import matplotlib, which is a Python plotting library:

  ```
  import matplotlib.pyplot as plt
  ```

  Press `Shift + Enter` to run the cell.

- Then, iterate through all cycles numbers, extract the capacity curves and plot:

  ```
  for cycle in c.get_cycle_numbers():
      d = c.get_cap(cycle)
      plt.plot(d["capacity"], d["voltage"])
  plt.show()
  ```

  Press `Shift + Enter` to run the cell.

  This will produce a plot for each cycle in the loaded data.

Once you've loaded your data, you can save it to a hdf5 file for later use:

```
c.save("saved_data.h5")
```

This saves the loaded data to a file named 'saved_data.h5'.

Now, lets try to create some dQ/dV plots. dQ/dV is a plot of the change in capacity (Q) with respect to
the change in voltage (V). It's often used in battery analysis
to observe specific electrochemical reactions. Here's how to create one:

- In a new cell in your Jupyter notebook, first, if you have not imported matplotlib:

  ```
  import matplotlib.pyplot as plt
  ```

  Press `Shift + Enter` to run the cell.

- Then, calculate dQ/dV using Cellpy's ica utility:

  ```
  import cellpy.utils.ica as ica

  dqdv = ica.dqdv_frames(c, cycle=[1, 10, 100], voltage_resolution=0.01)
  ```

  Press `Shift + Enter` to run the cell.

- Now, you can create a plot of dQ/dV. In a new cell, type:

  ```
  plt.figure(figsize=(10, 8))
  plt.plot(dqdv["v"], dqdv["dq"], label="dQ/dV")
  plt.xlabel("Voltage (V)")
  plt.ylabel("dQ/dV (Ah/V)")
  plt.legend()
  plt.grid(True)
  plt.show()
  ```

  Press `Shift + Enter` to run the cell.

In the code above, `plt.figure` is used to create a new figure, `plt.plot` plots the data, `plt.xlabel` and `plt.ylabel` set
the labels for the x and y axes, `plt.legend` adds a legend to the plot, `plt.grid` adds a grid to the plot, and `plt.show` displays the plot.

With this, you should be able to see the dQ/dV plot in your notebook.

Remember that the process of creating a dQ/dV plot can be quite memory-intensive, especially for large datasets,
so it may take a while for the plot to appear.

For more information and examples, check out the [official Cellpy documentation](https://cellpy.readthedocs.io/en/latest/) and
the [matplotlib documentation](https://matplotlib.org/stable/contents.html).

This recipe can only take you a certain distance. If you want to become more efficient with Python and Cellpy, you
might want to try to install it using the method described in the chapter "Installing and setting up cellpy" in the
[official Cellpy documentation](https://cellpy.readthedocs.io/en/latest/).

## More about installing and setting up `cellpy`

### Fixing dependencies

To make sure your environment contains the correct packages and dependencies
required for running cellpy, you can create an environment based on the available
`environment.yml` file. Download the
[environment.yml](https://github.com/jepegit/cellpy/blob/master/environment.yml)
file and place it in the directory shown in your Anaconda Prompt. If you want to
change the name of the environment, you can do this by changing the first line of
the file. Then type (in the Anaconda Prompt):

```console
conda env create -f environment.yml
```

Then activate your environment:

```console
conda activate cellpy
```

`cellpy` relies on a number of other python package and these need
to be installed. Most of these packages are included when creating the environment
based on the `environment.yml` file as outlined above.

#### Basic dependencies

In general, you need the typical scientific python pack, including

- `numpy`
- `scipy`
- `pandas`

Additional dependencies are:

- `pytables` is needed for working with the hdf5 files (the cellpy-files):

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

For more details, I recommend that you look at the documentation of these
packages (google it) and install them. You can most
likely use the same method as for pytables *etc*.

#### Additional requirements for .res files

Note! .res files from Arbin testers are actually in a Microsoft Access format.

**For Windows users:** if you do not have one of the
most recent Office versions, you might not be allowed to install a driver
of different bit than your office version is using (the installers can be found
[here](https://www.microsoft.com/en-US/download/details.aspx?id=13255)).
Also remark that the driver needs to be of the same bit as your Python
(so, if you are using 32 bit Python, you will need the 32 bit driver).

**For POSIX systems:** I have not found any suitable drivers. Instead,
`cellpy` will try to use `mdbtools`to first export the data to
temporary csv-files, and then import from those csv-file (using the
`pandas` library). You can install `mdbtools` using your systems
preferred package manager (*e.g.* `apt-get install mdbtools`).

### The cellpy configuration file

The paths to raw data, the cellpy data base file, file locations etc. are set in
the `.cellpy_prms_USER.conf` file that is located in your home directory.

To get the filepath to your config file (and other cellpy info), run:

```console
cellpy info -l
```

The config file is written in YAML format and it should be relatively easy to
edit it in a text editor.

Within the config file, the paths are the most important parts that need to
be set up correctly. This tells `cellpy` where to find (and save) different files,
such as the database file and raw data.

Furthermore, the config file contains details about the database-file to be
used for cell info and metadata (i.e. type and structure of the database file such
as column headers etc.). For more details, see chapter on Configuring cellpy.

### The 'database' file

The database file should contain information (cell name, type, mass loading etc.)
on your cells, so that cellpy can find and link the test data to the provided
metadata.

The database file is also useful when working with the `cellpy` batch routine.

## Useful `cellpy` commands

To help installing and controlling your `cellpy` installation, a CLI
(command-line-interface) is provided with several commands (including the already
mentioned `info` for getting information about your installation, and
`setup` for helping you to set up your installation and writing a configuration file).

To get a list of these commands including some basic information, you can issue

```console
cellpy --help
```

This will output some (hopefully) helpful text

```console
Usage: cellpy [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  edit   Edit your cellpy config file.
  info   This will give you some valuable information about your cellpy.
  new    Set up a batch experiment.
  pull   Download examples or tests from the big internet.
  run    Run a cellpy process.
  serve  Start a Jupyter server
  setup  This will help you to setup cellpy.
```

You can get information about the sub-commands by issuing –-help after
them also. For example, issuing

```console
cellpy info --help
```

gives

```console
Usage: cellpy info [OPTIONS]

Options:
 -v, --version    Print version information.
 -l, --configloc  Print full path to the config file.
 -p, --params     Dump all parameters to screen.
 -c, --check      Do a sanity check to see if things works as they should.
 --help           Show this message and exit.
```

## Running your first script

As with most software, you are encouraged to play a little with it. I
hope there are some useful stuff in the code repository (for example in
the [examples
folder](https://github.com/jepegit/cellpy/tree/master/examples)).

:::{hint}
The `cellpy pull` command can assist in downloading
both examples and tests.
:::

Start by trying to import `cellpy` in an interactive Python session.
If you have an icon to press to start up the Python in interactive mode,
do that (it could also be for example an ipython console or a Jupyter
Notebook).
You can also start an interactive Python session if you are in your
terminal window of command window by just writing `python` and pressing
enter.
*Hint:* Remember to activate your cellpy (or whatever name you
chose) environment.

Once inside Python, try issuing `import cellpy`. Hopefully you should not see
any error-messages.

```python
Python 3.9.9 | packaged by conda-forge | (main, Dec 20 2021, 02:36:06)
[MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import cellpy
>>>
```

Nothing bad happened this time. If you got an error message, try to interpret
it and check if you have skipped any steps in this tutorial. Maybe you are
missing the `box` package? If so, go out of the Python interpreter if you
started it in your command window, or open another command window and write

```console
pip install python-box
```

and try again.

Now let's try to be a bit more ambitious. Start up python again if you are
not still running it and try this:

```python
>>> from cellpy import prmreader
>>> prmreader.info()
```

The `prmreader.info()` command should print out information about your
cellpy settings. For example where you selected to look for your input
raw files (`prms.Paths.rawdatadir`).

Try scrolling to find your own `prms.Paths.rawdatadir`. Does it look
right? These settings can be changed by either re-running the
`cellpy setup -i` command (not in Python, but in the command window /
terminal window). You probably need to use the `--reset` flag this time
since it is not your first time running it).
