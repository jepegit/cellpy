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

CellpyData - main structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This class is the main work-horse for cellpy where all the functions for reading, selecting, and
tweaking your data is located. It also contains the header definitions, both for the cellpy hdf5
format, and for the various cell-tester file-formats that can be read. The class can contain
several tests and each test is stored in a list.

The class contains several attributes that can be assigned directly:

.. code-block:: python

    CellpyData.tester = "arbin"
    CellpyData.auto_dir = True
    print CellpyData.cellpy_datadir


The data for the run(s) are stored in the class attribute `CellpyData.tests` (this will most likely change
in future versions).
This attribute is just a list of runs (each run is a `cellpy.cellreader.DataSet` instance).
This implies that you can store many runs in one `CellpyData` instance. Sometimes this can be
necessary, but it is recommended to only store one run in one instance. Most of the
functions (the class methods) automatically selects the 0-th item in
`CellpyData.tests` if the test_number is not explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run. And each run is a `cellpy.cellreader.DataSet` instance.

Here is a list of other important class attributes in `CellpyData`:

column headings - normal data
..............................

.. code-block:: python

    CellpyData.headers_normal['aci_phase_angle_txt'] = 'ACI_Phase_Angle'
    CellpyData.headers_normal['ac_impedance_txt'] = 'AC_Impedance'
    CellpyData.headers_normal['charge_capacity_txt'] = 'Charge_Capacity'
    CellpyData.headers_normal['charge_energy_txt'] = 'Charge_Energy'
    CellpyData.headers_normal['current_txt'] = 'Current'
    CellpyData.headers_normal['cycle_index_txt'] = 'Cycle_Index'
    CellpyData.headers_normal['data_point_txt'] = 'Data_Point'
    CellpyData.headers_normal['datetime_txt'] = 'DateTime'
    CellpyData.headers_normal['discharge_capacity_txt'] = 'Discharge_Capacity'
    CellpyData.headers_normal['discharge_energy_txt'] = 'Discharge_Energy'
    CellpyData.headers_normal['internal_resistance_txt'] = 'Internal_Resistance'
    CellpyData.headers_normal['is_fc_data_txt'] = 'Is_FC_Data'
    CellpyData.headers_normal['step_index_txt'] = 'Step_Index'
    CellpyData.headers_normal['step_time_txt'] = 'Step_Time'
    CellpyData.headers_normal['test_id_txt'] = 'Test_ID'
    CellpyData.headers_normal['test_time_txt'] = 'Test_Time'
    CellpyData.headers_normal['voltage_txt'] = 'Voltage'
    CellpyData.headers_normal['dv_dt_txt'] = 'dV/dt'

column headings - summary data
..............................

