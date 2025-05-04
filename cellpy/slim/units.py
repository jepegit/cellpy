import logging
from typing import TypeVar
from cellpy.parameters.internal_settings import CellpyUnits
from cellpy.readers import core
from cellpy.parameters.internal_settings import (
    get_cellpy_units,
    get_default_output_units,
    HeadersNormal,
    HeadersStepTable,
    HeadersSummary,
    CellpyUnits,
)

DataFrame = TypeVar("DataFrame")

def get_converter_to_specific(
    data: core.Data,
    value: float = None,
    from_units: CellpyUnits = None,
    to_units: CellpyUnits = None,
    mode: str = "gravimetric",
) -> float:
    """Convert from absolute units to specific (areal or gravimetric).

    The method provides a conversion factor that you can multiply your
    values with to get them into specific values.

    Args:
        data: data instance
        value: value used to scale on.
        from_units: defaults to data.raw_units.
        to_units: defaults to cellpy_units.
        mode (str): gravimetric, areal or absolute

    Returns:
        conversion factor (float)

    """
    # TODO @jepe: implement handling of edge-cases
    # TODO @jepe: fix all the instrument readers (replace floats in raw_units with strings)

    new_units = to_units or get_cellpy_units()
    old_units = from_units or data.raw_units

    if mode == "gravimetric":
        value = value or data.mass
        value = core.Q(value, new_units["mass"])
        to_unit_specific = core.Q(1.0, new_units["specific_gravimetric"])

    elif mode == "areal":
        value = value or data.active_electrode_area
        value = core.Q(value, new_units["area"])
        to_unit_specific = core.Q(1.0, new_units["specific_areal"])

    elif mode == "volumetric":
        value = value or data.volume
        value = core.Q(value, new_units["volume"])
        to_unit_specific = core.Q(1.0, new_units["specific_volumetric"])

    elif mode == "absolute":
        value = core.Q(1.0, None)
        to_unit_specific = core.Q(1.0, None)

    else:
        logging.debug(f"mode={mode} not supported!")
        return 1.0

    from_unit_cap = core.Q(1.0, old_units["charge"])
    to_unit_cap = core.Q(1.0, new_units["charge"])

    # from unit is always in absolute values:
    from_unit = from_unit_cap

    to_unit = to_unit_cap / to_unit_specific

    conversion_factor = (from_unit / to_unit / value).to_reduced_units()
    logging.debug(f"conversion factor: {conversion_factor}")
    return conversion_factor.m