""" Very simple implementation of a plugin-like infrastructure"""
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

from ruamel import yaml


# TODO: make tests.
# TODO: move this into its own module (not __init__).
# TODO: refactor ``custom`` reader so that it uses this.
# TODO: document for devs.
# TODO: Bonus - make a python package/pre-commit hook that turns TODO-statements into issues.

HARD_CODED_MODULE_PATH = "cellpy.readers.instruments.configurations"
OPTIONAL_DICTIONARY_ATTRIBUTE_NAMES = [
    "formatters",
    "prefixes",
    "pre_processors",
    "post_processors",
    "meta_keys",
    "incremental_unit_labels",
    "not_implemented_in_cellpy_yet_renaming_dict",
]


@dataclass
class ModelParameters:
    """Dataclass to store sub-model specific parameters."""

    name: str
    unit_labels: dict = field(default_factory=dict)
    incremental_unit_labels: dict = field(default_factory=dict)
    normal_headers_renaming_dict: dict = field(default_factory=dict)
    not_implemented_in_cellpy_yet_renaming_dict: dict = field(default_factory=dict)
    columns_to_keep: dict = field(default_factory=dict)
    states: dict = field(default_factory=dict)
    raw_units: dict = field(default_factory=dict)
    raw_limits: dict = field(default_factory=dict)
    formatters: dict = field(default_factory=dict)
    meta_keys: dict = field(default_factory=dict)
    pre_processors: dict = field(default_factory=dict)
    post_processors: dict = field(default_factory=dict)
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

    model_01 = ModelParameters(
        name=name,
        unit_labels=settings["unit_labels"],
        prefixes=optional_dictionary_attributes["prefixes"],
        incremental_unit_labels=optional_dictionary_attributes[
            "incremental_unit_labels"
        ],
        normal_headers_renaming_dict=settings["normal_headers_renaming_dict"],
        not_implemented_in_cellpy_yet_renaming_dict=optional_dictionary_attributes[
            "not_implemented_in_cellpy_yet_renaming_dict"
        ],
        columns_to_keep=settings["columns_to_keep"],
        states=settings["states"],
        raw_units=settings["raw_units"],
        raw_limits=settings["raw_limits"],
        meta_keys=optional_dictionary_attributes["meta_keys"],
        formatters=optional_dictionary_attributes["formatters"],
        pre_processors=optional_dictionary_attributes["pre_processors"],
        post_processors=optional_dictionary_attributes["post_processors"],
    )
    return model_01


def register_configuration_from_module(
    name: str = "one", module: str = "maccor_txt_one"
) -> ModelParameters:
    """register a python module (.py file) and return it.

    This function will dynamically import the given module from the
    cellpy.readers.instruments.configurations module and return it.

    Returns: ModelParameters
    """

    m = import_module(f"{HARD_CODED_MODULE_PATH}.{module}")

    optional_dictionary_attributes = {
        key: getattr(m, key, dict()) for key in OPTIONAL_DICTIONARY_ATTRIBUTE_NAMES
    }


    model_01 = ModelParameters(
        name=name,
        unit_labels=m.unit_labels,
        prefixes=optional_dictionary_attributes["prefixes"],
        incremental_unit_labels=optional_dictionary_attributes[
            "incremental_unit_labels"
        ],
        normal_headers_renaming_dict=m.normal_headers_renaming_dict,
        not_implemented_in_cellpy_yet_renaming_dict=optional_dictionary_attributes[
            "not_implemented_in_cellpy_yet_renaming_dict"
        ],
        columns_to_keep=m.columns_to_keep,
        states=m.states,
        raw_units=m.raw_units,
        raw_limits=m.raw_limits,
        meta_keys=optional_dictionary_attributes["meta_keys"],
        formatters=optional_dictionary_attributes["formatters"],
        pre_processors=optional_dictionary_attributes["pre_processors"],
        post_processors=optional_dictionary_attributes["post_processors"],
    )
    return model_01
