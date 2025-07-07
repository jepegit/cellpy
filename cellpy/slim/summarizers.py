import logging
from typing import Sequence, TypeVar, Union

# old cellpy modules that are still not ported to slim:
from cellpy.readers import core
from cellpy.parameters.internal_settings import (
    get_cellpy_units,
    get_default_output_units,
    HeadersNormal,
    HeadersStepTable,
    HeadersSummary,
)

from cellpy.slim import selectors, units

logger = logging.getLogger(__name__)


DataFrame = TypeVar("DataFrame")
Array = TypeVar("Array")


headers_steps = HeadersStepTable()
headers_summary = HeadersSummary()
headers_raw = HeadersNormal()

cellpy_units = get_cellpy_units()
output_units = get_default_output_units()


# TODO: This must be implemented properly when we have a decided a way to get the raw limits from the instrument
DEFAULT_RAW_LIMITS = {
    "current_hard": 0.001,
    "current_soft": 0.001,
    "stable_current_hard": 0.001,
    "stable_current_soft": 0.001,
    "stable_voltage_hard": 0.001,
    "stable_voltage_soft": 0.001,
    "stable_charge_hard": 0.001,
    "stable_charge_soft": 0.001,
    "ir_change": 0.001,
}

DIGITS_C_RATE = 3
DIGITS_RATE = 12


def _ustep(n: Array) -> list:
    # not tested
    """Create u-steps from a pandas Series.

    Args:
        n (Array): The input series.

    Returns:
        list: The u-steps.
    """
    un = []
    c = 0
    dn = n.diff()
    for i in dn:
        if i != 0:
            c += 1
        un.append(c)
    return un


