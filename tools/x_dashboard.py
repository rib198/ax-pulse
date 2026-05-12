#!/usr/bin/env python3
"""Local dashboard for the X collection pipeline.

A tiny HTTP server + single-page HTML dashboard so a non-programmer can:
  • See where the Safari collector has reached
  • Start / stop / restart it
  • Run review (sideline low-value) and auto-target (promote high-value)
  • Browse accounts, tweets, sidelined, promoted
  • Manually restore or set a target

Run:
  ./x-dashboard.command
  open http://localhost:7870

Reads:
  data/manual_x/posts.json
  data/manual_x/safari_state.json
  data/manual_x/handle_review.json
  data/manual_x/handle_targets.json
  data/manual_x/watchlist.txt
  logs/safari-continuous.log

Writes (via x_manage.py subprocess): handle_review.json, handle_targets.json, watchlist.txt
Controls: tools/x_safari_browse.py --continuous (start/stop)
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"
STATE_PATH = ROOT / "data" / "manual_x" / "safari_state.json"
REVIEW_PATH = ROOT / "data" / "manual_x" / "handle_review.json"
TARGETS_PATH = ROOT / "data" / "manual_x" / "handle_targets.json"
WATCHLIST_PATH = ROOT / "data" / "manual_x" / "watchlist.txt"
LOG_PATH = ROOT / "logs" / "safari-continuous.log"
SAFARI_CMD = ROOT / "x-safari-continuous.command"
MANAGE_PY = ROOT / "tools" / "x_manage.py"
SAFARI_PY = ROOT / "tools" / "x_safari_browse.py"

PORT_BASE = 7870


# ---------- Helpers ----------

def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ago(iso: str | None) -> str:
    if not iso: return "—"
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return "—"
    d = datetime.now(timezone.utc) - t
    if d.days >= 1: return f"منذ {d.days} يوم"
    h = int(d.total_seconds() / 3600)
    if h >= 1: return f"منذ {h} س"
    m = int(d.total_seconds() / 60)
    if m >= 1: return f"منذ {m} د"
    return "الآن"


def parse_watchlist() -> list[tuple[str, str]]:
    if not WATCHLIST_PATH.exists():
        return []
    out, section, seen = [], "watchlist", set()
    for raw in WATCHLIST_PATH.read_text("utf-8").splitlines():
        s = raw.strip()
        if not s: continue
        if s.startswith("##"):
            section = s.lstrip("#").strip() or "watchlist"
            continue
        if s.startswith("#"): continue
        h = s.split()[0].lstrip("@")
        if not h or ".bsky." in h or "@" in h: continue
        if h.lower() in seen: continue
        seen.add(h.lower())
        out.append((h, section))
    return out


def find_safari_pid() -> int | None:
    try:
        r = subprocess.run(["pgrep", "-f", "x_safari_browse.py"],
                           capture_output=True, text=True, timeout=3)
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                return int(line)
    except Exception:
        pass
    return None


def start_safari() -> tuple[bool, str]:
    if find_safari_pid():
        return (False, "الأداة شغّالة بالفعل.")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\n=== launched from dashboard {_now_iso()} ===\n")
    p = subprocess.Popen(
        [str(SAFARI_CMD)],
        stdout=open(LOG_PATH, "a"), stderr=subprocess.STDOUT,
        cwd=str(ROOT), start_new_session=True,
    )
    time.sleep(2)
    pid = find_safari_pid()
    if pid:
        return (True, f"تم التشغيل (PID {pid}).")
    return (False, f"فشل التشغيل — راجع {LOG_PATH.name}.")


def stop_safari() -> tuple[bool, str]:
    pid = find_safari_pid()
    if not pid:
        return (False, "الأداة متوقفة بالفعل.")
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(3)
        if find_safari_pid():
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        return (True, f"تم الإيقاف (PID {pid}).")
    except ProcessLookupError:
        return (True, "متوقفة الآن.")
    except Exception as e:
        return (False, f"فشل الإيقاف: {e}")


def run_manage(args: list[str]) -> dict:
    """Run a tools/x_manage.py subcommand and return parsed output."""
    try:
        r = subprocess.run(
            [sys.executable, str(MANAGE_PY), *args],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        return {
            "ok": r.returncode == 0,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "code": r.returncode,
        }
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "code": -1}


# ---------- API data builders ----------

def api_state() -> dict:
    posts = _load(POSTS_PATH, {"items": []}).get("items") or []
    state = _load(STATE_PATH, {})
    review = _load(REVIEW_PATH, {"handles": {}})
    targets = _load(TARGETS_PATH, {"default": 100, "handles": {}, "sources": {}})

    wl = parse_watchlist()
    review_handles = review.get("handles") or {}
    sidelined = sum(1 for e in review_handles.values() if e.get("status") == "sidelined")
    paused    = sum(1 for e in review_handles.values() if e.get("status") == "paused")
    removed   = sum(1 for e in review_handles.values() if e.get("status") == "removed")

    enriched = [p for p in posts if p.get("radar_score", 0) > 0]
    scores = [p["radar_score"] for p in enriched]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    dc = state.get("daily_counters") or {}
    history = state.get("handle_history") or {}

    overrides = targets.get("handles") or {}

    # Tier distribution
    tiers = {"default": 0, "good_200": 0, "high_350": 0, "elite_500": 0, "premium_700": 0}
    for v in overrides.values():
        if v >= 700: tiers["premium_700"] += 1
        elif v >= 500: tiers["elite_500"] += 1
        elif v >= 350: tiers["high_350"] += 1
        elif v >= 200: tiers["good_200"] += 1
    tiers["default"] = len(wl) - len(overrides) - sidelined - paused - removed

    pid = find_safari_pid()

    return {
        "running":         pid is not None,
        "pid":             pid,
        "now":             _now_iso(),
        "watchlist_total": len(wl),
        "active":          len(wl) - sidelined - paused - removed,
        "sidelined":       sidelined,
        "paused":          paused,
        "removed":         removed,
        "store_total":     len(posts),
        "unique_authors":  len({(p.get("author_handle") or "").lower() for p in posts}),
        "all_time_visited": len(history),
        "today_date":      dc.get("date"),
        "today_handles":   dc.get("handles_visited", 0),
        "today_tweets":    dc.get("tweets_collected", 0),
        "daily_quota_handles": 260,
        "daily_quota_tweets":  22000,
        "avg_score":       round(avg_score, 3),
        "scores_ge_035":   sum(1 for s in scores if s >= 0.35),
        "scores_ge_050":   sum(1 for s in scores if s >= 0.50),
        "enriched_count":  len(enriched),
        "tiers":           tiers,
        "default_target":  targets.get("default", 100),
        "overrides_count": len(overrides),
        "last_session":    state.get("last_session"),
    }


def api_handles(filter_status: str | None, search: str | None, section: str | None) -> list[dict]:
    posts = _load(POSTS_PATH, {"items": []}).get("items") or []
    review = _load(REVIEW_PATH, {"handles": {}}).get("handles") or {}
    targets = _load(TARGETS_PATH, {"default": 100, "handles": {}, "sources": {}})
    overrides = targets.get("handles") or {}
    sources = targets.get("sources") or {}
    default_t = targets.get("default", 100)
    state = _load(STATE_PATH, {})
    history = state.get("handle_history") or {}

    by_h = {}
    for p in posts:
        h = (p.get("author_handle") or "").lstrip("@").lower()
        if h:
            by_h.setdefault(h, []).append(p)

    rows = []
    for handle, section_n in parse_watchlist():
        hlow = handle.lower()
        ts = by_h.get(hlow, [])
        last = history.get(hlow)
        avg = (sum(t.get("radar_score", 0) for t in ts) / len(ts)) if ts else 0
        target = overrides.get(hlow, default_t)
        src = sources.get(hlow, "default")
        rev = review.get(hlow) or {}
        status = rev.get("status") or ("active" if last else ("never" if not ts else "data-only"))
        rows.append({
            "handle":     handle,
            "section":    section_n,
            "tweets":     len(ts),
            "avg_score":  round(avg, 3),
            "target":     target,
            "target_source": src,
            "last_visit": last,
            "last_visit_ago": _ago(last),
            "status":     status,
            "verdict":    rev.get("last_verdict"),
            "review_count": rev.get("review_count", 0),
        })

    if filter_status:
        if filter_status == "promoted":
            rows = [r for r in rows if r["target"] > default_t]
        elif filter_status == "active":
            rows = [r for r in rows if r["status"] == "active"]
        else:
            rows = [r for r in rows if r["status"] == filter_status]
    if section:
        rows = [r for r in rows if r["section"] == section]
    if search:
        s = search.lower()
        rows = [r for r in rows if s in r["handle"].lower() or s in (r["section"] or "").lower()]

    return rows


def api_tweets(top: int, from_h: str | None, min_score: float | None) -> list[dict]:
    posts = _load(POSTS_PATH, {"items": []}).get("items") or []
    items = posts[:]
    if from_h:
        h = from_h.lstrip("@").lower()
        items = [t for t in items if (t.get("author_handle") or "").lstrip("@").lower() == h]
    if min_score is not None:
        items = [t for t in items if t.get("radar_score", 0) >= min_score]
    items.sort(key=lambda t: -(t.get("radar_score") or 0))
    items = items[:top]
    out = []
    for t in items:
        out.append({
            "tweet_id":     t.get("tweet_id"),
            "score":        round(t.get("radar_score", 0), 3),
            "signal_type":  t.get("signal_type"),
            "author":       t.get("author_handle"),
            "section":      t.get("section"),
            "posted_at":    t.get("posted_at"),
            "collected_at": t.get("collected_at"),
            "collected_ago": _ago(t.get("collected_at")),
            "text":         (t.get("text") or "")[:400],
            "url":          t.get("url"),
            "lang":         t.get("lang"),
        })
    return out


def api_log(lines: int = 60) -> str:
    if not LOG_PATH.exists(): return ""
    try:
        with LOG_PATH.open("r", encoding="utf-8") as f:
            tail = f.readlines()[-lines:]
        return "".join(tail)
    except Exception:
        return ""


# ---------- HTML page ----------

HTML = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>الرادار — لوحة التحكم</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: linear-gradient(180deg, #0a0e1a 0%, #0e1530 100%);
    color: #e4e9f5; font-family: -apple-system, "SF Pro Text", "Segoe UI", Tahoma, sans-serif;
    min-height: 100vh; font-size: 14px;
  }
  .container { max-width: 1400px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 22px; font-weight: 600; }
  h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #8ea1ce; }
  .muted { color: #8696b5; }
  .small { font-size: 12px; }

  /* Top bar */
  header {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,.04); backdrop-filter: blur(6px);
    border: 1px solid rgba(255,255,255,.06); border-radius: 14px;
    padding: 18px 22px; margin-bottom: 18px;
  }
  .brand { display: flex; align-items: center; gap: 14px; }
  .status-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #4a5470;
  }
  .status-dot.on { background: #2bdc8e; box-shadow: 0 0 12px #2bdc8e80; }
  .status-text { font-weight: 500; }
  .btn {
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
    color: #e4e9f5; padding: 8px 16px; border-radius: 8px;
    font-size: 13px; cursor: pointer; transition: all .15s;
  }
  .btn:hover { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.2); }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn.primary { background: #2bdc8e; color: #051515; border-color: #2bdc8e; font-weight: 600; }
  .btn.primary:hover { background: #45e8a1; }
  .btn.danger { background: #ff5f6d20; border-color: #ff5f6d50; color: #ff8f99; }
  .btn.danger:hover { background: #ff5f6d35; }
  .actions { display: flex; gap: 8px; }

  /* Stats grid */
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
  .card {
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06);
    border-radius: 12px; padding: 16px;
  }
  .card .label { font-size: 12px; color: #8696b5; margin-bottom: 8px; }
  .card .value { font-size: 26px; font-weight: 600; color: #ffffff; }
  .card .sub { font-size: 12px; color: #a8b8d8; margin-top: 6px; }
  .progress { height: 4px; background: rgba(255,255,255,.08); border-radius: 4px; margin-top: 8px; overflow: hidden; }
  .progress > div { height: 100%; background: linear-gradient(90deg, #2bdc8e, #4cb5ff); border-radius: 4px; transition: width .3s; }

  /* Tabs */
  .tabs { display: flex; gap: 4px; border-bottom: 1px solid rgba(255,255,255,.08); margin-bottom: 18px; }
  .tab {
    padding: 10px 18px; cursor: pointer; color: #8ea1ce;
    border-bottom: 2px solid transparent; font-size: 14px;
  }
  .tab:hover { color: #d0d9f0; }
  .tab.active { color: #ffffff; border-bottom-color: #2bdc8e; }
  .panel { display: none; }
  .panel.active { display: block; }

  /* Tables */
  .controls { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
  .controls input, .controls select {
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
    color: #e4e9f5; padding: 7px 12px; border-radius: 7px; font-size: 13px;
    min-width: 140px;
  }
  .controls input:focus, .controls select:focus { outline: none; border-color: #2bdc8e; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: right; padding: 10px 12px; color: #8ea1ce; font-weight: 500; font-size: 12px;
       background: rgba(255,255,255,.04); border-bottom: 1px solid rgba(255,255,255,.08); }
  td { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,.04); }
  tr:hover td { background: rgba(255,255,255,.02); }
  .badge {
    display: inline-block; padding: 2px 9px; border-radius: 11px;
    font-size: 11px; font-weight: 500;
  }
  .badge.active   { background: #2bdc8e20; color: #2bdc8e; }
  .badge.sidelined { background: #ffb44a20; color: #ffb44a; }
  .badge.paused    { background: #b785ff20; color: #c89dff; }
  .badge.removed   { background: #ff5f6d20; color: #ff8f99; }
  .badge.never     { background: rgba(255,255,255,.06); color: #8696b5; }
  .badge.data-only { background: #4cb5ff20; color: #4cb5ff; }
  .badge.good     { background: #2bdc8e30; color: #6df1ad; }
  .badge.high     { background: #4cb5ff30; color: #80ccff; }
  .badge.elite    { background: #b785ff30; color: #d2b3ff; }
  .badge.premium  { background: #ffd16a30; color: #ffdc94; }
  .badge.manual   { background: #ff5f6d30; color: #ff97a1; }
  .badge.auto     { background: #4cb5ff20; color: #80ccff; }

  /* Tweet cards */
  .tweets-grid { display: grid; gap: 10px; }
  .tweet {
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.05);
    border-radius: 10px; padding: 14px;
  }
  .tweet .head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12px; }
  .tweet .author { color: #80ccff; font-weight: 500; }
  .tweet .score { color: #ffd16a; font-weight: 600; font-family: ui-monospace, monospace; }
  .tweet .text { color: #e4e9f5; line-height: 1.7; font-size: 14px; word-break: break-word; }
  .tweet .text a { color: #80ccff; }

  /* Log box */
  .log {
    background: #050810; border: 1px solid rgba(255,255,255,.06);
    border-radius: 10px; padding: 14px; font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12px; color: #a8b8d8; max-height: 600px; overflow-y: auto;
    direction: ltr; text-align: left; white-space: pre-wrap; line-height: 1.55;
  }
  .log .recent { color: #2bdc8e; }

  /* Toast */
  .toast {
    position: fixed; top: 22px; left: 50%; transform: translateX(-50%);
    background: #131a30; border: 1px solid rgba(255,255,255,.1); border-radius: 10px;
    padding: 12px 22px; color: #e4e9f5; font-size: 14px; z-index: 100;
    box-shadow: 0 8px 24px rgba(0,0,0,.4); opacity: 0; transition: opacity .2s;
    pointer-events: none;
  }
  .toast.show { opacity: 1; }
  .toast.ok { border-color: #2bdc8e60; }
  .toast.err { border-color: #ff5f6d60; }

  /* Tier chips */
  .tier-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
  .tier-chip {
    padding: 4px 12px; border-radius: 8px; font-size: 12px;
    background: rgba(255,255,255,.05); display: flex; gap: 8px; align-items: center;
  }
  .tier-chip b { color: #ffffff; }

  /* Loading */
  .loading { padding: 40px; text-align: center; color: #8696b5; }

  /* Section icons */
  .ic { display: inline-block; width: 14px; text-align: center; }
</style>
</head>
<body>
<div class="container">

<header>
  <div class="brand">
    <span class="status-dot" id="status-dot"></span>
    <h1>الرادار — لوحة جمع المحتوى</h1>
    <span class="muted" id="status-text">جاري التحقق…</span>
  </div>
  <div class="actions">
    <button class="btn primary" id="btn-start">▶ تشغيل</button>
    <button class="btn danger" id="btn-stop">■ إيقاف</button>
    <button class="btn" id="btn-restart">🔄 إعادة</button>
  </div>
</header>

<div class="stats">
  <div class="card">
    <div class="label">اليوم — حسابات</div>
    <div class="value" id="stat-today-handles">—</div>
    <div class="sub" id="stat-today-handles-sub">—</div>
    <div class="progress"><div id="prog-today-handles" style="width: 0"></div></div>
  </div>
  <div class="card">
    <div class="label">اليوم — تغريدات</div>
    <div class="value" id="stat-today-tweets">—</div>
    <div class="sub" id="stat-today-tweets-sub">—</div>
    <div class="progress"><div id="prog-today-tweets" style="width: 0"></div></div>
  </div>
  <div class="card">
    <div class="label">المخزن — تغريدات</div>
    <div class="value" id="stat-store">—</div>
    <div class="sub" id="stat-store-sub">—</div>
  </div>
  <div class="card">
    <div class="label">المخزن — جودة</div>
    <div class="value" id="stat-quality">—</div>
    <div class="sub" id="stat-quality-sub">متوسط النقاط</div>
  </div>
</div>

<div class="stats" style="grid-template-columns: 2fr 1fr;">
  <div class="card">
    <div class="label">توزيع الطبقات (Tiers)</div>
    <div class="tier-row" id="tier-row">—</div>
  </div>
  <div class="card">
    <div class="label">الدورة الكاملة</div>
    <div class="value" id="stat-cycle">—</div>
    <div class="sub" id="stat-cycle-sub">من إجمالي watchlist</div>
    <div class="progress"><div id="prog-cycle" style="width: 0"></div></div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" data-tab="handles">الحسابات</div>
  <div class="tab" data-tab="tweets">التغريدات</div>
  <div class="tab" data-tab="review">العزل والترقية</div>
  <div class="tab" data-tab="log">السجل المباشر</div>
</div>

<div class="panel active" id="panel-handles">
  <div class="controls" style="background:rgba(180,90,255,.06); border:1px solid rgba(180,90,255,.15); padding:12px; border-radius:10px; margin-bottom:14px;">
    <span class="muted small">⏸ إيقاف نطاق بحسب الترتيب (لا يحذف، يتخطّى من الدوران فقط):</span>
    <input type="number" id="pr-from" placeholder="من #" style="min-width:90px;">
    <input type="number" id="pr-to" placeholder="إلى #" style="min-width:90px;">
    <button class="btn" id="btn-pause-range">⏸ إيقاف النطاق</button>
    <button class="btn" id="btn-unpause-all">↻ استعادة كل الموقوفين</button>
  </div>
  <div class="controls">
    <input type="text" id="h-search" placeholder="🔍 بحث (handle أو قسم)…">
    <select id="h-status">
      <option value="">كل الحالات</option>
      <option value="active">نشطة</option>
      <option value="never">لم تُزَر</option>
      <option value="data-only">بيانات فقط</option>
      <option value="sidelined">معزولة تلقائياً</option>
      <option value="paused">موقوفة يدوياً</option>
      <option value="removed">محذوفة</option>
      <option value="promoted">مرقّاة (target > default)</option>
    </select>
    <select id="h-section"><option value="">كل الأقسام</option></select>
    <button class="btn" id="btn-refresh-handles">🔄 تحديث</button>
  </div>
  <div id="handles-table">
    <div class="loading">جاري التحميل…</div>
  </div>
</div>

<div class="panel" id="panel-tweets">
  <div class="controls">
    <input type="number" id="t-min-score" placeholder="حد أدنى للنقاط (مثال 0.3)" step="0.05">
    <input type="text" id="t-from" placeholder="من حساب (handle بدون @)">
    <input type="number" id="t-top" value="50" placeholder="أعلى N">
    <button class="btn" id="btn-refresh-tweets">🔄 تحديث</button>
  </div>
  <div id="tweets-list">
    <div class="loading">جاري التحميل…</div>
  </div>
</div>

<div class="panel" id="panel-review">
  <div class="controls" style="margin-bottom: 18px;">
    <button class="btn primary" id="btn-review">📋 تشغيل المراجعة</button>
    <button class="btn primary" id="btn-auto-target">🎯 ترقية تلقائية</button>
    <button class="btn" id="btn-review-dryrun">🔍 محاكاة مراجعة</button>
    <button class="btn" id="btn-auto-target-dryrun">🔍 محاكاة ترقية</button>
  </div>
  <div class="card" style="margin-bottom: 18px;">
    <h2>نتيجة آخر تشغيل</h2>
    <pre class="log" id="review-output" style="max-height:300px;">— لم تُشغَّل بعد —</pre>
  </div>
  <h2>الحسابات المعزولة حالياً</h2>
  <div id="sidelined-list"><div class="loading">جاري التحميل…</div></div>
</div>

<div class="panel" id="panel-log">
  <div class="controls">
    <button class="btn" id="btn-refresh-log">🔄 تحديث</button>
    <label class="muted small" style="display:flex;align-items:center;gap:6px;">
      <input type="checkbox" id="log-auto" checked> تحديث تلقائي كل 5 ثوانٍ
    </label>
  </div>
  <pre class="log" id="log-content">جاري التحميل…</pre>
</div>

</div>

<div class="toast" id="toast"></div>

<script>
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

let currentTab = 'handles';
let logAutoTimer = null;

function toast(msg, kind='ok') {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast show ' + kind;
  setTimeout(()=> t.className = 'toast ' + kind, 3000);
}

async function api(path, opts) {
  try {
    const r = await fetch(path, opts);
    return await r.json();
  } catch (e) {
    toast('فشل الاتصال بالخادم', 'err');
    return null;
  }
}

function setStat(id, val, sub) {
  $('#'+id).textContent = (val ?? '—');
  if (sub !== undefined) $('#'+id+'-sub').textContent = sub;
}

function fmtNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString('ar');
}

async function refreshState() {
  const s = await api('/api/state');
  if (!s) return;

  // Top bar
  const dot = $('#status-dot');
  const txt = $('#status-text');
  if (s.running) {
    dot.classList.add('on');
    txt.textContent = `تعمل (PID ${s.pid}) — كل ~3 د حساب جديد`;
    $('#btn-start').disabled = true;
    $('#btn-stop').disabled = false;
    $('#btn-restart').disabled = false;
  } else {
    dot.classList.remove('on');
    txt.textContent = 'متوقفة';
    $('#btn-start').disabled = false;
    $('#btn-stop').disabled = true;
    $('#btn-restart').disabled = false;
  }

  // Cards
  setStat('stat-today-handles', fmtNum(s.today_handles),
    `من سقف ${fmtNum(s.daily_quota_handles)} (${s.today_date || '—'})`);
  $('#prog-today-handles').style.width = Math.min(100, 100*s.today_handles/s.daily_quota_handles) + '%';

  setStat('stat-today-tweets', fmtNum(s.today_tweets),
    `من سقف ${fmtNum(s.daily_quota_tweets)} يومياً`);
  $('#prog-today-tweets').style.width = Math.min(100, 100*s.today_tweets/s.daily_quota_tweets) + '%';

  setStat('stat-store', fmtNum(s.store_total),
    `${fmtNum(s.unique_authors)} مؤلّف فريد — كل التغريدات مفهرسة`);

  setStat('stat-quality', s.avg_score.toFixed(3),
    `${fmtNum(s.scores_ge_035)} تغريدة ≥ 0.35  ·  ${fmtNum(s.scores_ge_050)} ≥ 0.50`);

  // Tier chips
  const tr = $('#tier-row');
  const t = s.tiers;
  const chips = [
    ['default 100',    t.default,    ''],
    ['good 200',       t.good_200,   'good'],
    ['high 350',       t.high_350,   'high'],
    ['elite 500',      t.elite_500,  'elite'],
    ['premium 700',    t.premium_700,'premium'],
    ['معزولة تلقائياً',  s.sidelined,  'sidelined'],
    ['موقوفة يدوياً',   s.paused,     'paused'],
  ];
  tr.innerHTML = chips.map(([label, n, cls]) =>
    `<div class="tier-chip"><span class="badge ${cls}">${label}</span><b>${fmtNum(n)}</b></div>`
  ).join('');

  // Cycle
  setStat('stat-cycle', `${fmtNum(s.all_time_visited)} / ${fmtNum(s.active)}`,
    `${fmtNum(s.watchlist_total)} في القائمة (${fmtNum(s.sidelined)} معزولة)`);
  $('#prog-cycle').style.width = Math.min(100, 100*s.all_time_visited/Math.max(1, s.active)) + '%';
}

async function loadHandles() {
  const q = new URLSearchParams();
  const search = $('#h-search').value.trim();
  const status = $('#h-status').value;
  const section = $('#h-section').value;
  if (search) q.set('search', search);
  if (status) q.set('status', status);
  if (section) q.set('section', section);
  const rows = await api('/api/handles?' + q.toString());
  if (!rows) return;

  // Populate section dropdown if first call
  if ($('#h-section').options.length <= 1) {
    const secs = [...new Set(rows.map(r => r.section))].sort();
    $('#h-section').innerHTML = '<option value="">كل الأقسام</option>' +
      secs.map(s => `<option value="${s}">${s}</option>`).join('');
  }

  const html = `
    <table>
      <thead><tr>
        <th>#</th><th>الحساب</th><th>القسم</th><th>تغريدات</th><th>متوسط</th>
        <th>الهدف</th><th>المصدر</th><th>الحالة</th><th>آخر زيارة</th><th>إجراء</th>
      </tr></thead>
      <tbody>
      ${rows.slice(0, 500).map((r,i) => {
        let tierCls = '';
        if (r.target >= 700) tierCls = 'premium';
        else if (r.target >= 500) tierCls = 'elite';
        else if (r.target >= 350) tierCls = 'high';
        else if (r.target >= 200) tierCls = 'good';
        return `
        <tr>
          <td>${i+1}</td>
          <td><a href="https://x.com/${r.handle}" target="_blank" style="color:#80ccff;text-decoration:none;">@${r.handle}</a></td>
          <td class="small muted">${r.section}</td>
          <td>${r.tweets}</td>
          <td>${r.avg_score.toFixed(2)}</td>
          <td><span class="badge ${tierCls}">${r.target}</span></td>
          <td><span class="badge ${r.target_source}">${r.target_source}</span></td>
          <td><span class="badge ${r.status}">${r.status}${r.verdict?' / '+r.verdict:''}</span></td>
          <td class="small muted">${r.last_visit_ago}</td>
          <td>
            ${r.status === 'paused'
              ? `<button class="btn small" onclick="unpauseHandle('${r.handle}')">↻</button>`
              : (r.status === 'sidelined' || r.status === 'removed'
                  ? `<button class="btn small" onclick="restoreHandle('${r.handle}')">↻</button>`
                  : `<button class="btn small" onclick="pauseHandle('${r.handle}')">⏸</button>`)}
            <button class="btn small" onclick="setTargetPrompt('${r.handle}')">🎯</button>
          </td>
        </tr>`;
      }).join('')}
      </tbody>
    </table>
    <div class="small muted" style="padding: 12px;">
      ${rows.length > 500 ? `يُعرض 500 من ${rows.length}` : `${rows.length} حساب`}
    </div>
  `;
  $('#handles-table').innerHTML = html;
}

async function loadTweets() {
  const top = $('#t-top').value || 50;
  const fromH = $('#t-from').value.trim();
  const minS = $('#t-min-score').value;
  const q = new URLSearchParams({top});
  if (fromH) q.set('from', fromH);
  if (minS) q.set('min_score', minS);
  const tweets = await api('/api/tweets?' + q.toString());
  if (!tweets) return;
  if (!tweets.length) {
    $('#tweets-list').innerHTML = '<div class="loading">لا توجد تغريدات مطابقة.</div>';
    return;
  }
  const html = `<div class="tweets-grid">
    ${tweets.map(t => `
      <div class="tweet">
        <div class="head">
          <span class="score">${t.score.toFixed(2)}</span>
          <a class="author" href="https://x.com/${t.author}" target="_blank">@${t.author}</a>
          <span class="muted">${t.section || ''}</span>
          ${t.signal_type ? `<span class="badge">${t.signal_type}</span>` : ''}
          <span class="muted small" style="margin-right:auto;">${t.collected_ago}</span>
        </div>
        <div class="text">${escape_html(t.text)}</div>
        ${t.url ? `<div class="small muted" style="margin-top:6px;"><a href="${t.url}" target="_blank" style="color:#80ccff;">عرض على X →</a></div>` : ''}
      </div>
    `).join('')}
  </div>`;
  $('#tweets-list').innerHTML = html;
}

function escape_html(s) {
  if (!s) return '';
  return s.replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));
}

async function loadSidelined() {
  const r = await api('/api/handles?status=sidelined');
  if (!r) return;
  if (!r.length) {
    $('#sidelined-list').innerHTML = '<div class="loading">لا يوجد حسابات معزولة.</div>';
    return;
  }
  $('#sidelined-list').innerHTML = `<table>
    <thead><tr><th>الحساب</th><th>السبب</th><th>متوسط</th><th>تغريدات</th><th>مراجعات</th><th>الإجراء</th></tr></thead>
    <tbody>${r.map(x => `
      <tr>
        <td><a href="https://x.com/${x.handle}" target="_blank" style="color:#80ccff;text-decoration:none;">@${x.handle}</a></td>
        <td><span class="badge sidelined">${x.verdict || '?'}</span></td>
        <td>${x.avg_score.toFixed(2)}</td>
        <td>${x.tweets}</td>
        <td>${x.review_count}</td>
        <td><button class="btn small" onclick="restoreHandle('${x.handle}')">↻ استعادة</button></td>
      </tr>`).join('')}</tbody>
  </table>`;
}

async function loadLog() {
  const r = await api('/api/log');
  if (r === null) return;
  $('#log-content').textContent = r.text || '(فارغ)';
  $('#log-content').scrollTop = $('#log-content').scrollHeight;
}

async function callAction(cmd, args={}) {
  const r = await api('/api/action', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({cmd, ...args}),
  });
  if (!r) { toast('فشل', 'err'); return null; }
  toast(r.message || (r.ok ? 'تم' : 'فشل'), r.ok ? 'ok' : 'err');
  refreshState();
  return r;
}

window.restoreHandle = async function(h) {
  const r = await callAction('restore', {handle: h});
  if (r?.ok) { loadHandles(); loadSidelined(); }
};

window.pauseHandle = async function(h) {
  if (!confirm(`إيقاف @${h} (تخطّيه من الدوران)؟`)) return;
  const r = await callAction('pause', {handle: h});
  if (r?.ok) loadHandles();
};

window.unpauseHandle = async function(h) {
  const r = await callAction('unpause', {handle: h});
  if (r?.ok) { loadHandles(); loadSidelined(); }
};

window.setTargetPrompt = async function(h) {
  const v = prompt(`الهدف الجديد لـ @${h} (تغريدة لكل زيارة، 5-2000):`);
  if (!v) return;
  const n = parseInt(v, 10);
  if (isNaN(n)) return;
  const r = await callAction('set-target', {handle: h, value: n});
  if (r?.ok) loadHandles();
};

// Wiring
$$('.tab').forEach(t => t.addEventListener('click', () => {
  $$('.tab').forEach(x => x.classList.remove('active'));
  $$('.panel').forEach(x => x.classList.remove('active'));
  t.classList.add('active');
  currentTab = t.dataset.tab;
  $('#panel-' + currentTab).classList.add('active');
  if (currentTab === 'handles') loadHandles();
  else if (currentTab === 'tweets') loadTweets();
  else if (currentTab === 'review') loadSidelined();
  else if (currentTab === 'log') loadLog();
}));

$('#btn-start').onclick = async () => {
  const r = await callAction('start');
};
$('#btn-stop').onclick = async () => {
  if (!confirm('إيقاف الأداة؟')) return;
  await callAction('stop');
};
$('#btn-restart').onclick = async () => {
  if (!confirm('إعادة تشغيل الأداة؟')) return;
  await callAction('restart');
};

$('#btn-review').onclick = async () => {
  const r = await callAction('review');
  if (r) $('#review-output').textContent = r.stdout || '(فارغ)';
  loadSidelined();
};
$('#btn-review-dryrun').onclick = async () => {
  const r = await callAction('review-dry');
  if (r) $('#review-output').textContent = r.stdout || '(فارغ)';
};
$('#btn-auto-target').onclick = async () => {
  const r = await callAction('auto-target');
  if (r) $('#review-output').textContent = r.stdout || '(فارغ)';
  loadHandles();
};
$('#btn-auto-target-dryrun').onclick = async () => {
  const r = await callAction('auto-target-dry');
  if (r) $('#review-output').textContent = r.stdout || '(فارغ)';
};

$('#btn-pause-range').onclick = async () => {
  const lo = parseInt($('#pr-from').value);
  const hi = parseInt($('#pr-to').value);
  if (!lo || !hi || hi < lo) { toast('أدخل نطاقاً صحيحاً', 'err'); return; }
  if (!confirm(`إيقاف الحسابات من #${lo} إلى #${hi}؟`)) return;
  const r = await callAction('pause-range', {from: lo, to: hi});
  if (r?.ok) loadHandles();
};

$('#btn-unpause-all').onclick = async () => {
  if (!confirm('استعادة كل الحسابات الموقوفة يدوياً؟')) return;
  const r = await callAction('unpause-all');
  if (r?.ok) loadHandles();
};

$('#btn-refresh-handles').onclick = loadHandles;
$('#h-search').addEventListener('input', () => {
  clearTimeout(window._hSearchT);
  window._hSearchT = setTimeout(loadHandles, 300);
});
$('#h-status').onchange = loadHandles;
$('#h-section').onchange = loadHandles;

$('#btn-refresh-tweets').onclick = loadTweets;
$('#btn-refresh-log').onclick = loadLog;
$('#log-auto').onchange = (e) => {
  if (e.target.checked) {
    logAutoTimer = setInterval(loadLog, 5000);
  } else if (logAutoTimer) {
    clearInterval(logAutoTimer);
    logAutoTimer = null;
  }
};

// Initial load
refreshState();
loadHandles();
setInterval(refreshState, 5000);
logAutoTimer = setInterval(loadLog, 5000);
</script>
</body>
</html>
"""


