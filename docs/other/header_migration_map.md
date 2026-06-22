# Header migration map: cellpy → cellpy-core

Mapping of DataFrame column string values from the old cellpy header classes
(`HeadersNormal`, `HeadersSummary`, `HeadersStepTable`) to the new native
cellpy-core classes (`RawCols`, `CycleCols`, `StepCols` in `cellpycore.config`).

The legacy bridge (`cellpycore.legacy`) keeps the old names alive during the
transition; this document tracks what changes when the legacy layer is dropped.

---

## Raw data (`HeadersNormal` → `RawCols`)

| Old column | New column | Notes |
|---|---|---|
| `data_point` | `datapoint_num` | |
| `date_time` | `epoch_time_utc` | semantics change: unix epoch, not datetime obj |
| `cycle_index` | `cycle_num` | |
| `step_index` | `step_num` | |
| `sub_step_index` | *(not in RawCols yet)* | |
| `test_time` | `test_time` | unchanged |
| `step_time` | `step_time` | unchanged |
| `current` | `current` | unchanged |
| `voltage` | `potential` | **biggest rename** |
| `charge_capacity` | `cumulative_charge_capacity` | convention clarified |
| `discharge_capacity` | `cumulative_discharge_capacity` | convention clarified |
| `charge_energy` | `cumulative_charge_energy` | |
| `discharge_energy` | `cumulative_discharge_energy` | |
| `internal_resistance` | `internal_resistance` | unchanged |
| `test_id` | `test_id` | unchanged |
| `power` | `step_charge_power` / `step_discharge_power` | split by direction |
| `reference_voltage` | *(dropped)* | |
| `aci_phase_angle` | *(dropped)* | |
| `ref_aci_phase_angle` | *(dropped)* | |
| `ac_impedance` | *(dropped)* | |
| `ref_ac_impedance` | *(dropped)* | |
| `is_fc_data` | *(dropped)* | |
| `sub_step_time` | *(dropped)* | |
| `dv_dt` | *(dropped)* | |
| `frequency` | *(dropped)* | |
| `amplitude` | *(dropped)* | |
| `channel_id` | *(dropped)* | |
| `data_flag` | `mask` | closest equivalent |
| `test_name` | `source_uuid` | closest equivalent |
| *(new)* | `source_datapoint_num` | |
| *(new)* | `source_type` | |
| *(new)* | `source_step_num` | |
| *(new)* | `step_type` | was computed into step table only |
| *(new)* | `step_type_detail` | |
| *(new)* | `step_mode` | |
| *(new)* | `cycle_type` | |
| *(new)* | `aux_temperature_cell` | |
| *(new)* | `aux_temperature_chamber` | |
| *(new)* | `aux_pressure_cell` | |

---

## Summary (`HeadersSummary` → `CycleCols`)

