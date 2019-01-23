import logging
import warnings

from cellpy.utils.batch_tools.batch_core import BasePlotter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.exceptions import UnderDefined
from cellpy import prms

prms.BACKEND = "bokeh"


def summary_plotting_engine(**kwargs):
    """creates plots of summary data."""

    experiments = kwargs["experiments"]
    farms = kwargs["farms"]
    barn = None

    _preparing_data_for_plotting(
        experiments=experiments,
        farms=farms
    )

    _preparing_canvas()
    _plotting_data()

    print(f"Using {prms.BACKEND} for plotting")

    return farms, barn


def _preparing_data_for_plotting(**kwargs):
    # sub-engine
    experiments = kwargs["experiments"]
    farms = kwargs["farms"]

    for experiment in experiments:
        if not isinstance(experiment, CyclingExperiment):
            print(
                "No! This engine is only really good at"
                "processing CyclingExperiments"
            )
            print(experiment)
        else:
            print("processing")

    return farms


def _preparing_canvas(**kwargs):
    # sub-engine
    pass


def _plotting_data(**kwargs):
    # sub-engine
    pass


def exporting_plots(**kwargs):
    # dumper
    experiments = kwargs["experiments"]
    farms = kwargs["farms"]
    barn = kwargs["barn"]
    engine = kwargs["engine"]
    return None


class CyclingSummaryPlotter(BasePlotter):
    def __init__(self, *args):
        """
        Attributes (inherited):
            experiments: list of experiments.
            farms: list of farms (containing pandas DataFrames).
            barn (str): identifier for where to place the output-files.
        """

        super().__init__(*args)
        self.engines = list()
        self.dumpers = list()
        self._use_dir = None
        self.current_engine = None
        self._assign_engine(summary_plotting_engine)
        self._assign_dumper(exporting_plots)

    @property
    def columns(self):
        if len(self.experiments > 0):
            return self.experiments[0].summaries.columns.get_level_values(0)

    def _assign_engine(self, engine):
        self.engines.append(engine)

    def _assign_dumper(self, dumper):
        self.dumpers.append(dumper)

    def run_engine(self, engine):
        """run engine (once pr. experiment).

        Args:
            engine: engine to run (function or method).

        The method issues the engine command (with experiments and farms
        as input) that returns an updated farms as well as the barn and
        assigns them both to self.

        The farms attribute is a list of farms, i.e. [farm1, farm2, ...], where
        each farm contains pandas DataFrames.

        The barns attribute is a pre-defined string used for picking what
        folder(s) the file(s) should be exported to.
        For example, if barn equals "batch_dir", the the file(s) will be saved
        to the experiments batch directory.

        The engine(s) is given self.experiments and self.farms as input and
        returns farms to self.farms and barn to self.barn. Thus, one could
        in principle modify self.experiments within the engine without
        explicitly 'notifying' the poor soul who is writing a batch routine
        using that engine. However, it is strongly adviced not to do such
        things. And if you, as engine designer, really need to, then at least
        notify it through a debug (logger) statement.
        """

        logging.debug("running engine")

        self.current_engine = engine

        self.farms, self.barn = engine(
            experiments=self.experiments,
            farms=self.farms
        )

    def run_dumper(self, dumper):
        """run dumber (once pr. engine)

        Args:
            dumper: dumper to run (function or method).

        The dumper takes the attributes experiments, farms, and barn as input.
        It does not return anything. But can, if the dumper designer feels in
        a bad and nasty mood, modify the input objects
        (for example experiments).
        """

        logging.debug("running dumper")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )

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


class EISPlotter(BasePlotter):
    def __init__(self):
        super().__init__()

    def do(self):
        warnings.warn("not implemented yet")


if __name__ == '__main__':
    print("batch_plotters".center(80, "="))
    csp = CyclingSummaryPlotter()
    eisp = EISPlotter()