# TODO: [NEXT] - use this in cell_core / cellreader.CellpyCell make_step_table
def make_step_table(
    data: core.Data,
    step_specifications=None,
    short=False,
    override_step_types=None,
    override_raw_limits=None,
    usteps=False,
    skip_steps=None,
    sort_rows=True,
    from_data_point=None,
    raw_limits: dict = DEFAULT_RAW_LIMITS,
) -> Union[core.Data, DataFrame]:
    """Create a table (v.5) that contains summary information for each step.

    This function creates a table containing information about the
    different steps for each cycle and, based on that, decides what type of
    step it is (e.g. charge) for each cycle.

    The format of the steps is:

    - index: cycleno - stepno - sub-step-no - ustep
    - Time info: average, stdev, max, min, start, end, delta
    - Logging info: average, stdev, max, min, start, end, delta
    - Current info: average, stdev, max, min, start, end, delta
    - Voltage info: average,  stdev, max, min, start, end, delta
    - Type: (from pre-defined list) - SubType
    - Info: not used.

    Args:
        data (core.Data): The data object.
        step_specifications (pandas.DataFrame): step specifications
        short (bool): step specifications in short format
        override_step_types (dict): override the provided step types, for example set all
            steps with step number 5 to "charge" by providing {5: "charge"}.
        override_raw_limits (dict): override the instrument limits (resolution), for example set
            'current_hard' to 0.1 by providing {'current_hard': 0.1}.
        usteps (bool): investigate all steps including same steps within
            one cycle (this is useful for e.g. GITT).
        skip_steps (list of integers): list of step numbers that should not
            be processed (future feature - not used yet).
        sort_rows (bool): sort the rows after processing.
        from_data_point (int): first data point to use.
        raw_limits (dict): the raw limits (resolution) for the instrument.

    Returns:
        core.Data: The data object with the step table added if from_data_point is None,
          otherwise the step table is returned as a DataFrame.

    """

    # def first(x):
    #     return x.iloc[0]

    # def last(x):
    #     return x.iloc[-1]

    def delta(x):
        # Remark! this will not work if x is a TimeDelta object
        if x.iloc[0] == 0.0:
            # starts from a zero value
            difference = 100.0 * x.iloc[-1]
        else:
            difference_factor = 100.0 * (x.iloc[-1] - x.iloc[0])
            difference_dividend = abs(x.iloc[0])
            difference = difference_factor / difference_dividend

        return difference

    if from_data_point is not None:
        df = data.raw.loc[data.raw[headers_raw.data_point_txt] >= from_data_point]
    else:
        df = data.raw
    # df[headers_steps.internal_resistance_change] = \
    #     df[headers_raw.internal_resistance_txt].pct_change()

    # selecting only the most important columns from raw:
    keep = [
        headers_raw.data_point_txt,
        headers_raw.test_time_txt,
        headers_raw.step_time_txt,
        headers_raw.step_index_txt,
        headers_raw.cycle_index_txt,
        headers_raw.current_txt,
        headers_raw.voltage_txt,
        headers_raw.ref_voltage_txt,
        headers_raw.charge_capacity_txt,
        headers_raw.discharge_capacity_txt,
        headers_raw.internal_resistance_txt,
        # "ir_pct_change"
    ]

    # only use col-names that exist:
    keep = [col for col in keep if col in df.columns]
    df = df[keep]
    # preparing for implementation of sub_steps (will come in the future):
    df = df.assign(**{f"{headers_raw.sub_step_index_txt}": 1})

    # using headers as defined in the internal_settings.py file
    rename_dict = {
        headers_raw.cycle_index_txt: headers_steps.cycle,
        headers_raw.step_index_txt: headers_steps.step,
        headers_raw.sub_step_index_txt: headers_steps.sub_step,
        headers_raw.data_point_txt: headers_steps.point,
        headers_raw.test_time_txt: headers_steps.test_time,
        headers_raw.step_time_txt: headers_steps.step_time,
        headers_raw.current_txt: headers_steps.current,
        headers_raw.voltage_txt: headers_steps.voltage,
        headers_raw.charge_capacity_txt: headers_steps.charge,
        headers_raw.discharge_capacity_txt: headers_steps.discharge,
        headers_raw.internal_resistance_txt: headers_steps.internal_resistance,
    }

    df = df.rename(columns=rename_dict)
    by = [headers_steps.cycle, headers_steps.step, headers_steps.sub_step]

    if skip_steps is not None:
        logging.debug(f"omitting steps {skip_steps}")
        df = df.loc[~df[headers_steps.step].isin(skip_steps)]

    if usteps:
        by.append(headers_steps.ustep)
        df[headers_steps.ustep] = _ustep(df[headers_steps.step])

    logging.debug(f"groupby: {by}")

    # TODO: make sure that all columns are numeric

    gf = df.groupby(by=by)

    # TODO: FutureWarning: The provided callable <function mean at 0x000002BD4D332840>
    #  is currently using SeriesGroupBy.mean. In a future version of pandas, the provided
    #  callable will be used directly. To keep current behavior pass the string "mean" instead.
    df_steps = gf.agg(["mean", "std", "min", "max", "first", "last", delta]).rename(
        columns={"amin": "min", "amax": "max", "mean": "avr"}
    )

    df_steps = df_steps.reset_index()

    df_steps[headers_steps.rate_avr] = abs(
        round(
            df_steps.loc[:, (headers_steps.current, "avr")],
            DIGITS_RATE,
        )
    )

    df_steps[headers_steps.type] = ""
    df_steps[headers_steps.sub_type] = ""
    df_steps[headers_steps.info] = ""

    if step_specifications is None:
        # TODO: refactor this:
        if override_raw_limits is None:
            override_raw_limits = {}
        current_limit_value_hard = (
            override_raw_limits.get("current_hard", None) or raw_limits["current_hard"]
        )
        # current_limit_value_soft = (
        #     override_raw_limits.get("current_soft", None) or raw_limits["current_soft"]
        # )
        # stable_current_limit_hard = (
        #     override_raw_limits.get("stable_current_hard", None)
        #     or raw_limits["stable_current_hard"]
        # )
        stable_current_limit_soft = (
            override_raw_limits.get("stable_current_soft", None)
            or raw_limits["stable_current_soft"]
        )
        stable_voltage_limit_hard = (
            override_raw_limits.get("stable_voltage_hard", None)
            or raw_limits["stable_voltage_hard"]
        )
        # stable_voltage_limit_soft = (
        #     override_raw_limits.get("stable_voltage_soft", None)
        #     or raw_limits["stable_voltage_soft"]
        # )
        stable_charge_limit_hard = (
            override_raw_limits.get("stable_charge_hard", None)
            or raw_limits["stable_charge_hard"]
        )
        # stable_charge_limit_soft = (
        #     override_raw_limits.get("stable_charge_soft", None)
        #     or raw_limits["stable_charge_soft"]
        # )
        # ir_change_limit = (
        #     override_raw_limits.get("ir_change", None) or raw_limits["ir_change"]
        # )

        mask_no_current_hard = (
            df_steps.loc[:, (headers_steps.current, "max")].abs()
            + df_steps.loc[:, (headers_steps.current, "min")].abs()
        ) < current_limit_value_hard / 2

        mask_voltage_down = (
            df_steps.loc[:, (headers_steps.voltage, "delta")]
            < -stable_voltage_limit_hard
        )

        mask_voltage_up = (
            df_steps.loc[:, (headers_steps.voltage, "delta")]
            > stable_voltage_limit_hard
        )

        mask_voltage_stable = (
            df_steps.loc[:, (headers_steps.voltage, "delta")].abs()
            < stable_voltage_limit_hard
        )

        mask_current_down = (
            df_steps.loc[:, (headers_steps.current, "delta")]
            < -stable_current_limit_soft
        )

        # mask_current_up = (
        #     df_steps.loc[:, (headers_steps.current, "delta")]
        #     > stable_current_limit_soft
        # )

        mask_current_negative = (
            df_steps.loc[:, (headers_steps.current, "avr")] < -current_limit_value_hard
        )

        mask_current_positive = (
            df_steps.loc[:, (headers_steps.current, "avr")] > current_limit_value_hard
        )

        # mask_galvanostatic = (
        #     df_steps.loc[:, (headers_steps.current, "delta")].abs()
        #     < stable_current_limit_soft
        # )

        mask_charge_changed = (
            df_steps.loc[:, (headers_steps.charge, "delta")].abs()
            > stable_charge_limit_hard
        )

        mask_discharge_changed = (
            df_steps.loc[:, (headers_steps.discharge, "delta")].abs()
            > stable_charge_limit_hard
        )

        mask_no_change = (
            (df_steps.loc[:, (headers_steps.voltage, "delta")] == 0)
            & (df_steps.loc[:, (headers_steps.current, "delta")] == 0)
            & (df_steps.loc[:, (headers_steps.charge, "delta")] == 0)
            & (df_steps.loc[:, (headers_steps.discharge, "delta")] == 0)
        )

        # TODO: make an option for only checking unique steps
        #     e.g.
        #     df_x = df_steps.where.steps.are.unique

        # TODO: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise in a future error
        #  of pandas. Value 'rest' has dtype incompatible with float64, please explicitly cast to a
        #  compatible dtype first.

        df_steps.loc[
            mask_no_current_hard & mask_voltage_stable,
            (headers_steps.type, slice(None)),
        ] = "rest"

        df_steps.loc[
            mask_no_current_hard & mask_voltage_up, (headers_steps.type, slice(None))
        ] = "ocvrlx_up"

        df_steps.loc[
            mask_no_current_hard & mask_voltage_down, (headers_steps.type, slice(None))
        ] = "ocvrlx_down"

        df_steps.loc[
            mask_discharge_changed & mask_current_negative,
            (headers_steps.type, slice(None)),
        ] = "discharge"

        df_steps.loc[
            mask_charge_changed & mask_current_positive,
            (headers_steps.type, slice(None)),
        ] = "charge"

        df_steps.loc[
            mask_voltage_stable & mask_current_negative & mask_current_down,
            (headers_steps.type, slice(None)),
        ] = "cv_discharge"

        df_steps.loc[
            mask_voltage_stable & mask_current_positive & mask_current_down,
            (headers_steps.type, slice(None)),
        ] = "cv_charge"

        # --- internal resistance ----
        df_steps.loc[mask_no_change, (headers_steps.type, slice(None))] = "ir"
        # assumes that IR is stored in just one row

        # --- sub-step-txt -----------
        df_steps[headers_steps.sub_type] = None

        # --- CV steps ----

        # "voltametry_charge"
        # mask_charge_changed
        # mask_voltage_up
        # (could also include abs-delta-cumsum current)

        # "voltametry_discharge"
        # mask_discharge_changed
        # mask_voltage_down

        if override_step_types is not None:
            for step, step_type in override_step_types.items():
                df_steps.loc[
                    df_steps[headers_steps.step] == step,
                    (headers_steps.type, slice(None)),
                ] = step_type

    else:
        # not tested!
        logger.debug("parsing custom step definition")
        if not short:
            logger.debug("using long format (cycle,step)")
            for row in step_specifications.itertuples():
                df_steps.loc[
                    (df_steps[headers_steps.step] == row.step)
                    & (df_steps[headers_steps.cycle] == row.cycle),
                    (headers_steps.type, slice(None)),
                ] = row.type
                df_steps.loc[
                    (df_steps[headers_steps.step] == row.step)
                    & (df_steps[headers_steps.cycle] == row.cycle),
                    (headers_steps.info, slice(None)),
                ] = row.info
        else:
            logger.debug("using short format (step)")
            for row in step_specifications.itertuples():
                df_steps.loc[
                    df_steps[headers_steps.step] == row.step,
                    (headers_steps.type, slice(None)),
                ] = row.type
                df_steps.loc[
                    df_steps[headers_steps.step] == row.step,
                    (headers_steps.info, slice(None)),
                ] = row.info

    # check if all the steps got categorizes
    logger.debug("looking for un-categorized steps")
    empty_rows = df_steps.loc[df_steps[headers_steps.type].isnull()]
    if not empty_rows.empty:
        logger.warning(
            f"found {len(empty_rows)}:{len(df_steps)} non-categorized steps (please, check your raw-limits)"
        )
        # logging.debug(empty_rows)

    # flatten (possible remove in the future),

    logger.debug("flatten columns")
    flat_cols = []
    for col in df_steps.columns:
        if isinstance(col, tuple):
            if col[-1]:
                col = "_".join(col)
            else:
                col = col[0]
        flat_cols.append(col)

    df_steps.columns = flat_cols
    if sort_rows:
        logger.debug("sorting the step rows")
        # TODO: [#index]
        # if this throws a KeyError: 'test_time_first' it probably
        # means that the df contains a non-nummeric 'test_time' column.
        df_steps = df_steps.sort_values(
            by=headers_steps.test_time + "_first"
        ).reset_index()

    if from_data_point is not None:
        return df_steps
    else:
        data.steps = df_steps
        return data


