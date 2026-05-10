"""Agent 7 — صانع الفرص (Opportunity Builder).

Replaces the 4 hardcoded buckets in pulse_radar.build_opportunities with
OpenAI-driven opportunity synthesis. With no API key, falls back to a
clustering-based rule that's still better than fixed templates.

Output schema is backwards-compatible with what `opportunities.html` and
`build_digest.py` already read.
"""
from __future__ import annotations

import re
from collections import Counter

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DEFAULT_MODEL,
    RADAR_DIR,
    call_openai_json,
    now_iso,
    truncate,
    write_json,
)


SYSTEM_AR = (
    "أنت محلل ذكاء أعمال متخصص في تحويل إشارات تقنية إلى فرص دخل ملموسة "
    "في السوق العربي والسعودي. تكتب بإيجاز عربي واضح. "
    "ترفض التكهن: لا تذكر سعرًا أو رقمًا إلا إذا ورد في الإشارات. "
    "تعيد JSON فقط."
)


USER_TEMPLATE_AR = """فيما يلي مجموعة إشارات حديثة عن الذكاء الاصطناعي. حلّلها واستخرج فرصًا تجارية قابلة للتنفيذ.

الإشارات:
{evidence}

أعد JSON بهذا الشكل بالضبط:
{{
  "opportunities": [
    {{
      "id": "kebab-case-id",
      "title_ar": "عنوان مختصر للفرصة",
      "thesis_ar": "جملتان توضحان لماذا هذه فرصة الآن",
      "buyer_ar": "من المشتري المحتمل",
      "sellable_product_ar": "ما المنتج/الخدمة القابلة للبيع",
      "first_paid_test_ar": "أصغر اختبار مدفوع لإثبات الجدوى",
      "tools_ar": "الأدوات المطلوبة (3 كحد أقصى)",
      "capital_ar": "بدون رأس مال | منخفض | متوسط",
      "evidence_ids": ["id1", "id2"],
      "confidence": 0.0
    }}
  ]
}}

اكتب فقط الفرص التي تستند إلى ≥3 إشارات. حد أقصى 5 فرص. confidence بين 0 و1.
لا تذكر أسعارًا محددة. لا تذكر اسم شركة لم تظهر في الإشارات."""


def _evidence_text(items: list[dict], max_items: int = 30) -> tuple[str, list[dict]]:
    out_lines = []
    selected = items[:max_items]
    for it in selected:
        title = truncate(it.get("title") or "", 140)
        body = truncate(it.get("text") or "", 220)
        out_lines.append(f"- [{it.get('id') or it.get('source_id')}] ({it.get('trust_tier','?')}/{(it.get('priority') or 0):.2f}) {title} — {body}")
    return "\n".join(out_lines), selected


_NEEDLES = {
    "ai_income_services": ["service", "agency", "client", "consulting", "freelance", "خدمة", "عميل", "عملاء", "وكالة", "استشارات", "مستقل"],
    "ai_income_tools": ["tool", "app", "saas", "subscription", "product", "framework", "أداة", "تطبيق", "اشتراك", "منتج"],
    "ai_income_automation": ["automation", "workflow", "agent", "agents", "mcp", "أتمتة", "سير عمل", "وكلاء"],
    "ai_income_content": ["content", "video", "voice", "image", "design", "marketing", "محتوى", "فيديو", "تصميم", "تسويق", "صوت"],
}

_FALLBACK_TEMPLATES = {
    "ai_income_services": {
        "title_ar": "خدمات يمكن بيعها باستخدام الذكاء الاصطناعي",
        "buyer_ar": "أفراد، مستقلون، وشركات صغيرة لديها عمل متكرر",
        "sellable_product_ar": "باقة خدمة تنفذ عملاً متكررًا للعميل باستخدام أدوات AI",
        "first_paid_test_ar": "بيع تجربة صغيرة لعميل واحد: نتيجة جاهزة خلال 48 ساعة",
        "tools_ar": "ChatGPT أو Claude، Notion، أداة تسليم بسيطة",
        "capital_ar": "بدون رأس مال",
    },
    "ai_income_tools": {
        "title_ar": "أدوات ومنتجات صغيرة مدعومة بالذكاء الاصطناعي",
        "buyer_ar": "صناع محتوى، فرق صغيرة، شركات ناشئة",
        "sellable_product_ar": "أداة محددة تحل مهمة واحدة قابلة للتكرار",
        "first_paid_test_ar": "صفحة انتظار + نموذج أولي + 5 مقابلات شراء",
        "tools_ar": "واجهة بسيطة، API نموذج AI، صفحة هبوط",
        "capital_ar": "منخفض",
    },
    "ai_income_automation": {
        "title_ar": "أتمتة أعمال توفّر وقتًا قابل للتسعير",
        "buyer_ar": "شركات صغيرة وفرق تشغيل لديها مهام متكررة",
        "sellable_product_ar": "أتمتة تربط أدوات العميل وتقلل عملًا يدويًا",
        "first_paid_test_ar": "اختيار عملية واحدة وقياس الوقت قبل/بعد",
        "tools_ar": "n8n أو Make، API، نموذج AI",
        "capital_ar": "منخفض",
    },
    "ai_income_content": {
        "title_ar": "محتوى وتسويق بالذكاء الاصطناعي قابل للبيع",
        "buyer_ar": "متاجر، صناع محتوى، علامات شخصية",
        "sellable_product_ar": "إنتاج محتوى/إعلانات/فيديوهات قصيرة بمساعدة AI",
        "first_paid_test_ar": "إنتاج 3 عينات قبل/بعد لعميل واحد",
        "tools_ar": "ChatGPT/Claude، أداة تصميم أو فيديو، جدولة نشر",
        "capital_ar": "بدون رأس مال",
    },
}


