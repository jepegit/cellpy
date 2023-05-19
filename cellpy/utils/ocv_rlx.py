import datetime
import logging
import time
import warnings

try:
    from lmfit import Model, Parameters, minimize, report_ci, report_fit
except ImportError as e:
    logging.warning(
        "Could not import lmfit. This is needed " "for fitting (run pip install lmfit)."
    )
    logging.debug(e)

import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cellpy import cellreader

# TODO: (28.05.2017 jepe) Docstrings are missing!!!!!!!! - AU: fix!


# some utility functions


# TODO: (05.10.2019 jepe) This function is slow due to use of loops. Should fix it.
def select_ocv_points(
    cellpydata,
    cycles=None,
    cell_label=None,
    include_times=True,
    selection_method="martin",
    number_of_points=5,
    interval=10,
    relative_voltage=False,
    report_times=False,
    direction="both",
):
    """Select points from the ocvrlx steps.

    Args:
        cellpydata: ``CellpyData-object``
        cycles: list of cycle numbers to process (optional)
        cell_label (str): optional, will be added to the frame if given
        include_times (bool): include additional information including times.
        selection_method ('martin' | 'fixed_times'): criteria for selecting points ('martin': select first and last, and
            then last/2, last/2/2 etc. until you have reached the wanted number of points; 'fixed_times': select first,
            and then same interval between each subsequent point).
        number_of_points: number of points you want.
        interval: interval between each point (in use only for methods
            where interval makes sense). If it is a list, then
            number_of_points will be calculated as len(interval) + 1 (and
            override the set number_of_points).
        relative_voltage: set to True if you would like the voltage to be
            relative to the voltage before starting the ocv rlx step.
            Defaults to False. Remark that for the initial rxl step (when
            you just have put your cell on the tester) does not have any
            prior voltage. The relative voltage will then be versus the
            first measurement point.
        report_times: also report the ocv rlx total time if True (defaults
            to False)
        direction ("up", "down" or "both"): select "up" if you would like
            to process only the ocv rlx steps where the voltage is relaxing
            upwards and vice versa. Defaults to "both".

    Returns:
        ``pandas.DataFrame`` (and another ``pandas.DataFrame`` if return_times is True)

    """

    if cycles is None:
        cycles = cellpydata.get_cycle_numbers()
    else:
        if not isinstance(cycles, (list, tuple)):
            cycles = [cycles]

    if not isinstance(interval, (list, tuple)):
        interval = [float(interval) for _ in range(number_of_points - 1)]

    ocv_rlx_id = "ocvrlx"

    step_table = cellpydata.data.steps
    dfdata = cellpydata.data.raw

    ocv_steps = step_table.loc[step_table["cycle"].isin(cycles), :]
    ocv_steps = ocv_steps.loc[ocv_steps.type.str.startswith(ocv_rlx_id, na=False), :]

    if selection_method in ["fixed_times", "fixed_points", "selected_times"]:
        number_of_points = len(interval) + 1

    headers2 = []
    for j in range(number_of_points):
        n = str(j).zfill(2)
        headers2.append(f"point_{n}")

    # doing an iteration (thought I didn't have to, but...) (fix later)

    results_list = list()
    info_dict = {"dt": [], "dv": [], "method": []}

    iter_range = number_of_points - 1
    if selection_method == "martin":
        iter_range -= 1

    # very slow:
    for index, row in ocv_steps.iterrows():
        # voltage
        first, last, delta = (
            row["voltage_first"],
            row["voltage_last"],
            row["voltage_delta"],
        )

        voltage_reference = 0.0

        if relative_voltage:
            if index > 0:
                reference_row = step_table.iloc[index - 1, :]
                voltage_reference = reference_row["voltage_last"]

            else:
                voltage_reference = first
                logging.warning("STEP 0: Using first point as ref voltage")

        # time
        start, end, duration = (
            row["step_time_first"],
            row["step_time_last"],
            row["step_time_delta"],
        )

        cycle, step = (row["cycle"], row["step"])
        info = row["type"]

        v_df = dfdata.loc[
            (dfdata["cycle_index"] == cycle) & (dfdata["step_index"] == step),
            ["step_time", "voltage"],
        ]

        poi = []

        _end = end
        _start = start

        t = datetime.timedelta(seconds=round(end - start, 0))

        info_dict["method"].append(selection_method)
        info_dict["dt"].append(t)
        info_dict["dv"].append(first - last)

        if report_times:
            print(f"Cycle {cycle}:", end=" ")
            print(f"dt = {str(t)}, dv = {first-last:6.3f}")

        for i, j in enumerate(range(max(1, iter_range))):
            if selection_method == "martin":
                # logging.debug("using the 'martin'-method")
                _end = _end / 2.0
                poi.append(_end)

            elif selection_method == "fixed_times":
                logging.debug(f"using fixed times with interval {interval[i]}")
                _start = _start + interval[i]
                logging.debug(f"time: {_start}")
                poi.append(_start)
            else:
                # more methods to come?
                logging.info("this method is not implemented")
                return None

        if selection_method == "martin":
            poi.reverse()

        df_poi = pd.DataFrame({"step_time": poi})
        df_poi["voltage"] = np.nan

        v_df = pd.concat([v_df, df_poi], ignore_index=True)
        v_df = v_df.sort_values("step_time").reset_index(drop=True)
        v_df["new"] = v_df["voltage"].interpolate()

        voi = []
        for p in poi:
            _v = v_df.loc[v_df["step_time"].isin([p]), "new"].values
            _v = _v - voltage_reference
            voi.append(_v[0])

        poi.insert(0, start)
        voi.insert(0, first - voltage_reference)
        if selection_method == "martin":
            poi.append(end)
            voi.append(last - voltage_reference)

        d1 = {"cycle": cycle}
        d2 = {h: [v] for h, v in zip(headers2, voi)}
        d = {**d1, **d2}
        result = pd.DataFrame(d)
        result["step"] = step
        result["type"] = info
        results_list.append(result)

        if "t0" not in info_dict:
            for i, p in enumerate(poi):
                info_dict[f"t{i}"] = [p]
        else:
            for i, p in enumerate(poi):
                info_dict[f"t{i}"].append(p)
    final = pd.concat(results_list)

    if direction == "down":
        final = final.loc[final["type"] == "ocvrlx_down", :]
    elif direction == "up":
        final = final.loc[final["type"] == "ocvrlx_up", :]

    if cell_label is not None:
        final = final.assign(cell=cell_label)
    final = final.reset_index(drop=True)

    if include_times:
        try:
            info_pd = pd.DataFrame(info_dict)
            final = pd.concat(
                [info_pd, final],
                axis=1,
            )
            final = final.reset_index(drop=True)
        except Exception as e:
            logging.info("could not create dataframe with time information")
            logging.info(e)
    return final


