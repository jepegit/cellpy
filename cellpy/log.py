"""Set up logger instance"""

import os
import json
import logging.config
import logging
import warnings
from cellpy import prms


def setup_logging(default_json_path=None, default_level=None, env_key='LOG_CFG',
                  custom_log_dir=None):
    """Setup logging configuration

    """

    if not default_json_path:
        default_json_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "logging.json")
    path = default_json_path
    value = os.getenv(env_key, None)
    if value:
        path = value

    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)

        log_dir = os.path.abspath(prms.Paths["filelogdir"])

        if custom_log_dir:
            log_dir = custom_log_dir

        if not os.path.isdir(log_dir):
            warning_txt = ("\nCould not set custom log-dir - "
                           "non-existing directory"
                           f"\nDir: {log_dir}"
                           "\nUsing current directory instead: "
                           f"{os.getcwd()}")
            logging.warning(warning_txt)
            log_dir = os.getcwd()

        for file_handler in ["error_file_handler", "info_file_handler",
                             "debug_file_handler"]:
            try:
                file_name = config["handlers"][file_handler]["filename"]
                logging.debug("Setting file handlers for logging.")
                logging.debug(f"Filename: {file_name}")
                logging.debug(f"Full path: {os.path.join(log_dir,file_name)}")
                # print(f"Filename: {file_name}")
                # print(f"Full path: {os.path.join(log_dir,file_name)}")
                config["handlers"][file_handler][
                    "filename"] = os.path.join(log_dir,
                                               file_name)
            except Exception as e:
                warnings.warn("\nCould not set custom log-dir" + str(e))

        if default_level:
            w_txt = "\nCould not set custom default level for logger"
            if default_level not in [
                "INFO", "DEBUG", logging.INFO, logging.DEBUG
            ]:
                _txt = "\nonly 'INFO' and 'DEBUG' is supported"
                _txt += " as default_level"
                warnings.warn(w_txt + _txt)

            else:
                try:
                    config["handlers"]["console"]["level"] = default_level
                    if default_level in ["DEBUG", logging.DEBUG]:
                        config["handlers"]["console"]["formatter"] = "stamped"

                except Exception as e:
                    warnings.warn(w_txt + "\n" + str(e))

        logging.config.dictConfig(config)
    else:
        if not default_level:
            default_level = logging.INFO
        logging.basicConfig(level=default_level)


if __name__ == '__main__':
    setup_logging()
