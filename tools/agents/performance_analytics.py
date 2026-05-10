"""Agent 9 — تحليل الأداء (Performance Analytics).

Records radar run metrics so the team and the Memory agent can see what's working:
- corpus growth, signal volume by source, trust distribution
- per-run delta in opportunities and editor stories
- how often each model family gets mentioned

Persisted to data/radar/agents/performance.json with rolling history.
"""
from __future__ import annotations

from collections import Counter

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    read_json,
    write_json,
)


class PerformanceAnalytics(Agent):
    name = "performance_analytics"
    description = "يحسب مقاييس كل تشغيل: نمو القاعدة، توزيع الثقة، عدد الفرص، أكثر العائلات ذكرًا."
    inputs = ["ctx.state.ranked_items", "ctx.state.tagged_items"]
    outputs = ["data/radar/agents/performance.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        run_at = ctx.state.get("run_at") or now_iso()
        items = ctx.state.get("ranked_items") or ctx.state.get("tagged_items") or []
        opps = read_json(RADAR_DIR / "opportunities.json", {}).get("opportunities") or []

        tier_counts = Counter(it.get("trust_tier", "unknown") for it in items)
        source_counts = Counter(it.get("source_id", "unknown") for it in items)
        priority_buckets = Counter()
        for it in items:
            p = it.get("priority") or 0
            if p >= 0.7:
                priority_buckets["high"] += 1
            elif p >= 0.45:
                priority_buckets["mid"] += 1
            else:
                priority_buckets["low"] += 1

        run_record = {
            "run_at": run_at,
            "items_total": len(items),
            "opportunities_total": len(opps),
            "openai_calls": ctx.openai_calls,
            "by_tier": dict(tier_counts),
            "by_priority": dict(priority_buckets),
            "top_sources": source_counts.most_common(8),
        }

        path = RADAR_DIR / "agents" / "performance.json"
        prev = read_json(path, {"runs": []})
        runs = prev.get("runs") or []
        runs.append(run_record)
        runs = runs[-60:]  # rolling 60-run window

        # simple deltas vs previous run
        delta = {}
        if len(runs) >= 2:
            cur, prev_r = runs[-1], runs[-2]
            delta = {
                "items": cur["items_total"] - prev_r["items_total"],
                "opportunities": cur["opportunities_total"] - prev_r["opportunities_total"],
                "openai_calls": cur["openai_calls"] - prev_r["openai_calls"],
            }

        out = {
            "generated_at": run_at,
            "note_ar": "مقاييس تشغيلية لكل دورة رادار. تستخدم في لوحة الأداء وفي ضبط أوزان الترتيب.",
            "latest": run_record,
            "delta_vs_prev": delta,
            "runs": runs,
        }
        write_json(path, out)
        ctx.state["performance"] = out

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=[f"items={run_record['items_total']}, opps={run_record['opportunities_total']}, calls={run_record['openai_calls']}"])
