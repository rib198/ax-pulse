"""Autonomous Insight Generator — one short observation per run.

Reads system metrics, recent signals, recent events, and (when OpenAI is
available) writes a 2-3 sentence Arabic + English observation about
*what changed* — not what happened. The radar develops an "opinion".

Falls back to a deterministic rule-based summary when OpenAI is off,
so the system always has an insight to show.

Output: data/radar/agents/insights.json
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DEFAULT_MODEL,
    RADAR_DIR,
    call_openai_json,
    now_iso,
    read_json,
    truncate,
    write_json,
)


SYSTEM_AR = (
    "أنت محلّل ذكاء أعمال يُلاحظ الأنماط في إشارات الذكاء الاصطناعي. "
    "تكتب ملاحظة عربية واحدة في 2-3 جمل تشرح *ما تغيّر* في النشاط، "
    "ليس ما حدث. اللغة مختصرة، احترافية، بدون مبالغة. تعيد JSON فقط."
)


USER_TMPL = """فيما يلي لقطة من حالة الرادار. اكتب ملاحظة واحدة عمّا لاحظته من نمط أو تغيّر.

📊 المقاييس
- إجمالي الإشارات اليوم: {signal_count}
- فرص هذا التشغيل: {opp_count}
- أحداث مرصودة: {event_count}
- مصادر نشطة: {active_sources}

🎯 أبرز الأحداث الجديدة:
{events_block}

📈 الإشارات الأكثر بروزاً:
{top_signals}

📉 ما تغيّر مقارنة بالتشغيل السابق:
- إشارات: {delta_items:+}
- فرص: {delta_opps:+}

أعد JSON بهذا الشكل:
{{
  "insight_ar": "جملتان أو ثلاث جمل عربية",
  "insight_en": "Same in English, 2-3 sentences",
  "topic": "كلمتان عن الموضوع",
  "anchor_event_id": "id من الأحداث إن وُجد، وإلا null",
  "anchor_signal_id": "id من الإشارات إن لم يوجد حدث، وإلا null"
}}

