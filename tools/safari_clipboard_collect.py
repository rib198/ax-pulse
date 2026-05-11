#!/usr/bin/env python3
"""
Read the Safari bookmarklet payload from the macOS clipboard and merge it into
data/manual_x/posts.json with the same schema the Playwright collector uses.

Quality gate runs at write time so weak content never reaches posts.json.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_FILE = ROOT / "data" / "manual_x" / "posts.json"


# Mirror of the JS scoring vocabulary so the schema stays consistent with the
# Playwright collector's output.
AI_TERMS = [
    "ai", "a.i.", "gpt", "chatgpt", "claude", "gemini", "grok", "llm", "llms",
    "agent", "agents", "agentic", "automation", "cursor", "codex", "sora",
    "veo", "runway", "midjourney", "hugging face", "huggingface", "openai",
    "anthropic", "deepmind", "mistral", "perplexity", "replit", "devin",
    "cline", "aider", "lovable", "bolt.new", "v0.dev", "rag", "fine-tune",
    "embedding", "mcp", "tool use", "function calling", "n8n", "langchain",
    "langgraph", "crewai", "autogen",
    "ذكاء اصطناعي", "ذكاء صناعي", "كلود", "وكلاء", "وكيل", "شات جي بي تي",
    "أتمتة", "نماذج", "نموذج لغوي",
    "人工知能", "生成ai", "aiエージェント", "인공지능", "智能体",
]
PRODUCT_TERMS = [
    "tool", "tools", "launch", "launched", "released", "release", "ship",
    "shipping", "update", "workflow", "startup", "product", "mvp", "build",
    "service", "income", "money", "revenue", "business", "subscription",
    "design", "dashboard", "video", "voice", "dubbing", "api", "open source",
    "open-source", "تحديث", "إطلاق", "أداة", "أدوات", "دخل", "منتج", "خدمة",
    "مشروع", "تصميم", "فيديو", "صوت", "دبلجة", "اشتراك", "مجاني", "مدفوع",
]
PAIN_TERMS = [
    "problem", "pain", "hard", "expensive", "slow", "broken", "bug", "need",
    "wish", "missing", "struggling", "frustrat", "annoying", "painful",
    "doesn't work", "doesnt work", "not working", "rate limit",
    "مشكلة", "صعب", "بطيء", "مكلف", "أحتاج", "احتاج", "أتمنى", "ناقص",
    "لا يعمل", "متعب", "مزعج", "تحدي", "محبط",
]
HARD_KEEP = [
    "launching", "just launched", "just shipped", "we just released",
    "new model", "new tool", "open source", "we built", "i built",
    "available now", "public beta", "early access", "introducing",
    "أطلقنا", "أطلقت", "أطلق", "متاح الآن", "بنينا", "بنيت",
]
HARD_REJECT = [
    "subscribe to premium", "get verified", "sign up to like",
    "turn on browser notifications", "cookie policy",
]
OFF_TOPIC = ["football", "soccer", "nba", "fifa", "world cup", "كرة القدم"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def read_clipboard() -> str:
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            return data
    try:
        return subprocess.check_output(["pbpaste"], text=True)
    except Exception as exc:
        print(f"  تعذر قراءة الحافظة: {exc}")
        return ""


def parse_payload(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema") != "ax_pulse.safari_radar.v1":
        return None
    return payload


def score_text(text: str) -> tuple[float, list[str], list[str]]:
    low = text.lower()
    matched: list[str] = []
    score = 0.0
    for term in AI_TERMS:
        if term.lower() in low:
            matched.append(term)
            score += 0.07
    for term in PRODUCT_TERMS:
        if term.lower() in low:
            matched.append(term)
            score += 0.06
    for term in PAIN_TERMS:
        if term.lower() in low:
            matched.append(term)
            score += 0.10
    for term in HARD_KEEP:
        if term.lower() in low:
            matched.append(term)
            score += 0.20
    tags: list[str] = []
    if re.search(r"\b(agent|agents|agentic)\b|وكلاء|وكيل", text):
        tags.append("agents")
    if re.search(r"\b(code|coding|cursor|codex|claude code|copilot)\b|برمجة|كود", text):
        tags.append("coding")
    if re.search(r"\b(video|sora|veo|runway|midjourney)\b|فيديو", text):
        tags.append("video")
    if re.search(r"\b(voice|audio|dubbing|tts)\b|صوت|دبلجة", text):
        tags.append("voice")
    if re.search(r"\b(income|money|startup|business|revenue|saas)\b|دخل|مشروع|خدمة", text):
        tags.append("business")
    if re.search(r"\b(launch|launched|released|shipping|introducing)\b|إطلاق|أطلق|متاح", text):
        tags.append("launch")
    if any(term.lower() in low for term in PAIN_TERMS):
        tags.append("pain")
    return min(1.0, round(score, 2)), sorted(set(matched))[:18], sorted(set(tags))


def is_acceptable(text: str, score: float, min_score: float = 0.18) -> bool:
    if not text or len(text) < 40:
        return False
    low = text.lower()
    if any(f in low for f in HARD_REJECT):
        return False
    if any(f in low for f in OFF_TOPIC):
        return False
    if any(p.lower() in low for p in HARD_KEEP):
        return True
    has_ai = any(t.lower() in low for t in AI_TERMS)
    has_product = any(t.lower() in low for t in PRODUCT_TERMS)
    has_pain = any(t.lower() in low for t in PAIN_TERMS)
    if not has_ai:
        return False
    if not (has_product or has_pain):
        return False
    return score >= min_score


def load_posts() -> dict:
    if not POSTS_FILE.exists():
        return {"collected_at": now_iso(), "items": []}
    try:
        data = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
        if "items" not in data:
            data["items"] = []
        return data
    except json.JSONDecodeError:
        return {"collected_at": now_iso(), "items": []}


def save_posts(data: dict) -> None:
    POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    raw = read_clipboard()
    payload = parse_payload(raw)
    if payload is None:
        print("\n  لم أجد بيانات صالحة في الحافظة.")
        print("  افتحي x.com في Safari، اضغطي زر \"اجمع X للرادار\"، اضغطي \"انسخي للحافظة\"،")
        print("  ثم أعيدي تشغيل ./safari-radar.command\n")
        return 2

    items = payload.get("items") or []
    page_url = payload.get("page_url") or ""
    if "x.com" not in page_url and "twitter.com" not in page_url:
        print(f"  المصدر ليس X/Twitter ({page_url}). أوقفت الجمع.")
        return 3

    posts = load_posts()
    existing: set[str] = set()
    for item in posts.get("items", []):
        if item.get("tweet_id"):
            existing.add(f"id:{item['tweet_id']}")
        if item.get("text"):
            existing.add(f"hash:{sha(item['text'])[:18]}")

    session_id = f"safari-radar-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    added = 0
    skipped_dup = 0
    skipped_quality = 0

    for raw_item in items:
        text = (raw_item.get("text") or "").strip()
        if not text:
            skipped_quality += 1
            continue
        score, matched, tags = score_text(text)
        if not is_acceptable(text, score):
            skipped_quality += 1
            continue
        tweet_id = (raw_item.get("tweet_id") or "").strip()
        # Require a real numeric tweet_id so the radar can always link back to
        # the verifiable post. Non-numeric or missing IDs mean the article was
        # only partially scraped — drop it.
        if not tweet_id or not tweet_id.isdigit():
            skipped_quality += 1
            continue
        key = f"id:{tweet_id}"
        if key in existing:
            skipped_dup += 1
            continue

        handle = (raw_item.get("author_handle") or "").lstrip("@")
        url = raw_item.get("url") or ""
        if not url and tweet_id and handle:
            url = f"https://x.com/{handle}/status/{tweet_id}"

        posts["items"].append({
            "tweet_id": tweet_id,
            "author_handle": handle,
            "text": text[:1600],
            "url": url,
            "posted_at": raw_item.get("posted_at"),
            "collected_at": now_iso(),
            "source_type": "safari_radar_bookmarklet",
            "query": page_url,
            "page_url": raw_item.get("page_url") or page_url,
            "matched_keywords": matched,
            "public_metrics": None,
            "pain_signal_score": score,
            "opportunity_tags": tags,
            "verification_status": "safari_visible_x",
            "capture_session_id": session_id,
        })
        existing.add(key)
        added += 1

    posts["collected_at"] = now_iso()
    posts["last_safari_capture"] = {
        "session_id": session_id,
        "collected_at": now_iso(),
        "page_url": page_url,
        "added": added,
        "skipped_duplicates": skipped_dup,
        "skipped_low_quality": skipped_quality,
        "total_seen": len(items),
    }
    save_posts(posts)

    print()
    print("  AI Radar — Safari Capture")
    print("  ─────────────────────────")
    print(f"  المصدر:                {page_url[:70]}")
    print(f"  شوهد إجماليًا:         {len(items)}")
    print(f"  أضيف للأرشيف:          {added}")
    print(f"  متكرر (مهمل):          {skipped_dup}")
    print(f"  ضعيف/خارج الموضوع:   {skipped_quality}")
    print(f"  إجمالي الأرشيف الآن:  {len(posts['items'])}")
    print(f"  الملف: data/manual_x/posts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
