#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "data" / "manual_x" / "posts.json"
OUT = ROOT / "data" / "manual_x" / "radar_ready_posts.json"


AI_TERMS = [
    "ai", "gpt", "gpt-5", "gpt-5.5", "claude", "chatgpt", "gemini", "llm",
    "agent", "agents", "automation", "n8n", "cursor", "codex", "sora", "veo",
    "midjourney", "runway", "hugging face", "voice cloning", "dubbing",
    "ذكاء", "كلاود", "شات", "وكلاء", "أتمت", "بوتات", "نماذج"
]

PRODUCT_TERMS = [
    "income", "app ideas", "build", "tool", "tools", "startup", "mvp", "service",
    "workflow", "automate", "design", "slides", "cad", "website", "course",
    "مصدر دخل", "دخل", "أدوات", "ابن", "أتمت", "موقع", "دورة", "أنظمة"
]

NEWS_TERMS = [
    "released", "launch", "breaking", "available", "free", "update", "model",
    "إطلاق", "أطلقنا", "تحديث", "متاح", "مجاني"
]

REJECT_TERMS = [
    "ad\n", "peptazol", "bsf", "kyan", "steam", "subscribe to premium",
    "terms of service", "privacy policy", "who to follow"
]


def load_posts():
    if not POSTS.exists():
        return []
    return json.loads(POSTS.read_text(encoding="utf-8")).get("items", [])


def clean_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text or "").strip()
    text = re.sub(r"(Subscribe to Premium|Terms of Service|Privacy Policy).*", "", text, flags=re.I | re.S)
    return text[:1100].strip()


def has_any(text, terms):
    low = text.lower()
    return any(term.lower() in low for term in terms)


def classify(item):
    text = clean_text(item.get("text", ""))
    low = text.lower()
    if not text or has_any(text, REJECT_TERMS) or item.get("author_handle") in {"PeptazolSA", "BSF_sa", "KYANcafe", "rogueducknet", "makkaheye_sa"}:
        return "reject", "إعلان أو محتوى غير مناسب لهدف المنتج", 0.0

    score = 0.0
    reasons = []
    if has_any(text, AI_TERMS):
        score += 0.42
        reasons.append("مرتبط بالذكاء الاصطناعي")
    if has_any(text, PRODUCT_TERMS):
        score += 0.28
        reasons.append("يمكن أن يلهم منتجًا أو خدمة")
    if has_any(text, NEWS_TERMS):
        score += 0.14
        reasons.append("يتضمن تحديثًا أو إطلاقًا أو أداة")
    if item.get("pain_signal_score", 0) >= 0.2:
        score += 0.12
        reasons.append("فيه ألم/فرصة تشغيلية")
    if re.search(r"\b(likes|bookmarks|views|reposts)\b|مشاهد|إعجاب|حفظ", low):
        score += 0.04
        reasons.append("يحمل مؤشر تفاعل")

    if score >= 0.58:
        return "accept", "، ".join(reasons[:3]), round(min(score, 1), 2)
    if score >= 0.42:
        return "archive", "مرتبط جزئيًا لكنه يحتاج تحققًا أو سياقًا أكثر", round(score, 2)
    return "reject", "لا يخدم أخبار AI أو الرائج أو أفكار المنتجات بشكل كافٍ", round(score, 2)


def category_for(text):
    low = text.lower()
    if any(term in low for term in ["income", "app ideas", "website", "مصدر دخل", "دخل"]):
        return "product_ideas"
    if any(term in low for term in ["released", "launch", "breaking", "update", "إطلاق", "تحديث"]):
        return "radar_updates"
    if any(term in low for term in ["likes", "bookmarks", "views", "reposts", "مشاهد"]):
        return "trending"
    return "archive"


def source_url_for(item):
    url = (item.get("url") or "").strip()
    if url and url != "-":
        return url
    tweet_id = str(item.get("tweet_id") or "").strip()
    handle = str(item.get("author_handle") or "").strip().lstrip("@")
    if tweet_id and handle:
        return f"https://x.com/{handle}/status/{tweet_id}"
    if tweet_id:
        return f"https://x.com/i/web/status/{tweet_id}"
    return ""


