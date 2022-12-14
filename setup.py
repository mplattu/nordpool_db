#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='nordpool_db',
    version='0.1.0',
    description='Python library for finding the cheapest hours from Nord Pool spot prices.',
    author='mplattu',
    url='https://github.com/mplattu/nordpool_db',
    packages=[
        'nordpool_db',
    ],
    install_requires=[
        'pytz>=2022.5',
        'requests>=2.27.1',
        'nordpool>=0.3.3',
    ])