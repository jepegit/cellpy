"""Set up logger instance"""

import datetime
import json
import logging
import logging.config
import os
import pathlib
import shutil
import tempfile
import warnings

from cellpy import prms

logging.raiseExceptions = False


def setup_logging(
    default_json_path=None,
    default_level=None,
    env_key="LOG_CFG",
    custom_log_dir=None,
    reset_big_log=False,
    max_size=5_000_000,
    testing=False,
):
    """Setup logging configuration.

    Args:
        default_level: default log-level to screen (std.out).
        default_json_path: path to config file for setting up logging.
        env_key (str): use this environment prm to try to get default_json_path.
        custom_log_dir: path for saving logs.
        reset_big_log (bool): reset log if too big (max_size).
        max_size (int): if reset_log, this is the max limit.
        testing (bool): set as True if testing, and you don't want to create any .log files

    """

    if not default_json_path:
        default_json_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "logging.json"
        )
    path = default_json_path
    value = os.getenv(env_key, None)
    if value:
        path = value

    if default_level is None:
        default_level = "CRITICAL"

    # loading logging configs
    if os.path.exists(path):
        with open(path, "rt") as f:
            config = json.load(f)

        if testing:
            log_dir = tempfile.mkdtemp()
        elif custom_log_dir:
            log_dir = custom_log_dir
        else:
            log_dir = os.path.abspath(prms.Paths.filelogdir)

        if not os.path.isdir(log_dir):
            warning_txt = (
                "\nCould not set custom log-dir - "
                "non-existing directory"
                f"\nDir: {log_dir}"
                "\nUsing current directory instead: "
                f"{os.getcwd()}"
            )
            logging.warning(warning_txt)
            log_dir = os.getcwd()

        for file_handler in [
            "error_file_handler",
            "info_file_handler",
            "debug_file_handler",
        ]:
            try:
                file_name = config["handlers"][file_handler]["filename"]
                logging.debug("Setting file handlers for logging.")
                logging.debug(f"Filename: {file_name}")
                logging.debug(f"Full path: {os.path.join(log_dir,file_name)}")
                # print(f"Filename: {file_name}")
                # print(f"Full path: {os.path.join(log_dir,file_name)}")
                config["handlers"][file_handler]["filename"] = os.path.join(
                    log_dir, file_name
                )

                if reset_big_log:
                    full_log_file_path = pathlib.Path(log_dir) / file_name
                    if full_log_file_path.is_file():
                        file_size = full_log_file_path.lstat().st_size
                        if file_size > max_size:
                            d_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
                            new_file_name = "_".join([d_str, file_name])
                            new_full_log_file_path = (
                                pathlib.Path(log_dir) / new_file_name
                            )
                            shutil.copy(full_log_file_path, new_full_log_file_path)
                    else:
                        logging.debug(
                            "Could not reset big log: could not find the file"
                        )

            except Exception as e:
                warnings.warn("\nCould not set custom log-dir" + str(e))

        if default_level:
            w_txt = "\nCould not set custom default level for logger"
            if default_level not in [
                "INFO",
                "DEBUG",
                "CRITICAL",
                logging.INFO,
                logging.DEBUG,
                logging.CRITICAL,
            ]:
                _txt = "\nonly 'INFO', 'DEBUG' and 'CRITICAL' is supported"
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
            default_level = logging.CRITICAL
        logging.basicConfig(level=default_level)


if __name__ == "__main__":
    setup_logging()
