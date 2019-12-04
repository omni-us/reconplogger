#!/usr/bin/env bash

set -e;
SD="$( dirname "${BASH_SOURCE[0]}" )";
cd "$SD/../../";

if [ $(which virtualenv | wc -l) != 0 ]; then
  virtualenv -p python3 venv_build;
  . venv_build/bin/activate;
fi

rm -f dist/*.whl;
./setup.py clean;
./setup.py bdist_wheel;
