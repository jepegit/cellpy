import numpy as np
import pandas as pd
import os
import pathlib

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import (
    get_headers_summary, get_cellpy_units,
    get_headers_normal, get_headers_step_table, cellpy_attributes
)
from cellpy import prmreader
from cellpy.utils import batch, ica


hdr_summary = get_headers_summary()


def update_journal_cellpy_data_dir(pages, new_path=None,
                                   from_path="PureWindowsPath", to_path="Path"):
    if new_path is None:
        new_path = prms.Paths.cellpydatadir

    from_path = getattr(pathlib, from_path)
    to_path = getattr(pathlib, to_path)

    pages.cellpy_file_names = pages.cellpy_file_names.apply(from_path)
    pages.cellpy_file_names = pages.cellpy_file_names.apply(
        lambda x: to_path(new_path) / x.name)
    return pages


cellpydata_attr_that_should_be_copied = [
    'auto_dirs', 'capacity_modifiers', 'cellpy_datadir', 'cycle_mode',
    'daniel_number', 'ensure_step_table',
    'file_names', 'filestatuschecker', 'force_all', 'force_step_table_creation',
    'forced_errors', 'limit_loaded_cycles',
    'load_only_summary', 'minimum_selection', 'name', 'number_of_datasets',
    'profile', 'raw_datadir', 'raw_limits',
    'raw_units', 'select_minimal', 'selected_dataset_number', 'selected_scans',
    'sep', 'status_datasets', 'summary_exists',
    'table_names', 'tester'
]

dataset_attr_that_should_be_copied = [
    'cellpy_file_version', 'channel_index', 'channel_number', 'charge_steps',
    'creator', 'data',
    'discharge_steps', 'file_errors', 'ir_steps', 'item_ID', 'loaded_from',
    'mass', 'mass_given', 'material',
    'merged', 'name', 'no_cycles', 'nom_cap', 'normal_table_version',
    'ocv_steps', 'raw_data_files', 'raw_data_files_length',
    'raw_limits', 'raw_units', 'schedule_file_name', 'start_datetime',
    'step_table_version', 'summary',
    'summary_version', 'test_ID', 'test_no', 'tot_mass'
]


def make_new_cell():
    new_cell = cellpy.cellreader.CellpyData()
    data = cellpy.cellreader.DataSet()
    new_cell.datasets.append(data)
    return new_cell


def split_experiment(cell, base_cycles=None):
    """Split experiment (CellpyData object) into several sub-experiments."""

    if base_cycles is None:
        all_cycles = cell.get_cycle_numbers()
        base_cycles = int(np.median(all_cycles))

    cells = list()
    if not isinstance(base_cycles, (list, tuple)):
        base_cycles = [base_cycles]

    dataset = cell.dataset
    steptable = dataset.step_table
    data = dataset.dfdata
    summary = dataset.dfsummary

    for b_cycle in base_cycles:
        steptable0, steptable = [steptable[steptable.cycle < b_cycle],
                                 steptable[steptable.cycle >= b_cycle]]
        data0, data = [data[data.Cycle_Index < b_cycle],
                       data[data.Cycle_Index >= b_cycle]]
        summary0, summary = [summary[summary.index < b_cycle],
                             summary[summary.index >= b_cycle]]

        new_cell = make_new_cell()

        new_cell.dataset.step_table = steptable0
        # new_cell.dataset.step_table_made = True

        new_cell.dataset.dfdata = data0
        new_cell.dataset.dfsummary = summary0

        old_cell = make_new_cell()
        old_cell.dataset.step_table = steptable
        # old_cell.dataset.step_table_made = True

        old_cell.dataset.dfdata = data
        old_cell.dataset.dfsummary = summary

        for attr in dataset_attr_that_should_be_copied:
            value = getattr(cell.dataset, attr)
            setattr(new_cell.dataset, attr, value)
            setattr(old_cell.dataset, attr, value)

        for attr in cellpydata_attr_that_should_be_copied:
            value = getattr(cell, attr)
            setattr(new_cell, attr, value)
            setattr(old_cell, attr, value)

        cells.append(new_cell)

    cells.append(old_cell)

    return cells