def generate_absolute_summary_columns(
    data: core.Data,
    _first_step_txt: str = headers_raw.charge_capacity_txt,
    _second_step_txt: str = headers_raw.discharge_capacity_txt,
) -> core.Data:
    """Generate absolute summary columns.

    Args:
        data (core.Data): The data object.
        _first_step_txt (str): The first step text.
        _second_step_txt (str): The second step text.
    """

    summary = data.summary

    # Coulombic efficiency
    summary[headers_summary.coulombic_efficiency] = (
        100 * summary[_second_step_txt] / summary[_first_step_txt]
    )
    summary[headers_summary.cumulated_coulombic_efficiency] = summary[
        headers_summary.coulombic_efficiency
    ].cumsum()

    # Capacity columns
    capacity_columns = {
        headers_summary.charge_capacity: summary[headers_raw.charge_capacity_txt],
        headers_summary.discharge_capacity: summary[headers_raw.discharge_capacity_txt],
    }
    summary = summary.assign(**capacity_columns)

    # Cumulated capacity columns
    calculated_from_capacity_columns = {
        headers_summary.cumulated_charge_capacity: summary[
            headers_summary.charge_capacity
        ].cumsum(),
        headers_summary.cumulated_discharge_capacity: summary[
            headers_summary.discharge_capacity
        ].cumsum(),
        headers_summary.discharge_capacity_loss: (
            summary[headers_summary.discharge_capacity].shift(1)
            - summary[headers_summary.discharge_capacity]
        ),
        headers_summary.charge_capacity_loss: (
            summary[headers_summary.charge_capacity].shift(1)
            - summary[headers_summary.charge_capacity]
        ),
        headers_summary.coulombic_difference: (
            summary[_first_step_txt] - summary[_second_step_txt]
        ),
    }
    summary = summary.assign(**calculated_from_capacity_columns)

    # Cumulated coulombic difference
    calculated_from_coulombic_efficiency_columns = {
        headers_summary.cumulated_coulombic_difference: summary[
            headers_summary.coulombic_difference
        ].cumsum(),
    }
    summary = summary.assign(**calculated_from_coulombic_efficiency_columns)

    # Cumulated capacity loss columns
    calculated_from_capacity_loss_columns = {
        headers_summary.cumulated_discharge_capacity_loss: summary[
            headers_summary.discharge_capacity_loss
        ].cumsum(),
        headers_summary.cumulated_charge_capacity_loss: summary[
            headers_summary.charge_capacity_loss
        ].cumsum(),
    }
    summary = summary.assign(**calculated_from_capacity_loss_columns)

    # Shifted capacity columns
    individual_edge_movement = summary[_first_step_txt] - summary[_second_step_txt]
    shifted_charge_capacity_column = {
        headers_summary.shifted_charge_capacity: individual_edge_movement.cumsum(),
    }
    summary = summary.assign(**shifted_charge_capacity_column)

    shifted_discharge_capacity_column = {
        headers_summary.shifted_discharge_capacity: summary[
            headers_summary.shifted_charge_capacity
        ]
        + summary[_first_step_txt],
    }
    summary = summary.assign(**shifted_discharge_capacity_column)

    ric = (summary[_first_step_txt].shift(1) - summary[_second_step_txt]) / summary[
        _second_step_txt
    ].shift(1)
    ric_column = {headers_summary.cumulated_ric: ric.cumsum()}
    summary = summary.assign(**ric_column)
    summary[headers_summary.cumulated_ric] = ric.cumsum()
    ric_sei = (summary[_first_step_txt] - summary[_second_step_txt].shift(1)) / summary[
        _second_step_txt
    ].shift(1)
    ric_sei_column = {headers_summary.cumulated_ric_sei: ric_sei.cumsum()}
    summary = summary.assign(**ric_sei_column)
    ric_disconnect = (
        summary[_second_step_txt].shift(1) - summary[_second_step_txt]
    ) / summary[_second_step_txt].shift(1)
    ric_disconnect_column = {
        headers_summary.cumulated_ric_disconnect: ric_disconnect.cumsum()
    }
    data.summary = summary.assign(**ric_disconnect_column)

    return data


