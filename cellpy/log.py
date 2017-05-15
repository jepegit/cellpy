"""Set up logger instance"""


import os
import json
import logging.config
import logging
import warnings


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
            if not os.path.isdir(custom_log_dir):
                warnings.warn("could not set custom log-dir - non-existing directory")
            else:
                for file_handler in ["error_file_handler", "info_file_handler",
                                     "debug_file_handler"]:
                    try:
                        file_name = config["handlers"][file_handler]["filename"]
                        config["handlers"][file_handler]["filename"] = os.path.join(custom_log_dir,file_name)
                    except Exception as e:
                        warnings.warn("could not set custom log-dir" + str(e))

        if default_level:
            # set "root": {"level": "INFO",} to default_level
            w_txt = "could not set custom default level for logger"
            if not default_level in ["INFO", "DEBUG"]:
                warnings.warn(w_txt + "\nonly 'INFO' and 'DEBUG' is supported as default_level")
            else:
                try:
                    # setting root level
                    config["root"]["level"] = default_level
                    # setting streaming level
                    config["handlers"]["console"]["level"] = default_level
                    if default_level == "DEBUG":
                        config["handlers"]["console"]["formatter"] = "stamped"

                except Exception as e:
                    warnings.warn(w_txt + "\n" +str(e))


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
