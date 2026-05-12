#!/usr/bin/env python3
"""Drive Safari to browse X like a human — anti-detection edition.

This is the "manual browsing as an expert, automated" path. It uses your
real, logged-in Safari window and behaves the way a careful person would,
not a script:

  • Rotation: each session visits 12–22 randomly-picked handles out of
    your watchlist, skipping anyone seen in the last 18 hours. The full
    list of 217 handles is covered organically across ~5-10 sessions.
  • Random everything: page-load wait (4-8.5s), scroll distance
    (55-92% viewport), scroll passes (1-3), inter-handle pause (1-4s),
    occasional reading pause (8-25s, ~15% of handles).
  • Warmup: opens x.com/home, scrolls a bit, waits. Looks like a normal
    person opening X before they navigate to a specific profile.
  • Work hours: only runs between 8am and 11pm local time. Off otherwise.
  • Cooldown: 3 consecutive login walls → 6 hours forced rest.
  • State file: data/manual_x/safari_state.json tracks handle history,
    last session, last block. Survives across runs.

Schedule recipe (don't run hourly — that itself is a flag):
  Have launchd or a manual cron fire this 2-4 times a day at jittered
  hours (e.g. 9:23, 13:47, 17:12, 20:38). With 20 handles per session,
  ~4 sessions/day, full watchlist refreshes in 3 days. That's slower
  than the original design — that's the point.

One-time macOS setup:
  Safari → Settings → Advanced → check "Show Develop menu"
  Develop menu → "Allow JavaScript from Apple Events"
  First run will prompt: System Settings → Privacy & Security →
  Automation → Terminal → toggle Safari ON.

Run:
  python3 tools/x_safari_browse.py                  # one session, rotates
  python3 tools/x_safari_browse.py --only sama,karpathy   # specific (bypasses rotation + work hours)
  python3 tools/x_safari_browse.py --pipeline       # + run agents after
  python3 tools/x_safari_browse.py --force          # skip work-hours gate
  python3 tools/x_safari_browse.py --max 8          # smaller session

When the cron path on Vercel/GitHub Actions runs, it uses x_auto_collect.py
(Nitter + Bluesky + Mastodon) — no Safari needed there. This tool is for
local sessions you run from your Mac when you want fresher first-party data.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_JS = ROOT / "tools" / "x_extract.js"
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
WATCHLIST_PATH = ROOT / "data" / "manual_x" / "watchlist.txt"
STATE_PATH = ROOT / "data" / "manual_x" / "safari_state.json"
TARGETS_PATH = ROOT / "data" / "manual_x" / "handle_targets.json"
REVIEW_PATH = ROOT / "data" / "manual_x" / "handle_review.json"
ENRICH_SCRIPT = ROOT / "tools" / "x_smart_enrich.py"
RADAR_SCRIPT = ROOT / "tools" / "run_radar_agents.py"

# ===== Anti-detection strategy =====
# Goal: behave like a careful human, not a script. Every action has variance,
# every session has a rotation, and the tool never sprints through the whole
# watchlist in one go.
STRATEGY = {
    # Session size — how many handles per run
    "session_handles_min":      12,
    "session_handles_max":      22,

    # Page load wait (after navigation)
    "page_load_min":            4.0,
    "page_load_max":            8.5,

    # Per-handle scroll passes (after initial extract)
    "scroll_passes_min":        1,
    "scroll_passes_max":        3,

    # Scroll pause between passes
    "scroll_pause_min":         1.8,
    "scroll_pause_max":         4.0,

    # Scroll distance as fraction of viewport
    "scroll_pct_min":           0.55,
    "scroll_pct_max":           0.92,

    # Inter-handle pause
    "handle_pause_min":         0.9,
    "handle_pause_max":         3.5,

    # Occasional "reading" pause to break the cadence
    "reading_pause_chance":     0.15,
    "reading_pause_min":        8,
    "reading_pause_max":        25,

    # Rotation — don't revisit anyone seen in last N hours
    "rotation_hours":           18,

    # Block-response — after K consecutive login walls, stop and cool down
    "blocks_to_stop":           3,
    "cooldown_hours_after_block": 6,

    # Work hours (local time)
    "work_hours_start":         8,
    "work_hours_end":           23,

    # Warmup — open home timeline first, scroll a bit
    "warmup_enabled":           True,
    "warmup_scrolls":           (1, 3),       # range
    "warmup_post_wait":         (3.0, 7.0),   # final settle before profiles
}

# Continuous mode strategy — for the "one handle every 4-7 minutes" loop.
# Combines deep collection per profile with daily quotas + periodic breaks.
CONTINUOUS = {
    # Interval between profile visits (random per-iteration).
    # Tighter pacing (~3 min, mild jitter) — still random enough to look human
    # but cycles the 703-handle watchlist faster.
    "interval_min_seconds":     2 * 60 + 30,   # 2:30
    "interval_max_seconds":     3 * 60 + 30,   # 3:30

    # Per-profile depth target — try to gather up to this many tweets
    "target_tweets":            100,
    "max_scrolls":              18,
    "stop_after_dry_scrolls":   2,    # bottom-detector: 2 scrolls add nothing → done

    # Warmup re-runs every N profiles (randomized range)
    "warmup_every":             (8, 12),

    # Occasional longer breaks to disrupt the cadence
    "extra_break_chance":       0.06,        # 6% chance per profile
    "extra_break_min":          15 * 60,
    "extra_break_max":          30 * 60,

    # Daily safety caps. Beyond these the loop sleeps until next day.
    # Sized for the ~3 min pacing × 15 work-hours (~300 theoretical visits/day),
    # with margin for cooldowns + breaks.
    "daily_handle_quota":       260,
    "daily_tweet_quota":        22000,

    # Enrich after every N successful visits
    "enrich_every_n":           5,
}

MAX_OSASCRIPT_TIMEOUT = 30


# ---------- Time + randomness ----------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def random_delay(lo: float, hi: float) -> None:
    time.sleep(random.uniform(lo, hi))


def in_work_hours() -> bool:
    h = datetime.now().hour
    return STRATEGY["work_hours_start"] <= h < STRATEGY["work_hours_end"]


# ---------- State persistence ----------

def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"version": 1, "handle_history": {}, "last_session": None, "last_block_at": None}
    try:
        return json.loads(STATE_PATH.read_text("utf-8"))
    except Exception:
        return {"version": 1, "handle_history": {}, "last_session": None, "last_block_at": None}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def is_blocked_by_review(handle: str) -> tuple[bool, str]:
    """True if x_manage.py has sidelined or marked-removed this handle and it's
    still inside its sideline window. Returns (blocked, reason)."""
    if not REVIEW_PATH.exists():
        return (False, "")
    try:
        doc = json.loads(REVIEW_PATH.read_text("utf-8"))
    except Exception:
        return (False, "")
    e = (doc.get("handles") or {}).get(handle.lower())
    if not e:
        return (False, "")
    status = e.get("status", "active")
    if status == "removed":
        return (True, "removed")
    if status != "sidelined":
        return (False, "")
    nr = e.get("next_review_at")
    if not nr:
        return (True, "sidelined")
    try:
        nr_dt = datetime.fromisoformat(nr.replace("Z", "+00:00"))
    except Exception:
        return (True, "sidelined")
    if _now() < nr_dt:
        return (True, "sidelined")
    return (False, "")   # cooldown elapsed → eligible for re-test


def target_for_handle(handle: str) -> int:
    """Per-handle tweet-collection target. Falls back to global default,
    then the in-code CONTINUOUS default. Edited via:
        python3 tools/x_manage.py set-target @handle N
        python3 tools/x_manage.py auto-target            # bulk auto-tier
    """
    if not TARGETS_PATH.exists():
        return CONTINUOUS["target_tweets"]
    try:
        cfg = json.loads(TARGETS_PATH.read_text("utf-8"))
    except Exception:
        return CONTINUOUS["target_tweets"]
    handles = cfg.get("handles") or {}
    v = handles.get(handle.lower())
    if v is None:
        v = cfg.get("default", CONTINUOUS["target_tweets"])
    try:
        v = int(v)
    except (ValueError, TypeError):
        return CONTINUOUS["target_tweets"]
    return max(5, min(2000, v))


def scrolls_for_target(target: int) -> int:
    """Scale max_scrolls with target — high-value visits need many more scrolls
    to actually surface 500+ tweets. ~6 tweets per scroll observed; floor at the
    configured CONTINUOUS minimum so small visits don't get shorter."""
    return max(CONTINUOUS["max_scrolls"], min(target // 6, 120))


def in_cooldown(state: dict) -> tuple[bool, float]:
    """Returns (in_cd, hours_remaining)."""
    blk = state.get("last_block_at")
    if not blk:
        return (False, 0.0)
    try:
        blk_dt = datetime.fromisoformat(blk.replace("Z", "+00:00"))
    except Exception:
        return (False, 0.0)
    cd = timedelta(hours=STRATEGY["cooldown_hours_after_block"])
    elapsed = _now() - blk_dt
    if elapsed < cd:
        return (True, (cd - elapsed).total_seconds() / 3600)
    return (False, 0.0)


# ---------- AppleScript driver ----------

def _osascript(script: str, timeout: int = MAX_OSASCRIPT_TIMEOUT) -> str:
    r = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "").strip() or "osascript failed")
    return r.stdout.strip()


