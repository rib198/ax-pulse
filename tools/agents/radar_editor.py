"""Agent 8 — محرر الرادار (Radar Editor).

Writes the daily Arabic brief in the four-question structure the user asked for:
ماذا حدث؟ — لماذا يهمك؟ — كيف تستفيد؟ — ما الدليل؟

Outputs `data/brief.ar.json` (consumed by dashboard.html and build_digest.py).
Also produces `data/brief.en.json` as a literal English mirror for parity.
"""
from __future__ import annotations

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DATA_DIR,
    DEFAULT_MODEL,
    call_openai_json,
    now_iso,
    truncate,
    write_json,
)


SYSTEM_AR = (
    "أنت محرر نشرة عربية يومية عن الذكاء الاصطناعي. أسلوبك: مباشر، بدون مبالغة، "
    "بدون كلمات تسويقية. كل جملة لها معنى. تعيد JSON فقط."
)


USER_TEMPLATE_AR = """من الإشارات التالية، اكتب نشرة اليوم العربية. الجمهور رواد أعمال وصناع محتوى عرب يبحثون عن دخل من الذكاء الاصطناعي.

أعلى {n} إشارة (مرتبة):
{evidence}

أعد JSON بهذا الشكل:
{{
  "headline_ar": "عنوان رئيسي للنشرة (أقل من 70 حرفًا)",
  "summary_ar": "ملخص في 3 جمل: ماذا حدث، لماذا يهم، كيف تستفيد",
  "stories": [
    {{
      "title_ar": "خبر/إشارة واحدة",
      "what_happened_ar": "ماذا حدث (جملة)",
      "why_it_matters_ar": "لماذا يهمك (جملة)",
      "how_to_use_ar": "كيف تستفيد عمليًا (جملة قابلة للتنفيذ)",
      "evidence_id": "id من الإشارات"
    }}
  ]
}}

عدد القصص: 5 بالضبط. لا تكرر معلومة بين headline و summary و stories.
لا تذكر أسعارًا أو أرقامًا غير موجودة في الإشارات. لا تخترع معلومات."""


def _evidence_block(items: list[dict], n: int = 12) -> tuple[str, list[dict]]:
    selected = items[:n]
    lines = []
    for it in selected:
        title = truncate(it.get("title") or "", 140)
        body = truncate(it.get("text") or "", 200)
        lines.append(f"- [{it.get('id') or it.get('source_id')}] ({it.get('trust_tier','?')}) {title} — {body}")
    return "\n".join(lines), selected


def _rule_brief(items: list[dict]) -> dict:
    top = items[:5]
    stories = []
    for it in top:
        title = it.get("title_ar") or it.get("title") or ""
        text = it.get("text") or ""
        stories.append({
            "title_ar": truncate(title, 120),
            "what_happened_ar": truncate(text or title, 180),
            "why_it_matters_ar": "إشارة من مصدر " + (it.get("trust_tier") or "غير محدد") + " قد تفتح فرصة عملية.",
            "how_to_use_ar": "افحص الإشارة، حدد إن كانت تخدم عميلًا أو منتجًا حاليًا.",
            "evidence_id": it.get("id") or it.get("source_id") or "",
        })
    headline = top[0].get("title_ar") or top[0].get("title") or "نبض اليوم في الذكاء الاصطناعي" if top else "نبض اليوم في الذكاء الاصطناعي"
    return {
        "headline_ar": truncate(headline, 70),
        "summary_ar": "نظرة سريعة على أبرز إشارات اليوم في الذكاء الاصطناعي وكيف يمكن الاستفادة منها.",
        "stories": stories,
    }


class RadarEditor(Agent):
    name = "radar_editor"
    description = "يكتب النشرة العربية اليومية بأربع أسئلة: ماذا/لماذا/كيف/الدليل (OpenAI مع سقوط لقواعد)."
    inputs = ["ctx.state.ranked_items"]
    outputs = ["data/brief.ar.json", "data/brief.en.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("ranked_items") or []
        run_at = ctx.state.get("run_at") or now_iso()
        notes: list[str] = []

        brief: dict | None = None
        used_openai = False

        if ctx.can_call_openai(1) and items:
            evidence_text, picked = _evidence_block(items, n=12)
            data = call_openai_json(
                ctx,
                system=SYSTEM_AR,
                user=USER_TEMPLATE_AR.format(n=len(picked), evidence=evidence_text),
                model=DEFAULT_MODEL,
                max_tokens=1200,
                temperature=0.4,
            )
            if data and data.get("headline_ar") and isinstance(data.get("stories"), list):
                brief = {
                    "headline_ar": data["headline_ar"],
                    "summary_ar": data.get("summary_ar", ""),
                    "stories": [s for s in data["stories"] if isinstance(s, dict) and s.get("title_ar")][:5],
                }
                used_openai = True
                notes.append("openai produced brief")

        if brief is None:
            brief = _rule_brief(items)
            notes.append("rule fallback brief")

        # attach evidence URLs by id
        by_id = {(it.get("id") or it.get("source_id")): it for it in items}
        for s in brief["stories"]:
            ev = by_id.get(s.get("evidence_id"))
            if ev:
                s["evidence_url"] = ev.get("source_url")
                s["evidence_source"] = ev.get("source_name") or ev.get("source_id")
                s["trust_tier"] = ev.get("trust_tier")

        ar_out = {
            "generated_at": run_at,
            "source": "agent_pipeline_v1" + ("+openai" if used_openai else "+rules"),
            **brief,
        }
        write_json(DATA_DIR / "brief.ar.json", ar_out)

        # English mirror — keep schema parity for dashboard.html EN mode
        en_out = {
            "generated_at": run_at,
            "source": ar_out["source"],
            "headline_en": brief["headline_ar"],
            "summary_en": brief.get("summary_ar", ""),
            "stories": [
                {
                    "title_en": s.get("title_ar"),
                    "what_happened_en": s.get("what_happened_ar"),
                    "why_it_matters_en": s.get("why_it_matters_ar"),
                    "how_to_use_en": s.get("how_to_use_ar"),
                    "evidence_id": s.get("evidence_id"),
                    "evidence_url": s.get("evidence_url"),
                    "evidence_source": s.get("evidence_source"),
                }
                for s in brief["stories"]
            ],
        }
        write_json(DATA_DIR / "brief.en.json", en_out)

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/brief.ar.json", "data/brief.en.json"], notes=notes)
