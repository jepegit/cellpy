The cellpy command
==================

At the moment, only a very limited set of things can be achieved by running the ``cellpy`` command at the shell (or in
the cmd window).

.. code-block:: shell

    $ cellpy
    Usage: cellpy [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      configloc
      setup
      version

A couple of commands are implemented to get some information about your cellpy environment (currently getting your
cellpy version and the location of your configuration file):

.. code-block:: shell

    $ cellpy version
    [cellpy] version: 0.1.11

    $ cellpy configloc
    [cellpy] ->C:\Users\jepe\_cellpy_prms_jepe.conf


The most important command is probably the ``setup`` command (that should be run when you install cellpy for the first
time).
