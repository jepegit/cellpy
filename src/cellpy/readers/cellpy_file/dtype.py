"""dtype coercion helpers for cellpy-file step tables."""

from __future__ import annotations

import logging

from cellpy.readers import externals
from cellpy.parameters.internal_settings import get_headers_step_table


def fix_dtype_step_table(dataset):
    # used when saving to cellpy format
    hst = get_headers_step_table()
    try:
        cols = dataset.steps.columns
    except AttributeError:
        logging.info("Could not extract columns from steps")
        return
    for col in cols:
        if col not in [hst.cycle, hst.sub_step, hst.info]:
            dataset.steps[col] = dataset.steps[col].apply(
                externals.pandas.to_numeric
            )
        else:
            dataset.steps[col] = dataset.steps[col].astype("str")
    return dataset
