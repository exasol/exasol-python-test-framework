#!/usr/bin/env bash

set -euo pipefail

mkdir -p "$1/downloads/EXAPLUS"
curl -s https://exasol-script-languages-dependencies.s3.eu-central-1.amazonaws.com/EXAplus-7.0.11.tar.gz | tar -C "$1/downloads/EXAPLUS" --strip-components 1 -zxf -
