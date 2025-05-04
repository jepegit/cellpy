import collections
import functools
import logging

import numbers
import time
import datetime

from typing import Callable, Union, Sequence, Optional, Any, List, TypeVar

from cellpy.readers import core
from cellpy.exceptions import (
    NoDataFound,
)

from cellpy.parameters.internal_settings import (
    get_cellpy_units,
    get_default_output_units,
    HeadersNormal,
    HeadersStepTable,
    HeadersSummary,
    CellpyUnits,
)

from cellpy.slim import selectors

DataFrame = TypeVar("DataFrame")

logger = logging.getLogger(__name__)

headers_step_table = HeadersStepTable()
headers_summary = HeadersSummary()
headers_normal = HeadersNormal()

cellpy_units = get_cellpy_units()
output_units = get_default_output_units() 

CAPACITY_MODIFIERS = ["reset"]
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


class CellpyCellCore:  # Rename to CellpyCell when cellpy core is ready

    def __init__(
        self,
        initialize: bool = False,
        debug: bool = False,
    ):
        """
        Args:
            initialize (bool): set to True if you want to initialize the cellpy object with an empty Data instance.
            debug (bool): set to True if you want to see debug messages.
        """

        self.debug = debug
        logger.debug("created CellpyCellCore instance")

        self._cell_name: Optional[str] = None
        self._cycle_mode: Optional[str] = None
        self._data: Optional[core.Data] = None

        self.cellpy_file_name: Optional[str] = None
        self.cellpy_object_created_at: datetime.datetime = datetime.datetime.now()
        self.forced_errors: int = 0

        self.capacity_modifiers: List[str] = CAPACITY_MODIFIERS
        self.list_of_step_types: List[str] = STEP_TYPES

        # - headers
        self.headers_normal: HeadersNormal = headers_normal  # remove this when cellpy core is ready
        self.headers_summary: HeadersSummary = headers_summary  # remove this when cellpy core is ready
        self.headers_step_table: HeadersStepTable = headers_step_table  # remove this when cellpy core is ready

        # - units used by cellpy
        self.cellpy_units = get_cellpy_units()  # remove this when cellpy core is ready
        self.output_units = get_default_output_units()  # remove this when cellpy core is ready
        if initialize:
            self.initialize()
        
    def initialize(self):
        """Initialize the CellpyCell object with empty Data instance."""

        logger.debug("Initializing...")
        self._data = core.Data()

    @property
    def data(self) -> core.Data:
        """Returns the DataSet instance.
        
        Returns:
            DataSet instance.

        Raises:
            NoDataFound: If the CellpyCell does not have any data.
        """

        if not self._data:
            raise NoDataFound("The CellpyCell does not have any data.")
        else:
            return self._data

    @data.setter
    def data(self, new_cell: core.Data):
        """Sets the Data instance"""

        self._data = new_cell

    @property
    def cycle_mode(self) -> str:
        # TODO: v2.0 edit this from scalar to list
        try:
            data = self.data
            m = data.meta_test_dependent.cycle_mode
            # cellpy saves this as a list (ready for v2.0),
            # but we want to return a scalar for the moment
            # Temporary fix to make sure that cycle_mode is a scalar:
            if isinstance(m, (tuple, list)):
                return m[0]
            return m
        except NoDataFound:
            return self._cycle_mode

    @cycle_mode.setter
    def cycle_mode(self, cycle_mode: str):
        if isinstance(cycle_mode, (tuple, list)):
            cycle_mode = [cycle_mode.lower() for cycle_mode in cycle_mode]
        else:
            cycle_mode = cycle_mode.lower()
        # TODO: v2.0 edit this from scalar to list
        logger.debug(f"-> cycle_mode: {cycle_mode}")
        try:
            data = self.data
            data.meta_test_dependent.cycle_mode = cycle_mode
            self._cycle_mode = cycle_mode
        except NoDataFound:
            self._cycle_mode = cycle_mode

    
    def _dump_cellpy_unit(self, value, parameter):
        """Parse for unit, update cellpy_units class, and return magnitude."""
        import numpy as np

        c_value, c_unit = self._check_value_unit(value, parameter)
        if not isinstance(c_value, numbers.Number) or np.isnan(c_value):
            logger.critical(f"Could not parse {parameter} ({value})")
            logger.critical("Setting it to 1.0")
            return 1.0
        if c_unit is not None:
            self.cellpy_units[parameter] = f"{c_unit}"
            logger.debug(f"Updated your cellpy_units['{parameter}'] to '{c_unit}'")

        return c_value

    @staticmethod
    def _check_value_unit(value, parameter) -> tuple:
        """Check if value is a valid number, or a quantity with units."""
        if isinstance(value, numbers.Number):
            return value, None
        logger.critical(f"Parsing {parameter} ({value})")

        try:
            c = core.Q(value)
            c_unit = c.units
            c_value = c.magnitude
        except ValueError:
            logger.debug(f"Could not parse {value}")
            return None, None
        return c_value, c_unit
    
    def _generate_specific_summary_columns(self, data: core.Data, mode: str, specific_columns: Sequence) -> core.Data:
        specific_converter = self.get_converter_to_specific(data=data, mode=mode)
        summary = data.summary
        for col in specific_columns:
            logging.debug(f"generating specific column {col}_{mode}")
            summary[f"{col}_{mode}"] = specific_converter * summary[col]
        data.summary = summary
        return data


    def _generate_absolute_summary_columns(self, data, _first_step_txt, _second_step_txt) -> core.Data:
        summary = data.summary
        summary[headers_summary.coulombic_efficiency] = 100 * summary[_second_step_txt] / summary[_first_step_txt]
        summary[headers_summary.cumulated_coulombic_efficiency] = summary[
            headers_summary.coulombic_efficiency
        ].cumsum()

        capacity_columns = {
            headers_summary.charge_capacity: summary[headers_normal.charge_capacity_txt],
            headers_summary.discharge_capacity: summary[headers_normal.discharge_capacity_txt],
        }
        summary = summary.assign(**capacity_columns)

        calculated_from_capacity_columns = {
            headers_summary.cumulated_charge_capacity: summary[headers_summary.charge_capacity].cumsum(),
            headers_summary.cumulated_discharge_capacity: summary[
                headers_summary.discharge_capacity
            ].cumsum(),
            headers_summary.discharge_capacity_loss: (
                summary[headers_summary.discharge_capacity].shift(1)
                - summary[headers_summary.discharge_capacity]
            ),
            headers_summary.charge_capacity_loss: (
                summary[headers_summary.charge_capacity].shift(1) - summary[headers_summary.charge_capacity]
            ),
            headers_summary.coulombic_difference: (summary[_first_step_txt] - summary[_second_step_txt]),
        }

        summary = summary.assign(**calculated_from_capacity_columns)

        calculated_from_coulombic_efficiency_columns = {
            headers_summary.cumulated_coulombic_difference: summary[
                headers_summary.coulombic_difference
            ].cumsum(),
        }

        summary = summary.assign(**calculated_from_coulombic_efficiency_columns)
        calculated_from_capacity_loss_columns = {
            headers_summary.cumulated_discharge_capacity_loss: summary[
                headers_summary.discharge_capacity_loss
            ].cumsum(),
            headers_summary.cumulated_charge_capacity_loss: summary[
                headers_summary.charge_capacity_loss
            ].cumsum(),
        }
        summary = summary.assign(**calculated_from_capacity_loss_columns)

        individual_edge_movement = summary[_first_step_txt] - summary[_second_step_txt]
        shifted_charge_capacity_column = {
            headers_summary.shifted_charge_capacity: individual_edge_movement.cumsum(),
        }
        summary = summary.assign(**shifted_charge_capacity_column)

        shifted_discharge_capacity_column = {
            headers_summary.shifted_discharge_capacity: summary[headers_summary.shifted_charge_capacity]
            + summary[_first_step_txt],
        }
        summary = summary.assign(**shifted_discharge_capacity_column)
        ric = (summary[_first_step_txt].shift(1) - summary[_second_step_txt]) / summary[_second_step_txt].shift(1)
        ric_column = {headers_summary.cumulated_ric: ric.cumsum()}
        summary = summary.assign(**ric_column)
        summary[headers_summary.cumulated_ric] = ric.cumsum()
        ric_sei = (summary[_first_step_txt] - summary[_second_step_txt].shift(1)) / summary[_second_step_txt].shift(1)
        ric_sei_column = {headers_summary.cumulated_ric_sei: ric_sei.cumsum()}
        summary = summary.assign(**ric_sei_column)
        ric_disconnect = (summary[_second_step_txt].shift(1) - summary[_second_step_txt]) / summary[
            _second_step_txt
        ].shift(1)
        ric_disconnect_column = {headers_summary.cumulated_ric_disconnect: ric_disconnect.cumsum()}
        data.summary = summary.assign(**ric_disconnect_column)

        return data

    def _c_rates_to_summary(self, data: core.Data) -> core.Data:
        logger.debug("Extracting C-rates")

        def rate_to_cellpy_units(rate):
            conversion_factor = core.Q(1.0, self.data.raw_units["current"]) / core.Q(1.0, self.cellpy_units["current"])
            conversion_factor = conversion_factor.to_reduced_units().magnitude
            return rate * conversion_factor

        summary = data.summary
        steps = self.data.steps

        charge_steps = steps.loc[
            steps.type == "charge",
            [headers_step_table.cycle, headers_step_table.rate_avr],
        ].rename(columns={headers_step_table.rate_avr: headers_summary.charge_c_rate})

        charge_steps = charge_steps.drop_duplicates(subset=[headers_step_table.cycle], keep="first")
        charge_steps[headers_summary.charge_c_rate] = rate_to_cellpy_units(
            charge_steps[headers_summary.charge_c_rate]
        )

        summary = summary.merge(
            charge_steps,
            left_on=headers_summary.cycle_index,
            right_on=headers_step_table.cycle,
            how="left",
        ).drop(columns=headers_step_table.cycle)

        discharge_steps = steps.loc[
            steps.type == "discharge",
            [headers_step_table.cycle, headers_step_table.rate_avr],
        ].rename(columns={headers_step_table.rate_avr: headers_summary.discharge_c_rate})

        discharge_steps = discharge_steps.drop_duplicates(subset=[headers_step_table.cycle], keep="first")
        discharge_steps[headers_summary.discharge_c_rate] = rate_to_cellpy_units(
            discharge_steps[headers_summary.discharge_c_rate]
        )
        summary = summary.merge(
            discharge_steps,
            left_on=headers_summary.cycle_index,
            right_on=headers_step_table.cycle,
            how="left",
        ).drop(columns=headers_step_table.cycle)
        data.summary = summary
        return data

    def _equivalent_cycles_to_summary(
        self,
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
            logger.info(f"Using these cycles for finding the nominal capacity: {normalization_cycles}")
            if not isinstance(normalization_cycles, (list, tuple)):
                normalization_cycles = [normalization_cycles]

            cap_ref = summary.loc[
                summary[headers_normal.cycle_index_txt].isin(normalization_cycles),
                _first_step_txt,
            ]
            if not cap_ref.empty:
                nom_cap = cap_ref.mean()
            else:
                logger.info("Empty reference cycle(s)")

        normalized_cycle_index_column = {
            headers_summary.normalized_cycle_index: summary[headers_summary.cumulated_charge_capacity]
            / nom_cap
        }
        summary = summary.assign(**normalized_cycle_index_column)
        data.summary = summary
        return data

    def _ir_to_summary(self, data):
        # should check:  test.charge_steps = None,
        # test.discharge_steps = None
        # THIS DOES NOT WORK PROPERLY!!!!
        # Found a file where it writes IR for cycle n on cycle n+1
        # This only picks out the data on the last IR step before
        summary = data.summary
        raw = data.raw

        logger.debug("finding ir")
        only_zeros = summary[headers_normal.discharge_capacity_txt] * 0.0
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
            cycle = summary.iloc[i][headers_normal.cycle_index_txt]
            step = discharge_steps[cycle]
            if step[0]:
                ir = raw.loc[
                    (raw[headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[headers_normal.step_index_txt] == step[0]),
                    headers_normal.internal_resistance_txt,
                ]
                # This will not work if there are more than one item in step
                ir = ir.values[0]
            else:
                ir = 0
            step2 = charge_steps[cycle]
            if step2[0]:
                ir2 = raw[
                    (raw[headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[headers_normal.step_index_txt] == step2[0])
                ][headers_normal.internal_resistance_txt].values[0]
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

    def _end_voltage_to_summary(self, data):
        # needs to be fixed so that end-voltage also can be extracted
        # from the summary
        ev_t0 = time.time()
        raw = data.raw
        summary = data.summary

        logger.debug("finding end-voltage")
        logger.debug(f"dt: {time.time() - ev_t0}")
        only_zeros_discharge = summary[headers_normal.discharge_capacity_txt] * 0.0
        only_zeros_charge = summary[headers_normal.charge_capacity_txt] * 0.0
        logger.debug("need to collect discharge steps")
        discharge_steps = selectors.get_step_numbers(data, steptype="discharge", allctypes=False)
        logger.debug(f"dt: {time.time() - ev_t0}")
        logger.debug("need to collect charge steps")
        charge_steps = selectors.get_step_numbers(data, steptype="charge", allctypes=False)
        logger.debug(f"dt: {time.time() - ev_t0}")
        endv_indexes = []
        endv_values_dc = []
        endv_values_c = []
        logger.debug("starting iterating through the index")
        for i in summary.index:
            cycle = summary.iloc[i][headers_normal.cycle_index_txt]
            step = discharge_steps[cycle]

            # finding end voltage for discharge
            if step[-1]:  # selecting last
                end_voltage_dc = raw[
                    (raw[headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[headers_normal.step_index_txt] == step[-1])
                ][headers_normal.voltage_txt]
                # This will not work if there are more than one item in step
                end_voltage_dc = end_voltage_dc.values[-1]  # selecting
            else:
                end_voltage_dc = 0  # could also use numpy.nan

            # finding end voltage for charge
            step2 = charge_steps[cycle]
            if step2[-1]:
                end_voltage_c = raw[
                    (raw[headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[headers_normal.step_index_txt] == step2[-1])
                ][headers_normal.voltage_txt]
                end_voltage_c = end_voltage_c.values[-1]
            else:
                end_voltage_c = 0
            endv_indexes.append(i)
            endv_values_dc.append(end_voltage_dc)
            endv_values_c.append(end_voltage_c)

        ir_frame_dc = only_zeros_discharge + endv_values_dc
        ir_frame_c = only_zeros_charge + endv_values_c
        data.summary.insert(0, column=headers_summary.end_voltage_discharge, value=ir_frame_dc)
        data.summary.insert(0, column=headers_summary.end_voltage_charge, value=ir_frame_c)

        return data

    def make_core_summary(
        self,
        data: core.Data,
        selector: Optional[Callable] = None,
        find_ir: bool = True,
        find_end_voltage: bool = False,
        select_columns: bool = True,
    ) -> core.Data:
        """Make the core summary.
        
        Args:
            data: The data to make the summary from.
            selector: The selector to use.
            find_ir: Whether to find the IR.
            find_end_voltage: Whether to find the end voltage.
            select_columns: Whether to select only the minimum columns that are needed.

        Returns:
            Data object with the summary.
        """


        time_00 = time.time()
        logger.debug("start making summary")

        summary = selector()
        column_names = summary.columns
        # TODO @jepe: use pandas.DataFrame properties instead (.len, .reset_index), but maybe first
        #  figure out if this is really needed and why it was implemented in the first place.
        summary_length = len(summary[column_names[0]])
        summary.index = list(range(summary_length))

        if select_columns:
            logger.debug("keeping only selected set of columns")
            columns_to_keep = [
                headers_normal.charge_capacity_txt,
                headers_normal.cycle_index_txt,
                headers_normal.data_point_txt,
                headers_normal.datetime_txt,
                headers_normal.discharge_capacity_txt,
                headers_normal.test_time_txt,
            ]
            for cn in column_names:
                if not columns_to_keep.count(cn):
                    try:
                        summary.pop(cn)
                    except KeyError:
                        logger.debug(f"could not pop {cn}")

        data.summary = summary

        # ----------------- calculated values -----------------------

        if self.cycle_mode == "anode":
            logger.info("Assuming cycling in anode half-data (discharge before charge) mode")
            _first_step_txt = headers_summary.discharge_capacity
            _second_step_txt = headers_summary.charge_capacity
        else:
            logger.info("Assuming cycling in full-data / cathode mode")
            _first_step_txt = headers_summary.charge_capacity
            _second_step_txt = headers_summary.discharge_capacity

        # ---------------- absolute -------------------------------

        data = self._generate_absolute_summary_columns(data, _first_step_txt, _second_step_txt)

        # TODO @jepe: refactor this to method:
        if find_end_voltage:
            data = self._end_voltage_to_summary(data)

        if find_ir and (headers_normal.internal_resistance_txt in data.raw.columns):
            data = self._ir_to_summary(data)

        data = self._c_rates_to_summary(data)


        logger.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return data
    
    def add_scaled_summary_columns(
            self, 
            data: core.Data, 
            nom_cap_abs: float,
            normalization_cycles: Union[Sequence, int, None],
            specifics: Optional[List[str]] = None,
            ) -> core.Data:
        """Add specific summary columns to the summary.
        
        Args:
            data: The data to add the specific summary columns to.
            nom_cap_abs: The nominal capacity of the cell.
            normalization_cycles: The number of cycles to normalize the data by.
            specifics: The specifics to add.

        Returns:
            The data with the specific summary columns added.
        """
        if specifics is None:
            specifics = ["gravimetric", "areal", "absolute"]

        if self.cycle_mode == "anode":
            logging.debug("Assuming cycling in anode half-data (discharge before charge) mode")
            _first_step_txt = headers_summary.discharge_capacity
            _second_step_txt = headers_summary.charge_capacity
        else:
            logging.debug("Assuming cycling in full-data / cathode mode")
            _first_step_txt = headers_summary.charge_capacity
            _second_step_txt = headers_summary.discharge_capacity

        data = self._equivalent_cycles_to_summary(
            data, _first_step_txt, _second_step_txt, nom_cap_abs, normalization_cycles
        )

        specific_columns = headers_summary.specific_columns
        for mode in specifics:
            data = self._generate_specific_summary_columns(data, mode, specific_columns)

        return data




    @staticmethod
    def set_col_first(df, col_names):
        """Set selected columns first in a pandas.DataFrame.

        This function sets cols with names given in  col_names (a list) first in
        the DataFrame. The last col in col_name will come first (processed last)

        """

        column_headings = df.columns
        column_headings = column_headings.tolist()
        try:
            for col_name in col_names:
                column_headings.pop(column_headings.index(col_name))
                column_headings.insert(0, col_name)

        finally:
            df = df.reindex(columns=column_headings)
            return df
        
    @staticmethod
    def get_converter_to_specific(
        data: core.Data,
        value: float = None,
        from_units: CellpyUnits = None,
        to_units: CellpyUnits = None,
        mode: str = "gravimetric",
    ) -> float:
        """Convert from absolute units to specific (areal or gravimetric).

        The method provides a conversion factor that you can multiply your
        values with to get them into specific values.

        Args:
            data: data instance
            value: value used to scale on.
            from_units: defaults to data.raw_units.
            to_units: defaults to cellpy_units.
            mode (str): gravimetric, areal or absolute

        Returns:
            conversion factor (float)

        """
        # TODO @jepe: implement handling of edge-cases
        # TODO @jepe: fix all the instrument readers (replace floats in raw_units with strings)

        new_units = to_units or get_cellpy_units()
        old_units = from_units or data.raw_units

        if mode == "gravimetric":
            value = value or data.mass
            value = core.Q(value, new_units["mass"])
            to_unit_specific = core.Q(1.0, new_units["specific_gravimetric"])

        elif mode == "areal":
            value = value or data.active_electrode_area
            value = core.Q(value, new_units["area"])
            to_unit_specific = core.Q(1.0, new_units["specific_areal"])

        elif mode == "volumetric":
            value = value or data.volume
            value = core.Q(value, new_units["volume"])
            to_unit_specific = core.Q(1.0, new_units["specific_volumetric"])

        elif mode == "absolute":
            value = core.Q(1.0, None)
            to_unit_specific = core.Q(1.0, None)

        else:
            logging.debug(f"mode={mode} not supported!")
            return 1.0

        from_unit_cap = core.Q(1.0, old_units["charge"])
        to_unit_cap = core.Q(1.0, new_units["charge"])

        # from unit is always in absolute values:
        from_unit = from_unit_cap

        to_unit = to_unit_cap / to_unit_specific

        conversion_factor = (from_unit / to_unit / value).to_reduced_units()
        logging.debug(f"conversion factor: {conversion_factor}")
        return conversion_factor.m