class MultiCycleOcvFit:
    """Object for performing fitting of multiple cycles.

    Remarks:
        This is only tested for OCV relaxation data for half-cells in anode mode
        where the OCV relaxation is performed according to the standard protocol
        implemented at IFE in the battery development group.

        If you want to use this for other data or protocols, please report an issue
        on the GitHub page.

    """
    def __init__(self, cellpydata, cycles, circuits=3):
        """Object for performing fitting of multiple cycles.

        Args:
            cellpydata: ``CellpyCell-object``
            cycles (list): cycles to fit.
            circuits (int): number of circuits to use in fitting.
        """
        self._cycles = cycles
        self.data = cellpydata
        self.circuits = circuits

        self.fit_cycles = []
        self.result = []
        self.best_fit_data = []
        self.best_fit_parameters = []
        self.best_fit_parameters_translated = []

    @property
    def cycles(self):
        return self._cycles

    @cycles.setter
    def cycles(self, value):
        if isinstance(value, int):
            self._cycles = [value]
        elif isinstance(value, list):
            self._cycles = value
        else:
            raise TypeError("cycles must be int or list of ints")

    def set_data(self, cellpydata):
        """Sets the CellpyCell."""

        self.data = cellpydata

    def set_cycles(self, cycles):
        """Sets the cycles."""

        self.cycles = cycles

    def run_fitting(self, direction="up", weighted=True):
        """

        Args:
            direction ('up' | 'down'): what type of ocv relaxation to fit
            weighted (bool): use weighted fitting.

        Returns:
            None

        """

        # TODO @jepe: refactor and use col names directly from HeadersNormal instead:

        ocv_fitter = OcvFit()
        ocv_fitter.set_circuits(self.circuits)
        time_voltage = self.data.get_ocv(direction=direction, cycles=self.cycles[0])
        time_step = time_voltage.step_time
        voltage = time_voltage.voltage
        if voltage is not None and time_step is not None:
            ocv_fitter.set_data(time_step, voltage)
        else:
            ocv_fitter.set_data([0, 1, 2, 3], [2, 2, 2, 2])

        try:
            ocv_fitter.create_model()
        except AttributeError as e:
            print(e)
            return

        for cycle in self.cycles:
            print("Fitting cycle " + str(cycle))
            if cycle == 1 and direction == "down":
                remove_first = True
            else:
                remove_first = False
            time_voltage = self.data.get_ocv(direction=direction, cycles=cycle, remove_first=remove_first)
            time_step = time_voltage.step_time
            voltage = time_voltage.voltage

            if voltage is not None:
                try:
                    end_current, end_voltage = self.find_zero(cycle, direction)
                except IndexError as e:
                    warnings.warn(f"Could not find zero current and voltage for cycle {cycle}")
                    print(e)
                else:
                    ocv_fitter.set_zero_voltage(end_voltage)
                    ocv_fitter.set_zero_current(end_current)
                    ocv_fitter.set_data(time_step, voltage)
                    if weighted:
                        ocv_fitter.set_weights_power_law()

                    try:
                        ocv_fitter.run_fit()
                    except Exception as e:
                        print(f"COULD NOT FIT CYCLE {cycle}")
                        print(e)
                    else:
                        self.fit_cycles.append(cycle)
                        self.result.append(ocv_fitter.get_result())
                        self.best_fit_parameters.append(ocv_fitter.get_best_fit_parameters())
                        self.best_fit_parameters_translated.append(
                            ocv_fitter.get_best_fit_parameters_translated()
                        )
                        self.best_fit_data.append(ocv_fitter.get_best_fit_data())

    def find_zero(self, cycle, direction):
        step_table = self.data.data.steps
        hdr = self.data.headers_step_table
        end_current = 0
        end_voltage = 0
        if direction == "up":
            end_voltage = step_table[
                (step_table["cycle"] == cycle)
                & (step_table["type"].isin(["discharge"]))
                ][hdr.voltage + "_last"].values[0]

            end_current = step_table[
                (step_table["cycle"] == cycle)
                & (step_table["type"].isin(["discharge"]))
                ][hdr.current + "_last"].values[0]

        elif direction == "down":
            end_voltage = step_table[
                (step_table["cycle"] == cycle)
                & (step_table["type"].isin(["charge"]))
                ][hdr.voltage + "_last"].values[0]

            end_current = step_table[
                (step_table["cycle"] == cycle)
                & (step_table["type"].isin(["charge"]))
                ][hdr.current + "_last"].values[0]

        return end_current, end_voltage

    def get_best_fit_data(self):
        """Returns the best fit data."""
        return self.best_fit_data

    def get_best_fit_parameters(self) -> list:
        """Returns parameters for the best fit."""
        return self.best_fit_parameters

    def get_best_fit_parameters_translated(self) -> list:
        """Returns the parameters in 'real units' for the best fit."""
        return self.best_fit_parameters_translated

    def get_best_fit_parameters_grouped(self) -> dict:
        """Returns a dictionary of the best fit."""
        result_dict = dict()
        result_dict["ocv"] = [
            parameters["ocv"] for parameters in self.best_fit_parameters
        ]

        for i in range(self.circuits):
            result_dict["t" + str(i)] = [
                parameters["t" + str(i)] for parameters in self.best_fit_parameters
            ]
            result_dict["w" + str(i)] = [
                parameters["w" + str(i)] for parameters in self.best_fit_parameters
            ]
        return result_dict

    def get_best_fit_parameters_translated_grouped(self) -> dict:
        """Returns the parameters as a dictionary of the 'real units'
        for the best fit."""
        result_dict = dict()
        result_dict["ocv"] = [
            parameters["ocv"] for parameters in self.best_fit_parameters_translated
        ]
        result_dict["ir"] = [
            parameters["ir"] for parameters in self.best_fit_parameters_translated
        ]

        for i in range(self.circuits):
            result_dict["r" + str(i)] = [
                parameters["r" + str(i)]
                for parameters in self.best_fit_parameters_translated
            ]
            result_dict["c" + str(i)] = [
                parameters["c" + str(i)]
                for parameters in self.best_fit_parameters_translated
            ]
        return result_dict

    def get_fit_cycles(self):
        """Returns a list of the fit cycles"""
        return self.fit_cycles

    @staticmethod
    def create_colormap(name="plasma", cycles=None):
        if cycles is None:
            cycles = np.arange(1, 101)
        colormap_proxy = np.array(cycles)
        colors = mpl.colormaps.get_cmap(name)
        norm = mpl.colors.Normalize(vmin=colormap_proxy.min(), vmax=colormap_proxy.max())
        cmap = mpl.cm.ScalarMappable(norm=norm, cmap=colors)
        cmap.set_array([])
        return cmap

    def plot_summary(self, cycles=None):
        """Convenience function for plotting the summary of the fit"""
        if cycles is None:
            cycles = self.get_fit_cycles()
        fig1 = plt.figure(tight_layout=True)
        gs = mpl.gridspec.GridSpec(3, 2, figure=fig1)
        ax1 = fig1.add_subplot(gs[:, 0])
        ax2 = fig1.add_subplot(gs[0, 1])
        ax3 = fig1.add_subplot(gs[1, 1])
        ax4 = fig1.add_subplot(gs[2, 1])

        ax1.set_title("Fit")
        ax2.set_title("OCV")
        ax3.set_title("Tau")
        ax3.set_yscale("log")
        ax4.set_title("Voltage Impact")

        plot_data = self.get_best_fit_data()
        cmap = self.create_colormap(cycles=cycles)
        for cycle in cycles:
            try:
                color = cmap.to_rgba(cycle)
                x = plot_data[cycle][0]
                y_measured = plot_data[cycle][1]
                y_fit = plot_data[cycle][2]
                ax1.plot(x, y_measured, "x", c=color)
                ax1.plot(x, y_fit, "-", c=color)
            except IndexError:
                pass
        fig1.colorbar(cmap, ax=ax1, label="Cycle")

        plot_data = self.get_best_fit_parameters_grouped()

        for i in range(self.circuits):
            ax3.plot(self.get_fit_cycles(), plot_data["t" + str(i)])
            ax4.plot(self.get_fit_cycles(), plot_data["w" + str(i)])

        ax2.plot(self.get_fit_cycles(), plot_data["ocv"])
        plt.tight_layout()

    def plot_summary_translated(self):
        """Convenience function for plotting the summary of the
        fit (translated)"""

        fig2 = plt.figure()
        ax1 = fig2.add_subplot(221)
        ax1.set_title("OCV (V)")
        ax2 = fig2.add_subplot(222)
        ax2.set_title("IR (Ohm)")
        ax3 = fig2.add_subplot(223)
        ax3.set_title("Resistances (Ohm)")
        ax4 = fig2.add_subplot(224)
        ax4.set_title("Capacitances (F)")
        ax4.set_yscale("log")

        plot_data = self.get_best_fit_parameters_translated_grouped()

        ax1.plot(self.get_fit_cycles(), plot_data["ocv"])
        ax2.plot(self.get_fit_cycles(), plot_data["ir"])

        for i in range(self.circuits):
            ax3.plot(self.get_fit_cycles(), plot_data["r" + str(i)])
            ax4.plot(self.get_fit_cycles(), plot_data["c" + str(i)])
        plt.tight_layout()
        plt.show()

    def summary_translated(self) -> pd.DataFrame:
        """Convenience function for creating a dataframe of the summary of the
        fit (translated)"""
        data = self.get_best_fit_parameters_translated_grouped()
        data["cycle"] = self.get_fit_cycles()
        df = pd.DataFrame(data)
        df = df.set_index("cycle")
        return df


