import logging

import pandas as pd

from cellpy.utils.batch_tools.batch_core import BaseAnalyzer
from cellpy.utils.ocv_rlx import select_ocv_points
from cellpy.exceptions import UnderDefined


class ICAAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class EISAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class OCVRelaxationAnalyzer(BaseAnalyzer):
    """Analyze open curcuit relaxation curves.

    This analyzer is still under development.
    (Partly) implented so far: select_ocv_points -> farms.
    To get the DataFrames from the farms, you can use
    >>> ocv_point_frames = OCVRelaxationAnalyzer.last

    Attributes (for select_ocv_points):
        selection_method: criteria for selecting points
            martin: select first and last, and then last/2, last/2/2 etc.
                until you have reached the wanted number of points.
            fixed_time: select first, and then
            defaults to "martin"
        number_of_points: number of points you want.
            defaults to 5
        interval: interval between each point (in use only for methods
            where interval makes sense). If it is a list, then
            number_of_points will be calculated as len(interval) + 1 (and
            override the set number_of_points).
            defaults to 10
        relative_voltage: set to True if you would like the voltage to be
            relative to the voltage before starting the ocv rlx step.
            Defaults to False. Remark that for the initial rxl step (when
            you just have put your cell on the tester) does not have any
            prior voltage. The relative voltage will then be versus the
            first measurement point.
            defaults to False
        report_times: also report the ocv rlx total time if True (defaults
            to False)
        direction ("up", "down" or "both"): select "up" if you would like
            to process only the ocv rlx steps where the voltage is relaxing
            upwards and vize versa. Defaults to "both

    To-do:
        - include better engine-dumper methodology and dump
            stuff to both memory and file(s)
            (should add this to BaseAnalyser)
        - recieve settings and parameters
        - option (dumper) for plotting?
        - automatic fitting of OCV rlx data?
    """

    def __init__(self):
        super().__init__()
        self.engines = []
        self.dumpers = []
        self.current_engine = None
        self._assign_engine(self.ocv_points_engine)
        # self._assign_dumper(self.screen_dumper)
        # prms for select_ocv_points
        self.selection_method = "martin"
        self.number_of_points = 5
        self.interval = 10
        self.relative_voltage = False
        self.report_times = False
        self.direction = None

    def _assign_engine(self, engine):
        self.engines.append(engine)

    def _assign_dumper(self, dumper):
        self.dumpers.append(dumper)

    def screen_dumper(self, **kwargs):
        for farm in self.farms:
            print(farm)

    @property
    def last(self):
        return self.farms[-1]

    def run_engine(self, engine):
        logging.debug(f"start engine::{engine.__name__}]")

        self.current_engine = engine

        self.farms, self.barn = engine(
            experiments=self.experiments,
            farms=self.farms
        )
        logging.debug("::engine ended")

    def run_dumper(self, dumper):
        logging.debug(f"start dumper::{dumper.__name__}]")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )
        logging.debug("::dumper ended")

    def do(self):
        if not self.experiments:
            raise UnderDefined("cannot run until "
                               "you have assigned an experiment")

        for engine in self.engines:
            self.empty_the_farms()
            logging.debug(f"running - {str(engine)}")
            self.run_engine(engine)

            for dumper in self.dumpers:
                logging.debug(f"exporting - {str(dumper)}")
                self.run_dumper(dumper)

    def ocv_points_engine(self, **kwargs):
        experiments = kwargs["experiments"]
        farms = kwargs["farms"]
        barn = None
        for experiment, farm in zip(experiments, farms):
            for cell_label in experiment.cell_data_frames:
                logging.info(f"Analyzing {cell_label}")
                if experiment.all_in_memory:
                    logging.debug("CellpyData picked from memory")
                    cell = experiment.cell_data_frames[cell_label]
                    if cell.empty:
                        logging.warning("Oh-no! Empty CellpyData-object")
                else:
                    logging.debug("CellpyData loaded from Cellpy-file")
                    cell = experiment.data[cell_label]
                    if cell.empty:
                        logging.warning("Oh-no! Empty CellpyData-object")

                df = select_ocv_points(
                    cell,
                    selection_method=self.selection_method,
                    number_of_points=self.number_of_points,
                    interval=self.interval,
                    relative_voltage=self.relative_voltage,
                    report_times=self.report_times,
                    direction=self.direction,
                )
                farm.append(df)

        return farms, barn

    def do2(self):
        for experiment, farm in zip(self.experiments, self.farms):
            for cell_label in experiment.cell_data_frames:
                logging.info(f"Analyzing {cell_label}")
                if experiment.all_in_memory:
                    logging.debug("CellpyData picked from memory")
                    cell = experiment.cell_data_frames[cell_label]
                    if cell.empty:
                        logging.warning("Oh-no! Empty CellpyData-object")
                else:
                    logging.debug("CellpyData loaded from Cellpy-file")
                    cell = experiment.data[cell_label]
                    if cell.empty:
                        logging.warning("Oh-no! Empty CellpyData-object")

                df = select_ocv_points(
                    cell,
                    selection_method=self.selection_method,
                    number_of_points=self.number_of_points,
                    interval=self.interval,
                    relative_voltage=self.relative_voltage,
                    report_times=self.report_times,
                    direction=self.direction,
                )
                farm.append(df)
        return self.farms



