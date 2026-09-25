#!/usr/bin/env bash
# Smoke test a built image through its packaged entrypoint. The image leaves the
# test suite out (see .dockerignore), so this checks what a user of the image
# runs. integration.yml runs it on every pull request, and deployment.yml
# before anything is pushed.
set -euo pipefail

image="${1:?usage: $0 IMAGE}"

docker run --rm "$image" --version
docker run --rm "$image" tijuana new_york
docker run --rm "$image" --list tbd

# Print the LOCAL column's zone and abbreviation, from the JSON output, which is
# the output meant to be parsed. Extra arguments go to ``docker run``.
local_column() {
    docker run --rm "$@" "$image" tijuana --hour 12 --format json |
        python3 -c '
import json, sys
column = json.load(sys.stdin)["columns"][0]
print(column["zone"], column["abbreviation"])
'
}

expect() {
    local description="$1" actual="$2"
    shift 2
    for wanted in "$@"; do
        if [ "$actual" = "$wanted" ]; then
            echo "ok: $description -> $actual"
            return
        fi
    done
    echo "FAIL: $description -> expected one of: $*, got: $actual" >&2
    exit 1
}

# A container has no timezone of its own.
expect 'no TZ' "$(local_column)" 'None UTC'

# TZ has to name the local zone. Madrid is CET or CEST depending on the date.
expect 'TZ=Europe/Madrid' "$(local_column -e TZ=Europe/Madrid)" \
    'Europe/Madrid CET' 'Europe/Madrid CEST'

# Again with both of the operating system's timezone lookups disabled: TZDIR for
# the C library, PYTHONTZPATH for zoneinfo. TZ must then come from the bundled
# tzdata wheel, whether or not the base image ships its own copy. Resolved by the
# C library instead, it silently becomes a zone called "Europe" at UTC+0.
expect 'TZ=Europe/Madrid without the OS timezone database' \
    "$(local_column -e TZ=Europe/Madrid -e TZDIR=/nonexistent -e PYTHONTZPATH=)" \
    'Europe/Madrid CET' 'Europe/Madrid CEST'
