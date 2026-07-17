"""Capacity/voltage curve extraction for CellpyCell (issue #509, V2-09).

Moved verbatim from ``cellreader.py`` (the capacity getters "deserve their own
module" per the long-standing TODO). Functions take the ``CellpyCell``
instance as their first argument; ``CellpyCell`` keeps thin delegate methods
with identical signatures, so the public API is unchanged. Cross-calls go
through the instance (``cell.get_ccap(...)``, ``cell._get_cap(...)`` ...) to
preserve subclass dispatch exactly as before the move.
"""

import collections
import logging
import warnings
from typing import TYPE_CHECKING

import cellpy.config as config

from . import externals as externals
from cellpy.readers import data_structures as ds
from cellpy.exceptions import NullData

if TYPE_CHECKING:
    from cellpy.readers.cellreader import CellpyCell


def get_dcap(
    cell,
    cycle=None,
    converter=None,
    mode="gravimetric",
    as_frame=True,
    usteps=False,
    **kwargs,
):
    """Returns discharge capacity and voltage for the selected cycle.

    Args:
        cycle (int): cycle number.
        converter (float): a multiplication factor that converts the values to
            specific values (i.e. from Ah to mAh/g). If not provided (or None),
            the factor is obtained from the cell.get_converter_to_specific() method.
        mode (str): 'gravimetric', 'areal' or 'absolute'. Defaults to 'gravimetric'. Used
            if converter is not provided (or None).
        as_frame (bool): if True: returns externals.pandas.DataFrame instead of capacity, voltage series.
        **kwargs (dict): additional keyword arguments sent to the internal _get_cap method.

    Returns:
        ``pandas.DataFrame`` or list of ``pandas.Series`` if cycle=None and as_frame=False.

    """

    if converter is None:
        converter = cell.get_converter_to_specific(mode=mode)

    dc, v = cell._get_cap(
        cycle, "discharge", converter=converter, usteps=usteps, **kwargs
    )
    if as_frame:
        cycle_df = externals.pandas.concat([v, dc], axis=1)
        return cycle_df
    else:
        return dc, v

def get_ccap(
    cell,
    cycle=None,
    converter=None,
    mode="gravimetric",
    as_frame=True,
    usteps=False,
    **kwargs,
):
    """Returns charge capacity and voltage for the selected cycle.

    Args:
        cycle (int): cycle number.
        converter (float): a multiplication factor that converts the values to
            specific values (i.e. from Ah to mAh/g). If not provided (or None),
            the factor is obtained from the cell.get_converter_to_specific() method.
        mode (str): 'gravimetric', 'areal' or 'absolute'. Defaults to 'gravimetric'. Used
            if converter is not provided (or None).
        as_frame (bool): if True: returns externals.pandas.DataFrame instead of capacity, voltage series.
        **kwargs (dict): additional keyword arguments sent to the internal _get_cap method.

    Returns:
        ``pandas.DataFrame`` or list of ``pandas.Series`` if cycle=None and as_frame=False.

    """

    if converter is None:
        converter = cell.get_converter_to_specific(mode=mode)
    cc, v = cell._get_cap(
        cycle, "charge", converter=converter, usteps=usteps, **kwargs
    )

    if as_frame:
        cycle_df = externals.pandas.concat([v, cc], axis=1)
        return cycle_df
    else:
        return cc, v

