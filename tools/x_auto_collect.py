#!/usr/bin/env python3
"""Auto-collect X tweets and route them straight to the radar.

Replaces manual Safari capture. One command:
  python3 tools/x_auto_collect.py            # collect + enrich
  python3 tools/x_auto_collect.py --pipeline # collect + enrich + run agents
  python3 tools/x_auto_collect.py --watch 600 # poll every N seconds

Collection strategy (tries each in order, until tweets are gathered):
  1. X API v2 recent search        (if X_BEARER_TOKEN env is set)
  2. Public Nitter instances (RSS) (best-effort, often blocked in 2024+)
  3. Logs and continues — never crashes the pipeline

Inputs:
  data/radar/x_focus_accounts.json    → which accounts to watch
  data/manual_x/search_queries.json   → which keyword queries to run

Output (idempotent, merges into existing data):
  data/manual_x/posts.json            → primary tweet store, dedup by tweet_id

Then automatically:
  → runs tools/x_smart_enrich.py   (re-score, classify, dedupe)
  → optionally runs pulse-radar-agents (--pipeline)

Pure stdlib: urllib, json, xml.etree. No pip install needed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
ACCOUNTS_PATH = ROOT / "data" / "radar" / "x_focus_accounts.json"
QUERIES_PATH = ROOT / "data" / "manual_x" / "search_queries.json"
ENRICH_SCRIPT = ROOT / "tools" / "x_smart_enrich.py"
RADAR_SCRIPT = ROOT / "tools" / "run_radar_agents.py"

# Nitter instance pool — tried in order, first success wins per query.
# Most are flaky in 2026; we rotate aggressively.
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.cz",
    "https://nitter.fdn.fr",
    "https://nitter.kavin.rocks",
    "https://nitter.net",
]

HTTP_TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (compatible; RadarAutoCollect/1.0)"


# ---------- HTTP helpers ----------

def _http_get(url: str, headers: dict | None = None, timeout: int = HTTP_TIMEOUT) -> str | None:
    req = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, ConnectionError):
        return None
    except Exception:
        return None


# ---------- X API v2 source ----------

def x_api_search(query: str, max_results: int, token: str) -> list[dict]:
    """Recent-search endpoint. Returns raw tweet dicts (already X API schema).
    Requires Basic tier or higher — Free tier doesn't expose this endpoint."""
    params = {
        "query": query,
        "max_results": str(max(10, min(100, max_results))),
        "tweet.fields": "id,author_id,created_at,public_metrics,lang,referenced_tweets",
        "expansions": "author_id",
        "user.fields": "id,username,name,verified,public_metrics,description",
    }
    url = "https://api.twitter.com/2/tweets/search/recent?" + urlencode(params)
    req = Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        print(f"   [x-api] HTTP {e.code}: {body[:120]}", file=sys.stderr)
        return []
    except (URLError, TimeoutError, ConnectionError) as e:
        print(f"   [x-api] network: {e}", file=sys.stderr)
        return []
    tweets = payload.get("data") or []
    users = {u["id"]: u for u in (payload.get("includes") or {}).get("users") or []}

    normalized = []
    for t in tweets:
        u = users.get(t.get("author_id")) or {}
        m = t.get("public_metrics") or {}
        normalized.append({
            "tweet_id":      t.get("id"),
            "author_handle": u.get("username") or "",
            "author_name":   u.get("name") or "",
            "text":          t.get("text") or "",
            "url":           f"https://x.com/{u.get('username','i')}/status/{t.get('id')}",
            "posted_at":     t.get("created_at"),
            "collected_at":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_type":   "x_api",
            "query":         query,
            "matched_keywords": [],
            "public_metrics": {
                "likes":   m.get("like_count") or 0,
                "reposts": m.get("retweet_count") or 0,
                "replies": m.get("reply_count") or 0,
                "quotes":  m.get("quote_count") or 0,
                "views":   m.get("impression_count") or 0,
            },
            "pain_signal_score": 0,
            "opportunity_tags": [],
            "verification_status": "x_api_v2",
            "lang": t.get("lang") or "",
        })
    return normalized


# ---------- Nitter source (RSS fallback) ----------

