"""Agent 12 — Growth & Social (نمو الرادار والتسويق).

Turns the top opportunities + best signals into a feed of social posts
the user can copy into X / LinkedIn / Threads, with a clear CTA toward
the radar subscription page. Each post hooks first, evidences second,
asks-to-subscribe third.

Uses OpenAI when available; falls back to a rule-based template.
"""
from __future__ import annotations

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
    "أنت كاتب محتوى تسويقي عربي قصير لرواد أعمال السعودية والخليج. "
    "تكتب منشورات X و LinkedIn حادّة بدون مبالغة. كل منشور يبدأ بهوك، "
    "ثم سطر واحد دليل، ثم دعوة هادئة للاشتراك في 'AX Pulse Radar'. "
    "تعيد JSON فقط."
)


USER_TEMPLATE_AR = """من الفرص والإشارات التالية، اكتب 5 منشورات اجتماعية متنوعة (3 لـ X و2 لـ LinkedIn).

الفرص:
{opps}

أعلى الإشارات:
{signals}

أعد JSON بهذا الشكل:
{{
  "posts": [
    {{
      "platform": "x" | "linkedin",
      "hook_ar": "السطر الأول الجاذب",
      "body_ar": "1-2 جملة دليل",
      "cta_ar": "دعوة قصيرة للاشتراك",
      "hashtags": ["AI", "ذكاء_اصطناعي"],
      "evidence_id": "id من الإشارات أو الفرص"
    }}
  ]
}}

X: أقل من 240 حرفًا للمنشور كاملًا. LinkedIn: أقل من 600 حرف.
لا تستخدم لغة مبالغ بها (\"الأفضل\", \"ثوري\", \"غيّر اللعبة\")."""


def _opps_block(opps: list[dict], n: int = 5) -> str:
    lines = []
    for o in opps[:n]:
        lines.append(f"- [{o.get('id')}] {o.get('title_ar')}: {truncate(o.get('thesis_ar') or o.get('sellable_product_ar') or '', 160)}")
    return "\n".join(lines) or "(لا توجد فرص جاهزة)"


def _signals_block(items: list[dict], n: int = 8) -> str:
    lines = []
    for it in items[:n]:
        lines.append(f"- [{it.get('id') or it.get('source_id')}] ({it.get('trust_tier','?')}) {truncate(it.get('title') or '', 140)}")
    return "\n".join(lines) or "(لا توجد إشارات)"


def _rule_posts(opps: list[dict], items: list[dict]) -> list[dict]:
    posts = []
    for o in opps[:3]:
        posts.append({
            "platform": "x",
            "hook_ar": truncate(o.get("title_ar") or "فرصة جديدة في الذكاء الاصطناعي", 80),
            "body_ar": truncate(o.get("thesis_ar") or o.get("sellable_product_ar") or "", 160),
            "cta_ar": "اشترك في AX Pulse Radar لتصلك أمثال هذه يوميًا.",
            "hashtags": ["AI", "ذكاء_اصطناعي", "ريادة"],
            "evidence_id": o.get("id"),
        })
    for it in items[:2]:
        posts.append({
            "platform": "linkedin",
            "hook_ar": truncate(it.get("title_ar") or it.get("title") or "", 100),
            "body_ar": truncate(it.get("text") or "", 320),
            "cta_ar": "نتابع هذه الإشارات أسبوعيًا في AX Pulse Radar — يمكنك الاشتراك من الموقع.",
            "hashtags": ["AI", "BusinessIntelligence"],
            "evidence_id": it.get("id") or it.get("source_id"),
        })
    return posts


class GrowthSocial(Agent):
    name = "growth_social"
    description = "يحوّل أبرز الفرص والإشارات إلى منشورات X/LinkedIn ودعوات اشتراك."
    inputs = ["ctx.state.ranked_items", "data/radar/opportunities.json"]
    outputs = ["data/radar/agents/social_posts.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("ranked_items") or []
        opps_doc = ctx.state.get("opportunities_doc") or read_json(RADAR_DIR / "opportunities.json", {}) or {}
        opps = opps_doc.get("opportunities") or []

        run_at = ctx.state.get("run_at") or now_iso()
        notes: list[str] = []
        posts: list[dict] = []
        used_openai = False

        if ctx.can_call_openai(1):
            data = call_openai_json(
                ctx,
                system=SYSTEM_AR,
                user=USER_TEMPLATE_AR.format(opps=_opps_block(opps), signals=_signals_block(items)),
                model=DEFAULT_MODEL,
                max_tokens=1200,
                temperature=0.6,
            )
            if data and isinstance(data.get("posts"), list):
                for p in data["posts"][:5]:
                    if isinstance(p, dict) and p.get("hook_ar"):
                        posts.append({
                            "platform": p.get("platform", "x"),
                            "hook_ar": p.get("hook_ar", ""),
                            "body_ar": p.get("body_ar", ""),
                            "cta_ar": p.get("cta_ar", ""),
                            "hashtags": p.get("hashtags") or [],
                            "evidence_id": p.get("evidence_id"),
                        })
                used_openai = True
                notes.append(f"openai produced {len(posts)} posts")

        if not posts:
            posts = _rule_posts(opps, items)
            notes.append(f"rule fallback produced {len(posts)} posts")

        out = {
            "generated_at": run_at,
            "source": "agent_pipeline_v1" + ("+openai" if used_openai else "+rules"),
            "note_ar": "منشورات جاهزة للنسخ يدويًا إلى X و LinkedIn. لا يتم النشر التلقائي.",
            "posts": posts,
        }
        path = RADAR_DIR / "agents" / "social_posts.json"
        write_json(path, out)

        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=notes)
