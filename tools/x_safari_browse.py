#!/usr/bin/env python3
"""Drive Safari like a human, extract tweets, route them to the radar.

This is the "manual browsing as an expert, automated" path. No API,
no Nitter, no third-party scrapers. We use the Safari you're already
logged into.

How it works:
  1. Read X handles from data/manual_x/watchlist.txt (skips @bsky and
     @user@instance entries — those go to Bluesky/Mastodon collectors).
  2. For each handle:
     a. Tell Safari to open https://x.com/<handle> in its front window.
     b. Wait for the timeline to render.
     c. Run tools/x_extract.js in the page (same DOM the bookmarklet uses).
     d. Scroll a few times to load more tweets, extract each time.
     e. Dedupe by tweet_id, merge into data/manual_x/posts.json.
  3. After all handles: run x_smart_enrich.py.
  4. Optional: --pipeline to run the full radar agent pipeline.

One-time macOS setup (required):
  Safari → Settings → Advanced → check "Show Develop menu in menu bar"
  Develop menu → "Allow JavaScript from Apple Events"
  (On macOS Sequoia you may also be prompted the first time you run this
   to allow Terminal to control Safari — accept it.)

Run:
  python3 tools/x_safari_browse.py                 # all X handles
  python3 tools/x_safari_browse.py --only sama,karpathy   # subset
  python3 tools/x_safari_browse.py --pipeline      # + run agents
  python3 tools/x_safari_browse.py --max 30        # cap handles per run

Login-wall detection: if Safari returns is_login_wall=true for more than
two handles in a row, we stop and remind you to log in (no fake data).

This is the heaviest collector — expect ~5-10 seconds per handle. Run
it on your machine, not in CI. The cron path still uses Nitter/Bluesky/
Mastodon for unattended runs.
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

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_JS = ROOT / "tools" / "x_extract.js"
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
WATCHLIST_PATH = ROOT / "data" / "manual_x" / "watchlist.txt"
ENRICH_SCRIPT = ROOT / "tools" / "x_smart_enrich.py"
RADAR_SCRIPT = ROOT / "tools" / "run_radar_agents.py"

PAGE_LOAD_SECS = 6        # initial wait for X to render the timeline
SCROLL_PASSES = 3         # number of scrolls per handle (each gets more tweets)
SCROLL_WAIT = 2.5         # pause between scrolls
HANDLE_PAUSE = 0.8        # gentle pacing between handles
MAX_OSASCRIPT_TIMEOUT = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- AppleScript driver ----------

def _osascript(script: str, timeout: int = MAX_OSASCRIPT_TIMEOUT) -> str:
    """Run an AppleScript via osascript and return stdout."""
    r = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        msg = (r.stderr or "").strip()
        raise RuntimeError(f"osascript failed: {msg}")
    return r.stdout.strip()


def safari_open_url(url: str) -> None:
    """Tell Safari to navigate the front document to URL (creates one if none)."""
    script = f'''
tell application "Safari"
    activate
    if (count of documents) = 0 then
        make new document with properties {{URL:"{url}"}}
    else
        set URL of front document to "{url}"
    end if
end tell
'''
    _osascript(script)


def safari_run_js(js: str) -> str:
    """Run JS in the front Safari document, return its string result.
    Requires Develop → Allow JavaScript from Apple Events."""
    # Escape backslashes and double-quotes for AppleScript string literal.
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "Safari" to return (do JavaScript "{escaped}" in front document)'
    return _osascript(script)


def safari_scroll() -> None:
    """Scroll the front Safari document down one viewport."""
    js = "window.scrollBy(0, Math.max(400, Math.floor(window.innerHeight * 0.85)));"
    safari_run_js(js)


# ---------- Watchlist parsing (X-only subset) ----------

def parse_x_handles(path: Path) -> list[tuple[str, str]]:
    """Parse watchlist.txt and return [(handle, section)] for X handles only.
    Skips Bluesky (*.bsky.social) and Mastodon (user@instance) entries."""
    if not path.exists():
        return []
    out: list[tuple[str, str]] = []
    section = "watchlist"
    seen = set()
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            section = line.lstrip("#").strip() or "watchlist"
            continue
        if line.startswith("#"):
            continue
        handle = line.split()[0].lstrip("@")
        if not handle:
            continue
        # Skip non-X handles
        if ".bsky.social" in handle or ".bsky.team" in handle or ".bsky." in handle:
            continue
        if "@" in handle:
            continue
        if handle.lower() in seen:
            continue
        seen.add(handle.lower())
        out.append((handle, section))
    return out


# ---------- Per-handle browse loop ----------

def collect_from_handle(handle: str, section: str, extract_js: str) -> list[dict]:
    """Open profile, scroll, extract repeatedly, return deduped post dicts."""
    url = f"https://x.com/{handle}"
    print(f"  → {handle} ({section}) …", end="", flush=True)
    try:
        safari_open_url(url)
    except Exception as e:
        print(f"  open failed: {e}")
        return []

    time.sleep(PAGE_LOAD_SECS)

    by_id: dict[str, dict] = {}
    login_wall = False

    for pass_idx in range(SCROLL_PASSES + 1):  # initial + scrolls
        try:
            raw = safari_run_js(extract_js)
        except subprocess.TimeoutExpired:
            print(f"  timeout on pass {pass_idx}")
            break
        except RuntimeError as e:
            print(f"  js failed: {e}")
            break

        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}

        if payload.get("is_login_wall"):
            login_wall = True
            break

        for p in payload.get("posts") or []:
            tid = p.get("tweet_id")
            if tid and tid not in by_id:
                # Existing radar schema normalization
                by_id[tid] = {
                    "tweet_id":         tid,
                    "author_handle":    p.get("author_handle") or handle,
                    "author_name":      "",
                    "text":             p.get("text") or "",
                    "url":              p.get("url") or url,
                    "posted_at":        p.get("posted_at"),
                    "collected_at":     p.get("collected_at") or _now_iso(),
                    "source_type":      "safari_browse",
                    "platform":         "x",
                    "section":          section,
                    "query":            f"profile:@{handle}",
                    "matched_keywords": [],
                    "public_metrics": {
                        "likes":   p.get("likes") or 0,
                        "reposts": p.get("retweets") or 0,
                        "replies": p.get("replies") or 0,
                        "quotes":  0,
                        "views":   None,
                    },
                    "pain_signal_score": 0,
                    "opportunity_tags": [],
                    "verification_status": "safari_browse",
                    "lang":             "",
                }

        if pass_idx < SCROLL_PASSES:
            try: safari_scroll()
            except Exception: break
            time.sleep(SCROLL_WAIT)

    items = list(by_id.values())
    status = "login wall" if login_wall else f"{len(items)} tweets"
    print(f"  {status}")
    return [] if login_wall else items


# ---------- Store merge ----------

def merge_into_posts(new_items: list[dict]) -> dict:
    if POSTS_PATH.exists():
        try:
            doc = json.loads(POSTS_PATH.read_text("utf-8"))
        except json.JSONDecodeError:
            doc = {"items": []}
    else:
        doc = {"items": []}
    POSTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing = doc.get("items") or []
    by_id = {p.get("tweet_id"): i for i, p in enumerate(existing) if p.get("tweet_id")}
    added = updated = 0

    for it in new_items:
        tid = it.get("tweet_id")
        if not tid:
            continue
        if tid in by_id:
            old = existing[by_id[tid]]
            old_m = old.get("public_metrics") or {}
            for k, v in (it.get("public_metrics") or {}).items():
                if v and v > (old_m.get(k) or 0):
                    old_m[k] = v
            old["public_metrics"] = old_m
            old["collected_at"] = it.get("collected_at")
            updated += 1
        else:
            existing.append(it)
            by_id[tid] = len(existing) - 1
            added += 1

    existing.sort(key=lambda p: p.get("collected_at") or "", reverse=True)
    existing = existing[:500]

    doc["items"] = existing
    doc["collected_at"] = _now_iso()
    POSTS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(existing)}


# ---------- Setup check ----------

def check_safari_access() -> bool:
    """Try a no-op AppleScript to see if we have permission to drive Safari."""
    try:
        out = _osascript('tell application "Safari" to return name', timeout=8)
        return "Safari" in out
    except subprocess.TimeoutExpired:
        return False
    except RuntimeError as e:
        msg = str(e)
        if "not authorized" in msg.lower() or "1743" in msg:
            print("\n⚠ Terminal is not authorized to control Safari.")
            print("   System Settings → Privacy & Security → Automation → Terminal → toggle Safari.")
        return False


def check_js_from_events() -> str | None:
    """Returns None if JS-from-Apple-Events works, else an error message."""
    try:
        out = safari_run_js("'js_ok'")
        if "js_ok" in out:
            return None
        return f"unexpected js output: {out[:60]}"
    except RuntimeError as e:
        msg = str(e)
        if "JavaScript through" in msg or "Apple Events" in msg or "Allow" in msg:
            return ("Develop → Allow JavaScript from Apple Events is OFF.\n"
                    "   Enable: Safari → Settings → Advanced → Show Develop menu.\n"
                    "   Then: Develop → Allow JavaScript from Apple Events.")
        return msg


# ---------- Main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Drive Safari to browse X like a human.")
    parser.add_argument("--only", help="Comma-separated handle subset (overrides watchlist filter)")
    parser.add_argument("--max", type=int, default=0, help="Cap handles processed this run")
    parser.add_argument("--pipeline", action="store_true", help="Run radar agent pipeline after enrich")
    parser.add_argument("--no-enrich", action="store_true", help="Skip x_smart_enrich after collection")
    parser.add_argument("--skip-checks", action="store_true", help="Skip Safari/Apple Events probes (use at own risk)")
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("This tool needs macOS Safari. On Linux/CI use x_auto_collect.py (Nitter/Bluesky/Mastodon).")
        return 1

    if not args.skip_checks:
        if not check_safari_access():
            print("Cannot reach Safari via AppleScript. Open Safari once manually then re-run.")
            return 1
        err = check_js_from_events()
        if err:
            print(f"⚠ {err}")
            return 1

    extract_js = EXTRACT_JS.read_text("utf-8")

    handles = parse_x_handles(WATCHLIST_PATH)
    if args.only:
        wanted = {h.strip().lstrip("@").lower() for h in args.only.split(",")}
        handles = [(h, s) for (h, s) in handles if h.lower() in wanted]
    if args.max and args.max > 0:
        handles = handles[: args.max]

    if not handles:
        print("No X handles to browse. Check watchlist.txt or --only.")
        return 1

    print(f"=== Safari browse — {_now_iso()} ===")
    print(f"will visit {len(handles)} X handle(s), ~{PAGE_LOAD_SECS + SCROLL_PASSES * SCROLL_WAIT:.0f}s each")

    all_new: list[dict] = []
    consecutive_login_walls = 0
    for handle, section in handles:
        before = len(all_new)
        items = collect_from_handle(handle, section, extract_js)
        if not items:
            consecutive_login_walls += 1
            if consecutive_login_walls >= 3:
                print("\n⚠ Three handles in a row returned no tweets / hit a login wall.")
                print("   Log into x.com in Safari (the same window), then re-run.")
                break
        else:
            consecutive_login_walls = 0
        all_new.extend(items)
        time.sleep(HANDLE_PAUSE)

    merge = merge_into_posts(all_new)
    print(f"\nmerged: +{merge['added']} new, {merge['updated']} updated, {merge['total']} total in store")

    if not args.no_enrich and ENRICH_SCRIPT.exists() and merge["added"] + merge["updated"] > 0:
        print("→ smart enrich…")
        r = subprocess.run([sys.executable, str(ENRICH_SCRIPT)], capture_output=True, text=True)
        if r.stdout:
            print("  " + r.stdout.strip().splitlines()[-1])

    if args.pipeline and RADAR_SCRIPT.exists():
        print("→ radar pipeline…")
        agent_args = [sys.executable, str(RADAR_SCRIPT), "--skip-collect"]
        if not os.environ.get("OPENAI_API_KEY"):
            agent_args.append("--no-openai")
        r = subprocess.run(agent_args, capture_output=True, text=True)
        for line in (r.stdout or "").splitlines()[-3:]:
            if line.strip(): print("  " + line.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
