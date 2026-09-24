# The cell object

`CellpyCell` is what `cellpy.get` returns: one cell, its frames, and the
methods that work on them. Its members are grouped by task below; the
right-hand table of contents lists every one.

::: cellpy.readers.cellreader.CellpyCell
    options:
      members: false
      show_source: false

## Loading and saving

Create a cell and read or write files. Most scripts use `cellpy.get` instead of calling these directly.

::: cellpy.readers.cellreader.CellpyCell.from_raw
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.load
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.save
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.merge
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.vacant
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.initialize
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.loadcell
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_instrument
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.register_instrument_readers
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_raw_datadir
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_cellpy_datadir
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.check_file_ids
    options:
      heading_level: 3

## The data and what it describes

The frames live on `c.data`; `c.schema` gives their column names.

::: cellpy.readers.cellreader.CellpyCell.data
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.schema
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.empty
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.cell_name
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.raw_units
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.cycle_mode
    options:
      heading_level: 3

## Mass, area and nominal capacity

What the capacities are normalised by. After changing one, call `refresh_after`. See [Units, mass, area and C-rates](../guides/units.md).

::: cellpy.readers.cellreader.CellpyCell.mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.active_mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.tot_mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.active_electrode_area
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.nominal_capacity
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.nom_cap
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.nom_cap_specifics
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.nominal_capacity_as_absolute
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.inspect_nominal_capacity
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_tot_mass
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_nom_cap
    options:
      heading_level: 3

## Step table and summary

Build, rebuild and read the derived tables. See [Understand the step table](../guides/step_table.md) and [Summary columns](../reference/summary_columns.md).

::: cellpy.readers.cellreader.CellpyCell.make_step_table
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.load_step_specifications
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.print_steps
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_step_numbers
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.make_summary
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.refresh_after
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_summary
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.add_to_summary
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.filtered_summary
    options:
      heading_level: 3

## Cycles and curves

Pull numbers and curves out for chosen cycles.

::: cellpy.readers.cellreader.CellpyCell.get_cycle_numbers
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_number_of_cycles
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_rates
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_cap
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_ccap
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_dcap
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_ocv
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_ir
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.total_time_at_voltage_level
    options:
      heading_level: 3

## Raw values

Columns from the raw frame, for a whole test or one cycle/step (the `sget_` variants).

::: cellpy.readers.cellreader.CellpyCell.get_raw
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_voltage
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_current
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_datetime
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_timestamp
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.sget_voltage
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.sget_current
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.sget_steptime
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.sget_timestamp
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.sget_step_numbers
    options:
      heading_level: 3

## Selecting and splitting cycles

Return a new cell with only part of the test.

::: cellpy.readers.cellreader.CellpyCell.with_cycles
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.from_cycle
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.to_cycle
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.drop_from
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.drop_to
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.drop_edges
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.split
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.split_many
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.mod_raw_split_cycle
    options:
      heading_level: 3

## Exporting

See [Get your data out](../guides/exporting.md).

::: cellpy.readers.cellreader.CellpyCell.to_excel
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.to_csv
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.to_bdf
    options:
      heading_level: 3

## Units

Convert between the tester's units and cellpy's.

::: cellpy.readers.cellreader.CellpyCell.with_cellpy_unit
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.to_cellpy_unit
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.unit_scaler_from_raw
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.get_converter_to_specific
    options:
      heading_level: 3

## Checks and helpers

::: cellpy.readers.cellreader.CellpyCell.has_data_point_as_index
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.has_data_point_as_column
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.has_no_full_duplicates
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.has_no_partial_duplicates
    options:
      heading_level: 3

::: cellpy.readers.cellreader.CellpyCell.set_col_first
    options:
      heading_level: 3
