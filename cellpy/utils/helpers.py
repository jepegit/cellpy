import numpy as np
import pandas as pd
import os
import pathlib

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import (
    get_headers_summary,
    get_headers_step_table,
    get_headers_normal,
    ATTRS_CELLPYDATA,
    ATTRS_DATASET,
)

from cellpy import prmreader
from cellpy.utils import batch, ica


hdr_summary = get_headers_summary()
hdr_steps = get_headers_step_table()
hdr_normal = get_headers_normal()


def update_journal_cellpy_data_dir(
    pages, new_path=None, from_path="PureWindowsPath", to_path="Path"
):
    """Update the path in the pages (batch) from one type of OS to another.

    I use this function when I switch from my work PC (windows) to my home
    computer (mac).

    Args:
        pages: the (batch.experiment.)journal.pages object (pandas.DataFrame)
        new_path: the base path (uses prms.Paths.cellpydatadir if not given)
        from_path: type of path to convert from.
        to_path: type of path to convert to.

    Returns:
        journal.pages (pandas.DataFrame)

    """
    # TODO: move this to batch?

    if new_path is None:
        new_path = prms.Paths.cellpydatadir

    from_path = getattr(pathlib, from_path)
    to_path = getattr(pathlib, to_path)

    pages.cellpy_file_names = pages.cellpy_file_names.apply(from_path)
    pages.cellpy_file_names = pages.cellpy_file_names.apply(
        lambda x: to_path(new_path) / x.name
    )
    return pages


def make_new_cell():
    """create an empty CellpyData object."""

    new_cell = cellpy.cellreader.CellpyData(initialize=True)
    return new_cell


def split_experiment(cell, base_cycles=None):
    """Split experiment (CellpyData object) into several sub-experiments.

    Args:
        cell (CellpyData): original cell
        base_cycles (int or list of ints): cycle(s) to do the split on.

    Returns:
        List of CellpyData objects
    """

    # TODO: implement similar functionality as method for CellpyData
    #       examples:
    #           cell.split(cycle=28)
    #           cell.drop_from(cycle=28)
    #           cell.drop_to(cycle=28)
    #           cell.pop(from=22, to=28)
    #           cell.copy()
    #           cell.copy(from=22, to=28)

    if base_cycles is None:
        all_cycles = cell.get_cycle_numbers()
        base_cycles = int(np.median(all_cycles))

    cells = list()
    if not isinstance(base_cycles, (list, tuple)):
        base_cycles = [base_cycles]

    dataset = cell.cell
    steptable = dataset.steps
    data = dataset.raw
    summary = dataset.summary

    for b_cycle in base_cycles:
        steptable0, steptable = [
            steptable[steptable.cycle < b_cycle],
            steptable[steptable.cycle >= b_cycle],
        ]
        data0, data = [
            data[data.Cycle_Index < b_cycle],
            data[data.Cycle_Index >= b_cycle],
        ]
        summary0, summary = [
            summary[summary.index < b_cycle],
            summary[summary.index >= b_cycle],
        ]

        new_cell = make_new_cell()

        new_cell.cell.steps = steptable0
        # new_cell.dataset.step_table_made = True

        new_cell.cell.raw = data0
        new_cell.cell.summary = summary0

        old_cell = make_new_cell()
        old_cell.cell.steps = steptable
        # old_cell.dataset.step_table_made = True

        old_cell.cell.raw = data
        old_cell.cell.summary = summary

        for attr in ATTRS_DATASET:
            value = getattr(cell.cell, attr)
            setattr(new_cell.cell, attr, value)
            setattr(old_cell.cell, attr, value)

        for attr in ATTRS_CELLPYDATA:
            value = getattr(cell, attr)
            setattr(new_cell, attr, value)
            setattr(old_cell, attr, value)

        cells.append(new_cell)

    cells.append(old_cell)

    return cells


def add_normalized_cycle_index(cell, nom_cap=None, column_name=None):
    """Adds normalized cycles to the summary data frame.

    This functionality is now also implemented as default when creating
    the summary (make_summary). However it is kept here if you would like to
    redo the normalization, for example if you want to use another nominal
    capacity or if you would like to have more than one normalized cycle index.

    Args:
        cell (CellpyData): cell object
        nom_cap (float): nominal capacity to use when normalizing. Defaults to
            the nominal capacity defined in the cell object (this is typically
            set during creation of the CellpyData object based on the value
            given in the parameter file).
        column_name (str): name of the new column. Uses the name defined in
            cellpy.parameters.internal_settings as default.

    Returns:
        cell object now with normalized cycle index in its summary.
    """
    # TODO: remove this function
    # now also included in dfsummary
    if column_name is None:
        column_name = hdr_summary.normalized_cycle_index
    h_cum_charge = hdr_summary.cumulated_charge_capacity

    if nom_cap is None:
        nom_cap = cell.cell.nom_cap
    cell.cell.summary[column_name] = cell.cell.summary[h_cum_charge] / nom_cap
    return cell


