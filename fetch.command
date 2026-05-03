#!/usr/bin/env bash
# AX Pulse — one-click: fetch RSS + merge into radar signals
set -e
cd "$(dirname "$0")"
echo ""
echo "  AX Pulse — تحديث البيانات الحية"
echo "  ─────────────────────────────────"
echo ""
echo "  [1/2] جلب من 11 مصدر RSS..."
echo ""
python3 tools/fetch_ai_newsletters.py
echo ""
echo "  [2/2] دمج في radar signals..."
echo ""
python3 tools/newsletters_to_signals.py
echo ""
echo "  ✓ تم. شغّل ./start.command لرؤية الواجهة."
echo ""