def generate_specific_summary_columns(
    data: core.Data, mode: str, specific_columns: Sequence
) -> core.Data:
    """
    Generate specific summary columns.

    Args:
        data (core.Data): The data object.
        mode (str): The mode of the data (gravimetric, areal or absolute).
        specific_columns (Sequence): The columns to generate specific summary columns for.

    Returns:
        core.Data: The data object with the specific summary columns added to the summary.
    """
    specific_converter = units.get_converter_to_specific(data=data, mode=mode)
    summary = data.summary
    for col in specific_columns:
        logger.debug(f"generating specific column {col}_{mode}")
        summary[f"{col}_{mode}"] = specific_converter * summary[col]
    data.summary = summary
    return data


def end_voltage_to_summary(data: core.Data) -> core.Data:
    """
    Add end-voltage columns to the summary.

    Args:
        data (core.Data): The data object.

    Returns:
        core.Data: The data object with the end-voltage columns added to the summary.
    """

    # TODO: refactor this to use the correct headers and parameters when we have decided on them:
    DISCHARGE_TYPE_PREFIX = "discharge"
    CHARGE_TYPE_PREFIX = "charge"
    header_summary_cycle = headers_summary.cycle_index
    header_steps_cycle = headers_steps.cycle
    header_steps_voltage_last = "voltage_last"

    summary = data.summary
    steps = data.steps

    discharge_steps = selectors.get_step_numbers(
        data, steptype="discharge", allctypes=False
    )
    charge_steps = selectors.get_step_numbers(data, steptype="charge", allctypes=False)

    discharge_steps = steps.loc[
        steps["type"].str.startswith(DISCHARGE_TYPE_PREFIX),
        [header_steps_cycle, header_steps_voltage_last],
    ]
    charge_steps = steps.loc[
        steps["type"].str.startswith(CHARGE_TYPE_PREFIX),
        [header_steps_cycle, header_steps_voltage_last],
    ]
    charge_steps = charge_steps.rename(
        columns={
            header_steps_cycle: header_summary_cycle,
            header_steps_voltage_last: headers_summary.end_voltage_charge,
        }
    )
    discharge_steps = discharge_steps.rename(
        columns={
            header_steps_cycle: header_summary_cycle,
            header_steps_voltage_last: headers_summary.end_voltage_discharge,
        }
    )

    summary = summary.merge(discharge_steps, on=header_summary_cycle, how="left")
    summary = summary.merge(charge_steps, on=header_summary_cycle, how="left")

    data.summary = summary

    return data