.. code-block:: python

    CellpyData.headers_summary["discharge_capacity"] = "Discharge_Capacity(mAh/g)"
    CellpyData.headers_summary["charge_capacity"] = "Charge_Capacity(mAh/g)"
    CellpyData.headers_summary["cumulated_charge_capacity"] = "Cumulated_Charge_Capacity(mAh/g)"
    CellpyData.headers_summary["cumulated_discharge_capacity"] = "Cumulated_Discharge_Capacity(mAh/g)"
    CellpyData.headers_summary["coulombic_efficiency"] = "Coulombic_Efficiency(percentage)"
    CellpyData.headers_summary["cumulated_coulombic_efficiency"] = "Cumulated_Coulombic_Efficiency(percentage)"
    CellpyData.headers_summary["coulombic_difference"] = "Coulombic_Difference(mAh/g)"
    CellpyData.headers_summary["cumulated_coulombic_difference"] = "Cumulated_Coulombic_Difference(mAh/g)"
    CellpyData.headers_summary["discharge_capacity_loss"] = "Discharge_Capacity_Loss(mAh/g)"
    CellpyData.headers_summary["charge_capacity_loss"] = "Charge_Capacity_Loss(mAh/g)"
    CellpyData.headers_summary["cumulated_discharge_capacity_loss"] = "Cumulated_Discharge_Capacity_Loss(mAh/g)"
    CellpyData.headers_summary["cumulated_charge_capacity_loss"] = "Cumulated_Charge_Capacity_Loss(mAh/g)"
    CellpyData.headers_summary["ir_discharge"] = "IR_Discharge(Ohms)"
    CellpyData.headers_summary["ir_charge"] = "IR_Charge(Ohms)"
    CellpyData.headers_summary["ocv_first_min"] = "OCV_First_Min(V)"
    CellpyData.headers_summary["ocv_second_min"] = "OCV_Second_Min(V)"
    CellpyData.headers_summary["ocv_first_max"] = "OCV_First_Max(V)"
    CellpyData.headers_summary["ocv_second_max"] = "OCV_Second_Max(V)"
    CellpyData.headers_summary["date_time_txt"] = "Date_Time_Txt(str)"
    CellpyData.headers_summary["end_voltage_discharge"] = "End_Voltage_Discharge(V)"
    CellpyData.headers_summary["end_voltage_charge"] = "End_Voltage_Charge(V)"
    CellpyData.headers_summary["cumulated_ric_disconnect"] = "RIC_Disconnect(none)"
    CellpyData.headers_summary["cumulated_ric_sei"] = "RIC_SEI(none)"
    CellpyData.headers_summary["cumulated_ric"] = "RIC(none)"
    CellpyData.headers_summary["low_level"] = "Low_Level(percentage)"  # Sum of irreversible capacity
    CellpyData.headers_summary["high_level"] = "High_Level(percentage)"  # SEI loss
    CellpyData.headers_summary["shifted_charge_capacity"] = "Charge_Endpoint_Slippage(mAh/g)"
    CellpyData.headers_summary["shifted_discharge_capacity"] = "Discharge_Endpoint_Slippage(mAh/g)"
    CellpyData.headers_summary["temperature_last"] = "Last_Temperature(C)"
    CellpyData.headers_summary["temperature_mean"] = "Average_Temperature(C)"
    CellpyData.headers_summary["pre_aux"] = "Aux_"

column headings - step table
............................

.. code-block:: python

    CellpyData.headers_step_table["test"] = "test"
    CellpyData.headers_step_table["cycle"] = "cycle"
    CellpyData.headers_step_table["step"] = "step"
    CellpyData.headers_step_table["sub_step"] = "sub_step"
    CellpyData.headers_step_table["type"] = "type"
    CellpyData.headers_step_table["sub_type"] = "sub_type"
    CellpyData.headers_step_table["info"] = "info"
    CellpyData.headers_step_table["pre_current"] = "I_"
    CellpyData.headers_step_table["pre_voltage"] = "V_"
    CellpyData.headers_step_table["pre_charge"] = "Charge_"
    CellpyData.headers_step_table["pre_discharge"] = "Discharge_"
    CellpyData.headers_step_table["pre_point"] = "datapoint_"
    CellpyData.headers_step_table["pre_time"] = "time_"
    CellpyData.headers_step_table["post_mean"] = "avr"
    CellpyData.headers_step_table["post_std"] = "std"
    CellpyData.headers_step_table["post_max"] = "max"
    CellpyData.headers_step_table["post_min"] = "min"
    CellpyData.headers_step_table["post_start"] = "start"
    CellpyData.headers_step_table["post_end"] = "end"
    CellpyData.headers_step_table["post_delta"] = "delta"
    CellpyData.headers_step_table["post_rate"] = "rate"
    CellpyData.headers_step_table["internal_resistance"] = "IR"
    CellpyData.headers_step_table["internal_resistance_change"] = "IR_pct_change"

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
inside the CellpyData class, but will be moved out later.

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


CellpyData - methods
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

FileID
~~~~~~

Todo
