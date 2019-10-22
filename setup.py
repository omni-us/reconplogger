#!/usr/bin/env python3

from setuptools import setup, Command

NAME = next(filter(lambda x: x.startswith('name = '), open('setup.cfg').readlines())).strip().split()[-1]

setup(version=__import__(NAME+'.__init__').__version__)
