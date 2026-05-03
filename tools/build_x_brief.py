#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "data" / "manual_x" / "posts.json"
OUT = ROOT / "data" / "manual_x" / "x_brief.json"


NOISE = [
    "Subscribe to Premium", "Today’s News", "Trending now", "What’s happening",
    "Terms of Service", "Privacy Policy", "Cookie Policy", "Who to follow",
    "To view keyboard shortcuts", "Show more", "Get rid of ads",
]


def clean(text):
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(n.lower() in s.lower() for n in NOISE):
            break
        lines.append(s)
    return "\n".join(lines).strip()


def load_posts():
    if not POSTS.exists():
        return []
    return json.loads(POSTS.read_text(encoding="utf-8")).get("items", [])


def evidence(posts, needles):
    out = []
    for item in posts:
        text = clean(item.get("text", ""))
        hay = text.lower()
        if any(n.lower() in hay for n in needles):
            out.append({
                "tweet_id": item.get("tweet_id"),
                "url": item.get("url"),
                "author_handle": item.get("author_handle"),
                "text": text[:900],
                "pain_signal_score": item.get("pain_signal_score"),
                "collected_at": item.get("collected_at"),
                "verification_status": item.get("verification_status"),
            })
    return out[:5]


def main():
    posts = load_posts()
    opps = [
        {
            "rank": 1,
            "title_ar": "حزمة خبرة Claude Code للعرب وغير الناطقين بالإنجليزية",
            "why_now_ar": "الإشارات المتكررة تقول إن المعرفة الاحترافية في Claude Code موجودة لكنها محصورة لدى قلة، بينما أغلب المستخدمين يتعاملون معه كشات أو يفتقدون قواعد/ذاكرة/هندسة عمل.",
            "customer_ar": "مطورون مستقلون، فرق صغيرة، صناع محتوى تقني، ومكاتب برمجية عربية تريد رفع جودة الإنتاج بالوكلاء.",
            "mvp_ar": "مجموعة عربية من قواعد CLAUDE.md، قوالب workflows، أمثلة مشاريع، وقائمة فحص لتشغيل Claude Code كمهندس عمل لا كمحادثة.",
            "confidence": 0.72,
            "evidence_items": evidence(posts, ["Claude Code", "كلود ليس مجرد", "everyone else's AI write code", "Claude Code users", "memory layer"]),
        },
        {
            "rank": 2,
            "title_ar": "Design Context Pack للوكلاء حتى لا ينتجوا واجهات ضعيفة",
            "why_now_ar": "هناك إشارة عربية واضحة إلى أن الوكلاء ينتجون واجهات غير جيدة بسبب عدم تعرضهم لتصاميم عالية الجودة. كما ظهرت إشارات حول open claude design و design systems.",
            "customer_ar": "مصممو منتجات، فرق SaaS صغيرة، ومطورون يستخدمون Claude/Codex/Gemini لبناء واجهات.",
            "mvp_ar": "حزمة ملفات DESIGN.md وtokens وأمثلة مكونات قابلة للحقن في Claude/Codex قبل توليد الواجهة.",
            "confidence": 0.68,
            "evidence_items": evidence(posts, ["واجهات غير جيدة", "DESIGN.md", "design systems", "open claude design", "beautiful design systems"]),
        },
        {
            "rank": 3,
            "title_ar": "AI Workflow Coach لتحويل استخدام Claude من محادثة إلى نظام عمل",
            "why_now_ar": "إشارات عربية تتحدث عن استخدام Claude كمنظومة كاملة: اختيار النموذج، أدوات الإنتاج، البحث، التكاملات، والجدولة. هذا يكشف فجوة تعليمية/تشغيلية لا مجرد خبر.",
            "customer_ar": "مستقلون، مدراء مشاريع، صناع محتوى، ومؤسسون يريدون تحويل AI إلى نظام إنتاج يومي.",
            "mvp_ar": "دليل/لوحة تشغيل يومية تولد workflows جاهزة: بحث، كتابة، تحليل، جداول، مهام، وملفات، مع قوالب عربية.",
            "confidence": 0.63,
            "evidence_items": evidence(posts, ["نظام عمل كامل", "Scheduled Tasks", "Connectors", "Claude in Excel", "يدير مشاريع", "تنبيهين"]),
        },
        {
            "rank": 4,
            "title_ar": "مراقب تكلفة/قيمة لأدوات AI المدفوعة",
            "why_now_ar": "ظهرت إشارات عن الاشتراكات، استهلاك الرصيد، وتوحيد الاشتراكات. الألم ليس دائمًا صريحًا، لكنه يتكرر حول القيمة مقابل التكلفة.",
            "customer_ar": "مستخدمو Claude/ChatGPT المدفوعون والفرق الصغيرة التي تدفع لعدة أدوات AI.",
            "mvp_ar": "حاسبة بسيطة تربط الاستخدام بالنتائج: أي نموذج/أداة تختار، متى تستخدم Thinking، وكيف تقلل هدر التوكنز والاشتراكات.",
            "confidence": 0.54,
            "evidence_items": evidence(posts, ["تحرق رصيدك", "بدل ما تدفع", "7x cheaper", "اشتراك", "رصيدك"]),
        },
    ]

    brief = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "manual_x_visible_posts",
        "input_count": len(posts),
        "headline_ar": "إشارات X الحالية تميل إلى فرصة: تشغيل Claude Code والوكلاء كمنظومة عمل احترافية، لا مجرد أدوات دردشة.",
        "summary_ar": "العينة صغيرة ومتحيزة لتفضيلات الحساب، لكنها تكشف اتجاهًا واضحًا: المحتوى حول Claude Code، الوكلاء، التصميم، وقواعد العمل يجذب انتباهًا متعدد اللغات. أكثر الفرص واقعية الآن ليست بناء أداة AI عامة، بل تغليف خبرة التشغيل: قواعد، workflows، design context، وتعليم عربي/متعدد اللغات قابل للتطبيق.",
        "data_quality": {
            "status": "directional_not_statistical",
            "note_ar": "هذه ليست عينة إحصائية من X كله. هي إشارات حقيقية/مرئية من حساب المستخدم وتصلح لتوليد فرضيات وفرص أولية، لا لإعلان أرقام سوقية.",
        },
        "opportunities": opps,
        "next_action_ar": "اختبر الفرصة الأولى سريعًا: صفحة/ملف واحد يقدم Claude Code Arabic Operating Kit مع 5 قوالب جاهزة، ثم راقب هل الحسابات العربية تتفاعل معها.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