def add_normalized_cycle_index(cell, nom_cap=None, column_name=None):
    """Adds normalized cycles to the summary data frame."""

    # now also included in dfsummary
    if column_name is None:
        column_name = hdr_summary.normalized_cycle_index
    h_cum_charge = hdr_summary.cumulated_charge_capacity

    if nom_cap is None:
        nom_cap = cell.dataset.nom_cap
    cell.dataset.dfsummary[column_name] = cell.dataset.dfsummary[
        h_cum_charge
    ] / nom_cap
    return cell


def add_c_rate(cell, column_name="rate_avr"):
    """Adds c-rates to the step table data frame."""

    # obs! hard-coded col-names (please fix)
    nom_cap = cell.dataset.nom_cap
    spec_conv_factor = cell.get_converter_to_specific()
    cell.dataset.step_table[column_name] = abs(
        round(
            cell.dataset.step_table.current_avr / (nom_cap / spec_conv_factor),
            2)
    )

    return cell


def add_areal_capacity(cell, cell_id, journal):

    # obs! hard-coded col-names (please fix)
    loading = journal.pages.loc[cell_id, "loadings"]
    cell.dataset.dfsummary["Areal_Charge_Capacity(mAh/cm2)"] = \
    cell.dataset.dfsummary["Charge_Capacity(mAh/g)"] * loading / 1000
    cell.dataset.dfsummary["Areal_Discharge_Capacity(mAh/cm2)"] = \
    cell.dataset.dfsummary["Discharge_Capacity(mAh/g)"] * loading / 1000
    return cell


def create_rate_column(df, nom_cap, spec_conv_factor, column="current_avr"):
    # obs! hard-coded col-names (please fix)
    col = abs(
        round(df[column] / (nom_cap / spec_conv_factor), 2)
    )
    return col


def select_summary_based_on_rate(cell, rate=None, rate_std=None,
                                 rate_column="rate_avr", inverse=False,
                                 inverted=False):
    """Select only cycles charged or discharged with a given rate.

    Parameters:
        cell (cellpy.CellpyData)
        rate (float): the rate to filter on. Remark that it should be given
            as a float, i.e. you will have to convert from C-rate to
            the actual nummeric value. For example, use rate=0.05 if you want
            to filter on cycles that has a C/20 rate.
        rate_std (float): fix me.
        rate_column (str): column header name to use for the rate column,
        inverse (bool): fix me.
        inverted (bool): fix me.

    Returns:
        filtered summary (Pandas.DataFrame).
    """

    # obs! hard-coded col-names (please fix)
    if rate is None:
        rate = 0.05
    if rate_std is None:
        rate_std = 0.1 * rate

    step_table = cell.dataset.step_table
    summary = cell.dataset.dfsummary

    cycles_mask = (step_table[rate_column] < (rate + rate_std)) & (
        step_table[rate_column] > (rate - rate_std))
    if inverse:
        cycles_mask = ~cycles_mask

    filtered_step_table = step_table[cycles_mask]

    filtered_cycles = filtered_step_table.cycle.unique()

    if inverted:
        filtered_summary = summary[~summary.index.isin(filtered_cycles)]
    else:
        filtered_summary = summary[summary.index.isin(filtered_cycles)]

    return filtered_summary


def add_normalized_capacity(cell, norm_cycles=None,
                            individual_normalization=False):

    # obs! hard-coded col-names (please fix)
    if norm_cycles is None:
        norm_cycles = [1, 2, 3, 4, 5]

    col_name_charge = "Charge_Capacity(mAh/g)"
    col_name_discharge = "Discharge_Capacity(mAh/g)"

    norm_val_charge = cell.dataset.dfsummary.loc[
        norm_cycles, col_name_charge].mean()
    if individual_normalization:
        norm_val_discharge = cell.dataset.dfsummary.loc[
            norm_cycles, col_name_discharge].mean()
    else:
        norm_val_discharge = norm_val_charge

    norm_val = norm_val_charge

    for col_name, norm_value in zip(
        [col_name_charge, col_name_discharge],
        [norm_val_charge, norm_val_discharge]
    ):
        norm_col_name = "_".join(["Normalized", col_name])
        cell.dataset.dfsummary[norm_col_name] = cell.dataset.dfsummary[
                                                    col_name] / norm_val

    return cell