def safari_open_url(url: str) -> None:
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
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "Safari" to return (do JavaScript "{escaped}" in front document)'
    return _osascript(script)


def safari_scroll_random() -> None:
    pct = random.uniform(STRATEGY["scroll_pct_min"], STRATEGY["scroll_pct_max"])
    safari_run_js(f"window.scrollBy(0, Math.floor(window.innerHeight * {pct}));")


# ---------- Watchlist parsing ----------

def parse_x_handles(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    out: list[tuple[str, str]] = []
    section = "watchlist"
    seen: set[str] = set()
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
        if ".bsky.social" in handle or ".bsky.team" in handle or ".bsky." in handle:
            continue
        if "@" in handle:
            continue
        if handle.lower() in seen:
            continue
        seen.add(handle.lower())
        out.append((handle, section))
    return out


# ---------- Rotation ----------

def rotate_handles(all_handles: list[tuple[str, str]], state: dict) -> list[tuple[str, str]]:
    """Pick a randomized subset that hasn't been visited recently."""
    history = state.get("handle_history") or {}
    cutoff = _now() - timedelta(hours=STRATEGY["rotation_hours"])
    candidates: list[tuple[str, str]] = []
    for h, s in all_handles:
        last_iso = history.get(h.lower())
        if last_iso:
            try:
                last_dt = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
                if last_dt > cutoff:
                    continue   # too recent
            except Exception:
                pass
        candidates.append((h, s))

    random.shuffle(candidates)
    size = random.randint(STRATEGY["session_handles_min"], STRATEGY["session_handles_max"])
    chosen = candidates[:size]
    if not chosen:
        # Everything was visited recently — pick from least-recent instead
        sorted_by_last = sorted(
            all_handles,
            key=lambda hs: history.get(hs[0].lower()) or "0",
        )
        chosen = sorted_by_last[:size]
    return chosen


# ---------- Warmup ----------

def warmup() -> None:
    if not STRATEGY["warmup_enabled"]:
        return
    print("→ warmup (home timeline)…")
    try:
        safari_open_url("https://x.com/home")
        random_delay(*STRATEGY["warmup_post_wait"])
        scrolls = random.randint(*STRATEGY["warmup_scrolls"])
        for _ in range(scrolls):
            safari_scroll_random()
            random_delay(1.5, 3.5)
        random_delay(*STRATEGY["warmup_post_wait"])
    except Exception as e:
        print(f"  warmup failed (continuing): {e}")


# ---------- Per-handle ----------

def collect_from_handle(handle: str, section: str, extract_js: str) -> list[dict] | None:
    """Returns the list of extracted posts (possibly empty if profile had
    nothing new). Returns None if a login wall was hit — caller treats that
    as a block signal."""
    url = f"https://x.com/{handle}"
    print(f"  → @{handle} ({section}) …", end="", flush=True)
    try:
        safari_open_url(url)
    except Exception as e:
        print(f"  open failed: {e}")
        return []

    random_delay(STRATEGY["page_load_min"], STRATEGY["page_load_max"])

    by_id: dict[str, dict] = {}
    login_wall = False

    def _extract_once() -> bool:
        """Returns True if extraction was healthy, False if login wall."""
        try:
            raw = safari_run_js(extract_js)
        except (subprocess.TimeoutExpired, RuntimeError):
            return True   # treat as transient, continue
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return True
        if payload.get("is_login_wall"):
            return False
        for p in payload.get("posts") or []:
            tid = p.get("tweet_id")
            if tid and tid not in by_id:
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
                    "pain_signal_score":  0,
                    "opportunity_tags":   [],
                    "verification_status": "safari_browse",
                    "lang":               "",
                }
        return True

    # Initial extract
    if not _extract_once():
        login_wall = True

    # Variable scroll passes
    if not login_wall:
        scrolls = random.randint(STRATEGY["scroll_passes_min"], STRATEGY["scroll_passes_max"])
        for _ in range(scrolls):
            try:
                safari_scroll_random()
            except Exception:
                break
            random_delay(STRATEGY["scroll_pause_min"], STRATEGY["scroll_pause_max"])
            if not _extract_once():
                login_wall = True
                break

    if login_wall:
        print("  login wall")
        return None
    print(f"  {len(by_id)} tweets")
    return list(by_id.values())


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
    # Cap sized for the tiered targets: ~100 active handles × 200 avg = 20k.
    # Newest-first sort means trims drop the stalest tweets first.
    existing = existing[:20000]

    doc["items"] = existing
    doc["collected_at"] = _now_iso()
    POSTS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(existing)}


