import collections
import functools
from typing import Any, Callable, Iterable, List, Optional, Union, TypeVar
import logging

from cellpy.readers import core
from cellpy.parameters.internal_settings import (
    HeadersNormal,
    HeadersStepTable,
    HeadersSummary,
)

DataFrame = TypeVar("DataFrame")

logger = logging.getLogger(__name__)

FIRST = "_first"
LAST = "_last"
DELTA = "_diff"

headers_step_table = HeadersStepTable()
headers_summary = HeadersSummary()
headers_normal = HeadersNormal()

# TODO: move this to a settings file
STEP_TYPES = [
    "charge",
    "discharge",
    "cv_charge",
    "cv_discharge",
    "taper_charge",
    "taper_discharge",
    "charge_cv",
    "discharge_cv",
    "ocvrlx_up",
    "ocvrlx_down",
    "ir",
    "rest",
    "not_known",
]


def create_selector(
    data: core.Data,
    selector_type: Optional[str] = None,
    exclude_types: Optional[List[str]] = None,
    exclude_steps: Optional[List[str]] = None,
    final_data_points: Optional[Iterable[int]] = None,
) -> Callable:
    """Create a simple summary selector function.

    Args:
        data: The data to create the selector from.
        selector_type: The type of selector to create.
        exclude_types: The types to exclude from the selector.
        exclude_steps: The steps to exclude from the selector.
        final_data_points: The final data point for each cycle to use for the selector.

    Returns:
        A selector function for the summary dataframe.
    """

    if selector_type == "non-cv":
        exclude_types = ["cv_"]
    elif selector_type == "non-rest":
        exclude_types = ["rest_"]
    elif selector_type == "non-ocv":
        exclude_types = ["ocv_"]
    elif selector_type == "only-cv":
        exclude_types = ["charge", "discharge"]
    selector = functools.partial(
        summary_selector_exluder,
        data=data,
        custom_headers_normal=headers_normal,
        custom_headers_step_table=headers_step_table,
        exclude_types=exclude_types,
        exclude_steps=exclude_steps,
        final_data_points=final_data_points,
    )
    return selector


def summary_selector_exluder(
    data: core.Data,
    custom_headers_normal: Optional[HeadersNormal] = None,
    custom_headers_step_table: Optional[HeadersStepTable] = None,
    exclude_types: Optional[Iterable[str]] = None,
    exclude_steps: Optional[Iterable[str]] = None,
    replace_nan: bool = True,
    final_data_points: Optional[Iterable[int]] = None,
) -> Callable:
    """Create a summary selector.

    This function creates a summary selector that can be used to select a subset of the raw data
    to base the summary on.

    Args:
        data: The data to create the summary selector from.
        custom_headers_normal: The custom headers to use for the summary selector.
        custom_headers_step_table: The custom headers to use for the summary selector.
        exclude_types: The types to exclude from the summary selector.
        exclude_steps: The steps to exclude from the summary selector.
        replace_nan: Whether to replace NaN values with 0.0.
        final_data_points: The final data point for each cycle to use for the summary selector.
    """
    steps = data.steps
    raw = data.raw.copy()

    if custom_headers_normal is None:
        custom_headers_normal = headers_normal
    if custom_headers_step_table is None:
        custom_headers_step_table = headers_step_table

    # unravel the headers:
    d_n_txt = custom_headers_normal.data_point_txt
    v_n_txt = custom_headers_normal.voltage_txt
    c_n_txt = custom_headers_normal.cycle_index_txt
    # s_n_txt = headers_normal.step_index_txt
    i_n_txt = custom_headers_normal.current_txt
    ch_n_txt = custom_headers_normal.charge_capacity_txt
    dch_n_txt = custom_headers_normal.discharge_capacity_txt

    d_st_txt = custom_headers_step_table.point
    v_st_txt = custom_headers_step_table.voltage
    c_st_txt = custom_headers_step_table.cycle
    i_st_txt = custom_headers_step_table.current
    ch_st_txt = custom_headers_step_table.charge
    dch_st_txt = custom_headers_step_table.discharge
    t_st_txt = custom_headers_step_table.type
    # s_st_txt = headers_step_table.step

    _first = FIRST
    _last = LAST
    _delta_label = DELTA

    # TODO: implement also for energy and power (and probably others as well) - this will
    #  require changing step-table to also include energy and power etc. If implementing
    #  this, you should also include diff in the step-table. You should preferably also use this
    #  opportunity to also make both the headers in the tables as well as the names used for
    #  the headers more aligned (e.g. for header_normal.data_point_txt -> header_normal.point;
    #  "cycle_index" -> "cycle")

    # TODO: @jepe - this method might be a bit slow for large datasets - consider using
    #  more "native" pandas methods and get rid of all looping (need some timing to check first)

    if final_data_points is None:
        final_data_points = (
            steps.loc[:, [c_st_txt, d_st_txt + _last]]
            .groupby(c_st_txt)
            .last()
            .values.ravel()
        )
    last_items = raw[d_n_txt].isin(final_data_points)
    selected = raw[last_items]

    if exclude_types is None and exclude_steps is None:
        return selected

    if not isinstance(exclude_types, (list, tuple)):
        exclude_types = [exclude_types]

    if not isinstance(exclude_steps, (list, tuple)):
        exclude_steps = [exclude_steps]

    q = None
    for exclude_type in exclude_types:
        _q = ~steps[t_st_txt].str.startswith(exclude_type)
        q = _q if q is None else q & _q

    if exclude_steps:
        _q = ~steps[t_st_txt].isin(exclude_steps)
        q = _q if q is None else q & _q

    _delta_columns = [
        i_st_txt,
        v_st_txt,
        ch_st_txt,
        dch_st_txt,
    ]
    _raw_columns = [
        i_n_txt,
        v_n_txt,
        ch_n_txt,
        dch_n_txt,
    ]
    _diff_columns = [f"{col}{_delta_label}" for col in _delta_columns]

    delta_first = [f"{col}{_first}" for col in _delta_columns]
    delta_last = [f"{col}{_last}" for col in _delta_columns]
    delta_columns = delta_first + delta_last

    delta = steps.loc[~q, [c_st_txt, d_st_txt + _last, *delta_columns]].copy()

    for col in _delta_columns:
        delta[col + _delta_label] = delta[col + _last] - delta[col + _first]
    delta = delta.drop(columns=delta_columns)
    delta = delta.groupby(c_st_txt).sum()
    delta = delta.reset_index()

    selected = selected.merge(delta, how="left", left_on=c_n_txt, right_on=c_st_txt)
    if replace_nan:
        selected = selected.fillna(0.0)

    for col_n, col_diff in zip(_raw_columns, _diff_columns):
        selected[col_n] -= selected[col_diff]
    selected = selected.drop(columns=_diff_columns)

    return selected


