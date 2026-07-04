#!/usr/bin/env bash
# Sync cellpy from uv.lock (PyPI cellpycore) and overlay a local editable
# cellpy-core checkout. Use when developing both repos side by side.
set -euo pipefail
cd "$(dirname "$0")/.."

CORE="../cellpy-core"
if [[ ! -f "${CORE}/pyproject.toml" ]]; then
  echo "error: expected cellpy-core checkout at ${CORE} (relative to cellpy root)" >&2
  exit 1
fi

uv sync --no-sources
uv pip install -e "${CORE}"
echo "Dev env ready: cellpy editable + cellpycore from ${CORE}"