| Old column | New column | Notes |
|---|---|---|
| `cycle_index` | `cycle_num` | |
| `data_point` | `datapoint_num_first` / `datapoint_num_last` | split |
| `test_time` | `first_test_time` / `last_test_time` | split |
| `date_time` | `first_epoch_time_utc` / `last_epoch_time_utc` | split |
| `discharge_capacity` | `discharge_capacity` | unchanged |
| `charge_capacity` | `charge_capacity` | unchanged |
| `discharge_capacity_loss` | `discharge_capacity_loss` | unchanged |
| `charge_capacity_loss` | `charge_capacity_loss` | unchanged |
| `coulombic_efficiency` | `coulombic_efficiency` | unchanged |
| `coulombic_difference` | `coulombic_difference` | unchanged |
| `cumulated_charge_capacity` | `test_cumulated_charge_capacity` | |
| `cumulated_discharge_capacity` | `test_cumulated_discharge_capacity` | |
| `cumulated_coulombic_difference` | `test_cumulated_coulombic_difference` | |
| `cumulated_charge_capacity_loss` | `test_cumulated_charge_capacity_loss` | |
| `cumulated_discharge_capacity_loss` | `test_cumulated_discharge_capacity_loss` | |
| `end_voltage_charge` | `potential_end_charge` | |
| `end_voltage_discharge` | `potential_end_discharge` | |
| `ir_charge` | `ir_start_charge` / `ir_end_charge` | split |
| `ir_discharge` | `ir_start_discharge` / `ir_end_discharge` | split |
| `ocv_first_max` | `relaxation_potential_charge` | approximate |
| `ocv_first_min` | `relaxation_potential_discharge` | approximate |
| `ocv_second_max` | *(no direct equivalent)* | |
| `ocv_second_min` | *(no direct equivalent)* | |
| `discharge_capacity_raw` | *(dropped / redundant)* | |
| `charge_capacity_raw` | *(dropped / redundant)* | |
| `cumulated_coulombic_efficiency` | *(dropped)* | |
| `normalized_charge_capacity` | *(dropped)* | |
| `normalized_discharge_capacity` | *(dropped)* | |
| `shifted_charge_capacity` | *(dropped)* | |
| `shifted_discharge_capacity` | *(dropped)* | |
| `cumulated_ric_disconnect` | *(dropped)* | |
| `cumulated_ric_sei` | *(dropped)* | |
| `cumulated_ric` | *(dropped)* | |
| `normalized_cycle_index` | *(dropped)* | |
| `low_level` | *(dropped)* | |
| `high_level` | *(dropped)* | |
| `temperature_last` | *(dropped)* | aux cols replace these |
| `temperature_mean` | *(dropped)* | aux cols replace these |
| `charge_c_rate` | *(dropped)* | |
| `discharge_c_rate` | *(dropped)* | |
| `test_name` | *(dropped)* | |
| `channel_id` | *(dropped)* | |
| `data_flag` | `mask` | |

New columns in `CycleCols` with no old equivalent: `mask`, `cycle_duration`,
`charge_duration`, `discharge_duration`, `rest_duration`, `test_net_capacity`,
`charge_energy`, `discharge_energy`, `cycle_net_energy`, `energy_efficiency`,
`voltage_efficiency`, `test_cumulated_charge_energy`,
`test_cumulated_discharge_energy`, `test_net_energy`,
`current_charge_mean/min/max/mean_tw/mean_cw`, `current_discharge_*`,
`potential_charge_mean/min/max/start/mean_tw/mean_cw`, `potential_discharge_*`,
`power_charge_*`, `power_discharge_*`,
`open_circuit_potential_charge/discharge`, `cv_share`,
`cv/cc_charge_capacity/energy/time`.

---

## Step table (`HeadersStepTable` → `StepCols`)

| Old column | New column | Notes |
|---|---|---|
| `cycle` | `cycle_num` | |
| `step` | `step_num` | |
| `sub_step` | `sub_step_num` | |
| `type` | `step_type` | |
| `sub_type` | `sub_step_type` | |
| `test_time` | `test_time_first` / `test_time_last` | split |
| `step_time` | `step_time_first` / `step_time_last` / `step_time_mean` … | expanded |
| `point` | `datapoint_num_first` / `datapoint_num_last` | split |
| `voltage` | `potential_mean` / `potential_first` / `potential_last` … | expanded |
| `current` | `current_mean` / `current_first` / `current_last` … | expanded |
| `charge` | `charge_capacity_mean` / `charge_capacity_last` … | expanded |
| `discharge` | `discharge_capacity_mean` / `discharge_capacity_last` … | expanded |
| `ir` | `internal_resistance_mean` / `internal_resistance_last` … | expanded |
| `rate_avr` | `c_rate` | |
| `test` | *(dropped)* | |
| `ustep` | *(dropped)* | |
| `info` | *(dropped)* | |
| `ir_pct_change` | *(dropped)* | |

Each expanded quantity gets `_mean`, `_std`, `_min`, `_max`, `_first`, `_last`,
`_delta` variants.
