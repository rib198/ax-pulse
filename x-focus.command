#!/usr/bin/env bash
# AX Pulse — fetch verified focus accounts for X monitoring.
set -e
cd "$(dirname "$0")"
python3 tools/x_focus_accounts.py "$@"
