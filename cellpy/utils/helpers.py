import logging
import os
import pathlib
from typing import Optional
import warnings
from copy import deepcopy

import numpy as np
import pandas as pd
from scipy import stats

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import (
    get_headers_journal,
    get_headers_summary,
    get_headers_step_table,
    get_headers_normal,
)
from cellpy.readers.cellreader import CellpyCell
from cellpy.utils.batch import Batch
from cellpy.internals.core import check_connection as _check_connection

hdr_summary = get_headers_summary()
hdr_steps = get_headers_step_table()
hdr_normal = get_headers_normal()
hdr_journal = get_headers_journal()


def _make_average_legacy(
    frames,
    keys=None,
    columns=None,
    skip_st_dev_for_equivalent_cycle_index=True,
    key_index_bounds=None,
):
    if key_index_bounds is None:
        key_index_bounds = [1, -2]
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    hdr_cum_charge = hdr_summary["cumulated_charge_capacity"]
    cell_id = ""
    not_a_number = np.nan
    new_frames = []

    if columns is None:
        columns = frames[0].columns

    if keys is not None:
        if isinstance(keys, (list, tuple)):
            cell_id = list(set(["_".join(k.split("_")[key_index_bounds[0] : key_index_bounds[1]]) for k in keys]))[0]
        elif isinstance(keys, str):
            cell_id = keys
    new_frame = pd.concat(frames, axis=1)
    for col in columns:
        number_of_cols = len(new_frame.columns)
        if col in [hdr_norm_cycle, hdr_cum_charge] and skip_st_dev_for_equivalent_cycle_index:
            if number_of_cols > 1:
                avg_frame = new_frame[col].agg(["mean"], axis=1).rename(columns={"mean": col})
            else:
                avg_frame = new_frame[col].copy()

        else:
            new_col_name_mean = col + "_mean"
            new_col_name_std = col + "_std"

            if number_of_cols > 1:
                avg_frame = (
                    new_frame[col]
                    .agg(["mean", "std"], axis=1)
                    .rename(columns={"mean": new_col_name_mean, "std": new_col_name_std})
                )
            else:
                avg_frame = pd.DataFrame(data=new_frame[col].values, columns=[new_col_name_mean])
                avg_frame[new_col_name_std] = not_a_number
        new_frames.append(avg_frame)
    final_frame = pd.concat(new_frames, axis=1)

    return final_frame, cell_id


def _make_average(
    frames,
    columns=None,
    skip_st_dev_for_equivalent_cycle_index=True,
    average_method="mean",
):
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    not_a_number = np.nan
    new_frames = []

    if columns is None:
        columns = frames[0].columns

    new_frame = pd.concat(frames, axis=1)
    normalized_cycle_index_frame = pd.DataFrame(index=new_frame.index)
    for col in columns:
        number_of_cols = len(new_frame.columns)
        if col == hdr_norm_cycle and skip_st_dev_for_equivalent_cycle_index:
            if number_of_cols > 1:
                normalized_cycle_index_frame = (
                    new_frame[col].agg([average_method], skipna=True, axis=1).rename(columns={average_method: "equivalent_cycle"})
                )
            else:
                normalized_cycle_index_frame = new_frame[col].copy()

        else:
            new_col_name_mean = average_method
            new_col_name_std = "std"

            if number_of_cols > 1:
                # sqr = _ensure_numeric((avg - values) ** 2)
                # TODO: Fix this - RuntimeWarning: invalid value encountered in subtract
                # Could consider using np.nanmean(new_frame[col]) instead of np.mean(new_frame[col])?
                
                # Replace inf with nan
                new_frame[col] = new_frame[col].replace([np.inf, -np.inf], np.nan)

                avg_frame = new_frame[col].agg([average_method, "std"], skipna=True, axis=1)
            else:
                avg_frame = pd.DataFrame(data=new_frame[col].values, columns=[new_col_name_mean])
                avg_frame[new_col_name_std] = not_a_number

            avg_frame = avg_frame.assign(variable=col)
            new_frames.append(avg_frame)

    if not normalized_cycle_index_frame.empty:
        new_frames = [pd.concat([normalized_cycle_index_frame, x], axis=1) for x in new_frames]
    final_frame = pd.concat(new_frames, axis=0)
    cols = final_frame.columns.to_list()
    new_cols = []
    for n in ["variable", average_method, "std"]:
        if n in cols:
            new_cols.append(n)
            cols.remove(n)
    cols.extend(new_cols)
    final_frame = final_frame.reindex(columns=cols)
    # rename the mean column to "mean" for backward compatibility:
    final_frame = final_frame.rename(columns={average_method: "mean"})
    return final_frame


def update_journal_cellpy_data_dir(pages, new_path=None, from_path="PureWindowsPath", to_path="Path"):
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
    pages.cellpy_file_names = pages.cellpy_file_names.apply(lambda x: to_path(new_path) / x.name)
    return pages


def make_new_cell():
    """create an empty CellpyCell object."""
    warnings.warn("make_new_cell is deprecated, use CellpyCell.vacant instead", DeprecationWarning)
    new_cell = cellpy.cellreader.CellpyCell(initialize=True)
    return new_cell


