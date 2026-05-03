#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo ""
echo "  AX Pulse — hourly AI revenue-product radar"
echo "  ─────────────────────────────────────────"
echo "  يبحث كل ساعة عن منتجات/خدمات/تطبيقات تستخدم AI ولها مسار دخل."
echo "  اتركي هذه النافذة مفتوحة. للإيقاف اضغطي Ctrl+C."
echo ""

while true; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] تحديث الرادار..."
  ./x-radar.command \
    --x-limit 30 \
    --x-query '(AI OR "artificial intelligence" OR ChatGPT OR Claude OR agents OR automation OR "ذكاء اصطناعي") ("make money" OR income OR revenue OR profit OR monetize OR paid OR sell OR product OR "AI-powered" OR "powered by AI" OR "uses AI" OR "built with AI" OR client OR customers OR service OR agency OR freelance OR consulting OR دخل OR ربح OR أرباح OR مال OR بيع OR منتج OR "مدعوم بالذكاء" OR "يستخدم الذكاء" OR عميل OR عملاء OR خدمة) -is:retweet -from:grok' \
    --x-query '("AI-powered" OR "powered by AI" OR "uses AI" OR "built with AI" OR "مدعوم بالذكاء" OR "يستخدم الذكاء") (product OR app OR SaaS OR startup OR tool OR subscription OR منتج OR تطبيق OR أداة OR اشتراك OR "شركة ناشئة") -is:retweet -from:grok' \
    --x-query '(AI OR LLM OR agents OR automation OR "ذكاء اصطناعي") ("business model" OR "use case" OR workflow OR automation OR "نموذج عمل" OR "حالة استخدام" OR أتمتة OR مشروع) (startup OR founder OR customer OR client OR شركة OR مؤسس OR عميل) -is:retweet -from:grok'
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] تم. التحديث التالي بعد ساعة."
  sleep 3600
done
