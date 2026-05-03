#!/usr/bin/env bash
# AX Pulse — run X Radar against high-signal AI focus accounts.
set -e
cd "$(dirname "$0")"

TOP="${TOP:-12}"
QUERY="$(python3 tools/build_x_focus_query.py --top "$TOP")"
./x-radar.command --x-limit 25 --x-query "$QUERY" "$@"
