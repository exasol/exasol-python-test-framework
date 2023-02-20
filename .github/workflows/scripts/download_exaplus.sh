#!/usr/bin/env bash

set -euo pipefail

mkdir -p "$1/downloads/EXAPLUS"
curl -s https://x-up.s3.amazonaws.com/7.x/7.1.17/EXAplus-7.1.17.tar.gz | tar -C "$1/downloads/EXAPLUS" --strip-components 1 -zxf -
