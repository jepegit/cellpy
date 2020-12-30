.. highlight:: shell

================================
File Formats and Data Structures
================================

.. warning::
   This part of the documentation is currently being updated.
   We hope to have a trustable version ready by end of 2020.


The most important file formats and data structures for cellpy is
summarized here.
It is also possible to look into the source-code at the
repository https://github.com/jepegit/cellpy.

Data Structures
---------------

CellpyData - main structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This class is the main work-horse for cellpy where all the functions
for reading, selecting, and tweaking your data is located.
It also contains the header definitions, both for the cellpy hdf5
format, and for the various cell-tester file-formats that can be read.
The class can contain several tests and each test is stored in a list.

The class contains several attributes that can be assigned directly:

.. code-block:: python

    CellpyData.tester = "arbin"
    CellpyData.auto_dirs = True
    print(CellpyData.cellpy_datadir)


The data for the experiment(s)/runs(s) are stored in the class attribute
``CellpyData.cells``
This attribute is just a list of runs (each run is a
``cellpy.cellreader.Cell`` instance).
This implies that you can store many runs in one ``CellpyData`` instance.
Sometimes this can be necessary, but it is recommended to only store one
run in one instance. Most of the functions (the class methods) automatically
selects the 0-th item in ``CellpyData.cells`` if the `test_number` is not
explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run. And each run is a `cellpy.cellreader.Cell` instance.

Here is a list of other important class attributes in `CellpyData`:

column headings - normal data
..............................

.. code-block:: python

    CellpyData.headers_normal["aci_phase_angle_txt"] = "aci_phase_angle"
    CellpyData.headers_normal["ref_aci_phase_angle_txt"] = "ref_aci_phase_angle"
    CellpyData.headers_normal["ac_impedance_txt"] = "ac_impedance"
    CellpyData.headers_normal["ref_ac_impedance_txt"] = "ref_ac_impedance"
    CellpyData.headers_normal["charge_capacity_txt"] = "charge_capacity"
    CellpyData.headers_normal["charge_energy_txt"] = "charge_energy"
    CellpyData.headers_normal["current_txt"] = "current"
    CellpyData.headers_normal["cycle_index_txt"] = "cycle_index"
    CellpyData.headers_normal["data_point_txt"] = "data_point"
    CellpyData.headers_normal["datetime_txt"] = "date_time"
    CellpyData.headers_normal["discharge_capacity_txt"] = "discharge_capacity"
    CellpyData.headers_normal["discharge_energy_txt"] = "discharge_energy"
    CellpyData.headers_normal["internal_resistance_txt"] = "internal_resistance"
    CellpyData.headers_normal["is_fc_data_txt"] = "is_fc_data"
    CellpyData.headers_normal["step_index_txt"] = "step_index"
    CellpyData.headers_normal["sub_step_index_txt"] = "sub_step_index"
    CellpyData.headers_normal["step_time_txt"] = "step_time"
    CellpyData.headers_normal["sub_step_time_txt"] = "sub_step_time"
    CellpyData.headers_normal["test_id_txt"] = "test_id"
    CellpyData.headers_normal["test_time_txt"] = "test_time"
    CellpyData.headers_normal["voltage_txt"] = "voltage"
    CellpyData.headers_normal["ref_voltage_txt"] = "reference_voltage"
    CellpyData.headers_normal["dv_dt_txt"] = "dv_dt"
    CellpyData.headers_normal["frequency_txt"] = "frequency"
    CellpyData.headers_normal["amplitude_txt"] = "amplitude"

column headings - summary data
..............................