def _rule_fallback(items: list[dict]) -> list[dict]:
    """If OpenAI is unavailable: cluster by needles like the legacy code did,
    but use the new trust + priority scores so output is at least better."""
    opps = []
    for key, needles in _NEEDLES.items():
        ev = []
        for it in items:
            hay = ((it.get("title") or "") + " " + (it.get("text") or "")).lower()
            if it.get("priority", 0) >= 0.30 and any(n in hay for n in needles):
                ev.append(it)
        if len(ev) < 3:
            continue
        ev = sorted(ev, key=lambda x: x.get("priority", 0), reverse=True)[:8]
        avg = sum(e.get("priority", 0) for e in ev) / len(ev)
        tmpl = _FALLBACK_TEMPLATES[key]
        opps.append({
            "id": key,
            "title_ar": tmpl["title_ar"],
            "thesis_ar": "إشارات متعددة من مصادر مختلفة تشير إلى نشاط في هذا المسار.",
            "buyer_ar": tmpl["buyer_ar"],
            "sellable_product_ar": tmpl["sellable_product_ar"],
            "first_paid_test_ar": tmpl["first_paid_test_ar"],
            "tools_ar": tmpl["tools_ar"],
            "capital_ar": tmpl["capital_ar"],
            "signal_count": len(ev),
            "avg_score": round(avg, 2),
            "confidence": round(min(0.85, 0.35 + len(ev) * 0.05 + avg * 0.20), 2),
            "source": "rules",
            "evidence_items": [
                {"source_id": e.get("source_id"), "title": e.get("title"), "url": e.get("source_url"), "score": round(e.get("priority", 0), 3), "trust_tier": e.get("trust_tier")}
                for e in ev
            ],
        })
    return sorted(opps, key=lambda o: o["confidence"], reverse=True)


def _attach_evidence(opp: dict, items: list[dict]) -> dict:
    ids_wanted = set(opp.get("evidence_ids") or [])
    ev = [it for it in items if (it.get("id") in ids_wanted or it.get("source_id") in ids_wanted)]
    if not ev:
        # fallback: take top-priority items that share keywords with the title
        kws = re.findall(r"\w+", (opp.get("title_ar") or "").lower())
        ev = [it for it in items[:8] if any(k in (it.get("title") or "").lower() for k in kws)][:6] or items[:6]
    avg = sum(e.get("priority", 0) for e in ev) / len(ev) if ev else 0.0
    opp["signal_count"] = len(ev)
    opp["avg_score"] = round(avg, 2)
    opp["evidence_items"] = [
        {"source_id": e.get("source_id"), "title": e.get("title"), "url": e.get("source_url"), "score": round(e.get("priority", 0), 3), "trust_tier": e.get("trust_tier")}
        for e in ev
    ]
    return opp


class OpportunityBuilder(Agent):
    name = "opportunity_builder"
    description = "يحوّل أفضل الإشارات إلى فرص دخل قابلة للتنفيذ (OpenAI مع سقوط لقواعد عند غياب المفتاح)."
    inputs = ["ctx.state.ranked_items"]
    outputs = ["data/radar/opportunities.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("ranked_items") or []
        run_at = ctx.state.get("run_at") or now_iso()
        notes: list[str] = []

        top = sorted(items, key=lambda x: x.get("priority", 0), reverse=True)[:30]
        opps: list[dict] = []
        used_openai = False

        if ctx.can_call_openai(1) and top:
            evidence_text, _ = _evidence_text(top, max_items=30)
            data = call_openai_json(
                ctx,
                system=SYSTEM_AR,
                user=USER_TEMPLATE_AR.format(evidence=evidence_text),
                model=DEFAULT_MODEL,
                max_tokens=1400,
                temperature=0.4,
            )
            if data and isinstance(data.get("opportunities"), list):
                for raw in data["opportunities"][:5]:
                    if not isinstance(raw, dict):
                        continue
                    opp = {
                        "id": raw.get("id") or "opp",
                        "title_ar": raw.get("title_ar") or "",
                        "thesis_ar": raw.get("thesis_ar") or "",
                        "buyer_ar": raw.get("buyer_ar") or "",
                        "sellable_product_ar": raw.get("sellable_product_ar") or "",
                        "first_paid_test_ar": raw.get("first_paid_test_ar") or "",
                        "tools_ar": raw.get("tools_ar") or "",
                        "capital_ar": raw.get("capital_ar") or "منخفض",
                        "evidence_ids": raw.get("evidence_ids") or [],
                        "confidence": float(raw.get("confidence") or 0.5),
                        "source": "openai",
                    }
                    _attach_evidence(opp, top)
                    if opp["signal_count"] >= 2:
                        opps.append(opp)
                used_openai = True
                notes.append(f"openai produced {len(opps)} opportunities")

        if not opps:
            opps = _rule_fallback(items)
            notes.append(f"rule fallback produced {len(opps)} opportunities")

        out = {
            "generated_at": run_at,
            "source": "agent_pipeline_v1" + ("+openai" if used_openai else "+rules"),
            "note_ar": "فرص مبنية على إشارات حقيقية. التكرار عبر الوقت يرفع الثقة.",
            "corpus_count": len(items),
            "opportunities": opps,
        }
        write_json(RADAR_DIR / "opportunities.json", out)

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=["data/radar/opportunities.json"], notes=notes)
