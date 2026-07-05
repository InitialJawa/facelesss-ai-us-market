#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set default log level
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Starting FACELess AI..."
python main.py "$@"