class OcvFit(object):
    """Class for fitting open circuit relaxation data.

    The model is a sum of exponentials and a constant offset (Ohmic resistance).
    The number of exponentials is set by the number of circuits.
    The model is:
        v(t) = v0 + R0 + sum(wi * exp(-t/tau_i))
        where v0 is the OCV, wi is the weight of the exponential tau_i is the
        time constant of the exponential and R0 is the Ohmic resistance.

        r is found by calculating v0 / i_start --> err(r)= err(v0) + err(i_start).
        c is found from using tau / r --> err(c) = err(r) + err(tau).

    The fit is performed by using lmfit.

    Attributes:
        data (cellpydata-object): The data to be fitted.
        time (list): Time measured during relaxation (extracted from data if provided).
        voltage (list): Time measured during relaxation (extracted from data if provided).
        steps (str): Step information (if data is provided).
        circuits (int): The number of circuits to be fitted.
        weights (list): The weights of the different circuits.
        zero_current (float): Last current observed before turning the current off.
        zero_voltage (float): Last voltage observed before turning the current off.
        model (lmfit-object): The model used for fitting.
        params (lmfit-object): The parameters used for fitting.
        result (lmfit-object): The result of the fitting.
        best_fit_data (list): The best fit data [x, y_measured, y_fitted].
        best_fit_parameters (dict): The best fit parameters.

    Remarks:
        This class does not take advantage of the cellpydata-object. It is
        primarily used for fitting data that does not originate from cellpy,
        but it can also be used for fitting cellpy-data.

        If you have cellpy-data, you should use the MultiCycleOcvFit class instead.

    """

    def __init__(self, circuits=None, direction=None, zero_current=0.1, zero_voltage=0.05):
        """Initializes the class.

        Args:
            circuits (int): The number of circuits to be fitted (including R0).
            direction (str): The direction of the relaxation (up or down).
            zero_current (float): Last current observed before turning the current off.
            zero_voltage (float): Last voltage observed before turning the current off.
        """
        if circuits is None:
            self.circuits = 3
        else:
            self.circuits = circuits

        if direction is None:
            self.direction = "up"
        else:
            self.direction = direction

        if zero_current is None:
            warnings.warn("zero_current not set, using 0.1")
            self.zero_current = 0.1
        else:
            self.zero_current = zero_current

        if zero_voltage is None:
            warnings.warn("zero_voltage not set, using 0.05")
            self.zero_voltage = 0.05
        else:
            self.zero_voltage = zero_voltage

        self.data = None
        self.weights = None
        self.time = []
        self.voltage = []
        self.steps = None

        self.model = None
        self.params = Parameters()

        self.result = None
        self.best_fit_data = list()
        self.best_fit_parameters = dict()

    def set_cellpydata(self, cellpydata, cycle):
        """Convenience method for setting the data from a cellpydata-object.
        Args:
            cellpydata (CellpyCell): data object from cellreader
            cycle (int): cycle number to get from CellpyCell object

        Remarks:
            You need to set the direction before calling this method if you
            don't want to use the default direction (up).

        Returns:
            None

        """
        time_voltage = cellpydata.get_ocv(direction=self.direction, cycles=cycle)
        self.set_data(time_voltage.step_time, time_voltage.voltage)

    def set_data(self, t, v):
        """Set the data to be fitted."""
        self.time = np.array(t)
        self.voltage = np.array(v)

    def set_zero_current(self, zero_current):
        self.zero_current = zero_current

    def set_zero_voltage(self, zero_voltage):
        self.zero_voltage = zero_voltage

    def set_circuits(self, circuits):
        """Set the number of circuits to be used in the fit.

        Args:
            circuits (int): number of circuits to be used in the fit. Can be 1 to 4.
        """
        if circuits > 4:
            raise ValueError("Maximum number of circuits is 4.")
        if circuits < 1:
            raise ValueError("Minimum number of circuits is 1.")

        self.circuits = circuits

    def set_weights(self, weights):
        self.weights = weights

    def reset_weights(self):
        self.weights = None

    def set_weights_power_law(self, prefactor=1, power=-2, zero_level=1):
        if self.voltage is not None:
            self.weights = [
                prefactor * pow(t + 1, power) + zero_level for t in self.time
            ]
        else:
            raise NotImplementedError("Data is not set. Set data using set_data().")

    def create_model(self):
        """Create the model to be used in the fit."""

        # Setting starting values and bounds
        # ----------------------------------
        params = Parameters()
        # open circuit voltage (range 0-10V):
        params.add("ocv", value=self.voltage[-1], min=0, max=10)
        # time constants:
        taus = [math.pow(10, i) for i in range(self.circuits)]
        # weights (setting all to zero):
        weights = np.zeros(self.circuits)

        # populating the fit-parameters (lmfit)
        # -------------------------------------------------------------
        # tau0 and w0: this is for the first Ohmic resistance (R0)
        logging.info(f"Adding R circuit element (Ohmic resistance)")
        params.add("t0", value=taus[0], min=0.01)
        params.add("w0", value=weights[0])
        logging.info(f" added t0 with value {taus[0]}")
        logging.info(f" added w0 with value {weights[0]}")

        # tau1-4 and w1-4: this is for the RC circuit elements (Rn, Cn)
        for i in range(1, self.circuits):
            logging.info(f"Adding RC circuit element {i}")

            _delta = taus[i] - taus[i - 1]
            _delta_label = f"delta{i}"
            _delta_expression = f"delta{i}+t{i-1}"
            _t_label = f"t{i}"
            _w_label = f"w{i}"
            _w = weights[i]
            params.add(_delta_label, value=_delta, min=0.0)
            params.add(_t_label, expr=_delta_expression)
            params.add(_w_label, value=_w)

            logging.info(f" added {_delta_label} with value {_delta}")
            logging.info(f" added {_t_label} with expression {_delta_expression}")
            logging.info(f" added {_w_label} with value {_w}")

        for i in range(self.circuits, 5):
            logging.info(f"Adding RC circuit element {i}")

            _t_label = f"t{i}"
            _w_label = f"w{i}"
            params.add("t" + str(i), value=1, vary=False)
            params.add("w" + str(i), value=0, vary=False)

            logging.info(f" added {_t_label} with value 1 as fixed (i.e. not used)")
            logging.info(f" added {_w_label} with value 0 as fixed (i.e. not used)")

        self.params = params
        self.model = Model(self._model)

    @staticmethod
    def _model(t, ocv, t0, w0, t1, w1, t2, w2, t3, w3, t4, w4):
        # Calculates a voltage profile for the given
        # time array for a given set of parameters
        #
        # Model:
        # ------
        # v = ocv + w0*exp(-t/t0) + w1*exp(-t/t1) + w2*exp(-t/t2) + w3*exp(-t/t3) + w4*exp(-t/t4)
        #
        # t: time array
        # ocv: open circuit voltage
        # t0: time constant
        # w0: weight

        model = ocv
        model = (
            model
            + w0 * np.exp(-t / t0)
            + w1 * np.exp(-t / t1)
            + w2 * np.exp(-t / t2)
            + w3 * np.exp(-t / t3)
            + w4 * np.exp(-t / t4)
        )

        return model

    def fit_model(self):
        if self.model is not None:
            self.result = self.model.fit(
                self.voltage, weights=self.weights, t=self.time, params=self.params
            )
        else:
            raise NotImplementedError(
                "Model is not created. Set model using create_model()."
            )

        self.best_fit_parameters = self.result.best_values
        self.best_fit_data = [self.time, self.voltage, self.result.best_fit]

    def run_fit(self):
        """Performing fit of the OCV steps in the cycles set by set_cycles()
        from the data set by set_data()

        r is found by calculating v0 / i_start --> err(r)= err(v0) + err(i_start).

        c is found from using tau / r --> err(c) = err(r) + err(tau).

        The resulting best fit parameters are stored in self.result for the given cycles.

        Returns:
            None

        """

        # Check if data is set
        if self.time is []:
            self.result = []
            return

        try:
            self.fit_model()
        except ValueError as e:
            print(e)
        except AttributeError as e:
            print(e)

    def get_result(self):
        return self.result

    def get_best_fit_data(self):
        return self.best_fit_data

    def get_best_fit_parameters(self):
        return self.best_fit_parameters

    def get_best_fit_parameters_translated(self):
        result_dict = dict()
        result_dict["ocv"] = self.best_fit_parameters["ocv"]
        result_dict["ir"] = (
            -(
                (
                    self.best_fit_parameters["ocv"]
                    + self.best_fit_parameters["w0"]
                    + self.best_fit_parameters["w1"]
                    + self.best_fit_parameters["w2"]
                    + self.best_fit_parameters["w3"]
                    + self.best_fit_parameters["w4"]
                )
                - self.zero_voltage
            )
            / self.zero_current
        )

        for i in range(self.circuits):
            result_dict["r" + str(i)] = (
                self.best_fit_parameters["w" + str(i)] / self.zero_current
            )
            result_dict["c" + str(i)] = (
                self.best_fit_parameters["t" + str(i)] / result_dict["r" + str(i)]
            )

        return result_dict