def get_cap(
    cell,
    cycle=None,
    cycles=None,
    method="back-and-forth",
    insert_nan=None,
    shift=0.0,
    categorical_column=False,
    label_cycle_number=False,
    split=False,
    interpolated=False,
    dx=0.1,
    number_of_points=None,
    ignore_errors=True,
    inter_cycle_shift=True,
    interpolate_along_cap=False,
    capacity_then_voltage=False,
    mode="gravimetric",
    mass=None,
    area=None,
    volume=None,
    cycle_mode=None,
    usteps=None,
    dynamic=False,
    **kwargs,
):
    """Gets the capacity for the run.

    Args:
        cycle (int, list): cycle number (s).
        cycles (list): list of cycle numbers.
        method (str): how the curves are given

            - "back-and-forth" - standard back and forth; discharge
              (or charge) reversed from where charge (or discharge) ends.
            - "forth" - discharge (or charge) continues along x-axis.
            - "forth-and-forth" - discharge (or charge) also starts at 0
              (or shift if not shift=0.0)

        insert_nan (bool): insert a externals.numpy.nan between the charge and discharge curves.
            Defaults to True for "forth-and-forth", else False
        shift: start-value for charge (or discharge) (typically used when
            plotting shifted-capacity).
        categorical_column: add a categorical column showing if it is
            charge or discharge.
        label_cycle_number (bool): add column for cycle number
            (tidy format).
        split (bool): return a list of c and v instead of the default
            that is to return them combined in a DataFrame. This is only
            possible for some specific combinations of options (neither
            categorical_column=True or label_cycle_number=True are
            allowed).
        interpolated (bool): set to True if you would like to get
            interpolated data (typically if you want to save disk space
            or memory). Defaults to False.
        dx (float): the step used when interpolating.
        number_of_points (int): number of points to use (over-rides dx)
            for interpolation (i.e. the length of the interpolated data).
        ignore_errors (bool): don't break out of loop if an error occurs.
        inter_cycle_shift (bool): cumulative shifts between consecutive
            cycles. Defaults to True.
        interpolate_along_cap (bool): interpolate along capacity axis instead
            of along the voltage axis. Defaults to False.
        capacity_then_voltage (bool): return capacity and voltage instead of
            voltage and capacity. Defaults to False.
        mode (str): 'gravimetric', 'areal', 'volumetric' or 'absolute'. Defaults
            to 'gravimetric'.
        mass (float): mass of active material (in set cellpy unit, typically mg).
        area (float): area of electrode (in set cellpy units, typically cm2).
        volume (float): volume of electrode (in set cellpy units, typically cm3).
        cycle_mode (str): if 'anode' the first step is assumed to be the discharge,
            else charge (defaults to ``CellpyCell.cycle_mode``).
        dynamic: for dynamic retrieving data from cellpy-file.
            [NOT IMPLEMENTED YET]
        **kwargs: sent to ``get_ccap`` and ``get_dcap``.

    Returns:
        ``pandas.DataFrame`` ((cycle) voltage, capacity, (direction (-1, 1)))
        unless split is explicitly set to True. Then it returns a tuple
        with capacity and voltage.
    """

    # TODO: allow for fixing the interpolation range (so that it is possible
    #   to run the function on several cells and have a common x-axis)

    # if cycle is not given, then this function should
    # iterate through cycles

    def last(df):
        try:
            return df.iat[-1]
        except TypeError:
            return 0.0

    def first(df):
        try:
            return df.iat[0]
        except TypeError:
            return 0.0

    if usteps is None:
        usteps = cell._using_usteps()
        logging.debug(
            f"Since usteps is None, it is set automatically (usteps={usteps})"
        )

    experimental = True

    cycle_mode = cycle_mode or cell.cycle_mode

    available_cycles = cell.get_cycle_numbers()
    if cycles is not None:
        cycle = cycles

    if cycle is None:
        cycle = available_cycles

    if not isinstance(cycle, collections.abc.Iterable):
        cycle = [cycle]

    cycle = list(set(cycle).intersection(set(available_cycles)))

    if split and not (categorical_column or label_cycle_number):
        return_dataframe = False
    else:
        return_dataframe = True

    method = method.lower()
    if method not in ["back-and-forth", "forth", "forth-and-forth"]:
        warnings.warn(
            f"method '{method}' is not a valid option - setting to 'back-and-forth'"
        )
        method = "back-and-forth"

    if insert_nan is None:
        if method == "forth-and-forth":
            insert_nan = True
        else:
            insert_nan = False

    if insert_nan:
        _nan = externals.pandas.DataFrame(
            {"capacity": [externals.numpy.nan], "voltage": [externals.numpy.nan]}
        )

    converter_kwargs = dict()
    if mass is not None:
        logging.info(
            f"mass of {mass} {cell.cellpy_units['mass']} given - using gravimetric mode"
        )
        converter_kwargs["value"] = mass
        mode = "gravimetric"

    if area is not None:
        logging.info(
            f"area of {area} {cell.cellpy_units['area']} given - using areal mode"
        )
        converter_kwargs["value"] = area
        mode = "areal"

    if volume is not None:
        logging.info(
            f"volume of {volume} {cell.cellpy_units['volume']} given - using volumetric mode"
        )
        converter_kwargs["value"] = volume
        mode = "volumetric"

    if mode == "absolute":
        logging.info("absolute mode - no conversion")

    capacity = None
    voltage = None
    specific_converter = cell.get_converter_to_specific(
        mode=mode, **converter_kwargs
    )
    cycle_df = externals.pandas.DataFrame()

    initial = True
    for current_cycle in cycle:
        cc = externals.pandas.DataFrame()
        cv = externals.pandas.DataFrame()
        dc = externals.pandas.DataFrame()
        dv = externals.pandas.DataFrame()
        error = False
        try:
            cc, cv = cell.get_ccap(
                current_cycle,
                converter=specific_converter,
                as_frame=False,
                usteps=usteps,
                **kwargs,
            )

        except NullData as e:
            error = True
            logging.info(e)
            if not ignore_errors:
                logging.debug("breaking out of loop")
                break

        try:
            dc, dv = cell.get_dcap(
                current_cycle,
                converter=specific_converter,
                as_frame=False,
                usteps=usteps,
                **kwargs,
            )

        except NullData as e:
            error = True
            logging.info(e)
            if not ignore_errors:
                logging.debug("breaking out of loop")
                break

        if not error or experimental:
            if cc.empty:
                logging.debug("get_ccap returns empty cc Series")

            if dc.empty:
                logging.debug("get_ccap returns empty dc Series")

            if initial:
                prev_end = shift
                initial = False

            if cycle_mode == "anode":
                first_interpolation_direction = -1
                _first_step_c = dc
                _first_step_v = dv
                last_interpolation_direction = 1
                _last_step_c = cc
                _last_step_v = cv
            else:
                first_interpolation_direction = 1
                _first_step_c = cc
                _first_step_v = cv
                last_interpolation_direction = -1
                _last_step_c = dc
                _last_step_v = dv

            if method == "back-and-forth":
                _last = last(_first_step_c)
                _first = None
                _new_first = None

                if not inter_cycle_shift:
                    prev_end = 0.0

                if _last_step_c is not None:
                    _last_step_c = _last - _last_step_c + prev_end

                else:
                    logging.info("no last charge step found")

                if _first_step_c is not None:
                    _first = first(_first_step_c)
                    _first_step_c += prev_end
                    _new_first = first(_first_step_c)

                else:
                    logging.info("probably empty (_first_step_c is None)")
                prev_end = last(_last_step_c)

            elif method == "forth":
                _last = last(_first_step_c)
                if _last_step_c is not None:
                    _last_step_c += _last + prev_end
                else:
                    logging.debug("no last charge step found")
                if _first_step_c is not None:
                    _first_step_c += prev_end
                else:
                    logging.debug("no first charge step found")

                if inter_cycle_shift:
                    prev_end = last(_last_step_c)
                else:
                    prev_end = 0.0

            elif method == "forth-and-forth":
                if _last_step_c is not None:
                    _last_step_c += shift
                else:
                    logging.debug("no last charge step found")
                if _first_step_c is not None:
                    _first_step_c += shift
                else:
                    logging.debug("no first charge step found")

            if return_dataframe:
                x_col = "voltage"
                y_col = "capacity"
                if interpolate_along_cap:
                    x_col, y_col = y_col, x_col

                try:
                    # processing first
                    if not _first_step_c.empty:
                        _first_df = externals.pandas.DataFrame(
                            {
                                "voltage": _first_step_v,
                                "capacity": _first_step_c,
                            }
                        )
                        if interpolated:
                            _first_df = ds.interpolate_y_on_x_per_monotonic_segments(
                                _first_df,
                                y=y_col,
                                x=x_col,
                                dx=dx,
                                number_of_points=number_of_points,
                                direction=first_interpolation_direction,
                            )
                        if insert_nan:
                            _first_df = externals.pandas.concat([_first_df, _nan])
                        if categorical_column:
                            _first_df["direction"] = -1
                    else:
                        _first_df = externals.pandas.DataFrame()

                    # processing last
                    if not _last_step_c.empty:
                        _last_df = externals.pandas.DataFrame(
                            {
                                "voltage": _last_step_v.values,
                                "capacity": _last_step_c.values,
                            }
                        )
                        if interpolated:
                            _last_df = ds.interpolate_y_on_x_per_monotonic_segments(
                                _last_df,
                                y=y_col,
                                x=x_col,
                                dx=dx,
                                number_of_points=number_of_points,
                                direction=last_interpolation_direction,
                            )
                        if insert_nan:
                            _last_df = externals.pandas.concat([_last_df, _nan])
                        if categorical_column:
                            _last_df["direction"] = 1
                    else:
                        _last_df = externals.pandas.DataFrame()

                    if interpolate_along_cap:
                        if method == "forth":
                            _first_df = _first_df.loc[::-1].reset_index(drop=True)
                        elif method == "back-and-forth":
                            _first_df = _first_df.loc[::-1].reset_index(drop=True)
                            _last_df = _last_df.loc[::-1].reset_index(drop=True)

                except AttributeError:
                    logging.info(f"Could not extract cycle {current_cycle}")
                else:
                    c = externals.pandas.concat([_first_df, _last_df], axis=0)
                    if label_cycle_number:
                        c.insert(0, "cycle", current_cycle)
                        # c["cycle"] = current_cycle
                        # c = c[["cycle", "voltage", "capacity", "direction"]]
                    if cycle_df.empty:
                        cycle_df = c
                    else:
                        cycle_df = externals.pandas.concat([cycle_df, c], axis=0)
                if capacity_then_voltage:
                    cols = cycle_df.columns.to_list()
                    new_cols = [
                        cols.pop(cols.index("capacity")),
                        cols.pop(cols.index("voltage")),
                    ]
                    new_cols.extend(cols)
                    cycle_df = cycle_df[new_cols]
            else:
                logging.warning("returning non-dataframe")
                _non_empty_c = []
                _non_empty_v = []
                if not _first_step_c.empty:
                    _non_empty_c.append(_first_step_c)
                    _non_empty_v.append(_first_step_v)
                if not _last_step_c.empty:
                    _non_empty_c.append(_last_step_c)
                    _non_empty_v.append(_last_step_v)

                c = externals.pandas.concat(_non_empty_c, axis=0)
                v = externals.pandas.concat(_non_empty_v, axis=0)

                if not c.empty:
                    capacity = externals.pandas.concat([capacity, c], axis=0)
                    voltage = externals.pandas.concat([voltage, v], axis=0)

    if return_dataframe:
        return cycle_df
    else:
        return capacity, voltage