def _calculate_nominal_capacity_from_cycles(
    summary: DataFrame,
    normalization_cycles: Union[Sequence, int],
    step_txt: str,
) -> float:
    """
    Calculate nominal capacity from specified normalization cycles.

    Args:
        summary: The summary DataFrame containing cycle data.
        normalization_cycles: The cycles to use for normalization (can be int or sequence).
        step_txt: The header string for the capacity column.

    Returns:
        float: The calculated nominal capacity.
    """
    logger.info(
        f"Using these cycles for finding the nominal capacity: {normalization_cycles}"
    )
    if not isinstance(normalization_cycles, (list, tuple)):
        normalization_cycles = [normalization_cycles]

    cap_ref = summary.loc[
        summary[headers_raw.cycle_index_txt].isin(normalization_cycles),
        step_txt,
    ]
    if not cap_ref.empty:
        nom_cap = cap_ref.mean()
    else:
        logger.info("Empty reference cycle(s)")
        nom_cap = 1.0  # Default fallback value

    return nom_cap


def equivalent_cycles_to_summary(
    data: core.Data,
    nom_cap: float = 1.0,
    normalization_cycles: Union[Sequence, int, None] = None,
    step_txt: str = headers_raw.charge_capacity_txt,
) -> core.Data:
    """
    Add equivalent cycles column to the summary.

    Args:
        data (core.Data): The data object.
        nom_cap (float): The nominal capacity (default: 1.0)
        normalization_cycles (Union[Sequence, int, None]): The cycles for normalization (default: None)
        step_txt (str): The header string for the charge or discharge capacity (default: charge capacity)
    """
    summary = data.summary

    if normalization_cycles is not None:
        nom_cap = _calculate_nominal_capacity_from_cycles(
            summary, normalization_cycles, step_txt
        )

    normalized_cycle_index_column = {
        headers_summary.normalized_cycle_index: summary[
            headers_summary.cumulated_charge_capacity
        ]
        / nom_cap
    }
    summary = summary.assign(**normalized_cycle_index_column)
    data.summary = summary
    return data