def insight_for(item, category, score):
    text = clean_text(item.get("text", ""))
    low = text.lower()
    handle = item.get("author_handle") or "X"
    base = {
        "summary_ar": f"إشارة من @{handle}: محتوى مرتبط بأداة أو استخدام للذكاء الاصطناعي ويحتاج تسمية أوضح قبل رفعه كفرصة قوية.",
        "why_it_matters_ar": "تهمك لأنها تكشف اهتمامًا أو ألمًا أو أداة بدأت تظهر في محادثات المستخدمين.",
        "product_opportunity_ar": "استخدمها كإلهام أولي فقط، واحتفظ بها كفكرة مبكرة حتى تظهر أدلة إضافية.",
        "confidence": score,
    }
    if "chatgpt-image2" in low or "brand visual identity" in low:
        base.update({
            "summary_ar": "ChatGPT-Image2 يمكن استخدامه لتوليد حزمة هوية بصرية كاملة من اسم العلامة وتموضعها: غلاف، نظام تمييز، تغليف، ومشاهد استخدام.",
            "why_it_matters_ar": "تهمك لأنها تحول التصميم إلى خدمة سريعة قابلة للبيع للمتاجر والمطاعم والمنتجات الجديدة.",
            "product_opportunity_ar": "باقة “هوية بصرية خلال يوم” تشمل صور إعلان، تغليف، وقوالب نشر للمتاجر الصغيرة.",
        })
    elif "claude code design" in low or "ui/ux designs" in low:
        base.update({
            "summary_ar": "أداة تصميم محلية شبيهة بـ Claude Code Design تولّد واجهات ولوحات وشرائح وتعمل محليًا بدون إخراج البيانات.",
            "why_it_matters_ar": "تكشف طلبًا واضحًا على أدوات تصميم AI آمنة ومحلية، خصوصًا للفرق التي لا تريد إرسال بياناتها للخارج.",
            "product_opportunity_ar": "حزمة عربية لتوليد واجهات وتقارير وشرائح محليًا مع قوالب جاهزة للشركات والمدربين.",
        })
    elif "google maps" in low and "website" in low:
        base.update({
            "summary_ar": "فكرة خدمة: العثور على شركات لديها تقييمات جيدة في خرائط Google ولا تملك موقعًا، ثم بناء موقع سريع لها باستخدام AI.",
            "why_it_matters_ar": "الألم واضح والعميل معروف والنتيجة قابلة للعرض؛ لذلك تناسب هدف المنتج في إلهام دخل عملي.",
            "product_opportunity_ar": "خدمة “موقع خلال 48 ساعة” للمحلات والعيادات والمطاعم الصغيرة مع نصوص وصور محسنة بالذكاء الاصطناعي.",
        })
    elif "python" in low and ("node.js" in low or "react" in low):
        base.update({
            "summary_ar": "ألم تقني: مطورو الويب يريدون بناء وكلاء AI دون اضطرار لبناء خدمات Python جانبية.",
            "why_it_matters_ar": "هذه ليست ضجة عامة؛ إنها شريحة مستخدمين واضحة ومشكلة قابلة للتحويل إلى أداة أو SDK.",
            "product_opportunity_ar": "قوالب أو SDK لبناء وكلاء AI في Node/React مع تكاملات وأمثلة جاهزة.",
        })
    elif "voice-pro" in low or "voice cloning" in low or "dubbing" in low:
        base.update({
            "summary_ar": "أداة تجمع الاستنساخ الصوتي والتفريغ وعزل الصوت والدبلجة لأكثر من لغة ضمن مسار واحد.",
            "why_it_matters_ar": "تخفض تكلفة تعريب ودبلجة المحتوى، وهذا يفتح فرصًا لصناع المحتوى والتعليم والتسويق.",
            "product_opportunity_ar": "خدمة تعريب فيديوهات تعليمية وتسويقية مع صوت قريب من المتحدث الأصلي.",
        })
    elif "agentic engineering" in low or "ai agents" in low or "وكلاء" in low:
        base.update({
            "summary_ar": "إشارة حول تزايد الاهتمام بتعلّم بناء المنتجات وسير العمل باستخدام وكلاء الذكاء الاصطناعي.",
            "why_it_matters_ar": "السوق لا يبحث عن أداة فقط، بل عن طريقة تشغيل وقوالب تساعده يبني وينظم العمل بالوكلاء.",
            "product_opportunity_ar": "قوالب تشغيل عربية للفرق الصغيرة: تقسيم مهام، قواعد مشروع، ومتابعة تنفيذ عبر وكلاء AI.",
        })
    elif "cad" in low or "forgecad" in low:
        base.update({
            "summary_ar": "اتجاه نحو CAD موجه بالكود ومدعوم بنماذج لغوية لتسهيل التصميم الصناعي ثلاثي الأبعاد.",
            "why_it_matters_ar": "يفتح زاوية دخل خارج المحتوى والتسويق، باتجاه التصميم الصناعي والمنتجات الفيزيائية.",
            "product_opportunity_ar": "خدمة تحويل وصف المنتج إلى نموذج CAD أولي للشركات الصغيرة والمصممين.",
        })
    elif "slides" in low or "open-slide" in low:
        base.update({
            "summary_ar": "أداة تساعد على توليد عروض تقديمية بسرعة من سطر الأوامر أو سير عمل قريب من المطورين.",
            "why_it_matters_ar": "تحويل التقارير والأفكار إلى شرائح جاهزة مشكلة متكررة للمدربين والشركات والاستشاريين.",
            "product_opportunity_ar": "مولّد عروض عربي يحول ملخص المنتج أو التقرير إلى عرض جاهز وقابل للتعديل.",
        })
    elif "science app" in low or "interactive" in low:
        base.update({
            "summary_ar": "تجربة بناء تطبيق تعليمي تفاعلي باستخدام صور مولدة بالذكاء الاصطناعي وكود من نموذج برمجي.",
            "why_it_matters_ar": "تربط التعليم بالتصميم والبرمجة السريعة، ما يجعل بناء منتجات تعليمية صغيرة أسرع.",
            "product_opportunity_ar": "مختبرات تفاعلية عربية للمدارس أو المنصات التعليمية.",
        })
    base["category"] = category
    return base