المطلوب: ملاحظة عن *النمط*، لا قائمة وقائع. مثال جيد: "نشاط الإصدارات تركّز على Anthropic هذا الأسبوع — 3 إعلانات في 5 أيام بينما المعدل العادي إعلان كل 9 أيام."
سيء: "اليوم: Anthropic أعلنت X."
"""


def _events_block(events: list[dict], n: int = 5) -> str:
    if not events:
        return "(لا أحداث مرصودة في هذا التشغيل)"
    lines = []
    for e in events[:n]:
        lines.append(f"- [{e.get('label_ar')}] {e.get('subject')} ({e.get('evidence_count')} إشارة، ثقة {e.get('confidence', 0):.2f})")
    return "\n".join(lines)


def _signals_block(items: list[dict], n: int = 6) -> str:
    if not items:
        return "(لا إشارات)"
    lines = []
    for it in items[:n]:
        title = truncate(it.get("title") or "", 120)
        lines.append(f"- [{it.get('source_id', '?')}] ({it.get('trust_tier','?')}/{(it.get('priority') or 0):.2f}) {title}")
    return "\n".join(lines)


def _rule_insight(signals: list[dict], events: list[dict], delta_items: int, delta_opps: int) -> dict:
    """Deterministic fallback when OpenAI is unavailable."""
    ar_parts = []
    en_parts = []

    if events:
        new_events = [e for e in events if e.get("is_new")]
        if new_events:
            top = new_events[0]
            ar_parts.append(f"رصد {len(new_events)} حدثًا جديدًا أبرزها: {top.get('label_ar')} على {top.get('subject')} بـ {top.get('evidence_count')} إشارة.")
            en_parts.append(f"Detected {len(new_events)} new events; most prominent: {top.get('label_en')} on {top.get('subject')} with {top.get('evidence_count')} signals.")
        else:
            ar_parts.append(f"الأحداث المرصودة مستقرة هذا التشغيل ({len(events)} حدث متابع).")
            en_parts.append(f"Tracked events stable this run ({len(events)} ongoing).")
    else:
        ar_parts.append("لم تُرصد أحداث مركّبة من الإشارات هذا التشغيل.")
        en_parts.append("No composite events surfaced from signals this run.")

    if abs(delta_items) >= 20:
        direction_ar = "ارتفع" if delta_items > 0 else "انخفض"
        direction_en = "rose" if delta_items > 0 else "fell"
        ar_parts.append(f"تدفّق الإشارات {direction_ar} بمقدار {abs(delta_items)} منذ التشغيل السابق.")
        en_parts.append(f"Signal flow {direction_en} by {abs(delta_items)} since last run.")

    return {
        "insight_ar": " ".join(ar_parts) or "النظام في وضع مراقبة عادي.",
        "insight_en": " ".join(en_parts) or "System nominal — passive monitoring.",
        "topic": "system_state",
        "anchor_event_id": events[0]["id"] if events else None,
        "anchor_signal_id": signals[0].get("id") if signals and not events else None,
        "source": "rules",
    }


class InsightGenerator(Agent):
    name = "insight_generator"
    description = "يكتب ملاحظة ذكية عن نمط هذا التشغيل (OpenAI مع سقوط لقواعد)."
    inputs = ["events.json", "performance.json", "signals.json"]
    outputs = ["data/radar/agents/insights.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        run_at = ctx.state.get("run_at") or now_iso()
        events = ctx.state.get("events") or (read_json(RADAR_DIR / "agents" / "events.json", {}) or {}).get("events") or []
        items = ctx.state.get("ranked_items") or ctx.state.get("tagged_items") or []
        if not items:
            items = (read_json(RADAR_DIR / "signals.json", {}) or {}).get("items") or []
        opps_doc = read_json(RADAR_DIR / "opportunities.json", {}) or {}
        perf_doc = read_json(RADAR_DIR / "agents" / "performance.json", {}) or {}

        delta = (perf_doc.get("delta_vs_prev") or {})
        delta_items = int(delta.get("items") or 0)
        delta_opps  = int(delta.get("opportunities") or 0)

        insight = None
        used_openai = False

        if ctx.can_call_openai(1):
            active_sources = len({s.get("source_id") for s in items if s.get("source_id")})
            user_prompt = USER_TMPL.format(
                signal_count=len(items),
                opp_count=len(opps_doc.get("opportunities") or []),
                event_count=len(events),
                active_sources=active_sources,
                events_block=_events_block(events),
                top_signals=_signals_block(items),
                delta_items=delta_items,
                delta_opps=delta_opps,
            )
            data = call_openai_json(
                ctx,
                system=SYSTEM_AR,
                user=user_prompt,
                model=DEFAULT_MODEL,
                max_tokens=600,
                temperature=0.6,
            )
            if data and data.get("insight_ar"):
                insight = {
                    "insight_ar": data["insight_ar"],
                    "insight_en": data.get("insight_en", ""),
                    "topic": data.get("topic", "general"),
                    "anchor_event_id": data.get("anchor_event_id"),
                    "anchor_signal_id": data.get("anchor_signal_id"),
                    "source": "openai",
                }
                used_openai = True

        if insight is None:
            insight = _rule_insight(items, events, delta_items, delta_opps)

        # Read history (last 30 insights kept)
        prev = read_json(RADAR_DIR / "agents" / "insights.json", {}) or {}
        history = list(prev.get("history") or [])
        history.insert(0, {**insight, "generated_at": run_at})
        history = history[:30]

        out = {
            "generated_at": run_at,
            "source": insight.get("source"),
            "current": {**insight, "generated_at": run_at},
            "history": history,
            "note_ar": "ملاحظة الرادار عن النمط لا الوقائع. تتجدّد كل تشغيل.",
        }
        path = RADAR_DIR / "agents" / "insights.json"
        write_json(path, out)
        ctx.state["insight"] = out["current"]

        return AgentResult(
            name=self.name,
            ok=True,
            duration_s=0.0,
            written=[str(path.relative_to(RADAR_DIR.parent.parent))],
            notes=[f"insight via {insight.get('source')}: {truncate(insight.get('insight_ar', ''), 80)}"],
        )
