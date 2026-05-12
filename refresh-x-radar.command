#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "  AI Radar — Refresh X Signals"
echo "  ─────────────────────────────"
echo "  يفلتر ما جُمع من Safari/X ثم يحدث الرادار المحلي."
echo ""

python3 tools/filter_x_radar_ready.py
python3 tools/curate_x_opportunities.py >/dev/null || true
python3 tools/build_x_brief.py >/dev/null || true
python3 tools/build_focused_discussions.py >/dev/null || true
python3 tools/build_inline_radar_data.py >/dev/null

echo ""
echo "  انتهى. حدثي radar.html في Safari."
