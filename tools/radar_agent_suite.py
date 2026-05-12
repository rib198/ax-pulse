#!/usr/bin/env python3
"""Build the AI Radar multi-agent operating layer.

This script does not collect new data. It reads the current radar archives and
produces three operational artifacts:

- data/radar/agent_manifest.json: the complete agent map.
- data/radar/agent_performance_report.json: a monitor report for agent output.
- data/radar/growth_tweet_drafts.json: X-ready marketing drafts for review.

It is intentionally deterministic so it can run locally, in n8n, or in GitHub
Actions without spending API credits. OpenAI enrichment can be layered later.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "radar"
MANUAL_X = ROOT / "data" / "manual_x"

MANIFEST_FILE = DATA / "agent_manifest.json"
PERFORMANCE_FILE = DATA / "agent_performance_report.json"
GROWTH_FILE = DATA / "growth_tweet_drafts.json"
AGENT_RUNS_FILE = DATA / "agent_runs.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_agent_run(row: dict[str, Any]) -> None:
    archive = load_json(AGENT_RUNS_FILE, {"schema_version": "mvp-agent-runs-v1", "runs": []})
    runs = archive.get("runs") or []
    runs.append(row)
    runs = sorted(runs, key=lambda item: item.get("started_at") or "", reverse=True)
    write_json(
        AGENT_RUNS_FILE,
        {
            "schema_version": "mvp-agent-runs-v1",
            "generated_at": now(),
            "count": len(runs),
            "note_ar": "سجل تراكمي لتشغيل Orchestrator والوكلاء. لا يحذف التشغيلات القديمة.",
            "runs": runs,
        },
    )


def pct(value: float) -> int:
    return max(0, min(100, int(round(value))))


def list_from(data: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def text_of(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


WEAK_PATTERNS = [
    "تحديث عملي حول الذكاء الاصطناعي",
    "هذه الإشارة تصبح مفيدة",
    "اعرضها كخبر محفوظ",
    "تحديث AI مرصود",
    "أدوات مرتبطة بالذكاء الاصطناعي",
    "يستحق التجربة",
    "ظهر إطلاق أو تحديث مرتبط",
    "استخدمها كإلهام أولي فقط",
]


def weak_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if any(pattern in text_of(item) for pattern in WEAK_PATTERNS))


def agent_manifest() -> dict[str, Any]:
    agents = [
        {
            "id": "company_scout",
            "name_ar": "وكيل كاشف الشركات",
            "name_en": "Company Scout Agent",
            "purpose_ar": "يرصد شركات ومنتجات AI ويستخرج المنتج، الجمهور، الاستخدامات، وفرص الاستفادة.",
            "inputs": ["source_registry", "signals", "x_focus_accounts", "official_sources"],
            "outputs": ["company_product_signals", "company_cards"],
            "runs": "كل ساعتين وبعد أي تحديث يدوي",
            "failure_policy_ar": "إذا لم يجد مصدرًا موثوقًا يرسل العنصر للمراجعة ولا يعرضه كرصد مؤكد.",
        },
        {
            "id": "model_pulse",
            "name_ar": "وكيل نبض النماذج",
            "name_en": "Model Pulse Agent",
            "purpose_ar": "يراقب النماذج والميزات والأسعار وحدود الاستخدام ويحوّلها إلى تحديث مفهوم.",
            "inputs": ["official_blogs", "model_timeline", "signals"],
            "outputs": ["focused_updates", "model_update_cards"],
            "runs": "كل ساعتين + عند تشغيل الرادار يدويًا",
            "failure_policy_ar": "يعرض آخر نسخة محفوظة مع توضيح أن المصدر لم يتحدث.",
        },
        {
            "id": "market_radar",
            "name_ar": "وكيل رادار السوق",
            "name_en": "Market Radar Agent",
            "purpose_ar": "يرصد مشاريع ومنتجات AI عالمية ومحلية قابلة للاستلهام أو التعريب.",
            "inputs": ["news_sources", "x_cards", "github", "reddit", "product_signals"],
            "outputs": ["market_project_signals", "localization_opportunities"],
            "runs": "يوميًا أو مع تشغيل الرادار الكامل",
            "failure_policy_ar": "لا يحول المشروع إلى فرصة سعودية إلا بوجود جمهور واضح أو مشكلة قابلة للنقل.",
        },
        {
            "id": "opportunity_builder",
            "name_ar": "وكيل صانع الفرص",
            "name_en": "Opportunity Builder Agent",
            "purpose_ar": "يحوّل الإشارات إلى فرص دخل محددة وليست عناوين عامة.",
            "inputs": ["verified_signals", "x_radar_cards", "market_project_signals"],
            "outputs": ["focused_opportunities", "opportunity_cards"],
            "runs": "بعد التحقق والتحرير",
            "failure_policy_ar": "إذا لا توجد مشكلة وجمهور وزاوية دخل، تبقى الإشارة خبرًا أو أرشيفًا.",
        },
        {
            "id": "evidence_guard",
            "name_ar": "وكيل حارس المصادر",
            "name_en": "Evidence Guard Agent",
            "purpose_ar": "يتحقق من المصدر والثقة ويمنع الإشاعات والروابط الضعيفة من الواجهة الرئيسية.",
            "inputs": ["raw_signals", "source_registry"],
            "outputs": ["verified_signals", "review_queue"],
            "runs": "بعد كل جمع",
            "failure_policy_ar": "أي عنصر غير مؤكد يذهب للمراجعة ولا يظهر كحقيقة.",
        },
        {
            "id": "priority_ranker",
            "name_ar": "وكيل ترتيب الأولويات",
            "name_en": "Priority Ranker Agent",
            "purpose_ar": "يرتب البطاقات حسب الثقة، الحداثة، الأثر، والقابلية للبناء.",
            "inputs": ["validated_cards", "source_health", "freshness_state"],
            "outputs": ["ranked_cards", "featured_home_items"],
            "runs": "بعد كل بناء للبطاقات",
            "failure_policy_ar": "يستخدم ترتيبًا احتياطيًا: الثقة ثم الحداثة ثم الأثر.",
        },
        {
            "id": "radar_editor",
            "name_ar": "وكيل محرر الرادار",
            "name_en": "Radar Editor Agent",
            "purpose_ar": "يصيغ البطاقة بالعربية: ماذا حدث، لماذا يهمك، كيف تستفيد، والدليل.",
            "inputs": ["verified_signals", "opportunities", "x_cards"],
            "outputs": ["display_cards", "arabic_first_cards"],
            "runs": "بعد بناء الفرص والتحديثات",
            "failure_policy_ar": "يرفض النص الخام والعناوين العامة ويرسلها لطابور المراجعة.",
        },
        {
            "id": "radar_growth",
            "name_ar": "وكيل نمو وتسويق الرادار",
            "name_en": "Radar Growth Agent",
            "purpose_ar": "يحوّل أفضل الفرص والتحديثات إلى منشورات X وLinkedIn ونشرة بريدية.",
            "inputs": ["top_opportunities", "top_updates", "top_discussions"],
            "outputs": ["growth_tweet_drafts", "linkedin_drafts", "newsletter_hooks"],
            "runs": "بعد كل تحديث ناجح، لكن النشر يحتاج موافقة صريحة.",
            "failure_policy_ar": "لا ينشر تلقائيًا. إذا فشل، يحفظ مسودات غير منشورة فقط.",
        },
        {
            "id": "performance_agent",
            "name_ar": "وكيل تحليل الأداء",
            "name_en": "Performance Agent",
            "purpose_ar": "يقيس جودة المحتوى، تكرار الضعف، حالة المصادر، وفجوات العودة اليومية.",
            "inputs": ["agent_runs", "card_validation_report", "review_queue_summary", "source_runs"],
            "outputs": ["performance_recommendations", "quality_scores"],
            "runs": "بعد كل تشغيل للرادار",
            "failure_policy_ar": "يعطي تقريرًا ناقصًا مع ذكر الأدلة غير المتوفرة.",
        },
        {
            "id": "radar_orchestrator",
            "name_ar": "وكيل منسق الرادار",
            "name_en": "Radar Orchestrator Agent",
            "purpose_ar": "يدير تسلسل الوكلاء ويضمن أن كل بطاقة مرت بالجمع والتحقق والتحرير والترتيب.",
            "inputs": ["agent_config", "source_registry", "run_status"],
            "outputs": ["orchestrator_status", "agent_runs"],
            "runs": "هو نقطة التشغيل الرئيسية",
            "failure_policy_ar": "لا يخفي الفشل؛ يعلّم التشغيل partial أو failed حسب المرحلة.",
        },
        {
            "id": "agent_monitor",
            "name_ar": "وكيل مراقبة أداء الوكلاء",
            "name_en": "Agent Performance Monitor",
            "purpose_ar": "يراقب الوكلاء أنفسهم: من فشل، من ينتج محتوى ضعيفًا، وأين تتوقف السلسلة.",
            "inputs": ["agent_runs", "output_files", "quality_rules"],
            "outputs": ["agent_performance_report", "next_actions"],
            "runs": "بعد كل تشغيل أو عند طلب المراجعة",
            "failure_policy_ar": "يفصل بين فشل المصدر وفشل الصياغة حتى لا يضيع السبب الحقيقي.",
        },
        {
            "id": "tweet_publisher_guard",
            "name_ar": "وكيل حارس النشر على X",
            "name_en": "X Publishing Guard Agent",
            "purpose_ar": "يراجع مسودات التسويق قبل التغريد ويتأكد أنها لا تبالغ ولا تنشر معلومة غير موثقة.",
            "inputs": ["growth_tweet_drafts", "source_evidence", "publishing_policy"],
            "outputs": ["approved_tweet_drafts", "blocked_tweets"],
            "runs": "بعد وكيل النمو وقبل أي نشر",
            "failure_policy_ar": "الوضع الافتراضي مسودات فقط. النشر الفعلي يحتاج تفعيل وموافقة.",
        },
    ]
    return {
        "schema_version": "radar-agent-manifest-v1",
        "generated_at": now(),
        "principle_ar": "كل وكيل له دور محدد. لا توجد بطاقة رئيسية بدون مصدر، ثقة، وصياغة مفهومة.",
        "publishing_policy_ar": "وكيل التسويق يكتب مسودات فقط. لا يغرد تلقائيًا إلا عند تفعيل صريح لاحقًا.",
        "agents": agents,
    }


def build_performance_report() -> dict[str, Any]:
    run_status = load_json(DATA / "run_status.json", {})
    source_runs = load_json(DATA / "source_runs.json", {})
    validation = load_json(DATA / "card_validation_report.json", {})
    review = load_json(DATA / "review_queue_summary.json", {})
    agent_runs = load_json(DATA / "agent_runs.json", {"runs": []})
    opportunities = list_from(load_json(DATA / "focused_opportunities.json", {}), "opportunities")
    updates = list_from(load_json(DATA / "focused_updates.json", {}), "updates")
    discussions = list_from(load_json(DATA / "focused_discussions.json", {}), "discussions")
    x_cards = list_from(load_json(MANUAL_X / "x_radar_cards.json", {}), "cards")
    openai_cards = load_json(DATA / "openai_intelligence_cards.json", {})

    files = {
        "فرص الدخل": opportunities,
        "ما الجديد اليوم": updates,
        "ماذا يتحدث الناس عنه": discussions,
        "بطاقات X": x_cards,
    }
    section_scores = {}
    for name, items in files.items():
        total = len(items)
        weak = weak_count(items)
        if total == 0:
            score = 35 if name == "ما الجديد اليوم" else 45
            note = "القسم فارغ أو لا يملك بطاقات مركزة."
        else:
            score = pct(100 - (weak / total) * 75)
            note = "مقبول" if weak == 0 else f"يحتاج تنظيف: {weak} بطاقة تحمل صياغة عامة."
        section_scores[name] = {
            "count": total,
            "weak_count": weak,
            "score": score,
            "note_ar": note,
        }

    runs = agent_runs.get("runs") or []
    recent = runs[:20]
    failed = [r for r in recent if r.get("status") == "failed"]
    partial = [r for r in recent if r.get("status") == "partial"]

    openai_status = openai_cards.get("status", "missing")
    openai_score = 35 if openai_status == "skipped" else 80 if openai_cards.get("card_count", 0) else 50
    quality_score = pct(
        (
            section_scores["فرص الدخل"]["score"]
            + section_scores["ما الجديد اليوم"]["score"]
            + section_scores["ماذا يتحدث الناس عنه"]["score"]
            + section_scores["بطاقات X"]["score"]
            + openai_score
        )
        / 5
    )

    next_actions = []
    if not updates:
        next_actions.append("تشغيل وكيل نبض النماذج/ما الجديد اليوم لأن القسم لا يملك تحديثات مركزة.")
    if openai_status == "skipped" or openai_cards.get("card_count", 0) == 0:
        next_actions.append("تشغيل طبقة OpenAI Intelligence بعد التأكد من وجود OPENAI_API_KEY.")
    if section_scores["بطاقات X"]["weak_count"] > 0:
        next_actions.append("إعادة تحرير بطاقات X العامة قبل عرضها في الواجهة الرئيسية.")
    if review.get("total_pending", 0):
        next_actions.append(f"مراجعة {review.get('total_pending')} عنصرًا في طابور المراجعة أو إبقاؤها خارج الرئيسية.")
    if run_status.get("sources_failed"):
        next_actions.append("إظهار فشل المصادر للمستخدم ومتابعة آخر نسخة محفوظة بدون ادعاء أنها مباشرة.")

    return {
        "schema_version": "radar-agent-performance-v1",
        "generated_at": now(),
        "overall_score": quality_score,
        "verdict_ar": "جزئيًا جاهز: البنية تعمل، لكن ذكاء التحرير والتسويق يحتاجان تفعيلًا أقوى."
        if quality_score < 75
        else "جيد: المنظومة تعمل وتحتاج تحسينات جودة دورية.",
        "source_health": {
            "run_status": run_status.get("status"),
            "started_at": run_status.get("started_at"),
            "finished_at": run_status.get("finished_at"),
            "sources_succeeded": len(run_status.get("sources_succeeded") or []),
            "sources_failed": len(run_status.get("sources_failed") or []),
            "skipped_sources": len(run_status.get("skipped_sources") or []),
            "source_runs_count": source_runs.get("count", 0),
        },
        "section_scores": section_scores,
        "validation": {
            "total_cards": validation.get("total_cards", 0),
            "valid_count": validation.get("valid_count", 0),
            "rejected_count": validation.get("rejected_count", 0),
            "review_pending": review.get("total_pending", 0),
        },
        "openai_intelligence": {
            "status": openai_status,
            "card_count": openai_cards.get("card_count", 0),
            "skipped_reason": openai_cards.get("skipped_reason", ""),
        },
        "recent_agent_runs": [
            {
                "agent_name": r.get("agent_name"),
                "status": r.get("status"),
                "started_at": r.get("started_at"),
                "output_count": r.get("output_count"),
                "error_message": (r.get("error_message") or "")[:300],
            }
            for r in recent[:12]
        ],
        "issues_ar": [
            "قسم ما الجديد اليوم فارغ من التحديثات المركزة." if not updates else "",
            "بطاقات X فيها صياغات عامة كثيرة." if section_scores["بطاقات X"]["weak_count"] else "",
            "OpenAI Intelligence لم ينتج بطاقات بعد." if openai_cards.get("card_count", 0) == 0 else "",
            "يوجد فشل/تقييد في بعض المصادر." if run_status.get("sources_failed") else "",
        ],
        "next_actions_ar": next_actions,
        "failed_recent_runs": len(failed),
        "partial_recent_runs": len(partial),
    }


def clean_line(value: str, limit: int = 230) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    value = value.replace("الرادار الرادار", "الرادار")
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def pick_top_opportunities() -> list[dict[str, Any]]:
    opportunities = list_from(load_json(DATA / "focused_opportunities.json", {}), "opportunities")
    return sorted(opportunities, key=lambda item: item.get("confidence_score") or item.get("confidence") or 0, reverse=True)[:4]


def pick_top_discussions() -> list[dict[str, Any]]:
    discussions = list_from(load_json(DATA / "focused_discussions.json", {}), "discussions")
    return sorted(discussions, key=lambda item: item.get("confidence_score") or item.get("signal_count") or 0, reverse=True)[:3]


def build_tweet_drafts(performance: dict[str, Any]) -> dict[str, Any]:
    opportunities = pick_top_opportunities()
    discussions = pick_top_discussions()
    drafts = []

    for idx, item in enumerate(opportunities, 1):
        title = item.get("title_ar") or item.get("title") or "فرصة AI قابلة للبناء"
        problem = item.get("problem_ar") or item.get("problem") or item.get("summary_ar") or ""
        use = item.get("how_to_use_ar") or item.get("how_to_use") or ""
        evidence = item.get("evidence_count_total") or item.get("evidence_count") or len(item.get("evidence_items") or [])
        text = "\n".join(
            [
                f"فرصة من الرادار: {clean_line(title, 90)}",
                "",
                f"المشكلة: {clean_line(problem, 150)}" if problem else "",
                f"كيف تستفيد؟ {clean_line(use, 150)}" if use else "",
                f"الدليل: {evidence} إشارات" if evidence else "الدليل: إشارات مرصودة من مصادر الرادار",
                "",
                "الرادار لا يكتفي بخبر AI؛ يحاول كشف الفرصة خلفه.",
            ]
        )
        drafts.append(
            {
                "id": f"growth-opportunity-{idx}",
                "platform": "x",
                "status": "draft_only",
                "source_card_id": item.get("id"),
                "goal_ar": "جذب المهتمين بفرص الدخل من الذكاء الاصطناعي.",
                "tweet_ar": clean_line(text, 900),
                "safety_note_ar": "مسودة فقط؛ لا تنشر قبل مراجعة الرابط والدليل.",
            }
        )

    for idx, item in enumerate(discussions, 1):
        title = item.get("title_ar") or item.get("title") or "نقاش AI صاعد"
        pain = item.get("pain_point_ar") or item.get("pain_ar") or item.get("what_people_say_ar") or ""
        signal = item.get("business_signal_ar") or item.get("opportunity_ar") or item.get("why_it_matters_ar") or ""
        text = "\n".join(
            [
                f"ماذا يقول الناس عن AI؟ {clean_line(title, 90)}",
                "",
                f"الألم المتكرر: {clean_line(pain, 150)}" if pain else "",
                f"الإشارة التجارية: {clean_line(signal, 160)}" if signal else "",
                "",
                "هذه هي وظيفة الرادار: تحويل الضجيج إلى إشارة قابلة للفهم.",
            ]
        )
        drafts.append(
            {
                "id": f"growth-discussion-{idx}",
                "platform": "x",
                "status": "draft_only",
                "source_card_id": item.get("id"),
                "goal_ar": "شرح قيمة الرادار كفلتر للنقاشات الاجتماعية.",
                "tweet_ar": clean_line(text, 900),
                "safety_note_ar": "مسودة فقط؛ لا تنشر قبل مراجعة المصادر.",
            }
        )

    score = performance.get("overall_score", 0)
    drafts.append(
        {
            "id": "growth-product-positioning-1",
            "platform": "x",
            "status": "draft_only",
            "goal_ar": "تعريف المنتج بدون مبالغة.",
            "tweet_ar": clean_line(
                "\n".join(
                    [
                        "الرادار ليس تطبيق أخبار AI.",
                        "",
                        "فكرته أبسط وأهم:",
                        "1. يرصد ما يحدث في الذكاء الاصطناعي",
                        "2. يتحقق من المصدر",
                        "3. يشرح لماذا يهمك",
                        "4. يحاول تحويل الإشارة إلى فرصة قابلة للبناء",
                        "",
                        f"حالة الجودة الحالية داخليًا: {score}/100، وما زلنا نطوره.",
                    ]
                ),
                900,
            ),
            "safety_note_ar": "مناسب للنشر عند الرغبة في بناء الجمهور علنًا.",
        }
    )

    return {
        "schema_version": "radar-growth-drafts-v1",
        "generated_at": now(),
        "publishing_mode": "draft_only",
        "note_ar": "هذه مسودات يكتبها وكيل النمو. لا يوجد نشر تلقائي على X في هذه النسخة.",
        "draft_count": len(drafts),
        "drafts": drafts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Radar agent suite")
    parser.add_argument("--no-growth", action="store_true", help="Skip growth tweet drafts.")
    args = parser.parse_args()

    started_at = now()
    manifest = agent_manifest()
    performance = build_performance_report()
    write_json(MANIFEST_FILE, manifest)
    write_json(PERFORMANCE_FILE, performance)

    if not args.no_growth:
        growth = build_tweet_drafts(performance)
        write_json(GROWTH_FILE, growth)
    else:
        growth = {"draft_count": 0}

    finished_at = now()
    append_agent_run(
        {
            "id": f"agent_suite:{started_at}",
            "run_id": f"agent-suite-{started_at.replace(':', '').replace('+', 'Z')}",
            "agent_name": "Agent Performance Monitor",
            "started_at": started_at,
            "finished_at": finished_at,
            "status": "success",
            "input_count": 6,
            "output_count": 3 if not args.no_growth else 2,
            "error_message": "",
            "mode": "agent_suite_monitoring",
            "outputs": [
                str(MANIFEST_FILE.relative_to(ROOT)),
                str(PERFORMANCE_FILE.relative_to(ROOT)),
                str(GROWTH_FILE.relative_to(ROOT)) if not args.no_growth else "",
            ],
        }
    )

    print(
        json.dumps(
            {
                "status": "success",
                "agents": len(manifest["agents"]),
                "overall_score": performance["overall_score"],
                "growth_drafts": growth.get("draft_count", 0),
                "manifest": str(MANIFEST_FILE.relative_to(ROOT)),
                "performance_report": str(PERFORMANCE_FILE.relative_to(ROOT)),
                "growth_drafts_file": str(GROWTH_FILE.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
