"""Set up logger instance"""


import os
import json
import logging.config
import logging


def setup_logging(default_json_path=None, default_level=None, env_key='LOG_CFG',
                  custom_log_dir=None):
    """Setup logging configuration

    """
    # finding the json log-config
    if not default_json_path:
        default_json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"logging.json")
    path = default_json_path
    value = os.getenv(env_key, None)
    if value:
        path = value

    # reading the json log-config file
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        # changing config if required by user
        if custom_log_dir:
            for key, value in config.iteritems():
                print key, value
            # set "error_file_handler": {"filename": "cellpy_errors.log",}
            # set "debug_file_handler": {"filename": "cellpy_errors.log",}
            # set "info_file_handler": {"filename": "cellpy_errors.log",}
            pass
        if not default_level:
            # set "root": {"level": "INFO",} to default_level
            pass

        logging.config.dictConfig(config)
    else:
        if not default_level:
            default_level = logging.INFO
        logging.basicConfig(level=default_level)

    # if custom_log_dir:
    #     log = logging.getLogger()  # root logger
    #     for hdlr in log.handlers[:]:  # remove all old handlers
    #         log.removeHandler(hdlr)
    #     log.addHandler(fileh)

if __name__ == '__main__':
    setup_logging()
