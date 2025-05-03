import collections
import functools
import logging

import numbers
import time
import datetime

from typing import Union, Sequence, Optional, Any

from cellpy.readers import core

from cellpy.exceptions import (

    NoDataFound,
)

from cellpy.parameters.internal_settings import (
    get_cellpy_units,
    headers_normal,
    headers_step_table,
    headers_summary,
    get_default_output_units,
)

_module_logger = logging.getLogger(__name__)

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


class CellpyCellCore:

    def __init__(
        self,
        cellpy_units=None,
        output_units=None,
        initialize=False,
        debug=False,
    ):
        """
        Args:
            cellpy_units (dict): sent to cellpy.parameters.internal_settings.get_cellpy_units
            output_units (dict): sent to cellpy.parameters.internal_settings.get_default_output_units
            debug (bool): set to True if you want to see debug messages.
        """

        self.debug = debug
        logging.debug("created CellpyCellCore instance")

        self._cell_name = None
        self._cycle_mode = None
        self._data = None

        self.cellpy_file_name = None
        self.cellpy_object_created_at = datetime.datetime.now()
        self.forced_errors = 0

        self.capacity_modifiers = CAPACITY_MODIFIERS
        self.list_of_step_types = STEP_TYPES

        # - headers
        self.headers_normal = headers_normal
        self.headers_summary = headers_summary
        self.headers_step_table = headers_step_table

        # - units used by cellpy
        self.cellpy_units = get_cellpy_units(cellpy_units)
        self.output_units = get_default_output_units(output_units) 
        if initialize:
            self.initialize()
        
    def initialize(self):
        """Initialize the CellpyCell object with empty Data instance."""

        logging.debug("Initializing...")
        self._data = core.Data()

    @property
    def data(self):
        """Returns the DataSet instance"""

        if not self._data:
            logging.debug("NoDataFound - might consider defaulting to create one in the future")
            raise NoDataFound
        else:
            return self._data

    @data.setter
    def data(self, new_cell: core.Data):
        """sets the DataSet instance"""

        self._data = new_cell

    @property
    def cycle_mode(self):
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
    def cycle_mode(self, cycle_mode):
        # TODO: v2.0 edit this from scalar to list
        logging.debug(f"-> cycle_mode: {cycle_mode}")
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
            logging.critical(f"Could not parse {parameter} ({value})")
            logging.critical("Setting it to 1.0")
            return 1.0
        if c_unit is not None:
            self.cellpy_units[parameter] = f"{c_unit}"
            logging.debug(f"Updated your cellpy_units['{parameter}'] to '{c_unit}'")

        return c_value

    @staticmethod
    def _check_value_unit(value, parameter) -> tuple:
        """Check if value is a valid number, or a quantity with units."""
        if isinstance(value, numbers.Number):
            return value, None
        logging.critical(f"Parsing {parameter} ({value})")

        try:
            c = core.Q(value)
            c_unit = c.units
            c_value = c.magnitude
        except ValueError:
            logging.debug(f"Could not parse {value}")
            return None, None
        return c_value, c_unit

    def get_step_numbers(
        self,
        steptype: str = "charge",
        allctypes: bool = True,
        pdtype: bool = False,
        cycle_number: int = None,
        trim_taper_steps: int = None,
        steps_to_skip: Optional[list] = None,
        steptable: Any = None,
        usteps: bool = False,
    ) -> Union[dict, Any]:
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
            logging.warning("Trimming taper steps is not possible when using usteps. Not doing any trimming.")
            trim_taper_steps = None

        if steps_to_skip is None:
            steps_to_skip = []

        if steptable is None:
            if not self.data.has_steps:
                logging.debug("step-table is not made")

                if self.force_step_table_creation or self.force_all:
                    logging.debug("creating step-table for")
                    logging.debug(self.data.loaded_from)
                    self.make_step_table()

                else:
                    logging.info("ERROR! Cannot use get_step_numbers: you must create your step-table first")
                    return None

        # check if steptype is valid
        steptype = steptype.lower()
        steptypes = []
        helper_step_types = ["ocv", "charge_discharge"]
        valid_step_type = True
        if steptype in self.list_of_step_types:
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
            st = self.data.steps
        else:
            st = steptable
        shdr = self.headers_step_table

        # Retrieving cycle numbers (if cycle_number is None, it selects all cycles)
        if cycle_number is None:
            cycle_numbers = self.get_cycle_numbers(steptable=steptable)
        else:
            if isinstance(cycle_number, collections.abc.Iterable):
                cycle_numbers = cycle_number
            else:
                cycle_numbers = [cycle_number]

        if trim_taper_steps is not None:
            trim_taper_steps = -trim_taper_steps
            logging.debug("taper steps to trim given")

        if pdtype:
            if trim_taper_steps:
                logging.info(
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
                    logging.debug(f"Cycle {cycle} | StepType {s}: Not present!")
                else:
                    # Get the step numbers
                    step = st[mask_type_and_cycle][step_hdr].tolist()
                    for newstep in step[:trim_taper_steps]:
                        if newstep in steps_to_skip:
                            logging.debug(f"skipping step {newstep}")
                        else:
                            steplist.append(int(newstep))

            if not steplist:
                steplist = [0]
            out[cycle] = steplist
        return out

    @staticmethod
    def _select_without(
        data=None,
        headers_normal=None,
        headers_step_table=None,
        exclude_types=None,
        exclude_steps=None,
        replace_nan=True,
    ):
        steps = data.steps
        raw = data.raw.copy()

        # unravel the headers:
        d_n_txt = headers_normal.data_point_txt
        v_n_txt = headers_normal.voltage_txt
        c_n_txt = headers_normal.cycle_index_txt
        s_n_txt = headers_normal.step_index_txt
        i_n_txt = headers_normal.current_txt
        ch_n_txt = headers_normal.charge_capacity_txt
        dch_n_txt = headers_normal.discharge_capacity_txt

        d_st_txt = headers_step_table.point
        v_st_txt = headers_step_table.voltage
        c_st_txt = headers_step_table.cycle
        i_st_txt = headers_step_table.current
        ch_st_txt = headers_step_table.charge
        dch_st_txt = headers_step_table.discharge
        t_st_txt = headers_step_table.type
        s_st_txt = headers_step_table.step

        _first = "_first"
        _last = "_last"
        _delta_label = "_diff"

        # TODO: implement also for energy and power (and probably others as well) - this will
        #  require changing step-table to also include energy and power etc. If implementing
        #  this, you should also include diff in the step-table. You should preferably also use this
        #  opportunity to also make both the headers in the tables as well as the names used for
        #  the headers more aligned (e.g. for header_normal.data_point_txt -> header_normal.point;
        #  "cycle_index" -> "cycle")

        # TODO: @jepe - this method might be a bit slow for large datasets - consider using
        #  more "native" pandas methods and get rid of all looping (need some timing to check first)

        last_data_points = steps.loc[:, [c_st_txt, d_st_txt + _last]].groupby(c_st_txt).last().values.ravel()
        last_items = raw[d_n_txt].isin(last_data_points)
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

    def create_selector(self, selector_type=None, exclude_types=None, exclude_steps=None):
        if selector_type == "non-cv":
            exclude_types = ["cv_"]
        elif selector_type == "non-rest":
            exclude_types = ["rest_"]
        elif selector_type == "non-ocv":
            exclude_types = ["ocv_"]
        elif selector_type == "only-cv":
            exclude_types = ["charge", "discharge"]
        selector = functools.partial(
            self._select_without,
            data=self.data,
            headers_normal=self.headers_normal,
            headers_step_table=self.headers_step_table,
            exclude_types=exclude_types,
            exclude_steps=exclude_steps,
        )
        return selector

    def _generate_absolute_summary_columns(self, data, _first_step_txt, _second_step_txt) -> core.Data:
        summary = data.summary
        summary[self.headers_summary.coulombic_efficiency] = 100 * summary[_second_step_txt] / summary[_first_step_txt]
        summary[self.headers_summary.cumulated_coulombic_efficiency] = summary[
            self.headers_summary.coulombic_efficiency
        ].cumsum()

        capacity_columns = {
            self.headers_summary.charge_capacity: summary[self.headers_normal.charge_capacity_txt],
            self.headers_summary.discharge_capacity: summary[self.headers_normal.discharge_capacity_txt],
        }
        summary = summary.assign(**capacity_columns)

        calculated_from_capacity_columns = {
            self.headers_summary.cumulated_charge_capacity: summary[self.headers_summary.charge_capacity].cumsum(),
            self.headers_summary.cumulated_discharge_capacity: summary[
                self.headers_summary.discharge_capacity
            ].cumsum(),
            self.headers_summary.discharge_capacity_loss: (
                summary[self.headers_summary.discharge_capacity].shift(1)
                - summary[self.headers_summary.discharge_capacity]
            ),
            self.headers_summary.charge_capacity_loss: (
                summary[self.headers_summary.charge_capacity].shift(1) - summary[self.headers_summary.charge_capacity]
            ),
            self.headers_summary.coulombic_difference: (summary[_first_step_txt] - summary[_second_step_txt]),
        }

        summary = summary.assign(**calculated_from_capacity_columns)

        calculated_from_coulombic_efficiency_columns = {
            self.headers_summary.cumulated_coulombic_difference: summary[
                self.headers_summary.coulombic_difference
            ].cumsum(),
        }

        summary = summary.assign(**calculated_from_coulombic_efficiency_columns)
        calculated_from_capacity_loss_columns = {
            self.headers_summary.cumulated_discharge_capacity_loss: summary[
                self.headers_summary.discharge_capacity_loss
            ].cumsum(),
            self.headers_summary.cumulated_charge_capacity_loss: summary[
                self.headers_summary.charge_capacity_loss
            ].cumsum(),
        }
        summary = summary.assign(**calculated_from_capacity_loss_columns)

        individual_edge_movement = summary[_first_step_txt] - summary[_second_step_txt]
        shifted_charge_capacity_column = {
            self.headers_summary.shifted_charge_capacity: individual_edge_movement.cumsum(),
        }
        summary = summary.assign(**shifted_charge_capacity_column)

        shifted_discharge_capacity_column = {
            self.headers_summary.shifted_discharge_capacity: summary[self.headers_summary.shifted_charge_capacity]
            + summary[_first_step_txt],
        }
        summary = summary.assign(**shifted_discharge_capacity_column)
        ric = (summary[_first_step_txt].shift(1) - summary[_second_step_txt]) / summary[_second_step_txt].shift(1)
        ric_column = {self.headers_summary.cumulated_ric: ric.cumsum()}
        summary = summary.assign(**ric_column)
        summary[self.headers_summary.cumulated_ric] = ric.cumsum()
        ric_sei = (summary[_first_step_txt] - summary[_second_step_txt].shift(1)) / summary[_second_step_txt].shift(1)
        ric_sei_column = {self.headers_summary.cumulated_ric_sei: ric_sei.cumsum()}
        summary = summary.assign(**ric_sei_column)
        ric_disconnect = (summary[_second_step_txt].shift(1) - summary[_second_step_txt]) / summary[
            _second_step_txt
        ].shift(1)
        ric_disconnect_column = {self.headers_summary.cumulated_ric_disconnect: ric_disconnect.cumsum()}
        data.summary = summary.assign(**ric_disconnect_column)

        return data

    def _c_rates_to_summary(self, data: core.Data) -> core.Data:
        logging.debug("Extracting C-rates")

        def rate_to_cellpy_units(rate):
            conversion_factor = core.Q(1.0, self.data.raw_units["current"]) / core.Q(1.0, self.cellpy_units["current"])
            conversion_factor = conversion_factor.to_reduced_units().magnitude
            return rate * conversion_factor

        summary = data.summary
        steps = self.data.steps

        charge_steps = steps.loc[
            steps.type == "charge",
            [self.headers_step_table.cycle, self.headers_step_table.rate_avr],
        ].rename(columns={self.headers_step_table.rate_avr: self.headers_summary.charge_c_rate})

        charge_steps = charge_steps.drop_duplicates(subset=[self.headers_step_table.cycle], keep="first")
        charge_steps[self.headers_summary.charge_c_rate] = rate_to_cellpy_units(
            charge_steps[self.headers_summary.charge_c_rate]
        )

        summary = summary.merge(
            charge_steps,
            left_on=self.headers_summary.cycle_index,
            right_on=self.headers_step_table.cycle,
            how="left",
        ).drop(columns=self.headers_step_table.cycle)

        discharge_steps = steps.loc[
            steps.type == "discharge",
            [self.headers_step_table.cycle, self.headers_step_table.rate_avr],
        ].rename(columns={self.headers_step_table.rate_avr: self.headers_summary.discharge_c_rate})

        discharge_steps = discharge_steps.drop_duplicates(subset=[self.headers_step_table.cycle], keep="first")
        discharge_steps[self.headers_summary.discharge_c_rate] = rate_to_cellpy_units(
            discharge_steps[self.headers_summary.discharge_c_rate]
        )
        summary = summary.merge(
            discharge_steps,
            left_on=self.headers_summary.cycle_index,
            right_on=self.headers_step_table.cycle,
            how="left",
        ).drop(columns=self.headers_step_table.cycle)
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
            logging.info(f"Using these cycles for finding the nominal capacity: {normalization_cycles}")
            if not isinstance(normalization_cycles, (list, tuple)):
                normalization_cycles = [normalization_cycles]

            cap_ref = summary.loc[
                summary[self.headers_normal.cycle_index_txt].isin(normalization_cycles),
                _first_step_txt,
            ]
            if not cap_ref.empty:
                nom_cap = cap_ref.mean()
            else:
                logging.info(f"Empty reference cycle(s)")

        normalized_cycle_index_column = {
            self.headers_summary.normalized_cycle_index: summary[self.headers_summary.cumulated_charge_capacity]
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

        logging.debug("finding ir")
        only_zeros = summary[self.headers_normal.discharge_capacity_txt] * 0.0
        discharge_steps = self.get_step_numbers(
            steptype="discharge",
            allctypes=False,
        )
        charge_steps = self.get_step_numbers(
            steptype="charge",
            allctypes=False,
        )
        ir_indexes = []
        ir_values = []
        ir_values2 = []
        for i in summary.index:
            # selecting the appropriate cycle
            cycle = summary.iloc[i][self.headers_normal.cycle_index_txt]
            step = discharge_steps[cycle]
            if step[0]:
                ir = raw.loc[
                    (raw[self.headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[self.headers_normal.step_index_txt] == step[0]),
                    self.headers_normal.internal_resistance_txt,
                ]
                # This will not work if there are more than one item in step
                ir = ir.values[0]
            else:
                ir = 0
            step2 = charge_steps[cycle]
            if step2[0]:
                ir2 = raw[
                    (raw[self.headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[self.headers_normal.step_index_txt] == step2[0])
                ][self.headers_normal.internal_resistance_txt].values[0]
            else:
                ir2 = 0
            ir_indexes.append(i)
            ir_values.append(ir)
            ir_values2.append(ir2)
        ir_frame = only_zeros + ir_values
        ir_frame2 = only_zeros + ir_values2
        summary.insert(0, column=self.headers_summary.ir_discharge, value=ir_frame)
        summary.insert(0, column=self.headers_summary.ir_charge, value=ir_frame2)
        data.summary = summary
        return data

    def _end_voltage_to_summary(self, data):
        # needs to be fixed so that end-voltage also can be extracted
        # from the summary
        ev_t0 = time.time()
        raw = data.raw
        summary = data.summary

        logging.debug("finding end-voltage")
        logging.debug(f"dt: {time.time() - ev_t0}")
        only_zeros_discharge = summary[self.headers_normal.discharge_capacity_txt] * 0.0
        only_zeros_charge = summary[self.headers_normal.charge_capacity_txt] * 0.0
        logging.debug("need to collect discharge steps")
        discharge_steps = self.get_step_numbers(steptype="discharge", allctypes=False)
        logging.debug(f"dt: {time.time() - ev_t0}")
        logging.debug("need to collect charge steps")
        charge_steps = self.get_step_numbers(steptype="charge", allctypes=False)
        logging.debug(f"dt: {time.time() - ev_t0}")
        endv_indexes = []
        endv_values_dc = []
        endv_values_c = []
        logging.debug("starting iterating through the index")
        for i in summary.index:
            cycle = summary.iloc[i][self.headers_normal.cycle_index_txt]
            step = discharge_steps[cycle]

            # finding end voltage for discharge
            if step[-1]:  # selecting last
                end_voltage_dc = raw[
                    (raw[self.headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[self.headers_normal.step_index_txt] == step[-1])
                ][self.headers_normal.voltage_txt]
                # This will not work if there are more than one item in step
                end_voltage_dc = end_voltage_dc.values[-1]  # selecting
            else:
                end_voltage_dc = 0  # could also use numpy.nan

            # finding end voltage for charge
            step2 = charge_steps[cycle]
            if step2[-1]:
                end_voltage_c = raw[
                    (raw[self.headers_normal.cycle_index_txt] == cycle)
                    & (data.raw[self.headers_normal.step_index_txt] == step2[-1])
                ][self.headers_normal.voltage_txt]
                end_voltage_c = end_voltage_c.values[-1]
            else:
                end_voltage_c = 0
            endv_indexes.append(i)
            endv_values_dc.append(end_voltage_dc)
            endv_values_c.append(end_voltage_c)

        ir_frame_dc = only_zeros_discharge + endv_values_dc
        ir_frame_c = only_zeros_charge + endv_values_c
        data.summary.insert(0, column=self.headers_summary.end_voltage_discharge, value=ir_frame_dc)
        data.summary.insert(0, column=self.headers_summary.end_voltage_charge, value=ir_frame_c)

        return data

    def make_core_summary(
        self,
        data,
        nom_cap_abs=1.0,
        select_columns=True,
        find_ir=True,
        find_end_voltage=False,
        sort_my_columns=True,
        normalization_cycles=None,
        selector=None,
        **kwargs,
    ):

        time_00 = time.time()
        logging.debug("start making summary")

        summary = selector()
        column_names = summary.columns
        # TODO @jepe: use pandas.DataFrame properties instead (.len, .reset_index), but maybe first
        #  figure out if this is really needed and why it was implemented in the first place.
        summary_length = len(summary[column_names[0]])
        summary.index = list(range(summary_length))

        if select_columns:
            logging.debug("keeping only selected set of columns")
            columns_to_keep = [
                self.headers_normal.charge_capacity_txt,
                self.headers_normal.cycle_index_txt,
                self.headers_normal.data_point_txt,
                self.headers_normal.datetime_txt,
                self.headers_normal.discharge_capacity_txt,
                self.headers_normal.test_time_txt,
            ]
            for cn in column_names:
                if not columns_to_keep.count(cn):
                    try:
                        summary.pop(cn)
                    except KeyError:
                        logging.debug(f"could not pop {cn}")

        data.summary = summary

        # ----------------- calculated values -----------------------

        if self.cycle_mode == "anode":
            logging.info("Assuming cycling in anode half-data (discharge before charge) mode")
            _first_step_txt = self.headers_summary.discharge_capacity
            _second_step_txt = self.headers_summary.charge_capacity
        else:
            logging.info("Assuming cycling in full-data / cathode mode")
            _first_step_txt = self.headers_summary.charge_capacity
            _second_step_txt = self.headers_summary.discharge_capacity

        # ---------------- absolute -------------------------------

        data = self._generate_absolute_summary_columns(data, _first_step_txt, _second_step_txt)

        # TODO @jepe: refactor this to method:
        if find_end_voltage:
            data = self._end_voltage_to_summary(data)

        if find_ir and (self.headers_normal.internal_resistance_txt in data.raw.columns):
            data = self._ir_to_summary(data)

        # data = self._equivalent_cycles_to_summary(data, _first_step_txt, _second_step_txt, nom_cap_abs, normalization_cycles)
        #
        # # getting the C-rates, using values from step-table (so it will not be changed
        # # even though you provide make_summary with a new nom_cap unfortunately):
        # data = self._c_rates_to_summary(data)
        #
        # if sort_my_columns:
        #     logging.debug("sorting columns")
        #     new_first_col_list = [
        #         self.headers_normal.datetime_txt,
        #         self.headers_normal.test_time_txt,
        #         self.headers_normal.data_point_txt,
        #         self.headers_normal.cycle_index_txt,
        #     ]
        #     data.summary = self.set_col_first(data.summary, new_first_col_list)

        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
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

    def get_cycle_numbers(
        self,
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

        logging.debug("getting cycle numbers")

        if steptable is None:
            d = self.data.raw
            cycles = d[self.headers_normal.cycle_index_txt].dropna().unique()
            steptable = self.data.steps
        else:
            logging.debug("steptable is given as input parameter")
            cycles = steptable[self.headers_step_table.cycle].dropna().unique()

        if rate is None:
            return cycles

        logging.debug("filtering on rate")

        if rate is None:
            rate = 0.05

        if rate_std is None:
            rate_std = 0.1 * rate

        if rate_on is None:
            rate_on = ["charge", "discharge"]
        rates = self.get_rates(steptable=steptable, agg=rate_agg, direction=rate_on)
        rate_column = self.headers_step_table.rate_avr
        cycles_mask = (rates[rate_column] < (rate + rate_std)) & (rates[rate_column] > (rate - rate_std))

        if inverse:
            cycles_mask = ~cycles_mask

        filtered_rates = rates[cycles_mask]
        filtered_cycles = filtered_rates[self.headers_step_table["cycle"]].unique()

        return filtered_cycles