def add_normalized_cycle_index(summary, nom_cap, column_name=None):
    """Adds normalized cycles to the summary data frame.

    This functionality is now also implemented as default when creating
    the summary (make_summary). However, it is kept here if you would like to
    redo the normalization, for example if you want to use another nominal
    capacity or if you would like to have more than one normalized cycle index.

    Args:
        summary (pandas.DataFrame): data summary
        nom_cap (float): nominal capacity to use when normalizing.
        column_name (str): name of the new column. Uses the name defined in
            cellpy.parameters.internal_settings as default.

    Returns:
        data object now with normalized cycle index in its summary.
    """
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]
    hdr_cum_charge = hdr_summary["cumulated_charge_capacity_gravimetric"]

    if column_name is None:
        column_name = hdr_norm_cycle

    summary[column_name] = summary[hdr_cum_charge] / nom_cap
    return summary


def add_c_rate(cell, nom_cap=None, column_name=None):
    """Adds C-rates to the step table data frame.

    This functionality is now also implemented as default when creating
    the step_table (make_step_table). However, it is kept here if you would
    like to recalculate the C-rates, for example if you want to use another
    nominal capacity or if you would like to have more than one column with
    C-rates.

    Args:
        cell (CellpyCell): cell object
        nom_cap (float): nominal capacity to use for estimating C-rates.
            Defaults to the nominal capacity defined in the cell object
            (this is typically set during creation of the CellpyData object
            based on the value given in the parameter file).
        column_name (str): name of the new column. Uses the name defined in
            cellpy.parameters.internal_settings as default.

    Returns:
        data object.
    """

    # now also included in step_table
    # TODO: remove this function
    if column_name is None:
        column_name = hdr_steps["rate_avr"]
    if nom_cap is None:
        nom_cap = cell.data.nom_cap

    spec_conv_factor = cell.get_converter_to_specific()
    cell.data.steps[column_name] = abs(round(cell.data.steps.current_avr / (nom_cap / spec_conv_factor), 2))

    return cell


def add_areal_capacity(cell, cell_id, journal):
    """Adds areal capacity to the summary."""

    loading = journal.pages.loc[cell_id, hdr_journal["loading"]]

    cell.data.summary[hdr_summary["areal_charge_capacity"]] = (
        cell.data.summary[hdr_summary["charge_capacity"]] * loading / 1000
    )
    cell.data.summary[hdr_summary["areal_discharge_capacity"]] = (
        cell.data.summary[hdr_summary["discharge_capacity"]] * loading / 1000
    )
    return cell


def _remove_outliers_from_summary(s, filter_vals, freeze_indexes=None):
    if freeze_indexes is not None:
        try:
            filter_vals[freeze_indexes] = True
        except IndexError:
            logging.critical(f"Could not freeze - missing cycle indexes {freeze_indexes}")

    return s[filter_vals]


def remove_outliers_from_summary_on_window(s, window_size=3, cut=0.1, iterations=1, col_name=None, freeze_indexes=None):
    """Removes outliers based on neighbours"""
    if col_name is None:
        col = hdr_summary["charge_capacity"]

    else:
        col = hdr_summary[col_name]

    def fractional_std(x):
        return np.std(x) / np.mean(x)

    for j in range(iterations):
        fractional_deviation_series = (
            s[col].rolling(window=window_size, center=True, min_periods=1).apply(fractional_std)
        )
        filter_vals = fractional_deviation_series < cut
        s = s[filter_vals]

    s = _remove_outliers_from_summary(s, filter_vals, freeze_indexes=freeze_indexes)

    return s


