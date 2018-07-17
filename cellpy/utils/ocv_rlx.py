from lmfit import Parameters, minimize, report_fit, Model, report_ci
import numpy as np
import math
import matplotlib.pyplot as plt
from cellpy import cellreader
import pandas as pd


# TODO: (28.05.2017 jepe) Tests are missing!!!!!!!! - AU: fix!
# TODO: (28.05.2017 jepe) Docstrings are missing!!!!!!!! - AU: fix!

class MultiCycleOcvFit(object):
    def __init__(self, cellpydata, cycles, circuits=3):
        """

        Args:
            cellpydata:
            cycles:
            circuits:
        """
        self.cycles = cycles
        self.data = cellpydata
        self.circuits = circuits

        self.fit_cycles = []
        self.result = []
        self.best_fit_data = []
        self.best_fit_parameters = []
        self.best_fit_parameters_translated = []

    def set_data(self, cellpydata):
        """Sets the CellpyData."""

        self.data = cellpydata

    def set_cycles(self, cycles):
        """Sets the cycles."""

        self.cycles = cycles

    def run_fitting(self, ocv_type='ocvrlx_up', weighted=True):
        """

        Args:
            ocv_type:
            weighted:

        Returns:

        """
        ocv_fitter = OcvFit()
        ocv_fitter.set_circuits(self.circuits)
        time, voltage = self.data.get_ocv(ocv_type=ocv_type,
                                          cycle_number=self.cycles[0])
        if voltage is not None and time is not None:
            ocv_fitter.set_data(time, voltage)
        else:
            ocv_fitter.set_data([0, 1, 2, 3], [2, 2, 2, 2])

        try:
            ocv_fitter.create_model()
        except AttributeError as e:
            print(e)
            return

        for cycle in self.cycles:
            print("Fitting cycle " + str(cycle))
            time, voltage = self.data.get_ocv(ocv_type=ocv_type,
                                              cycle_number=cycle)

            if voltage is not None:
                step_table = self.data.dataset.step_table  # hope it works...
                if ocv_type is 'ocvrlx_up':
                    end_voltage = step_table[(step_table['cycle'] == cycle) & (
                        step_table['type'].isin(['discharge']))][
                        'V_end'].values[0]
                    end_current = step_table[(step_table['cycle'] == cycle) & (
                        step_table['type'].isin(['discharge']))][
                        'I_end'].values[0]
                    ocv_fitter.set_zero_voltage(end_voltage)
                    ocv_fitter.set_zero_current(end_current)
                elif ocv_type is 'ocvrlx_down':
                    end_voltage = \
                        step_table[(step_table['cycle'] == cycle) & (
                            step_table['type'].isin(['charge']))][
                            'V_end'].values[
                            0]
                    end_current = \
                        step_table[(step_table['cycle'] == cycle) & (
                            step_table['type'].isin(['charge']))][
                            'I_end'].values[
                            0]
                    ocv_fitter.set_zero_voltage(end_voltage)
                    ocv_fitter.set_zero_current(end_current)

                ocv_fitter.set_data(time, voltage)
                if weighted:
                    ocv_fitter.set_weights_power_law()
                ocv_fitter.run_fit()

                self.fit_cycles.append(cycle)
                self.result.append(ocv_fitter.get_result())
                self.best_fit_parameters.append(
                    ocv_fitter.get_best_fit_parameters())
                self.best_fit_parameters_translated.append(
                    ocv_fitter.get_best_fit_parameters_translated())
                self.best_fit_data.append(ocv_fitter.get_best_fit_data())

    def get_best_fit_data(self):
        """Returns the best fit data."""
        return self.best_fit_data

    def get_best_fit_parameters(self):
        """Returns parameters for the best fit."""
        return self.best_fit_parameters

    def get_best_fit_parameters_translated(self):
        """Returns the parameters in 'real units' for the best fit."""
        return self.best_fit_parameters_translated

    def get_best_fit_parameters_grouped(self):
        """Returns a dictionary of the best fit."""
        result_dict = dict()
        result_dict['ocv'] = [parameters['ocv'] for parameters in
                              self.best_fit_parameters]

        for i in range(self.circuits):
            result_dict['t' + str(i)] = [parameters['t' + str(i)] for parameters
                                         in self.best_fit_parameters]
            result_dict['w' + str(i)] = [parameters['w' + str(i)] for parameters
                                         in self.best_fit_parameters]
        return result_dict

    def get_best_fit_parameters_translated_grouped(self):
        """Returns the parameters as a dictionary of the 'real units' for the best fit."""
        result_dict = dict()
        result_dict['ocv'] = [parameters['ocv'] for parameters in
                              self.best_fit_parameters_translated]
        result_dict['ir'] = [parameters['ir'] for parameters in
                             self.best_fit_parameters_translated]

        for i in range(self.circuits):
            result_dict['r' + str(i)] = [parameters['r' + str(i)] for parameters
                                         in self.best_fit_parameters_translated]
            result_dict['c' + str(i)] = [parameters['c' + str(i)] for parameters
                                         in self.best_fit_parameters_translated]
        return result_dict

    def get_fit_cycles(self):
        """Returns the fit cycles"""
        return self.fit_cycles

    def plot_summary(self, cycles=None):
        """Convenience function for plotting the summary of the fit"""
        if cycles is None:
            cycles = [0]
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(221)
        ax1.set_title('Fit')
        ax2 = fig1.add_subplot(222)
        ax2.set_title('OCV')
        ax3 = fig1.add_subplot(223)
        ax3.set_title('Tau')
        ax3.set_yscale("log")
        ax4 = fig1.add_subplot(224)
        ax4.set_title('Voltage Impact')

        plot_data = self.get_best_fit_data()
        for cycle in cycles:
            ax1.plot(plot_data[cycle][0], plot_data[cycle][1])
            ax1.plot(plot_data[cycle][0], plot_data[cycle][2])

        plot_data = self.get_best_fit_parameters_grouped()

        for i in range(self.circuits):
            ax3.plot(self.get_fit_cycles(), plot_data['t' + str(i)])
            ax4.plot(self.get_fit_cycles(), plot_data['w' + str(i)])

        ax2.plot(self.get_fit_cycles(), plot_data['ocv'])

    def plot_summary_translated(self):
        """Convenience function for plotting the summary of the
        fit (translated)"""

        fig2 = plt.figure()
        ax1 = fig2.add_subplot(221)
        ax1.set_title('OCV (V)')
        ax2 = fig2.add_subplot(222)
        ax2.set_title('IR (Ohm)')
        ax3 = fig2.add_subplot(223)
        ax3.set_title('Resistances (Ohm)')
        ax4 = fig2.add_subplot(224)
        ax4.set_title('Capacitances (F)')
        ax4.set_yscale("log")

        plot_data = self.get_best_fit_parameters_translated_grouped()
        print(plot_data['ocv'])
        print(plot_data['ir'])
        print(plot_data['r0'])

        ax1.plot(self.get_fit_cycles(), plot_data['ocv'])
        ax2.plot(self.get_fit_cycles(), plot_data['ir'])

        for i in range(self.circuits):
            ax3.plot(self.get_fit_cycles(), plot_data['r' + str(i)])
            ax4.plot(self.get_fit_cycles(), plot_data['c' + str(i)])

        plt.show()


