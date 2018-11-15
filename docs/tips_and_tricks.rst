====================
Some tips and tricks
====================

Overriding settings
-------------------
If you would like to override some of the standard settings, then
the route of less friction is to import the prms class and set
new values directly.

.. code-block:: python

    from cellpy import prms

    # use mdbtools even though you are on windows
    prms.Instruments.use_subprocess = True

Then...