def remove_outliers_from_summary_on_nn_distance(s, distance=0.7, filter_cols=None, freeze_indexes=None):
    """Remove outliers with missing neighbours.

    Args:
        s (pandas.DataFrame): summary frame
        distance (float): cut-off (all cycles that have a closest neighbour further apart this number will be removed)
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

    def neighbour_window(y):
        y = y.values
        if len(y) == 1:
            # only included in case the pandas rolling function changes in the future
            return 0.5
        if len(y) == 2:
            return abs(np.diff(y)) / np.mean(y)
        else:
            return min(abs(y[1] - y[0]), abs(y[1] - y[2])) / min(np.mean(y[0:1]), np.mean(y[1:]))

    s2 = s[filter_cols].copy()

    r = s2[filter_cols].rolling(3, center=True, min_periods=1).apply(neighbour_window)
    filter_vals = (r < distance).all(axis=1)

    s = _remove_outliers_from_summary(s, filter_vals, freeze_indexes=freeze_indexes)

    return s


def remove_outliers_from_summary_on_zscore(s, zscore_limit=4, filter_cols=None, freeze_indexes=None):
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


def remove_outliers_from_summary_on_value(s, low=0.0, high=7_000, filter_cols=None, freeze_indexes=None):
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
    logging.debug("removing outliers from summary on index")
    if indexes is None:
        indexes = []

    selection = s.index.isin(indexes)
    if remove_last:
        selection[-1] = True
    return s[~selection]


def remove_last_cycles_from_summary(s, last=None):
    """Remove last rows after given cycle number"""

    if last is not None:
        s = s.loc[s.index <= last, :]
    return s


def remove_first_cycles_from_summary(s, first=None):
    """Remove last rows after given cycle number"""

    if first is not None:
        s = s.loc[s.index >= first, :]
    return s


def yank_after(b, last=None, keep_old=False):
    """Cut all cycles after a given cycle index number.

    Args:
        b (batch object): the batch object to perform the cut on.
        last (int or dict {cell_name: last index}): the last cycle index to keep
            (if dict: use individual last indexes for each cell).
        keep_old (bool): keep the original batch object and return a copy instead.

    Returns:
        batch object if keep_old is True, else None
    """

    if keep_old:
        b = deepcopy(b)

    if last is None:
        return b

    for cell_number, cell_label in enumerate(b.experiment.cell_names):
        c = b.experiment.data[cell_label]
        s = c.data.summary
        if isinstance(last, dict):
            last_this_cell = last.get(cell_label, None)
        else:
            last_this_cell = last
        s = remove_last_cycles_from_summary(s, last_this_cell)
        c.data.summary = s
    if keep_old:
        return b


def yank_before(b, first=None, keep_old=False):
    """Cut all cycles before a given cycle index number.

    Args:
        b (batch object): the batch object to perform the cut on.
        first (int or dict {cell_name: first index}): the first cycle index to keep
            (if dict: use individual first indexes for each cell).
        keep_old (bool): keep the original batch object and return a copy instead.

    Returns:
        batch object if keep_old is True, else None
    """

    if keep_old:
        b = deepcopy(b)

    if first is None:
        return b

    for cell_number, cell_label in enumerate(b.experiment.cell_names):
        c = b.experiment.data[cell_label]
        s = c.data.summary
        if isinstance(first, dict):
            first_this_cell = first.get(cell_label, None)
        else:
            first_this_cell = first
        s = remove_first_cycles_from_summary(s, first_this_cell)
        c.data.summary = s
    if keep_old:
        return b


def yank_outliers(
    b: Batch,
    zscore_limit=None,
    low=0.0,
    high=7_000.0,
    filter_cols=None,
    freeze_indexes=None,
    remove_indexes=None,
    remove_last=False,
    iterations=1,
    zscore_multiplyer=1.3,
    distance=None,
    window_size=None,
    window_cut=0.1,
    keep_old=False,
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
        zscore_multiplyer (int): multiply `zscore_limit` with this number between each z-score filtering
            (should usually be less than 1).
        distance (float): nearest neighbour normalised distance required (typically 0.5).
        window_size (int): number of cycles to include in the window.
        window_cut (float): cut-off.

        keep_old (bool): perform filtering of a copy of the batch object
            (not recommended at the moment since it then loads the full cellpyfile).

    Returns:
        if keep_old: new cellpy.utils.batch object.
        else: dictionary of removed cycles
    """

    if keep_old:
        b = deepcopy(b)

    removed_cycles = dict()

    # remove based on indexes and values
    for cell_number, cell_label in enumerate(b.experiment.cell_names):
        logging.debug(f"yanking {cell_label} ")
        c = b.experiment.data[cell_label]
        s = c.data.summary
        before = set(s.index)
        if remove_indexes is not None:
            logging.debug("removing indexes")
            if isinstance(remove_indexes, dict):
                remove_indexes_this_cell = remove_indexes.get(cell_label, None)
            else:
                remove_indexes_this_cell = remove_indexes

            if isinstance(remove_last, dict):
                remove_last_this_cell = remove_last.get(cell_label, None)
            else:
                remove_last_this_cell = remove_last

            s = remove_outliers_from_summary_on_index(s, remove_indexes_this_cell, remove_last_this_cell)

        s = remove_outliers_from_summary_on_value(
            s,
            low=low,
            high=high,
            filter_cols=filter_cols,
            freeze_indexes=freeze_indexes,
        )

        if distance is not None:
            s = remove_outliers_from_summary_on_nn_distance(
                s,
                distance=distance,
                filter_cols=filter_cols,
                freeze_indexes=freeze_indexes,
            )
            c.data.summary = s

        if window_size is not None:
            s = remove_outliers_from_summary_on_window(
                s,
                window_size=window_size,
                cut=window_cut,
                iterations=iterations,
                freeze_indexes=freeze_indexes,
            )

        removed = before - set(s.index)
        c.data.summary = s
        if removed:
            removed_cycles[cell_label] = list(removed)

    if zscore_limit is not None:
        logging.info("using the zscore - removed cycles not kept track on")
        for j in range(iterations):
            tot_rows_removed = 0
            for cell_number, cell_label in enumerate(b.experiment.cell_names):
                c = b.experiment.data[cell_label]
                n1 = len(c.data.summary)
                s = remove_outliers_from_summary_on_zscore(
                    c.data.summary,
                    filter_cols=filter_cols,
                    zscore_limit=zscore_limit,
                    freeze_indexes=freeze_indexes,
                )
                # TODO: populate removed_cycles
                rows_removed = n1 - len(s)
                tot_rows_removed += rows_removed
                c.data.summary = s
            if tot_rows_removed == 0:
                break
            zscore_limit *= zscore_multiplyer

    if keep_old:
        return b
    else:
        return removed_cycles


