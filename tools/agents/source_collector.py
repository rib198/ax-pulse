"""Agent 1 — Source Collector (كاشف الإشارات).

Wraps the existing fetch logic in `tools/pulse_radar.py` so we don't
duplicate hundreds of lines of source-specific code. Produces the same
`data/radar/raw_items.json` and stores items in ctx.state for downstream agents.
"""
from __future__ import annotations

import argparse
import time

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    write_json,
)


class SourceCollector(Agent):
    name = "source_collector"
    description = "يجمع الإشارات من جميع المصادر الرسمية والعامة (RSS/arXiv/HF/HN/GitHub/Reddit/Feedly/X)."
    outputs = ["data/radar/raw_items.json", "ctx.state.raw_items"]

    def __init__(self, limit: int = 25, x_limit: int = 25, x_queries: list[str] | None = None):
        self.limit = limit
        self.x_limit = x_limit
        self.x_queries = x_queries or [None]

    def run(self, ctx: AgentContext) -> AgentResult:
        from tools import pulse_radar as pr  # type: ignore

        notes: list[str] = []
        errors: list[dict] = []
        items: list[dict] = []

        # Source isolation principle: every fetch is wrapped in try/except so
        # one source raising (network blip, malformed payload, 429 rate-limit,
        # unexpected DNS) NEVER kills the rest of the collection. Each loss
        # is recorded in `errors` for run_status.json without affecting the
        # rest of the radar.

        for source in pr.RSS_SOURCES:
            try:
                got, err = pr.fetch_rss_source(source, limit=self.limit)
                items.extend(got)
                if err:
                    errors.append(err)
            except Exception as exc:
                errors.append({"source": source.get("id", "rss_unknown"), "error": str(exc)})
            time.sleep(0.2)

        # arXiv enforces an aggressive rate limit (HTTP 429). One backoff retry
        # per query gives transient throttles a second chance; persistent
        # failures still drop through cleanly.
        for source in pr.ARXIV_QUERIES:
            for attempt in (0, 1):
                try:
                    items.extend(pr.fetch_arxiv_query(source, limit=min(self.limit, 15)))
                    break
                except Exception as exc:
                    if attempt == 0 and "429" in str(exc):
                        time.sleep(3.0)
                        continue
                    errors.append({"source": source["id"], "error": str(exc)})
                    break
            time.sleep(0.6)

        for fn, src in [
            (pr.fetch_huggingface_daily_papers, "huggingface_daily_papers"),
            (pr.fetch_huggingface_models, "huggingface_models"),
        ]:
            try:
                items.extend(fn(limit=min(self.limit, 20)))
            except Exception as exc:
                errors.append({"source": src, "error": str(exc)})

        try:
            got, err = pr.fetch_feedly(limit=self.limit)
            items.extend(got)
            if err:
                errors.append(err)
        except Exception as exc:
            errors.append({"source": "feedly", "error": str(exc)})

        for q in self.x_queries:
            try:
                got, err = pr.fetch_x_recent_search(limit=self.x_limit, query=q)
                items.extend(got)
                if err:
                    errors.append(err)
            except Exception as exc:
                errors.append({"source": "x_recent_search", "error": str(exc)})
            time.sleep(0.2)

        for source in pr.REDDIT_SOURCES:
            try:
                items.extend(pr.fetch_reddit_source(source))
            except Exception as exc:
                errors.append({"source": source["id"], "error": str(exc)})
            time.sleep(0.2)

        for fn, src in [(pr.fetch_hn, "hn_algolia"), (pr.fetch_github, "github_repos")]:
            try:
                items.extend(fn(limit=min(self.limit, 30)))
            except Exception as exc:
                errors.append({"source": src, "error": str(exc)})

        items = [it for it in pr.dedupe(items) if pr.is_ai_news_update_signal(it)]

        run_at = now_iso()
        raw = {"generated_at": run_at, "count": len(items), "errors": errors, "items": items}
        write_json(RADAR_DIR / "raw_items.json", raw)

        ctx.state["raw_items"] = items
        ctx.state["raw_errors"] = errors
        ctx.state["run_at"] = run_at

        notes.append(f"collected {len(items)} signals from {len(pr.RSS_SOURCES) + len(pr.ARXIV_QUERIES) + len(pr.REDDIT_SOURCES) + 4} source families")
        if errors:
            notes.append(f"{len(errors)} source errors (non-fatal)")

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/raw_items.json"], notes=notes)
