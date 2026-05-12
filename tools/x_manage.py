#!/usr/bin/env python3
"""Manage the X collection — see what's tracked, prune, tune per-handle targets.

The Safari browser feeds posts.json. Over time you accumulate accounts and
tweets. This CLI gives you control:

  python3 tools/x_manage.py list-accounts                  # full overview
  python3 tools/x_manage.py list-accounts --status visited
  python3 tools/x_manage.py show @sama                     # detail for one handle

  python3 tools/x_manage.py list-tweets                    # top by radar_score
  python3 tools/x_manage.py list-tweets --from @sama
  python3 tools/x_manage.py list-tweets --search "claude code"
  python3 tools/x_manage.py list-tweets --section saudi_official --top 30

  python3 tools/x_manage.py delete-account @sama           # remove watchlist + tweets
  python3 tools/x_manage.py delete-account @sama --keep-tweets
  python3 tools/x_manage.py delete-tweet 1234567890        # one tweet

  python3 tools/x_manage.py set-target @sama 200           # this account → 200 tweets/visit
  python3 tools/x_manage.py set-target default 75          # global default
  python3 tools/x_manage.py reset-target @sama             # back to default
  python3 tools/x_manage.py targets                        # show all overrides

  python3 tools/x_manage.py export --csv > my-tweets.csv

All destructive operations prompt for confirmation. Use --yes to skip.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
WATCHLIST_PATH = ROOT / "data" / "manual_x" / "watchlist.txt"
TARGETS_PATH = ROOT / "data" / "manual_x" / "handle_targets.json"
STATE_PATH = ROOT / "data" / "manual_x" / "safari_state.json"
REVIEW_PATH = ROOT / "data" / "manual_x" / "handle_review.json"
REMOVED_LOG = ROOT / "data" / "manual_x" / "removed_handles.log"

REVIEW_DEFAULTS = {
    "min_avg_score":            0.18,   # avg radar_score floor
    "min_tweets_for_judgment":  5,      # need this many tweets to judge low_score
    "stale_age_days":           60,     # if newest tweet older than this → stale
    "sideline_days":            7,      # how long to skip after sidelining
    "max_failed_reviews":       2,      # nth failed review → remove permanently
}


# ---------- Helpers ----------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError:
        return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ago(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return "—"
    diff = datetime.now(timezone.utc) - t
    if diff.days >= 2: return f"{diff.days}d ago"
    if diff.days == 1: return "1d ago"
    h = int(diff.total_seconds() / 3600)
    if h >= 1: return f"{h}h ago"
    m = int(diff.total_seconds() / 60)
    if m >= 1: return f"{m}m ago"
    return "now"


def _truncate(s: str, n: int) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _confirm(msg: str, auto_yes: bool) -> bool:
    if auto_yes:
        return True
    try:
        ans = input(f"{msg} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


# ---------- Watchlist parsing ----------

def parse_watchlist() -> list[tuple[str, str]]:
    """Returns [(handle, section)] preserving order — X handles only."""
    if not WATCHLIST_PATH.exists():
        return []
    out: list[tuple[str, str]] = []
    section = "watchlist"
    seen: set[str] = set()
    for raw in WATCHLIST_PATH.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line: continue
        if line.startswith("##"):
            section = line.lstrip("#").strip() or "watchlist"
            continue
        if line.startswith("#"): continue
        h = line.split()[0].lstrip("@")
        if not h: continue
        if ".bsky.social" in h or ".bsky.team" in h or ".bsky." in h: continue
        if "@" in h: continue
        if h.lower() in seen: continue
        seen.add(h.lower())
        out.append((h, section))
    return out


def remove_from_watchlist(handle: str) -> bool:
    """Returns True if the handle was found and removed."""
    if not WATCHLIST_PATH.exists():
        return False
    h_low = handle.lstrip("@").lower()
    lines = WATCHLIST_PATH.read_text("utf-8").splitlines()
    new_lines = []
    removed = False
    for line in lines:
        s = line.strip()
        if s.startswith("@") and s.lstrip("@").split()[0].lower() == h_low:
            removed = True
            continue
        new_lines.append(line)
    if removed:
        WATCHLIST_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return removed


# ---------- Tweet store helpers ----------

def load_posts() -> tuple[dict, list[dict]]:
    doc = _load_json(POSTS_PATH, {"items": []})
    return doc, doc.get("items") or []


def save_posts(doc: dict, items: list[dict]) -> None:
    doc["items"] = items
    doc["updated_at"] = _now_iso()
    _save_json(POSTS_PATH, doc)


def posts_by_handle(items: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for it in items:
        h = (it.get("author_handle") or "").lstrip("@").lower()
        if not h: continue
        out.setdefault(h, []).append(it)
    return out


# ---------- list-accounts ----------

def cmd_list_accounts(args) -> int:
    watchlist = parse_watchlist()
    _, posts = load_posts()
    by_h = posts_by_handle(posts)
    state = _load_json(STATE_PATH, {})
    history = state.get("handle_history") or {}
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    default_target = targets.get("default", 100)
    overrides = targets.get("handles") or {}

    rows = []
    for handle, section in watchlist:
        hlow = handle.lower()
        ts = by_h.get(hlow, [])
        last_visit = history.get(hlow)
        avg = (sum(t.get("radar_score", 0) for t in ts) / len(ts)) if ts else 0
        target = overrides.get(hlow, default_target)
        status = "active" if last_visit else ("never" if not ts else "data-only")
        rows.append({
            "section": section, "handle": handle, "tweets": len(ts),
            "avg": avg, "last": last_visit, "target": target, "status": status,
        })

    # Filter
    if args.status:
        statuses = set(args.status.split(","))
        rows = [r for r in rows if r["status"] in statuses]
    if args.section:
        rows = [r for r in rows if r["section"] == args.section]

    # Sort
    rows.sort(key=lambda r: (r["section"], -r["tweets"]))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"{'#':>4}  {'section':<20}  {'handle':<22}  {'tweets':>6}  {'avg':>5}  {'target':>6}  {'last':<12}  {'status':<10}")
    print("─" * 100)
    for i, r in enumerate(rows, 1):
        print(f"{i:>4}  {r['section'][:20]:<20}  @{r['handle'][:21]:<21}  "
              f"{r['tweets']:>6}  {r['avg']:>5.2f}  {r['target']:>6}  "
              f"{_ago(r['last']):<12}  {r['status']:<10}")
    print()
    print(f"summary: {len(rows)} accounts, "
          f"{sum(r['tweets'] for r in rows)} tweets total, "
          f"{sum(1 for r in rows if r['status'] == 'active')} actively visited")
    return 0


# ---------- show one account ----------

def cmd_show(args) -> int:
    h = args.handle.lstrip("@")
    _, posts = load_posts()
    state = _load_json(STATE_PATH, {})
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    watchlist = {hh.lower(): sec for hh, sec in parse_watchlist()}

    hlow = h.lower()
    if hlow not in watchlist and not any((p.get("author_handle") or "").lower() == hlow for p in posts):
        print(f"@{h} not in watchlist and has no tweets in store.")
        return 1

    section = watchlist.get(hlow, "(not in watchlist)")
    last_visit = (state.get("handle_history") or {}).get(hlow)
    by_h = posts_by_handle(posts).get(hlow, [])
    target = targets.get("handles", {}).get(hlow, targets.get("default", 100))

    print(f"=== @{h} ===")
    print(f"section:       {section}")
    print(f"in watchlist:  {'yes' if hlow in watchlist else 'no'}")
    print(f"last visited:  {_ago(last_visit)}  ({last_visit or '—'})")
    print(f"target/visit:  {target}")
    print(f"tweets stored: {len(by_h)}")
    if by_h:
        scores = [t.get("radar_score", 0) for t in by_h]
        print(f"avg score:     {sum(scores)/len(scores):.3f}")
        print(f"max score:     {max(scores):.3f}")
        print()
        by_h.sort(key=lambda t: t.get("radar_score", 0), reverse=True)
        print(f"top 10 tweets:")
        for i, t in enumerate(by_h[:10], 1):
            print(f"  {i:>2}. {t.get('radar_score', 0):.3f}  [{t.get('signal_type','?')}]  "
                  f"{_truncate(t.get('text'), 100)}")
    return 0


# ---------- list-tweets ----------

def cmd_list_tweets(args) -> int:
    _, posts = load_posts()
    items = posts[:]
    if args.from_handle:
        h = args.from_handle.lstrip("@").lower()
        items = [t for t in items if (t.get("author_handle") or "").lstrip("@").lower() == h]
    if args.section:
        items = [t for t in items if t.get("section") == args.section]
    if args.signal_type:
        items = [t for t in items if t.get("signal_type") == args.signal_type]
    if args.search:
        q = args.search.lower()
        items = [t for t in items if q in (t.get("text") or "").lower()]
    if args.min_score is not None:
        items = [t for t in items if t.get("radar_score", 0) >= args.min_score]

    sort_key = {
        "score": lambda t: -(t.get("radar_score") or 0),
        "recent": lambda t: t.get("collected_at") or "",
        "posted": lambda t: t.get("posted_at") or "",
    }.get(args.sort, lambda t: -(t.get("radar_score") or 0))
    items.sort(key=sort_key, reverse=(args.sort == "recent" or args.sort == "posted"))

    items = items[: args.top]

    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0

    print(f"{'#':>4}  {'score':>5}  {'type':<10}  {'author':<22}  {'collected':<10}  text")
    print("─" * 110)
    for i, t in enumerate(items, 1):
        print(f"{i:>4}  {t.get('radar_score', 0):>5.2f}  {(t.get('signal_type') or '?')[:10]:<10}  "
              f"@{(t.get('author_handle') or '?')[:21]:<21}  "
              f"{_ago(t.get('collected_at')):<10}  {_truncate(t.get('text'), 70)}")
    print(f"\n{len(items)} tweets shown")
    return 0


# ---------- delete-account ----------

def cmd_delete_account(args) -> int:
    h = args.handle.lstrip("@")
    hlow = h.lower()

    doc, posts = load_posts()
    by_h = posts_by_handle(posts).get(hlow, [])
    state = _load_json(STATE_PATH, {})
    in_watchlist = any(hh.lower() == hlow for hh, _ in parse_watchlist())

    print(f"delete @{h}:")
    print(f"  in watchlist:   {'yes' if in_watchlist else 'no'}")
    print(f"  tweets in store: {len(by_h)}")
    print(f"  in state history: {'yes' if hlow in (state.get('handle_history') or {}) else 'no'}")
    print(f"  per-handle target: {'yes' if hlow in (_load_json(TARGETS_PATH, {}).get('handles') or {}) else 'no'}")

    if not _confirm(
        f"remove from watchlist + {('delete ' + str(len(by_h)) + ' tweets') if not args.keep_tweets else 'KEEP tweets'}?",
        args.yes,
    ):
        print("aborted.")
        return 1

    actions = []

    # 1. Watchlist
    if remove_from_watchlist(h):
        actions.append("removed from watchlist.txt")
        REMOVED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with REMOVED_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{_now_iso()}  removed @{h}  tweets_deleted={not args.keep_tweets}\n")

    # 2. Tweets
    if not args.keep_tweets and by_h:
        remaining = [t for t in posts if (t.get("author_handle") or "").lstrip("@").lower() != hlow]
        deleted = len(posts) - len(remaining)
        save_posts(doc, remaining)
        actions.append(f"deleted {deleted} tweets")

    # 3. State history
    history = state.get("handle_history") or {}
    if hlow in history:
        del history[hlow]
        state["handle_history"] = history
        _save_json(STATE_PATH, state)
        actions.append("removed from state history")

    # 4. Per-handle target
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    if hlow in (targets.get("handles") or {}):
        del targets["handles"][hlow]
        _save_json(TARGETS_PATH, targets)
        actions.append("removed per-handle target")

    if not actions:
        print("nothing to remove — @" + h + " was not present anywhere.")
        return 1
    print("done: " + "; ".join(actions))
    return 0


# ---------- delete-tweet ----------

def cmd_delete_tweet(args) -> int:
    doc, posts = load_posts()
    tid = str(args.tweet_id)
    match = next((t for t in posts if t.get("tweet_id") == tid), None)
    if not match:
        print(f"tweet {tid} not found in store.")
        return 1
    print(f"tweet {tid}:")
    print(f"  author:  @{match.get('author_handle','?')}")
    print(f"  posted:  {match.get('posted_at') or '—'}")
    print(f"  score:   {match.get('radar_score', 0):.3f}")
    print(f"  text:    {_truncate(match.get('text'), 200)}")

    if not _confirm("delete this tweet?", args.yes):
        print("aborted.")
        return 1

    remaining = [t for t in posts if t.get("tweet_id") != tid]
    save_posts(doc, remaining)
    print(f"deleted. {len(remaining)} tweets remain.")
    return 0


# ---------- set-target / targets / reset-target ----------

def cmd_set_target(args) -> int:
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    targets.setdefault("handles", {})
    h = args.handle.lstrip("@")
    val = max(5, min(1000, int(args.value)))

    if h.lower() == "default":
        old = targets.get("default", 100)
        targets["default"] = val
        _save_json(TARGETS_PATH, targets)
        print(f"global default: {old} → {val}")
        return 0

    old = targets["handles"].get(h.lower())
    targets["handles"][h.lower()] = val
    _save_json(TARGETS_PATH, targets)
    print(f"@{h}: {old or 'default'} → {val}")
    return 0


def cmd_reset_target(args) -> int:
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    raw = args.handle.lstrip("@")
    h = raw.lower()
    if h in (targets.get("handles") or {}):
        del targets["handles"][h]
        _save_json(TARGETS_PATH, targets)
        print(f"@{raw}: target removed (back to default {targets.get('default', 100)})")
        return 0
    print(f"@{raw} had no override.")
    return 1


def cmd_targets(args) -> int:
    targets = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})
    default = targets.get("default", 100)
    overrides = targets.get("handles") or {}
    if args.json:
        print(json.dumps(targets, ensure_ascii=False, indent=2))
        return 0
    print(f"global default: {default} tweets per visit")
    print()
    if not overrides:
        print("no per-handle overrides set.")
        print("set one with:  python3 tools/x_manage.py set-target @handle N")
        return 0
    print(f"{'handle':<28}  {'target':>7}")
    print("─" * 40)
    for h, v in sorted(overrides.items()):
        print(f"@{h:<27}  {v:>7}")
    print(f"\n{len(overrides)} overrides set.")
    return 0


# ---------- review (sideline low-value handles, retire repeat offenders) ----------

def _load_review() -> dict:
    doc = _load_json(REVIEW_PATH, {})
    crit = dict(REVIEW_DEFAULTS)
    crit.update(doc.get("criteria") or {})
    doc["criteria"] = crit
    doc.setdefault("handles", {})
    return doc


def _save_review(doc: dict) -> None:
    _save_json(REVIEW_PATH, doc)


def _newest_age_days(items: list[dict]) -> float | None:
    """Days since the newest post in the list (None if no parseable dates)."""
    newest = None
    for it in items:
        for k in ("posted_at", "collected_at"):
            v = it.get(k)
            if not v: continue
            try:
                t = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                continue
            if newest is None or t > newest:
                newest = t
            break
    if newest is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - newest).total_seconds() / 86400)


def _judge_handle(handle: str, tweets: list[dict], visited_at_iso: str | None, crit: dict) -> tuple[str | None, dict]:
    """Returns (verdict, stats). verdict is None when handle is healthy.
    Verdicts: 'dead' | 'low_score' | 'stale'.
    """
    stats = {"tweets": len(tweets), "avg_score": 0.0, "newest_age_days": None}

    if not tweets:
        # Dead only if we've visited at least 6h ago and got nothing (a recent
        # visit could just be a transient extraction blip).
        if visited_at_iso:
            try:
                visited_dt = datetime.fromisoformat(visited_at_iso.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - visited_dt).total_seconds() / 3600
                if age_hours >= 6:
                    return ("dead", stats)
            except Exception:
                pass
        return (None, stats)

    scores = [t.get("radar_score", 0) for t in tweets]
    # Skip judgment if not yet enriched (all zero → enrich pending)
    if all(s == 0 for s in scores):
        return (None, stats)

    avg = sum(scores) / len(scores)
    stats["avg_score"] = round(avg, 4)

    age = _newest_age_days(tweets)
    stats["newest_age_days"] = round(age, 1) if age is not None else None

    # Stale: hasn't posted in a long time
    if age is not None and age > crit["stale_age_days"]:
        return ("stale", stats)

    # Low score: enough sample + below threshold
    if len(tweets) >= crit["min_tweets_for_judgment"] and avg < crit["min_avg_score"]:
        return ("low_score", stats)

    return (None, stats)


def cmd_review(args) -> int:
    doc = _load_review()
    crit = doc["criteria"]
    handles_rev = doc["handles"]

    _, posts = load_posts()
    by_h = posts_by_handle(posts)
    state = _load_json(STATE_PATH, {})
    history = state.get("handle_history") or {}
    watchlist = parse_watchlist()
    targets_doc = _load_json(TARGETS_PATH, {"default": 100, "handles": {}})

    now_iso = _now_iso()
    sideline_until = (datetime.now(timezone.utc) + timedelta(days=crit["sideline_days"])).isoformat(timespec="seconds")

    new_sidelined: list[tuple[str, str, dict]] = []
    promoted_to_removed: list[tuple[str, str]] = []
    acquitted: list[str] = []
    still_sidelined: list[str] = []

    for handle, _section in watchlist:
        hlow = handle.lower()
        tweets = by_h.get(hlow, [])
        visited_at = history.get(hlow)
        verdict, stats = _judge_handle(handle, tweets, visited_at, crit)

        entry = handles_rev.get(hlow) or {"status": "active", "review_count": 0}
        current_status = entry.get("status", "active")

        # Apply force flags
        if args.dry_run:
            pass  # never write, just report

        if verdict is None:
            # healthy
            if current_status in ("sidelined", "removed"):
                # acquitted — back to active
                entry["status"] = "active"
                entry["review_count"] = 0
                entry["last_verdict"] = None
                entry["last_reviewed"] = now_iso
                entry["next_review_at"] = None
                entry["stats_at_review"] = stats
                handles_rev[hlow] = entry
                acquitted.append(handle)
            else:
                # already active — no change unless we want a "last seen healthy" record
                if entry.get("review_count", 0) > 0:
                    entry["last_reviewed"] = now_iso
                    entry["stats_at_review"] = stats
                    handles_rev[hlow] = entry
            continue

        # verdict raised
        entry["review_count"] = (entry.get("review_count") or 0) + 1
        entry["last_verdict"] = verdict
        entry["last_reviewed"] = now_iso
        entry["stats_at_review"] = stats

        if entry["review_count"] >= crit["max_failed_reviews"]:
            entry["status"] = "removed"
            entry["next_review_at"] = None
            handles_rev[hlow] = entry
            promoted_to_removed.append((handle, verdict))
        else:
            entry["status"] = "sidelined"
            entry["next_review_at"] = sideline_until
            handles_rev[hlow] = entry
            if current_status == "sidelined":
                still_sidelined.append(handle)
            else:
                new_sidelined.append((handle, verdict, stats))

    if not args.dry_run:
        _save_review(doc)
        # Apply removals — remove from watchlist + (optionally) prune posts.
        if promoted_to_removed and not args.keep_removed:
            REMOVED_LOG.parent.mkdir(parents=True, exist_ok=True)
            with REMOVED_LOG.open("a", encoding="utf-8") as f:
                for h, verdict in promoted_to_removed:
                    f.write(f"{now_iso}  removed @{h}  verdict={verdict}  (auto-review)\n")
                    remove_from_watchlist(h)
                    # also drop their target override if any
                    overrides = targets_doc.get("handles") or {}
                    if h.lower() in overrides:
                        del overrides[h.lower()]
            _save_json(TARGETS_PATH, targets_doc)

    # Report
    print(f"=== review pass @ {now_iso} ===")
    print(f"  criteria: avg_score<{crit['min_avg_score']}, ≥{crit['min_tweets_for_judgment']} tweets, "
          f"stale>{crit['stale_age_days']}d, sideline {crit['sideline_days']}d, "
          f"remove after {crit['max_failed_reviews']} fails")
    if args.dry_run:
        print("  [DRY RUN — no changes written]")
    print()

    if new_sidelined:
        print(f"⊘ sidelined ({len(new_sidelined)}):")
        for h, v, s in new_sidelined:
            extra = ""
            if v == "low_score": extra = f"avg={s['avg_score']:.2f} n={s['tweets']}"
            elif v == "stale":   extra = f"newest {s['newest_age_days']}d old"
            elif v == "dead":    extra = "visited but no tweets"
            print(f"    @{h:<26}  {v:<10}  {extra}")
        print()

    if still_sidelined:
        print(f"⊘ still sidelined / 2nd strike ({len(still_sidelined)}):  " + ", ".join("@"+h for h in still_sidelined[:20]))
        print()

    if promoted_to_removed:
        action = "would remove" if args.dry_run or args.keep_removed else "REMOVED"
        print(f"✗ {action} from watchlist ({len(promoted_to_removed)}):")
        for h, v in promoted_to_removed:
            print(f"    @{h:<26}  verdict={v}")
        print()

    if acquitted:
        print(f"✓ acquitted ({len(acquitted)}):  " + ", ".join("@"+h for h in acquitted[:20]))
        print()

    # totals
    by_status = {"active": 0, "sidelined": 0, "removed": 0}
    for h, e in handles_rev.items():
        by_status[e.get("status", "active")] = by_status.get(e.get("status", "active"), 0) + 1
    total = len(parse_watchlist())
    print(f"summary: {total} accounts in watchlist · "
          f"{by_status['sidelined']} sidelined · {by_status['removed']} marked-removed")
    if not promoted_to_removed and not new_sidelined and not still_sidelined and not acquitted:
        print("no changes — all judged accounts are healthy 🎯")
    return 0


def cmd_sidelined(args) -> int:
    doc = _load_review()
    rows = []
    for h, e in doc["handles"].items():
        if e.get("status") in ("sidelined", "removed"):
            rows.append((h, e))
    if not rows:
        print("nothing sidelined.")
        return 0
    rows.sort(key=lambda r: r[1].get("last_reviewed") or "", reverse=True)
    print(f"{'handle':<28}  {'status':<10}  {'verdict':<10}  {'avg':>5}  {'n':>3}  {'reviews':>7}  next-review")
    print("─" * 100)
    for h, e in rows:
        s = e.get("stats_at_review") or {}
        nr = e.get("next_review_at") or "—"
        print(f"@{h:<27}  {e.get('status',''):<10}  "
              f"{(e.get('last_verdict') or '?'):<10}  "
              f"{(s.get('avg_score') or 0):>5.2f}  "
              f"{(s.get('tweets') or 0):>3}  "
              f"{e.get('review_count', 0):>7}  {nr[:19]}")
    print(f"\n{len(rows)} entries")
    return 0


def cmd_restore(args) -> int:
    doc = _load_review()
    h = args.handle.lstrip("@").lower()
    e = doc["handles"].get(h)
    if not e or e.get("status") == "active":
        print(f"@{args.handle.lstrip('@')} is not sidelined.")
        return 1
    was = e.get("status")
    e["status"] = "active"
    e["review_count"] = 0
    e["next_review_at"] = None
    e["last_verdict"] = None
    doc["handles"][h] = e
    _save_review(doc)
    print(f"@{args.handle.lstrip('@')}: {was} → active. Will re-enter rotation.")
    return 0


# ---------- export ----------

def cmd_export(args) -> int:
    _, posts = load_posts()
    if args.min_score is not None:
        posts = [t for t in posts if t.get("radar_score", 0) >= args.min_score]
    if args.from_handle:
        h = args.from_handle.lstrip("@").lower()
        posts = [t for t in posts if (t.get("author_handle") or "").lstrip("@").lower() == h]

    if args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["tweet_id", "score", "signal_type", "author", "section", "posted_at", "collected_at", "text", "url"])
        for t in posts:
            w.writerow([
                t.get("tweet_id"),
                f"{t.get('radar_score', 0):.3f}",
                t.get("signal_type") or "",
                "@" + (t.get("author_handle") or ""),
                t.get("section") or "",
                t.get("posted_at") or "",
                t.get("collected_at") or "",
                (t.get("text") or "").replace("\n", " "),
                t.get("url") or "",
            ])
        return 0

    # Default: JSON to stdout
    print(json.dumps(posts, ensure_ascii=False, indent=2))
    return 0


# ---------- Main ----------

def main() -> int:
    p = argparse.ArgumentParser(description="Manage the X collection — view, prune, tune.")
    sub = p.add_subparsers(dest="cmd", required=True)

    # list-accounts
    a = sub.add_parser("list-accounts", help="Show every watched account + its stats")
    a.add_argument("--status", help="Filter: active,never,data-only")
    a.add_argument("--section", help="Filter by section name")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_list_accounts)

    # show
    a = sub.add_parser("show", help="Detail for one account")
    a.add_argument("handle")
    a.set_defaults(func=cmd_show)

    # list-tweets
    a = sub.add_parser("list-tweets", help="Browse the tweet store")
    a.add_argument("--from", dest="from_handle", help="Filter by author")
    a.add_argument("--section", help="Filter by section tag")
    a.add_argument("--signal-type", help="Filter: pain | launch | opportunity | discussion | news")
    a.add_argument("--search", help="Substring match in text (case-insensitive)")
    a.add_argument("--min-score", type=float, help="Minimum radar_score")
    a.add_argument("--top", type=int, default=30, help="Limit (default 30)")
    a.add_argument("--sort", choices=["score", "recent", "posted"], default="score")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_list_tweets)

    # delete-account
    a = sub.add_parser("delete-account", help="Remove a handle from watchlist + (optionally) its tweets")
    a.add_argument("handle")
    a.add_argument("--keep-tweets", action="store_true", help="Remove from watchlist but keep collected tweets")
    a.add_argument("--yes", action="store_true", help="Skip confirmation")
    a.set_defaults(func=cmd_delete_account)

    # delete-tweet
    a = sub.add_parser("delete-tweet", help="Remove a single tweet by id")
    a.add_argument("tweet_id")
    a.add_argument("--yes", action="store_true")
    a.set_defaults(func=cmd_delete_tweet)

    # set-target
    a = sub.add_parser("set-target", help="Set tweets-per-visit target. Use 'default' as handle to update the global default.")
    a.add_argument("handle")
    a.add_argument("value", type=int)
    a.set_defaults(func=cmd_set_target)

    # reset-target
    a = sub.add_parser("reset-target", help="Remove a per-handle override → back to global default")
    a.add_argument("handle")
    a.set_defaults(func=cmd_reset_target)

    # targets
    a = sub.add_parser("targets", help="Show global default + all per-handle overrides")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_targets)

    # review — sideline low-value handles, retire repeat offenders
    a = sub.add_parser("review", help="Analyze each handle's content. Sideline low-value ones; remove repeat offenders.")
    a.add_argument("--dry-run", action="store_true", help="Print decisions without writing")
    a.add_argument("--keep-removed", action="store_true", help="Mark as 'removed' in review state but don't actually delete from watchlist")
    a.set_defaults(func=cmd_review)

    # sidelined — list currently sidelined / removed
    a = sub.add_parser("sidelined", help="Show currently sidelined and marked-removed handles")
    a.set_defaults(func=cmd_sidelined)

    # restore — manually return a sidelined handle to active rotation
    a = sub.add_parser("restore", help="Un-sideline a handle (back into the rotation)")
    a.add_argument("handle")
    a.set_defaults(func=cmd_restore)

    # export
    a = sub.add_parser("export", help="Export tweets to JSON (default) or CSV")
    a.add_argument("--csv", action="store_true")
    a.add_argument("--from", dest="from_handle")
    a.add_argument("--min-score", type=float)
    a.set_defaults(func=cmd_export)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
