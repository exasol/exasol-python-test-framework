#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

source "$SCRIPT_DIR/poetry_utils.sh"

check_requirements

set -euo pipefail

init_poetry

if [ -n "$POETRY_BIN" ]
then
  PYTHONPATH=$SCRIPT_DIR/../.. $POETRY_BIN run python3 -u $SCRIPT_DIR/check_release.py
else
  echo "Could not find poetry!"
  exit 1
fi