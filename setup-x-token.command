#!/usr/bin/env bash
# AX Pulse — save X API Bearer Token in macOS Keychain.
set -e
cd "$(dirname "$0")"

echo ""
echo "  AX Pulse — حفظ X Bearer Token"
echo "  ─────────────────────────────"
echo "  سيتم حفظ التوكن خارج ملفات المشروع في ملف مخفي بصلاحية خاصة."
echo ""
read -r -s -p "  X Bearer Token: " X_TOKEN
echo ""

if [ -z "$X_TOKEN" ]; then
  echo "  لم يتم إدخال توكن."
  exit 1
fi

TOKEN_FILE="$HOME/.ax-pulse-x-token"
umask 077
printf "%s" "$X_TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"

unset X_TOKEN

if [ -s "$TOKEN_FILE" ]; then
  STATUS="تم التحقق من الحفظ."
else
  STATUS="لم أستطع التحقق من الحفظ. جربي تشغيل الملف مرة أخرى."
fi
echo ""
echo "  $STATUS"
echo "  الآن يمكن تشغيل:"
echo "    ./x-radar.command --x-limit 25"
echo ""
