#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

INTERVAL="${INTERVAL:-300}"
X_EVERY="${X_EVERY:-6}"
WITH_X="${WITH_X:-0}"

echo ""
echo "  AX Pulse — live AI radar updater"
echo "  ─────────────────────────────────"
echo "  يجلب المصادر الموثوقة كل ${INTERVAL} ثانية ويحدّث الرادار المفتوح تلقائيًا."
echo "  X API لا يعمل إلا إذا شغّلتِه هكذا: WITH_X=1 ./auto-radar-live.command"
echo "  للإيقاف اضغطي Ctrl+C."
echo ""

cycle=0
while true; do
  cycle=$((cycle + 1))
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] تحديث المصادر الموثوقة..."
  ./pulse-radar --limit 18 --x-limit 10

  if [ "$WITH_X" = "1" ] && [ $((cycle % X_EVERY)) -eq 0 ]; then
    TOKEN_FILE="$HOME/.ax-pulse-x-token"
    if [ -z "$X_BEARER_TOKEN" ] && [ -s "$TOKEN_FILE" ]; then
      export X_BEARER_TOKEN="$(cat "$TOKEN_FILE")"
    fi
    if [ -n "$X_BEARER_TOKEN" ]; then
      YESTERDAY="$(date -v-2d '+%Y-%m-%d' 2>/dev/null || date -d '2 days ago' '+%Y-%m-%d')"
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] فحص X بكلمات ضيقة لتقليل التكلفة..."
      ./pulse-radar --limit 8 --x-limit 20 \
        --x-query '(GPT OR Claude OR Gemini OR Grok OR OpenAI OR Anthropic OR DeepMind OR "Hugging Face" OR Runway OR Midjourney OR ElevenLabs OR Perplexity) (launch OR released OR announces OR model OR pricing OR limits OR benchmark OR tool OR feature OR إطلاق OR نموذج OR أداة OR سعر OR حدود) since:'"${YESTERDAY}"' -is:retweet -from:grok'
    else
      echo "  لا يوجد X Bearer Token، تم تخطي X."
    fi
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] تم. التحديث التالي بعد ${INTERVAL} ثانية."
  sleep "$INTERVAL"
done
