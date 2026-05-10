"""Agent — Auto-Archive.

Sets `status = "archived"` on opportunities and signals that haven't
been updated in a configurable window (default 90 days). Items are
NEVER deleted — archived content stays available to subscribers and
can be unarchived later.

Reads `data/config.json` → `features.auto_archive_days` (default 90).
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


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _archive_old(items: list[dict], cutoff: datetime, run_at: str) -> tuple[list[dict], int]:
    out = []
    archived_count = 0
    for it in items:
        last = _parse_iso(
            it.get("updatedAt") or it.get("last_seen_at") or it.get("collected_at") or it.get("posted_at") or ""
        )
        if last and last < cutoff and (it.get("status") or "published") == "published":
            archived_item = {**it, "status": "archived", "archived_at": run_at}
            out.append(archived_item)
            archived_count += 1
        else:
            out.append(it)
    return out, archived_count


class AutoArchive(Agent):
    name = "auto_archive"
    description = "يؤرشف العناصر التي لم تُحدّث منذ N يوم (افتراضي 90) دون حذف. الأرشيف يبقى متاحاً للمشتركين."
    inputs = ["data/radar/opportunities.json", "data/radar/signals.json"]
    outputs = ["data/radar/opportunities.json", "data/radar/signals.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        cfg = _config()
        feat = cfg.get("features", {}) or {}
        days = int(feat.get("auto_archive_days") or 90)
        run_at = ctx.state.get("run_at") or now_iso()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        notes: list[str] = []

        opps_doc = read_json(RADAR_DIR / "opportunities.json", {}) or {}
        opps = opps_doc.get("opportunities") or []
        if opps:
            new_opps, archived = _archive_old(opps, cutoff, run_at)
            if archived:
                opps_doc["opportunities"] = new_opps
                opps_doc["last_archive_pass"] = run_at
                write_json(RADAR_DIR / "opportunities.json", opps_doc)
            notes.append(f"opportunities: {archived} archived (cutoff = {days}d)")

        sig_doc = read_json(RADAR_DIR / "signals.json", {}) or {}
        items = sig_doc.get("items") or []
        if items:
            new_items, archived = _archive_old(items, cutoff, run_at)
            if archived:
                sig_doc["items"] = new_items
                sig_doc["last_archive_pass"] = run_at
                write_json(RADAR_DIR / "signals.json", sig_doc)
            notes.append(f"signals: {archived} archived (cutoff = {days}d)")

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/opportunities.json", "data/radar/signals.json"], notes=notes)
