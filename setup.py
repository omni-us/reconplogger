#!/usr/bin/env python3

from setuptools import setup

VERSION = next(filter(lambda x: x.startswith('__version__ = '), open('reconplogger.py').readlines())).strip().replace("'","").split()[-1]

setup(version=VERSION)
