import logging

from cellpy import log
from cellpy.parameters.internal_settings import get_headers_normal

log.setup_logging(default_level="DEBUG", testing=True)


def test_get_headers_normal():
    headers = get_headers_normal()
    logging.debug(headers)
    assert headers["voltage_txt"] == "voltage"
