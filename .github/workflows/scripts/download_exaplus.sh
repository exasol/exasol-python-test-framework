#!/usr/bin/env bash

set -euo pipefail

mkdir -p "$1/downloads/EXAPLUS"
curl -s https://www.exasol.com/support/secure/attachment/155319/EXAplus-7.0.11.tar.gz | tar -C "$1/downloads/EXAPLUS" --strip-components 1 -zxf -
