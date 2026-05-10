#!/usr/bin/env python3
"""Entry point for the AX Pulse Radar agent pipeline.

Replaces the monolithic `pulse_radar.py` flow with a 13-agent system.
Backward compatible — writes the same `data/radar/*.json` files the
existing HTML pages and `build_digest.py` already consume.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow `from tools import pulse_radar` and `from tools.agents...`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.agents.base import AgentContext, OPENAI_BUDGET_ITEMS, now_iso
from tools.agents.orchestrator import Orchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AX Pulse Radar agent pipeline.")
    parser.add_argument("--limit", type=int, default=25, help="Items per source (default 25).")
    parser.add_argument("--x-limit", type=int, default=25, help="X items per query.")
    parser.add_argument("--skip-collect", action="store_true", help="Reuse existing data/radar/raw_items.json — skip network fetch.")
    parser.add_argument("--budget", type=int, default=OPENAI_BUDGET_ITEMS, help="Max OpenAI calls per run.")
    parser.add_argument("--no-openai", action="store_true", help="Force rule-based mode (ignore OPENAI_API_KEY).")
    args = parser.parse_args()

    key = None if args.no_openai else os.environ.get("OPENAI_API_KEY")

    ctx = AgentContext(
        run_at=now_iso(),
        openai_key=key,
        openai_budget=args.budget,
    )

    if args.skip_collect:
        # When skipping collect, we still need raw_items in ctx.state for downstream agents.
        from tools.agents.base import RADAR_DIR, read_json
        raw = read_json(RADAR_DIR / "raw_items.json", {"items": []}).get("items") or []
        ctx.state["raw_items"] = raw

    orch = Orchestrator(skip_collect=args.skip_collect, limit=args.limit, x_limit=args.x_limit)
    log = orch.run(ctx)

    print(f"run_at={log['run_at']} openai_calls={log['openai_calls']}/{log['openai_budget']}")
    for r in log["results"]:
        flag = "✓" if r["ok"] else "✗"
        notes = "; ".join(r["notes"]) if r["notes"] else ""
        line = f"  {flag} {r['agent']:<26} {r['duration_s']:>6.2f}s  {notes}"
        if r.get("error"):
            line += f"  ERROR: {r['error']}"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
