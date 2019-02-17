#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for PyPI packaging

This script is used for creating the PyPI package.
python setup.py sdist - create gzip distr (source dist)
python setup.py bdist_wheel - create build
twine upload dist/* - upload to PyPI
"""
from setuptools import setup, find_packages
import os

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

included_packages=find_packages(exclude=['build', 'docs', 'templates'])

requirements = [
    'scipy', 'numpy', 'pandas', 'python-box', 'setuptools', 'pyyaml',
    'matplotlib', 'xlrd', 'click', 'PyGithub',
    # 'pytables',
]

test_requirements = [
    'scipy', 'numpy', 'pandas', 'python-box', 'setuptools', 'pyyaml'
    'matplotlib', 'lmfit', 'pyodbc', 'xlrd', 'click', 'PyGithub',
    'pytables', 'pytest',
]


name = 'cellpy'

here = os.path.abspath(os.path.dirname(__file__))

userdir = os.path.expanduser("~")
# os.mkdir(os.path.join(userdir, ".cellpy"))

version_ns = {}
with open(os.path.join(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)


description = 'Extract data from battery cell testers.'

setup(name=name,
      version=version_ns['__version__'],
      description=description,
      long_description=readme + '\n\n' + history,
      author="Jan Petter Maehlen",
      author_email='jepe@ife.no',
      url='https://github.com/jepegit/cellpy',
      packages=included_packages,
      package_dir={'cellpy':'cellpy'},
      package_data={
        'cellpy':[],
            # 'README.rst'],
        'databases':
             ['databases/cellpy_db.xlxs',
             'databases/cellpy_dbc.xlxs',
             ],
        'indata':
            [
            ],
        'outdata':
            [
             ],
        'parameters':
            ['parameters/_cellpy_prms_default.ini',
             ],
        'scripts':
            ['examples/simple_reader.py',
             ],
             },
    entry_points={
        'console_scripts': [
            'cellpy=cellpy.cli:cli',
        ],
    },
    #data_files=[userdir, ['cellpy/parameters/_cellpy_prms_default.ini']],
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='cellpy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
