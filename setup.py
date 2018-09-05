from setuptools import setup, find_packages, Command
import subprocess
import os
from plogger import __version__

NAME = 'plogger'
VERSION = __version__
DESCRIPTION = 'omni:us python logging package'
LONG_DESCRIPTION = '\n\n'.join([
    open('README.md').read()])
AUTHOR = 'Nischal Padmanabha'
EMAIL = 'nischal@omnius.com'

REQUIRED = ['logmatic-python==0.1.7', 'python-json-logger==0.1.9']

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    license='Omnius Copyright'
)
