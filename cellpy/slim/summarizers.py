import logging
from typing import Sequence, TypeVar, Union

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
    logger.debug("created u-steps")
    return un


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


# def end_voltage_to_summary(data: core.Data) -> core.Data:
#     summary = data.summary
#     end_voltage_discharge_column = {
#         headers_summary.end_voltage_discharge: summary[headers_raw.voltage_txt]
#     }
#     summary = summary.assign(**end_voltage_discharge_column)
#     end_voltage_charge_column = {
#         headers_summary.end_voltage_charge: summary[headers_raw.voltage_txt]
#     }
#     summary = summary.assign(**end_voltage_charge_column)
#     data.summary = summary
#     return data


def generate_specific_summary_columns(
    data: core.Data, mode: str, specific_columns: Sequence
) -> core.Data:
    specific_converter = units.get_converter_to_specific(data=data, mode=mode)
    summary = data.summary
    for col in specific_columns:
        logging.debug(f"generating specific column {col}_{mode}")
        summary[f"{col}_{mode}"] = specific_converter * summary[col]
    data.summary = summary
    return data


def end_voltage_to_summary(data: core.Data) -> core.Data:
    # needs to be fixed so that end-voltage also can be extracted
    # from the summary

    # raw = data.raw
    summary = data.summary
    steps = data.steps

    logger.debug("need to collect discharge steps")
    discharge_steps = selectors.get_step_numbers(
        data, steptype="discharge", allctypes=False
    )
    charge_steps = selectors.get_step_numbers(data, steptype="charge", allctypes=False)

    print(f"discharge_steps: {discharge_steps}")
    print(f"charge_steps: {charge_steps}")
    print(f"summary.columns: {summary.columns}")

    print(f"steps.columns: {steps.columns}")
    discharge_steps = steps.loc[
        steps["type"].str.startswith("discharge"), ["cycle", "voltage_last"]
    ]
    charge_steps = steps.loc[
        steps["type"].str.startswith("charge"), ["cycle", "voltage_last"]
    ]
    print(f"discharge_steps: {discharge_steps}")
    print(f"charge_steps: {charge_steps}")

    # NEXT: add the end-voltage columns to the summary so that the cycle index is used as the key

    # for i in summary.index:
    #     cycle = summary.iloc[i][headers_raw.cycle_index_txt]
    #     step = discharge_steps[cycle]

    #     # finding end voltage for discharge
    #     if step[-1]:  # selecting last
    #         end_voltage_dc = raw[
    #             (raw[headers_raw.cycle_index_txt] == cycle)
    #             & (data.raw[headers_raw.step_index_txt] == step[-1])
    #         ][headers_raw.voltage_txt]
    #         # This will not work if there are more than one item in step
    #         end_voltage_dc = end_voltage_dc.values[-1]  # selecting
    #     else:
    #         end_voltage_dc = 0  # could also use numpy.nan

    #     # finding end voltage for charge
    #     step2 = charge_steps[cycle]
    #     if step2[-1]:
    #         end_voltage_c = raw[
    #             (raw[headers_raw.cycle_index_txt] == cycle)
    #             & (data.raw[headers_raw.step_index_txt] == step2[-1])
    #         ][headers_raw.voltage_txt]
    #         end_voltage_c = end_voltage_c.values[-1]
    #     else:
    #         end_voltage_c = 0
    #     endv_indexes.append(i)
    #     endv_values_dc.append(end_voltage_dc)
    #     endv_values_c.append(end_voltage_c)

    # ir_frame_dc = only_zeros_discharge + endv_values_dc
    # ir_frame_c = only_zeros_charge + endv_values_c
    # data.summary.insert(
    #     0, column=headers_summary.end_voltage_discharge, value=ir_frame_dc
    # )
    # data.summary.insert(0, column=headers_summary.end_voltage_charge, value=ir_frame_c)

    return data


def equivalent_cycles_to_summary(
    data: core.Data,
    _first_step_txt: str,
    _second_step_txt: str,
    nom_cap: float,
    normalization_cycles: Union[Sequence, int, None],
) -> core.Data:
    # The method currently uses the charge capacity for calculating equivalent cycles. This
    # can be easily extended to also allow for choosing the discharge capacity later on if
    # it turns out that to be needed.

    summary = data.summary

    if normalization_cycles is not None:
        logger.info(
            f"Using these cycles for finding the nominal capacity: {normalization_cycles}"
        )
        if not isinstance(normalization_cycles, (list, tuple)):
            normalization_cycles = [normalization_cycles]

        cap_ref = summary.loc[
            summary[headers_raw.cycle_index_txt].isin(normalization_cycles),
            _first_step_txt,
        ]
        if not cap_ref.empty:
            nom_cap = cap_ref.mean()
        else:
            logger.info("Empty reference cycle(s)")

    normalized_cycle_index_column = {
        headers_summary.normalized_cycle_index: summary[
            headers_summary.cumulated_charge_capacity
        ]
        / nom_cap
    }
    summary = summary.assign(**normalized_cycle_index_column)
    data.summary = summary
    return data


def c_rates_to_summary(data: core.Data) -> core.Data:
    logger.debug("Extracting C-rates")

    def rate_to_cellpy_units(rate):
        conversion_factor = core.Q(1.0, data.raw_units["current"]) / core.Q(
            1.0, cellpy_units["current"]
        )
        conversion_factor = conversion_factor.to_reduced_units().magnitude
        return rate * conversion_factor

    summary = data.summary
    steps = data.steps

    charge_steps = steps.loc[
        steps.type == "charge",
        [headers_steps.cycle, headers_steps.rate_avr],
    ].rename(columns={headers_steps.rate_avr: headers_summary.charge_c_rate})

    charge_steps = charge_steps.drop_duplicates(
        subset=[headers_steps.cycle], keep="first"
    )
    charge_steps[headers_summary.charge_c_rate] = rate_to_cellpy_units(
        charge_steps[headers_summary.charge_c_rate]
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
        discharge_steps[headers_summary.discharge_c_rate]
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
    cpi.make_step_table()

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


if __name__ == "__main__":
    _main()
