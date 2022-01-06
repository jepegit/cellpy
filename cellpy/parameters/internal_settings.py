"""Internal settings and definitions and functions for getting them."""
from collections import UserDict
from dataclasses import dataclass, fields


# TODO: remove import of this
class HeaderDict(UserDict):
    """Sub-classing dict to allow for tab-completion."""

    def __setitem__(self, key: str, value: str) -> None:
        if key == "data":
            raise KeyError("protected key")
        super().__setitem__(key, value)
        self.__dict__[key] = value


@dataclass
class DictLikeClass:
    """Add some dunder-methods so that it does not break old code that used
    dictionaries for storing settings

    Remark! it is not a complete dictionary experience - for example,
        setting new attributes (new keys) is not supported (raises KeyError
        if using the typical dict setting method) since it uses the
        dataclasses.fields method to find its members.

    """

    def __getitem__(self, key):
        try:
            v = getattr(self, key)
            return v
        except AttributeError:
            raise KeyError(f"missing key: {key}")

    def __setitem__(self, key, value):
        if key not in self._field_names:
            raise KeyError(f"creating new key not allowed: {key}")
        setattr(self, key, value)

    def __missing__(self, key):
        raise KeyError

    @property
    def _field_names(self):
        return [field.name for field in fields(self)]

    def __iter__(self):
        for field in self._field_names:
            yield field

    def _value_iter(self):
        for field in self._field_names:
            yield getattr(self, field)

    def keys(self):
        return [key for key in self.__iter__()]

    def values(self):
        return [v for v in self._value_iter()]

    def items(self):
        return zip(self.keys(), self.values())


@dataclass
class BaseSettings(DictLikeClass):
    """Base class for internal cellpy settings.

    Usage:
        @dataclass
        class MyCoolCellpySetting(BaseSetting):
            var1: str = "first var"
            var2: int = 12

    """

    ...


@dataclass
class InstrumentSettings(DictLikeClass):
    """Base class for instrument settings.

    Usage:
        @dataclass
        class MyCoolInstrumentSetting(InstrumentSettings):
            var1: str = "first var"
            var2: int = 12

    Remark!:
        Try to use it as you would use a normal dataclass.

    """

    ...


@dataclass
class CellpyUnits(BaseSettings):
    current: float = 0.001
    charge: float = 0.001
    mass: float = 0.001
    specific: float = 1.0
    voltage: float = 1.0


@dataclass
class CellpyLimits(BaseSettings):
    current_hard: float = 1e-13
    current_soft: float = 1e-05
    stable_current_hard: float = 2.0
    stable_current_soft: float = 4.0
    stable_voltage_hard: float = 2.0
    stable_voltage_soft: float = 4.0
    stable_charge_hard: float = 0.9
    stable_charge_soft: float = 5.0
    ir_change: float = 1e-05


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


keys_journal_session = ["starred", "bad_cells", "bad_cycles", "notes"]

cellpy_units = CellpyUnits()
cellpy_limits = CellpyLimits()
headers_step_table = HeadersStepTable()
headers_journal = HeadersJournal()
headers_summary = HeadersSummary()
headers_normal = HeadersNormal()

# cellpy attributes that should be loaded from cellpy-files:

ATTRS_CELLPYFILE = [
    "mass",
    "channel_index",
    "channel_number",
    "creator",
    "cycle_mode",
    "schedule_file_name",
    "start_datetime",
    "test_ID",
    "cell_no",
    "name",
    "nom_cap",
    "material",
    "item_ID",
    "active_electrode_area",
    "active_electrode_thickness",
    "electrolyte_type",
    "electrolyte_volume",
    "active_electrode_type",
    "counter_electrode_type",
    "reference_electrode_type",
    "experiment_type",
    "active_electrode_current_collector",
    "reference_electrode_current_collector",
    "comment",
]

# Attributes that should be copied when duplicating cellpy objects:

# current attributes for the cellpy.cellpydata objects
ATTRS_CELLPYDATA = [
    "auto_dirs",
    "capacity_modifiers",
    "cellpy_datadir",
    "daniel_number",
    "ensure_step_table",
    "file_names",
    "filestatuschecker",
    "force_all",
    "force_step_table_creation",
    "forced_errors",
    "limit_loaded_cycles",
    "load_only_summary",
    "minimum_selection",
    "name",
    "number_of_datasets",
    "profile",
    "raw_datadir",
    "raw_limits",
    "raw_units",
    "select_minimal",
    "selected_cell_number",
    "selected_scans",
    "sep",
    "status_datasets",
    "summary_exists",
    "table_names",
    "tester",
]

# current attributes used for the cellpy.cell objects
ATTRS_DATASET = [
    "cellpy_file_version",
    "channel_index",
    "channel_number",
    "charge_steps",
    "creator",
    "cycle_mode",
    # "data",
    "discharge_steps",
    "file_errors",
    "ir_steps",
    "item_ID",
    "loaded_from",
    "mass",
    "mass_given",
    "material",
    "merged",
    "name",
    "no_cycles",
    "nom_cap",
    "ocv_steps",
    "raw_data_files_length",
    "raw_limits",
    "raw_units",
    "schedule_file_name",
    "start_datetime",
    # "summary",
    "test_ID",
    "cell_no",
    "tot_mass",
]

ATTRS_DATASET_DEEP = ["raw_data_files"]


def get_headers_summary() -> BaseSettings:
    """Returns a dictionary containing the header-strings for the summary
    (used as column headers for the summary pandas DataFrames)"""
    # maybe I can do some tricks in here so that tab completion works?
    # ctrl + space works
    return headers_summary


def get_cellpy_units() -> CellpyUnits:
    """Returns a dictionary with units"""
    return cellpy_units


def get_headers_normal() -> HeadersNormal:
    """Returns a dictionary containing the header-strings for the normal data
    (used as column headers for the main data pandas DataFrames)"""
    return headers_normal


def get_headers_step_table() -> HeadersStepTable:
    """Returns a dictionary containing the header-strings for the steps table
    (used as column headers for the steps pandas DataFrames)"""
    return headers_step_table


def get_headers_journal() -> HeadersJournal:
    """Returns a dictionary containing the header-strings for the journal (batch)
    (used as column headers for the journal pandas DataFrames)"""
    return headers_journal