def filter_cells():
    """Filter cells based on some criteria.

    This is a helper function that can be used to filter cells based on
    some criteria. It is not very flexible, but it is easy to use.

    Returns:
        a list of cell names that passed the criteria.
    """

    # TODO: refactor concatenate_summaries to use this function, then
    #  allow collectors to use it as well.

    pass


def concatenate_summaries(
    b: Batch,
    max_cycle=None,
    rate=None,
    on="charge",
    columns=None,
    column_names=None,
    normalize_capacity_on=None,
    scale_by=None,
    nom_cap=None,
    normalize_cycles=False,
    group_it=False,
    custom_group_labels=None,
    rate_std=None,
    rate_column=None,
    inverse=False,
    inverted=False,
    key_index_bounds=None,
) -> pd.DataFrame:
    """Merge all summaries in a batch into a gigantic summary data frame.

    Args:
        b (cellpy.batch object): the batch with the cells.
        max_cycle (int): drop all cycles above this value.
        rate (float): filter on rate (C-rate)
        on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        columns (list): selected column(s) (using cellpy attribute name) [defaults to "charge_capacity_gravimetric"]
        column_names (list): selected column(s) (using exact column name)
        normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the
            normalization (typically the first few cycles after formation)
        scale_by (float or str): scale the normalized data with nominal capacity if "nom_cap",
            or given value (defaults to one).
        nom_cap (float): nominal capacity of the cell
        normalize_cycles (bool): perform a normalization of the cycle numbers (also called equivalent cycle index)
        group_it (bool): if True, average pr group.
        custom_group_labels (dict): dictionary of custom labels (key must be the group number/name).
        rate_std (float): allow for this inaccuracy when selecting cycles based on rate
        rate_column (str): name of the column containing the C-rates.
        inverse (bool): select steps that do not have the given C-rate.
        inverted (bool): select cycles that do not have the steps filtered by given C-rate.
        key_index_bounds (list): used when creating a common label for the cells by splitting and combining from
            key_index_bound[0] to key_index_bound[1].

    Returns:
        ``pandas.DataFrame``
    """

    warnings.warn("This helper function is not maintained anymore", category=DeprecationWarning)

    if key_index_bounds is None:
        key_index_bounds = [1, -2]

    cell_names_nest = []
    group_nest = []

    if group_it:
        g = b.pages.groupby("group")
        # this ensures that order is kept and grouping is correct
        # it is therefore ok to assume from now on that all the cells within a list belongs to the same group
        for gno, b_sub in g:
            cell_names_nest.append(list(b_sub.index))
            group_nest.append(gno)
    else:
        cell_names_nest.append(list(b.experiment.cell_names))
        group_nest.append(b.pages.group.to_list())

    default_columns = [hdr_summary["charge_capacity_gravimetric"]]
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]

    if columns is None:
        columns = []

    if column_names is None:
        column_names = []

    if isinstance(columns, str):
        columns = [columns]

    if isinstance(column_names, str):
        column_names = [column_names]

    columns = [hdr_summary[name] for name in columns]
    columns += column_names

    if not columns:
        columns = default_columns

    output_columns = columns.copy()
    frames = []
    keys = []

    if normalize_cycles:
        if hdr_norm_cycle not in columns:
            output_columns.insert(0, hdr_norm_cycle)

    if normalize_capacity_on is not None:
        normalize_capacity_headers = [
            hdr_summary["normalized_charge_capacity"],
            hdr_summary["normalized_discharge_capacity"],
        ]
        output_columns = [
            col
            for col in output_columns
            if col
            not in [
                hdr_summary["charge_capacity"],
                hdr_summary["discharge_capacity"],
            ]
        ]
        output_columns.extend(normalize_capacity_headers)

    for gno, cell_names in zip(group_nest, cell_names_nest):
        frames_sub = []
        keys_sub = []
        for cell_id in cell_names:
            logging.debug(f"Processing [{cell_id}]")
            group = b.pages.loc[cell_id, "group"]
            sub_group = b.pages.loc[cell_id, "sub_group"]
            try:
                c = b.experiment.data[cell_id]
            except KeyError as e:
                logging.debug(f"Could not load data for {cell_id}")
                logging.debug(f"{e}")
                raise e

            if not c.empty:
                if max_cycle is not None:
                    c = c.drop_from(max_cycle + 1)
                if normalize_capacity_on is not None:
                    if scale_by == "nom_cap":
                        if nom_cap is None:
                            scale_by = c.data.nom_cap
                        else:
                            scale_by = nom_cap
                    elif scale_by is None:
                        scale_by = 1.0

                    c = add_normalized_capacity(c, norm_cycles=normalize_capacity_on, scale=scale_by)

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
                    s = c.data.summary

                if columns is not None:
                    s = s.loc[:, output_columns].copy()

                # somehow using normalized cycles (i.e. equivalent cycles) messes up the order of the index sometimes:
                if normalize_cycles:
                    s = s.reset_index()

                # add group and subgroup
                if not group_it:
                    s = s.assign(group=group, sub_group=sub_group)

                frames_sub.append(s)
                keys_sub.append(cell_id)

        if group_it:
            try:
                s, cell_id = _make_average_legacy(
                    frames_sub,
                    keys_sub,
                    output_columns,
                    key_index_bounds=key_index_bounds,
                )
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
            keys = fix_group_names(keys)

        return collect_frames(frames, group_it, hdr_norm_cycle, keys, normalize_cycles)
    else:
        logging.info("Empty - nothing to concatenate!")
        return pd.DataFrame()
    