def fit(c, direction="up", circuits=3, cycles=None, return_fit_object=False):
    """Fits the OCV steps in CellpyCell object c.

    Args:
        c: CellpyCell object
        direction: direction of the OCV steps ('up' or 'down')
        circuits: number of circuits to use (first is IR, rest is RC) in the fitting (min=1, max=4)
        cycles: list of cycles to fit (if None, all cycles will be used)
        return_fit_object: if True, returns the MultiCycleOcvFit instance.

    Returns:
        pd.DataFrame with the fitted parameters for each cycle if return_fit_object=False,
        else MultiCycleOcvFit instance
    """

    if cycles is None:
        cycles = c.get_cycle_numbers()

    # Fitting
    ocv_fit = MultiCycleOcvFit(c, cycles, circuits=circuits)
    ocv_fit.run_fitting(direction=direction)
    if not return_fit_object:
        return ocv_fit.summary_translated()
    return ocv_fit


def __single_fit(n=3):
    import os, sys, pathlib

    import matplotlib.pyplot as plt

    import cellpy

    print(50 * "=")
    print("FITTING OCV ROUTINES - TEST")
    print(50 * "-")
    # filename(s) and folders etc
    raw_file_name = pathlib.Path("../../testdata/data/20160805_test001_45_cc_01.res")

    # parameters about the run (mass (mg))
    mass = 0.982

    print(50 * "-")
    print("Loading data")
    print(50 * "-")

    print("loading file", end=" ")
    print(raw_file_name)

    # Loading dataframe
    c = cellpy.get(raw_file_name, mass=mass)

    # Fitting
    ocv_fit = OcvFit()
    ocv_fit.set_cellpydata(c, 1)
    ocv_fit.set_circuits(n)
    ocv_fit.create_model()
    ocv_fit.run_fit()

    # Plotting
    fig1, (ax1, ax2) = plt.subplots(2, 1, sharex="col", gridspec_kw={"height_ratios": [3, 1]})
    fig1.suptitle("Fit")

    x, y0, y1 = ocv_fit.get_best_fit_data()
    diff = 100*(y0 - y1)/y0
    ax1.plot(x, y0, "x", label="measured")
    ax1.plot(x, y1, "-",  label="fit")
    ax1.legend()
    ax2.plot(x, diff, "-", label="dV (%)")
    ax2.set_xlabel("time (s)")
    ax2.set_ylabel("dV (%)")
    ax1.set_ylabel("voltage (V)")
    print(ocv_fit.get_best_fit_parameters_translated())
    print(ocv_fit.result.fit_report())
    # plt.tight_layout()
    fig1.align_ylabels()
    plt.show()


