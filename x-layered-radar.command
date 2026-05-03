#!/usr/bin/env bash
# AX Pulse — run layered X Radar against focused AI account groups.
set -e
cd "$(dirname "$0")"

Q1="$(python3 tools/build_x_focus_query.py --layer companies --top 8)"
Q2="$(python3 tools/build_x_focus_query.py --layer builders --top 8)"
Q3="$(python3 tools/build_x_focus_query.py --layer experts --top 10)"

./x-radar.command \
  --x-limit 10 \
  --x-query "$Q1" \
  --x-query "$Q2" \
  --x-query "$Q3" \
  "$@"
