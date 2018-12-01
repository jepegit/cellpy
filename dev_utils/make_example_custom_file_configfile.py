import pathlib
import logging
from pprint import pprint
import yaml

from cellpy.readers.instruments import custom


default_config = custom.DEFAULT_CONFIG

path = pathlib.Path()
ex_path = path.absolute() / "../cellpy/parameters/custom_format_example.yml"
ex_path = ex_path.resolve()


def _read(name):
    """read the yml file"""
    logging.debug("Reading config-file: %s" % name)
    try:
        with open(name, "r") as config_file:
            prm_dict = yaml.load(config_file)
    except yaml.YAMLError:
        raise yaml.YAMLErrorr
    else:
        return prm_dict


def _write(file_name=None):
    logging.debug("saving configuration to %s" % file_name)
    try:
        with open(file_name, "w") as config_file:
            yaml.dump(default_config, config_file, default_flow_style=False,
                      explicit_start=True, explicit_end=True)
    except yaml.YAMLError:
        raise Exception("Could not save file")


def main():

    _write(ex_path)

    if not ex_path.is_file():
        print(f"missing file: {ex_path}")
        return

    d = _read(ex_path)
    print(f"read: {ex_path}")
    pprint(d)


if __name__ == '__main__':
    main()