def __fit(n=3):
    import os, sys, pathlib

    import matplotlib.pyplot as plt

    import cellpy

    print(50 * "=")
    print("FITTING OCV ROUTINES - TEST")
    print(50 * "-")
    # filename(s) and folders etc
    raw_file_name = pathlib.Path("../../testdata/data/20160805_test001_45_cc_01.res")
    single_cell = True

    # parameters about the run (mass (mg))
    mass = 0.982

    print(50 * "-")
    print("Loading data")
    print(50 * "-")

    print("loading file", end=" ")
    print(raw_file_name)

    # Loading dataframe
    c = cellpy.get(raw_file_name, mass=mass)
    # cycles to test:
    cycles = c.get_cycle_numbers()

    # Fitting
    ocv_fit = MultiCycleOcvFit(c, cycles, circuits=n)
    ocv_fit.run_fitting(direction="down")
    ocv_fit.plot_summary()
    ocv_fit.plot_summary_translated()

    # Printing best fit parameters
    for best_fit_parameters in ocv_fit.get_best_fit_parameters():
        print(50 * '-')
        print(best_fit_parameters)

    print("SUMMARY")
    print(50 * "-")
    print(ocv_fit.summary_translated())


if __name__ == "__main__":
    print("ocv-rlx".center(80, "="))
    __fit()
