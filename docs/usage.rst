=====
Usage
=====

To use ``cellpy``, start with importing the needed modules::

    >>> from cellpy import cellreader

Lets define some variables::

    >>> FileName  = r"C:\data\20141030_CELL_6_cc_01.res"
    >>> Mass      = 0.982 # mass of active material in mg
    >>> OutFolder = r"C:\processed_data"

Then load the data into the data-class (this is data obtained using an Arbin battery tester,
for the moment we assume that you are using the default settings where the default
data-format is the Arbin .res format)::

    >>> d = cellreader.CellpyData()
    >>> d.from_raw(FileName) # this tells cellpy to read the arbin data file (.res format)
    >>> d.set_mass(Mass)

Create a summary (for each cycle) and generate a step table (parsing the
data and finding out what each step in each cycle is)::

    >>> d.make_summary()
    >>> d.make_step_table()

You can save your data in csv-format easily by::

    >>> d.to_csv(OutFolder)

Or maybe you want to take a closer look at the capacities for
the different cycles? No problem. Now you are set to extract data
for specific cycles and steps::

    >>> list_of_cycles = d.get_cycle_numbers()
    >>> number_of_cycles = len(list_of_cycles)
    >>> print "you have %i cycles" % (number_of_cycles)
    you have 658 cycles
    >>> current,voltage = d.get_cap(5) # current and voltage for cycle 5

You can also look for open circuit voltage steps::

    >>> cycle = 44
    >>> time1, voltage1 = d.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
    >>> time2, voltage2 = d.get_ocv(ocv_type='ocvrlx_down', cycle_number=cycle)

If you would like to use more sophisticated methods (e.g. database readers),
take a look at the tutorial (if it exists), check the source code, or simply
send an e-mail to one of the authors.
