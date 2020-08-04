import os
import logging
import pathlib
import warnings
import collections
from copy import deepcopy

import numpy as np
import pandas as pd
from scipy import stats

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import (
    get_headers_summary,
    get_headers_step_table,
    get_headers_normal,
    get_headers_journal,
    ATTRS_CELLPYDATA,
    ATTRS_DATASET,
)

from cellpy import prmreader
from cellpy.readers.cellreader import CellpyData
from cellpy.utils import batch, ica

hdr_summary = get_headers_summary()
hdr_steps = get_headers_step_table()
hdr_normal = get_headers_normal()
hdr_journal = get_headers_journal()


def _make_average(
    frames, keys=None, columns=None, normalize_cycles=False, key_index_bounds=None
):
    if key_index_bounds is None:
        key_index_bounds = [1, -2]
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    hdr_cum_charge = hdr_summary["cumulated_charge_capacity"]
    cell_id = ""
    not_a_number = np.NaN
    new_frames = []

    if columns is None:
        columns = frames[0].columns

    if keys is not None:
        if isinstance(keys, (list, tuple)):
            cell_id = list(
                set(
                    [
                        "_".join(
                            k.split("_")[key_index_bounds[0] : key_index_bounds[1]]
                        )
                        for k in keys
                    ]
                )
            )[0]
        elif isinstance(keys, str):
            cell_id = keys
    new_frame = pd.concat(frames, axis=1)

    for col in columns:
        number_of_cols = len(new_frame.columns)
        if col in [hdr_norm_cycle, hdr_cum_charge] and normalize_cycles:
            if number_of_cols > 1:
                avg_frame = (
                    new_frame[col].agg(["mean"], axis=1).rename(columns={"mean": col})
                )
            else:
                avg_frame = new_frame[col].copy()

        else:

            new_col_name_mean = col + "_mean"
            new_col_name_std = col + "_std"

            if number_of_cols > 1:
                # very slow:
                avg_frame = (
                    new_frame[col]
                    .agg(["mean", "std"], axis=1)
                    .rename(
                        columns={"mean": new_col_name_mean, "std": new_col_name_std,}
                    )
                )
            else:
                avg_frame = pd.DataFrame(
                    data=new_frame[col].values, columns=[new_col_name_mean]
                )
                avg_frame[new_col_name_std] = not_a_number

        new_frames.append(avg_frame)
    final_frame = pd.concat(new_frames, axis=1)

    return final_frame, cell_id


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
    warnings.warn(
        "make_new_cell is deprecated, use CellpyData.vacant instead", DeprecationWarning
    )
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
    warnings.warn(
        "split_experiment is deprecated, use CellpyData.split_many instead",
        DeprecationWarning,
    )

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
            data[data.cycle_index < b_cycle],
            data[data.cycle_index >= b_cycle],
        ]
        summary0, summary = [
            summary[summary.index < b_cycle],
            summary[summary.index >= b_cycle],
        ]

        new_cell = make_new_cell()

        new_cell.cell.steps = steptable0

        new_cell.cell.raw = data0
        new_cell.cell.summary = summary0

        old_cell = make_new_cell()
        old_cell.cell.steps = steptable

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


