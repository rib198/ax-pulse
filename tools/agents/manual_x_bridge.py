"""Agent — Manual X Bridge.

Reads manually captured X posts from data/manual_x/posts.json and injects
them into ctx.state["raw_items"] before EvidenceGuard. Downstream agents then
rank, cluster, and cite those posts like any other signal while the frontend
can still identify them through the manual/authorship fields.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

from .base import Agent, AgentContext, AgentResult, DATA_DIR, now_iso, read_json, truncate


POSTS_FILE = DATA_DIR / "manual_x" / "posts.json"
MAX_AGE_DAYS = 30
MIN_TEXT_LEN = 20

PAIN_RE = re.compile(
    r"\b(broken|bug|hate|wish|need|frustrat|slow|expensive|impossible|problem|"
    r"missing|fail|painful|مشكلة|صعب|بطيء|غالي|أحتاج|احتاج|أتمنى)\b",
    re.IGNORECASE,
)
LAUNCH_RE = re.compile(
    r"\b(launch|released|announce|introduc|ship|available now|إطلاق|أعلنت|متاح|أصدر)\b",
    re.IGNORECASE,
)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _metrics(raw: dict | None) -> dict:
    raw = raw or {}
    likes = int(raw.get("likes") or 0)
    reposts = int(raw.get("reposts") or raw.get("retweets") or 0)
    replies = int(raw.get("replies") or 0)
    quotes = int(raw.get("quotes") or 0)
    views = int(raw.get("views") or raw.get("impressions") or 0)
    return {
        "likes": likes,
        "retweets": reposts,
        "reposts": reposts,
        "replies": replies,
        "quotes": quotes,
        "impressions": views,
        "engagement": likes + reposts * 3 + replies * 2 + quotes * 2,
    }


def _signal_type(text: str, pain_score: float) -> str:
    if pain_score >= 0.5 or PAIN_RE.search(text):
        return "pain"
    if LAUNCH_RE.search(text):
        return "launch"
    return "news"


def _score(post: dict, metrics: dict) -> float:
    pain = float(post.get("pain_signal_score") or 0)
    engagement_boost = min(0.35, metrics.get("engagement", 0) / 1000)
    tag_boost = min(0.15, 0.05 * len(post.get("opportunity_tags") or []))
    keyword_boost = min(0.10, 0.03 * len(post.get("matched_keywords") or []))
    text = post.get("text") or ""
    pain_floor = 0.18 if PAIN_RE.search(text) else 0
    return round(min(1.0, max(pain, pain_floor) + engagement_boost + tag_boost + keyword_boost), 3)


def _normalize(post: dict, run_at: str) -> dict | None:
    text = (post.get("text") or "").strip()
    if len(text) < MIN_TEXT_LEN:
        return None
    if (post.get("verification_status") or "").lower() == "rejected":
        return None

    posted_at = post.get("posted_at") or post.get("collected_at") or run_at
    posted_dt = _parse_iso(posted_at)
    if posted_dt and posted_dt < datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS):
        return None

    tweet_id = str(post.get("tweet_id") or "").strip()
    handle = str(post.get("author_handle") or "").lstrip("@").strip()
    url = post.get("url") or (f"https://x.com/{handle}/status/{tweet_id}" if handle and tweet_id else "")
    metrics = _metrics(post.get("public_metrics"))
    score = _score(post, metrics)
    fallback_id = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]

    keywords = list(dict.fromkeys((post.get("matched_keywords") or []) + (post.get("opportunity_tags") or [])))[:12]
    pain_score = float(post.get("pain_signal_score") or 0)

    return {
        "id": f"manual_x:{tweet_id or fallback_id}",
        "source_id": "manual_x",
        "source_name": f"X · @{handle}" if handle else "X",
        "source_kind": "social",
        "source_url": url,
        "url": url,
        "external_id": tweet_id,
        "title": truncate(text.replace("\n", " "), 140),
        "text": text,
        "posted_at": posted_at,
        "collected_at": post.get("collected_at") or run_at,
        "matched_keywords": keywords,
        "signal_type": _signal_type(text, pain_score),
        "opportunity_score": score,
        "metrics": metrics,
        "verification_status": post.get("verification_status") or "manual_curated",
        "manual": True,
        "author_handle": f"@{handle}" if handle else "",
        "pain_signal_score": pain_score,
        "lang": post.get("lang") or "",
    }


class ManualXBridge(Agent):
    name = "manual_x_bridge"
    description = "يدخل تغريدات X الملتقطة يدويًا في خط الرادار قبل EvidenceGuard."
    inputs = ["data/manual_x/posts.json"]
    outputs = ["ctx.state.raw_items"]

    def run(self, ctx: AgentContext) -> AgentResult:
        doc = read_json(POSTS_FILE, {"items": []})
        posts = doc.get("items") or doc.get("posts") or []
        run_at = ctx.state.get("run_at") or now_iso()

        injected = []
        skipped = 0
        seen = {item.get("id") for item in (ctx.state.get("raw_items") or [])}
        for post in posts:
            item = _normalize(post, run_at)
            if not item or item["id"] in seen:
                skipped += 1
                continue
            injected.append(item)
            seen.add(item["id"])

        if injected:
            ctx.state["raw_items"] = injected + (ctx.state.get("raw_items") or [])
            ctx.state["manual_x_items"] = injected

        return AgentResult(
            name=self.name,
            ok=True,
            duration_s=0.0,
            notes=[f"injected {len(injected)} manual X items (skipped {skipped} of {len(posts)})"],
        )
