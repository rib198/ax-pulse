#!/usr/bin/env bash
# AI Radar — Safari Radar
#
# Reads the X capture from either:
#   1. ~/Downloads/ax-pulse-x-capture.json  (preferred — the bookmarklet's
#      "احفظي للملف ↓" button writes here)
#   2. The macOS clipboard (fallback — the "نسخ بديل" button)
#
# Then runs the same radar pipeline as the Playwright collector.

set -euo pipefail
cd "$(dirname "$0")"

cat <<EOF

  AI Radar — Safari Radar
  ───────────────────────
  يقرأ بيانات Safari من ملف Downloads أولًا، ثم من الحافظة احتياطيًا.

EOF

if ! command -v python3 >/dev/null 2>&1; then
  echo "  Python 3 غير مثبت."; exit 1
fi

# --- 1. Try the downloaded JSON file first ------------------------------------
DL_FILE=""
for cand in \
  "$HOME/Downloads/ax-pulse-x-capture.json" \
  "$HOME/Downloads/ax-pulse-x-capture (1).json" \
  "$HOME/Downloads/ax-pulse-x-capture (2).json" \
  "$HOME/Downloads/ax-pulse-x-capture (3).json" \
; do
  if [ -f "$cand" ]; then
    DL_FILE="$cand"
  fi
done

# Pick the most recently modified ax-pulse-x-capture*.json in Downloads
if [ -z "$DL_FILE" ]; then
  DL_FILE="$(ls -t "$HOME/Downloads"/ax-pulse-x-capture*.json 2>/dev/null | head -1 || true)"
fi

USED_SOURCE=""
if [ -n "$DL_FILE" ] && [ -f "$DL_FILE" ]; then
  if grep -q "ax_pulse.safari_radar.v1" "$DL_FILE" 2>/dev/null; then
    echo "  وجدت ملف Downloads: $(basename "$DL_FILE")"
    USED_SOURCE="$DL_FILE"
  fi
fi

# --- 2. Fall back to clipboard ------------------------------------------------
if [ -z "$USED_SOURCE" ]; then
  if command -v pbpaste >/dev/null 2>&1; then
    CLIP_HEAD="$(pbpaste 2>/dev/null | head -c 200 || true)"
    if printf '%s' "$CLIP_HEAD" | grep -q "ax_pulse.safari_radar.v1"; then
      echo "  وجدت بيانات في الحافظة."
      USED_SOURCE="clipboard"
    fi
  fi
fi

# --- 3. Nothing usable --------------------------------------------------------
if [ -z "$USED_SOURCE" ]; then
  cat <<EOF
  لم أجد بيانات Safari Radar — لا في Downloads ولا في الحافظة.

  الخطوات:
    1. افتحي x.com في Safari (مسجلة دخول).
    2. اضغطي زر "اجمع X للرادار" من شريط المفضلة.
    3. انتظري حتى يكتمل الجمع (الزر الأخضر يصبح فاقعًا).
    4. اضغطي "احفظي للملف ↓".
       - سيتنزل ملف اسمه ax-pulse-x-capture.json إلى Downloads.
    5. ارجعي هنا وشغّلي الأمر مرة ثانية.

  إذا لم يظهر زر البوكماركلت في شريط المفضلة:
    open setup-safari-radar.html
    ثم اسحبي الزر الأخضر إلى شريط المفضلة في Safari.
EOF
  exit 4
fi

echo "  المرحلة 1/2: قراءة البيانات وحفظها..."
if [ "$USED_SOURCE" = "clipboard" ]; then
  python3 tools/safari_clipboard_collect.py
else
  python3 tools/safari_clipboard_collect.py < "$USED_SOURCE"
  # Move the consumed file aside so we don't import it again next run
  mkdir -p "$HOME/Downloads/ax-pulse-archive"
  mv "$USED_SOURCE" "$HOME/Downloads/ax-pulse-archive/$(basename "$USED_SOURCE" .json)-$(date +%Y%m%d-%H%M%S).json"
  echo "  أرشفت الملف في Downloads/ax-pulse-archive/"
fi

echo
echo "  المرحلة 2/2: بوابة الجودة + بناء بطاقات الرادار..."
python3 tools/filter_x_radar_ready.py
python3 tools/curate_x_opportunities.py >/dev/null || true
python3 tools/build_x_brief.py >/dev/null || true
python3 tools/build_focused_discussions.py >/dev/null || true
python3 tools/build_x_radar_cards.py
python3 tools/build_inline_radar_data.py

echo
echo "  انتهى الجمع والتحديث."
echo "  posts.json:        data/manual_x/posts.json"
echo "  x_radar_cards:     data/manual_x/x_radar_cards.json"
echo
echo "  سيتم فتح الرادار الآن..."
open "$PWD/radar.html" >/dev/null 2>&1 || true
