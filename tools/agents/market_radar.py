"""Agent 4 — رادار السوق (Market Radar).

Filters the global signal stream for Saudi / Arab market relevance.
Detects: Arabic-language signals, GCC/MENA references, Arabic-named tools/apps,
Vision 2030 keywords, halal/finance/government themes that fit local audience.
"""
from __future__ import annotations

import re

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    truncate,
    write_json,
)


ARAB_GEO = [
    "saudi", "ksa", "uae", "emirates", "dubai", "abu dhabi", "qatar", "doha",
    "kuwait", "bahrain", "oman", "egypt", "jordan", "morocco", "tunisia",
    "السعودية", "الإمارات", "دبي", "أبوظبي", "قطر", "الكويت", "البحرين", "مصر", "الأردن", "المغرب",
    "الرياض", "جدة", "الدمام", "خليج",
]

ARAB_THEMES = [
    "vision 2030", "neom", "pif", "stc", "saudi aramco", "noon", "tabby", "tamara", "careem",
    "رؤية 2030", "نيوم", "الرياض", "صندوق الاستثمارات", "أرامكو",
    "halal", "حلال", "زكاة", "ريال", "درهم",
]

ARABIC_RE = re.compile(r"[؀-ۿ]")


def _is_arab_relevant(item: dict) -> tuple[bool, list[str]]:
    text = ((item.get("title") or "") + " " + (item.get("text") or "")).lower()
    hits: list[str] = []
    for w in ARAB_GEO:
        if w in text:
            hits.append(w)
    for w in ARAB_THEMES:
        if w in text:
            hits.append(w)
    if ARABIC_RE.search(item.get("title") or "") or ARABIC_RE.search(item.get("text") or ""):
        hits.append("arabic_text")
    return (len(hits) > 0, hits[:8])


class MarketRadar(Agent):
    name = "market_radar"
    description = "يفلتر الإشارات لما يخدم السوق السعودي/العربي ويحفظ قائمة فرص محلية."
    inputs = ["ctx.state.ranked_items"]
    outputs = ["data/radar/agents/market_focus.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("ranked_items") or ctx.state.get("tagged_items") or []
        run_at = ctx.state.get("run_at") or now_iso()

        focused = []
        for it in items:
            ok, hits = _is_arab_relevant(it)
            if not ok:
                continue
            focused.append({
                "id": it.get("id"),
                "title": truncate(it.get("title") or "", 160),
                "source_id": it.get("source_id"),
                "source_url": it.get("source_url"),
                "trust_tier": it.get("trust_tier"),
                "priority": it.get("priority"),
                "matched": hits,
            })
        focused.sort(key=lambda x: x.get("priority") or 0, reverse=True)
        focused = focused[:40]

        out = {
            "generated_at": run_at,
            "note_ar": "إشارات وفرص ذات علاقة مباشرة بالسوق السعودي/العربي.",
            "count": len(focused),
            "items": focused,
        }
        path = RADAR_DIR / "agents" / "market_focus.json"
        write_json(path, out)
        ctx.state["market_items"] = focused

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=[f"{len(focused)} arab-market items"])
