.. highlight:: shell

================================
File Formats and Data Structures
================================

.. warning::
   This part of the documentation is currently being updated.
   It is 99.9% trustable, but in need of better logical structure and formatting.


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

    CellpyData.tester = "arbin_res"
    CellpyData.auto_dirs = True
    print(CellpyData.cellpy_datadir)


The data for the experiment(s)/runs(s) are stored in the class attribute
``CellpyData.cells``
This attribute is just a list of runs (each run is a
``cellpy.cellreader.Cell`` instance).
This implies that you can store many runs in one ``CellpyData`` instance.
Sometimes this can be necessary, but it is recommended to only store one
run in one instance. Most of the functions (the class methods) automatically
selects the 0-th item in ``CellpyData.cells`` if the ``test_number`` is not
explicitly given.

You may already have figured it out: in cellpy, data for a given cell
is usually named a run. And each run is a ``cellpy.cellreader.Cell`` instance.

Here is a list of other important class attributes in ``CellpyData``:

Column headings
...............
``cellpy`` uses ``pandas.DataFrame`` objects internally. The column headers
of the dataframes are defined in corresponding dataclass objects that can be
accessed using both dot-notation and through normal dictionary look-up.

All the headers are set internally in ``cellpy`` and you can get them directly
by e.g.

.. code-block:: python

    from cellpy.parameters.internal_settings import headers_normal

    cycle_column_header = headers_normal.cycle_index_txt

