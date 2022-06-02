""" Very simple implementation of a plugin-like infrastructure"""
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

from ruamel import yaml

# TODO: make tests.
# TODO: move this into its own module (not __init__).
# TODO: document for devs.
# TODO: Bonus - make a python package/pre-commit hook that
# turns TODO-statements into issues.

HARD_CODED_MODULE_PATH = "cellpy.readers.instruments.configurations"
OPTIONAL_DICTIONARY_ATTRIBUTE_NAMES = [
    "file_info",
    "formatters",
    "prefixes",
    "pre_processors",
    "post_processors",
    "meta_keys",
    "incremental_unit_labels",
    "not_implemented_in_cellpy_yet_renaming_dict",
    "raw_units",
    "raw_limits",
    "states",
    "unit_labels",
]
OPTIONAL_LIST_ATTRIBUTE_NAMES = [
    "columns_to_keep",
]


RAW_LIMITS = {
    "current_hard": 0.000_000_000_000_1,
    "current_soft": 0.000_01,
    "stable_current_hard": 2.0,
    "stable_current_soft": 4.0,
    "stable_voltage_hard": 2.0,
    "stable_voltage_soft": 4.0,
    "stable_charge_hard": 0.001,
    "stable_charge_soft": 5.0,
    "ir_change": 0.00001,
}


@dataclass
class ModelParameters:
    """Dataclass to store sub-model specific parameters."""

    name: str
    # The unit labels are only used when generating new headers
    # (normal_headers_renaming_dict)
    # with units (post_processor: get_column_names):
    file_info: dict = field(default_factory=dict)
    unit_labels: dict = field(default_factory=dict)
    incremental_unit_labels: dict = field(default_factory=dict)

    normal_headers_renaming_dict: dict = field(default_factory=dict)
    not_implemented_in_cellpy_yet_renaming_dict: dict = field(default_factory=dict)
    columns_to_keep: list = field(default_factory=list)
    states: dict = field(default_factory=dict)
    raw_units: dict = field(default_factory=dict)
    raw_limits: dict = field(default_factory=dict)
    formatters: dict = field(default_factory=dict)
    meta_keys: dict = field(default_factory=dict)
    pre_processors: dict = field(default_factory=dict)
    post_processors: dict = field(default_factory=dict)
    # used for defining e.g. M, k, etc. - probably not needed:
    prefixes: dict = field(default_factory=dict)


def register_local_configuration_from_yaml_file(instrument) -> ModelParameters:
    """register a module (.yml file) and return it.

    This function will dynamically import the given module from the
    cellpy.readers.instruments.configurations module and return it.

    Returns: ModelParameters

    """

    yml = yaml.YAML()
    with open(instrument, "r") as ff:
        settings = yml.load(ff.read())

    name = Path(instrument).name

    optional_dictionary_attributes = {
        key: settings.get(key, dict()) for key in OPTIONAL_DICTIONARY_ATTRIBUTE_NAMES
    }

    optional_list_attributes = {
        key: settings.get(key, list()) for key in OPTIONAL_LIST_ATTRIBUTE_NAMES
    }

    # special hacks
    # -- raw limits (this should be moved to internal settings, prms or something like that
    raw_limits = optional_dictionary_attributes["raw_limits"]
    if not raw_limits:
        raw_limits = RAW_LIMITS

    model_01 = ModelParameters(
        name=name,
        file_info=optional_dictionary_attributes["file_info"],
        normal_headers_renaming_dict=settings["normal_headers_renaming_dict"],
        unit_labels=optional_dictionary_attributes["unit_labels"],
        prefixes=optional_dictionary_attributes["prefixes"],
        incremental_unit_labels=optional_dictionary_attributes[
            "incremental_unit_labels"
        ],
        not_implemented_in_cellpy_yet_renaming_dict=optional_dictionary_attributes[
            "not_implemented_in_cellpy_yet_renaming_dict"
        ],
        columns_to_keep=optional_list_attributes["columns_to_keep"],
        states=optional_dictionary_attributes["states"],
        raw_units=optional_dictionary_attributes["raw_units"],
        raw_limits=raw_limits,
        meta_keys=optional_dictionary_attributes["meta_keys"],
        formatters=optional_dictionary_attributes["formatters"],
        pre_processors=optional_dictionary_attributes["pre_processors"],
        post_processors=optional_dictionary_attributes["post_processors"],
    )
    return model_01


def register_configuration_from_module(
    name: str = "one",
    module: str = "maccor_txt_one",
    _module_path=None,
    _m=None,
) -> ModelParameters:
    """register a python module (.py file) and return it.

    This function will dynamically import the given module from the
    cellpy.readers.instruments.configurations module and return it.

    Returns: ModelParameters
    """

    if _m is None:
        if _module_path is None:
            _m = import_module(f"{HARD_CODED_MODULE_PATH}.{module}")
        else:
            _m = import_module(f"{_module_path}.{module}")

    optional_dictionary_attributes = {
        key: getattr(_m, key, dict()) for key in OPTIONAL_DICTIONARY_ATTRIBUTE_NAMES
    }

    optional_list_attributes = {
        key: getattr(_m, key, list()) for key in OPTIONAL_LIST_ATTRIBUTE_NAMES
    }

    # special hacks
    # -- raw limits (this should be moved to internal settings, prms or something like that
    raw_limits = optional_dictionary_attributes["raw_limits"]
    if not raw_limits:
        raw_limits = RAW_LIMITS

    return ModelParameters(
        name=name,
        file_info=optional_dictionary_attributes["file_info"],
        normal_headers_renaming_dict=_m.normal_headers_renaming_dict,
        unit_labels=optional_dictionary_attributes["unit_labels"],
        prefixes=optional_dictionary_attributes["prefixes"],
        incremental_unit_labels=optional_dictionary_attributes[
            "incremental_unit_labels"
        ],
        not_implemented_in_cellpy_yet_renaming_dict=optional_dictionary_attributes[
            "not_implemented_in_cellpy_yet_renaming_dict"
        ],
        columns_to_keep=optional_list_attributes["columns_to_keep"],
        states=optional_dictionary_attributes["states"],
        raw_units=optional_dictionary_attributes["raw_units"],
        raw_limits=raw_limits,
        meta_keys=optional_dictionary_attributes["meta_keys"],
        formatters=optional_dictionary_attributes["formatters"],
        pre_processors=optional_dictionary_attributes["pre_processors"],
        post_processors=optional_dictionary_attributes["post_processors"],
    )