def _parse_nitter_rss(xml_text: str) -> list[dict]:
    """Parses Nitter RSS feed into our normalized tweet shape."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns_dc = "{http://purl.org/dc/elements/1.1/}"
    items = []
    for item in root.iterfind(".//item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        author = (item.findtext(ns_dc + "creator") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        # Tweet ID lives at the end of the link path
        m = re.search(r"/status/(\d+)", link)
        tweet_id = m.group(1) if m else None
        # Strip HTML from description (very simple)
        text = re.sub(r"<[^>]+>", "", desc or title).strip()
        # Nitter URL → canonical X URL
        x_url = re.sub(r"https?://[^/]+", "https://x.com", link)
        items.append({
            "tweet_id":      tweet_id,
            "author_handle": author.lstrip("@"),
            "author_name":   "",
            "text":          text or title,
            "url":           x_url,
            "posted_at":     pub or None,
            "collected_at":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_type":   "nitter",
            "query":         "",  # caller fills
            "matched_keywords": [],
            "public_metrics": {"likes": 0, "reposts": 0, "replies": 0, "quotes": 0, "views": None},
            "pain_signal_score": 0,
            "opportunity_tags": [],
            "verification_status": "public_x_page",
            "lang": "",
        })
    return [i for i in items if i.get("tweet_id")]


def nitter_search(query: str, max_results: int) -> list[dict]:
    """Try public Nitter instances until one returns content. Best-effort."""
    encoded = quote_plus(query)
    for base in NITTER_INSTANCES:
        url = f"{base}/search/rss?f=tweets&q={encoded}"
        xml = _http_get(url, timeout=10)
        if not xml or "<item>" not in xml:
            continue
        items = _parse_nitter_rss(xml)
        if items:
            for it in items:
                it["query"] = query
            return items[:max_results]
    return []


def nitter_account(handle: str, max_results: int) -> list[dict]:
    """Get a single account's recent tweets via Nitter RSS."""
    handle = handle.lstrip("@")
    for base in NITTER_INSTANCES:
        url = f"{base}/{handle}/rss"
        xml = _http_get(url, timeout=10)
        if not xml or "<item>" not in xml:
            continue
        items = _parse_nitter_rss(xml)
        if items:
            for it in items:
                it["query"] = f"from:@{handle}"
            return items[:max_results]
    return []


# ---------- Merge into posts.json ----------

