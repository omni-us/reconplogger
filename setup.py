#!/usr/bin/env python3

from setuptools import setup, Command
import os
import re
import sys
import unittest


LONG_DESCRIPTION = re.sub(":class:|:func:|:ref:", "", open("README.rst").read())
CMDCLASS = {}


## test_coverage target ##
class CoverageCommand(Command):
    description = "run test coverage and generate html or xml report"
    user_options = []  # type: ignore

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            import coverage
        except ImportError:
            print("error: coverage package not found, run_test_coverage requires it.")
            sys.exit(True)
        cov = coverage.Coverage(source=["reconplogger"])
        cov.start()
        tests = unittest.defaultTestLoader.loadTestsFromName("reconplogger_tests")
        if not unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful():
            sys.exit(True)
        cov.stop()
        cov.save()
        cov.report()
        if "TEST_COVERAGE_XML" in os.environ:
            outfile = os.environ["TEST_COVERAGE_XML"]
            cov.xml_report(outfile=outfile)
            print("\nSaved coverage report to " + outfile + ".")
        else:
            cov.html_report(directory="htmlcov")
            print("\nSaved html coverage report to htmlcov directory.")


CMDCLASS["test_coverage"] = CoverageCommand


## build_sphinx target ##
try:
    from sphinx.setup_command import BuildDoc

    CMDCLASS["build_sphinx"] = BuildDoc  # type: ignore

except Exception:
    print(
        "warning: sphinx package not found, build_sphinx target will not be available."
    )


## Run setuptools setup ##
setup(long_description=LONG_DESCRIPTION, cmdclass=CMDCLASS)