def main():
    posts = load_posts()
    # Process every post we have. Dedupe on tweet_id so the archive grows
    # safely without classifying the same post twice.
    seen = set()
    batch = []
    for item in posts:
        key = item.get("tweet_id") or item.get("url") or ""
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        batch.append(item)
    accepted = []
    archived = []
    rejected = []

    for item in batch:
        decision, reason, score = classify(item)
        text = clean_text(item.get("text", ""))
        source_url = source_url_for(item)
        if decision == "accept" and not source_url:
            decision = "archive"
            reason = "لا يوجد رابط مصدر يمكن التحقق منه، لذلك لا يظهر في الرادار الرئيسي."
            score = min(score, 0.41)
        row = {
            "tweet_id": item.get("tweet_id"),
            "author_handle": item.get("author_handle") or "",
            "url": source_url,
            "text": text,
            "decision": decision,
            "category": category_for(text) if decision == "accept" else "not_displayed",
            "quality_score": score,
            "reason_ar": reason,
            "collected_at": item.get("collected_at"),
            "source_type": item.get("source_type"),
        }
        if decision == "accept":
            row.update(insight_for(item, row["category"], score))
        else:
            row["rejection_reason_ar"] = reason
            row["weak"] = True
        if decision == "accept":
            accepted.append(row)
        elif decision == "archive":
            archived.append(row)
        else:
            rejected.append(row)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "x_first_50_quality_gate",
        "batch_size": len(batch),
        "accepted_count": len(accepted),
        "archived_count": len(archived),
        "rejected_count": len(rejected),
        "rules_ar": [
            "لا يظهر في الرادار إلا ما يرتبط بوضوح بالذكاء الاصطناعي.",
            "الأولوية لما يحتوي تحديث أداة/نموذج، تفاعل واضح، أو قابلية تحويل إلى منتج/دخل.",
            "الإعلانات والمحتوى العام تُرفض حتى لو كان التفاعل مرتفعًا.",
            "المحتوى الجزئي يُحفظ في الأرشيف ولا يظهر للمستخدم الآن.",
        ],
        "accepted": sorted(accepted, key=lambda row: row["quality_score"], reverse=True),
        "archived": sorted(archived, key=lambda row: row["quality_score"], reverse=True),
        "rejected": rejected,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(f"batch={len(batch)} accepted={len(accepted)} archived={len(archived)} rejected={len(rejected)}")


if __name__ == "__main__":
    main()