def merge_into_store(new_items: list[dict]) -> dict:
    """Dedup by tweet_id. Preserve existing fields (enrichment, scores).
    Append new items at the end; smart-enrich will re-sort by radar_score."""
    if POSTS_PATH.exists():
        try:
            doc = json.loads(POSTS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {"items": []}
    else:
        doc = {"items": []}
    POSTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing = doc.get("items") or []
    seen = {p.get("tweet_id"): i for i, p in enumerate(existing) if p.get("tweet_id")}

    added = 0
    updated = 0
    for it in new_items:
        tid = it.get("tweet_id")
        if not tid:
            continue
        if tid in seen:
            # Light update: refresh metrics, keep enrichment intact
            idx = seen[tid]
            old = existing[idx]
            old_metrics = old.get("public_metrics") or {}
            new_metrics = it.get("public_metrics") or {}
            # Only update if newer metrics are non-zero (don't downgrade)
            for k, v in new_metrics.items():
                if v and (not old_metrics.get(k) or v > (old_metrics.get(k) or 0)):
                    old_metrics[k] = v
            old["public_metrics"] = old_metrics
            old["collected_at"] = it.get("collected_at") or old.get("collected_at")
            updated += 1
        else:
            existing.append(it)
            seen[tid] = len(existing) - 1
            added += 1

    # Trim to most recent 500 (by collected_at) to avoid unbounded growth
    existing.sort(key=lambda p: p.get("collected_at") or "", reverse=True)
    existing = existing[:500]

    doc["items"] = existing
    doc["collected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    POSTS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(existing)}


# ---------- Plan + execute ----------

def build_plan() -> list[tuple[str, str, int, str]]:
    """Returns list of (kind, query_or_handle, max_results, section)."""
    plan: list[tuple[str, str, int, str]] = []
    # Accounts
    if ACCOUNTS_PATH.exists():
        try:
            accs = json.loads(ACCOUNTS_PATH.read_text("utf-8")).get("accounts") or []
        except Exception:
            accs = []
        for a in accs:
            uname = a.get("username") if isinstance(a, dict) else str(a).lstrip("@")
            if uname:
                plan.append(("account", uname, 10, "watchlist"))
    # Keyword searches
    if QUERIES_PATH.exists():
        try:
            qcfg = json.loads(QUERIES_PATH.read_text("utf-8"))
            per_q = int(qcfg.get("tweets_per_query") or 15)
            for entry in qcfg.get("queries") or []:
                if isinstance(entry, str):
                    plan.append(("query", entry, per_q, "search"))
                elif isinstance(entry, dict) and entry.get("q"):
                    plan.append(("query", entry["q"], per_q, entry.get("section") or "search"))
        except Exception:
            pass
    return plan


def run_one_round() -> dict:
    token = os.environ.get("X_BEARER_TOKEN")
    plan = build_plan()
    if not plan:
        print("nothing to collect — empty plan (no accounts or queries configured)")
        return {"collected": 0}

    print(f"plan: {len(plan)} items "
          f"({sum(1 for k, *_ in plan if k == 'account')} accounts, "
          f"{sum(1 for k, *_ in plan if k == 'query')} queries)")

    if not token:
        print("⚠ X_BEARER_TOKEN not set — will only try public Nitter (best-effort, often blocked)")

    all_new: list[dict] = []
    stats = {"x_api_hits": 0, "x_api_miss": 0, "nitter_hits": 0, "nitter_miss": 0}

    for kind, target, n, section in plan:
        items: list[dict] = []
        # Try X API first
        if token and kind == "query":
            items = x_api_search(target, n, token)
            stats["x_api_hits" if items else "x_api_miss"] += 1
        elif token and kind == "account":
            items = x_api_search(f"from:{target} -is:retweet", n, token)
            stats["x_api_hits" if items else "x_api_miss"] += 1

        # Fallback to Nitter
        if not items:
            if kind == "account":
                items = nitter_account(target, n)
            else:
                items = nitter_search(target, n)
            stats["nitter_hits" if items else "nitter_miss"] += 1

        # Tag with section for the radar
        for it in items:
            it["section"] = section

        if items:
            print(f"  ✓ {kind:8} {target[:50]:<50} → {len(items)} via {items[0]['source_type']}")
        else:
            print(f"  · {kind:8} {target[:50]:<50} → 0")
        all_new.extend(items)
        time.sleep(0.4)   # gentle pacing — avoid X rate limits

    merge = merge_into_store(all_new)
    print(f"merged: +{merge['added']} new, {merge['updated']} updated, {merge['total']} total in store")
    print(f"sources: x_api {stats['x_api_hits']}✓/{stats['x_api_miss']}✗ · "
          f"nitter {stats['nitter_hits']}✓/{stats['nitter_miss']}✗")

    # Auto-enrich
    if ENRICH_SCRIPT.exists():
        print("→ running smart enrich…")
        r = subprocess.run([sys.executable, str(ENRICH_SCRIPT)], capture_output=True, text=True)
        print("  " + (r.stdout.strip().splitlines()[-1] if r.stdout else "(no output)"))
        if r.returncode != 0:
            print(f"  ⚠ enrich exited {r.returncode}: {r.stderr[:200]}")
    return {"collected": merge["added"], "updated": merge["updated"], **stats}


def run_pipeline_after():
    if not RADAR_SCRIPT.exists():
        return
    print("→ running radar agent pipeline (--skip-collect)…")
    args = [sys.executable, str(RADAR_SCRIPT), "--skip-collect"]
    if not os.environ.get("OPENAI_API_KEY"):
        args.append("--no-openai")
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode == 0:
        # Show just the summary line
        for line in r.stdout.splitlines()[-3:]:
            if line.strip():
                print("  " + line.strip())
    else:
        print(f"  ⚠ pipeline exited {r.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-collect X tweets and route to radar")
    parser.add_argument("--pipeline", action="store_true", help="Run full agent pipeline after collection")
    parser.add_argument("--watch", type=int, default=0, metavar="SECONDS",
                        help="Poll continuously, every N seconds (default: one-shot)")
    parser.add_argument("--no-fallback", action="store_true", help="Skip Nitter fallback (X API only)")
    args = parser.parse_args()

    while True:
        started = time.time()
        print(f"=== auto-collect — {datetime.now(timezone.utc).isoformat(timespec='seconds')} ===")
        try:
            run_one_round()
            if args.pipeline:
                run_pipeline_after()
        except Exception as e:
            print(f"⚠ run failed: {e}")
        if not args.watch:
            return 0
        elapsed = time.time() - started
        sleep_s = max(15, args.watch - int(elapsed))
        print(f"sleeping {sleep_s}s…")
        time.sleep(sleep_s)


if __name__ == "__main__":
    raise SystemExit(main())
