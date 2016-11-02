"""Set up logger instance"""


import os
import json
import logger.config


def setup_logging(default_path='logging.json', default_level=logger.INFO, env_key='LOG_CFG'):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logger.config.dictConfig(config)
    else:
        logger.basicConfig(level=default_level)
