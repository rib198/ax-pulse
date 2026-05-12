"""Agent — Access Tier Tagger.

Adds the content-access metadata the frontend uses to gate paid content:
  - tier: "free" | "premium"
  - status: "published" | "archived"
  - is_featured: bool
  - is_new: bool
  - version: int
  - publishedAt / updatedAt (ISO)
  - sortOrder: number

Rules (kept simple, deterministic, deletable later):
  - Top N opportunities (highest confidence) → free preview.
  - Everything else → premium.
  - Top signals: free_preview_count from config → free; rest → premium.
  - is_new: published within `show_new_badge_days` days.
  - is_featured: confidence ≥ 0.7 OR is the #1 opportunity.

This agent NEVER deletes anything and NEVER changes existing items in place
beyond adding/updating the tier fields. Old items keep their place.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DATA_DIR,
    RADAR_DIR,
    now_iso,
    read_json,
    write_json,
)


def _config() -> dict:
    return read_json(DATA_DIR / "config.json", {}) or {}


def _within_days(ts: str, days: int) -> bool:
    if not ts:
        return False
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    return datetime.now(timezone.utc) - d <= timedelta(days=days)


def _tag_opportunities(opps: list[dict], free_count: int, new_days: int, run_at: str) -> list[dict]:
    sorted_opps = sorted(opps, key=lambda o: o.get("confidence", 0), reverse=True)
    out = []
    for i, o in enumerate(sorted_opps):
        tier = "free" if i < free_count else "premium"
        is_featured = bool(i == 0 or (o.get("confidence") or 0) >= 0.70)
        is_new = _within_days(o.get("generated_at") or run_at, new_days)
        existing_status = o.get("status") or "published"
        existing_version = int(o.get("version") or 1)
        out.append({
            **o,
            "tier": o.get("tier") or tier,
            "status": existing_status,
            "is_featured": o.get("is_featured", is_featured),
            "is_new": is_new,
            "version": existing_version,
            "publishedAt": o.get("publishedAt") or run_at,
            "updatedAt": run_at,
            "sortOrder": o.get("sortOrder", i),
        })
    return out


def _tag_signals(items: list[dict], free_count: int, new_days: int, run_at: str) -> list[dict]:
    sorted_items = sorted(items, key=lambda x: x.get("priority") or x.get("opportunity_score") or 0, reverse=True)
    out = []
    for i, it in enumerate(sorted_items):
        tier = "free" if i < free_count else "premium"
        is_new = _within_days(it.get("posted_at") or it.get("collected_at") or run_at, new_days)
        out.append({
            **it,
            "tier": it.get("tier") or tier,
            "status": it.get("status") or "published",
            "is_featured": it.get("is_featured", False),
            "is_new": is_new,
            "version": int(it.get("version") or 1),
            "publishedAt": it.get("publishedAt") or it.get("posted_at") or run_at,
            "updatedAt": run_at,
            "sortOrder": it.get("sortOrder", i),
        })
    return out


class AccessTier(Agent):
    name = "access_tier"
    description = "يصنّف الفرص والإشارات إلى مجاني/مشترك ويضيف شارات جديد/مميز/منشور."
    inputs = ["data/radar/opportunities.json", "data/radar/signals.json", "data/config.json"]
    outputs = ["data/radar/opportunities.json", "data/radar/signals.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        cfg = _config()
        sub_cfg = cfg.get("subscription", {}) or {}
        feat_cfg = cfg.get("features", {}) or {}
        free_opps = int(sub_cfg.get("free_preview_count") or 3)
        free_signals = max(6, free_opps * 2)
        new_days = int(feat_cfg.get("show_new_badge_days") or 3)
        run_at = ctx.state.get("run_at") or now_iso()

        notes: list[str] = []

        # Opportunities
        opps_doc = read_json(RADAR_DIR / "opportunities.json", {}) or {}
        opps = opps_doc.get("opportunities") or []
        if opps:
            tagged_opps = _tag_opportunities(opps, free_opps, new_days, run_at)
            opps_doc["opportunities"] = tagged_opps
            opps_doc["tiered_at"] = run_at
            opps_doc["free_preview_count"] = free_opps
            write_json(RADAR_DIR / "opportunities.json", opps_doc)
            notes.append(f"opps: {sum(1 for o in tagged_opps if o['tier']=='free')} free / {sum(1 for o in tagged_opps if o['tier']=='premium')} premium")

        # Signals
        sig_doc = read_json(RADAR_DIR / "signals.json", {}) or {}
        items = sig_doc.get("items") or []
        if items:
            tagged_items = _tag_signals(items, free_signals, new_days, run_at)
            sig_doc["items"] = tagged_items
            sig_doc["tiered_at"] = run_at
            sig_doc["free_preview_count"] = free_signals
            write_json(RADAR_DIR / "signals.json", sig_doc)
            notes.append(f"signals: {sum(1 for s in tagged_items if s['tier']=='free')} free / {sum(1 for s in tagged_items if s['tier']=='premium')} premium")

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/opportunities.json", "data/radar/signals.json"], notes=notes)