def get_step_numbers(
    data: core.Data,
    steptype: str = "charge",
    allctypes: bool = True,
    pdtype: bool = False,
    cycle_number: Optional[int] = None,
    trim_taper_steps: Optional[int] = None,
    steps_to_skip: Optional[list] = None,
    steptable: Optional[Any] = None,
    usteps: bool = False,
) -> Union[dict, DataFrame]:
    # TODO: @jepe - include sub_steps here
    # TODO: @jepe - include option for not selecting taper steps here
    # TODO: @jepe - refactor this method!
    """Get the step numbers of selected type.

    Returns the selected step_numbers for the selected type of step(s).
    Either in a dictionary containing a list of step numbers corresponding
    to the selected steptype for the cycle(s), or a ``pandas.DataFrame`` instead of
    a dict of lists if pdtype is set to True. The frame is a sub-set of the
    step-table frame (i.e. all the same columns, only filtered by rows).

    Args:
        steptype (string): string identifying type of step.
        allctypes (bool): get all types of charge (or discharge).
        pdtype (bool): return results as pandas.DataFrame
        cycle_number (int): selected cycle, selects all if not set.
        trim_taper_steps (int): number of taper steps to skip (counted
            from the end, i.e. 1 means skip last step in each cycle).
        steps_to_skip (list): step numbers that should not be included.
        steptable (pandas.DataFrame): optional steptable

    Returns:
        dict or ``pandas.DataFrame``

    Example:
        >>> my_charge_steps = CellpyCell.get_step_numbers(
        >>>    "charge",
        >>>    cycle_number = 3
        >>> )
        >>> print my_charge_steps
        {3: [5,8]}

    """
    if trim_taper_steps is not None and usteps:
        logger.warning(
            "Trimming taper steps is not possible when using usteps. Not doing any trimming."
        )
        trim_taper_steps = None

    if steps_to_skip is None:
        steps_to_skip = []

    if steptable is None:
        if not data.has_steps:
            logger.debug("step-table is not made")
            logger.info(
                "ERROR! Cannot use get_step_numbers: you must create your step-table first"
            )
            raise ValueError(
                "Cannot use get_step_numbers: you must create your step-table first"
            )

    # check if steptype is valid
    steptype = steptype.lower()
    steptypes = []
    helper_step_types = ["ocv", "charge_discharge"]
    valid_step_type = True
    if steptype in STEP_TYPES:
        steptypes.append(steptype)
    else:
        if steptype in helper_step_types:
            if steptype == "ocv":
                steptypes.append("ocvrlx_up")
                steptypes.append("ocvrlx_down")
            elif steptype == "charge_discharge":
                steptypes.append("charge")
                steptypes.append("discharge")
        else:
            valid_step_type = False
    if not valid_step_type:
        return None

    # in case of selection `allctypes`, then modify charge, discharge
    if allctypes:
        add_these = []
        for st in steptypes:
            if st in ["charge", "discharge"]:
                st1 = st + "_cv"
                add_these.append(st1)
                st1 = "cv_" + st
                add_these.append(st1)
        for st in add_these:
            steptypes.append(st)

    if steptable is None:
        st = data.steps
    else:
        st = steptable
    shdr = headers_step_table

    # Retrieving cycle numbers (if cycle_number is None, it selects all cycles)
    if cycle_number is None:
        cycle_numbers = get_cycle_numbers(data, steptable=steptable)
    else:
        if isinstance(cycle_number, collections.abc.Iterable):
            cycle_numbers = cycle_number
        else:
            cycle_numbers = [cycle_number]

    if trim_taper_steps is not None:
        trim_taper_steps = -trim_taper_steps
        logger.debug("taper steps to trim given")

    if pdtype:
        if trim_taper_steps:
            logger.info(
                "Trimming taper steps is currently not"
                "possible when returning externals.pandas.DataFrame. "
                "Do it manually instead."
            )
        out = st[st[shdr.type].isin(steptypes) & st[shdr.cycle].isin(cycle_numbers)]
        return out

    out = dict()
    step_hdr = shdr.ustep if usteps else shdr.step
    for cycle in cycle_numbers:
        steplist = []
        for s in steptypes:
            mask_type_and_cycle = (st[shdr.type] == s) & (st[shdr.cycle] == cycle)
            if not any(mask_type_and_cycle):
                logger.debug(f"Cycle {cycle} | StepType {s}: Not present!")
            else:
                # Get the step numbers
                step = st[mask_type_and_cycle][step_hdr].tolist()
                for newstep in step[:trim_taper_steps]:
                    if newstep in steps_to_skip:
                        logger.debug(f"skipping step {newstep}")
                    else:
                        steplist.append(int(newstep))

        if not steplist:
            steplist = [0]
        out[cycle] = steplist
    return out