# ---------- HTTP handler ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass  # quiet

    def _json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, body, content_type="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._text(HTML)
        if u.path == "/api/state":
            return self._json(api_state())
        if u.path == "/api/handles":
            qs = parse_qs(u.query)
            return self._json(api_handles(
                qs.get("status", [None])[0],
                qs.get("search", [None])[0],
                qs.get("section", [None])[0],
            ))
        if u.path == "/api/tweets":
            qs = parse_qs(u.query)
            top = int(qs.get("top", ["50"])[0])
            fromh = qs.get("from", [None])[0]
            mins = qs.get("min_score", [None])[0]
            mins = float(mins) if mins else None
            return self._json(api_tweets(top, fromh, mins))
        if u.path == "/api/log":
            return self._json({"text": api_log(60)})
        return self._text("not found", "text/plain", 404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/action":
            return self._text("not found", "text/plain", 404)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except Exception:
            payload = {}
        cmd = payload.get("cmd")

        if cmd == "start":
            ok, msg = start_safari()
            return self._json({"ok": ok, "message": msg})

        if cmd == "stop":
            ok, msg = stop_safari()
            return self._json({"ok": ok, "message": msg})

        if cmd == "restart":
            stop_safari()
            time.sleep(2)
            ok, msg = start_safari()
            return self._json({"ok": ok, "message": "أُعيد التشغيل: " + msg})

        if cmd == "review":
            r = run_manage(["review"])
            return self._json({"ok": r["ok"], "message": "تمت المراجعة", **r})
        if cmd == "review-dry":
            r = run_manage(["review", "--dry-run"])
            return self._json({"ok": r["ok"], "message": "محاكاة المراجعة", **r})

        if cmd == "auto-target":
            r = run_manage(["auto-target"])
            return self._json({"ok": r["ok"], "message": "تمت الترقية", **r})
        if cmd == "auto-target-dry":
            r = run_manage(["auto-target", "--dry-run"])
            return self._json({"ok": r["ok"], "message": "محاكاة الترقية", **r})

        if cmd == "restore":
            h = payload.get("handle")
            if not h: return self._json({"ok": False, "message": "handle مطلوب"})
            r = run_manage(["restore", h])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:200]})

        if cmd == "set-target":
            h = payload.get("handle"); v = payload.get("value")
            if not h or v is None:
                return self._json({"ok": False, "message": "handle و value مطلوبان"})
            r = run_manage(["set-target", h, str(int(v))])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:200]})

        if cmd == "pause":
            h = payload.get("handle")
            if not h: return self._json({"ok": False, "message": "handle مطلوب"})
            r = run_manage(["pause", h])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:200]})

        if cmd == "pause-range":
            try:
                lo = int(payload.get("from", 0))
                hi = int(payload.get("to", 0))
            except (ValueError, TypeError):
                return self._json({"ok": False, "message": "from / to مطلوبان"})
            if lo < 1 or hi < lo:
                return self._json({"ok": False, "message": "نطاق غير صحيح"})
            r = run_manage(["pause-range", str(lo), str(hi)])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:300]})

        if cmd == "unpause":
            h = payload.get("handle")
            if not h: return self._json({"ok": False, "message": "handle مطلوب"})
            r = run_manage(["unpause", h])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:200]})

        if cmd == "unpause-all":
            r = run_manage(["unpause-all"])
            return self._json({"ok": r["ok"], "message": r["stdout"].strip()[:200]})

        return self._json({"ok": False, "message": f"أمر غير معروف: {cmd}"})


def find_open_port(start: int = PORT_BASE, span: int = 10) -> int:
    import socket
    for p in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p)); return p
            except OSError:
                continue
    raise RuntimeError("no open port found")


def main() -> int:
    port = find_open_port()
    print(f"=== لوحة الرادار — http://localhost:{port} ===")
    print(f"  posts:    {POSTS_PATH.name}")
    print(f"  watchlist: {WATCHLIST_PATH.name}  ({len(parse_watchlist())} handles)")
    print(f"  Safari PID: {find_safari_pid() or '—'}")
    print(f"  Ctrl+C للإيقاف")

    # Try opening the browser (non-blocking, best-effort)
    if sys.platform == "darwin":
        try:
            subprocess.Popen(["open", f"http://localhost:{port}"])
        except Exception:
            pass

    srv = HTTPServer(("127.0.0.1", port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
