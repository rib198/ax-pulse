"""Agent 3 — نبض النماذج (Models Pulse).

Detects model release / update signals and maintains
`data/radar/model_timeline.json` (already used by the existing UI).

We treat any signal that mentions a known model family + a release verb
as a candidate. We keep the most recent N entries per family to avoid drift.
"""
from __future__ import annotations

import re
from collections import defaultdict

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    read_json,
    truncate,
    write_json,
)


MODEL_PATTERNS = {
    "gpt": re.compile(r"\bgpt[\-\s]?(?:4|4o|4\.\d|5|6|o\d)\b", re.I),
    "claude": re.compile(r"\bclaude(?:\s+(?:opus|sonnet|haiku|code|\d))?\b", re.I),
    "gemini": re.compile(r"\bgemini[\-\s]?\d?(?:\.\d+)?\b", re.I),
    "grok": re.compile(r"\bgrok[\-\s]?\d?\b", re.I),
    "llama": re.compile(r"\bllama[\-\s]?\d?(?:\.\d+)?\b", re.I),
    "mistral": re.compile(r"\bmistral|mixtral|codestral\b", re.I),
    "sora": re.compile(r"\bsora\b", re.I),
    "veo": re.compile(r"\bveo[\-\s]?\d?\b", re.I),
    "midjourney": re.compile(r"\bmidjourney\b", re.I),
    "runway": re.compile(r"\brunway|gen[\-\s]?3\b", re.I),
    "stable_diffusion": re.compile(r"\bstable\s+diffusion|sdxl\b", re.I),
    "elevenlabs": re.compile(r"\belevenlabs\b", re.I),
    "deepseek": re.compile(r"\bdeepseek\b", re.I),
    "qwen": re.compile(r"\bqwen\b", re.I),
}

RELEASE_VERBS = re.compile(r"\b(release|released|announce|announces|announcing|introduce|introduces|ships|shipping|launch|launched|available|preview|drops?)\b", re.I)


def _extract(item: dict) -> list[dict]:
    text = (item.get("title") or "") + " " + (item.get("text") or "")
    if not RELEASE_VERBS.search(text):
        return []
    found = []
    for family, pattern in MODEL_PATTERNS.items():
        m = pattern.search(text)
        if m:
            found.append({"family": family, "matched": m.group(0).lower()})
    return found


class ModelsPulse(Agent):
    name = "models_pulse"
    description = "يلتقط إعلانات وإصدارات النماذج (GPT/Claude/Gemini/Grok/Llama/...) ويُحدّث الخط الزمني."
    inputs = ["ctx.state.tagged_items"]
    outputs = ["data/radar/model_timeline.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("tagged_items") or ctx.state.get("ranked_items") or []
        run_at = ctx.state.get("run_at") or now_iso()
        path = RADAR_DIR / "model_timeline.json"
        prev = read_json(path, {"families": {}, "events": []})

        events: list[dict] = list(prev.get("events") or [])
        seen_keys = {(e.get("family"), e.get("source_url")) for e in events}

        new_count = 0
        for it in items:
            for hit in _extract(it):
                key = (hit["family"], it.get("source_url"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                events.append({
                    "family": hit["family"],
                    "matched": hit["matched"],
                    "title": truncate(it.get("title") or "", 160),
                    "source_id": it.get("source_id"),
                    "source_url": it.get("source_url"),
                    "trust_tier": it.get("trust_tier"),
                    "posted_at": it.get("posted_at") or it.get("collected_at"),
                    "detected_at": run_at,
                })
                new_count += 1

        events.sort(key=lambda e: e.get("posted_at") or e.get("detected_at") or "", reverse=True)
        events = events[:300]

        # group latest per family
        latest_by_family: dict[str, dict] = {}
        for e in events:
            fam = e["family"]
            if fam not in latest_by_family:
                latest_by_family[fam] = e

        out = {
            "generated_at": run_at,
            "note_ar": "أحدث إصدارات/إعلانات النماذج بحسب ما رصدته الإشارات. تستخدم في صفحة model timeline.",
            "families": {fam: ev for fam, ev in latest_by_family.items()},
            "events": events,
        }
        write_json(path, out)
        ctx.state["model_events"] = events

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/model_timeline.json"], notes=[f"+{new_count} new model events", f"{len(events)} total"])
