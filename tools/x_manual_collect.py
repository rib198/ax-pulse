#!/usr/bin/env python3
import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "manual_x"
POSTS_FILE = OUT_DIR / "posts.json"
OPPS_FILE = OUT_DIR / "opportunity_signals.json"

AI_TERMS = [
    "AI", "LLM", "Claude", "ChatGPT", "GPT", "OpenAI", "Anthropic", "Cursor",
    "agent", "agents", "automation", "Sora", "Veo",
    "ذكاء اصطناعي", "شات جي بي تي", "كلاود", "وكلاء", "أتمتة"
]

PAIN_TERMS = [
    "problem", "issue", "bug", "broken", "slow", "expensive", "hate",
    "struggling", "wish", "need", "missing", "hard", "can't", "cannot",
    "مشكلة", "صعب", "بطيء", "غالي", "مكلف", "أحتاج", "احتاج", "أتمنى",
    "ناقص", "لا يعمل", "ما يشتغل", "تحدي", "معاناة"
]

MARKET_TERMS = [
    "Arabic", "Saudi", "MENA", "Riyadh", "Khaleeji", "RTL",
    "عربي", "السعودية", "سعودي", "الخليج", "الشرق الأوسط", "الرياض"
]

QUERIES = [
    '(AI OR LLM OR ChatGPT OR Claude OR Cursor) (problem OR wish OR need OR broken OR expensive)',
    '(AI agents OR "AI agent" OR automation) (struggling OR slow OR missing OR hard)',
    '(ChatGPT OR Claude OR AI) (Arabic OR Saudi OR MENA OR RTL)',
    '(ذكاء اصطناعي OR شات جي بي تي OR كلاود) (مشكلة OR أحتاج OR أتمنى OR صعب OR مكلف)',
    '(وكلاء OR أتمتة OR AI agents) (السعودية OR عربي OR الخليج OR تحدي)',
]

FEED_GUIDE = [
    "افتح X بحسابك الشخصي.",
    "اذهب إلى For You أو Following أو Likes/Bookmarks إن كانت مليئة بمحتوى AI.",
    "اختر التغريدات التي تكشف ألمًا أو تحديًا أو طلبًا واضحًا، وليس مجرد خبر عام.",
    "انسخ رابط التغريدة أو نصها، ثم احفظها بـ: pbpaste | ./x-collect add --source for_you",
    "للإشارات العربية/متعددة اللغات استخدم نفس الأمر؛ الأداة تحفظ النص كما هو.",
]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def x_search_url(query):
    return "https://x.com/search?q=" + quote(query) + "&src=typed_query&f=live"


def cmd_queries(_args):
    print("افتح هذه الروابط وأنت مسجل دخولك في X، ثم انسخ التغريدات/الروابط المفيدة:")
    print()
    for index, query in enumerate(QUERIES, start=1):
        print(f"{index}. {query}")
        print(f"   {x_search_url(query)}")
        print()


def cmd_feed(_args):
    print("طريقة استخدام تفضيلات حسابك كمصدر إشارات:")
    print()
    for index, line in enumerate(FEED_GUIDE, start=1):
        print(f"{index}. {line}")


def read_input(parts):
    if parts:
        return " ".join(parts).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def extract_url(text):
    match = re.search(r"https?://(?:www\.)?(?:x|twitter)\.com/[^\s]+", text)
    return match.group(0) if match else ""


def extract_tweet_id(url):
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else ""


def extract_author(url):
    match = re.search(r"(?:x|twitter)\.com/([^/\s]+)/status/", url)
    return match.group(1) if match else ""


def score_text(text):
    lower = text.lower()
    pain_hits = [term for term in PAIN_TERMS if term.lower() in lower or term in text]
    ai_hits = [term for term in AI_TERMS if term.lower() in lower or term in text]
    market_hits = [term for term in MARKET_TERMS if term.lower() in lower or term in text]
    score = min(1.0, (len(pain_hits) * 0.22) + (len(ai_hits) * 0.08) + (len(market_hits) * 0.12))
    tags = []
    if pain_hits:
        tags.append("pain")
    if market_hits:
        tags.append("mena_arabic")
    if "agent" in lower or "وكلاء" in text:
        tags.append("agents")
    if "cursor" in lower or "code" in lower or "برمجة" in text:
        tags.append("coding")
    return round(score, 2), sorted(set(pain_hits + ai_hits + market_hits)), tags


