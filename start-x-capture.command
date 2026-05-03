#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
URL="http://127.0.0.1:8020"
echo ""
echo "  AX X Capture"
echo "  افتح: ${URL}"
echo ""
( sleep 1 && open "${URL}" >/dev/null 2>&1 || true ) &
exec python3 tools/x_capture_server.py
