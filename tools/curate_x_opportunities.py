#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "data" / "manual_x" / "posts.json"
OUT = ROOT / "data" / "manual_x" / "curated_opportunities.json"


NOISE_MARKERS = [
    "Ad\n",
    "Subscribe to Premium",
    "Terms of Service",
    "Privacy Policy",
    "Who to follow",
    "What’s happening",
    "Get rid of ads",
]


OPPORTUNITY_RULES = [
    {
        "id": "agentic_engineering_services",
        "needles": ["claude code", "agentic engineering", "agents", "وكلاء", "الوكلاء", "hermes", "مدير مشاريع"],
        "title_ar": "خدمة إعداد وكلاء ذكاء اصطناعي يتابعون العمل اليومي للفرق الصغيرة",
        "title_en": "AI agent operating studio for small teams",
        "category_ar": "وكلاء وإنتاجية",
        "category_en": "Agents & productivity",
        "why_now_ar": "تكررت إشارات عن استخدام Claude Code والوكلاء كفريق عمل صغير: يوزعون المهام، يراجعون التقدم، ويجهزون تقارير بدل أن يبقى الذكاء الاصطناعي مجرد شات.",
        "why_now_en": "Repeated X signals frame Claude Code and agents as an operating system for work: task splitting, daily follow-up, product building, and semi-autonomous execution.",
        "customer_ar": "فرق ناشئة، مستقلون، مكاتب برمجة، وأصحاب أعمال صغيرة لديهم مهام متكررة ولا يريدون توظيف فريق كبير.",
        "customer_en": "Startups, freelancers, dev shops, and technical creators who want AI to become a daily operating workflow.",
        "mvp_ar": "نسخة أولى بسيطة: تختار عملية واحدة مثل متابعة العملاء أو تقرير يومي، ثم تبني لها قالب مهام ولوحة متابعة ورسائل جاهزة يراجعها الإنسان قبل الإرسال.",
        "mvp_en": "An operating kit: task templates, project rules, a follow-up board, and a short training flow for splitting work between humans and agents.",
    },
    {
        "id": "voice_dubbing_localization",
        "needles": ["voice-pro", "voice cloning", "dubbing", "whisper", "elevenlabs", "descript", "استنساخ", "دبلجة", "ترجمة"],
        "title_ar": "خدمة تعريب ودبلجة فيديوهات الشركات وصناع المحتوى بالذكاء الاصطناعي",
        "title_en": "Video-to-multilingual voice localization service",
        "category_ar": "صوت وفيديو",
        "category_en": "Voice & video",
        "why_now_ar": "تكررت إشارات عن أدوات تحول الفيديو إلى نص، تترجمه، وتنتج صوتًا جديدًا. هذا يجعل إعادة استخدام فيديو واحد بلغات ولهجات مختلفة أسهل وأرخص.",
        "why_now_en": "High-engagement posts point to local tools that combine transcription, vocal isolation, translation, voice cloning, and dubbing into one workflow.",
        "customer_ar": "مدربون، يوتيوبرز، شركات تعليم، متاجر، وصناع محتوى يريدون إعادة استخدام فيديو واحد بلغات ولهجات مختلفة.",
        "customer_en": "Educators, YouTubers, training companies, stores, and creators who want one video repurposed across languages and dialects.",
        "mvp_ar": "عرض بسيط: أرسل فيديو قصيرًا ونرجعه بنسخة عربية/إنجليزية مدبلجة مع ملف ترجمة ونص قابل للنشر.",
        "mvp_en": "A simple offer: send a short video and receive an Arabic/English dubbed version with subtitles and publish-ready copy.",
    },
    {
        "id": "trend_to_app_lab",
        "needles": ["trending topic", "creator search insights", "app ideas", "launch the app", "low-competition", "topics"],
        "title_ar": "خدمة تحويل الترندات إلى أفكار تطبيقات صغيرة قابلة للاختبار",
        "title_en": "Trend-to-micro-app idea lab",
        "category_ar": "بحث منتجات",
        "category_en": "Product research",
        "why_now_ar": "تظهر إشارات تربط بين الترندات والبحث عن كلمات قليلة المنافسة وبناء تطبيقات صغيرة بسرعة. المستخدم لا يحتاج فكرة ضخمة؛ يحتاج تجربة صغيرة تثبت الطلب.",
        "why_now_en": "X signals connect trends, low-competition keyword research, and the ability to ship a small app in one or two days.",
        "customer_ar": "مطورون أفراد، أصحاب متاجر، وصناع محتوى يريدون أفكارًا قابلة للاختبار بسرعة بدل بناء منتج كبير من البداية.",
        "customer_en": "Solo builders, store owners, and creators who want fast testable ideas instead of starting with a large product.",
        "mvp_ar": "تقرير أسبوعي: 10 ترندات + فكرة تطبيق لكل ترند + صفحة اختبار بسيطة + مؤشر منافسة.",
        "mvp_en": "A weekly report: 10 trends, one app idea per trend, a simple validation page, and a competition signal.",
    },
    {
        "id": "ai_design_context_pack",
        "needles": ["html-in-canvas", "three.js", "design", "figma", "canvas", "webgpu", "واجهات", "تصميم"],
        "title_ar": "حزمة تعليمات تصميم تجعل أدوات AI تنتج واجهات أجمل وأوضح",
        "title_en": "Design context pack for agents and builders",
        "category_ar": "تصميم وتجربة",
        "category_en": "Design & UX",
        "why_now_ar": "كثيرون يستخدمون AI لبناء واجهات، لكن النتائج تخرج عشوائية أو ضعيفة بصريًا. الإشارات الأخيرة تؤكد أن الوكيل يحتاج تعليمات تصميم وسياقًا بصريًا قبل البرمجة.",
        "why_now_en": "Visible signals combine advanced interactive UI, HTML-in-Canvas, and design systems that agents need clear context to reproduce well.",
        "customer_ar": "مؤسسو SaaS، مصممون، مطورون، وأصحاب مشاريع يريدون واجهات احترافية من أدوات AI بدون خبرة تصميم عميقة.",
        "customer_en": "SaaS founders, designers, and developers using AI to build interfaces but getting weak visual output.",
        "mvp_ar": "نسخة أولى: ملف تعليمات تصميم، ألوان وخطوط جاهزة، أمثلة شاشات، وقواعد حركة بسيطة تُضاف إلى Claude أو Codex قبل بناء الواجهة.",
        "mvp_en": "Ready files: DESIGN.md, tokens, interface examples, and motion rules injected into Claude/Codex before implementation.",
    },
    {
        "id": "ai_property_tour_content",
        "needles": ["tour enclosed spaces", "360-degree camera", "realhorizons", "phone", "spaces"],
        "title_ar": "خدمة تحويل تصوير الهاتف إلى جولة عقارية تفاعلية بالذكاء الاصطناعي",
        "title_en": "AI property tours from phone footage",
        "category_ar": "عقار ومحتوى",
        "category_en": "Real estate & content",
        "why_now_ar": "ظهرت إشارة عن صنع جولات لمساحات مغلقة من تصوير الهاتف بدل معدات 360 المكلفة. هذا مناسب لمكاتب العقار والشقق والعيادات التي تريد عرض المكان بسرعة.",
        "why_now_en": "An X signal points to making enclosed-space tours with a phone instead of expensive 360 gear, opening an offer for real estate and hospitality.",
        "customer_ar": "مكاتب عقار، شقق مفروشة، قاعات تدريب، عيادات، ومقاهي تريد عرض المكان بشكل غني بدون تصوير مكلف.",
        "customer_en": "Real estate offices, furnished apartments, training halls, clinics, and cafes that need rich space previews without expensive shoots.",
        "mvp_ar": "نسخة أولى: يأخذ العميل فيديو قصيرًا للمكان، وتحوّله الخدمة إلى جولة تفاعلية مع وصف عربي/إنجليزي ونص إعلان جاهز للنشر.",
        "mvp_en": "First version: a client sends a short phone video of the space, and the service turns it into an interactive tour with Arabic/English copy and ad text.",
    },
    {
        "id": "company_knowledge_assistant",
        "needles": ["rag", "knowledge vault", "knowledge base", "notebooklm", "obsidian", "file search", "documents", "citations", "references", "مستندات", "وثائق", "معرفة"],
        "title_ar": "مساعد يجيب من ملفات الشركة ويعرض مصدر كل إجابة",
        "title_en": "A company-file assistant that answers with cited sources",
        "category_ar": "معرفة ووثائق",
        "category_en": "Knowledge & documents",
        "why_now_ar": "تكررت إشارات عن RAG وNotebookLM وقواعد المعرفة. المشكلة ليست في الحصول على إجابة عامة، بل في إجابة موثوقة من ملفات الشركة نفسها.",
        "why_now_en": "Repeated RAG, NotebookLM, and knowledge-base signals show demand for trusted answers from company files, not generic web answers.",
        "customer_ar": "مدارس، عيادات، مكاتب محاماة، فرق مبيعات، وشركات لديها ملفات كثيرة ويضيع وقتها في البحث داخلها.",
        "customer_en": "Schools, clinics, law offices, sales teams, and companies with many documents and slow internal search.",
        "mvp_ar": "نسخة أولى: رفع 20 ملفًا فقط، ثم مساعد يجيب بالعربية ويعرض اسم الملف والفقرة التي استند إليها.",
        "mvp_en": "First version: upload only 20 files, then a simple Arabic assistant answers with the exact file and passage it used.",
    },
    {
        "id": "app_onboarding_video_service",
        "needles": ["onboarding", "screenshots", "screen recording", "video proof", "before/after", "motion graphics", "app functionality", "paywall"],
        "title_ar": "خدمة تحويل لقطات التطبيق إلى فيديو يشرح المنتج قبل صفحة الدفع",
        "title_en": "A service that turns app screenshots into onboarding videos",
        "category_ar": "تسويق التطبيقات",
        "category_en": "App marketing",
        "why_now_ar": "ظهرت إشارات عن تحويل لقطات الشاشة إلى فيديو onboarding. هذا يحل مشكلة شائعة: المستخدم لا يفهم قيمة التطبيق قبل أن يُطلب منه الدفع.",
        "why_now_en": "Signals around screenshot-to-onboarding video workflows solve a common problem: users don't understand an app before the paywall.",
        "customer_ar": "أصحاب تطبيقات، مؤسسو SaaS، مطورو ألعاب، ومنتجات اشتراك تريد رفع التحويل قبل الدفع.",
        "customer_en": "App owners, SaaS founders, game developers, and subscription products that need better conversion before payment.",
        "mvp_ar": "نسخة أولى: يرسل العميل 5 لقطات شاشة، وتسلّمه الخدمة فيديو قصيرًا يشرح أهم ميزة مع نص عربي وإنجليزي.",
        "mvp_en": "First version: the client sends five screenshots and receives a short video explaining the main feature in Arabic and English.",
    },
    {
        "id": "qa_video_proof_automation",
        "needles": ["qa automation", "video proof", "before/afters", "screen recording", "bug", "testing", "openclaw", "codex"],
        "title_ar": "خدمة اختبار واجهات تسجل فيديو يثبت المشكلة قبل وبعد الإصلاح",
        "title_en": "UI testing service that records before/after proof videos",
        "category_ar": "اختبار وجودة",
        "category_en": "QA & testing",
        "why_now_ar": "إشارات OpenClaw وCodex تتحدث عن توليد دليل فيديو للمشاكل تلقائيًا. هذا مهم لأن العميل لا يريد تقريرًا طويلًا؛ يريد أن يرى المشكلة والإصلاح.",
        "why_now_en": "OpenClaw and Codex signals show automated video proof for issues. Clients don't want long bug reports; they want to see the issue and the fix.",
        "customer_ar": "مكاتب برمجة، فرق SaaS، مطورو تطبيقات، وأصحاب مواقع يتكرر عندهم كسر الواجهة.",
        "customer_en": "Dev shops, SaaS teams, app developers, and site owners with recurring UI regressions.",
        "mvp_ar": "نسخة أولى: اختبار 5 مسارات في الموقع، تسجيل فيديو للمشكلة، ثم فيديو بعد الإصلاح مع قائمة مختصرة بما تغير.",
        "mvp_en": "First version: test five site flows, record the bug, then record the fixed version with a short change list.",
    },
]


