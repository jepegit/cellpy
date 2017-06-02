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

The class contains several attributes that can be assigned directly:

.. code-block:: python

    cellpydata.tester = "arbin"
    cellpydata.auto_dir = True
    print cellpydata.cellpy_datadir


The data for the run(s) are stored in the class attribute `cellpydata.tests` (this will most likely change
in future versions).
This attribute is just a list of runs (each run is a `cellpy.cellreader.DataSet` instance).
This implies that you can store many runs in one `cellpydata` instance. Sometimes this can be
necessary, but it is recommended to only store one run in one instance. Most of the
functions (the class methods) automatically selects the 0-th item in
`cellpydata.tests` if the test_number is not explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run. And each run is a `cellpy.cellreader.DataSet` instance.

Here is a list of other important class attributes in `cellpydata`:

column headings - normal data
..............................

.. code-block:: python

    cellpydata.headers_normal['aci_phase_angle_txt'] = 'ACI_Phase_Angle'
    cellpydata.headers_normal['ac_impedance_txt'] = 'AC_Impedance'
    cellpydata.headers_normal['charge_capacity_txt'] = 'Charge_Capacity'
    cellpydata.headers_normal['charge_energy_txt'] = 'Charge_Energy'
    cellpydata.headers_normal['current_txt'] = 'Current'
    cellpydata.headers_normal['cycle_index_txt'] = 'Cycle_Index'
    cellpydata.headers_normal['data_point_txt'] = 'Data_Point'
    cellpydata.headers_normal['datetime_txt'] = 'DateTime'
    cellpydata.headers_normal['discharge_capacity_txt'] = 'Discharge_Capacity'
    cellpydata.headers_normal['discharge_energy_txt'] = 'Discharge_Energy'
    cellpydata.headers_normal['internal_resistance_txt'] = 'Internal_Resistance'
    cellpydata.headers_normal['is_fc_data_txt'] = 'Is_FC_Data'
    cellpydata.headers_normal['step_index_txt'] = 'Step_Index'
    cellpydata.headers_normal['step_time_txt'] = 'Step_Time'
    cellpydata.headers_normal['test_id_txt'] = 'Test_ID'
    cellpydata.headers_normal['test_time_txt'] = 'Test_Time'
    cellpydata.headers_normal['voltage_txt'] = 'Voltage'
    cellpydata.headers_normal['dv_dt_txt'] = 'dV/dt'

column headings - summary data
..............................

.. code-block:: python

    cellpydata.headers_summary["discharge_capacity"] = "Discharge_Capacity(mAh/g)"
    cellpydata.headers_summary["charge_capacity"] = "Charge_Capacity(mAh/g)"
    cellpydata.headers_summary["cumulated_charge_capacity"] = "Cumulated_Charge_Capacity(mAh/g)"
    cellpydata.headers_summary["cumulated_discharge_capacity"] = "Cumulated_Discharge_Capacity(mAh/g)"
    cellpydata.headers_summary["coulombic_efficiency"] = "Coulombic_Efficiency(percentage)"
    cellpydata.headers_summary["cumulated_coulombic_efficiency"] = "Cumulated_Coulombic_Efficiency(percentage)"
    cellpydata.headers_summary["coulombic_difference"] = "Coulombic_Difference(mAh/g)"
    cellpydata.headers_summary["cumulated_coulombic_difference"] = "Cumulated_Coulombic_Difference(mAh/g)"
    cellpydata.headers_summary["discharge_capacity_loss"] = "Discharge_Capacity_Loss(mAh/g)"
    cellpydata.headers_summary["charge_capacity_loss"] = "Charge_Capacity_Loss(mAh/g)"
    cellpydata.headers_summary["cumulated_discharge_capacity_loss"] = "Cumulated_Discharge_Capacity_Loss(mAh/g)"
    cellpydata.headers_summary["cumulated_charge_capacity_loss"] = "Cumulated_Charge_Capacity_Loss(mAh/g)"
    cellpydata.headers_summary["ir_discharge"] = "IR_Discharge(Ohms)"
    cellpydata.headers_summary["ir_charge"] = "IR_Charge(Ohms)"
    cellpydata.headers_summary["ocv_first_min"] = "OCV_First_Min(V)"
    cellpydata.headers_summary["ocv_second_min"] = "OCV_Second_Min(V)"
    cellpydata.headers_summary["ocv_first_max"] = "OCV_First_Max(V)"
    cellpydata.headers_summary["ocv_second_max"] = "OCV_Second_Max(V)"
    cellpydata.headers_summary["date_time_txt"] = "Date_Time_Txt(str)"
    cellpydata.headers_summary["end_voltage_discharge"] = "End_Voltage_Discharge(V)"
    cellpydata.headers_summary["end_voltage_charge"] = "End_Voltage_Charge(V)"
    cellpydata.headers_summary["cumulated_ric_disconnect"] = "RIC_Disconnect(none)"
    cellpydata.headers_summary["cumulated_ric_sei"] = "RIC_SEI(none)"
    cellpydata.headers_summary["cumulated_ric"] = "RIC(none)"
    cellpydata.headers_summary["low_level"] = "Low_Level(percentage)"  # Sum of irreversible capacity
    cellpydata.headers_summary["high_level"] = "High_Level(percentage)"  # SEI loss
    cellpydata.headers_summary["shifted_charge_capacity"] = "Charge_Endpoint_Slippage(mAh/g)"
    cellpydata.headers_summary["shifted_discharge_capacity"] = "Discharge_Endpoint_Slippage(mAh/g)"
    cellpydata.headers_summary["temperature_last"] = "Last_Temperature(C)"
    cellpydata.headers_summary["temperature_mean"] = "Average_Temperature(C)"
    cellpydata.headers_summary["pre_aux"] = "Aux_"

column headings - step table
............................

.. code-block:: python

    cellpydata.headers_step_table["test"] = "test"
    cellpydata.headers_step_table["cycle"] = "cycle"
    cellpydata.headers_step_table["step"] = "step"
    cellpydata.headers_step_table["sub_step"] = "sub_step"
    cellpydata.headers_step_table["type"] = "type"
    cellpydata.headers_step_table["sub_type"] = "sub_type"
    cellpydata.headers_step_table["info"] = "info"
    cellpydata.headers_step_table["pre_current"] = "I_"
    cellpydata.headers_step_table["pre_voltage"] = "V_"
    cellpydata.headers_step_table["pre_charge"] = "Charge_"
    cellpydata.headers_step_table["pre_discharge"] = "Discharge_"
    cellpydata.headers_step_table["pre_point"] = "datapoint_"
    cellpydata.headers_step_table["pre_time"] = "time_"
    cellpydata.headers_step_table["post_mean"] = "avr"
    cellpydata.headers_step_table["post_std"] = "std"
    cellpydata.headers_step_table["post_max"] = "max"
    cellpydata.headers_step_table["post_min"] = "min"
    cellpydata.headers_step_table["post_start"] = "start"
    cellpydata.headers_step_table["post_end"] = "end"
    cellpydata.headers_step_table["post_delta"] = "delta"
    cellpydata.headers_step_table["post_rate"] = "rate"
    cellpydata.headers_step_table["internal_resistance"] = "IR"
    cellpydata.headers_step_table["internal_resistance_change"] = "IR_pct_change"

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

DataSet
~~~~~~~

Each run is a `cellpy.cellreader.DataSet` instance. The instance contain general information about
the run-settings (such as mass etc.). The measurement data, information, and summary is stored
in three pandas.DataFrames:

* normal data
* step table
* summary data

Todo.

fileID
~~~~~~

Todo
