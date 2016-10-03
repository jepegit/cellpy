#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for PyPI packaging

This script is used for creating the PyPI package.
python setup.py sdist - create gzip distr (source dist)
python setup.py bdist_wheel - create build
twine upload dist/* - upload to PyPI
"""
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

included_packages=find_packages(exclude=['build', 'docs', 'templates'])

requirements = [
    'pyodbc', 'scipy', 'numpy', 'pandas', 'matplotlib',
]

test_requirements = [
    'pyodbc', 'scipy', 'numpy', 'pandas',
]

setup(name='cellpy', version='0.1.0', description='Extract data from battery cell testers.',
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
        'scripts':
            ['scripts/simple_reader.py',
             # 'scripts/make_hdf5.py',
             # 'scripts/FetchArbinData.py',
             # 'scripts/batchplot.py',
             ],
             },
    entry_points={
        'console_scripts': [
            'cellpy=cellpy.cli:main'
        ]
    },
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
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
