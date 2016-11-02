"""Set up logger instance"""


import os
import json
import logging.config
import logging


def setup_logging(default_json_path=None, default_level=logging.INFO, env_key='LOG_CFG',
                  custom_log_dir=None):
    """Setup logging configuration

    """
    if not default_json_path:
        default_json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"logging.json")
    path = default_json_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
            # for key, value in config.iteritems():
            #     print key, value
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

    # if custom_log_dir:
    #     log = logging.getLogger()  # root logger
    #     for hdlr in log.handlers[:]:  # remove all old handlers
    #         log.removeHandler(hdlr)
    #     log.addHandler(fileh)

if __name__ == '__main__':
    setup_logging()
