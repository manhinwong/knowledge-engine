#!/bin/bash
# Load project .env and run Letta server (uses venv so letta is found).
cd "$(dirname "$0")"
set -a
[ -f .env ] && source .env
set +a
exec ./venv/bin/letta server "$@"