def load_posts():
    if not POSTS.exists():
        return []
    return json.loads(POSTS.read_text(encoding="utf-8")).get("items", [])


def is_noise(item):
    text = item.get("text") or ""
    if any(marker.lower() in text.lower() for marker in NOISE_MARKERS):
        return True
    if item.get("author_handle") in {"PeptazolSA", "BSF_sa", "rogueducknet"}:
        return True
    return False


def clean_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text or "").strip()
    text = re.sub(r"(Subscribe to Premium|Terms of Service|Privacy Policy).*", "", text, flags=re.I | re.S)
    return text[:900].strip()


def score_item(item):
    text = (item.get("text") or "").lower()
    base = float(item.get("pain_signal_score") or 0)
    if any(k in text for k in ["claude", "gpt", "ai", "agent", "voice", "dubbing", "figma", "canvas", "three.js", "app"]):
        base += 0.12
    metrics = item.get("public_metrics") or {}
    if isinstance(metrics, dict):
        likes = metrics.get("likes") or 0
        reposts = metrics.get("reposts") or 0
        if likes >= 100 or reposts >= 30:
            base += 0.08
    if "views" in text or "likes" in text or "bookmarks" in text:
        base += 0.04
    return round(min(base, 0.95), 2)


def evidence_for(posts, needles):
    rows = []
    for item in posts:
        if is_noise(item):
            continue
        text = clean_text(item.get("text") or "")
        hay = text.lower()
        if not any(needle.lower() in hay for needle in needles):
            continue
        rows.append({
            "tweet_id": item.get("tweet_id"),
            "author_handle": item.get("author_handle") or "",
            "url": item.get("url") or "",
            "text": text,
            "score": score_item(item),
            "collected_at": item.get("collected_at"),
            "source_type": item.get("source_type"),
            "verification_status": item.get("verification_status"),
        })
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:5]