.. code-block:: python

    CellpyData.headers_summary["cycle_index"] = headers_normal["cycle_index_txt"]
    CellpyData.headers_summary["data_point"] = headers_normal["data_point_txt"]
    CellpyData.headers_summary["test_time"] = headers_normal["test_time_txt"]
    CellpyData.headers_summary["datetime"] = headers_normal["datetime_txt"]
    CellpyData.headers_summary["discharge_capacity_raw"] = headers_normal["discharge_capacity_txt"]
    CellpyData.headers_summary["charge_capacity_raw"] = headers_normal["charge_capacity_txt"]
    CellpyData.headers_summary["discharge_capacity"] = "discharge_capacity_u_mAh_g"
    CellpyData.headers_summary["charge_capacity"] = "charge_capacity_u_mAh_g"
    CellpyData.headers_summary["cumulated_charge_capacity"] = "cumulated_charge_capacity_u_mAh_g"
    CellpyData.headers_summary["cumulated_discharge_capacity"] = "cumulated_discharge_capacity_u_mAh_g"
    CellpyData.headers_summary["coulombic_efficiency"] = "coulombic_efficiency_u_percentage"
    CellpyData.headers_summary[
        "cumulated_coulombic_efficiency"
    ] = "cumulated_coulombic_efficiency_u_percentage"
    CellpyData.headers_summary["coulombic_difference"] = "coulombic_difference_u_mAh_g"
    CellpyData.headers_summary[
        "cumulated_coulombic_difference"
    ] = "cumulated_coulombic_difference_u_mAh_g"
    CellpyData.headers_summary["discharge_capacity_loss"] = "discharge_capacity_loss_u_mAh_g"
    CellpyData.headers_summary["charge_capacity_loss"] = "charge_capacity_loss_u_mAh_g"
    CellpyData.headers_summary[
        "cumulated_discharge_capacity_loss"
    ] = "cumulated_discharge_capacity_loss_u_mAh_g"
    CellpyData.headers_summary[
        "cumulated_charge_capacity_loss"
    ] = "cumulated_charge_capacity_loss_u_mAh_g"
    CellpyData.headers_summary["ir_discharge"] = "ir_discharge_u_Ohms"
    CellpyData.headers_summary["ir_charge"] = "ir_charge_u_Ohms"
    CellpyData.headers_summary["ocv_first_min"] = "ocv_first_min_u_V"
    CellpyData.headers_summary["ocv_second_min"] = "ocv_second_min_u_V"
    CellpyData.headers_summary["ocv_first_max"] = "ocv_first_max_u_V"
    CellpyData.headers_summary["ocv_second_max"] = "ocv_second_max_u_V"
    CellpyData.headers_summary["end_voltage_discharge"] = "end_voltage_discharge_u_V"
    CellpyData.headers_summary["end_voltage_charge"] = "end_voltage_charge_u_V"
    CellpyData.headers_summary["cumulated_ric_disconnect"] = "cumulated_ric_disconnect_u_none"
    CellpyData.headers_summary["cumulated_ric_sei"] = "cumulated_ric_sei_u_none"
    CellpyData.headers_summary["cumulated_ric"] = "cumulated_ric_u_none"
    CellpyData.headers_summary["normalized_cycle_index"] = "normalized_cycle_index"
    CellpyData.headers_summary["normalized_charge_capacity"] = "normalized_charge_capacity"
    CellpyData.headers_summary["normalized_discharge_capacity"] = "normalized_discharge_capacity"

    # Sum of irreversible capacity:
    CellpyData.headers_summary["low_level"] = "low_level_u_percentage"
    # SEI loss:
    CellpyData.headers_summary["high_level"] = "high_level_u_percentage"
    # Shifted capacities:
    CellpyData.headers_summary["shifted_charge_capacity"] = "shifted_charge_capacity_u_mAh_g"
    CellpyData.headers_summary["shifted_discharge_capacity"] = "shifted_discharge_capacity_u_mAh_g"
    # Other
    CellpyData.headers_summary["temperature_last"] = "temperature_last_u_C"
    CellpyData.headers_summary["temperature_mean"] = "temperature_mean_u_C"
    CellpyData.headers_summary["areal_charge_capacity"] = "areal_charge_capacity_u_mAh_cm2"
    CellpyData.headers_summary["areal_discharge_capacity"] = "areal_discharge_capacity_u_mAh_cm2"
    CellpyData.headers_summary["charge_c_rate"] = "charge_c_rate"
    CellpyData.headers_summary["discharge_c_rate"] = "discharge_c_rate"
    CellpyData.headers_summary["pre_aux"] = "aux_"

