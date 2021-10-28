#!/usr/bin/env bash

set -euo pipefail

mkdir -p "$1/downloads/ODBC"
curl -s https://www.exasol.com/support/secure/attachment/155337/EXASOL_ODBC-7.0.11.tar.gz| tar -C "$1/downloads/ODBC" --strip-components 1 -zxf -
