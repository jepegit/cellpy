.. highlight:: shell

================================
File Formats and Data Structures
================================

The most important file formats and data structures for cellpy is
summarized here.

It is also possible to look into the source-code at the
repository https://github.com/jepegit/cellpy.

Data Structures
----------------------

cellpydata
~~~~~~~~~~~

This class is the main work-horse for cellpy where all the functions for reading, selecting, and
tweaking your data is located. It also contains the header definitions, both for the cellpy hdf5
format, and for the various cell-tester file-formats that can be read. The class can contain
several tests and each test is stored in a list.

The class contains several attributes that can be accessed
directly by the ordinary Pythonic way, e.g.:

.. code-block:: python

    cellpydata.tester = "arbin"
    cellpydata.auto_dir = True
    print cellpydata.cellpy_datadir


The data for the run(s) are stored in the class attribute `cellpydata.tests`.
This attribute is just a list of runs. This further implies that
you can store many runs in one `cellpydata` instance. Sometimes this can be
necessary, but it is recommended to only store one run in one instance. Most of the
functions (the class methods) automatically selects the 0-th item in
`cellpydata.tests` if the test_number is not explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run.

Here is a list of other important class attributes in cellpydata:

list_of_step_types


*column headings - summary data*

.. code-block::

    summary_txt_discharge_cap = "Discharge_Capacity(mAh/g)"
    summary_txt_charge_cap = "Charge_Capacity(mAh/g)"
    summary_txt_cum_charge_cap = "Cumulated_Charge_Capacity(mAh/g)"
    summary_txt_coul_eff = "Coulombic_Efficiency(percentage)"
    summary_txt_coul_diff = "Coulombic_Difference(mAh/g)"
    summary_txt_cum_coul_diff = "Cumulated_Coulombic_Difference(mAh/g)"
    summary_txt_discharge_cap_loss = "Discharge_Capacity_Loss(mAh/g)"
    summary_txt_charge_cap_loss = "Charge_Capacity_Loss(mAh/g)"
    summary_txt_cum_discharge_cap_loss = "Cumulated_Discharge_Capacity_Loss(mAh/g)"
    summary_txt_cum_charge_cap_loss = "Cumulated_Charge_Capacity_Loss(mAh/g)"
    summary_txt_ir_discharge = "ir_discharge"
    summary_txt_ir_charge = "ir_charge"
    summary_txt_ocv_1_min = "ocv_first_min"
    summary_txt_ocv_2_min = "ocv_second_min"
    summary_txt_ocv_1_max = "ocv_first_max"
    summary_txt_ocv_2_max = "ocv_second_max"
    summary_txt_datetime_txt = "date_time_txt"
    summary_txt_endv_discharge = "end_voltage_discharge"
    summary_txt_endv_charge = "end_voltage_charge"


etc.
