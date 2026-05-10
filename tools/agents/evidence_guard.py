"""Agent 5 — حارس المصادر (Evidence Guard).

Tags each signal with a trust tier so downstream agents can weight them
honestly. Pure rules — fast, free, deterministic. Replaces the implicit
"all sources weighted equally" behavior in pulse_radar.
"""
from __future__ import annotations

from .base import Agent, AgentContext, AgentResult, RADAR_DIR, write_json


# trust tier → numeric weight used by the ranker
TIER_WEIGHTS = {
    "official": 1.00,      # company blogs, model hubs
    "research": 0.85,      # arxiv, HF papers
    "press": 0.70,         # tech press
    "community": 0.55,     # HN, GitHub, Reddit, newsletters
    "social": 0.35,        # X
    "unknown": 0.25,
}

OFFICIAL_KINDS = {"official", "model_hub"}
RESEARCH_KINDS = {"scientific_paper"}
PRESS_KINDS = {"newsletter"}      # techcrunch_ai is tagged as newsletter in pulse_radar
COMMUNITY_KINDS = {"community", "code_repo"}
SOCIAL_KINDS = {"social"}

# explicit overrides for sources whose kind is generic but identity matters
SOURCE_OVERRIDES = {
    "openai_news": "official",
    "anthropic": "official",
    "google_deepmind": "official",
    "google_ai_blog": "official",
    "huggingface_blog": "official",
    "huggingface_daily_papers": "research",
    "huggingface_models": "official",
    "techcrunch_ai": "press",
    "bens_bites": "press",
    "hn_algolia": "community",
    "github_repos": "community",
    "x_recent_search": "social",
}


def classify(item: dict) -> str:
    sid = item.get("source_id") or ""
    if sid in SOURCE_OVERRIDES:
        return SOURCE_OVERRIDES[sid]
    kind = item.get("source_kind") or ""
    if kind in OFFICIAL_KINDS:
        return "official"
    if kind in RESEARCH_KINDS:
        return "research"
    if kind in PRESS_KINDS:
        return "press"
    if kind in SOCIAL_KINDS:
        return "social"
    if kind in COMMUNITY_KINDS:
        return "community"
    return "unknown"


def freshness_factor(item: dict, run_at: str) -> float:
    """1.0 for items seen this run, decays gently for older items.
    Uses seen_count from corpus when available — repeated mentions raise trust."""
    seen = item.get("seen_count") or 1
    boost = min(0.10, 0.02 * (seen - 1))
    last = item.get("last_seen_at") or item.get("collected_at") or run_at
    same_day = last[:10] == run_at[:10] if last and run_at else False
    base = 1.0 if same_day else 0.85
    return min(1.0, base + boost)


class EvidenceGuard(Agent):
    name = "evidence_guard"
    description = "يصنّف كل إشارة حسب موثوقية المصدر (official/research/press/community/social) ويحسب وزن الثقة."
    inputs = ["ctx.state.raw_items"]
    outputs = ["ctx.state.tagged_items", "data/radar/agents/evidence_report.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("raw_items") or []
        run_at = ctx.state.get("run_at") or ""
        tier_counts: dict[str, int] = {}
        tagged: list[dict] = []
        for item in items:
            tier = classify(item)
            weight = TIER_WEIGHTS[tier]
            fresh = freshness_factor(item, run_at)
            trust = round(min(1.0, weight * fresh), 3)
            tagged.append({**item, "trust_tier": tier, "trust_weight": weight, "freshness": round(fresh, 3), "trust_score": trust})
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        ctx.state["tagged_items"] = tagged

        report = {
            "generated_at": run_at,
            "total": len(tagged),
            "tier_counts": tier_counts,
            "tier_weights": TIER_WEIGHTS,
            "note_ar": "كل إشارة تأخذ درجة ثقة (trust_score) = وزن المصدر × الحداثة. تستخدمها بقية الوكلاء في الترتيب وبناء الفرص.",
        }
        path = RADAR_DIR / "agents" / "evidence_report.json"
        write_json(path, report)

        notes = [f"tagged {len(tagged)} items"]
        if tier_counts:
            notes.append("by tier: " + ", ".join(f"{k}={v}" for k, v in sorted(tier_counts.items(), key=lambda x: -x[1])))

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=notes)