class OcvFit(object):
    """Class for fitting open circuit relaxation data."""

    def __init__(self, zero_current=0.1, zero_voltage=0.05):
        self.data = None
        self.weights = None
        self.time = []
        self.voltage = []
        self.step_table = ''
        self.circuits = 3
        self.zero_current = zero_current
        self.zero_voltage = zero_voltage

        self.model = None
        self.params = Parameters()

        self.result = None
        self.best_fit_data = dict()
        self.best_fit_parameters = dict()

    def set_cellpydata(self, cellpydata, cycle):
        """Performing fit of the OCV steps in the cycles set by set_cycles()
        from the data set by set_data()

        r is found by calculating v0 / i_start --> err(r)= err(v0) + err(i_start).
        c is found from using tau / r --> err(c) = err(r) + err(tau)

        Args:
            cellpydata (CellpyData): data object from cellreader
            cycle (int): cycle number to get from CellpyData object

        Returns:
            None

        """
        self.data = cellpydata
        self.step_table = self.data.dataset  # hope it works...
        time, voltage = self.data.get_ocv(ocv_type='ocvrlx_up',
                                          cycle_number=cycle)
        self.time = np.array(time)
        self.voltage = np.array(voltage)

    def set_data(self, time, voltage):
        self.time = np.array(time)
        self.voltage = np.array(voltage)

    def set_zero_current(self, zero_current):
        self.zero_current = zero_current

    def set_zero_voltage(self, zero_voltage):
        self.zero_voltage = zero_voltage

    def set_circuits(self, circuits):
        self.circuits = circuits

    def set_weights(self, weights):
        self.weights = weights

    def reset_weights(self):
        self.weights = None

    def set_weights_power_law(self, prefactor=1, power=-2, zero_level=1):
        if self.voltage is not None:
            self.weights = [prefactor * pow(time + 1, power) + zero_level for
                            time in self.time]
        else:
            raise NotImplementedError(
                'Data is not set. Set data using set_data().')

    def create_model(self):
        params = Parameters()
        params.add('ocv', value=self.voltage[-1], min=0, max=10)
        taus = [math.pow(10, i) for i in range(self.circuits)]
        weights = np.zeros(self.circuits)

        params.add('t0', value=taus[0], min=0.01)
        params.add('w0', value=weights[0])

        for i in range(1, self.circuits):
            params.add('delta' + str(i), value=taus[i] - taus[i - 1], min=0.0)
            params.add('t' + str(i), expr='delta' + str(i) + '+t' + str(i - 1))
            params.add('w' + str(i), value=weights[i])
        for i in range(self.circuits, 5):
            params.add('t' + str(i), value=1, vary=False)
            params.add('w' + str(i), value=0, vary=False)

        self.params = params
        self.model = Model(self._model)

    @staticmethod
    def _model(time, ocv, t0, w0, t1, w1, t2, w2, t3, w3, t4, w4):
        # Calculates a voltage profile for the given
        # time array for a given set of parameters
        model = ocv
        model = model + w0 * np.exp(-time / t0) + w1 * np.exp(
            -time / t1) + w2 * np.exp(-time / t2) + w3 * np.exp(
            -time / t3) + w4 * np.exp(-time / t4)

        return model

    def fit_model(self):

        if self.model is not None:
            self.result = self.model.fit(self.voltage, weights=self.weights,
                                         time=self.time, params=self.params)
        else:
            raise NotImplementedError(
                'Model is not created. Set model using create_model().')

        self.best_fit_parameters = self.result.best_values
        self.best_fit_data = [self.time, self.voltage, self.result.best_fit]

    def run_fit(self):
        """Performing fit of the OCV steps in the cycles set by set_cycles()
        from the data set by set_data()

        r is found by calculating v0 / i_start --> err(r)= err(v0) + err(i_start).

        c is found from using tau / r --> err(c) = err(r) + err(tau)

        Returns:
            None: Resulting best fit parameters are stored in self.result for the given cycles

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
        result_dict['ocv'] = self.best_fit_parameters['ocv']
        result_dict['ir'] = -((self.best_fit_parameters['ocv'] +
                               self.best_fit_parameters['w0']
                               + self.best_fit_parameters['w1'] +
                               self.best_fit_parameters['w2']
                               + self.best_fit_parameters['w3'] +
                               self.best_fit_parameters['w4'])
                              - self.zero_voltage) / self.zero_current

        for i in range(self.circuits):
            result_dict['r' + str(i)] = self.best_fit_parameters[
                                            'w' + str(i)] / self.zero_current
            result_dict['c' + str(i)] = self.best_fit_parameters['t' + str(i)] / \
                                        result_dict['r' + str(i)]

        return result_dict


def _main():
    from cellpy import cellreader
    import os
    import matplotlib.pyplot as plt

    print(50 * "=")
    print("FITTING OCV ROUTINES - TEST")
    print(50 * "-")

    # filename(s) and folders etc
    resfilename = "20160809_TF7_A1_04_cc_02.res"
    resfilename = "20160216_snx001_01_cc_01.res"
    resfilename = "20160216_snx001_02_cc_01.res"
    resfilename = "20170310_snx002_03_cc_01.res"
    # resfilename = "20160306_snx001_09_cc_01.res"
    # resfilename = "20150501_TF7_A1_01_cc_01.res"
    resfilename = "20160805_test001_45_cc_01.res"
    resfilename = "20160306_snx001_07_cc_02.res"
    resfilename = "20160306_snx001_08_cc_02.res"
    resfilename = "20160306_snx001_10_cc_01.res"

    single_cell = False

    datafolder_in = r'..\data_ex'
    datafolder_out = r'..\outdata'

    # parameters about the run (mass (mg))
    mass = 0.982

    # cycles to test
    cycles = [i * 10 for i in range(1, 10)]
    cycles = [i * 1 for i in range(1, 100)]
    print(50 * "-")
    print("Loading data")
    print(50 * "-")

    print("loading file", end=' ')
    print(resfilename)

    # Loading dataframe
    d = cellreader.CellpyData()
    # noinspection PyDeprecation
    d.from_raw(os.path.join(datafolder_in, resfilename))
    d.set_mass(mass)
    d.make_step_table()

    if single_cell:
        # Sending data to ocv_fit object and running fit
        ocv_fit = OcvFit()
        ocv_fit.set_cellpydata(d, 1)
        ocv_fit.set_circuits(4)
        ocv_fit.create_model()
        ocv_fit.run_fit()

        fig1 = plt.figure()
        fig1.suptitle("Fit")
        ax1 = fig1.add_subplot(111)

        plot_data = ocv_fit.get_best_fit_data()
        ax1.plot(plot_data[0], plot_data[1])
        ax1.plot(plot_data[0], plot_data[2])

        plt.show()

    else:
        ocv_fit = MultiCycleOcvFit(d, cycles, circuits=3)
        ocv_fit.run_fitting(ocv_type="ocvrlx_up")
        ocv_fit.plot_summary([0])
        ocv_fit.plot_summary_translated()

        # # Printing best fit parameters
        # for best_fit_parameters in ocv_fit.get_best_fit_parameters():
        #     print 50 * '-'
        #     print best_fit_parameters


if __name__ == '__main__':
    _main()
