#!/usr/bin/env python3

from setuptools import setup, Command
import os
import re

NAME = next(filter(lambda x: x.startswith('name = '), open('setup.cfg').readlines())).strip().split()[-1]

version_regex = r'__version__ = ["\']([^"\']*)["\']'
with open(os.path.join(NAME, '__version__.py'), 'r') as version_file:
    version_lines = version_file.read()
    match = re.search(version_regex, version_lines)


setup(version=match.group(1))
