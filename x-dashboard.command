#!/usr/bin/env bash
# الرادار — لوحة تحكم محلية لجمع X
# Opens a local web dashboard for the Safari collector. Double-click in Finder
# or run from terminal. The browser will open automatically.
#
# Stop the dashboard: Ctrl+C in the terminal window (or close it).
# The dashboard reads/writes the same JSON files the CLI uses — safe to run
# alongside ./x-safari-continuous.command.
set -e
cd "$(dirname "$0")"
exec /usr/bin/env python3 tools/x_dashboard.py "$@"
