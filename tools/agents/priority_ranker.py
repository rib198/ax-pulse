"""Agent 6 — ترتيب الأولويات (Priority Ranker).

Combines five axes per signal: recency, trust, impact, buildability, income potential.
Pure rules — no OpenAI cost. Memory & Learning agent (agent 13) tunes the weights
over time via ctx.state["learned_weights"].
"""
from __future__ import annotations

from datetime import datetime, timezone

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    safe_get,
    write_json,
)

# Recency weighted highest — surface NEW signals first. Pre-fix the recency
# axis was inversely correlated with newness (rewarded `seen_count`), so old
# repeated items dominated the feed. Now: weight 0.30 + time-decay scoring.
DEFAULT_WEIGHTS = {
    "recency": 0.30,
    "trust": 0.20,
    "impact": 0.20,
    "buildability": 0.15,
    "income": 0.15,
}

BUILDABLE_HINTS = ["api", "open source", "open-source", "github", "sdk", "template", "starter", "framework", "boilerplate", "tutorial", "guide", "playbook", "mcp", "tool", "أداة", "قالب", "إطار"]
INCOME_HINTS = ["pricing", "subscribe", "saas", "service", "agency", "client", "freelance", "monetize", "paid", "revenue", "اشتراك", "خدمة", "وكالة", "عميل", "ربح", "تسعير"]
HIGH_IMPACT_HINTS = ["release", "launch", "announce", "introduce", "ships", "available", "إطلاق", "أعلنت", "متاح"]


def _hits(text: str, words: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for w in words if w in t)


def _recency(item: dict) -> float:
    """Time-decay score in [0.0, 1.0]. Newer = closer to 1.

    Uses first_seen_at when available (when our pipeline first encountered the
    signal), else falls back to posted_at, else collected_at. Unknown dates
    score 0.45 — slightly below the 1-day mark so dateless items don't crowd
    out properly-dated fresh signals."""
    iso = (
        item.get("first_seen_at")
        or item.get("posted_at")
        or item.get("collected_at")
        or ""
    )
    if not iso:
        return 0.45
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0.45
    age_hours = (datetime.now(timezone.utc) - t).total_seconds() / 3600
    if age_hours <= 6:     return 1.00   # last 6h — front-page priority
    if age_hours <= 24:    return 0.85   # today
    if age_hours <= 72:    return 0.65   # last 3 days
    if age_hours <= 168:   return 0.40   # last week
    if age_hours <= 336:   return 0.20   # last 2 weeks
    if age_hours <= 720:   return 0.10   # last month
    return 0.03                          # older — barely surfaces


def _score_axes(item: dict) -> dict[str, float]:
    text = ((item.get("title") or "") + " " + (item.get("text") or "")).lower()
    metrics = item.get("metrics") or {}
    seen = item.get("seen_count") or 1

    recency = _recency(item)
    # Small corroboration bonus folded into trust: signals seen multiple times
    # across the corpus get a tiny credibility boost (caps at +0.15).
    trust = min(1.0, float(item.get("trust_score") or 0.5) + min(0.15, 0.025 * (seen - 1)))

    impact_signals = [
        _hits(text, HIGH_IMPACT_HINTS) * 0.15,
        min(0.30, (metrics.get("stars") or 0) / 1500),
        min(0.25, (metrics.get("score") or 0) / 200),  # HN
        min(0.25, (metrics.get("upvotes") or 0) / 200),  # Reddit
        min(0.30, (metrics.get("impressions") or 0) / 5000),
        min(0.25, (metrics.get("engagement") or 0) / 200),
    ]
    impact = min(1.0, sum(impact_signals))

    buildability = min(1.0, 0.20 + 0.12 * _hits(text, BUILDABLE_HINTS))
    income = min(1.0, 0.15 + 0.14 * _hits(text, INCOME_HINTS))

    return {
        "recency": round(recency, 3),
        "trust": round(trust, 3),
        "impact": round(impact, 3),
        "buildability": round(buildability, 3),
        "income": round(income, 3),
    }


class PriorityRanker(Agent):
    name = "priority_ranker"
    description = "يرتّب الإشارات على خمسة محاور: الحداثة، الثقة، الأثر، قابلية البناء، احتمال الدخل."
    inputs = ["ctx.state.tagged_items"]
    outputs = ["data/radar/signals.json", "ctx.state.ranked_items"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("tagged_items") or ctx.state.get("raw_items") or []
        weights = ctx.state.get("learned_weights") or DEFAULT_WEIGHTS
        run_at = ctx.state.get("run_at") or ""

        scored: list[dict] = []
        for it in items:
            axes = _score_axes(it)
            priority = sum(axes[k] * weights.get(k, DEFAULT_WEIGHTS[k]) for k in DEFAULT_WEIGHTS)
            scored.append({**it, "axes": axes, "priority": round(priority, 4)})

        scored.sort(key=lambda x: x["priority"], reverse=True)
        top = scored[:120]

        ctx.state["ranked_items"] = scored

        # signals.json schema must match what radar.html / dashboard.html / build_digest.py expect
        prev = safe_get(ctx.state, "prev_signals", default={}) or {}
        out = {
            "generated_at": run_at,
            "count": len(top),
            "corpus_count": prev.get("corpus_count") or len(scored),
            "history_snapshot": prev.get("history_snapshot", ""),
            "note_ar": "إشارات مرتبة بالأولوية (حداثة + ثقة + أثر + قابلية بناء + دخل). الإشارات القديمة تبقى في signals_corpus.json.",
            "weights": weights,
            "items": top,
        }
        write_json(RADAR_DIR / "signals.json", out)

        notes = [f"ranked {len(scored)} items, top priority={top[0]['priority'] if top else 0:.3f}"]
        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/signals.json"], notes=notes)
