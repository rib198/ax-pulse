#!/usr/bin/env python3
"""
AX Pulse — AI newsletters RSS aggregator.

Fetches several AI-focused newsletters' RSS feeds, normalizes them
into one unified schema, and writes:
  - data/newsletters/items.json    (every item from every source)
  - data/newsletters/sources.json  (per-source health and counts)

Stdlib only. No pip install required.
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "newsletters"
OUT_FILE = OUT_DIR / "items.json"
SOURCES_FILE = OUT_DIR / "sources.json"

# Curated AI-focused RSS sources. Add or remove freely.
SOURCES = [
    {
        "id": "tldr_ai",
        "name": "TLDR AI",
        "url": "https://tldr.tech/api/rss/ai",
        "ai_focused": True,
    },
    {
        "id": "smol_ai_news",
        "name": "AI News by smol.ai",
        "url": "https://buttondown.email/ainews/rss",
        "ai_focused": True,
    },
    {
        "id": "the_rundown",
        "name": "The Rundown AI",
        "url": "https://www.therundown.ai/feed.xml",
        "ai_focused": True,
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://www.bensbites.co/feed",
        "ai_focused": True,
    },
    {
        "id": "import_ai",
        "name": "Import AI (Jack Clark)",
        "url": "https://jack-clark.net/feed/",
        "ai_focused": True,
    },
    {
        "id": "huggingface_blog",
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "ai_focused": True,
    },
    {
        "id": "anthropic_news",
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/rss.xml",
        "ai_focused": True,
    },
    {
        "id": "openai_blog",
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "ai_focused": True,
    },
    {
        "id": "deepmind_blog",
        "name": "DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "ai_focused": True,
    },
    {
        "id": "simonw",
        "name": "Simon Willison's Weblog",
        "url": "https://simonwillison.net/atom/everything/",
        "ai_focused": False,
    },
    {
        "id": "latent_space",
        "name": "Latent Space",
        "url": "https://www.latent.space/feed",
        "ai_focused": True,
    },
]

# If a feed is not declared ai_focused, items are filtered by these keywords.
AI_KEYWORDS = re.compile(
    r"\b(AI|LLM|GPT|Claude|Gemini|Sora|Anthropic|OpenAI|DeepMind|"
    r"agent|model|ML|machine learning|neural|prompt|chatbot|"
    r"Hugging Face|Mistral|RAG|fine-tun|inference|transformer)",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_url(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AX-Pulse/1.0 (RSS aggregator)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


class TextStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    stripper = TextStripper()
    try:
        stripper.feed(raw)
        out = stripper.text()
    except Exception:
        out = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\s+", " ", out).strip()


def localname(tag: str) -> str:
    """Strip XML namespace from a tag name."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def find_text(parent, *names: str) -> str:
    """Find direct child by local name (any namespace) and return its text."""
    for child in parent:
        if localname(child.tag) in names:
            return (child.text or "").strip()
    return ""


