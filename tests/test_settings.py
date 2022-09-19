import logging

from cellpy import log
from cellpy.parameters.internal_settings import get_headers_normal, get_headers_summary

log.setup_logging(default_level="DEBUG", testing=True)


def test_get_headers_normal():
    headers = get_headers_normal()
    logging.debug(headers)
    assert headers["voltage_txt"] == "voltage"


def test_get_headers_summary():
    headers = get_headers_summary()
    logging.debug(headers)
    assert headers["discharge_capacity"] == "discharge_capacity"
    assert headers["discharge_capacity_gravimetric"] == "discharge_capacity_gravimetric"
    assert headers["discharge_capacity_areal"] == "discharge_capacity_areal"
    assert headers.get("discharge_capacity") == "discharge_capacity"