# ---------- Deep collection (for continuous mode) ----------

def collect_deep_from_handle(handle: str, section: str, extract_js: str, target: int, max_scrolls: int) -> list[dict] | None:
    """Visit a profile and scroll until we have `target` tweets OR hit the
    floor (two scrolls in a row produce nothing new) OR run out of scrolls.
    Returns None if a login wall is hit at any point."""
    url = f"https://x.com/{handle}"
    print(f"  → @{handle} ({section})  target={target} …", end="", flush=True)
    try:
        safari_open_url(url)
    except Exception as e:
        print(f"  open failed: {e}")
        return []

    random_delay(STRATEGY["page_load_min"], STRATEGY["page_load_max"])

    by_id: dict[str, dict] = {}

    def _extract_once() -> tuple[bool, int]:
        """Returns (login_wall, new_count_this_pass)."""
        try:
            raw = safari_run_js(extract_js)
        except (subprocess.TimeoutExpired, RuntimeError):
            return (False, 0)
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return (False, 0)
        if payload.get("is_login_wall"):
            return (True, 0)
        added = 0
        for p in payload.get("posts") or []:
            tid = p.get("tweet_id")
            if tid and tid not in by_id:
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
                    "pain_signal_score":   0,
                    "opportunity_tags":    [],
                    "verification_status": "safari_browse",
                    "lang":                "",
                }
                added += 1
        return (False, added)

    # Initial extract
    login_wall, _ = _extract_once()
    if login_wall:
        print("  login wall")
        return None

    dry_in_a_row = 0
    scrolls_done = 0
    while len(by_id) < target and scrolls_done < max_scrolls and dry_in_a_row < CONTINUOUS["stop_after_dry_scrolls"]:
        try:
            safari_scroll_random()
        except Exception:
            break
        random_delay(STRATEGY["scroll_pause_min"], STRATEGY["scroll_pause_max"])
        login_wall, added = _extract_once()
        if login_wall:
            print(f"  login wall after {scrolls_done} scrolls ({len(by_id)} collected)")
            return None
        if added == 0:
            dry_in_a_row += 1
        else:
            dry_in_a_row = 0
        scrolls_done += 1

    reason = "target" if len(by_id) >= target else ("floor" if dry_in_a_row >= CONTINUOUS["stop_after_dry_scrolls"] else "max-scrolls")
    print(f"  {len(by_id)} tweets [{scrolls_done} scrolls, stop:{reason}]")
    return list(by_id.values())


