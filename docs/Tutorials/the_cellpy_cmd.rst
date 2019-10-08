The cellpy command
==================

At the moment, only a very limited set of things can be achieved by running
the ``cellpy`` command at the shell (or in the cmd window).

.. code-block:: shell

    $ cellpy
    Usage: cellpy [OPTIONS] COMMAND [ARGS]...

    Options:
     --help  Show this message and exit.

    Commands:
      info   This will give you some valuable information about your cellpy.
      new    Will in the future be used for setting up a batch experiment.
      pull   Download examples or tests from the big internet.
      run    Will in the future be used for running a cellpy process.
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