def find_link(parent) -> str:
    """RSS uses <link>text</link>, Atom uses <link href='...'/>."""
    for child in parent:
        if localname(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            return href.strip()
        if child.text:
            return child.text.strip()
    return ""


def parse_feed(xml_bytes: bytes):
    """Return (items, error). Supports both RSS 2.0 and Atom."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        return [], f"parse_error: {exc}"

    items = []
    # RSS 2.0: <rss><channel><item>
    for entry in root.iter():
        if localname(entry.tag) not in ("item", "entry"):
            continue
        title = find_text(entry, "title")
        url = find_link(entry)
        summary_raw = (
            find_text(entry, "description")
            or find_text(entry, "summary")
            or find_text(entry, "content")
        )
        published = (
            find_text(entry, "pubDate")
            or find_text(entry, "published")
            or find_text(entry, "updated")
            or ""
        )
        items.append(
            {
                "title": title,
                "url": url,
                "summary": strip_html(summary_raw)[:600],
                "published_at": published,
            }
        )

    return items, None


def is_ai_relevant(item) -> bool:
    blob = (item.get("title", "") + " " + item.get("summary", ""))[:2000]
    return bool(AI_KEYWORDS.search(blob))


def stable_id(source_id: str, payload: str) -> str:
    """A short stable id, deterministic across runs (sha256, first 16 hex)."""
    h = hashlib.sha256(f"{source_id}|{payload}".encode("utf-8")).hexdigest()
    return f"{source_id}_{h[:16]}"


def to_iso_published(raw: str) -> str:
    """Convert any common feed date string into ISO-8601 UTC, or '' if unknown."""
    if not raw:
        return ""
    raw = raw.strip()
    # RFC 822 (RSS pubDate)
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        pass
    # ISO 8601 (Atom)
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw.replace("Z", "+0000"), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            continue
    return raw  # fall back to whatever was provided


def normalize_item(source, item):
    return {
        "id": stable_id(source["id"], item.get("url") or item.get("title") or ""),
        "source_id": source["id"],
        "source_name": source["name"],
        "source_type": "rss",
        "source_url": item.get("url", ""),
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "published_at": to_iso_published(item.get("published_at", "")),
        "collected_at": now_iso(),
        "verification_status": "auto_verified_rss",
    }


def parse_args():
    p = argparse.ArgumentParser(description="AX Pulse RSS/newsletters aggregator")
    p.add_argument("--max-per-source", type=int, default=40,
                   help="حد أقصى لكل مصدر بعد الفلترة (افتراضي 40)")
    p.add_argument("--days", type=int, default=30,
                   help="نافذة زمنية بالأيام (افتراضي 30، 0 = بلا حد)")
    return p.parse_args()


def published_dt(item):
    """Return aware datetime from normalized published_at, or None."""
    raw = item.get("published_at", "")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def filter_and_cap(normalized_items, days, max_per_source):
    """Apply --days window then per-source cap. Items without dates are kept
    but never sort to the top (they get sentinel ''). Per-source cap keeps the
    newest within each source."""
    cutoff = None
    if days and days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    in_window = []
    for it in normalized_items:
        dt = published_dt(it)
        if cutoff is not None and dt is not None and dt < cutoff:
            continue  # too old
        in_window.append(it)

    # group by source then keep newest N per source
    by_source = {}
    for it in in_window:
        by_source.setdefault(it["source_id"], []).append(it)

    capped = []
    for source_id, items in by_source.items():
        items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        capped.extend(items[:max_per_source])

    capped.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return capped


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    collected = []
    sources_state = []
    started = now_iso()

    for src in SOURCES:
        print(f"  → {src['id']:20s}  {src['url']}", file=sys.stderr)
        status = "ok"
        raw_count = 0
        error = None
        try:
            xml = fetch_url(src["url"])
            items, parse_err = parse_feed(xml)
            if parse_err:
                status = "parse_error"
                error = parse_err
            else:
                for item in items:
                    if not src.get("ai_focused") and not is_ai_relevant(item):
                        continue
                    collected.append(normalize_item(src, item))
                    raw_count += 1
        except urllib.error.HTTPError as exc:
            status = "http_error"
            error = f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            status = "down"
            error = f"network: {exc.reason}"
        except Exception as exc:
            status = "error"
            error = str(exc)

        sources_state.append(
            {
                "id": src["id"],
                "name": src["name"],
                "url": src["url"],
                "type": "rss",
                "last_fetched": now_iso(),
                "items_raw": raw_count,
                "status": status,
                "error": error,
            }
        )
        emoji = "✓" if status == "ok" else "✗"
        print(f"    {emoji} {status:12s}  {raw_count:4d} raw"
              + (f"  ({error})" if error else ""), file=sys.stderr)

    # Apply windowing + per-source cap
    final_items = filter_and_cap(collected, args.days, args.max_per_source)

    # Backfill items_collected per source (after cap)
    counts_after = {}
    for it in final_items:
        counts_after[it["source_id"]] = counts_after.get(it["source_id"], 0) + 1
    for s in sources_state:
        s["items_collected"] = counts_after.get(s["id"], 0)

    ok_sources_count = sum(1 for s in sources_state if s["status"] == "ok")

    OUT_FILE.write_text(
        json.dumps(
            {
                "generated_at": started,
                "total_items": len(final_items),
                "sources_count": len(SOURCES),
                "ok_sources_count": ok_sources_count,
                "filters": {
                    "max_per_source": args.max_per_source,
                    "days": args.days,
                },
                "items": final_items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    SOURCES_FILE.write_text(
        json.dumps(
            {
                "updated_at": started,
                "ok_sources_count": ok_sources_count,
                "total_sources": len(SOURCES),
                "sources": sources_state,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\n✓ {len(final_items)} items (raw: {len(collected)}) من "
        f"{ok_sources_count}/{len(SOURCES)} مصادر · "
        f"window={args.days}d · cap={args.max_per_source}/source",
        file=sys.stderr,
    )
    print(f"✓ تم الكتابة: {OUT_FILE.relative_to(ROOT)}", file=sys.stderr)
    print(f"✓ حالة المصادر: {SOURCES_FILE.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