def _get_cap(
    cell,
    cycle=None,
    cap_type="charge",
    trim_taper_steps=None,
    steps_to_skip=None,
    steptable=None,
    converter=None,
    usteps=False,
    detailed=False,
):
    # TODO: @jepe - does not allow for constant voltage yet?
    # TODO: @jepe - refactor this (can be done without making the individual lists first)

    data_points = None
    test_time = None

    if cap_type.lower() == "charge_capacity":
        cap_type = "charge"
    elif cap_type.lower() == "discharge_capacity":
        cap_type = "discharge"

    cycles = cell.get_step_numbers(
        steptype=cap_type,
        allctypes=False,
        cycle_number=cycle,
        trim_taper_steps=trim_taper_steps,
        steps_to_skip=steps_to_skip,
        steptable=steptable,
        usteps=usteps,
    )
    if cap_type == "charge":
        column_txt = cell.headers_normal.charge_capacity_txt
    else:
        column_txt = cell.headers_normal.discharge_capacity_txt

    if cycle:
        steps = cycles[cycle]
        _v = []
        _c = []
        _t = []
        _p = []

        if len(set(steps)) < len(steps) and not usteps:
            raise ValueError(f"You have duplicate step numbers!")

        if usteps:
            selected = cell._select_usteps(cycle, steps)
            if not cell._is_empty_array(selected):
                _v.append(selected[cell.headers_normal.voltage_txt])
                _c.append(selected[column_txt] * converter)
                if detailed:
                    _t.append(selected[cell.headers_normal.test_time_txt])
                    _p.append(selected[cell.headers_normal.data_point_txt])
            else:
                logging.debug(f"Steps {steps} is empty")
        else:
            for step in sorted(steps):
                selected_step = cell._select_step(cycle, step)
                if not cell._is_empty_array(selected_step):
                    _v.append(selected_step[cell.headers_normal.voltage_txt])
                    _c.append(selected_step[column_txt] * converter)
                    if detailed:
                        _t.append(selected_step[cell.headers_normal.test_time_txt])
                        _p.append(selected_step[cell.headers_normal.data_point_txt])
                else:
                    logging.debug(f"Step {step} is empty")
        try:
            voltage = externals.pandas.concat(_v, axis=0)
            cap = externals.pandas.concat(_c, axis=0)
            if detailed:
                test_time = externals.pandas.concat(_t, axis=0)
                data_points = externals.pandas.concat(_p, axis=0)
        except Exception:
            logging.debug("could not find any steps for this cycle")
            raise NullData(f"no steps found (c:{cycle} s:{steps} type:{cap_type})")
    else:
        # get all the discharge cycles
        # this is a dataframe filtered on step and cycle
        # This functionality is not crucial since get_cap (that uses this method) has it
        # (but it might be nice to improve performance)
        raise NotImplementedError(
            "Not yet possible to extract without giving cycle numbers (use get_cap instead)"
        )
    if detailed:
        return data_points, test_time, cap, voltage
    return cap, voltage