def add_signal(text, source="x_manual", query="manual"):
    posts = load_json(POSTS_FILE, {"collected_at": now(), "items": []})
    url = extract_url(text)
    tweet_id = extract_tweet_id(url)
    existing_ids = {item.get("tweet_id") for item in posts["items"] if item.get("tweet_id")}
    if tweet_id and tweet_id in existing_ids:
        return False, "هذه التغريدة موجودة مسبقًا، لم أكررها.", None
    score, matched, tags = score_text(text)
    item = {
        "tweet_id": tweet_id or f"manual_{len(posts['items']) + 1}",
        "author_handle": extract_author(url),
        "text": text,
        "url": url,
        "posted_at": None,
        "collected_at": now(),
        "source_type": source,
        "query": query or "manual",
        "matched_keywords": matched,
        "public_metrics": None,
        "pain_signal_score": score,
        "opportunity_tags": tags,
        "verification_status": "manual_visible",
    }
    posts["items"].append(item)
    posts["collected_at"] = now()
    save_json(POSTS_FILE, posts)
    return True, f"تمت إضافة الإشارة. pain_signal_score={score}", item


def cmd_add(args):
    text = read_input(args.text)
    if not text:
        raise SystemExit('الاستخدام: ./x-collect add "نص التغريدة أو الرابط"')
    added, message, item = add_signal(text, source=args.source, query=args.query)
    print(message)
    if not added:
        return
    if item and item.get("url"):
        print(f"الرابط: {item['url']}")


def cmd_show(args):
    posts = load_json(POSTS_FILE, {"items": []})
    items = posts["items"][-args.last :] if args.last else posts["items"]
    print(f"عدد الإشارات المحفوظة: {len(posts['items'])}")
    for index, item in enumerate(items, start=1):
        print()
        print(f"[{index}] score={item.get('pain_signal_score')} tags={', '.join(item.get('opportunity_tags', [])) or '-'}")
        print(f"url: {item.get('url') or '-'}")
        print(item.get("text", "")[:700])


def cmd_review(args):
    posts = load_json(POSTS_FILE, {"items": []})
    items = posts["items"][-args.last :] if args.last else posts["items"]
    print("روابط تحتاج مراجعة نصية:")
    print("افتح الرابط، ظلل نص التغريدة أو انسخه، ثم أعد إضافته بنفس الزر أو عبر x-collect add.")
    print()
    for index, item in enumerate(items, start=1):
        text = item.get("text", "").strip()
        url = item.get("url", "")
        only_url = url and text.replace("\n", " ").strip() == url
        if only_url or item.get("pain_signal_score", 0) == 0:
            print(f"{index}. {url or text[:120]}")


def fetch_public_x_tweet(url):
    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        return None
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as res:
        page = res.read().decode("utf-8", errors="replace")
    marker = "window.__INITIAL_STATE__="
    start = page.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = page.find(";window.__META_DATA__", start)
    if end == -1:
        end = page.find("</script>", start)
    if end == -1:
        return None
    data = json.loads(page[start:end].rstrip(";"))
    tweet = data.get("entities", {}).get("tweets", {}).get("entities", {}).get(tweet_id)
    if not tweet:
        return None
    users = data.get("entities", {}).get("users", {}).get("entities", {})
    user = users.get(str(tweet.get("user")), {})
    views = tweet.get("views") or {}
    return {
        "tweet_id": tweet_id,
        "author_handle": user.get("screen_name") or extract_author(url),
        "text": html.unescape(tweet.get("full_text", "")),
        "url": url,
        "posted_at": None,
        "public_metrics": {
            "likes": tweet.get("favorite_count"),
            "reposts": tweet.get("retweet_count"),
            "replies": tweet.get("reply_count"),
            "quotes": tweet.get("quote_count"),
            "views": views.get("count"),
        },
        "lang": tweet.get("lang"),
    }


