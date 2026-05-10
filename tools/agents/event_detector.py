"""Smart Event Detector — turns lists of signals into discrete events.

Detects 6 event classes:
  - model_release   (new model / version available)
  - pricing_change  ($X/mo or $X/seat patterns)
  - funding_round   (Series X, raised $XM)
  - acquisition     (acquired by, merger)
  - personnel_move  (joined, hired, leaves, new CEO)
  - policy_signal   (regulation, GDPR, EU AI Act)

Every event is anchored to a subject (entity) and gathers its supporting
signals (evidence). Same subject + type within 24h = single event with
N evidence. Pure rules — no OpenAI cost.

Output: data/radar/agents/events.json
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

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
from .companies_detector import KNOWN_ENTITIES
from .models_pulse import MODEL_PATTERNS, RELEASE_VERBS


# --- Regex patterns for each event class ---

PRICING_RE = re.compile(
    r"\$\s*\d+(?:\.\d+)?\s*(?:/\s*(?:mo|month|yr|year|user|seat|m))?",
    re.IGNORECASE,
)
FUNDING_RE = re.compile(
    r"\b(?:series\s+[A-Z]|seed\s+round|raised\s+\$\d+\s*[MmBb]|"
    r"\$\d+\s*[MmBb]\s+round|funded|funding)\b",
    re.IGNORECASE,
)
ACQUISITION_RE = re.compile(
    r"\b(?:acquir(?:ed|ing|e[sd]?)|acquisition|merger|merg(?:ed|ing)|"
    r"buyout|bought\s+by|takeover)\b",
    re.IGNORECASE,
)
PERSONNEL_RE = re.compile(
    r"\b(?:joined|hired\s+by|leaves|leaving|appointed|new\s+CEO|"
    r"new\s+CTO|new\s+head\s+of|departing|stepping\s+down)\b",
    re.IGNORECASE,
)
POLICY_RE = re.compile(
    r"\b(?:regulation|regulator|GDPR|EU\s+AI\s+Act|HIPAA|SOC\s*2|"
    r"compliance|moratorium|antitrust|FTC|investigation|"
    r"تنظيم|حوكمة|امتثال|قوانين)\b",
    re.IGNORECASE,
)


def _extract_subject(text: str) -> str | None:
    """Find which known entity this signal is about (best match)."""
    low = text.lower()
    matches = []
    for name in KNOWN_ENTITIES.keys():
        if name in low:
            matches.append((len(name), name))
    if not matches:
        return None
    # longest match wins (e.g. "stability ai" before "ai")
    return max(matches)[1]


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _classify(item: dict) -> list[str]:
    """Return event types this signal could belong to (zero or more)."""
    text = ((item.get("title") or "") + " " + (item.get("text") or ""))
    types = []
    if RELEASE_VERBS.search(text):
        for fam, pattern in MODEL_PATTERNS.items():
            if pattern.search(text):
                types.append(("model_release", fam))
                break
    if PRICING_RE.search(text):
        types.append(("pricing_change", None))
    if FUNDING_RE.search(text):
        types.append(("funding_round", None))
    if ACQUISITION_RE.search(text):
        types.append(("acquisition", None))
    if PERSONNEL_RE.search(text):
        types.append(("personnel_move", None))
    if POLICY_RE.search(text):
        types.append(("policy_signal", None))
    return types


_TYPE_LABELS_AR = {
    "model_release":   "إصدار نموذج",
    "pricing_change":  "تغيير سعر",
    "funding_round":   "جولة تمويل",
    "acquisition":     "استحواذ",
    "personnel_move":  "حركة كادر",
    "policy_signal":   "إشارة تنظيمية",
}

_TYPE_LABELS_EN = {
    "model_release":   "Model release",
    "pricing_change":  "Pricing change",
    "funding_round":   "Funding round",
    "acquisition":     "Acquisition",
    "personnel_move":  "Personnel move",
    "policy_signal":   "Policy signal",
}

_TYPE_ICONS = {
    "model_release":   "⊕",
    "pricing_change":  "$",
    "funding_round":   "↑",
    "acquisition":     "⊗",
    "personnel_move":  "↪",
    "policy_signal":   "§",
}


def _bucket_key(subject: str, etype: str, fam: str | None, posted_at: datetime | None, run_at: datetime) -> tuple:
    """Group key: events about the same subject+type within a 24h window are one event."""
    bucket_day = (posted_at or run_at).strftime("%Y-%m-%d")
    return (subject, etype, fam or "", bucket_day)


class SmartEventDetector(Agent):
    name = "event_detector"
    description = "يحوّل الإشارات إلى أحداث مرصودة (إصدارات، أسعار، تمويل، استحواذ، كادر، تنظيم)."
    inputs = ["data/radar/signals.json"]
    outputs = ["data/radar/agents/events.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        run_at_iso = ctx.state.get("run_at") or now_iso()
        run_at = _parse_iso(run_at_iso) or datetime.now(timezone.utc)

        # Use ranked items if available; otherwise fall back to disk.
        items = ctx.state.get("ranked_items") or ctx.state.get("tagged_items") or []
        if not items:
            items = (read_json(RADAR_DIR / "signals.json", {}) or {}).get("items") or []

        groups: dict[tuple, dict] = defaultdict(lambda: {"evidence": []})

        for item in items:
            text = (item.get("title") or "") + " " + (item.get("text") or "")
            subject = _extract_subject(text)
            classifications = _classify(item)
            if not classifications:
                continue
            posted = _parse_iso(item.get("posted_at") or item.get("collected_at"))
            for etype, fam in classifications:
                if not subject and etype == "model_release" and fam:
                    subject = fam  # use model family as subject if no entity
                if not subject:
                    continue
                key = _bucket_key(subject, etype, fam, posted, run_at)
                g = groups[key]
                g["subject"] = subject
                g["type"] = etype
                g["family"] = fam
                g["evidence"].append({
                    "id": item.get("id") or item.get("source_id"),
                    "source_id": item.get("source_id"),
                    "source_name": item.get("source_name"),
                    "title": truncate(item.get("title") or "", 160),
                    "url": item.get("source_url"),
                    "trust_tier": item.get("trust_tier"),
                    "posted_at": item.get("posted_at") or item.get("collected_at"),
                })

        # Keep events that have ≥2 evidence OR ≥1 evidence from official/research source
        previous_doc = read_json(RADAR_DIR / "agents" / "events.json", {}) or {}
        prev_events = {e.get("id"): e for e in (previous_doc.get("events") or [])}

        events = []
        for key, g in groups.items():
            ev = g["evidence"]
            tiers = {e.get("trust_tier") for e in ev}
            high_trust = bool(tiers & {"official", "research"})
            if len(ev) < 2 and not high_trust:
                continue

            event_id = "evt_" + "_".join(str(p) for p in key if p)
            event_id = re.sub(r"[^a-z0-9_]", "_", event_id.lower())[:80]
            etype = g["type"]
            subject = g["subject"]

            # First-seen vs returning event
            prev = prev_events.get(event_id)
            first_seen = prev["first_seen"] if prev else (ev[0].get("posted_at") or run_at_iso)
            is_new = not prev

            events.append({
                "id": event_id,
                "type": etype,
                "icon": _TYPE_ICONS[etype],
                "subject": subject,
                "family": g.get("family"),
                "title_ar": f"{_TYPE_LABELS_AR[etype]}: {subject}",
                "title_en": f"{_TYPE_LABELS_EN[etype]}: {subject}",
                "label_ar": _TYPE_LABELS_AR[etype],
                "label_en": _TYPE_LABELS_EN[etype],
                "evidence_count": len(ev),
                "confidence": min(1.0, 0.40 + 0.15 * len(ev) + (0.15 if high_trust else 0)),
                "first_seen": first_seen,
                "last_updated": run_at_iso,
                "is_new": is_new,
                "tier": "premium" if etype in {"funding_round", "acquisition"} else "free",
                "evidence": sorted(ev, key=lambda e: e.get("posted_at") or "", reverse=True)[:8],
            })

        events.sort(key=lambda e: (e["confidence"], e["evidence_count"]), reverse=True)
        events = events[:30]

        out = {
            "generated_at": run_at_iso,
            "note_ar": "أحداث مستخرجة من الإشارات تلقائيًا. كل حدث مدعوم بـ ≥ 2 إشارة أو إشارة من مصدر رسمي.",
            "count": len(events),
            "events": events,
        }
        path = RADAR_DIR / "agents" / "events.json"
        write_json(path, out)
        ctx.state["events"] = events

        notes = [f"{len(events)} events ({sum(1 for e in events if e['is_new'])} new)"]
        if events:
            top_types = {}
            for e in events:
                top_types[e["type"]] = top_types.get(e["type"], 0) + 1
            notes.append("by type: " + ", ".join(f"{k}={v}" for k, v in top_types.items()))
        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=notes)
