"""Internal settings and definitions and functions for getting them."""
import logging
import warnings
from collections import UserDict
from dataclasses import dataclass, fields
from typing import List

CELLPY_FILE_VERSION = 7
MINIMUM_CELLPY_FILE_VERSION = 4
STEP_TABLE_VERSION = 5
RAW_TABLE_VERSION = 5
SUMMARY_TABLE_VERSION = 7
# if you change this, remember that both loading and saving uses this
# constant at the moment, and check that loading old files still works
# - and possibly refactor so that the old-file loaders contain the
# appropriate pickle protocol:
PICKLE_PROTOCOL = 4


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
        if key not in self._field_names:
            logging.debug(f"{key} not in fields")
        try:
            return getattr(self, key)
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

    def get(self, key):
        """Get the value (postfixes not supported)."""
        if key not in self.keys():
            logging.critical(f"the column header '{key}' not found")
            return
        else:
            return self[key]


@dataclass
class BaseHeaders(BaseSettings):
    """Extending BaseSetting so that it's allowed to add postfixes.

    Example:
         >>> header["key_postfix"]  # returns "value_postfix"
    """

    postfixes = []

    def __getitem__(self, key):
        postfix = ""
        if key not in self._field_names:
            # check postfix:
            subs = key.split("_")
            _key = "_".join(subs[:-1])
            _postfix = subs[-1]
            if _postfix in self.postfixes:
                postfix = f"_{_postfix}"
                key = _key
        try:
            v = getattr(self, key)
            return f"{v}{postfix}"
        except AttributeError:
            raise KeyError(f"missing key: {key}")


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
    """These are the units used inside Cellpy.

    At least two sets of units needs to be defined; `cellpy_units` and `raw_units`.
    The `data.raw` dataframe is given in `raw_units` where the units are defined
    inside the instrument loader used. Since the `data.steps` dataframe is a summary of
    the step statistics from the `data.raw` dataframe, this also uses the `raw_units`.
    The `data.summary` dataframe contains columns with values directly from the `data.raw` dataframe
    given in `raw_units` as well as calculated columns given in `cellpy_units`.

    Remark that all input to cellpy through user interaction (or utils) should be in `cellpy_units`.
    This is also true for meta-data collected from the raw files. The instrument loader needs to
    take care of the translation from its raw units to `cellpy_units` during loading the raw data
    file for the meta-data (remark that this is not necessary and not recommended for the actual
    "raw" data that is going to be stored in the `data.raw` dataframe).

    As of 2022.09.29, cellpy does not automatically ensure unit conversion for input of meta-data,
    but has an internal method (`CellPyData.to_cellpy_units`) that can be used.

    These are the different attributes currently supported for data in the dataframes:

        current: str = "A"
        charge: str = "mAh"
        voltage: str = "V"
        time: str = "sec"
        resistance: str = "Ohms"
        power: str = "W"
        energy: str = "Wh"
        frequency: str = "hz"

    And here are the different attributes currently supported for meta-data:

        # output-units for specific capacity etc.
        specific_gravimetric: str = "g"
        specific_areal: str = "cm**2"  # used for calculating specific capacity etc.
        specific_volumetric: str = "cm**3"  # used for calculating specific capacity etc.

        # other meta-data
        nominal_capacity: str = "mAh/g"  # used for calculating rates etc.
        mass: str = "mg"
        length: str = "cm"
        area: str = "cm**2"
        volume: str = "cm**3"
        temperature: str = "C"

    """

    current: str = "A"
    charge: str = "mAh"
    voltage: str = "V"
    time: str = "sec"
    resistance: str = "Ohms"
    power: str = "W"
    energy: str = "Wh"
    frequency: str = "hz"
    mass: str = "mg"  # for mass
    nominal_capacity: str = "mAh/g"
    specific_gravimetric: str = "g"  # g in specific capacity etc
    specific_areal: str = "cm**2"  # m2 in specific capacity etc
    specific_volumetric: str = "cm**3"  # m3 in specific capacity etc

    length: str = "cm"
    area: str = "cm**2"
    volume: str = "cm**3"
    temperature: str = "C"


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
class HeadersNormal(BaseHeaders):
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
    power_txt: str = "power"
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
class HeadersSummary(BaseHeaders):
    """In addition to the headers defined here, the summary might also contain
    specific headers (ending in _gravimetric or _areal).
    """

    postfixes = ["gravimetric", "areal"]

    cycle_index: str = "cycle_index"
    data_point: str = "data_point"
    test_time: str = "test_time"
    datetime: str = "date_time"
    discharge_capacity_raw: str = "discharge_capacity"
    charge_capacity_raw: str = "charge_capacity"
    test_name: str = "test_name"
    data_flag: str = "data_flag"
    channel_id: str = "channel_id"

    coulombic_efficiency: str = "coulombic_efficiency"
    cumulated_coulombic_efficiency: str = "cumulated_coulombic_efficiency"

    discharge_capacity: str = "discharge_capacity"
    charge_capacity: str = "charge_capacity"
    cumulated_charge_capacity: str = "cumulated_charge_capacity"
    cumulated_discharge_capacity: str = "cumulated_discharge_capacity"

    coulombic_difference: str = "coulombic_difference"
    cumulated_coulombic_difference: str = "cumulated_coulombic_difference"
    discharge_capacity_loss: str = "discharge_capacity_loss"
    charge_capacity_loss: str = "charge_capacity_loss"
    cumulated_discharge_capacity_loss: str = "cumulated_discharge_capacity_loss"
    cumulated_charge_capacity_loss: str = "cumulated_charge_capacity_loss"

    normalized_charge_capacity: str = "normalized_charge_capacity"
    normalized_discharge_capacity: str = "normalized_discharge_capacity"

    shifted_charge_capacity: str = "shifted_charge_capacity"
    shifted_discharge_capacity: str = "shifted_discharge_capacity"

    ir_discharge: str = "ir_discharge"
    ir_charge: str = "ir_charge"
    ocv_first_min: str = "ocv_first_min"
    ocv_second_min: str = "ocv_second_min"
    ocv_first_max: str = "ocv_first_max"
    ocv_second_max: str = "ocv_second_max"
    end_voltage_discharge: str = "end_voltage_discharge"
    end_voltage_charge: str = "end_voltage_charge"
    cumulated_ric_disconnect: str = "cumulated_ric_disconnect"
    cumulated_ric_sei: str = "cumulated_ric_sei"
    cumulated_ric: str = "cumulated_ric"
    normalized_cycle_index: str = "normalized_cycle_index"
    low_level: str = "low_level"
    high_level: str = "high_level"

    temperature_last: str = "temperature_last"
    temperature_mean: str = "temperature_mean"

    charge_c_rate: str = "charge_c_rate"
    discharge_c_rate: str = "discharge_c_rate"
    pre_aux: str = "aux_"

    @property
    def areal_charge_capacity(self) -> str:
        warnings.warn(
            "using old-type look-up (areal_charge_capacity) -> will be deprecated soon",
            DeprecationWarning,
            stacklevel=2,
        )
        return f"{self.charge_capacity}_areal"

    @property
    def areal_discharge_capacity(self) -> str:
        warnings.warn(
            "using old-type look-up (areal_discharge_capacity) -> will be deprecated soon",
            DeprecationWarning,
            stacklevel=2,
        )
        return f"{self.discharge_capacity}_areal"

    @property
    def specific_columns(self) -> List[str]:
        return [
            self.discharge_capacity,
            self.charge_capacity,
            self.cumulated_charge_capacity,
            self.cumulated_discharge_capacity,
            self.coulombic_difference,
            self.cumulated_coulombic_difference,
            self.discharge_capacity_loss,
            self.charge_capacity_loss,
            self.cumulated_discharge_capacity_loss,
            self.cumulated_charge_capacity_loss,
            self.shifted_charge_capacity,
            self.shifted_discharge_capacity,
            # self.cumulated_ric_disconnect,
            # self.cumulated_ric_sei,
            # self.cumulated_ric,
            # self.normalized_cycle_index,
        ]


