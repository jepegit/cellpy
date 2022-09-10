import logging

from cellpy import log, prms
from cellpy.parameters.internal_settings import get_headers_summary

log.setup_logging(default_level=logging.DEBUG, testing=True)


# TODO: finish this
def test_header(dataset):
    h = dataset.cell.summary.columns
    print(h)

    summary_headers = get_headers_summary()
    print(summary_headers)
    print(dir(summary_headers))
    s = summary_headers.get("discharge_capacity_raw")
    print(s)
