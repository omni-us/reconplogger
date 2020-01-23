#!/usr/bin/env python3

from setuptools import setup, Command
import re

VERSION = next(filter(lambda x: x.startswith('__version__ = '), open('plogger.py').readlines())).strip().replace("'","").split()[-1]
NAME_TESTS = next(filter(lambda x: x.startswith('test_suite = '), open('setup.cfg').readlines())).strip().split()[-1]
LONG_DESCRIPTION = re.sub(':class:|:func:|:ref:', '', open('README.rst').read())
CMDCLASS = {}


## test_coverage target ##
try:
    import coverage

    class CoverageCommand(Command):
        description = 'print test coverage report'
        user_options = []  # type: ignore
        def initialize_options(self): pass
        def finalize_options(self): pass
        def run(self):
            cov = coverage.Coverage()
            cov.start()
            __import__(NAME_TESTS).run_tests()
            cov.stop()
            cov.save()
            cov.report()
            cov.html_report(directory='htmlcov')
            print('\nSaved html report to directory htmlcov')

    CMDCLASS['test_coverage'] = CoverageCommand

except Exception:
    print('warning: coverage package not found, test_coverage target will not be available.')


## build_sphinx target ##
try:
    from sphinx.setup_command import BuildDoc
    CMDCLASS['build_sphinx'] = BuildDoc

except Exception:
    print('warning: sphinx package not found, build_sphinx target will not be available.')


## Run setuptools setup ##
setup(version=VERSION,
      long_description=LONG_DESCRIPTION,
      cmdclass=CMDCLASS)
