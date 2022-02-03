import pytest
import logging
import pandas as pd
from cellpy import log
from cellpy.utils import ica
from cellpy.exceptions import NullData

log.setup_logging(default_level=logging.DEBUG, testing=True)


# TODO: manually renaming cellpy fixture to cell; remove this when all instances of dataset is renamed to cell
@pytest.fixture
def cell(dataset):
    return dataset


def test_first_cycle_irreversible_capacity(cell):
    pass

