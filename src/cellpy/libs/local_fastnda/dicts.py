"""Mappings used in data processing."""

from collections.abc import Mapping
from types import MappingProxyType

import polars as pl

# Neware step type integer to string codes
STEP_TYPE_MAP = MappingProxyType(
    {
        1: "CC_Chg",
        2: "CC_DChg",
        3: "CV_Chg",
        4: "Rest",
        5: "Cycle",
        7: "CCCV_Chg",
        8: "CP_DChg",
        9: "CP_Chg",
        10: "CR_DChg",
        13: "Pause",
        16: "Pulse",
        17: "SIM",
        18: "PCCCV_Chg",
        19: "CV_DChg",
        20: "CCCV_DChg",
        21: "Control",
        22: "OCV",
        25: "Ramp",
        26: "CPCV_DChg",
        27: "CPCV_Chg",
    }
)

# For _generate_cycle_number, 1 = charge, 0 = discharge
CHARGE_DISCHARGE_MAP = MappingProxyType(
    {
        1: 1,
        2: 0,
        3: 1,
        7: 1,
        8: 0,
        9: 1,
        10: 0,
        18: 1,
        19: 0,
        20: 0,
        26: 0,
        27: 1,
    }
)

# Final column datatypes (excluding aux columns)
DTYPE_MAP: Mapping[str, type[pl.DataType]] = MappingProxyType(
    {
        "index": pl.UInt32,
        "voltage_V": pl.Float32,
        "current_mA": pl.Float32,
        "unix_time_s": pl.Float64,
        "step_time_s": pl.Float64,
        "total_time_s": pl.Float64,
        "cycle_count": pl.UInt32,
        "step_count": pl.UInt32,
        "step_index": pl.UInt32,
        "step_type": pl.Categorical,
        "capacity_mAh": pl.Float32,
        "energy_mWh": pl.Float32,
    }
)

# Current value multiplier based on instrument Range setting
MULTIPLIER_MAP = MappingProxyType(
    {
        -100000000: 1e1,
        -200000: 1e-2,
        -100000: 1e-2,
        -60000: 1e-2,
        -30000: 1e-2,
        -50000: 1e-2,
        -40000: 1e-2,
        -20000: 1e-2,
        -12000: 1e-2,
        -10000: 1e-2,
        -6000: 1e-2,
        -5000: 1e-2,
        -3000: 1e-2,
        -2000: 1e-2,
        -1000: 1e-2,
        -500: 1e-3,
        -100: 1e-3,
        -50: 1e-4,
        -25: 1e-4,
        -20: 1e-4,
        -10: 1e-4,
        -5: 1e-5,
        -2: 1e-5,
        -1: 1e-5,
        0: 0.0,
        1: 1e-4,
        2: 1e-4,
        5: 1e-4,
        10: 1e-3,
        20: 1e-3,
        25: 1e-3,
        50: 1e-3,
        100: 1e-2,
        200: 1e-2,
        250: 1e-2,
        500: 1e-2,
        1000: 1e-1,
        6000: 1e-1,
        10000: 1e-1,
        12000: 1e-1,
        20000: 1e-1,
        30000: 1e-1,
        40000: 1e-1,
        50000: 1e-1,
        60000: 1e-1,
        100000: 1e-1,
        200000: 1e-1,
    }
)

# Auxiliary column names based on ChlType
AUX_CHL_MAP = MappingProxyType(
    {
        102: "temperature_CPU_degC",
        # 103: "temperature_degC",
        103: "single_cell_voltage_V",
        335: "temperature_setpoint_degC",
        345: "humidity_%",
        1122: "temperature_cell_degC",
    }
)

# User-facing mutable dicts
step_type_map = dict(STEP_TYPE_MAP)

# Kept for backwards compatibility
multiplier_dict = dict(MULTIPLIER_MAP)
aux_chl_type_columns = dict(AUX_CHL_MAP)
dtype_dict = dict(DTYPE_MAP)
state_dict = dict(STEP_TYPE_MAP)
