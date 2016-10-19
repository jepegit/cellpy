.. highlight:: shell

================================
File Formats and Data Structures
================================

The most important file formats and data structures for cellpy is
summarized here.
It is also possible to look into the source-code at the
repository https://github.com/jepegit/cellpy.

Data Structures
---------------

cellpydata - main structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
This attribute is just a list of runs (each run is a `cellpy.cellreader.dataset` instance).
This implies that you can store many runs in one `cellpydata` instance. Sometimes this can be
necessary, but it is recommended to only store one run in one instance. Most of the
functions (the class methods) automatically selects the 0-th item in
`cellpydata.tests` if the test_number is not explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run. And each run is a `cellpy.cellreader.dataset` instance.

Here is a list of other important class attributes in `cellpydata`:

column headings - summary data
..............................

.. code-block:: python

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


column headings - step table
............................

.. code-block:: python

    step_table_txt_test = "test"
    step_table_txt_cycle = "cycle"
    step_table_txt_step = "step"
    step_table_txt_type = "type"
    step_table_txt_info = "info"
    step_table_txt_I_ = "I_"
    step_table_txt_V_ = "V_"
    step_table_txt_C_ = "Charge_"
    step_table_txt_D_ = "Discharge_"
    step_table_txt_post_average = "avr"
    step_table_txt_post_stdev = "std"
    step_table_txt_post_max = "max"
    step_table_txt_post_min = "min"
    step_table_txt_post_start = "start"
    step_table_txt_post_end = "end"
    step_table_txt_post_delta = "delta"
    step_table_txt_post_rate = "rate"
    step_table_txt_ir = "IR"
    step_table_txt_ir_change = "IR_pct_change"

step types
..........

Identifiers for the different steps have pre-defined names given in the class attribute list
`list_of_step_types` and is written to the "step" column.

.. code-block:: python

    list_of_step_types = ['charge', 'discharge',
                          'cv_charge', 'cv_discharge',
                          'charge_cv', 'discharge_cv',
                          'ocvrlx_up', 'ocvrlx_down', 'ir',
                          'rest', 'not_known']


For each type of testers that are supported by cellpy, a set of column headings and
other different settings/attributes must be provided. These definitions are now put
inside the cellpydata class, but will be moved out later.

Supported testers are:

* arbin

Testers that is planned supported:

* biologic
* pec
* maccor


Tester dependent attributes
...........................

arbin
'''''

Three tables are read from the .res file:

* normal table: contains measurement data.
* global table: contains overall parametres for the test.
* stats table: contains statistics (for each cycle).



table names
'''''''''''

.. code-block:: python

    tablename_normal = "Channel_Normal_Table"
    tablename_global = "Global_Table"
    tablename_statistic = "Channel_Statistic_Table"

column headings - global table
''''''''''''''''''''''''''''''

.. code-block:: python

    applications_path_txt = 'Applications_Path'
    channel_index_txt = 'Channel_Index'
    channel_nuer_txt = 'Channel_Number'
    channel_type_txt = 'Channel_Type'
    comments_txt = 'Comments'
    creator_txt = 'Creator'
    daq_index_txt = 'DAQ_Index'
    item_id_txt = 'Item_ID'
    log_aux_data_flag_txt = 'Log_Aux_Data_Flag'
    log_chanstat_data_flag_txt = 'Log_ChanStat_Data_Flag'
    log_event_data_flag_txt = 'Log_Event_Data_Flag'
    log_smart_battery_data_flag_txt = 'Log_Smart_Battery_Data_Flag'
    mapped_aux_conc_cnumber_txt = 'Mapped_Aux_Conc_CNumber'
    mapped_aux_di_cnumber_txt = 'Mapped_Aux_DI_CNumber'
    mapped_aux_do_cnumber_txt = 'Mapped_Aux_DO_CNumber'
    mapped_aux_flow_rate_cnumber_txt = 'Mapped_Aux_Flow_Rate_CNumber'
    mapped_aux_ph_number_txt = 'Mapped_Aux_PH_Number'
    mapped_aux_pressure_number_txt = 'Mapped_Aux_Pressure_Number'
    mapped_aux_temperature_number_txt = 'Mapped_Aux_Temperature_Number'
    mapped_aux_voltage_number_txt = 'Mapped_Aux_Voltage_Number'
    schedule_file_name_txt = 'Schedule_File_Name'
    start_datetime_txt = 'Start_DateTime'
    test_id_txt = 'Test_ID'
    test_name_txt = 'Test_Name'

column headings - normal table
''''''''''''''''''''''''''''''

.. code-block:: python

    aci_phase_angle_txt = 'ACI_Phase_Angle'
    ac_impedance_txt = 'AC_Impedance'
    charge_capacity_txt = 'Charge_Capacity'
    charge_energy_txt = 'Charge_Energy'
    current_txt = 'Current'
    cycle_index_txt = 'Cycle_Index'
    data_point_txt = 'Data_Point'
    datetime_txt = 'DateTime'
    discharge_capacity_txt = 'Discharge_Capacity'
    discharge_energy_txt = 'Discharge_Energy'
    internal_resistance_txt = 'Internal_Resistance'
    is_fc_data_txt = 'Is_FC_Data'
    step_index_txt = 'Step_Index'
    step_time_txt = 'Step_Time'
    test_id_txt = 'Test_ID'
    test_time_txt = 'Test_Time'
    voltage_txt = 'Voltage'
    dv_dt_txt = 'dV/dt'


cellpydata - methods
~~~~~~~~~~~~~~~~~~~~


Todo

dataset
~~~~~~~

Each run is a `cellpy.cellreader.dataset` instance. The instance contain general information about
the run-settings (such as mass etc.). The measurement data, information, and summary is stored
in three pandas.DataFrames:

* normal data
* step table
* summary data

Todo.

fileID
~~~~~~

Todo
