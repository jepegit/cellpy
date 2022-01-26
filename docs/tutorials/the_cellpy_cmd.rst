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
        new    Set up a batch experiment.
        pull   Download examples or tests from the big internet.
        run    Run a cellpy process.
        serve  Start a Jupyter server
        setup  This will help you to setup cellpy.


As can be seen from the help-text, the cli is still under development
(cli stands for command-line-interface, by the way). Both the ``cellpy new``
and the ``cellpy serve`` command worked the last time I tried them. But
it might not work on your computer.

A couple of commands are implemented to get some information about your
cellpy environment (currently getting your
cellpy version and the location of your configuration file):

.. code-block:: shell

    $ cellpy info --version
    [cellpy] version: 0.3.1

    $ cellpy info --configloc
    [cellpy] ->C:\Users\jepe\_cellpy_prms_jepe.conf


The most important command is probably the ``setup`` command (that should be run
when you install cellpy for the first time).

.. code-block:: shell

    $ cellpy setup --interactive

Another very nice command is the ``new`` command that sets up a project structure
for batch-processing cell data (using templates, either from github or from your local computer).

.. code-block:: shell

    $ cellpy new
