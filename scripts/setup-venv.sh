#!/bin/bash
set -ex

SCRIPTS_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
export STADE_ROOT_DIR="$SCRIPTS_PATH/.."

pushd "$STADE_ROOT_DIR"

rm -rf ./env

python3.7 -m venv ./env

. ./env/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

pip install -e .

echo "To activate virtualenv, run:"
echo ". $STADE_ROOT_DIR/env/bin/activate"