def add_cv_step_columns(columns: list) -> list:
    """Add columns for CV steps.
    """
    new_columns = []
    for col in columns:
        if "_capacity" in col:
            new_columns.extend([col, col + "_cv", col + "_non_cv"])
        else:
            new_columns.append(col)
    return new_columns


def _partition_summary_based_on_cv_steps(
    c,
    column_set: Optional[list] = None,
    x: str = None,
):
    """Partition the summary data into CV and non-CV steps.

    Args:
        c: cellpy object
        column_set: names of columns to include
        x: x-axis column name (default is "cycle_index")

    Returns:
        ``pandas.DataFrame``
    """
    import pandas as pd

    if not x:
        x = hdr_summary["cycle_index"]

    summary = c.data.summary.copy()

    summary_no_cv = c.make_summary(selector_type="non-cv", create_copy=True).data.summary
    summary_only_cv = c.make_summary(selector_type="only-cv", create_copy=True).data.summary
    if x != summary.index.name:
        summary.set_index(x, inplace=True, drop=True)
        summary_no_cv.set_index(x, inplace=True, drop=True)
        summary_only_cv.set_index(x, inplace=True, drop=True)

    

    if column_set is None:
        column_set = summary.columns.tolist()
    else:
        # allow for non-existing columns in the dataframe:
        column_set = [col for col in column_set if col in summary.columns]

    # in case the column set already contains cv cols:
    column_set = [col for col in column_set if not "_cv" in col]

    summary = summary[column_set]

    summary_no_cv = summary_no_cv[column_set]
    summary_no_cv.columns = [col + "_non_cv" for col in summary_no_cv.columns]

    summary_only_cv = summary_only_cv[column_set]
    summary_only_cv.columns = [col + "_cv" for col in summary_only_cv.columns]

    s = pd.concat([summary, summary_no_cv, summary_only_cv], axis=1)

    return s


