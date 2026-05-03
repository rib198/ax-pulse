#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
echo ""
echo "  AX Pulse — local dev server"
echo "  ────────────────────────────"
echo "  Landing:       http://127.0.0.1:${PORT}/"
echo "  Today's Brief: http://127.0.0.1:${PORT}/dashboard.html"
echo "  Trending:      http://127.0.0.1:${PORT}/trending.html"
echo "  Opportunities: http://127.0.0.1:${PORT}/opportunities.html"
echo "  Categories:    http://127.0.0.1:${PORT}/categories.html"
echo ""
echo "  Press Ctrl+C to stop."
echo ""
( sleep 1 && open "http://127.0.0.1:${PORT}/" ) &
exec python3 -m http.server "${PORT}" --bind 127.0.0.1
