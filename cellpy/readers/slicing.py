"""Split / drop-cycle helpers for CellpyCell (issue #519, V2-09 follow-up).

Moved verbatim from ``cellreader.py`` (the twice-flagged ``# TODO: consider
moving splitting etc outside of CellpyCell``), following the #509
``capacity_curves`` pattern: functions take the ``CellpyCell`` instance as
their first argument; ``CellpyCell`` keeps thin delegate methods with
identical signatures, so the public API is unchanged. Cross-calls go through
the instance (``cell.split_many(...)``, ``cell.vacant(...)`` ...) to preserve
subclass dispatch exactly as before the move.
"""

import logging
from typing import TYPE_CHECKING, List, Optional, Union

from cellpy.readers import data_structures as ds
from cellpy.readers import externals

if TYPE_CHECKING:
    from cellpy.readers.cellreader import CellpyCell


def mod_raw_split_cycle(cell: "CellpyCell", data_points: List) -> None:
    """Split cycle(s) into several cycles.

    Args:
        cell: the CellpyCell instance.
        data_points: list of the first data point(s) for additional cycle(s).

    """
    logging.info(f"splitting cycles at {data_points}")
    for data_point in data_points:
        cell._mod_raw_split_cycle(data_point)
    logging.warning(
        f"splitting cycles at {data_points} -re-run make_step_table and make_summary to propagate change!"
    )


def _mod_raw_split_cycle(cell: "CellpyCell", data_point: int) -> None:
    r = cell.data.raw

    hdr_data_point = cell.schema.raw.datapoint_num
    hdr_cycle = cell.schema.raw.cycle_num
    hdr_c_cap = cell.schema.raw.cumulative_charge_capacity
    hdr_d_cap = cell.schema.raw.cumulative_discharge_capacity
    hdr_c_energy = cell.headers_normal.charge_energy_txt
    hdr_d_energy = cell.headers_normal.discharge_energy_txt

    # modifying cycle numbers
    c_mask = r[hdr_data_point] >= data_point
    r.loc[c_mask, hdr_cycle] = r.loc[c_mask, hdr_cycle] + 1

    # resetting capacities
    initial_values = r.loc[r[hdr_data_point] == data_point - 1, :]
    cycle = r.loc[r[hdr_data_point] == data_point, hdr_cycle].values[0]

    c_cap, d_cap, c_energy, d_energy = initial_values[
        [hdr_c_cap, hdr_d_cap, hdr_c_energy, hdr_d_energy]
    ].values[0]
    cycle_mask = r[hdr_cycle] == cycle
    r.loc[cycle_mask, hdr_c_cap] = r.loc[cycle_mask, hdr_c_cap] - c_cap
    r.loc[cycle_mask, hdr_d_cap] = r.loc[cycle_mask, hdr_d_cap] - d_cap
    r.loc[cycle_mask, hdr_c_energy] = r.loc[cycle_mask, hdr_c_energy] - c_energy
    r.loc[cycle_mask, hdr_d_energy] = r.loc[cycle_mask, hdr_d_energy] - d_energy


def split(cell: "CellpyCell", cycle=None):
    """Split experiment (CellpyCell object) into two sub-experiments. if cycle
    is not give, it will split on the median cycle number"""
    if isinstance(cycle, int) or cycle is None:
        return cell.split_many(base_cycles=cycle)


def drop_from(cell: "CellpyCell", cycle=None):
    """Select first part of experiment (CellpyCell object) up to cycle number
    'cycle'"""
    if isinstance(cycle, int):
        c1, c2 = cell.split_many(base_cycles=cycle)
        return c1


def drop_to(cell: "CellpyCell", cycle=None):
    """Select last part of experiment (CellpyCell object) from cycle number
    'cycle'"""
    if isinstance(cycle, int):
        c1, c2 = cell.split_many(base_cycles=cycle)
        return c2


def from_cycle(cell: "CellpyCell", cycle: int) -> "CellpyCell":
    """Select experiment (CellpyCell object) from cycle number 'cycle'"""
    if isinstance(cycle, int):
        return cell.split_many(base_cycles=cycle)[1]
    else:
        raise ValueError("cycle must be an integer")


def to_cycle(cell: "CellpyCell", cycle: int) -> "CellpyCell":
    """Select experiment (CellpyCell object) to cycle number 'cycle'"""
    if isinstance(cycle, int):
        return cell.split_many(base_cycles=cycle + 1)[0]
    else:
        raise ValueError("cycle must be an integer")