def concat_summaries(
    b: Batch,
    max_cycle=None,
    rate=None,
    on="charge",
    columns=None,
    column_names=None,
    normalize_capacity_on=None,
    scale_by=None,
    nom_cap=None,
    normalize_cycles=False,
    group_it=False,
    custom_group_labels=None,
    rate_std=None,
    rate_column=None,
    inverse=False,
    inverted=False,
    key_index_bounds=None,
    pages=None,
    recalc_summary_kwargs=None,
    recalc_step_table_kwargs=None,
    only_selected=False,
    experimental_feature_cell_selector=None,
    partition_by_cv=False,
    replace_inf_with_nan=True,
    individual_summary_hooks=None,
    concatenated_summary_hooks=None,
    drop_columns=None,
    average_method="mean",
    replace_extremes_with_nan=True,
    low_limit=-10e5,
    high_limit=10e5,
    *args,
    **kwargs,
) -> pd.DataFrame:
    """Merge all summaries in a batch into a gigantic summary data frame.

    Args:
        b (cellpy.batch object): the batch with the cells.
        max_cycle (int): drop all cycles above this value.
        rate (float): filter on rate (C-rate)
        on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        columns (list): selected column(s) (using cellpy attribute name) [defaults to "charge_capacity_gravimetric"]
        column_names (list): selected column(s) (using exact column name)
        normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the
            normalization (typically the first few cycles after formation)
        scale_by (float or str): scale the normalized data with nominal capacity if "nom_cap",
            or given value (defaults to one).
        nom_cap (float): nominal capacity of the cell
        normalize_cycles (bool): perform a normalization of the cycle numbers (also called equivalent cycle index)
        group_it (bool): if True, average pr group.
        partition_by_cv (bool): if True, partition the data by cv_step.
        custom_group_labels (dict): dictionary of custom labels (key must be the group number/name).
        rate_std (float): allow for this inaccuracy when selecting cycles based on rate
        rate_column (str): name of the column containing the C-rates.
        inverse (bool): select steps that do not have the given C-rate.
        inverted (bool): select cycles that do not have the steps filtered by given C-rate.
        key_index_bounds (list): used when creating a common label for the cells by splitting the label on '_'
            and combining again using the key_index_bounds as start and end index.
        pages (pandas.DataFrame): alternative pages (journal) of the batch object (if not given, it will use the
            pages from the batch object).
        recalc_summary_kwargs (dict): keyword arguments to be used when recalculating the summary. If not given, it
            will not recalculate the summary.
        recalc_step_table_kwargs (dict): keyword arguments to be used when recalculating the step table. If not given,
            it will not recalculate the step table.
        only_selected (bool): only use the selected cells.
        experimental_feature_cell_selector (list): list of cell names to select.
        partition_by_cv (bool): if True, partition the data by cv_step.
        replace_inf_with_nan (bool): if True, replace inf with nan in the summary data.
        individual_summary_hooks (list): list of functions to be applied to the individual summary data.
        concatenated_summary_hooks (list): list of functions to be applied to the concatenated summary data 
            (passed to the collect_frames function).
        drop_columns (list): list of columns to drop before concatenation.
        average_method (str): method to be used when averaging the summary data. Remark that for backward compatibility,
            the column name will be "mean" regardless of the actual method used.
        replace_extremes_with_nan (bool): if True, replace values outside the range [low_limit, high_limit] with nan 
            in the summary data.
        low_limit (float): lower limit for replacing extremes with nan if replace_extremes_with_nan is True.
        high_limit (float): upper limit for replacing extremes with nan if replace_extremes_with_nan is True.
        remove_last (bool): if True, remove the last cycle from the summary data.
        *args,**kwargs: additional arguments to be passed to the hooks.

    Returns:
        ``pandas.DataFrame``
    """

    remove_last = kwargs.pop("remove_last", False)

    if key_index_bounds is None:
        # TODO: consider changing this to [1, -1]
        key_index_bounds = [1, -2]

    cell_names_nest = []
    group_nest = []
    if pages is None:
        pages = b.pages

    if experimental_feature_cell_selector is not None:
        pages = pages.loc[experimental_feature_cell_selector].copy()

    # selection is performed here:
    if only_selected and "selected" in pages.columns:
        # might be too strict to use the == 1 here (consider allowing for all true values)
        pages = pages.loc[pages.selected == 1, :].copy()

    if group_it:
        g = pages.groupby("group")
        for gno, b_sub in g:
            if len(b_sub) < 2:
                print("Can not group with less than two cells")
                print("Setting 'group_it' to False")
                group_it = False
                break

    if group_it:
        g = pages.groupby("group")
        # this ensures that order is kept and grouping is correct
        # it is therefore ok to assume from now on that all the cells within a list belongs to the same group

        for gno, b_sub in g:
            cell_names_nest.append(list(b_sub.index))
            group_nest.append(gno)
    else:
        cell_names_nest.append(list(pages.index))
        group_nest.append(pages.group.to_list())

    default_columns = [hdr_summary["charge_capacity_gravimetric"]]
    hdr_norm_cycle = hdr_summary["normalized_cycle_index"]

    if columns is None:
        columns = []

    if column_names is None:
        column_names = []

    if isinstance(columns, str):
        columns = [columns]

    if isinstance(column_names, str):
        column_names = [column_names]

    columns = [hdr_summary[name] for name in columns]
    columns += column_names

    if not columns:
        columns = default_columns

    output_columns = columns.copy()
    frames = []
    keys = []

    if normalize_cycles:
        if hdr_norm_cycle not in columns:
            output_columns.insert(0, hdr_norm_cycle)

    if normalize_capacity_on is not None:
        normalize_capacity_headers = [
            hdr_summary["normalized_charge_capacity"],
            hdr_summary["normalized_discharge_capacity"],
        ]
        output_columns = [
            col
            for col in output_columns
            if col
            not in [
                hdr_summary["charge_capacity"],
                hdr_summary["discharge_capacity"],
            ]
        ]
        output_columns.extend(normalize_capacity_headers)

    if partition_by_cv:
        output_columns = add_cv_step_columns(output_columns)

    for gno, cell_names in zip(group_nest, cell_names_nest):
        # NOTE: to allow for hooks to add columns, all functions that operates in this loop 
        # must allow for non-existing columns in the dataframe!
        frames_sub = []
        keys_sub = []
        for cell_id in cell_names:
            output_columns_current_cell = output_columns.copy()
            logging.debug(f"Processing [{cell_id}]")
            group = pages.loc[cell_id, "group"]
            sub_group = pages.loc[cell_id, "sub_group"]
            if "group_label" in pages.columns:
                group_label = pages.loc[cell_id, "group_label"]
            else:
                group_label = None

            if "label" in pages.columns:
                label = pages.loc[cell_id, "label"]
            else:
                label = None
            try:
                c = b.experiment.data[cell_id]
            except KeyError as e:
                logging.debug(f"Could not load data for {cell_id}")
                logging.debug(f"{e}")
                raise e

            if not c.empty:
                if max_cycle is not None:
                    c = c.drop_from(max_cycle + 1)
                if recalc_step_table_kwargs is not None:
                    c.make_step_table(**recalc_step_table_kwargs)
                if recalc_summary_kwargs is not None:
                    c.make_summary(**recalc_summary_kwargs)
                if normalize_capacity_on is not None:
                    if scale_by == "nom_cap":
                        if nom_cap is None:
                            scale_by = c.data.nom_cap
                        else:
                            scale_by = nom_cap
                    elif scale_by is None:
                        scale_by = 1.0

                    c = add_normalized_capacity(c, norm_cycles=normalize_capacity_on, scale=scale_by)

                if rate is not None:
                    if partition_by_cv:
                        print("partitioning by cv_step is experimental for rate selection")

                    s = select_summary_based_on_rate(
                        c,
                        rate=rate,
                        on=on,
                        rate_std=rate_std,
                        rate_column=rate_column,
                        inverse=inverse,
                        inverted=inverted,
                        partition_by_cv=partition_by_cv,
                    )
                elif partition_by_cv:
                    s = _partition_summary_based_on_cv_steps(c, column_set=output_columns_current_cell)

                else:
                    s = c.data.summary

                if remove_last:
                    s = s.iloc[:-1]


                if individual_summary_hooks is not None:
                    logging.info("Experimental feature: applying individual summary hooks")
                    for hook in individual_summary_hooks:
                        logging.info(f"  -applying {hook.__name__} to {cell_id}")
                        s, output_columns_current_cell = hook(s, columns=output_columns_current_cell.copy(), *args, **kwargs)
                        output_columns = output_columns_current_cell.copy()


                if columns is not None:
                    # Fill columns that don't exist in the dataframe with nan
                    for col in output_columns:
                        if col not in s.columns:
                            s[col] = np.nan
                    s = s.loc[:, output_columns].copy()
                    if drop_columns:
                        logging.debug(f"Dropping columns: {drop_columns}")
                        logging.debug(f"Columns in s before dropping: {s.columns}")
                        s = s.drop(columns=drop_columns, errors="ignore")
                        logging.debug(f"Columns in s after dropping: {s.columns}")


                # add group and subgroup
                if not group_it:
                    s = s.assign(group=group, sub_group=sub_group, group_label=group_label, label=label)
                else:
                    s = s.assign(group_label=group_label)

                frames_sub.append(s)
                keys_sub.append(cell_id)

        if group_it:
            # TODO: update this to allow for more advanced naming of groups
            cell_id = create_group_names(custom_group_labels, gno, key_index_bounds, keys_sub, pages)
            try:
                # if we used drop_columns, we need to remove them from the output_columns
                if drop_columns:
                    output_columns_current_group = [col for col in output_columns if col not in drop_columns]
                else:
                    output_columns_current_group = output_columns.copy()
                s = _make_average(frames_sub, output_columns_current_group, average_method=average_method)
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
            keys = fix_group_names(keys)

        
        
        if replace_inf_with_nan:
            # a lot of plotting tools do not like inf values, so we replace them with nan
            frames = [frame.replace([np.inf, -np.inf], np.nan) for frame in frames]

        if replace_extremes_with_nan:
            if group_it:
                # averaging sometimes gives extreme values, so we replace them with nan
                logging.debug(f"Replacing extremes with nan: {low_limit} < mean < {high_limit}")
                for frame in frames:
                    frame.loc[frame["mean"] < low_limit, "mean"] = np.nan
                    frame.loc[frame["mean"] > high_limit, "mean"] = np.nan
            else:
                logging.debug(f"Replacing extremes with nan: {low_limit} < column < {high_limit}")
                for frame in frames:
                    # these frames can have multiple of columns that we dont now the name of so we need to iterate over them
                    # and check if they are floats.
                    for col in frame.columns:
                        if pd.api.types.is_float_dtype(frame[col]):
                            frame.loc[frame[col] < low_limit, col] = np.nan
                            frame.loc[frame[col] > high_limit, col] = np.nan

        return collect_frames(frames, group_it, hdr_norm_cycle, keys, normalize_cycles, concatenated_summary_hooks)
    else:
        logging.info("Empty - nothing to concatenate!")
        return pd.DataFrame()


