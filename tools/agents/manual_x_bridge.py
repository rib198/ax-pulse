"""Agent — Manual X Bridge.

Imports manually-captured X posts from `data/manual_x/posts.json` and
injects them into the radar pipeline at the same point RSS/HN/GitHub
items enter — i.e. before EvidenceGuard. From that moment forward they
flow through every downstream agent (priority ranker, event detector,
opportunity builder, radar editor, social, insight, memory) like any
other source.

The agent never modifies `data/manual_x/posts.json`. It reads, normalizes,
and appends to `ctx.state["raw_items"]`. Downstream agents see them as
regular signals with a `manual: true` flag + author_handle, so the UI
can render them with the dedicated X treatment.

Filter rules (tuneable in data/config.json):
  - skip if verification_status == "rejected"
  - skip if posted_at older than 30 days
  - skip if text shorter than 20 chars
  - keep otherwise (we want broad coverage; the ranker decides priority)

Score normalization:
  pain_signal_score (0..1) → opportunity_score (0..1)
  public_metrics.likes/replies → engagement boost
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DATA_DIR,
    now_iso,
    read_json,
    truncate,
)


MANUAL_X_PATH = DATA_DIR / "manual_x" / "posts.json"
MAX_AGE_DAYS = 30
MIN_TEXT_LEN = 20

# Detect short-form pain/launch phrases the legacy scorer used.
PAIN_PHRASES = re.compile(
    r"\b(broken|bug|hate|wish|need|frustrat|slow|expensive|impossible|"
    r"problem|missing|fail|painful|cost too much|"
    r"مشكلة|صعب|بطيء|غالي|أحتاج|أتمنى)\b",
    re.IGNORECASE,
)
LAUNCH_PHRASES = re.compile(
    r"\b(launch|released|announce|introduc|ship|available now|drops?|"
    r"إطلاق|أعلنت|متاح|أصدر)\b",
    re.IGNORECASE,
)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _signal_type(text: str, pain: float) -> str:
    if pain >= 0.5 or PAIN_PHRASES.search(text):
        return "pain"
    if LAUNCH_PHRASES.search(text):
        return "launch"
    return "news"


def _engagement(metrics: dict) -> int:
    if not metrics:
        return 0
    return int((metrics.get("likes") or 0)
               + (metrics.get("reposts") or 0) * 3
               + (metrics.get("replies") or 0) * 2
               + (metrics.get("quotes") or 0) * 2)


def _opportunity_score(post: dict) -> float:
    """Combine the curator's pain score with raw engagement so quietly-
    interesting posts can still surface alongside loud ones."""
    pain = float(post.get("pain_signal_score") or 0)
    eng = _engagement(post.get("public_metrics") or {})
    eng_norm = min(0.35, eng / 1000)
    text = post.get("text") or ""
    tags = len(post.get("opportunity_tags") or [])
    tag_boost = min(0.15, tags * 0.05)
    keywords = len(post.get("matched_keywords") or [])
    kw_boost = min(0.10, keywords * 0.03)
    pain_floor = max(pain, 0.18 if PAIN_PHRASES.search(text) else 0)
    return round(min(1.0, pain_floor + eng_norm + tag_boost + kw_boost), 3)


def _normalize(post: dict, run_at: str) -> dict | None:
    text = (post.get("text") or "").strip()
    if len(text) < MIN_TEXT_LEN:
        return None
    if (post.get("verification_status") or "").lower() == "rejected":
        return None

    posted_at = post.get("posted_at") or post.get("collected_at") or run_at
    posted_dt = _parse_iso(posted_at)
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    if posted_dt and posted_dt < cutoff:
        return None

    tweet_id = post.get("tweet_id") or ""
    handle = (post.get("author_handle") or "").lstrip("@")
    url = post.get("url") or (f"https://x.com/{handle}/status/{tweet_id}" if handle and tweet_id else "")
    title = truncate(text.replace("\n", " "), 140)

    pm = post.get("public_metrics") or {}
    metrics = {
        "likes":       pm.get("likes") or 0,
        "retweets":    pm.get("reposts") or 0,
        "replies":     pm.get("replies") or 0,
        "quotes":      pm.get("quotes") or 0,
        "impressions": pm.get("views") or 0,
        "engagement":  _engagement(pm),
    }

    keywords = list(dict.fromkeys(
        (post.get("matched_keywords") or [])
        + (post.get("opportunity_tags") or [])
    ))[:12]

    score = _opportunity_score(post)
    return {
        "id":                  f"manual_x:{tweet_id}" if tweet_id else f"manual_x:{abs(hash(text)) & 0xffffffff}",
        "source_id":           "manual_x",
        "source_name":         f"X · @{handle}" if handle else "X",
        "source_kind":         "social",
        "source_url":          url,
        "external_id":         tweet_id,
        "title":               title,
        "text":                text,
        "posted_at":           posted_at,
        "collected_at":        post.get("collected_at") or run_at,
        "matched_keywords":    keywords,
        "signal_type":         _signal_type(text, float(post.get("pain_signal_score") or 0)),
        "opportunity_score":   score,
        "metrics":             metrics,
        "verification_status": post.get("verification_status") or "manual_curated",
        # Custom fields the radar UI uses for the manual-X treatment:
        "manual":              True,
        "author_handle":       f"@{handle}" if handle else "",
        "pain_signal_score":   float(post.get("pain_signal_score") or 0),
        "lang":                post.get("lang") or "",
    }


class ManualXBridge(Agent):
    name = "manual_x_bridge"
    description = "يقرأ التغريدات الملتقطة يدويًا ويُدخلها في الـ pipeline قبل EvidenceGuard."
    inputs = ["data/manual_x/posts.json"]
    outputs = ["ctx.state.raw_items (augmented)"]

    def run(self, ctx: AgentContext) -> AgentResult:
        raw_doc = read_json(MANUAL_X_PATH, {"items": []})
        posts = raw_doc.get("items") or raw_doc.get("posts") or []
        run_at = ctx.state.get("run_at") or now_iso()

        normalized = []
        skipped = 0
        for post in posts:
            n = _normalize(post, run_at)
            if n is None:
                skipped += 1
                continue
            normalized.append(n)

        if not normalized:
            return AgentResult(
                name=self.name,
                ok=True,
                duration_s=0.0,
                notes=[f"no manual X items eligible (skipped {skipped} of {len(posts)})"],
            )

        # Append into ctx.state.raw_items so the rest of the pipeline
        # (EvidenceGuard → PriorityRanker → Events → Opps → Editor) treats
        # them as regular signals. Manual items go first so they appear
        # earlier in the dock when priorities tie.
        existing = ctx.state.get("raw_items") or []
        ctx.state["raw_items"] = normalized + existing

        # Also expose them as a stand-alone list for any agent that wants
        # the manual subset (we don't use this today, but it's cheap).
        ctx.state["manual_x_items"] = normalized

        avg_score = round(sum(it["opportunity_score"] for it in normalized) / len(normalized), 3)
        return AgentResult(
            name=self.name,
            ok=True,
            duration_s=0.0,
            notes=[
                f"injected {len(normalized)} manual X items "
                f"(skipped {skipped} of {len(posts)}, avg score {avg_score})"
            ],
        )
