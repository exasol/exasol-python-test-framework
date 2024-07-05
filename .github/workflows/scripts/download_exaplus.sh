#!/usr/bin/env bash

set -euo pipefail

DIR="$1/downloads/EXAPLUS"
mkdir -p "$DIR"
# curl -s https://exasol-script-languages-dependencies.s3.eu-central-1.amazonaws.com/EXAplus-7.0.11.tar.gz | tar -C "$1/downloads/EXAPLUS" --strip-components 1 -zxf -
curl -s https://x-up.s3.amazonaws.com/7.x/24.1.1/EXAplus-24.1.1.tar.gz | tar -C "$DIR" --strip-components 2 -zxf -