def c_rates_to_summary(
    data: core.Data,
    nom_cap: float = 1.0,
    normalization_cycles: Union[Sequence, int, None] = None,
    step_txt: str = headers_raw.charge_capacity_txt,
) -> core.Data:
    """
    Add c-rates to the summary.

    Args:
        data (core.Data): The data object.
        nom_cap (float): The nominal capacity (default: 1.0)
        normalization_cycles (Union[Sequence, int, None]): The cycles for normalization (default: None)
        step_txt (str): The header string for the charge or discharge capacity (default: charge capacity)
    Returns:
        core.Data: The data object with the c-rates added to the summary.
    """
    logger.debug("Extracting C-rates")

    summary = data.summary
    steps = data.steps

    if normalization_cycles is not None:
        nom_cap = _calculate_nominal_capacity_from_cycles(
            summary, normalization_cycles, step_txt
        )

    def rate_to_cellpy_units(rate):
        conversion_factor = core.Q(1.0, data.raw_units["current"]) / core.Q(
            1.0, cellpy_units["current"]
        )
        conversion_factor = conversion_factor.to_reduced_units().magnitude
        return rate * conversion_factor

    charge_steps = steps.loc[
        steps.type == "charge",
        [headers_steps.cycle, headers_steps.rate_avr],
    ].rename(columns={headers_steps.rate_avr: headers_summary.charge_c_rate})

    charge_steps = charge_steps.drop_duplicates(
        subset=[headers_steps.cycle], keep="first"
    )
    charge_steps[headers_summary.charge_c_rate] = rate_to_cellpy_units(
        charge_steps[headers_summary.charge_c_rate] / nom_cap
    )

    summary = summary.merge(
        charge_steps,
        left_on=headers_summary.cycle_index,
        right_on=headers_steps.cycle,
        how="left",
    ).drop(columns=headers_steps.cycle)

    discharge_steps = steps.loc[
        steps.type == "discharge",
        [headers_steps.cycle, headers_steps.rate_avr],
    ].rename(columns={headers_steps.rate_avr: headers_summary.discharge_c_rate})

    discharge_steps = discharge_steps.drop_duplicates(
        subset=[headers_steps.cycle], keep="first"
    )
    discharge_steps[headers_summary.discharge_c_rate] = rate_to_cellpy_units(
        discharge_steps[headers_summary.discharge_c_rate] / nom_cap
    )
    summary = summary.merge(
        discharge_steps,
        left_on=headers_summary.cycle_index,
        right_on=headers_steps.cycle,
        how="left",
    ).drop(columns=headers_steps.cycle)
    data.summary = summary
    return data