@dataclass
class HeadersStepTable(BaseHeaders):
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
class HeadersJournal(BaseHeaders):
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
    argument: str = "argument"


keys_journal_session = ["starred", "bad_cells", "bad_cycles", "notes"]

headers_step_table = HeadersStepTable()
headers_journal = HeadersJournal()
headers_summary = HeadersSummary()
headers_normal = HeadersNormal()
cellpy_units = CellpyUnits()

base_columns_float = [
    headers_normal.test_time_txt,
    headers_normal.step_time_txt,
    headers_normal.current_txt,
    headers_normal.voltage_txt,
    headers_normal.ref_voltage_txt,
    headers_normal.charge_capacity_txt,
    headers_normal.discharge_capacity_txt,
    headers_normal.internal_resistance_txt,
]

base_columns_int = [
    headers_normal.data_point_txt,
    headers_normal.step_index_txt,
    headers_normal.cycle_index_txt,
]


# cellpy attributes that should be saved and loaded from cellpy-files
# (only uses the Data object):
ATTRS_CELLPYFILE = [
    # -- about the test(s):
    "test_ID",
    "channel_index",
    "creator",
    "cycle_mode",
    "schedule_file_name",
    "experiment_type",
    "comment",
    # -- new
    "tester_ID",
    "tester_server_software_version",
    "tester_client_software_version",
    "tester_calibration_date",
    # -- about the cell:
    "start_datetime",
    "cell_name",
    "mass",
    "nom_cap",
    "nom_cap_specifics",
    "material",
    "active_electrode_area",
    "active_electrode_thickness",
    "electrolyte_type",
    "electrolyte_volume",
    "active_electrode_type",
    "counter_electrode_type",
    "reference_electrode_type",
    "active_electrode_current_collector",
    "reference_electrode_current_collector",
    # -- new
    "time_zone",
    "cell_type",
]

