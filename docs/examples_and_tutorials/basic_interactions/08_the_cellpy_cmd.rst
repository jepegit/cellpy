The cellpy command
==================

To assist in using ``cellpy`` more efficiently, a set of routines are available from
the command line
by issuing the ``cellpy`` command at the shell (or in the cmd window).

.. code-block:: shell

    $ cellpy
    Usage: cellpy [OPTIONS] COMMAND [ARGS]...

    Options:
     --help  Show this message and exit.

    Commands:
      edit   Edit your cellpy config file.
      info   This will give you some valuable information about your cellpy.
      new    Set up a batch experiment (might need git installed).
      pull   Download examples or tests from the big internet (needs git).
      run    Run a cellpy process (batch-job, edit db, ...).
      serve  Start a Jupyter server.
      setup  This will help you to set up cellpy.

The cli is still under development (cli stands for command-line-interface, by the way).
Both the ``cellpy new`` and the ``cellpy serve`` command worked the last time I tried them.
But it might not work on your computer. If you run into problems, let us know.


Information
-----------

A couple of commands are implemented to get some information about your
``cellpy`` environment (currently getting your
``cellpy`` version and the location of your configuration file):

.. code-block:: shell

    $ cellpy info --version
    [cellpy] version: 0.4.1

    $ cellpy info --configloc
    [cellpy] ->C:\Users\jepe\_cellpy_prms_jepe.conf


Setting up ``cellpy`` from the cli
----------------------------------

To get the most out of ``cellpy`` it is to best to set it up properly. To help
with this, you can use the ``setup`` command. If you include the ``--interactive`` switch,
you will be prompted for your preferred location for the different folders / directories
``cellpy`` uses (it still will work without them, though).


.. code-block:: shell

    $ cellpy setup --interactive

The command will create a starting ``cellpy`` configuration file (`_cellpy_prms_yourname.conf`)
or update it if it exists, and create the following directory structure:

.. code-block:: shell

    batchfiles/
    cellpyfiles/
    db/
    examples/
    instruments/
    logs/
    notebooks/
    out/
    raw/
    templates/


.. note::

    It is recommended to rerun setup each time you update ``cellpy``.


.. note::

    You can get help for each sub-command by turning on the ``--help`` switch.
    For example, for ``setup``:

    .. code-block:: shell

        $ cellpy setup --help


    You will then get some more detailed information on the different switches
    you have at your disposal:

    .. code-block:: shell

        Usage: cellpy setup [OPTIONS]

          This will help you to setup cellpy.

        Options:
          -i, --interactive       Allows you to specify div. folders and setting.
          -nr, --not-relative     If root-dir is given, put it directly in the root
                                  (/) folder i.e. do not put it in your home directory.
                                  Defaults to False. Remark that if you specifically
                                  write a path name instead of selecting the suggested
                                  default, the path you write will be used as is.
          -dr, --dry-run          Run setup in dry mode (only print - do not execute).
                                  This is typically used when developing and testing
                                  cellpy. Defaults to False.
          -r, --reset             Do not suggest path defaults based on your current
                                  configuration-file
          -d, --root-dir PATH     Use custom root dir. If not given, your home
                                  directory will be used as the top level where
                                  cellpy-folders will be put. The folder path must
                                  follow directly after this option (if used).
                                  Example: $ cellpy setup -d 'MyDir'
          -n, --folder-name PATH
          -t, --testuser TEXT     Fake name for fake user (for testing)
          --help                  Show this message and exit.


The cellpy templating system
----------------------------

If you are performing the same type of data processing for many cells, and possibly
many times, it is beneficial to start out with a template.

Currently, ``cellpy`` provides a template system defaulting to a set of ``Jupyter notebooks`` and
a folder structure where the code is based on the ``batch`` utility (``cellpy.utils.batch``).

The templates are pulled from the `cellpy_templates` repository. It uses ``cookiecutter`` under
the hood (and therefore needs `git` installed).

This repository contains several template sets. The default is named `standard`, but you can
set another default in your configuration file.

You can also make your own templates and store them locally on your computer
(in the `templates` directory). The template should be in a zip file and start with "cellpy_template"
and end with ".zip".


.. code-block:: shell

    $ cellpy new --help


    Usage: cellpy new [OPTIONS]

      Set up a batch experiment (might need git installed).

    Options:
      -t, --template TEXT        Provide template name.
      -d, --directory TEXT       Create in custom directory.
      -p, --project TEXT         Provide project name (i.e. sub-directory name).
      -e, --experiment TEXT      Provide experiment name (i.e. lookup-value).
      -u, --local-user-template  Use local template from the templates directory.
      -s, --serve                Run Jupyter.
      -r, --run                  Use PaperMill to run the notebook(s) from the
                                 template (will only work properly if the
                                 notebooks can be sorted in correct run-order by
                                 'sorted'.
      -j, --lab                  Use Jupyter Lab instead of Notebook when serving.
      -l, --list                 List available templates and exit.
      --help                     Show this message and exit.


Automatically running batches
-----------------------------

The ``run`` command is used for running the appropriate editor for your
database, and for running (processing) files in batches.

.. code-block:: shell

    $ cellpy run --help

    Usage: cellpy run [OPTIONS] [NAME]

      Run a cellpy process (batch-job, edit db, ...).

      You can use this to launch specific applications.

      Examples:

          edit your cellpy database

             cellpy run db

          run a batch job described in a journal file

             cellpy run -j my_experiment.json

    Options:
      -j, --journal         Run a batch job defined in the given journal-file
      -k, --key             Run a batch job defined by batch-name
      -f, --folder          Run all batch jobs iteratively in a given folder
      -p, --cellpy-project  Use PaperMill to run the notebook(s) within the given
                            project folder (will only work properly if the
                            notebooks can be sorted in correct run-order by
                            'sorted'). Warning! since we are using `click` - the
                            NAME will be 'converted' when it is loaded (same as
                            print(name) does) - so you can't use backslash ('\')
                            as normal in windows (use either '/' or '\\' instead).
      -d, --debug           Run in debug mode.
      -s, --silent          Run in silent mode.
      --raw                 Force loading raw-file(s).
      --cellpyfile          Force cellpy-file(s).
      --minimal             Minimal processing.
      --nom-cap FLOAT       nominal capacity (used in calculating rates etc)
      --batch_col TEXT      batch column (if selecting running from db)
      --project TEXT        name of the project (if selecting running from db)
      -l, --list            List batch-files.
      --help                Show this message and exit.

