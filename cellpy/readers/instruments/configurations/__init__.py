""" Very simple implementation of a plugin-like infrastructure"""
from dataclasses import dataclass, field
from importlib import import_module

HARD_CODED_MODULE_PATH = "cellpy.readers.instruments.configurations"


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


def register_configuration(
    name: str = "one", module: str = "maccor_txt_one"
) -> ModelParameters:
    """register a python module (.py file) and return it.

    This function will dynamically import the given module from the
    cellpy.readers.instruments.configurations module and return it.

    Returns: ModelParameters
    """
    m = import_module(f"{HARD_CODED_MODULE_PATH}.{module}")
    model_01 = ModelParameters(
        name=name,
        unit_labels=m.unit_labels,
        incremental_unit_labels=m.incremental_unit_labels,
        normal_headers_renaming_dict=m.normal_headers_renaming_dict,
        not_implemented_in_cellpy_yet_renaming_dict=m.not_implemented_in_cellpy_yet_renaming_dict,
        columns_to_keep=m.columns_to_keep,
        states=m.states,
    )
    return model_01
