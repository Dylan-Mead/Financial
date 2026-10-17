#!/bin/bash
echo "Financial repo daily cron job start."
date
#this script is meant to be run daily via cron to update the FRED tables in the database and any other scripts that need to be run once daily

#resolve paths relative to this script's own location so no machine-specific absolute paths are committed to git
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
echo "Starting fred_updater.py"
"$PROJECT_ROOT/.venv/bin/python" "$SCRIPT_DIR/db/fred_updater.py"
date
echo "Starting alpaca_updater.py"
"$PROJECT_ROOT/.venv/bin/python" "$SCRIPT_DIR/db/alpaca_updater.py"
#date
#echo "Starting news_analyzer.py"
#"$PROJECT_ROOT/.venv/bin/python" "$SCRIPT_DIR/news/news_analyzer.py"

date
echo "Financial repo daily cron job end."
