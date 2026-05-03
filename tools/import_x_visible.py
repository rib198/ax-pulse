#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from x_manual_collect import add_signal


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("لم يصلني أي محتوى من Safari.")
        raise SystemExit(1)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("تعذر قراءة مخرجات Safari.")
        print(raw[:500])
        raise SystemExit(1)
    if isinstance(payload, list):
        page_url = "(قديم: لم يصل URL)"
        page_title = ""
        items = payload
    else:
        page_url = payload.get("page_url", "")
        page_title = payload.get("page_title", "")
        items = payload.get("items", [])
    print(f"المصدر: {page_title}")
    print(f"الرابط: {page_url}")
    if "x.com" not in page_url and "twitter.com" not in page_url:
        print("أوقفت الالتقاط: المصدر ليس X/Twitter.")
        raise SystemExit(1)
    added = 0
    skipped = 0
    for item in items:
        text = ((item.get("url") or "") + "\n" + (item.get("text") or "")).strip()
        if not text:
            skipped += 1
            continue
        ok, _message, _saved = add_signal(text, source=item.get("source") or "safari_visible")
        if ok:
            added += 1
        else:
            skipped += 1
    print(f"تم التقاط {added} تغريدة جديدة من Safari. تم تجاهل {skipped} مكررة/فارغة.")
    if not items:
        print("لم أجد تغريدات ظاهرة. جرّب تمرير صفحة X قليلًا ثم أعد التشغيل.")


if __name__ == "__main__":
    main()