def get_ocv(
    cell,
    cycles=None,
    direction="up",
    remove_first=False,
    interpolated=False,
    dx=None,
    number_of_points=None,
) -> "externals.pandas.DataFrame":
    """Get the open circuit voltage relaxation curves.

    Args:
        cycles (list of ints or None): the cycles to extract from
            (selects all if not given).
        direction ("up", "down", or "both"): extract only relaxations that
            is performed during discharge for "up" (because then the
            voltage relaxes upwards) etc.
        remove_first: remove the first relaxation curve (typically,
            the first curve is from the initial rest period between
            assembling the data to the actual testing/cycling starts)
        interpolated (bool): set to True if you want the data to be
            interpolated (e.g. for creating smaller files)
        dx (float): the step used when interpolating.
        number_of_points (int): number of points to use (over-rides dx)
            for interpolation (i.e. the length of the interpolated data).

    Returns:
        ``pandas.DataFrame`` with cycle-number, step-number, step-time, and voltage columns.

    """
    # TODO: use proper column header pickers
    if cycles is None:
        cycles = cell.get_cycle_numbers()
    else:
        if not isinstance(cycles, (list, tuple, externals.numpy.ndarray)):
            cycles = [cycles]
        else:
            remove_first = False

    ocv_rlx_id = "ocvrlx"
    if direction == "up":
        ocv_rlx_id += "_up"
    elif direction == "down":
        ocv_rlx_id += "_down"

    steps = cell.data.steps
    raw = cell.data.raw

    ocv_steps = steps.loc[steps["cycle"].isin(cycles), :]

    ocv_steps = ocv_steps.loc[
        ocv_steps.type.str.startswith(ocv_rlx_id, na=False), :
    ]

    if remove_first:
        ocv_steps = ocv_steps.iloc[1:, :]

    step_time_label = cell.headers_normal.step_time_txt
    voltage_label = cell.headers_normal.voltage_txt
    cycle_label = cell.headers_normal.cycle_index_txt
    step_label = cell.headers_normal.step_index_txt

    selected_df = raw.loc[
        (
            raw[cycle_label].isin(ocv_steps.cycle)
            & raw[step_label].isin(ocv_steps.step)
        ),
        [cycle_label, step_label, step_time_label, voltage_label],
    ]

    if interpolated:
        if dx is None and number_of_points is None:
            dx = config.reader.time_interpolation_step
        new_dfs = list()
        groupby_list = [cycle_label, step_label]

        for name, group in selected_df.groupby(groupby_list):
            new_group = ds.interpolate_y_on_x(
                group,
                x=step_time_label,
                y=voltage_label,
                dx=dx,
                number_of_points=number_of_points,
            )

            for i, j in zip(groupby_list, name):
                new_group[i] = j
            new_dfs.append(new_group)

        selected_df = externals.pandas.concat(new_dfs)

    return selected_df

