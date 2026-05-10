"""Agent 13 — Memory & Learning (الذاكرة والتعلّم).

Closes the feedback loop. Reads the rolling history of:
- which signals reappeared across runs (proven recurring topics → high signal)
- which sources kept producing reliable items vs flaky ones (per-source EWMA reliability)
- which model families dominate the conversation week-over-week
- past UX QA outcomes (pages that broke before deserve extra weight)

Then emits two things future runs consume:
1. ctx.state["learned_weights"] — feeds Priority Ranker so it adapts over time
2. data/radar/agents/learnings.json — narrative + numbers other agents can read

This is the only agent that reads its OWN previous output to evolve.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    read_json,
    write_json,
)


def _ewma(prev: float, sample: float, alpha: float = 0.3) -> float:
    return round(alpha * sample + (1 - alpha) * prev, 4)


class MemoryLearning(Agent):
    name = "memory_learning"
    description = "يتعلّم من تاريخ التشغيلات: موثوقية المصادر، تكرار المواضيع، أداء الواجهات. يضبط أوزان الترتيب."
    inputs = ["ctx.state.tagged_items", "data/radar/agents/performance.json", "data/radar/agents/qa_report.json"]
    outputs = ["data/radar/agents/learnings.json", "ctx.state.learned_weights"]

    def run(self, ctx: AgentContext) -> AgentResult:
        run_at = ctx.state.get("run_at") or now_iso()
        items = ctx.state.get("tagged_items") or []
        path = RADAR_DIR / "agents" / "learnings.json"
        prev = read_json(path, {})

        # 1) per-source reliability: trust_tier ratio of items that survived ranking
        source_reliability: dict[str, float] = dict(prev.get("source_reliability") or {})
        run_reliability: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # ok / total
        for it in items:
            sid = it.get("source_id") or "unknown"
            run_reliability[sid][1] += 1
            if (it.get("trust_score") or 0) >= 0.5 and (it.get("priority") or 0) >= 0.4:
                run_reliability[sid][0] += 1
        for sid, (ok, total) in run_reliability.items():
            sample = ok / total if total else 0.0
            source_reliability[sid] = _ewma(source_reliability.get(sid, sample), sample)

        # 2) recurring topics: track tags / model families across runs
        family_counts = Counter()
        prev_families: dict[str, int] = dict(prev.get("family_counts") or {})
        for ev in (ctx.state.get("model_events") or []):
            family_counts[ev["family"]] += 1
        for fam, c in family_counts.items():
            prev_families[fam] = prev_families.get(fam, 0) + c

        # 3) qa health trend: count of issues over last N runs
        qa = ctx.state.get("qa_report") or {}
        qa_history = list(prev.get("qa_history") or [])
        qa_history.append({"run_at": run_at, "issues": qa.get("issue_count", 0)})
        qa_history = qa_history[-30:]

        # 4) tune ranker weights — modest adjustments based on what's working
        weights = {"recency": 0.18, "trust": 0.22, "impact": 0.22, "buildability": 0.18, "income": 0.20}
        opps_doc = read_json(RADAR_DIR / "opportunities.json", {}) or {}
        opps = opps_doc.get("opportunities") or []
        # if many opportunities are showing up → income axis is yielding, keep it.
        # if few opportunities → bump buildability and income to surface more actionable items.
        if len(opps) <= 2:
            weights["buildability"] += 0.03
            weights["income"] += 0.03
            weights["recency"] -= 0.03
            weights["impact"] -= 0.03
        # if QA found issues → trust axis matters more next run
        if qa.get("issue_count", 0) >= 5:
            weights["trust"] += 0.04
            weights["impact"] -= 0.02
            weights["recency"] -= 0.02
        # normalize
        s = sum(weights.values())
        weights = {k: round(v / s, 4) for k, v in weights.items()}

        ctx.state["learned_weights"] = weights

        out = {
            "generated_at": run_at,
            "note_ar": "ذاكرة الرادار: ما المصادر التي تثبت موثوقيتها، أي عائلات نماذج تتصدّر، وكيف تعدّل أوزان الترتيب.",
            "learned_weights": weights,
            "source_reliability": source_reliability,
            "family_counts": prev_families,
            "qa_history": qa_history,
            "top_reliable_sources": sorted(source_reliability.items(), key=lambda x: x[1], reverse=True)[:10],
            "weakest_sources": sorted(source_reliability.items(), key=lambda x: x[1])[:5],
        }
        write_json(path, out)

        notes = [
            f"tracked {len(source_reliability)} sources",
            f"weights: " + ", ".join(f"{k}={v}" for k, v in weights.items()),
        ]
        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=notes)
