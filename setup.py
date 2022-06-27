#!/usr/bin/env python3

from setuptools import setup, Command
import re
import sys


NAME_TESTS = next(filter(lambda x: x.startswith('test_suite = '), open('setup.cfg').readlines())).strip().split()[-1]
LONG_DESCRIPTION = re.sub(':class:|:func:|:ref:', '', open('README.rst').read())
CMDCLASS = {}


## test_coverage target ##
class CoverageCommand(Command):
    description = 'run test coverage and generate html or xml report'
    user_options = [
        ('xml=', None, 'Whether to generate xml report instead of html'),
    ]
    def initialize_options(self): self.xml = None
    def finalize_options(self): pass
    def run(self):
        try:
            import coverage
        except:
            print('error: coverage package not found, run_test_coverage requires it.')
            sys.exit(True)
        cov = coverage.Coverage(source=['reconplogger'])
        cov.start()
        __import__(NAME_TESTS).run_tests()
        cov.stop()
        cov.save()
        cov.report()
        if self.xml:
            cov.xml_report(outfile=self.xml)
            print('\nSaved coverage report to '+self.xml+'.')
        else:
            cov.html_report(directory='htmlcov')
            print('\nSaved html coverage report to htmlcov directory.')


CMDCLASS['test_coverage'] = CoverageCommand


## build_sphinx target ##
try:
    from sphinx.setup_command import BuildDoc
    CMDCLASS['build_sphinx'] = BuildDoc  # type: ignore

except Exception:
    print('warning: sphinx package not found, build_sphinx target will not be available.')


## Run setuptools setup ##
setup(long_description=LONG_DESCRIPTION,
      cmdclass=CMDCLASS)
