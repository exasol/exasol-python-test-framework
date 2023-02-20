#!/usr/bin/env bash

set -euo pipefail

mkdir -p "$1/downloads/ODBC"
curl -s https://x-up.s3.amazonaws.com/7.x/7.1.17/EXASOL_ODBC-7.1.17.tar.gz | tar -C "$1/downloads/ODBC" --strip-components 1 -zxf -
