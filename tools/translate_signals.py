#!/usr/bin/env python3
"""
AX Pulse — ترجمة عناوين الإشارات إلى العربية عبر MyMemory API.

مجاني، بدون مفتاح API. الحد: ~5000 حرف/يوم لكل IP.

- يقرأ data/radar/signals.json
- يضيف title_ar لكل عنصر (ويخزّن في cache دائم لمقاومة إعادة توليد signals.json)
- idempotent: يتجاوز ما تُرجم سابقاً
- يبدأ بأعلى opportunity_score حتى نضمن ترجمة الأهم أولاً
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / "data" / "radar" / "signals.json"
CACHE = ROOT / "data" / "radar" / "_translations_ar.json"

LOCAL_TITLE_AR = {
    "Collaborative Agent Reasoning Engineering (CARE)": "هندسة تفكير الوكلاء التعاونية: منهجية لتصميم وكلاء ذكاء اصطناعي مع خبراء المجال والمطورين",
    "EdgeFM: Efficient Edge Inference for Vision-Language Models": "EdgeFM: تشغيل فعال لنماذج الرؤية واللغة على الأجهزة الطرفية",
    "Addressing the Reality Gap: A Three-Tension Framework for Agentic AI Adoption": "معالجة فجوة الواقع: إطار لقياس تبني الذكاء الاصطناعي الوكيلي",
    "Scalable Inference Architectures for Compound AI Systems": "بنى استدلال قابلة للتوسع لتطبيقات الذكاء الاصطناعي المركبة",
    "Crab: A Semantics-Aware Checkpoint/Restore Runtime for Agent Sandboxes": "Crab: نظام حفظ واسترجاع ذكي لحالة وكلاء الذكاء الاصطناعي داخل بيئات آمنة",
    "Exploring Interaction Paradigms for LLM Agents in Scientific Visualization": "استكشاف طرق التفاعل مع وكلاء النماذج اللغوية في التصور العلمي",
    "ITS-Mina": "ITS-Mina: إطار تنبؤ بالسلاسل الزمنية لتطبيقات مالية وطاقة ومرور",
    "Iterative Multimodal Retrieval-Augmented Generation for Medical Question Answering": "توليد معزز بالاسترجاع متعدد الوسائط للأسئلة الطبية",
    "Can AI Be a Good Peer Reviewer?": "هل يمكن للذكاء الاصطناعي أن يكون مراجعًا علميًا جيدًا؟",
    "CastFlow: Learning Role-Specialized Agentic Workflows for Time Series Forecasting": "CastFlow: سير عمل وكيلي متخصص للتنبؤ بالسلاسل الزمنية",
    "Purifying Multimodal Retrieval": "تنقية الاسترجاع متعدد الوسائط عبر اختيار الدليل على مستوى الأجزاء",
    "Top 10 uses for Codex at work": "أفضل 10 استخدامات لـ Codex في العمل",
    "Introducing workspace agents in ChatGPT": "تقديم وكلاء مساحة العمل في ChatGPT",
    "Workspace agents": "وكلاء مساحة العمل",
    "Plugins and skills": "الإضافات والمهارات",
    "Automations": "الأتمتة",
    "Salesforce is crowdsourcing its AI roadmap": "Salesforce تجمع آراء العملاء لتحديد خارطة طريق الذكاء الاصطناعي",
    "Stripe updates Link": "Stripe تحدث Link لاستخدامه مع وكلاء الذكاء الاصطناعي",
}


def is_arabic(text: str) -> bool:
    return any("؀" <= c <= "ۿ" for c in (text or ""))


def detect_source_lang(text: str) -> str:
    if any("؀" <= c <= "ۿ" for c in text):
        return "ar"
    if any("぀" <= c <= "ヿ" for c in text):
        return "ja"
    if any("一" <= c <= "鿿" for c in text):
        return "zh-CN"
    if any("가" <= c <= "힯" for c in text):
        return "ko"
    return "en"


def fetch_translation(text: str):
    if not text or not text.strip():
        return None
    payload = text[:480]  # MyMemory works best <500 chars
    src = detect_source_lang(payload)
    if src == "ar":
        return payload
    url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
        {"q": payload, "langpair": f"{src}|ar"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "AX-Pulse-Radar/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return "__RATE_LIMIT__"
        return None
    except Exception:
        return None
    if data.get("responseStatus") not in (200, "200"):
        return None
    translated = (data.get("responseData") or {}).get("translatedText", "")
    if not translated:
        return None
    bad_prefixes = ("PLEASE", "INVALID", "MYMEMORY WARNING", "QUOTA EXCEEDED")
    if any(translated.upper().startswith(p) for p in bad_prefixes):
        return "__RATE_LIMIT__" if "QUOTA" in translated.upper() else None
    return translated.strip()


def local_translation(text: str):
    if not text:
        return None
    for key, value in LOCAL_TITLE_AR.items():
        if key.lower() in text.lower():
            return value
    return None


def load_cache():
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if not SIGNALS.exists():
        print(f"signals.json not found at {SIGNALS}", file=sys.stderr)
        return 1

    data = json.loads(SIGNALS.read_text(encoding="utf-8"))
    items = data.get("items", [])
    cache = load_cache()

    print(f"  signals total:     {len(items)}", file=sys.stderr)
    print(f"  cached translations: {len(cache)}", file=sys.stderr)

    sorted_items = sorted(items, key=lambda x: -(x.get("opportunity_score") or 0))

    new_count = 0
    cached_count = 0
    fail_count = 0
    rate_limit_hit = False

    for item in sorted_items:
        item_id = item.get("id")
        title = item.get("title", "")
        if not item_id or not title:
            continue

        # Already cached? Apply and skip API.
        if item_id in cache:
            item["title_ar"] = cache[item_id].get("title_ar", title)
            cached_count += 1
            continue

        # Already Arabic? Use as-is.
        if is_arabic(title):
            cache[item_id] = {"title_ar": title}
            item["title_ar"] = title
            continue

        translated = local_translation(title) or fetch_translation(title)
        if translated == "__RATE_LIMIT__":
            print(f"\n  ⚠ بلغنا الحد اليومي لـ MyMemory. سنحفظ ما لدينا ونكمل غداً.", file=sys.stderr)
            rate_limit_hit = True
            break
        if translated:
            item["title_ar"] = translated
            cache[item_id] = {"title_ar": translated}
            new_count += 1
            preview_orig = title[:45].replace("\n", " ")
            preview_tr = translated[:45].replace("\n", " ")
            print(f"  ✓ {item.get('source_id','?')[:15]:15s}  {preview_orig:45s}  →  {preview_tr}", file=sys.stderr)
            save_cache(cache)
            time.sleep(0.5)
        else:
            fail_count += 1

    # Apply cache to all items (in case some were missed)
    for item in items:
        if item.get("id") in cache and "title_ar" not in item:
            item["title_ar"] = cache[item["id"]].get("title_ar", item.get("title", ""))

    SIGNALS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  ────────── ملخص ──────────", file=sys.stderr)
    print(f"  ترجمات جديدة:  {new_count}", file=sys.stderr)
    print(f"  من الكاش:      {cached_count}", file=sys.stderr)
    print(f"  فشل:           {fail_count}", file=sys.stderr)
    print(f"  rate limit:    {'نعم' if rate_limit_hit else 'لا'}", file=sys.stderr)
    print(f"  ✓ data/radar/signals.json تم تحديثه", file=sys.stderr)
    print(f"  ✓ data/radar/_translations_ar.json (cache دائم)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
