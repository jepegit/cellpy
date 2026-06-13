#!/usr/bin/env bash
# Build cellpy in a clean Docker container and smoke-test the built artifact.
#
# This mirrors what a fresh install of the published package would do: build
# the wheel, install it into an isolated environment, then import it and run
# the CLI. Use it to catch packaging problems (missing data files, broken
# entry points, bad metadata) before publishing.
set -euo pipefail

cd "$(dirname "$0")/.."

docker build -f docker/Dockerfile.build-test -t cellpy-build-test .

echo "Local build test passed."