def create_group_names(custom_group_labels, gno, key_index_bounds, keys_sub, pages):
    """Helper function for concat_summaries.

    The prioritisation of methods for creating the group name is as follows:
    1. custom_group_labels (if given)
    2. group_label in pages (if given)
    3. key_index_bounds and keys_sub (if no other option is available)

    Args:
        custom_group_labels (dict): dictionary of custom labels (key must be the group number).
        gno (int): group number.
        key_index_bounds (list): used when creating a common label for the cells by splitting the label on '_'
            and combining again using the key_index_bounds as start and end index.
        keys_sub (list): list of keys.
        pages (pandas.DataFrame): pages (journal) of the batch object. If the column "group_label" is present, it will
            be used to create the group name.

    """

    cell_id = None

    if custom_group_labels is not None:
        if isinstance(custom_group_labels, dict):
            if gno in custom_group_labels:
                cell_id = custom_group_labels[gno]
            else:
                if isinstance(gno, int):
                    cell_id = f"group-{gno:02d}"
                else:
                    cell_id = f"group-{gno}"
        elif isinstance(custom_group_labels, str):
            if isinstance(gno, int):
                cell_id = f"{custom_group_labels}-group-{gno:02d}"
            else:
                cell_id = f"{custom_group_labels}-group-{gno}"
        return cell_id

    if pages is not None:
        if "group_label" in pages.columns:
            cell_id = pages.loc[pages["group"] == gno, "group_label"].values[0]
            if isinstance(cell_id, str) and cell_id not in ["", "none"]:
                return cell_id

    if cell_id is None:
        # nothing else worked (or were chosen) - falling back to using key_index_bounds
        splitter = "_"
        cell_id = list(
            set([splitter.join(k.split(splitter)[key_index_bounds[0] : key_index_bounds[1]]) for k in keys_sub])
        )[0]
    return cell_id


