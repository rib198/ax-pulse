#!/usr/bin/env bash
# AX Pulse — run Radar with X API Bearer Token without saving it.
set -e
cd "$(dirname "$0")"

echo ""
echo "  AX Pulse — X API Radar"
echo "  ───────────────────────"
echo ""

if [ -z "$X_BEARER_TOKEN" ]; then
  TOKEN_FILE="$HOME/.ax-pulse-x-token"
  if [ -s "$TOKEN_FILE" ]; then
    X_BEARER_TOKEN="$(cat "$TOKEN_FILE")"
  fi
fi

if [ -z "$X_BEARER_TOKEN" ]; then
  X_BEARER_TOKEN="$(security find-generic-password -a ax-pulse -s AX_PULSE_X_BEARER_TOKEN -w 2>/dev/null || true)"
fi

if [ -z "$X_BEARER_TOKEN" ]; then
  echo "  الصقي Bearer Token هنا. لن يتم حفظه في ملفات المشروع."
  echo "  إذا أردت حفظه للمرة القادمة، افتحي setup-x-token.command أولاً."
  echo ""
  read -r -s -p "  X Bearer Token: " X_BEARER_TOKEN
  echo ""
fi

if [ -z "$X_BEARER_TOKEN" ]; then
  echo "  لم يتم إدخال توكن."
  exit 1
fi

export X_BEARER_TOKEN
./pulse-radar --x-limit 25 --include-x-notice "$@"
unset X_BEARER_TOKEN

echo ""
echo "  تم تحديث:"
echo "    • data/radar/signals.json"
echo "    • data/radar/opportunities.json"
echo ""