# Attributes that should be copied when duplicating cellpy objects:

# current attributes for the CellpyCell objects
ATTRS_CELLPYDATA = [
    "auto_dirs",
    "capacity_modifiers",
    "cellpy_datadir",
    "ensure_step_table",
    "file_names",
    "filestatuschecker",
    "force_all",
    "force_step_table_creation",
    "forced_errors",
    "limit_loaded_cycles",
    "minimum_selection",
    "session_name",
    "profile",
    "raw_datadir",
    "raw_limits",
    "select_minimal",
    "selected_cell_number",
    "selected_scans",
    "sep",
    "status_datasets",
    "summary_exists",
    "table_names",
    "tester",
]

# current attributes used for the cellpy.Data objects
ATTRS_DATASET = [
    "cellpy_file_version",
    "channel_index",
    "creator",
    "cycle_mode",
    "file_errors",
    "loaded_from",
    "mass",
    "material",
    "cell_name",
    "nom_cap",
    "raw_data_files_length",
    "raw_limits",
    "raw_units",
    "schedule_file_name",
    "start_datetime",
    "test_ID",
    "tot_mass",
    "time_zone",
]

ATTRS_DATASET_DEEP = ["raw_data_files"]


def get_cellpy_units() -> CellpyUnits:
    """Returns an augmented global dictionary with units"""
    return cellpy_units


def get_default_output_units() -> CellpyUnits:
    """Returns an augmented dictionary with units to use as default."""
    return CellpyUnits()


def get_default_cellpy_file_raw_units() -> CellpyUnits:
    """Returns a dictionary with units to use as default for old versions of cellpy files"""
    return CellpyUnits(
        charge="Ah",
        mass="mg",
    )


def get_default_raw_units() -> CellpyUnits:
    """Returns a dictionary with units as default for raw data"""
    return CellpyUnits(
        charge="Ah",
        mass="mg",
    )


def get_default_raw_limits() -> CellpyLimits:
    """Returns an augmented dictionary with units as default for raw data"""
    return CellpyLimits()


def get_headers_normal() -> HeadersNormal:
    """Returns an augmented global dictionary containing the header-strings for the normal data
    (used as column headers for the main data pandas DataFrames)"""
    return headers_normal


def get_headers_step_table() -> HeadersStepTable:
    """Returns an augmented global dictionary containing the header-strings for the steps table
    (used as column headers for the steps pandas DataFrames)"""
    return headers_step_table


def get_headers_journal() -> HeadersJournal:
    """Returns an augmented global dictionary containing the header-strings for the journal (batch)
    (used as column headers for the journal pandas DataFrames)"""
    return headers_journal


def get_headers_summary() -> HeadersSummary:
    """Returns an augmented global dictionary containing the header-strings for the summary
    (used as column headers for the summary pandas DataFrames)"""
    return headers_summary


def get_default_custom_headers_summary() -> HeadersSummary:
    """Returns an augmented dictionary that can be used to create custom header-strings for the summary
    (used as column headers for the summary pandas DataFrames)

    This function is mainly implemented to provide an example.

    """
    # maybe I can do some tricks in here so that tab completion works in pycharm?
    # solution: ctrl + space works
    return HeadersSummary()