def ir_to_summary(data: core.Data) -> core.Data:
    # should check:  test.charge_steps = None,
    # test.discharge_steps = None
    # THIS DOES NOT WORK PROPERLY!!!!
    # Found a file where it writes IR for cycle n on cycle n+1
    # This only picks out the data on the last IR step before
    summary = data.summary
    raw = data.raw

    logger.debug("finding ir")
    only_zeros = summary[headers_raw.discharge_capacity_txt] * 0.0
    discharge_steps = selectors.get_step_numbers(
        data,
        steptype="discharge",
        allctypes=False,
    )
    charge_steps = selectors.get_step_numbers(
        data,
        steptype="charge",
        allctypes=False,
    )
    ir_indexes = []
    ir_values = []
    ir_values2 = []
    for i in summary.index:
        # selecting the appropriate cycle
        cycle = summary.iloc[i][headers_raw.cycle_index_txt]
        step = discharge_steps[cycle]
        if step[0]:
            ir = raw.loc[
                (raw[headers_raw.cycle_index_txt] == cycle)
                & (data.raw[headers_raw.step_index_txt] == step[0]),
                headers_raw.internal_resistance_txt,
            ]
            # This will not work if there are more than one item in step
            ir = ir.values[0]
        else:
            ir = 0
        step2 = charge_steps[cycle]
        if step2[0]:
            ir2 = raw[
                (raw[headers_raw.cycle_index_txt] == cycle)
                & (data.raw[headers_raw.step_index_txt] == step2[0])
            ][headers_raw.internal_resistance_txt].values[0]
        else:
            ir2 = 0
        ir_indexes.append(i)
        ir_values.append(ir)
        ir_values2.append(ir2)
    ir_frame = only_zeros + ir_values
    ir_frame2 = only_zeros + ir_values2
    summary.insert(0, column=headers_summary.ir_discharge, value=ir_frame)
    summary.insert(0, column=headers_summary.ir_charge, value=ir_frame2)
    data.summary = summary
    return data