def add_c_rate(cell, nom_cap=None, column_name=None):
    """Adds C-rates to the step table data frame.

    This functionality is now also implemented as default when creating
    the step_table (make_step_table). However it is kept here if you would
    like to recalculate the C-rates, for example if you want to use another
    nominal capacity or if you would like to have more than one column with
    C-rates.

    Args:
        cell (CellpyData): cell object
        nom_cap (float): nominal capacity to use for estimating C-rates.
            Defaults to the nominal capacity defined in the cell object
            (this is typically set during creation of the CellpyData object
            based on the value given in the parameter file).
        column_name (str): name of the new column. Uses the name defined in
            cellpy.parameters.internal_settings as default.

    Returns:
        cell object.
    """

    # now also included in step_table
    # TODO: remove this function
    if column_name is None:
        column_name = hdr_steps["rate_avr"]
    if nom_cap is None:
        nom_cap = cell.cell.nom_cap

    spec_conv_factor = cell.get_converter_to_specific()
    cell.cell.steps[column_name] = abs(
        round(cell.cell.steps.current_avr / (nom_cap / spec_conv_factor), 2)
    )

    return cell


def add_areal_capacity(cell, cell_id, journal):
    """Adds areal capacity to the summary."""

    # obs! hard-coded col-names (please fix)
    loading = journal.pages.loc[cell_id, "loadings"]  # header 2 be changed

    cell.cell.summary["Areal_Charge_Capacity(mAh/cm2)"] = (
        cell.cell.summary["Charge_Capacity(mAh/g)"] * loading / 1000
    )
    cell.cell.summary["Areal_Discharge_Capacity(mAh/cm2)"] = (
        cell.cell.summary["Discharge_Capacity(mAh/g)"] * loading / 1000
    )
    return cell


def create_rate_column(df, nom_cap, spec_conv_factor, column="current_avr"):
    """Adds a rate column to the dataframe (steps)."""

    col = abs(round(df[column] / (nom_cap / spec_conv_factor), 2))
    return col


def select_summary_based_on_rate(
    cell, rate=None, rate_std=None, rate_column=None, inverse=False, inverted=False
):
    """Select only cycles charged or discharged with a given rate.

    Parameters:
        cell (cellpy.CellpyData)
        rate (float): the rate to filter on. Remark that it should be given
            as a float, i.e. you will have to convert from C-rate to
            the actual numeric value. For example, use rate=0.05 if you want
            to filter on cycles that has a C/20 rate.
        rate_std (float): fix me.
        rate_column (str): column header name of the rate column,
        inverse (bool): fix me.
        inverted (bool): fix me.

    Returns:
        filtered summary (Pandas.DataFrame).
    """

    if rate_column is None:
        rate_column = hdr_steps["rate_avr"]

    if rate is None:
        rate = 0.05
    if rate_std is None:
        rate_std = 0.1 * rate

    cycle_number_header = hdr_normal.cycle_index_txt

    step_table = cell.cell.steps
    summary = cell.cell.summary

    cycles_mask = (step_table[rate_column] < (rate + rate_std)) & (
        step_table[rate_column] > (rate - rate_std)
    )
    if inverse:
        cycles_mask = ~cycles_mask

    filtered_step_table = step_table[cycles_mask]

    filtered_cycles = filtered_step_table.cycle.unique()

    if inverted:
        filtered_summary = summary[~summary[cycle_number_header].isin(filtered_cycles)]
    else:
        filtered_summary = summary[summary[cycle_number_header].isin(filtered_cycles)]

    return filtered_summary


def add_normalized_capacity(cell, norm_cycles=None, individual_normalization=False):
    """Add normalized capacity to the summary.

    Args:
        cell (CellpyData): cell to add normalized capacity to.
        norm_cycles (list of ints): the cycles that will be used to find
            the normalization factor from (averaging their capacity)
        individual_normalization (bool): find normalization factor for both
            the charge and the discharge if true, else use normalization factor
            from charge on both charge and discharge.

    Returns:
        cell (CellpyData) with added normalization capacity columns in
        the summary.
    """

    if norm_cycles is None:
        norm_cycles = [1, 2, 3, 4, 5]

    col_name_charge = hdr_summary.charge_capacity
    col_name_discharge = hdr_summary.discharge_capacity

    norm_val_charge = cell.cell.summary.loc[norm_cycles, col_name_charge].mean()
    if individual_normalization:
        norm_val_discharge = cell.cell.summary.loc[
            norm_cycles, col_name_discharge
        ].mean()
    else:
        norm_val_discharge = norm_val_charge

    for col_name, norm_value in zip(
        [col_name_charge, col_name_discharge], [norm_val_charge, norm_val_discharge]
    ):
        norm_col_name = "_".join(["Normalized", col_name])
        cell.cell.summary[norm_col_name] = cell.cell.summary[col_name] / norm_value

    return cell