def drop_edges(cell: "CellpyCell", start: int, end: int) -> "CellpyCell":
    """Select middle part of experiment (CellpyCell object) from cycle
    number 'start' to 'end'"""
    if end < start:
        raise ValueError("end cannot be larger than start")
    if end == start:
        raise ValueError("end cannot be the same as start")
    return cell.split_many([start, end])[1]


def split_many(
    cell: "CellpyCell", base_cycles: Optional[Union[int, List[int]]] = None
) -> List["CellpyCell"]:
    """Split experiment (CellpyCell object) into several sub-experiments.

    Args:
        cell: the CellpyCell instance.
        base_cycles (int or list of ints): cycle(s) to do the split on.

    Returns:
        List of CellpyCell objects

    """
    h_summary_index = cell.schema.summary.cycle_num
    h_raw_index = cell.schema.raw.cycle_num
    h_step_cycle = cell.schema.steps.cycle_num

    if base_cycles is None:
        all_cycles = cell.get_cycle_numbers()
        base_cycles = int(externals.numpy.median(all_cycles))

    cells = list()
    if not isinstance(base_cycles, (list, tuple)):
        base_cycles = [base_cycles]

    dataset = cell.data
    steptable = dataset.steps
    data = dataset.raw
    summary = dataset.summary

    # In case Cycle_Index has been promoted to index [#index]
    if h_summary_index not in summary.columns:
        summary = summary.reset_index(drop=False)

    for b_cycle in base_cycles:
        steptable0, steptable = [
            steptable[steptable[h_step_cycle] < b_cycle],
            steptable[steptable[h_step_cycle] >= b_cycle],
        ]
        data0, data = [
            data[data[h_raw_index] < b_cycle],
            data[data[h_raw_index] >= b_cycle],
        ]
        summary0, summary = [
            summary[summary[h_summary_index] < b_cycle],
            summary[summary[h_summary_index] >= b_cycle],
        ]

        # instance-bound classmethod call == CellpyCell.vacant(cell=...) for
        # CellpyCell instances, and dispatches to the subclass otherwise
        new_cell = cell.vacant(cell=cell)
        old_cell = cell.vacant(cell=cell)

        # Polars Phase A (#457): keys live in columns — no re-promotion
        # of cycle_index to the summary index.

        new_cell.data.steps = steptable0
        new_cell.data.raw = data0
        new_cell.data.summary = summary0
        new_cell.data = ds.identify_last_data_point(new_cell.data)

        old_cell.data.steps = steptable
        old_cell.data.raw = data
        old_cell.data.summary = summary
        old_cell.data = ds.identify_last_data_point(old_cell.data)

        cells.append(new_cell)

    cells.append(old_cell)
    return cells


def with_cycles(cell: "CellpyCell", cycles: Union[int, List[int]]) -> "CellpyCell":
    """Select a subset of cycles from the experiment (CellpyCell object).

    This method should only be used for quick selection of cycles (e.g. for plotting).

    Args:
        cell: the CellpyCell instance.
        cycles (int or iterable of ints): cycle number(s) to keep.

    Returns:
        A new CellpyCell object containing only the selected cycles.

    """
    h_summary_index = cell.schema.summary.cycle_num
    h_raw_index = cell.schema.raw.cycle_num
    h_step_cycle = cell.schema.steps.cycle_num

    if isinstance(cycles, int):
        cycles = [cycles]
    cycles = list(cycles)

    dataset = cell.data
    steptable = dataset.steps
    data = dataset.raw
    summary = dataset.summary

    # In case Cycle_Index has been promoted to index [#index]
    if h_summary_index not in summary.columns:
        summary = summary.reset_index(drop=False)

    new_steptable = steptable[steptable[h_step_cycle].isin(cycles)]
    new_data = data[data[h_raw_index].isin(cycles)]
    new_summary = summary[summary[h_summary_index].isin(cycles)]

    # Polars Phase A (#457): keys live in columns — no re-promotion.

    new_cell = cell.vacant(cell=cell)
    new_cell.data.steps = new_steptable
    new_cell.data.raw = new_data
    new_cell.data.summary = new_summary
    new_cell.data = ds.identify_last_data_point(new_cell.data)

    return new_cell