column headings - raw data (or "normal" data)
'''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: python

    @dataclass
    class HeadersNormal(BaseSettings):
        aci_phase_angle_txt: str = "aci_phase_angle"
        ref_aci_phase_angle_txt: str = "ref_aci_phase_angle"
        ac_impedance_txt: str = "ac_impedance"
        ref_ac_impedance_txt: str = "ref_ac_impedance"
        charge_capacity_txt: str = "charge_capacity"
        charge_energy_txt: str = "charge_energy"
        current_txt: str = "current"
        cycle_index_txt: str = "cycle_index"
        data_point_txt: str = "data_point"
        datetime_txt: str = "date_time"
        discharge_capacity_txt: str = "discharge_capacity"
        discharge_energy_txt: str = "discharge_energy"
        internal_resistance_txt: str = "internal_resistance"
        is_fc_data_txt: str = "is_fc_data"
        step_index_txt: str = "step_index"
        sub_step_index_txt: str = "sub_step_index"
        step_time_txt: str = "step_time"
        sub_step_time_txt: str = "sub_step_time"
        test_id_txt: str = "test_id"
        test_time_txt: str = "test_time"
        voltage_txt: str = "voltage"
        ref_voltage_txt: str = "reference_voltage"
        dv_dt_txt: str = "dv_dt"
        frequency_txt: str = "frequency"
        amplitude_txt: str = "amplitude"
        channel_id_txt: str = "channel_id"
        data_flag_txt: str = "data_flag"
        test_name_txt: str = "test_name"

column headings - summary data
''''''''''''''''''''''''''''''

.. code-block:: python

    @dataclass
    class HeadersSummary(BaseSettings):
        cycle_index: str = "cycle_index"
        data_point: str = "data_point"
        test_time: str = "test_time"
        datetime: str = "date_time"
        discharge_capacity_raw: str = "discharge_capacity"
        charge_capacity_raw: str = "charge_capacity"
        test_name: str = "test_name"
        data_flag: str = "data_flag"
        channel_id: str = "channel_id"
        discharge_capacity: str = "discharge_capacity_u_mAh_g"
        charge_capacity: str = "charge_capacity_u_mAh_g"
        cumulated_charge_capacity: str = "cumulated_charge_capacity_u_mAh_g"
        cumulated_discharge_capacity: str = "cumulated_discharge_capacity_u_mAh_g"
        coulombic_efficiency: str = "coulombic_efficiency_u_percentage"
        cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency_u_percentage"
        coulombic_difference: str = "coulombic_difference_u_mAh_g"
        cumulated_coulombic_difference: str = "cumulated_coulombic_difference_u_mAh_g"
        discharge_capacity_loss: str = "discharge_capacity_loss_u_mAh_g"
        charge_capacity_loss: str = "charge_capacity_loss_u_mAh_g"
        cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss_u_mAh_g"
        cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss_u_mAh_g"
        ir_discharge: str = "ir_discharge_u_Ohms"
        ir_charge: str = "ir_charge_u_Ohms"
        ocv_first_min: str = "ocv_first_min_u_V"
        ocv_second_min: str = "ocv_second_min_u_V"
        ocv_first_max: str = "ocv_first_max_u_V"
        ocv_second_max: str = "ocv_second_max_u_V"
        end_voltage_discharge: str = "end_voltage_discharge_u_V"
        end_voltage_charge: str = "end_voltage_charge_u_V"
        cumulated_ric_disconnect: str = "cumulated_ric_disconnect_u_none"
        cumulated_ric_sei: str = "cumulated_ric_sei_u_none"
        cumulated_ric: str = "cumulated_ric_u_none"
        normalized_cycle_index: str = "normalized_cycle_index"
        normalized_charge_capacity: str = "normalized_charge_capacity"
        normalized_discharge_capacity: str = "normalized_discharge_capacity"
        low_level: str = "low_level_u_percentage"
        high_level: str = "high_level_u_percentage"
        shifted_charge_capacity: str = "shifted_charge_capacity_u_mAh_g"
        shifted_discharge_capacity: str = "shifted_discharge_capacity_u_mAh_g"
        temperature_last: str = "temperature_last_u_C"
        temperature_mean: str = "temperature_mean_u_C"
        areal_charge_capacity: str = "areal_charge_capacity_u_mAh_cm2"
        areal_discharge_capacity: str = "areal_discharge_capacity_u_mAh_cm2"
        charge_c_rate: str = "charge_c_rate"
        discharge_c_rate: str = "discharge_c_rate"
        pre_aux: str = "aux_"


column headings - step table
............................

.. code-block:: python

    @dataclass
    class HeadersStepTable(BaseSettings):
        test: str = "test"
        ustep: str = "ustep"
        cycle: str = "cycle"
        step: str = "step"
        test_time: str = "test_time"
        step_time: str = "step_time"
        sub_step: str = "sub_step"
        type: str = "type"
        sub_type: str = "sub_type"
        info: str = "info"
        voltage: str = "voltage"
        current: str = "current"
        charge: str = "charge"
        discharge: str = "discharge"
        point: str = "point"
        internal_resistance: str = "ir"
        internal_resistance_change: str = "ir_pct_change"
        rate_avr: str = "rate_avr"

column headings - journal pages
...............................

.. code-block:: python

    @dataclass
    class HeadersJournal(BaseSettings):
        filename: str = "filename"
        mass: str = "mass"
        total_mass: str = "total_mass"
        loading: str = "loading"
        nom_cap: str = "nom_cap"
        experiment: str = "experiment"
        fixed: str = "fixed"
        label: str = "label"
        cell_type: str = "cell_type"
        instrument: str = "instrument"
        raw_file_names: str = "raw_file_names"
        cellpy_file_name: str = "cellpy_file_name"
        group: str = "group"
        sub_group: str = "sub_group"
        comment: str = "comment"


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
other different settings/attributes must be provided. These definitions stored in the
``cellpy.parameters.internal_settings`` module and are also injected into
the CellpyData class upon initiation.

Supported testers are:

* arbin (.res type files)

Testers that are partly supported (but not tested very well) are:

* pec (txt files)
* arbin (ms sql-server and .csv and .xlsx exports)
* maccor (txt files)

Testers that is planned supported:

* biologic
* maccor

In addition, ``cellpy`` can load custom csv-ish files by providing a file description (using the
``ìnstruments.Custom`` object).


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

arbin MS SQL SERVER
...................

TODO...


PEC .csv
........

TODO...


Maccor .txt
...........

TODO...


CellpyData - methods
~~~~~~~~~~~~~~~~~~~~

The ``CellpyData`` object contains lots of methods for manipulating, extracting
and summarising the data from the run(s). Two methods are typically automatically run when
you create your ``CellpyData`` object when running ``cellpy.get(filename)``:

    - ``make_step_table``: creates a statistical summary of all the steps in the run(s) and categorizes
      the step type from that. It is also possible to give the step types directly (step_specifications).

    - ``make_summary``: create a summary based on cycle number.

Other methods worth mentioning are (based on what I typically use):

    - ``load``: load a cellpy file.

    - ``load_raw``: load raw data file(s) (merges automatically if several filenames are given as a list).

    - ``get_cap``: get the capacity-voltage graph from one or more cycles in three different formats as well
      as optionally interpolated, normalized and/or scaled.

    - ``get_cycle_numbers``: get the cycle numbers for your run.

    - ``get_ocv``: get the rest steps after each charge and discharge step.

Take a look at API section (Module index, ``cellpy.readers.cellreader.CellpyData``) for more info.

Cells
~~~~~

Each run is a ``cellpy.cellreader.Cell`` instance.
The instance contain general information about
the run-settings (such as mass etc.).
The measurement data, information, and summary is stored
in three ``pandas.DataFrames``:

    - ``raw``: raw data from the run.
    - ``steps``: stats from each step (and step type), created using the
      ``CellpyData.make_step_table`` method.
    - ``summary``: summary data vs. cycle number (e.g. coulombic coulombic efficiency), created using
      the ``CellpyData.make_summary`` method.

The headers (columns) for the different DataFrames were given earlier in this chapter.
As mentioned above, the ``Cell`` object also contains metadata for the run.

metadata
........

.. code-block:: python

    cell_no = None
    mass = prms.Materials.default_mass  # active material (in mg)
    tot_mass = prms.Materials.default_mass  # total material (in mg)
    no_cycles = 0.0
    charge_steps = None
    discharge_steps = None
    ir_steps = None
    ocv_steps = None
    nom_cap = prms.DataSet.nom_cap  # mAh/g (for finding c-rates)
    mass_given = False
    material = prms.Materials.default_material
    merged = False
    file_errors = None  # not in use at the moment
    loaded_from = None  # loaded from (can be list if merged)
    channel_index = None
    channel_number = None
    creator = None
    item_ID = None
    schedule_file_name = None
    start_datetime = None
    test_ID = None
    name = None
    cycle_mode = prms.Reader.cycle_mode
    active_electrode_area = None  # [cm2]
    active_electrode_thickness = None  # [micron]
    electrolyte_type = None  #
    electrolyte_volume = None  # [micro-liter]
    active_electrode_type = None
    counter_electrode_type = None
    reference_electrode_type = None
    experiment_type = None
    cell_type = None
    separator_type = None
    active_electrode_current_collector = None
    reference_electrode_current_collector = None
    comment = None


The ``Cell`` object can also take custom metadata if provieded as keyword arguments (for developers).

FileID
~~~~~~

The ``FileID`` object contains information about the raw file(s) and is used when comparing the cellpy-file
with the raw file(s) (for example to check if it has been updated compared to the cellpy-file).
Notice that ``FileID`` will contain a list of file identification parameters if the run is from several raw files.
