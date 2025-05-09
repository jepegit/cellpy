#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for PyPI packaging

This script is used for creating the PyPI package.

$ python setup.py sdist # create gzip distr (source dist)
$ python setup.py bdist_wheel # create build
$ twine upload dist/* # upload to PyPI
"""
import os

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

included_packages = find_packages(
    exclude=[
        "build",
        "docs",
        "templates",
        "tests",
        "examples",
        "dev_data",
        "dev_utils",
        "testdata",
        "recipe",
        ".github",
        ".pytest_cache",
    ]
)

# TODO: update this
requirements = [
    "scipy",
    "numpy",
    "pandas",
    "python-box",
    "setuptools",
    "ruamel.yaml",
    "matplotlib",
    "openpyxl",
    "click",
    "PyGithub",
    "tqdm",
    "pint",
    "requests",
    # 'pyodbc;platform_system=="windows"',
    "pyodbc",
    "sqlalchemy>=2.0.0",
    'sqlalchemy-access;platform_system=="windows"',
    "python-dotenv",
    "fabric",
    "dateparser",
    "cookiecutter",
    "jinja2_time",
    "tables",  # depends on HDF5 that is not available by pip
    "ipykernel",
    "rich",
    "charset-normalizer",
]

test_requirements = [
    "lmfit",
    "pytest",
]

extra_req_batch = ["ipython", "jupyter", "plotly", "seaborn", "kaleido==0.1.*"]
extra_req_fit = ["lmfit"]
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

description = "Extract and manipulate data from battery data testers."

setup(
    name=name,
    version=version_ns["__version__"],
    description=description,
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Jan Petter Maehlen",
    author_email="jepe@ife.no",
    url="https://github.com/jepegit/cellpy",
    packages=included_packages,
    package_dir={"cellpy": "cellpy"},
    package_data={
        "parameters": [".cellpy_prms_default.conf"],
        "utils/data": ["*.h5"],
    },
    entry_points={"console_scripts": ["cellpy=cellpy.cli:cli"]},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="cellpy",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
)