def _main():
    # a function to show how to use the summarizers
    import pathlib
    import matplotlib.pyplot as plt

    from cellpy import cellreader

    # load the data
    arbin_raw_file = (
        pathlib.Path(__file__).parent.parent.parent
        / "testdata"
        / "data"
        / "20160805_test001_45_cc_01.res"
    )
    cpi = cellreader.CellpyCell()
    cpi.set_instrument("arbin_res")
    cpi.from_raw(arbin_raw_file)

    # make the step table
    # cpi.make_step_table()
    cpi.data = make_step_table(cpi.data, raw_limits=cpi.raw_limits)

    # create a simple selector function that will be used to select the data
    # from the raw data (the create_selector method creates a function that picks the last row from each cycle,
    # thus assuming ended half-cycle values are repeated until end-of-cycle)
    simple_summary_selector_function = selectors.create_selector(cpi.data)
    cpi.data.summary = simple_summary_selector_function()

    # the data type is of "half-cell anode" ("anode"), so we assume that the first step is the discharge step
    # and the second step is the charge step
    _first_step_txt = headers_raw.discharge_capacity_txt
    _second_step_txt = headers_raw.charge_capacity_txt

    # generate the absolute summary columns (the columns that are only dependent on the raw data, and not for
    # example the mass of the electrodes)
    cpi.data = generate_absolute_summary_columns(
        cpi.data, _first_step_txt, _second_step_txt
    )

    # add end-voltage columns
    cpi.data = end_voltage_to_summary(cpi.data)

    # add ir
    cpi.data = ir_to_summary(cpi.data)

    # add equivalent cycles column (uses meta data)
    cpi.data = equivalent_cycles_to_summary(
        cpi.data, nom_cap=1.0, normalization_cycles=[1, 2, 3]
    )

    # add c-rates (uses meta data)
    cpi.data = c_rates_to_summary(cpi.data)

    # plot the summary
    fig, axes = plt.subplots(5, 1, figsize=(4, 8), sharex=True)

    # Capacities vs cycle
    axes[0].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.charge_capacity],
        label="charge",
    )
    axes[0].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.discharge_capacity],
        label="discharge",
    )
    axes[0].set_ylabel("Capacity")
    axes[0].legend()
    axes[0].set_title("Capacities vs Cycle")

    # Capacities vs equivalent cycles
    axes[1].plot(
        cpi.data.summary[headers_summary.normalized_cycle_index],
        cpi.data.summary[headers_summary.charge_capacity],
        label="charge",
    )
    axes[1].plot(
        cpi.data.summary[headers_summary.normalized_cycle_index],
        cpi.data.summary[headers_summary.discharge_capacity],
        label="discharge",
    )
    axes[1].set_ylabel("Capacity")
    axes[1].legend()
    axes[1].set_title("Capacities vs Equivalent Cycles")

    # End voltages
    axes[2].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.end_voltage_charge],
        label="charge",
    )
    axes[2].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.end_voltage_discharge],
        label="discharge",
    )
    axes[2].set_ylabel("End Voltage")
    axes[2].legend()
    axes[2].set_title("End Voltages vs Cycle")

    # C-rates
    axes[3].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.charge_c_rate],
        label="charge",
    )
    axes[3].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.discharge_c_rate],
        label="discharge",
    )
    axes[3].set_ylabel("C-rate")
    axes[3].legend()
    axes[3].set_title("C-rates vs Cycle")

    # Internal resistance
    axes[4].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.ir_charge],
        label="charge",
    )
    axes[4].plot(
        cpi.data.summary[headers_summary.cycle_index],
        cpi.data.summary[headers_summary.ir_discharge],
        label="discharge",
    )
    axes[4].set_ylabel("Internal Resistance")
    axes[4].set_xlabel("Cycle")
    axes[4].legend()
    axes[4].set_title("Internal Resistance vs Cycle")

    fig.align_ylabels()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    _main()