column headings - step table
............................

.. code-block:: python

    CellpyData.headers_step_table["test"] = "test"
    CellpyData.headers_step_table["ustep"] = "ustep"
    CellpyData.headers_step_table["cycle"] = "cycle"
    CellpyData.headers_step_table["step"] = "step"
    CellpyData.headers_step_table["test_time"] = "test_time"
    CellpyData.headers_step_table["step_time"] = "step_time"
    CellpyData.headers_step_table["sub_step"] = "sub_step"
    CellpyData.headers_step_table["type"] = "type"
    CellpyData.headers_step_table["sub_type"] = "sub_type"
    CellpyData.headers_step_table["info"] = "info"
    CellpyData.headers_step_table["voltage"] = "voltage"
    CellpyData.headers_step_table["current"] = "current"
    CellpyData.headers_step_table["charge"] = "charge"
    CellpyData.headers_step_table["discharge"] = "discharge"
    CellpyData.headers_step_table["point"] = "point"
    CellpyData.headers_step_table["internal_resistance"] = "ir"
    CellpyData.headers_step_table["internal_resistance_change"] = "ir_pct_change"
    CellpyData.headers_step_table["rate_avr"] = "rate_avr"


column headings - journal pages
...............................

.. code-block:: python

    CellpyData.headers_journal["filename"] = "filename"
    CellpyData.headers_journal["mass"] = "mass"
    CellpyData.headers_journal["total_mass"] = "total_mass"
    CellpyData.headers_journal["loading"] = "loading"
    CellpyData.headers_journal["nom_cap"] = "nom_cap"
    CellpyData.headers_journal["experiment"] = "experiment"
    CellpyData.headers_journal["fixed"] = "fixed"
    CellpyData.headers_journal["label"] = "label"
    CellpyData.headers_journal["cell_type"] = "cell_type"
    CellpyData.headers_journal["raw_file_names"] = "raw_file_names"
    CellpyData.headers_journal["cellpy_file_name"] = "cellpy_file_name"
    CellpyData.headers_journal["group"] = "group"
    CellpyData.headers_journal["sub_group"] = "sub_group"
    CellpyData.headers_journal["comment"] = "comment"

    CellpyData.keys_journal_session = ["starred", "bad_cells", "bad_cycles", "notes"]


step types
..........

Identifiers for the different steps have pre-defined names given in the
class attribute list `list_of_step_types` and is written to the "step" column.

.. code-block:: python

    list_of_step_types = ['charge', 'discharge',
                          'cv_charge', 'cv_discharge',
                          'charge_cv', 'discharge_cv',
                          'ocvrlx_up', 'ocvrlx_down', 'ir',
                          'rest', 'not_known']


For each type of testers that are supported by ``cellpy``,
a set of column headings and
other different settings/attributes must be provided. These definitions are now put
inside the CellpyData class, but will be moved out later.

Supported testers are:

* arbin (.res type files)

Testers that are partly supported (but not tested very well) are:

* biologic
* pec

Testers that is planned supported:

* arbin (ms sql-server)
* maccor


Tester dependent attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

arbin .res
..........

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

Cells
~~~~~

Each run is a `cellpy.cellreader.Cell` instance.
The instance contain general information about
the run-settings (such as mass etc.).
The measurement data, information, and summary is stored
in three pandas.DataFrames:

* ``raw``: raw data from the run.
* ``steps``: stats from each step (and step type).
* ``summary``  summary data vs. cycle number (e.g. coulombic coulombic efficiency)

Todo.

FileID
~~~~~~

Todo