def build_opportunities(posts):
    opportunities = []
    for rank, rule in enumerate(OPPORTUNITY_RULES, start=1):
        evidence = evidence_for(posts, rule["needles"])
        if not evidence:
            continue
        avg_score = sum(item["score"] for item in evidence) / len(evidence)
        confidence = min(0.86, 0.44 + avg_score * 0.55 + min(len(evidence), 5) * 0.035)
        opportunities.append({
            "rank": rank,
            "id": rule["id"],
            "title_ar": rule["title_ar"],
            "title_en": rule["title_en"],
            "category_ar": rule["category_ar"],
            "category_en": rule["category_en"],
            "why_now_ar": rule["why_now_ar"],
            "why_now_en": rule["why_now_en"],
            "customer_ar": rule["customer_ar"],
            "customer_en": rule["customer_en"],
            "mvp_ar": rule["mvp_ar"],
            "mvp_en": rule["mvp_en"],
            "confidence": round(confidence, 2),
            "evidence_count": len(evidence),
            "evidence_items": evidence,
            "source_links": [
                {
                    "label_ar": f"إشارة X من @{item['author_handle']}" if item["author_handle"] else "إشارة X",
                    "label_en": f"X signal from @{item['author_handle']}" if item["author_handle"] else "X signal",
                    "source": "X",
                    "url": item["url"],
                }
                for item in evidence
                if item.get("url")
            ],
        })
    return sorted(opportunities, key=lambda item: (item["confidence"], item["evidence_count"]), reverse=True)


def main():
    posts = load_posts()
    kept = [item for item in posts if not is_noise(item)]
    opportunities = build_opportunities(kept)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "x_safari_curated",
        "input_count": len(posts),
        "kept_count": len(kept),
        "rejected_count": len(posts) - len(kept),
        "curated_count": len(opportunities),
        "quality_rules_ar": [
            "استبعاد الإعلانات والمحتوى غير المرتبط بالذكاء الاصطناعي.",
            "تجميع الإشارات المتشابهة بدل عرض كل تغريدة منفصلة.",
            "تقديم الفكرة كإلهام قابل للاختبار، لا كوعد مالي.",
            "حفظ روابط الأدلة عند توفرها حتى يستطيع المستخدم التحقق.",
        ],
        "opportunities": opportunities,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(f"input={len(posts)} kept={len(kept)} rejected={len(posts)-len(kept)} curated={len(opportunities)}")


if __name__ == "__main__":
    main()
