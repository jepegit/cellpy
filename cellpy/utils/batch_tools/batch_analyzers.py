import logging

import pandas as pd

from cellpy.utils.batch_tools.batch_core import BaseAnalyzer
from cellpy.utils.ocv_rlx import select_ocv_points


class ICAAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class EISAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class OCVRelaxationAnalyzer(BaseAnalyzer):
    def __init__(self):
        """
        Attributes (inherited):
            experiments: list of experiments.
            farms: list of farms (one pr experiment)
                (containing pandas DataFrames or figs).
            barn (str): identifier for where to place the output-files.

        This analyzer is still under development.
        (Partly) implented so far: select_ocv_points -> farms

        Missing:
         - include the engine-dumper methodology and dump
        stuff to both memory and file(s) (should add this to BaseAnalyser)
         - recieve settings and parameters
         - option (dumper) for plotting?
         - automatic fitting of OCV rlx data?
        """
        super().__init__()

    def do(self):
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

                df = select_ocv_points(cell)
                farm.append(df)



