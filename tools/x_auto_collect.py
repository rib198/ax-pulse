#!/usr/bin/env python3
"""Auto-collect tweets/posts from X, Bluesky, and Mastodon — all FREE.

No X API needed. Uses three free, no-auth public sources:

  1. Nitter pool — 12 public instances, rotating per request. Primary X
     scraper. RSS-based, free, but several instances are intermittent.
  2. Bluesky AT Protocol — public.api.bsky.app, free, no auth. Many AI
     builders cross-post here. Reliable.
  3. Mastodon public API — per-instance, free, no auth. Researchers like
     @karpathy@hachyderm.io are active here.

Source is auto-detected from the handle format in data/manual_x/watchlist.txt:
  @user                       → X (via Nitter)
  @user.bsky.social           → Bluesky
  @user@instance.tld          → Mastodon

Run:
  python3 tools/x_auto_collect.py            # one-shot
  python3 tools/x_auto_collect.py --pipeline # + run agent pipeline
  python3 tools/x_auto_collect.py --watch N  # poll every N seconds

The X API path is kept dormant — only used if X_BEARER_TOKEN AND
RADAR_USE_X_API=1 are both set. We default to free sources only.

Pure stdlib (urllib, json, xml.etree, html.parser).
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
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
WATCHLIST_PATH = ROOT / "data" / "manual_x" / "watchlist.txt"
ACCOUNTS_PATH = ROOT / "data" / "radar" / "x_focus_accounts.json"
QUERIES_PATH = ROOT / "data" / "manual_x" / "search_queries.json"
ENRICH_SCRIPT = ROOT / "tools" / "x_smart_enrich.py"
RADAR_SCRIPT = ROOT / "tools" / "run_radar_agents.py"

# Expanded Nitter pool — tried in order, first success wins. Lifespan of
# any single instance is short these days; the pool is intentionally wide.
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://xcancel.com",
    "https://nitter.tiekoetter.com",
    "https://nitter.space",
    "https://nitter.cz",
    "https://nitter.fdn.fr",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
    "https://nitter.salastil.com",
    "https://nitter.no-logs.com",
    "https://nitter.net",
]

HTTP_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; RadarAutoCollect/2.0)"


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


def _http_get_json(url: str, headers: dict | None = None, timeout: int = HTTP_TIMEOUT) -> dict | list | None:
    body = _http_get(url, headers, timeout)
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data): self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p"): self.parts.append("\n")


def _strip_html(html: str) -> str:
    if not html:
        return ""
    s = _HTMLStripper()
    try:
        s.feed(html)
    except Exception:
        return re.sub(r"<[^>]+>", "", html).strip()
    return "".join(s.parts).strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- X via Nitter (primary) ----------

def _parse_nitter_rss(xml_text: str) -> list[dict]:
    """Parses Nitter RSS feed → normalized tweet shape."""
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
        m = re.search(r"/status/(\d+)", link)
        tweet_id = m.group(1) if m else None
        text = _strip_html(desc or title)
        x_url = re.sub(r"https?://[^/]+", "https://x.com", link)
        items.append({
            "tweet_id":         tweet_id,
            "author_handle":    author.lstrip("@"),
            "author_name":      "",
            "text":             text or title,
            "url":              x_url,
            "posted_at":        pub or None,
            "collected_at":     _now_iso(),
            "source_type":      "nitter",
            "platform":         "x",
            "query":            "",
            "matched_keywords": [],
            "public_metrics":   {"likes": 0, "reposts": 0, "replies": 0, "quotes": 0, "views": None},
            "pain_signal_score": 0,
            "opportunity_tags": [],
            "verification_status": "public_x_page",
            "lang":             "",
        })
    return [i for i in items if i.get("tweet_id")]


def nitter_account(handle: str, max_results: int) -> list[dict]:
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


def nitter_search(query: str, max_results: int) -> list[dict]:
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


# ---------- Bluesky AT Protocol (free, no auth) ----------

def bluesky_account(handle: str, max_results: int) -> list[dict]:
    """Fetch a Bluesky user's recent posts via the public AppView API.
    Handle format: 'user.bsky.social' or a custom domain handle.
    Endpoint: public.api.bsky.app — no authentication required."""
    h = handle.lstrip("@")
    url = (
        "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
        f"?actor={quote_plus(h)}&limit={min(50, max(5, max_results))}"
    )
    data = _http_get_json(url, timeout=12)
    if not data or "feed" not in data:
        return []
    items = []
    for entry in data.get("feed") or []:
        post = entry.get("post") or {}
        record = post.get("record") or {}
        author = post.get("author") or {}
        author_handle = author.get("handle") or h
        cid = post.get("cid") or ""
        uri = post.get("uri") or ""
        post_rkey = uri.split("/")[-1] if uri else ""
        items.append({
            "tweet_id":         cid,
            "author_handle":    author_handle,
            "author_name":      author.get("displayName") or "",
            "text":             record.get("text") or "",
            "url":              f"https://bsky.app/profile/{author_handle}/post/{post_rkey}" if post_rkey else "",
            "posted_at":        record.get("createdAt"),
            "collected_at":     _now_iso(),
            "source_type":      "bluesky",
            "platform":         "bluesky",
            "query":            f"from:{h}",
            "matched_keywords": [],
            "public_metrics":   {
                "likes":   post.get("likeCount") or 0,
                "reposts": post.get("repostCount") or 0,
                "replies": post.get("replyCount") or 0,
                "quotes":  post.get("quoteCount") or 0,
                "views":   None,
            },
            "pain_signal_score": 0,
            "opportunity_tags": [],
            "verification_status": "bluesky_public",
            "lang":             record.get("langs", [""])[0] if record.get("langs") else "",
        })
    return [i for i in items if i.get("tweet_id")][:max_results]


# ---------- Mastodon public API (free, no auth) ----------

def mastodon_account(full_handle: str, max_results: int) -> list[dict]:
    """Fetch a Mastodon user's recent statuses. Handle format:
    'user@instance.tld'. Two-call sequence: lookup → statuses."""
    h = full_handle.lstrip("@")
    if "@" not in h:
        return []
    user, instance = h.rsplit("@", 1)
    instance = instance.strip().lower()
    user = user.strip()
    if not user or not instance:
        return []
    lookup = _http_get_json(f"https://{instance}/api/v1/accounts/lookup?acct={quote_plus(user)}", timeout=10)
    if not lookup or not lookup.get("id"):
        return []
    acc_id = lookup["id"]
    statuses_url = (
        f"https://{instance}/api/v1/accounts/{acc_id}/statuses"
        f"?limit={min(40, max(5, max_results))}"
        "&exclude_replies=true&exclude_reblogs=true"
    )
    statuses = _http_get_json(statuses_url, timeout=10) or []
    if not isinstance(statuses, list):
        return []
    items = []
    for s in statuses:
        items.append({
            "tweet_id":         s.get("id"),
            "author_handle":    user,
            "author_name":      lookup.get("display_name") or "",
            "text":             _strip_html(s.get("content") or ""),
            "url":              s.get("url") or s.get("uri") or "",
            "posted_at":        s.get("created_at"),
            "collected_at":     _now_iso(),
            "source_type":      "mastodon",
            "platform":         "mastodon",
            "query":            f"from:{user}@{instance}",
            "matched_keywords": [],
            "public_metrics":   {
                "likes":   s.get("favourites_count") or 0,
                "reposts": s.get("reblogs_count") or 0,
                "replies": s.get("replies_count") or 0,
                "quotes":  0,
                "views":   None,
            },
            "pain_signal_score": 0,
            "opportunity_tags": [],
            "verification_status": "mastodon_public",
            "lang":             s.get("language") or "",
        })
    return [i for i in items if i.get("tweet_id")][:max_results]


# ---------- Optional X API v2 (dormant by default) ----------

def x_api_search(query: str, max_results: int, token: str) -> list[dict]:
    """Only invoked when RADAR_USE_X_API=1 AND X_BEARER_TOKEN is set.
    Default radar behavior is free Nitter+Bluesky+Mastodon."""
    params = {
        "query": query,
        "max_results": str(max(10, min(100, max_results))),
        "tweet.fields": "id,author_id,created_at,public_metrics,lang",
        "expansions": "author_id",
        "user.fields": "username,name",
    }
    url = "https://api.twitter.com/2/tweets/search/recent?" + urlencode(params)
    req = Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception:
        return []
    tweets = payload.get("data") or []
    users = {u["id"]: u for u in (payload.get("includes") or {}).get("users") or []}
    out = []
    for t in tweets:
        u = users.get(t.get("author_id")) or {}
        m = t.get("public_metrics") or {}
        out.append({
            "tweet_id":      t.get("id"),
            "author_handle": u.get("username") or "",
            "author_name":   u.get("name") or "",
            "text":          t.get("text") or "",
            "url":           f"https://x.com/{u.get('username','i')}/status/{t.get('id')}",
            "posted_at":     t.get("created_at"),
            "collected_at":  _now_iso(),
            "source_type":   "x_api",
            "platform":      "x",
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
    return out


# ---------- Handle format detection ----------

def classify_handle(raw: str) -> tuple[str, str]:
    """Returns (platform, normalized_handle). Auto-detects from format.

      user.bsky.social         → bluesky
      user.bsky.team           → bluesky
      *.bsky.app               → bluesky
      user@instance.tld        → mastodon
      anything else            → x
    """
    h = raw.strip().lstrip("@")
    if not h:
        return ("x", "")
    if h.endswith(".bsky.social") or h.endswith(".bsky.team") or ".bsky." in h:
        return ("bluesky", h)
    if "@" in h:
        return ("mastodon", h)
    return ("x", h)


# ---------- Store merge ----------

def merge_into_store(new_items: list[dict]) -> dict:
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

    added = updated = 0
    for it in new_items:
        tid = it.get("tweet_id")
        if not tid:
            continue
        if tid in seen:
            idx = seen[tid]
            old = existing[idx]
            old_m = old.get("public_metrics") or {}
            new_m = it.get("public_metrics") or {}
            for k, v in new_m.items():
                if v and v > (old_m.get(k) or 0):
                    old_m[k] = v
            old["public_metrics"] = old_m
            old["collected_at"] = it.get("collected_at") or old.get("collected_at")
            updated += 1
        else:
            existing.append(it)
            seen[tid] = len(existing) - 1
            added += 1

    existing.sort(key=lambda p: p.get("collected_at") or "", reverse=True)
    existing = existing[:500]

    doc["items"] = existing
    doc["collected_at"] = _now_iso()
    POSTS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(existing)}


# ---------- Plan + execute ----------

def _parse_watchlist(text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    section = "watchlist"
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            section = line.lstrip("#").strip() or "watchlist"
            continue
        if line.startswith("#"):
            continue
        handle = line.split()[0] if line else ""
        if handle and handle.lower() not in seen:
            seen.add(handle.lower())
            pairs.append((handle, section))
    return pairs


def build_plan() -> list[tuple[str, str, int, str]]:
    """Returns list of (kind, target, max_results, section).
    kind ∈ {x_account, bluesky_account, mastodon_account, query}."""
    plan: list[tuple[str, str, int, str]] = []
    accounts: list[tuple[str, str]] = []

    if WATCHLIST_PATH.exists():
        try:
            accounts.extend(_parse_watchlist(WATCHLIST_PATH.read_text("utf-8")))
        except Exception as e:
            print(f"⚠ could not parse watchlist.txt: {e}", file=sys.stderr)

    if not accounts and ACCOUNTS_PATH.exists():
        try:
            accs = json.loads(ACCOUNTS_PATH.read_text("utf-8")).get("accounts") or []
            for a in accs:
                uname = a.get("username") if isinstance(a, dict) else str(a).lstrip("@")
                if uname:
                    accounts.append((uname, "watchlist"))
        except Exception:
            pass

    per_account = int(os.environ.get("X_TWEETS_PER_ACCOUNT", "0"))
    if per_account <= 0:
        per_account = 10 if len(accounts) <= 30 else (7 if len(accounts) <= 60 else 5)

    for handle, section in accounts:
        platform, norm = classify_handle(handle)
        kind = f"{platform}_account"
        plan.append((kind, norm, per_account, section))

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
    plan = build_plan()
    if not plan:
        print("nothing to collect — empty plan")
        return {"collected": 0}

    # ---- Per-run sampling cap ----
    # Watchlist grew to 700+ handles. With each Nitter fetch capped at the
    # 10-second HTTP_TIMEOUT, a full sweep can take ~2 hours in the worst
    # case — way beyond the 6-min GitHub Actions step budget. So each cron
    # run takes a random sample (default 80) and the full list rotates
    # across runs. Operators can override via RADAR_X_MAX_HANDLES.
    try:
        cap = int(os.environ.get("RADAR_X_MAX_HANDLES", "80"))
    except ValueError:
        cap = 80
    if cap > 0 and len(plan) > cap:
        import random
        random.shuffle(plan)
        original = len(plan)
        plan = plan[:cap]
        print(f"sampled {len(plan)} of {original} plan items "
              f"(set RADAR_X_MAX_HANDLES to override; 0 = no cap)")

    counts = {"x_account": 0, "bluesky_account": 0, "mastodon_account": 0, "query": 0}
    for kind, *_ in plan:
        counts[kind] = counts.get(kind, 0) + 1
    print(f"plan: {len(plan)} items  "
          f"(X: {counts['x_account']}, Bluesky: {counts['bluesky_account']}, "
          f"Mastodon: {counts['mastodon_account']}, queries: {counts['query']})")

    use_x_api = os.environ.get("RADAR_USE_X_API", "").lower() in ("1", "true", "yes")
    x_token = os.environ.get("X_BEARER_TOKEN") if use_x_api else None
    if use_x_api and not x_token:
        print("⚠ RADAR_USE_X_API=1 set but X_BEARER_TOKEN missing — staying free-only")
    elif not use_x_api:
        print("free-only mode — Nitter / Bluesky / Mastodon (X API is opt-in via RADAR_USE_X_API=1)")

    all_new: list[dict] = []
    stats = {"nitter_ok": 0, "nitter_fail": 0,
             "bluesky_ok": 0, "bluesky_fail": 0,
             "mastodon_ok": 0, "mastodon_fail": 0,
             "x_api_ok": 0, "x_api_fail": 0}

    for kind, target, n, section in plan:
        items: list[dict] = []

        if kind == "bluesky_account":
            items = bluesky_account(target, n)
            stats["bluesky_ok" if items else "bluesky_fail"] += 1
        elif kind == "mastodon_account":
            items = mastodon_account(target, n)
            stats["mastodon_ok" if items else "mastodon_fail"] += 1
        elif kind == "x_account":
            if x_token:
                items = x_api_search(f"from:{target} -is:retweet", n, x_token)
                if items: stats["x_api_ok"] += 1
                else:     stats["x_api_fail"] += 1
            if not items:
                items = nitter_account(target, n)
                stats["nitter_ok" if items else "nitter_fail"] += 1
        elif kind == "query":
            if x_token:
                items = x_api_search(target, n, x_token)
                if items: stats["x_api_ok"] += 1
                else:     stats["x_api_fail"] += 1
            if not items:
                items = nitter_search(target, n)
                stats["nitter_ok" if items else "nitter_fail"] += 1

        for it in items:
            it["section"] = section

        platform = kind.replace("_account", "")
        label = target[:48]
        if items:
            print(f"  ✓ {platform:9} {label:<48} → {len(items)} via {items[0]['source_type']}")
        else:
            print(f"  · {platform:9} {label:<48} → 0")
        all_new.extend(items)
        time.sleep(0.3)

    merge = merge_into_store(all_new)
    print(f"merged: +{merge['added']} new, {merge['updated']} updated, {merge['total']} total")
    print(f"sources: "
          f"nitter {stats['nitter_ok']}✓/{stats['nitter_fail']}✗ · "
          f"bluesky {stats['bluesky_ok']}✓/{stats['bluesky_fail']}✗ · "
          f"mastodon {stats['mastodon_ok']}✓/{stats['mastodon_fail']}✗"
          + (f" · x_api {stats['x_api_ok']}✓/{stats['x_api_fail']}✗" if x_token else ""))

    if ENRICH_SCRIPT.exists():
        print("→ smart enrich…")
        r = subprocess.run([sys.executable, str(ENRICH_SCRIPT)], capture_output=True, text=True)
        last = r.stdout.strip().splitlines()[-1] if r.stdout else "(no output)"
        print("  " + last)
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
        for line in r.stdout.splitlines()[-3:]:
            if line.strip():
                print("  " + line.strip())
    else:
        print(f"  ⚠ pipeline exited {r.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-collect X/Bluesky/Mastodon posts — free, no X API needed")
    parser.add_argument("--pipeline", action="store_true", help="Run full agent pipeline after collection")
    parser.add_argument("--watch", type=int, default=0, metavar="SECONDS",
                        help="Poll continuously, every N seconds (default: one-shot)")
    args = parser.parse_args()

    while True:
        started = time.time()
        print(f"=== auto-collect — {_now_iso()} ===")
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