# ---------- Daily counters ----------

def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def reset_daily_if_needed(state: dict) -> dict:
    dc = state.setdefault("daily_counters", {})
    if dc.get("date") != _today_str():
        dc["date"] = _today_str()
        dc["handles_visited"] = 0
        dc["tweets_collected"] = 0
    return dc


def seconds_until_tomorrow() -> int:
    now = datetime.now()
    tomorrow_8am = (now + timedelta(days=1)).replace(
        hour=STRATEGY["work_hours_start"], minute=5, second=0, microsecond=0
    )
    return max(60, int((tomorrow_8am - now).total_seconds()))


# ---------- Continuous loop ----------

def continuous_loop(extract_js: str, run_pipeline: bool) -> int:
    state = load_state()
    visits_since_warmup = 0
    enrich_counter = 0

    targets_cfg = {}
    if TARGETS_PATH.exists():
        try:
            targets_cfg = json.loads(TARGETS_PATH.read_text("utf-8"))
        except Exception:
            targets_cfg = {}
    default_target = targets_cfg.get("default", CONTINUOUS["target_tweets"])
    overrides = targets_cfg.get("handles") or {}

    print(f"=== Continuous Safari session — started {_now_iso()} ===")
    print(f"  policy: 1 profile every "
          f"{CONTINUOUS['interval_min_seconds']//60}–{CONTINUOUS['interval_max_seconds']//60} min, "
          f"default target {default_target} tweets/profile"
          + (f" ({len(overrides)} per-handle overrides)" if overrides else ""))
    print(f"  daily safety caps: {CONTINUOUS['daily_handle_quota']} profiles + "
          f"{CONTINUOUS['daily_tweet_quota']} tweets")
    print("  Ctrl+C to stop. State persists between runs.")

    while True:
        all_handles = parse_x_handles(WATCHLIST_PATH)   # re-read every loop so edits stick
        if not all_handles:
            print("watchlist empty — sleeping 30 min")
            time.sleep(30 * 60)
            continue

        dc = reset_daily_if_needed(state)

        # Daily quota gates
        if dc["handles_visited"] >= CONTINUOUS["daily_handle_quota"]:
            wait = seconds_until_tomorrow()
            print(f"daily handle quota ({CONTINUOUS['daily_handle_quota']}) reached. sleeping {wait//3600}h until tomorrow.")
            save_state(state)
            time.sleep(wait)
            continue
        if dc["tweets_collected"] >= CONTINUOUS["daily_tweet_quota"]:
            wait = seconds_until_tomorrow()
            print(f"daily tweet quota ({CONTINUOUS['daily_tweet_quota']}) reached. sleeping {wait//3600}h.")
            save_state(state)
            time.sleep(wait)
            continue

        # Work-hours gate (re-checked every iteration so we naturally pause overnight)
        if not in_work_hours():
            print(f"outside work hours ({datetime.now().strftime('%H:%M')}). sleeping 30 min.")
            time.sleep(30 * 60)
            continue

        # Cooldown gate
        cd, hrs = in_cooldown(state)
        if cd:
            print(f"in cooldown ({hrs:.1f}h remaining). sleeping 30 min.")
            time.sleep(30 * 60)
            continue

        # Periodic warmup
        warmup_thresh = random.randint(*CONTINUOUS["warmup_every"])
        if visits_since_warmup >= warmup_thresh or visits_since_warmup == 0:
            warmup()
            visits_since_warmup = 0

        # Pick ONE handle to visit (rotation-aware + sideline-aware)
        candidates = []
        history = state.get("handle_history") or {}
        cutoff = _now() - timedelta(hours=STRATEGY["rotation_hours"])
        for h, s in all_handles:
            # Skip handles sidelined or removed by x_manage review
            blocked, _why = is_blocked_by_review(h)
            if blocked:
                continue
            last_iso = history.get(h.lower())
            if last_iso:
                try:
                    last_dt = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
                    if last_dt > cutoff:
                        continue
                except Exception:
                    pass
            candidates.append((h, s))
        if not candidates:
            # Rotation exhausted — fall back to least-recently-visited
            # (still respecting sideline)
            fallback = [
                (h, s) for h, s in all_handles if not is_blocked_by_review(h)[0]
            ]
            candidates = sorted(fallback, key=lambda hs: history.get(hs[0].lower()) or "0")
        handle, section = random.choice(candidates[: min(40, len(candidates))])

        # Visit deep — per-handle target from handle_targets.json, fall back to global default.
        # Scale max_scrolls with target so a 500-target visit actually keeps scrolling.
        target = target_for_handle(handle)
        max_scrolls = scrolls_for_target(target)
        items = collect_deep_from_handle(
            handle, section, extract_js,
            target=target,
            max_scrolls=max_scrolls,
        )

        if items is None:   # login wall
            blocks = state.get("consecutive_blocks", 0) + 1
            state["consecutive_blocks"] = blocks
            if blocks >= STRATEGY["blocks_to_stop"]:
                state["last_block_at"] = _now_iso()
                state["consecutive_blocks"] = 0
                save_state(state)
                print(f"⚠ {blocks} consecutive blocks → cooldown {STRATEGY['cooldown_hours_after_block']}h.")
                continue
        else:
            state["consecutive_blocks"] = 0
            state.setdefault("handle_history", {})[handle.lower()] = _now_iso()
            dc["handles_visited"] += 1
            dc["tweets_collected"] += len(items)
            visits_since_warmup += 1
            merge = merge_into_posts(items)
            print(f"     merged: +{merge['added']} new ({merge['total']} total in store)  "
                  f"daily: {dc['handles_visited']} profiles / {dc['tweets_collected']} tweets")
            enrich_counter += 1

        state["last_session"] = _now_iso()
        save_state(state)

        # Periodic enrich
        if enrich_counter >= CONTINUOUS["enrich_every_n"] and ENRICH_SCRIPT.exists():
            print("→ smart enrich…")
            r = subprocess.run([sys.executable, str(ENRICH_SCRIPT)], capture_output=True, text=True)
            if r.stdout:
                print("  " + r.stdout.strip().splitlines()[-1])
            enrich_counter = 0
            if run_pipeline and RADAR_SCRIPT.exists():
                print("→ pipeline…")
                agent_args = [sys.executable, str(RADAR_SCRIPT), "--skip-collect"]
                if not os.environ.get("OPENAI_API_KEY"):
                    agent_args.append("--no-openai")
                rp = subprocess.run(agent_args, capture_output=True, text=True)
                for line in (rp.stdout or "").splitlines()[-2:]:
                    if line.strip(): print("  " + line.strip())

        # Occasional longer break
        if random.random() < CONTINUOUS["extra_break_chance"]:
            br = random.uniform(CONTINUOUS["extra_break_min"], CONTINUOUS["extra_break_max"])
            print(f"  ☕ extra break {br/60:.0f} min")
            time.sleep(br)

        # Interval before next profile
        wait = random.uniform(CONTINUOUS["interval_min_seconds"], CONTINUOUS["interval_max_seconds"])
        print(f"  next in {wait/60:.1f} min…")
        time.sleep(wait)


