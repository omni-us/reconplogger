#!/usr/bin/env bash

set -e;
SD="$( dirname "${BASH_SOURCE[0]}" )";

## Default values ##
VENV_DIR="venv_test";
PIP_OPTS="--extra-index-url https://pypi.omnius.com";
CACHE_DIR="";
COVERAGE="";
WHEEL="dist/*.whl";

## Help message ##
tool_help () {
  echo "
Usage: test_wheel.sh [OPTIONS]

OPTIONS:
  --venv DIR               Directory for virtual environment (def.=$VENV_DIR).
  --pip OPTS               Options for pip (def.=$PIP_OPTS).
  --cache DIR              Set to use given directory for pip download cache (def.=none).
  --coverage XML           Generate coverage report in xml format in given path (def.=$COVERAGE).
  --wheel PATH             Wheel file to test (def.=$WHEEL).
  -h | --help              Print this message and exit.
";
}

## Parse input arguments ##
while [ "$#" -gt 0 ]; do
  case "$1" in
    --venv )       VENV_DIR="$2";  shift;  ;;
    --pip )        PIP_OPTS="$2";  shift;  ;;
    --cache )      CACHE_DIR="$2"; shift;  ;;
    --coverage )   COVERAGE="$2";  shift;  ;;
    --wheel )      WHEEL="$2";     shift;  ;;
    -h | --help )  tool_help;      exit 0; ;;
    * )            tool_help;      exit 1; ;;
  esac
  shift;
done

## Create virtual environment ##
if [ $(which virtualenv | wc -l) != 0 ] && [ "$VENV_DIR" != "" ] && [ ! -d "$VENV_DIR" ]; then
  virtualenv -p python3 "$VENV_DIR";
  . "$VENV_DIR/bin/activate";
else
  PIP_OPTS+=" --user";
fi
if [ "$CACHE_DIR" != "" ]; then
  PIP_OPTS+=" --cache-dir $CACHE_DIR";
fi

## Resolve required info ##
WHEEL=$(ls $WHEEL);
pip3 install $PIP_OPTS $(sed -n '/^# requirements:/{ s|.*:||; p; }' "$SD/wheel_info.py");
PROJECT=$("$SD/wheel_info.py" project $WHEEL);

## Install and test with optional dependencies ##
pip3 install $PIP_OPTS $WHEEL[all,test];
python3 -m ${PROJECT}_tests;

## Generate coverage report ##
if [ "$COVERAGE" != "" ]; then
  pip3 install $PIP_OPTS coverage;
  python3 -m coverage run -m ${PROJECT}_tests;
  python3 -m coverage report;
  python3 -m coverage xml -o "$COVERAGE";
fi