def cmd_enrich_public(args):
    posts = load_json(POSTS_FILE, {"collected_at": now(), "items": []})
    updated = 0
    failed = 0
    for item in posts["items"]:
        url = item.get("url")
        text = item.get("text", "").strip()
        if not url or (text and text.replace("\n", " ").strip() != url and len(text) > len(url) + 10):
            continue
        try:
            fetched = fetch_public_x_tweet(url)
        except Exception as exc:
            failed += 1
            print(f"تعذر فتح {url}: {exc}")
            continue
        if not fetched:
            failed += 1
            print(f"لم أجد نصًا عامًا في: {url}")
            continue
        score, matched, tags = score_text(fetched["text"])
        item.update({
            "tweet_id": fetched["tweet_id"],
            "author_handle": fetched["author_handle"],
            "text": fetched["text"],
            "posted_at": fetched["posted_at"],
            "public_metrics": fetched["public_metrics"],
            "lang": fetched["lang"],
            "matched_keywords": matched,
            "pain_signal_score": score,
            "opportunity_tags": tags,
            "verification_status": "public_x_page",
            "enriched_at": now(),
        })
        updated += 1
        print(f"تم إثراء: {url} score={score}")
    posts["collected_at"] = now()
    save_json(POSTS_FILE, posts)
    print()
    print(f"النتيجة: تم إثراء {updated}، تعذر {failed}.")


def cmd_export_opps(_args):
    posts = load_json(POSTS_FILE, {"items": []})
    grouped = {}
    for item in posts["items"]:
        for tag in item.get("opportunity_tags", []) or ["general"]:
            grouped.setdefault(tag, []).append(item)
    opportunities = []
    for tag, items in grouped.items():
        strong = [item for item in items if item.get("pain_signal_score", 0) >= 0.25]
        if not strong:
            continue
        opportunities.append({
            "tag": tag,
            "signal_count": len(strong),
            "avg_pain_score": round(sum(i["pain_signal_score"] for i in strong) / len(strong), 2),
            "evidence_items": [
                {
                    "tweet_id": i.get("tweet_id"),
                    "url": i.get("url"),
                    "text": i.get("text"),
                    "pain_signal_score": i.get("pain_signal_score"),
                    "collected_at": i.get("collected_at"),
                }
                for i in strong[:8]
            ],
            "verification_status": "manual_visible",
        })
    save_json(OPPS_FILE, {
        "generated_at": now(),
        "source": "manual_x_posts",
        "opportunities": sorted(opportunities, key=lambda o: o["avg_pain_score"], reverse=True),
    })
    print(OPPS_FILE)


def build_parser():
    parser = argparse.ArgumentParser(prog="./x-collect", description="جمع يدوي آمن لإشارات X/Twitter عن الذكاء الاصطناعي.")
    sub = parser.add_subparsers(dest="command", required=True)
    queries = sub.add_parser("queries", help="عرض روابط بحث جاهزة في X.")
    queries.set_defaults(func=cmd_queries)
    add = sub.add_parser("add", help="إضافة تغريدة/رابط بعد نسخه من حسابك الشخصي.")
    add.add_argument("text", nargs="*")
    add.add_argument("--query", default="")
    add.add_argument("--source", default="x_manual", choices=["x_manual", "for_you", "following", "search", "likes", "bookmarks"])
    add.set_defaults(func=cmd_add)
    feed = sub.add_parser("feed", help="شرح طريقة الجمع من تفضيلات حسابك/For You.")
    feed.set_defaults(func=cmd_feed)
    show = sub.add_parser("show", help="عرض الإشارات المحفوظة.")
    show.add_argument("--last", type=int, default=0)
    show.set_defaults(func=cmd_show)
    review = sub.add_parser("review", help="عرض الروابط التي تحتاج نص التغريدة لاستخراج فرصة.")
    review.add_argument("--last", type=int, default=0)
    review.set_defaults(func=cmd_review)
    enrich = sub.add_parser("enrich-public", help="فتح روابط X العامة ومحاولة ملء النص والمقاييس تلقائيًا.")
    enrich.set_defaults(func=cmd_enrich_public)
    export = sub.add_parser("export-opps", help="تجميع إشارات الألم في فرص أولية قابلة للتحقق.")
    export.set_defaults(func=cmd_export_opps)
    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
