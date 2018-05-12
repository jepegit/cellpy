"""
run.py is the entry to ef_common automation framework.
"""

import importlib
import inspect
import logging
import os
import sys
import traceback

from selenium.webdriver.remote.remote_connection import LOGGER

working_dir = os.path.dirname(os.path.abspath(__file__))
tests_dir = os.path.join(working_dir, 'tests')


def check_init_file(in_dir=tests_dir):
    for root, sub_folders, files in os.walk(in_dir):

        if '__init__.py' not in files:
            init_py = os.path.join(root, '__init__.py')
            open(init_py, 'a').close()

        for folder in sub_folders:
            check_init_file(folder)


def parse_arguments():
    if len(sys.argv) <= 1:
        return ['--help'], 'show_help'
    else:
        test_target = sys.argv[1:]
        return test_target, test_target[0]


def get_tests_in_module(module_path):
    from ef_common.base_testcase import BaseTestCase
    module_path = module_path.replace('.py', '')
    module = importlib.import_module(module_path)

    # get all class in this module
    class_objects = [v for k, v in module.__dict__.items() if
                     isinstance(v, type) and v.__module__ == module.__name__]

    # get all class inherits from BaseTestCase
    return [t.__name__ for t in class_objects if
            len(inspect.getmro(t)) > 2 and inspect.getmro(t)[::-1][1] == BaseTestCase]


def run_tests(args):
    os.environ['EF_COMMON_PROJECT_PATH'] = working_dir
    sys.path.insert(0, working_dir)

    try:
        from ef_common import main
        LOGGER.setLevel(logging.WARNING)
        if len(args) == 1 and args[0].endswith('.py'):
            args = get_tests_in_module(args[0])

        main.run_with(args)
    except ImportError:
        traceback.print_exc()
        raise Exception("No ef_common found! to install it execute: "
                        "'pip install ef_common --index-url http://jenkins.englishtown.com:8081/pypi -U'")


class TeamcityServiceMessages:
    """Message class to talk to pycharm plugin."""

    quote = {"'": "|'", "|": "||", "\n": "|n", "\r": "|r", ']': '|]'}

    def __init__(self, output=sys.stdout, prepend_linebreak=False):
        self.output = output
        self.prepend_linebreak = prepend_linebreak

    def escape_value(self, value):
        if sys.version_info[0] <= 2 and isinstance(value, unicode):
            s = value.encode('utf-8')
        else:
            s = str(value)
        return ''.join([self.quote.get(x, x) for x in s])

    def message(self, messageName, **properties):
        s = '##teamcity[' + messageName
        for k, v in properties.items():
            if v is None:
                continue
            s += " %s='%s'" % (k, self.escape_value(v))
        s += ']\n'

        if self.prepend_linebreak:
            self.output.write('\n')
        self.output.write(s)

    def test_suite_started(self, name, location=None):
        self.message('testSuiteStarted', name=name, locationHint=location)

    def test_suite_finished(self, name):
        self.message('testSuiteFinished', name=name)


if __name__ == '__main__':
    arguments, test_name = parse_arguments()
    m = TeamcityServiceMessages()
    m.test_suite_started(test_name)

    try:
        check_init_file()
        run_tests(arguments)
    finally:
        m.test_suite_finished(test_name)
