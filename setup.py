#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for PyPI packaging

This script is used for creating the PyPI package.

$ python setup.py sdist # create gzip distr (source dist)
$ python setup.py bdist_wheel # create build
$ twine upload dist/* # upload to PyPI
"""
from setuptools import setup, find_packages
import os

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

included_packages = find_packages(exclude=["build", "docs", "templates"])

requirements = [
    "scipy",
    "numpy>=1.16.4",
    "pandas",
    "python-box",
    "setuptools",
    "ruamel.yaml",
    "matplotlib",
    "xlrd",
    "click",
    "PyGithub",
    "tqdm",
    'pyodbc;platform_system=="windows"',
    # 'pytables', # not available by pip
]

test_requirements = [
    "scipy",
    "numpy>=1.16.4",
    "pandas",
    "python-box",
    "setuptools",
    "ruamel.yaml",
    "matplotlib",
    "lmfit",
    "pyodbc",
    "xlrd",
    "click",
    "PyGithub",
    # 'pytables', # not available by pip
    "pytest",
    "tqdm",
]

extra_req_batch = ["ipython", "jupyter"]
extra_req_fit = ["lmfit", "matplotlib"]
extra_req_all = extra_req_batch + extra_req_fit

extra_requirements = {
    "batch": extra_req_batch,
    "fit": extra_req_fit,
    "all": extra_req_all,
}
name = "cellpy"

here = os.path.abspath(os.path.dirname(__file__))

user_dir = os.path.expanduser("~")

version_ns = {}
with open(os.path.join(here, name, "_version.py")) as f:
    exec(f.read(), {}, version_ns)

description = "Extract and manipulate data from battery cell testers."

setup(
    name=name,
    version=version_ns["__version__"],
    description=description,
    long_description=readme + "\n\n" + history,
    author="Jan Petter Maehlen",
    author_email="jepe@ife.no",
    url="https://github.com/jepegit/cellpy",
    packages=included_packages,
    package_dir={"cellpy": "cellpy"},
    package_data={"parameters": [".cellpy_prms_default.conf"]},
    entry_points={"console_scripts": ["cellpy=cellpy.cli:cli"]},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="cellpy",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
)