def add_normalized_cycle_index(summary, nom_cap=None, column_name=None):
    """Adds normalized cycles to the summary data frame.

    This functionality is now also implemented as default when creating
    the summary (make_summary). However it is kept here if you would like to
    redo the normalization, for example if you want to use another nominal
    capacity or if you would like to have more than one normalized cycle index.

    Args:
        summary (pandas.DataFrame): cell summary
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
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    hdr_cum_charge = hdr_summary["cumulated_charge_capacity"]

    if column_name is None:
        column_name = hdr_norm_cycle
    hdr_cum_charge = hdr_cum_charge

    # if nom_cap is None:
    #   nom_cap = cell.cell.nom_cap
    summary[column_name] = summary[hdr_cum_charge] / nom_cap
    return summary


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

    loading = journal.pages.loc[cell_id, hdr_journal["loading"]]

    cell.cell.summary[hdr_summary["areal_charge_capacity"]] = (
        cell.cell.summary[hdr_summary["charge_capacity"]] * loading / 1000
    )
    cell.cell.summary[hdr_summary["areal_discharge_capacity"]] = (
        cell.cell.summary[hdr_summary["discharge_capacity"]] * loading / 1000
    )
    return cell


def _remove_outliers_from_summary(s, filter_vals, freeze_indexes=None):
    if freeze_indexes is not None:
        filter_vals[freeze_indexes] = True

    return s[filter_vals]


def remove_outliers_from_summary_on_zscore(
    s, zscore_limit=4, filter_cols=None, freeze_indexes=None
):
    """Remove outliers based on z-score.

    Args:
        s (pandas.DataFrame): summary frame
        zscore_limit (int): remove outliers outside this z-score limit
        filter_cols (list): list of column headers to perform the filtering on (defaults to charge and discharge capacity)
        freeze_indexes (list): list of cycle indexes that should never be removed (defaults to cycle 1)

    Returns:
        filtered summary (pandas.DataFrame)
    """

    if freeze_indexes is None:
        freeze_indexes = [1]

    if filter_cols is None:
        filter_cols = [
            hdr_summary["charge_capacity"],
            hdr_summary["discharge_capacity"],
        ]

    s2 = s[filter_cols].copy()

    filter_vals = (np.abs(stats.zscore(s2)) < zscore_limit).all(axis=1)

    s = _remove_outliers_from_summary(s, filter_vals, freeze_indexes=freeze_indexes)

    return s


def remove_outliers_from_summary_on_value(
    s, low=0.0, high=7_000, filter_cols=None, freeze_indexes=None
):
    """Remove outliers based highest and lowest allowed value

    Args:
        s (pandas.DataFrame): summary frame
        low (float): low cut-off (all cycles with values below this number will be removed)
        high (float): high cut-off (all cycles with values above this number will be removed)
        filter_cols (list): list of column headers to perform the filtering on (defaults to charge and discharge capacity)
        freeze_indexes (list): list of cycle indexes that should never be removed (defaults to cycle 1)

    Returns:
        filtered summary (pandas.DataFrame)

    Returns:

    """
    if filter_cols is None:
        filter_cols = [
            hdr_summary["charge_capacity"],
            hdr_summary["discharge_capacity"],
        ]

    s2 = s[filter_cols].copy()

    filter_vals = ((s2[filter_cols] > low) & (s2[filter_cols] < high)).all(axis=1)

    s = _remove_outliers_from_summary(s, filter_vals, freeze_indexes=freeze_indexes)

    return s


def remove_outliers_from_summary_on_index(s, indexes=None, remove_last=False):
    """Remove rows with supplied indexes (where the indexes typically are cycle-indexes).

    Args:
        s (pandas.DataFrame): cellpy summary to process
        indexes (list): list of indexes
        remove_last (bool): remove the last point

    Returns:
        pandas.DataFrame
    """
    if indexes is None:
        indexes = []

    selection = s.index.isin(indexes)
    if remove_last:
        selection[-1] = True

    return s[~selection]


def yank_outliers(
    b,
    zscore_limit=None,
    low=0.0,
    high=7_000.0,
    filter_cols=None,
    freeze_indexes=None,
    remove_indexes=None,
    remove_last=False,
    iterations=1,
    zscore_multiplyer=1.3,
    keep_old=True,
):
    """Remove outliers from a batch object.

    Args:
        b (cellpy.utils.batch object): the batch object to perform filtering one (required).
        zscore_limit (int): will filter based on z-score if given.
        low (float): low cut-off (all cycles with values below this number will be removed)
        high (float): high cut-off (all cycles with values above this number will be removed)
        filter_cols (str): what columns to filter on.
        freeze_indexes (list): indexes (cycles) that should never be removed.
        remove_indexes (dict or list): if dict, look-up on cell label, else a list that will be the same for all
        remove_last (dict or bool): if dict, look-up on cell label.
        iterations (int): repeat z-score filtering if `zscore_limit` is given.
        zscore_multiplyer (int): multiply `zscore_limit` with this number between each z-score filtering (should usually be less than 1).
        keep_old (bool): perform filtering of a copy of the batch object.

    Returns:
        cellpy.utils.batch object (returns a copy if `keep_old` is True).
    """

    if keep_old:
        b = deepcopy(b)

    # remove based on indexes and values
    for cell_number, cell_label in enumerate(b.experiment.cell_names):
        c = b.experiment.data[cell_label]
        s = c.cell.summary
        if remove_indexes is not None:
            if isinstance(remove_indexes, dict):
                remove_indexes_this_cell = remove_indexes.get(cell_label, None)
            else:
                remove_indexes_this_cell = remove_indexes

            if isinstance(remove_last, dict):
                remove_last_this_cell = remove_last.get(cell_label, None)
            else:
                remove_last_this_cell = remove_last

            s = remove_outliers_from_summary_on_index(
                s, remove_indexes_this_cell, remove_last_this_cell
            )
        s = remove_outliers_from_summary_on_value(
            s,
            low=low,
            high=high,
            filter_cols=filter_cols,
            freeze_indexes=freeze_indexes,
        )
        c.cell.summary = s

    # removed based on zscore
    if zscore_limit is not None:
        for j in range(iterations):
            tot_rows_removed = 0
            for cell_number, cell_label in enumerate(b.experiment.cell_names):
                c = b.experiment.data[cell_label]
                n1 = len(c.cell.summary)
                s = remove_outliers_from_summary_on_zscore(
                    c.cell.summary,
                    filter_cols=filter_cols,
                    zscore_limit=zscore_limit,
                    freeze_indexes=freeze_indexes,
                )

                rows_removed = n1 - len(s)
                tot_rows_removed += rows_removed
                c.cell.summary = s
            if tot_rows_removed == 0:
                break
            zscore_limit *= zscore_multiplyer
    return b


# from helpers - updated
def concatenate_summaries(
    b,
    rate=None,
    on="charge",
    columns=None,
    column_names=None,
    normalize_capacity_on=None,
    nom_cap=None,
    normalize_cycles=False,
    add_areal=False,
    group_it=False,
    rate_std=None,
    rate_column=None,
    inverse=False,
    inverted=False,
):

    """Merge all summaries in a batch into a gigantic summary data frame.

    TODO: Allow also dictionaries of cell objects.
    TODO: Allow iterating through batch-objects (for id, name in b.iteritems() or similar)

    Args:
        b (cellpy.batch object): the batch with the cells.
        rate (float): filter on rate (C-rate)
        on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        columns (list): selected column(s) (using cellpy name) [defaults to "charge_capacity"]
        column_names (list): selected column(s) (using exact column name)
        normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the normalization (typically the first few cycles after formation)
        nom_cap (float): nominal capacity of the cell
        normalize_cycles (bool): perform a normalisation of the cycle numbers (also called equivalent cycle index)
        add_areal (bool):  add areal capacity to the summary
        group_it (bool): if True, average pr group.
        rate_std (float): allow for this inaccuracy when selecting cycles based on rate
        rate_column (str): name of the column containing the C-rates.
        inverse (bool): select steps that does not have the given C-rate.
        inverted (bool): select cycles that does not have the steps filtered by given C-rate.

    Returns:
        Multi-index pandas.DataFrame
            top-level columns: cell-names (cell_name)
            second-level columns: summary headers (summary_headers)
            row-index: cycle number (cycle_index)

    """
    if normalize_capacity_on is not None:
        default_columns = ["normalized_charge_capacity"]
    else:
        default_columns = ["charge_capacity"]

    import logging

    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    hdr_cum_charge = hdr_summary["cumulated_charge_capacity"]

    cell_names_nest = []
    frames = []
    keys = []

    if columns is not None:
        if normalize_capacity_on is not None:
            _columns = []
            for name in columns:
                if name.startswith("normalized_"):
                    _columns.append(hdr_summary[name])
                else:
                    _columns.append(hdr_summary["normalized_" + name])
            columns = _columns
        else:
            columns = [hdr_summary[name] for name in columns]
    else:
        columns = [hdr_summary[name] for name in default_columns]

    if column_names is not None:
        columns += column_names

    normalize_cycles_headers = []

    if normalize_cycles:
        if hdr_norm_cycle not in columns:
            normalize_cycles_headers.append(hdr_norm_cycle)
        if hdr_cum_charge not in columns:
            normalize_cycles_headers.append(hdr_cum_charge)

    if group_it:
        g = b.pages.groupby("group")
        for gno, b_sub in g:
            cell_names_nest.append(list(b_sub.index))
    else:
        cell_names_nest.append(list(b.experiment.cell_names))

    for cell_names in cell_names_nest:
        frames_sub = []
        keys_sub = []

        for cell_id in cell_names:
            logging.debug(f"Processing [{cell_id}]")
            c = b.experiment.data[cell_id]

            if not c.empty:
                if add_areal:
                    c = add_areal_capacity(c, cell_id, b.experiment.journal)

                if normalize_capacity_on is not None:
                    c = add_normalized_capacity(c, norm_cycles=normalize_capacity_on)

                if rate is not None:
                    s = select_summary_based_on_rate(
                        c,
                        rate=rate,
                        on=on,
                        rate_std=rate_std,
                        rate_column=rate_column,
                        inverse=inverse,
                        inverted=inverted,
                    )

                else:
                    s = c.cell.summary

                if columns is not None:
                    if normalize_cycles:
                        s = s.loc[:, normalize_cycles_headers + columns].copy()
                    else:
                        s = s.loc[:, columns].copy()

                if normalize_cycles:
                    if nom_cap is None:
                        _nom_cap = c.cell.nom_cap
                    else:
                        _nom_cap = nom_cap

                    if not group_it:
                        s = add_normalized_cycle_index(s, nom_cap=_nom_cap)
                        if hdr_cum_charge not in columns:
                            s = s.drop(columns=hdr_cum_charge)

                    s = s.reset_index(drop=True)

                frames_sub.append(s)
                keys_sub.append(cell_id)

        if group_it:
            try:
                if normalize_cycles:
                    s, cell_id = _make_average(
                        frames_sub, keys_sub, normalize_cycles_headers + columns, True
                    )
                    s = add_normalized_cycle_index(s, nom_cap=_nom_cap)
                    if hdr_cum_charge not in columns:
                        s = s.drop(columns=hdr_cum_charge)
                else:
                    s, cell_id = _make_average(frames_sub, keys_sub, columns)
            except ValueError as e:
                print("could not make average!")
                print(e)
            else:
                frames.append(s)
                keys.append(cell_id)
        else:
            frames.extend(frames_sub)
            keys.extend(keys_sub)

    if frames:
        if len(set(keys)) != len(keys):
            logging.info("Got several columns with same test-name")
            logging.info("Renaming.")
            used_names = []
            new_keys = []
            for name in keys:
                if name in used_names:
                    name += "x"
                new_keys.append(name)
                used_names.append(name)
            keys = new_keys
        cdf = pd.concat(frames, keys=keys, axis=1)
        cdf = cdf.rename_axis(columns=["cell_name", "summary_header"])
        return cdf
    else:
        logging.info("Empty - nothing to concatenate!")
        return pd.DataFrame()


def create_rate_column(df, nom_cap, spec_conv_factor, column="current_avr"):
    """Adds a rate column to the dataframe (steps)."""

    col = abs(round(df[column] / (nom_cap / spec_conv_factor), 2))
    return col


def select_summary_based_on_rate(
    cell,
    rate=None,
    on=None,
    rate_std=None,
    rate_column=None,
    inverse=False,
    inverted=False,
    fix_index=True,
):
    """Select only cycles charged or discharged with a given rate.

    Parameters:
        cell (cellpy.CellpyData)
        rate (float): the rate to filter on. Remark that it should be given
            as a float, i.e. you will have to convert from C-rate to
            the actual numeric value. For example, use rate=0.05 if you want
            to filter on cycles that has a C/20 rate.
        on (str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        rate_std (float): allow for this inaccuracy in C-rate when selecting cycles
        rate_column (str): column header name of the rate column,
        inverse (bool): select steps that does not have the given C-rate.
        inverted (bool): select cycles that does not have the steps filtered by given C-rate.
        fix_index (bool): automatically set cycle indexes as the index for the summary dataframe if not already set.

    Returns:
        filtered summary (Pandas.DataFrame).
    """

    if on is None:
        on = ["charge"]
    else:
        if not isinstance(on, (list, tuple)):
            on = [on]

    if rate_column is None:
        rate_column = hdr_steps["rate_avr"]

    if on:
        on_column = hdr_steps["type"]

    if rate is None:
        rate = 0.05

    if rate_std is None:
        rate_std = 0.1 * rate

    cycle_number_header = hdr_summary["cycle_index"]

    step_table = cell.cell.steps
    summary = cell.cell.summary

    if summary.index.name != cycle_number_header:
        warnings.warn(
            f"{cycle_number_header} not set as index\n"
            f"Current index :: {summary.index}\n"
        )

        if fix_index:
            summary.set_index(cycle_number_header, drop=True, inplace=True)
        else:
            print(f"{cycle_number_header} not set as index!")
            print(f"Please, set the cycle index header as index before proceeding!")
            return summary

    if on:
        cycles_mask = (
            (step_table[rate_column] < (rate + rate_std))
            & (step_table[rate_column] > (rate - rate_std))
            & (step_table[on_column].isin(on))
        )
    else:
        cycles_mask = (step_table[rate_column] < (rate + rate_std)) & (
            step_table[rate_column] > (rate - rate_std)
        )

    if inverse:
        cycles_mask = ~cycles_mask

    filtered_step_table = step_table[cycles_mask]
    filtered_cycles = filtered_step_table[hdr_steps.cycle].unique()

    if inverted:
        filtered_index = summary.index.difference(filtered_cycles)
    else:
        filtered_index = summary.index.intersection(filtered_cycles)

    if filtered_index.empty:
        warnings.warn("EMPTY")

    return summary.loc[filtered_index, :]


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

    col_name_charge = hdr_summary["charge_capacity"]
    col_name_discharge = hdr_summary["discharge_capacity"]
    col_name_norm_charge = hdr_summary["normalized_charge_capacity"]
    col_name_norm_discharge = hdr_summary["normalized_discharge_capacity"]

    norm_val_charge = cell.cell.summary.loc[norm_cycles, col_name_charge].mean()
    if individual_normalization:
        norm_val_discharge = cell.cell.summary.loc[
            norm_cycles, col_name_discharge
        ].mean()
    else:
        norm_val_discharge = norm_val_charge

    for col_name, norm_col_name, norm_value in zip(
        [col_name_charge, col_name_discharge],
        [col_name_norm_charge, col_name_norm_discharge],
        [norm_val_charge, norm_val_discharge],
    ):
        cell.cell.summary[norm_col_name] = cell.cell.summary[col_name] / norm_value

    return cell


def load_and_save_resfile(filename, outfile=None, outdir=None, mass=1.00):
    """Load a raw data file and save it as cellpy-file.

    Args:
        mass (float): active material mass [mg].
        outdir (path): optional, path to directory for saving the hdf5-file.
        outfile (str): optional, name of hdf5-file.
        filename (str): name of the resfile.

    Returns:
        out_file_name (str): name of saved file.
    """
    warnings.warn(DeprecationWarning("This option will be removed in v.0.4.0"))
    d = CellpyData()

    if not outdir:
        outdir = prms.Paths["cellpydatadir"]

    if not outfile:
        outfile = os.path.basename(filename).split(".")[0] + ".h5"
        outfile = os.path.join(outdir, outfile)

    print("filename:", filename)
    print("outfile:", outfile)
    print("outdir:", outdir)
    print("mass:", mass, "mg")

    d.from_raw(filename)
    d.set_mass(mass)
    d.make_step_table()
    d.make_summary()
    d.save(filename=outfile)
    d.to_csv(datadir=outdir, cycles=True, raw=True, summary=True)
    return outfile
