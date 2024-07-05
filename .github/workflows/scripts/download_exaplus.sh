#!/usr/bin/env bash

set -euo pipefail

DIR="$1/downloads/EXAPLUS"
mkdir -p "$DIR"
curl -s https://x-up.s3.amazonaws.com/7.x/24.1.1/EXAplus-24.1.1.tar.gz \
    | tar -C "$DIR" --strip-components 2 -zxf -
