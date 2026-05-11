#!/usr/bin/env bash
# Continuous Safari browser — runs until you hit Ctrl+C or close the window.
# One profile every 4-7 minutes. Up to 100 tweets per profile.
# All anti-detection gates active (rotation, work-hours, cooldown, warmup).
#
# Stop politely: Ctrl+C in the terminal window.
# State persists in data/manual_x/safari_state.json — safe to start/stop.
set -e
cd "$(dirname "$0")"
exec /usr/bin/env python3 tools/x_safari_browse.py --continuous --pipeline "$@"
