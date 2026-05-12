#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "js" / "radar-inline-data.js"

DATA_FILES = [
    "data/radar/signals.json",
    "data/radar/signals_corpus.json",
    "data/radar/radar_card_candidates.json",
    "data/radar/card_validation_report.json",
    "data/radar/review_queue_summary.json",
    "data/radar/focused_opportunities.json",
    "data/radar/focused_updates.json",
    "data/radar/focused_discussions.json",
    "data/radar/openai_intelligence_cards.json",
    "data/radar/model_timeline.json",
    "data/radar/opportunities.json",
    "data/radar/product_playbooks.json",
    "data/radar/product_playbooks_dynamic.json",
    "data/radar/research_opportunities.json",
    "data/radar/global_sources.json",
    "data/radar/run_status.json",
    "data/manual_x/curated_opportunities.json",
    "data/manual_x/x_brief.json",
    "data/manual_x/radar_ready_posts.json",
    "data/manual_x/x_radar_cards.json",
    "data/radar/x_focus_accounts.json",
]


def main():
    payload = {}
    missing = []
    for rel in DATA_FILES:
        path = ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        payload[rel] = json.loads(path.read_text(encoding="utf-8"))

    OUTPUT.write_text(
        "window.RADAR_INLINE_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(OUTPUT.relative_to(ROOT)),
        "files_embedded": len(payload),
        "missing": missing,
        "size_kb": round(OUTPUT.stat().st_size / 1024, 1),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
