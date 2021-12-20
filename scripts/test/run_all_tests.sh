#!/bin/bash 
   
COMMAND_LINE_ARGS=("${@}") 
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" 
 
source "$SCRIPT_DIR/../build/poetry_utils.sh"

check_requirements

set -euo pipefail

init_poetry

if [ -n "$POETRY_BIN" ]
then
  PYTHONPATH=. $POETRY_BIN run $SCRIPT_DIR/run_locally.sh --server "$1" --odbc-driver="$2"
else
  echo "Could not find poetry!"
  exit 1
fi