def fix_group_names(keys):
    """Helper function for concat_summaries."""
    used_names = []
    new_keys = []
    for name in keys:
        while True:
            if name in used_names:
                name += "x"
            else:
                break
        new_keys.append(name)
        used_names.append(name)
    keys = new_keys
    return keys


def collect_frames(frames, group_it: bool, hdr_norm_cycle: str, keys: list, normalize_cycles: bool, hooks: list = None):
    """Helper function for concat_summaries."""
    cycle_header = "cycle"
    normalized_cycle_header = "equivalent_cycle"
    group_header = "group"
    sub_group_header = "sub_group"
    cell_header = "cell"
    id_vars = [cell_header, cycle_header]
    cdf = pd.concat(frames, keys=keys, axis=0, names=id_vars)
    cdf = cdf.reset_index(drop=False)

    if not group_it:
        id_vars.extend([group_header, sub_group_header])

    if normalize_cycles:
        cdf = cdf.rename(columns={hdr_norm_cycle: normalized_cycle_header})

    if hooks is not None:
        for hook in hooks:
            cdf = hook(cdf)

    return cdf


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
    partition_by_cv=False,
):
    """Select only cycles charged or discharged with a given rate.

    Parameters:
        cell (cellpy.CellpyCell)
        rate (float): the rate to filter on. Remark that it should be given
            as a float, i.e. you will have to convert from C-rate to
            the actual numeric value. For example, use rate=0.05 if you want
            to filter on cycles that has a C/20 rate.
        on (str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        rate_std (float): allow for this inaccuracy in C-rate when selecting cycles
        rate_column (str): column header name of the rate column,
        inverse (bool): select steps that do not have the given C-rate.
        inverted (bool): select cycles that do not have the steps filtered by given C-rate.
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

    step_table = cell.data.steps
    
    if partition_by_cv:
        summary = _partition_summary_based_on_cv_steps(cell.data.summary)
    else:
        summary = cell.data.summary

    if summary.index.name != cycle_number_header:
        warnings.warn(f"{cycle_number_header} not set as index\n" f"Current index :: {summary.index}\n")

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
        cycles_mask = (step_table[rate_column] < (rate + rate_std)) & (step_table[rate_column] > (rate - rate_std))

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


def add_normalized_capacity(cell, norm_cycles=None, individual_normalization=False, scale=1.0):
    """Add normalized capacity to the summary.

    Args:
        cell (CellpyCell): cell to add normalized capacity to.
        norm_cycles (list of ints): the cycles that will be used to find
            the normalization factor from (averaging their capacity)
        individual_normalization (bool): find normalization factor for both
            the charge and the discharge if true, else use normalization factor
            from charge on both charge and discharge.
        scale (float): scale of normalization (default is 1.0).

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

    try:
        norm_val_charge = cell.data.summary.loc[norm_cycles, col_name_charge].mean()
    except KeyError as e:
        print(f"Oh no! Are you sure these cycle indexes exist?")
        print(f"  norm_cycles: {norm_cycles}")
        print(f"  cycle indexes: {list(cell.data.summary.index)}")
        raise KeyError from e
    if individual_normalization:
        norm_val_discharge = cell.data.summary.loc[norm_cycles, col_name_discharge].mean()
    else:
        norm_val_discharge = norm_val_charge

    for col_name, norm_col_name, norm_value in zip(
        [col_name_charge, col_name_discharge],
        [col_name_norm_charge, col_name_norm_discharge],
        [norm_val_charge, norm_val_discharge],
    ):
        cell.data.summary[norm_col_name] = scale * cell.data.summary[col_name] / norm_value

    return cell


def check_connection(path=None):
    return _check_connection(path)


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
    d = CellpyCell()

    if not outdir:
        outdir = prms.Paths.cellpydatadir

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


def _check():
    print("Testing OtherPath-connection")
    info = check_connection()
    # p0 = "scp://odin/home/jepe@ad.ife.no/projects"
    # info = check_connection(p0)
    # p1 = "scp://odin/home/jepe@ad.ife.no/this-folder-does-not-exist"
    # info = check_connection(p1)
    # p2 = pathlib.Path(".").resolve()
    # info = check_connection(p2)
    # p3 = "scp://odin/home/evil@ad.ife.no/projects"
    # info = check_connection(p3)
    # p4 = "scp://madmax/home/evil@ad.ife.no/projects"
    # info = check_connection(p4)


if __name__ == "__main__":
    _check()
