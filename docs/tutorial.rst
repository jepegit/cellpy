=========
Tutorials
=========


How the parameters are set and read
===================================

When `cellpy`is imported, it sets a default set of parameters. Then it tries to read the parameters from you .conf-file
(located in your user directory). If it is successful, the paramteters set in your .conf-file will over-ride the
default ones.

The parameters are stored in the module cellpy.parameters.prms as a dictionary of dictionaries. I know, this is
probably not the most convenient method, but it is very easy to change these into class-type stuff later (using for
example using `type(x, y, z)` etc. or `setattr` etc.

If you during your script (or in your `jupyter notebook`) would like to change some of the settings (*e.g.* if you
want to use the cycle_mode option "cathode" instead of the default "anode"), then import the prms class and set new
values:

.. code-block:: python

    from cellpy import parameters.prms

    # Changing cycle_mode to cathode
    prms['Reader']['cycle_mode'] = 'cathode'

    # Changing delimiter to  ',' (used when saving .csv files)
    prms['Reader']['sep'] = ','


Using the batch utilities
=========================