# ---------- Permission probes ----------

def check_safari_access() -> bool:
    try:
        out = _osascript('tell application "Safari" to return name', timeout=8)
        return "Safari" in out
    except subprocess.TimeoutExpired:
        return False
    except RuntimeError as e:
        msg = str(e).lower()
        if "not authorized" in msg or "1743" in msg:
            print("\n⚠ Terminal not authorized to control Safari.")
            print("   System Settings → Privacy & Security → Automation → Terminal → toggle Safari.")
        return False


def check_js_from_events() -> str | None:
    try:
        out = safari_run_js("'js_ok'")
        return None if "js_ok" in out else f"unexpected JS output: {out[:60]}"
    except RuntimeError as e:
        msg = str(e)
        if "JavaScript through" in msg or "Apple Events" in msg or "Allow" in msg:
            return ("Develop → Allow JavaScript from Apple Events is OFF.\n"
                    "   Safari → Settings → Advanced → Show Develop menu.\n"
                    "   Then: Develop → Allow JavaScript from Apple Events.")
        return msg


# ---------- Main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Drive Safari to browse X like a human — anti-detection edition.")
    parser.add_argument("--only", help="Comma-separated handle subset (bypasses rotation + work-hours gate)")
    parser.add_argument("--max", type=int, default=0, help="Override session size (default randomized 12-22)")
    parser.add_argument("--pipeline", action="store_true", help="Run radar agent pipeline after collection")
    parser.add_argument("--no-enrich", action="store_true", help="Skip x_smart_enrich after collection")
    parser.add_argument("--force", action="store_true", help="Bypass work-hours + cooldown gates (use sparingly)")
    parser.add_argument("--skip-checks", action="store_true", help="Skip Safari/Apple Events probes")
    parser.add_argument("--status", action="store_true", help="Print session/cooldown/coverage status and exit")
    parser.add_argument("--continuous", action="store_true",
                        help="Run forever: one profile every 4-7 min, target 100 tweets each, "
                             "honors all gates + daily quota. Ctrl+C to stop.")
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("This tool needs macOS Safari. CI/cloud uses x_auto_collect.py instead.")
        return 1

    state = load_state()
    all_handles = parse_x_handles(WATCHLIST_PATH)

    # Permission probes before any branch that touches Safari
    if args.continuous and not args.skip_checks:
        if not check_safari_access():
            print("Cannot reach Safari via AppleScript. Open Safari then re-run.")
            return 1
        err = check_js_from_events()
        if err:
            print(f"⚠ {err}")
            return 1

    if args.continuous:
        extract_js = EXTRACT_JS.read_text("utf-8")
        try:
            return continuous_loop(extract_js, run_pipeline=args.pipeline)
        except KeyboardInterrupt:
            print("\nstopped by user.")
            return 0

    if args.status:
        cd, hrs = in_cooldown(state)
        history = state.get("handle_history") or {}
        cutoff = _now() - timedelta(hours=STRATEGY["rotation_hours"])
        fresh = sum(
            1 for h, _ in all_handles
            if (lambda last: last and datetime.fromisoformat(last.replace("Z", "+00:00")) > cutoff)
               (history.get(h.lower()))
        )
        print("=== Safari browse status ===")
        print(f"  watchlist size:     {len(all_handles)}")
        print(f"  visited last 18h:   {fresh}  ({100*fresh//max(1,len(all_handles))}%)")
        print(f"  available to visit: {len(all_handles) - fresh}")
        print(f"  last session:       {state.get('last_session') or '—'}")
        print(f"  in cooldown:        {'YES' if cd else 'no'}{f' ({hrs:.1f}h remaining)' if cd else ''}")
        print(f"  work hours now:     {'yes' if in_work_hours() else 'no'} (local {datetime.now().strftime('%H:%M')})")
        return 0

    # Gate: work hours
    if not args.force and not args.only and not in_work_hours():
        h_now = datetime.now().strftime("%H:%M")
        print(f"Outside work hours ({h_now} local). Window is "
              f"{STRATEGY['work_hours_start']:02d}:00–{STRATEGY['work_hours_end']:02d}:00. "
              "Use --force to override.")
        return 0

    # Gate: cooldown
    if not args.force:
        cd, hrs = in_cooldown(state)
        if cd:
            print(f"In cooldown after recent block. {hrs:.1f}h remaining. Use --force to override.")
            return 0

    # Permission preflight
    if not args.skip_checks:
        if not check_safari_access():
            print("Cannot reach Safari via AppleScript. Open Safari then re-run.")
            return 1
        err = check_js_from_events()
        if err:
            print(f"⚠ {err}")
            return 1

    # Pick handles
    if args.only:
        wanted = {h.strip().lstrip("@").lower() for h in args.only.split(",")}
        chosen = [(h, s) for (h, s) in all_handles if h.lower() in wanted]
    else:
        chosen = rotate_handles(all_handles, state)
    if args.max and args.max > 0:
        chosen = chosen[:args.max]

    if not chosen:
        print("No handles to visit (rotation found nothing fresh? check watchlist or --only).")
        return 1

    extract_js = EXTRACT_JS.read_text("utf-8")
    print(f"=== Safari session — {_now_iso()} ===")
    print(f"will visit {len(chosen)} of {len(all_handles)} watchlist handles (rotated)")

    # Warmup pass
    if not args.only:
        warmup()

    all_new: list[dict] = []
    blocks_in_a_row = 0
    visits_completed = 0

    for handle, section in chosen:
        # Occasional reading pause to break the cadence
        if random.random() < STRATEGY["reading_pause_chance"]:
            rp = random.uniform(STRATEGY["reading_pause_min"], STRATEGY["reading_pause_max"])
            print(f"  (reading pause {rp:.0f}s)")
            time.sleep(rp)

        items = collect_from_handle(handle, section, extract_js)
        if items is None:
            blocks_in_a_row += 1
            if blocks_in_a_row >= STRATEGY["blocks_to_stop"]:
                state["last_block_at"] = _now_iso()
                save_state(state)
                print(f"⚠ {blocks_in_a_row} consecutive blocks → entering "
                      f"{STRATEGY['cooldown_hours_after_block']}h cooldown.")
                break
        else:
            blocks_in_a_row = 0
            state.setdefault("handle_history", {})[handle.lower()] = _now_iso()
            all_new.extend(items)
            visits_completed += 1

        random_delay(STRATEGY["handle_pause_min"], STRATEGY["handle_pause_max"])

    state["last_session"] = _now_iso()
    save_state(state)

    merge = merge_into_posts(all_new)
    print(f"\nmerged: +{merge['added']} new, {merge['updated']} updated, {merge['total']} total")
    print(f"session: {visits_completed} successful visits of {len(chosen)} planned")

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
            if line.strip():
                print("  " + line.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
