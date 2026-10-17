#!/bin/bash
set -euo pipefail

echo "Financial repo hourly cron job start."
date
#this script is meant to be run hourly via cron to update the FRED tables in the database and any other scripts that need to be run once hourly

#resolve paths relative to this script's own location so no machine-specific absolute paths are committed to git
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting news_analyzer_1.py"
"$PROJECT_ROOT/.venv/bin/python" "$SCRIPT_DIR/news/news_analyzer_1.py"
date

echo "Financial repo hourly cron job end."