def get_cycle_numbers(
    data: core.Data,
    steptable=None,
    rate=None,
    rate_on=None,
    rate_std=None,
    rate_agg="first",
    inverse=False,
):
    """Get a array containing the cycle numbers in the test.

    Parameters:
        steptable (pandas.DataFrame): the step-table to use (if None, the step-table
            from the cellpydata object will be used).
        rate (float): the rate to filter on. Remark that it should be given
            as a float, i.e. you will have to convert from C-rate to
            the actual numeric value. For example, use rate=0.05 if you want
            to filter on cycles that has a C/20 rate.
        rate_on (str): only select cycles if based on the rate of this step-type (e.g. on="discharge").
        rate_std (float): allow for this inaccuracy in C-rate when selecting cycles
        rate_agg (str): perform an aggregation on rate if more than one step of charge or discharge is found
            (e.g. "mean", "first", "max"). For example, if agg='mean', the average rate for each cycle
            will be returned. Set to None if you want to keep all the rates.
        inverse (bool): select steps that does not have the given C-rate.

    Returns:
        numpy.ndarray of cycle numbers.
    """

    # TODO: add support for selecting cycles based on other criteria (for example, based on the
    #   existence of particular step-types, or max, min values of current, voltage, etc)

    logger.debug("getting cycle numbers")

    if steptable is None:
        d = data.raw
        cycles = d[headers_normal.cycle_index_txt].dropna().unique()
        steptable = data.steps
    else:
        logger.debug("steptable is given as input parameter")
        cycles = steptable[headers_step_table.cycle].dropna().unique()

    if rate is None:
        return cycles

    logger.debug("filtering on rate")

    if rate is None:
        rate = 0.05

    if rate_std is None:
        rate_std = 0.1 * rate

    if rate_on is None:
        rate_on = ["charge", "discharge"]
    rates = get_rates(data, steptable=steptable, agg=rate_agg, direction=rate_on)
    rate_column = headers_step_table.rate_avr
    cycles_mask = (rates[rate_column] < (rate + rate_std)) & (
        rates[rate_column] > (rate - rate_std)
    )

    if inverse:
        cycles_mask = ~cycles_mask

    filtered_rates = rates[cycles_mask]
    filtered_cycles = filtered_rates[headers_step_table["cycle"]].unique()

    return filtered_cycles


def get_rates(
    data: core.Data,
    steptable: Optional[Any] = None,
    agg: str = "first",
    direction: Optional[str] = None,
) -> DataFrame:
    """
    Get the rates in the test (only valid for constant current).

    Args:
        steptable: provide custom steptable (if None, the steptable from the cellpydata object will be used).
        agg (str): perform an aggregation if more than one step of charge or
            discharge is found (e.g. "mean", "first", "max"). For example, if agg='mean', the average rate
            for each cycle will be returned. Set to None if you want to keep all the rates.
        direction (str or list of str): only select rates for this direction (e.g. "charge" or "discharge").

    Returns:
        ``pandas.DataFrame`` with cycle, type, and rate_avr (i.e. C-rate) columns.
    """

    if steptable is None:
        steptable = data.steps
    rates = steptable[
        [
            headers_step_table.cycle,
            headers_step_table.type,
            headers_step_table.rate_avr,
        ]
    ].dropna()

    if agg:
        rates = (
            rates.groupby([headers_step_table.cycle, headers_step_table.type])
            .agg(agg)
            .reset_index()
        )

    if direction is not None:
        if not isinstance(direction, (list, tuple)):
            direction = [direction]
        rates = rates.loc[rates[headers_step_table.type].isin(direction), :]

    return rates
