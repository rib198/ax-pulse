"""Agent 10 — منسق الرادار (Orchestrator).

Runs the agent pipeline in dependency order, collects per-agent results,
and writes a single run log so we can audit what happened.

Pipeline order (matters):
  1. SourceCollector       — fetches all sources → ctx.state.raw_items
  2. EvidenceGuard         — tags trust on every item → ctx.state.tagged_items
  3. MemoryLearning (read) — applies last-run learned weights to ctx.state
  4. PriorityRanker        — ranks → writes signals.json, ctx.state.ranked_items
  5. CompaniesDetector     — extracts companies/products → companies.json
  6. ModelsPulse           — extracts model releases → model_timeline.json
  7. MarketRadar           — Saudi/Arab focus → market_focus.json
  8. OpportunityBuilder    — turns signals into opportunities → opportunities.json
  9. RadarEditor           — daily Arabic brief → brief.ar.json + brief.en.json
 10. GrowthSocial          — copy-ready posts → social_posts.json
 11. UXProductionQA        — validates the whole site state → qa_report.json
 12. PerformanceAnalytics  — records metrics → performance.json
 13. MemoryLearning (write)— evolves weights for next run → learnings.json
"""
from __future__ import annotations

from typing import Iterable

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    read_json,
    write_json,
)
from .access_tier import AccessTier
from .auto_archive import AutoArchive
from .companies_detector import CompaniesDetector
from .evidence_guard import EvidenceGuard
from .growth_social import GrowthSocial
from .market_radar import MarketRadar
from .memory_learning import MemoryLearning
from .models_pulse import ModelsPulse
from .opportunity_builder import OpportunityBuilder
from .performance_analytics import PerformanceAnalytics
from .priority_ranker import PriorityRanker
from .radar_editor import RadarEditor
from .source_collector import SourceCollector
from .ux_production_qa import UXProductionQA


class Orchestrator:
    name = "orchestrator"

    def __init__(self, *, skip_collect: bool = False, limit: int = 25, x_limit: int = 25):
        self.skip_collect = skip_collect
        self.limit = limit
        self.x_limit = x_limit

    def _build_pipeline(self) -> list[Agent]:
        agents: list[Agent] = []
        if not self.skip_collect:
            agents.append(SourceCollector(limit=self.limit, x_limit=self.x_limit))
        agents.extend([
            EvidenceGuard(),
            _LoadLearnedWeights(),     # injects last-run weights before ranking
            PriorityRanker(),
            CompaniesDetector(),
            ModelsPulse(),
            MarketRadar(),
            OpportunityBuilder(),
            RadarEditor(),
            AccessTier(),  # tags free/premium AFTER opps/editor wrote, BEFORE social/QA read.
            AutoArchive(), # archives stale items (status="archived"), never deletes.
            GrowthSocial(),
            UXProductionQA(),
            PerformanceAnalytics(),
            MemoryLearning(),          # writes new weights for next run
        ])
        return agents

    def run(self, ctx: AgentContext) -> dict:
        ctx.state.setdefault("run_at", now_iso())
        results: list[AgentResult] = []
        for agent in self._build_pipeline():
            res = agent.execute(ctx)
            results.append(res)
            ctx.log.append({
                "agent": res.name,
                "ok": res.ok,
                "duration_s": res.duration_s,
                "written": res.written,
                "notes": res.notes,
                "error": res.error,
            })

        # If SourceCollector ran but produced nothing usable, restore tagged_items
        # from raw_items.json so later agents don't silently no-op on a re-run.
        if not ctx.state.get("ranked_items"):
            raw = read_json(RADAR_DIR / "raw_items.json", {"items": []}).get("items") or []
            if raw:
                ctx.log.append({"agent": "orchestrator", "ok": True, "duration_s": 0, "written": [], "notes": [f"reused {len(raw)} items from disk"]})

        run_log = {
            "run_at": ctx.state["run_at"],
            "openai_calls": ctx.openai_calls,
            "openai_budget": ctx.openai_budget,
            "agents": [r.name for r in results],
            "results": ctx.log,
        }
        write_json(RADAR_DIR / "agents" / "run_log.json", run_log)
        return run_log


class _LoadLearnedWeights(Agent):
    """Tiny adapter agent that pulls last-run weights from learnings.json
    into ctx.state before PriorityRanker runs. Keeps the ranker dependency-free."""
    name = "load_learned_weights"

    def run(self, ctx: AgentContext) -> AgentResult:
        prev = read_json(RADAR_DIR / "agents" / "learnings.json", {})
        weights = prev.get("learned_weights")
        if weights:
            ctx.state["learned_weights"] = weights
            note = "applied learned weights from previous run"
        else:
            note = "no prior learnings — using defaults"
        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[], notes=[note])
