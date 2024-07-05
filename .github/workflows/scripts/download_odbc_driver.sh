#!/usr/bin/env bash

set -euo pipefail

DIR="$1/downloads/ODBC"
mkdir -p "$DIR"
# curl -s https://exasol-script-languages-dependencies.s3.eu-central-1.amazonaws.com/EXASOL_ODBC-7.0.11.tar.gz | tar -C "$1/downloads/ODBC" --strip-components 1 -zxf -
curl -s https://x-up.s3.amazonaws.com/7.x/24.1.1/Exasol_ODBC-24.1.1-Linux_x86_64.tar.gz  | tar -C "$DIR" --strip-components 2 -zxf -
find "$DIR" -name libexaodbc\*.so
