#!/usr/bin/env python3
"""
Shared freshness/recency helpers for radar build scripts.

The radar previously showed the same hand-written titles every day because
build scripts emitted static templates regardless of when the underlying
evidence appeared. This module gives each build script a small, consistent
toolbox to attach freshness metadata to every card it emits.

Usage from a builder:

    from freshness import (
        load_freshness_state, save_freshness_state,
        annotate_card, classify_freshness_label,
    )

    state = load_freshness_state()
    for card in cards:
        annotate_card(card, state, evidence=card["source_links"])
    save_freshness_state(state)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "data" / "radar" / "_freshness_state.json"


# Time buckets used across the radar UI.
BREAKING_WINDOW = timedelta(hours=2)
NEW_TODAY_WINDOW = timedelta(hours=24)
THIS_WEEK_WINDOW = timedelta(days=7)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Persisted state
# ---------------------------------------------------------------------------

def load_freshness_state() -> dict:
    """Return the stored per-card history dict.

    Shape:
        {
            "schema_version": 1,
            "cards": {
                "<card_id>": {
                    "first_appeared_at": iso,
                    "last_refreshed_at": iso,
                    "evidence_seen": ["<evidence_key>", ...]
                }
            }
        }
    """
    if not STATE_FILE.exists():
        return {"schema_version": 1, "cards": {}}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if "cards" not in data:
            data["cards"] = {}
        return data
    except json.JSONDecodeError:
        return {"schema_version": 1, "cards": {}}


def save_freshness_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Per-card annotation
# ---------------------------------------------------------------------------

def _evidence_key(item: dict) -> str:
    return (
        item.get("tweet_id")
        or item.get("id")
        or item.get("url")
        or item.get("source_url")
        or item.get("title")
        or ""
    )


def _evidence_when(item: dict) -> datetime | None:
    for key in (
        "detected_at",
        "first_seen_at",
        "collected_at",
        "posted_at",
        "generated_at",
    ):
        when = parse_iso(item.get(key))
        if when:
            return when
    return None


def annotate_card(
    card: dict,
    state: dict,
    *,
    card_id: str | None = None,
    evidence: list[dict] | None = None,
    fallback_when: datetime | None = None,
) -> dict:
    """Mutate `card` in place to add freshness metadata.

    Adds:
        - first_appeared_at
        - last_refreshed_at
        - new_evidence_count_24h
        - new_evidence_count_2h
        - evidence_count_total
        - freshness     (breaking | new_today | refreshed_today | this_week | older)
        - freshness_label_ar
    """
    card_id = card_id or card.get("id") or card.get("kind", "card")
    cards_state = state.setdefault("cards", {})
    record = cards_state.setdefault(card_id, {})

    now = now_utc()
    evidence = evidence or []

    # Seen evidence keys for this card across runs
    previous_keys: set[str] = set(record.get("evidence_seen") or [])
    current_keys: set[str] = {k for k in (_evidence_key(e) for e in evidence) if k}
    fresh_keys = current_keys - previous_keys

    # Compute timestamps
    evidence_times = [t for t in (_evidence_when(e) for e in evidence) if t]
    if not evidence_times and fallback_when:
        evidence_times = [fallback_when]

    first_appeared = parse_iso(record.get("first_appeared_at"))
    if not first_appeared:
        first_appeared = min(evidence_times) if evidence_times else now
    last_refreshed = max(evidence_times) if evidence_times else now

    # Counts within recency windows
    in_24h = sum(1 for t in evidence_times if (now - t) <= NEW_TODAY_WINDOW)
    in_2h = sum(1 for t in evidence_times if (now - t) <= BREAKING_WINDOW)

    # Decide freshness
    has_fresh_evidence = len(fresh_keys) > 0 or in_24h > 0
    is_first_appearance = not record  # nothing recorded yet

    if in_2h >= 2 or (is_first_appearance and in_2h >= 1):
        freshness = "breaking"
        label_ar = "🔥 الآن"
    elif is_first_appearance and in_24h >= 1:
        freshness = "new_today"
        label_ar = "جديد"
    elif has_fresh_evidence and in_24h >= 1:
        freshness = "refreshed_today"
        label_ar = "متجدد"
    elif evidence_times and (now - max(evidence_times)) <= THIS_WEEK_WINDOW:
        freshness = "this_week"
        label_ar = "هذا الأسبوع"
    else:
        freshness = "older"
        label_ar = "أرشيف"

    # Persist
    record["first_appeared_at"] = first_appeared.isoformat(timespec="seconds")
    record["last_refreshed_at"] = last_refreshed.isoformat(timespec="seconds")
    record["evidence_seen"] = sorted(previous_keys | current_keys)[:200]

    # Annotate the card
    card["first_appeared_at"] = first_appeared.isoformat(timespec="seconds")
    card["last_refreshed_at"] = last_refreshed.isoformat(timespec="seconds")
    card["new_evidence_count_24h"] = in_24h
    card["new_evidence_count_2h"] = in_2h
    card["new_evidence_count_since_last_run"] = len(fresh_keys)
    card["evidence_count_total"] = len(evidence)
    card["freshness"] = freshness
    card["freshness_label_ar"] = label_ar
    return card


# ---------------------------------------------------------------------------
# Convenience: filtering / grouping
# ---------------------------------------------------------------------------

def is_today(card: dict) -> bool:
    return card.get("freshness") in {"breaking", "new_today", "refreshed_today"}


def is_breaking(card: dict) -> bool:
    return card.get("freshness") == "breaking"


def relative_time_ar(iso_ts: str | None) -> str:
    """Return 'قبل ساعتين', 'منذ 6 ساعات', 'أمس'..."""
    if not iso_ts:
        return ""
    when = parse_iso(iso_ts)
    if not when:
        return ""
    delta = now_utc() - when
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "الآن"
    if seconds < 3600:
        minutes = seconds // 60
        return f"قبل {minutes} دقيقة" if minutes == 1 else f"قبل {minutes} دقيقة"
    if seconds < 86400:
        hours = seconds // 3600
        if hours == 1:
            return "قبل ساعة"
        if hours == 2:
            return "قبل ساعتين"
        return f"قبل {hours} ساعات"
    days = seconds // 86400
    if days == 1:
        return "أمس"
    if days < 7:
        return f"قبل {days} أيام"
    weeks = days // 7
    if weeks == 1:
        return "قبل أسبوع"
    if weeks < 4:
        return f"قبل {weeks} أسابيع"
    months = days // 30
    if months <= 1:
        return "قبل شهر"
    return f"قبل {months} أشهر"
