#!/usr/bin/env python3
"""
AX Pulse — adapter: newsletters/items.json  →  radar/signals.json

Reads the RSS items aggregated by fetch_ai_newsletters.py and merges them
into the radar signals stream consumed by the dashboard, using the same
schema as pulse_radar.py. Idempotent: re-running replaces any previously
merged newsletter items, never duplicates.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
NEWS_FILE = ROOT / "data" / "newsletters" / "items.json"
RADAR_DIR = ROOT / "data" / "radar"
SIGNALS_FILE = RADAR_DIR / "signals.json"

# Match pulse_radar.py keyword vocabulary so signals look uniform downstream.
KEYWORDS = [
    "ai", "llm", "agent", "agents", "claude", "chatgpt", "openai", "anthropic",
    "cursor", "gemini", "deepmind", "sora", "veo", "model", "mcp", "codex",
    "ذكاء", "كلاود", "شات", "وكلاء", "نموذج",
]

PAIN = [
    "problem", "broken", "slow", "expensive", "hard", "difficult", "struggle",
    "wish", "need", "missing", "fails", "bad", "worse", "cost", "pricing",
]

LAUNCH = [
    "launch", "released", "announces", "introduces", "ships",
    "open source", "open-source", "ga ", "now available", "preview",
]

# Per-source classification. Anything not listed defaults to 'newsletter'.
SOURCE_KIND_MAP = {
    "openai_blog": "official",
    "anthropic_news": "official",
    "huggingface_blog": "dev_blog",
    "deepmind_blog": "official",
    "tldr_ai": "newsletter",
    "smol_ai_news": "newsletter",
    "the_rundown": "newsletter",
    "bens_bites": "newsletter",
    "import_ai": "newsletter",
    "latent_space": "newsletter",
    "simonw": "dev_blog",
}

NEWSLETTER_SOURCE_IDS = set(SOURCE_KIND_MAP.keys())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def extract_external_id(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    return parts[-1] if parts else parsed.netloc


def matched(text: str, vocab) -> list:
    if not text:
        return []
    lowered = text.lower()
    hits = []
    for k in vocab:
        if k.lower() in lowered:
            hits.append(k)
    return sorted(set(hits))


def classify(text: str) -> str:
    if not text:
        return "info"
    lowered = text.lower()
    pain_hits = sum(1 for k in PAIN if k in lowered)
    launch_hits = sum(1 for k in LAUNCH if k in lowered)
    if pain_hits >= 2 or (pain_hits == 1 and launch_hits == 0):
        return "pain"
    if launch_hits >= 1:
        return "launch"
    return "info"


def opportunity_score(signal_type: str, kw_count: int, has_url: bool) -> float:
    base = 0.45
    if signal_type == "pain":
        base += 0.25
    elif signal_type == "launch":
        base += 0.10
    base += min(kw_count * 0.04, 0.20)
    if has_url:
        base += 0.05
    return round(min(base, 0.95), 2)


def to_signal(item):
    source_id = item.get("source_id", "rss")
    title = item.get("title", "")
    summary = item.get("summary", "")
    blob = f"{title} {summary}"
    kws = matched(blob, KEYWORDS)
    sig_type = classify(blob)
    return {
        "id": f"{source_id}:{item.get('id', '')}",
        "source_id": source_id,
        "source_name": item.get("source_name", source_id),
        "source_kind": SOURCE_KIND_MAP.get(source_id, "newsletter"),
        "source_url": item.get("source_url", ""),
        "external_id": extract_external_id(item.get("source_url", "")),
        "title": title,
        "text": summary,
        "posted_at": item.get("published_at", ""),
        "collected_at": item.get("collected_at", now_iso()),
        "matched_keywords": kws,
        "signal_type": sig_type,
        "opportunity_score": opportunity_score(sig_type, len(kws), bool(item.get("source_url"))),
        "metrics": {},
        "verification_status": "source_linked",
    }


def is_newsletter_signal(sig) -> bool:
    return sig.get("source_id") in NEWSLETTER_SOURCE_IDS


def load_existing_signals():
    if not SIGNALS_FILE.exists():
        return {"generated_at": now_iso(), "count": 0, "items": []}
    try:
        return json.loads(SIGNALS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"signals.json is corrupted: {e}")


def main() -> int:
    if not NEWS_FILE.exists():
        print(f"missing: {NEWS_FILE}", file=sys.stderr)
        print("شغّل أولاً: ./fetch.command", file=sys.stderr)
        return 1

    news = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    items = news.get("items", [])
    print(f"  newsletters source items: {len(items)}", file=sys.stderr)

    new_signals = [to_signal(it) for it in items if it.get("title") or it.get("summary")]
    print(f"  converted to signals:     {len(new_signals)}", file=sys.stderr)

    existing = load_existing_signals()
    kept = [s for s in existing.get("items", []) if not is_newsletter_signal(s)]
    print(f"  preserved non-newsletter signals: {len(kept)}", file=sys.stderr)

    merged = kept + new_signals
    # newest first by posted_at (ISO sorts correctly when normalized)
    merged.sort(key=lambda s: s.get("posted_at", ""), reverse=True)

    SIGNALS_FILE.write_text(
        json.dumps(
            {
                "generated_at": now_iso(),
                "count": len(merged),
                "items": merged,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n✓ {len(merged)} signal مُدمج في {SIGNALS_FILE.relative_to(ROOT)}", file=sys.stderr)

    by_source = {}
    for s in merged:
        by_source.setdefault(s.get("source_name", "?"), 0)
        by_source[s.get("source_name", "?")] += 1
    print("\nالتوزيع:", file=sys.stderr)
    for name, count in sorted(by_source.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:5d}  {name}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
