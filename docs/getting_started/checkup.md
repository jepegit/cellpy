# Checkup & useful commands

The easiest way to check if `cellpy` has been installed, is to issue
the command for printing the version number to the screen

```console
cellpy info --version
```

To run a more complete check of your installation, there exist a
`cellpy` sub-command than can be helpful

```console
cellpy info --check
```

:::{hint}
Even though some of the checks fail, you might still be able to use and enjoy several of the `cellpy` features.
But, if you want to use all the features, you should try to fix the issues that are reported.
:::

To get the filepath to your configuration file and other cellpy info, run:

```console
cellpy info -l
```

## Useful cellpy commands

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
  edit   Edit your cellpy config or database files.
  info   This will give you some valuable information about your cellpy.
  new    Set up a batch experiment (might need git installed).
  pull   Download examples or tests from the big internet (needs git).
  run    Run a cellpy process (for example a batch-job).
  serve  Start a Jupyter server.
  setup  This will help you to set up cellpy.
```

You can get information about the sub-commands by issuing –-help after
them also. For example, issuing

```console
cellpy info --help
```

gives

```console
Usage: cellpy info [OPTIONS]

  This will give you some valuable information about your cellpy.

Options:
  -v, --version    Print version information.
  -l, --configloc  Print full path to the config file.
  -p, --params     Dump all parameters to screen.
  -c, --check      Do a sanity check to see if things works as they should.
  --help           Show this message and exit.

```

## Upgrade `cellpy`

If you installed `cellpy` earlier and you want to upgrade to the most recent
version, run

```console
python -m pip install --upgrade cellpy
```

## Pre-releases
If you want to install a pre-release (a version that is so bleeding edge
that it ends with a alpha or beta release identification, *e.g.* ends
with .b2). Then you can add the –-pre modifier to the installation command

```console
python -m pip install --pre cellpy
```
