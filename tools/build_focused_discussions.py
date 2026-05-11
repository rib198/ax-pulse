#!/usr/bin/env python3
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freshness import (  # noqa: E402
    annotate_card,
    load_freshness_state,
    parse_iso,
    save_freshness_state,
    now_utc,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MANUAL_X_DIR = DATA_DIR / "manual_x"
READY_FILE = MANUAL_X_DIR / "radar_ready_posts.json"
CURATED_FILE = MANUAL_X_DIR / "curated_opportunities.json"
BRIEF_FILE = MANUAL_X_DIR / "x_brief.json"
OUTPUT_FILE = DATA_DIR / "radar" / "focused_discussions.json"


DISCUSSION_THEMES = [
    {
        "id": "agentic_work_operating_system",
        "keywords": ["agent", "agents", "agentic", "claude code", "codex", "وكلاء", "وكيل", "تشغيل", "workflow"],
        "title_ar": "الناس لا يريدون شات جديدًا؛ يريدون نظام عمل بالوكلاء",
        "title_en": "People do not want another chat; they want an agent work system",
        "what_people_say_ar": "النقاشات تدور حول تحويل Claude Code والوكلاء إلى طريقة تشغيل يومية: تقسيم مهام، متابعة، بناء منتجات، وإنجاز شبه مستقل.",
        "what_people_say_en": "The discussion is about turning Claude Code and agents into a daily operating workflow: task splitting, follow-up, product building, and semi-autonomous execution.",
        "pain_ar": "الألم المتكرر: المستخدم يسمع عن الوكلاء لكنه لا يعرف كيف يجعلها نظامًا عمليًا داخل مشروعه أو فريقه.",
        "pain_en": "Repeated pain: users hear about agents but do not know how to turn them into a practical system inside a project or team.",
        "business_signal_ar": "إشارة تجارية: باقات تشغيل وتدريب وقوالب جاهزة للفرق الصغيرة قد تكون أسهل للبيع من أداة عامة.",
        "business_signal_en": "Business signal: operating kits, training, and templates for small teams may be easier to sell than a generic tool.",
        "radar_take_ar": "راقب أي منشور يشرح طريقة تشغيل أو قالبًا أو تجربة قبل/بعد، لأن هذا أقرب لفرصة دخل من خبر عام.",
        "radar_take_en": "Watch posts that explain an operating method, template, or before/after workflow because they are closer to income opportunities than generic news.",
    },
    {
        "id": "ai_income_micro_services",
        "keywords": ["income", "money", "google maps", "website", "business", "دخل", "موقع", "خرائط", "متاجر", "شركات"],
        "title_ar": "يتداول الناس أفكار دخل صغيرة مبنية على AI وليس شركات ضخمة",
        "title_en": "People are sharing small AI income ideas, not only big startups",
        "what_people_say_ar": "ظهرت نقاشات عن العثور على أعمال لديها طلب واضح ثم استخدام AI لبناء موقع أو عرض سريع لها.",
        "what_people_say_en": "Discussions appeared around finding businesses with visible demand, then using AI to build a quick website or offer for them.",
        "pain_ar": "الألم المتكرر: أصحاب المشاريع الصغيرة لا يملكون موقعًا أو محتوى واضحًا، والمستقل لا يعرف أين يجد أول عميل.",
        "pain_en": "Repeated pain: small businesses lack a clear website or content, and freelancers do not know where to find the first customer.",
        "business_signal_ar": "إشارة تجارية: خدمات صغيرة قابلة للبيع بسرعة مثل موقع بسيط، صفحة هبوط، أو محتوى مبيعات مدعوم بـ AI.",
        "business_signal_en": "Business signal: small sellable services like a simple site, landing page, or AI-powered sales content.",
        "radar_take_ar": "لا تعرضها كنصيحة عامة للربح؛ اعرضها كمنهج: مصدر عملاء + ألم واضح + مخرجات AI قابلة للبيع.",
        "radar_take_en": "Do not show it as generic money advice; show it as a method: lead source + clear pain + sellable AI output.",
    },
    {
        "id": "design_context_for_agents",
        "keywords": ["design", "ui", "ux", "dashboard", "slides", "تصميم", "واجهة", "واجهات", "claude design", "canvas"],
        "title_ar": "النقاش حول التصميم يقول إن الوكلاء يحتاجون سياقًا بصريًا أفضل",
        "title_en": "The design discussion says agents need better visual context",
        "what_people_say_ar": "يتحدث الناس عن أدوات وتصاميم تساعد الوكلاء على توليد واجهات ولوحات وشرائح بجودة أعلى.",
        "what_people_say_en": "People are discussing tools and design systems that help agents generate better interfaces, dashboards, and slides.",
        "pain_ar": "الألم المتكرر: AI يبني الواجهة بسرعة، لكن النتيجة قد تكون ضعيفة إذا لم يحصل على أمثلة وقواعد تصميم واضحة.",
        "pain_en": "Repeated pain: AI builds UI quickly, but output can look weak without examples and clear design rules.",
        "business_signal_ar": "إشارة تجارية: حزم سياق تصميم، ملفات قواعد، ومكتبات أمثلة يمكن بيعها للمطورين ومؤسسي SaaS.",
        "business_signal_en": "Business signal: design context packs, rule files, and example libraries can be sold to builders and SaaS founders.",
        "radar_take_ar": "هذا النقاش لا يعني أداة واحدة فقط؛ يعني أن السوق يحتاج مواد توجيه تجعل الوكلاء ينتجون بشكل احترافي.",
        "radar_take_en": "This discussion is not about one tool only; it means the market needs guidance assets that make agents produce professional output.",
    },
    {
        "id": "voice_localization",
        "keywords": ["voice", "audio", "dubbing", "clone", "podcast", "صوت", "دبلجة", "استنساخ", "ترجمة", "فيديو"],
        "title_ar": "الصوت والدبلجة يتكرران كنقاش حول إعادة استخدام المحتوى",
        "title_en": "Voice and dubbing repeat as a discussion about repurposing content",
        "what_people_say_ar": "النقاشات تشير إلى أدوات تجمع التفريغ والترجمة واستنساخ الصوت والدبلجة في مسار واحد.",
        "what_people_say_en": "Discussions point to tools combining transcription, translation, voice cloning, and dubbing in one workflow.",
        "pain_ar": "الألم المتكرر: صناع المحتوى والشركات لديهم فيديوهات كثيرة لكن إعادة إنتاجها بلغات ولهجات مختلفة مكلفة.",
        "pain_en": "Repeated pain: creators and companies have many videos, but reproducing them across languages and dialects is expensive.",
        "business_signal_ar": "إشارة تجارية: خدمة تعريب ودبلجة محتوى قصير مع ملفات نشر جاهزة.",
        "business_signal_en": "Business signal: Arabic localization and dubbing service for short content with publish-ready assets.",
        "radar_take_ar": "الفرصة ليست في ذكر الأداة فقط؛ بل في تقديم مخرج واضح: نسخة صوتية/مدبلجة قابلة للنشر.",
        "radar_take_en": "The opportunity is not just naming the tool; it is delivering a clear output: publishable voiced or dubbed versions.",
    },
    {
        "id": "trend_to_micro_app",
        "keywords": ["trend", "trends", "keyword", "app", "ship", "ترند", "تطبيق", "كلمات", "إطلاق"],
        "title_ar": "هناك اهتمام بتحويل الترندات إلى تطبيقات صغيرة بسرعة",
        "title_en": "There is interest in turning trends into small apps quickly",
        "what_people_say_ar": "بعض الإشارات تربط بين الترندات والكلمات منخفضة المنافسة وإطلاق تطبيق بسيط خلال وقت قصير.",
        "what_people_say_en": "Some signals connect trends, low-competition keywords, and shipping a small app quickly.",
        "pain_ar": "الألم المتكرر: الناس ترى الترند بعد فوات الوقت ولا تعرف كيف تختبر الفكرة قبل بناء منتج كبير.",
        "pain_en": "Repeated pain: people see trends too late and do not know how to test the idea before building a large product.",
        "business_signal_ar": "إشارة تجارية: نشرة أو مختبر أسبوعي يحول الترند إلى فكرة تطبيق وصفحة اختبار.",
        "business_signal_en": "Business signal: a weekly brief or lab that turns trends into app ideas and validation pages.",
        "radar_take_ar": "اعرض النقاش كمنهج رصد، لا كقائمة ترندات: ما ظهر، لماذا له طلب، وكيف نختبره.",
        "radar_take_en": "Show this as a detection method, not a trend list: what appeared, why demand exists, and how to test it.",
    },
    {
        "id": "ai_tool_cost_value",
        "keywords": ["cost", "price", "pricing", "subscription", "credits", "اشتراك", "تكلفة", "رصيد", "مجاني", "مدفوع"],
        "title_ar": "نقاش التكلفة والقيمة يظهر مع كثرة أدوات AI المدفوعة",
        "title_en": "Cost and value discussions are rising as paid AI tools multiply",
        "what_people_say_ar": "تظهر إشارات عن الاشتراكات والرصيد والأدوات المجانية أو المدفوعة، لكنها غالبًا تحتاج تحققًا وسياقًا.",
        "what_people_say_en": "Signals mention subscriptions, credits, free tools, and paid tools, but often need verification and context.",
        "pain_ar": "الألم المتكرر: المستخدم يدفع لأدوات كثيرة ولا يعرف متى تستحق الأداة أو النموذج التكلفة.",
        "pain_en": "Repeated pain: users pay for many tools and do not know when a tool or model is worth the cost.",
        "business_signal_ar": "إشارة تجارية: حاسبة قيمة أو دليل اختيار أداة حسب المهمة والتكلفة.",
        "business_signal_en": "Business signal: a value calculator or tool-selection guide by task and cost.",
        "radar_take_ar": "تعامل بحذر مع ادعاءات المجاني والقوي؛ اعرضها كمؤشر يحتاج مصدرًا لا كحقيقة مطلقة.",
        "radar_take_en": "Treat free/powerful claims carefully; show them as a signal needing evidence, not as a fact.",
    },
]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def source_url(item):
    return item.get("url") or item.get("source_url") or ""


def discussion_text(item):
    return norm(" ".join(str(item.get(key) or "") for key in [
        "title_ar", "title_en", "summary_ar", "why_it_matters_ar", "mvp_ar",
        "text", "category_ar", "category_en", "customer_ar", "reason_ar", "id"
    ]))


def theme_score(item, theme):
    text = discussion_text(item)
    return sum(2 if len(norm(kw)) > 5 else 1 for kw in theme["keywords"] if norm(kw) in text)


def best_theme(item):
    scored = sorted(((theme_score(item, theme), theme) for theme in DISCUSSION_THEMES), key=lambda row: row[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] > 0 else None


def collect_items():
    ready = load_json(READY_FILE, {"accepted": []})
    curated = load_json(CURATED_FILE, {"opportunities": []})
    brief = load_json(BRIEF_FILE, {"opportunities": []})
    items = []
    for item in ready.get("accepted", []):
        items.append({
            **item,
            "origin": "radar_ready_posts",
            "source_label": f"X · @{item.get('author_handle') or 'source'}",
            "evidence_title": item.get("summary_ar") or item.get("text", "")[:120],
            "confidence": number(item.get("quality_score")) or 0.62,
        })
    for item in curated.get("opportunities", []):
        evidence = item.get("evidence_items") or []
        items.append({
            **item,
            "origin": "curated_opportunities",
            "source_label": "X · curated discussion",
            "text": " ".join(ev.get("text", "") for ev in evidence[:3]),
            "url": next((ev.get("url") for ev in evidence if ev.get("url")), ""),
            "evidence_title": item.get("title_ar") or item.get("title_en") or "",
            "confidence": number(item.get("confidence")) or 0.64,
        })
    for item in brief.get("opportunities", []):
        evidence = item.get("evidence_items") or []
        items.append({
            **item,
            "origin": "x_brief",
            "source_label": "X · brief",
            "text": " ".join(ev.get("text", "") for ev in evidence[:3]),
            "url": next((ev.get("url") for ev in evidence if ev.get("url")), ""),
            "evidence_title": item.get("title_ar") or "",
            "confidence": number(item.get("confidence")) or 0.58,
        })
    return items


def unique_items(items):
    seen = set()
    out = []
    for item in items:
        key = item.get("tweet_id") or item.get("id") or source_url(item) or item.get("evidence_title")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def make_discussion(theme, items):
    items = unique_items(items)
    if len(items) < 1:
        return None
    items.sort(key=lambda item: (number(item.get("confidence")), number(item.get("quality_score")), item.get("collected_at") or ""), reverse=True)
    evidence_items = items[:6]
    source_links = []
    for index, item in enumerate(evidence_items, start=1):
        label = item.get("source_label") or "X"
        title = item.get("evidence_title") or item.get("summary_ar") or item.get("title_ar") or item.get("text", "")[:120]
        source_links.append({
            "label_ar": f"دليل {index}: {label}",
            "label_en": f"Evidence {index}: {label}",
            "source": label,
            "url": source_url(item),
            "title": title,
            "detected_at": item.get("collected_at") or item.get("generated_at") or "",
        })
    confidence_values = [number(item.get("confidence")) or number(item.get("quality_score")) for item in evidence_items]
    avg = sum(confidence_values) / len(confidence_values) if confidence_values else 0.6
    confidence_score = max(54, min(92, round(avg * 100 + min(len(items), 6) * 2)))
    importance_score = max(50, min(94, round(confidence_score * 0.72 + min(len(items), 8) * 4)))
    return {
        "id": f"focused_discussion:{theme['id']}",
        "kind": "focused_discussion",
        "title_ar": theme["title_ar"],
        "title_en": theme["title_en"],
        "what_people_say_ar": theme["what_people_say_ar"],
        "what_people_say_en": theme["what_people_say_en"],
        "pain_ar": theme["pain_ar"],
        "pain_en": theme["pain_en"],
        "business_signal_ar": theme["business_signal_ar"],
        "business_signal_en": theme["business_signal_en"],
        "radar_take_ar": theme["radar_take_ar"],
        "radar_take_en": theme["radar_take_en"],
        "confidence_score": confidence_score,
        "importance_score": importance_score,
        "evidence_count": len(items),
        "source_links": source_links,
        "display_status": "cached",
        "detected_at": max((item.get("collected_at") or "" for item in evidence_items), default=""),
        "why_selected_ar": f"اختير لأن {len(items)} إشارات اجتماعية تدور حول نفس الألم أو الاهتمام، مع روابط قابلة للمراجعة.",
        "why_selected_en": f"Selected because {len(items)} social signals point to the same pain or interest, with reviewable links.",
    }


def _has_recent_evidence(items, hours=24):
    """True if any item has collected_at within the given window."""
    cutoff = now_utc().timestamp() - hours * 3600
    for item in items:
        when = parse_iso(item.get("collected_at") or item.get("posted_at"))
        if when and when.timestamp() >= cutoff:
            return True
    return False


def build():
    items = collect_items()
    grouped = defaultdict(list)
    unclassified = []
    for item in items:
        theme = best_theme(item)
        if theme:
            grouped[theme["id"]].append(item)
        else:
            unclassified.append(item)
    discussions = []
    freshness_state = load_freshness_state()
    for theme in DISCUSSION_THEMES:
        bucket = grouped.get(theme["id"], [])
        discussion = make_discussion(theme, bucket)
        if not discussion:
            continue
        # Annotate freshness using the underlying social items as evidence
        annotate_card(discussion, freshness_state, evidence=bucket)
        discussions.append(discussion)
    save_freshness_state(freshness_state)

    # Sort by freshness then importance
    freshness_priority = {
        "breaking": 0, "new_today": 1, "refreshed_today": 2,
        "this_week": 3, "older": 4,
    }
    discussions.sort(
        key=lambda d: (
            freshness_priority.get(d.get("freshness", "older"), 9),
            -d["importance_score"],
            -d["confidence_score"],
            -d["evidence_count"],
        )
    )
    output = {
        "schema_version": "focused-discussions-v2",
        "generated_at": now(),
        "source_files": [
            str(READY_FILE.relative_to(ROOT)),
            str(CURATED_FILE.relative_to(ROOT)),
            str(BRIEF_FILE.relative_to(ROOT)),
        ],
        "total_social_items": len(items),
        "total_discussions": len(discussions),
        "fresh_24h_count": sum(1 for d in discussions if d.get("freshness") in {"breaking", "new_today", "refreshed_today"}),
        "unclassified_count": len(unclassified),
        "note_ar": "ملخصات نقاش اجتماعي مبنية من إشارات X — كل بطاقة لها freshness label.",
        "discussions": discussions,
    }
    write_json(OUTPUT_FILE, output)
    return output


def main():
    output = build()
    print(json.dumps({
        "output": str(OUTPUT_FILE.relative_to(ROOT)),
        "total_discussions": output["total_discussions"],
        "total_social_items": output["total_social_items"],
        "unclassified_count": output["unclassified_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
