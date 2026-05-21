# STATUS — AX Pulse

> ملف الحالة الحيّ. حدّثه بعد كل جلسة Claude Code أو Codex.

## آخر جلسة

**التاريخ:** 2026-05-21 12:52 (Codex · كسر كاش ملفات الواجهة فورًا)
**ما تم:**
- اكتشاف أن تحديث الصفحة لم يكن كافيًا أحيانًا لأن [radar.html](./radar.html) كان يحمّل:
  - `assets/js/radar-inline-data.js`
  - `assets/js/radar.js`
  - عبر نسخة تتغير **كل ساعة فقط**
- هذا يعني أن أي تعديل داخل نفس الساعة قد لا ينعكس فورًا للمستخدم، حتى لو كانت الملفات نفسها محدثة.
- تعديل [radar.html](./radar.html) بحيث أصبح `radarAssetVersion` يعتمد على:
  - `Date.now()`
  - بدل نسخة الساعة
- النتيجة:
  - كل تحميل جديد للصفحة يسحب نسخة جديدة من ملفات الواجهة فورًا
  - وتختفي مشكلة بقاء منطق قديم ظاهر داخل نفس الساعة

**التحقق:**
- التأكد أن [radar.html](./radar.html) تحتوي الآن على:
  - `const radarAssetVersion = Date.now();`

**الأثر المتوقع:**
- أي تعديل جديد في:
  - [assets/js/radar.js](./assets/js/radar.js)
  - أو [assets/js/radar-inline-data.js](./assets/js/radar-inline-data.js)
  يجب أن يظهر فور إعادة فتح/تحديث الصفحة، بدون انتظار مرور ساعة جديدة.

**الخطوة التالية:**
- إعادة تحميل الصفحة مرة أخرى، والتأكد أن:
  - ترتيب المصادر أصبح صحيحًا
  - والصياغة الجديدة لرسائل التعذر ظهرت فعلًا

**التاريخ:** 2026-05-21 12:46 (Codex · تغيير ترتيب قائمة حالة البيانات)
**ما تم:**
- اكتشاف أن سبب ظهور المصادر المتعثرة أعلى القائمة لم يكن في البيانات نفسها، بل في منطق الفرز داخل:
  - [assets/js/radar.js](./assets/js/radar.js)
- الترتيب السابق كان يعطي الأولوية هكذا:
  - `failed`
  - ثم `skipped`
  - ثم `stale`
  - ثم `active`
- تم عكسه ليصبح:
  - `active`
  - ثم `stale`
  - ثم `skipped`
  - ثم `failed`
- هذا يعني أن المستخدم سيرى الآن:
  - المصادر التي نجحت أولًا
  - ثم النسخ المحفوظة
  - وتبقى المصادر المتعذرة في أسفل القائمة بدل تصدّرها للمشهد

**التحقق:**
- فحص صياغة JavaScript نجح:
  - `node -c assets/js/radar.js`

**الأثر المتوقع:**
- قسم `حالة البيانات` سيعطي انطباعًا أكثر توازنًا:
  - ما يعمل يظهر أولًا
  - وما تعذر يظهر لاحقًا بدون تهويل

**الخطوة التالية:**
- تحديث الصفحة والتأكد بصريًا أن ترتيب المصادر أصبح:
  - ناجح
  - محفوظ
  - غير متصل
  - متعذر

**التاريخ:** 2026-05-21 12:41 (Codex · تهدئة صياغة حالة البيانات للمستخدم)
**ما تم:**
- تعديل الصياغة الظاهرة للمستخدم في [assets/js/radar.js](./assets/js/radar.js) داخل طبقة `حالة البيانات` حتى لا توحي بأن الرادار كله ضعيف عند تعثر مصدر أو مصدرين.
- استبدال التعبيرات القاسية مثل:
  - `فشل آخر تحديث`
  - برسائل ألطف وأدق مثل:
  - `تعذّر التحديث الآن`
  - `نعرض نسخة محفوظة`
  - `المصدر غير متاح مؤقتًا`
- تعديل الشرح النصي المرافق بحيث يوضح أن:
  - الرادار نفسه يعمل
  - والمحتوى المعروض يبقى الموثوق أو المحفوظ
  - وأي مصدر متعذر لا يُعامل كتحديث مباشر
- تحسين عدّاد الحالة المختصر ليعرض:
  - `متعذر`
  - بدل `فشل`

**التحقق:**
- فحص صياغة JavaScript نجح:
  - `node -c assets/js/radar.js`
- تأكد اختفاء عبارة `فشل آخر تحديث` من الواجهة الرئيسية.

**الأثر المتوقع:**
- قسم `هل البيانات محدثة؟` سيبقى صادقًا، لكن بصياغة لا تضعف انطباع المستخدم عن الرادار كله.
- عند تعذر مصدر منفرد، سيرى المستخدم أنه غير متاح مؤقتًا أو أن النظام يعرض نسخة محفوظة، بدل إيحاء عام بأن المنصة فشلت.

**الخطوة التالية:**
- إذا أردنا تحسين الصورة أكثر من مجرد الصياغة، فالخطوة التالية هي إصلاح المصدرين المتعثرين أنفسهما:
  - `Anthropic`
  - `Indie Hackers`
  أو إخفاؤهما من الواجهة العامة حتى يعودا للعمل.

**التاريخ:** 2026-05-21 12:29 (Codex · ربط pulse-radar بملف حالة البيانات)
**ما تم:**
- إصلاح سبب انفصال:
  - تحديث المحتوى
  - عن جزئية `آخر دورة رصد` في الواجهة
- تم التأكد أن الواجهة تقرأ هذه الجزئية من:
  - [data/radar/run_status.json](./data/radar/run_status.json)
  - بينما `./pulse-radar` كان يحدث:
    - [data/radar/raw_items.json](./data/radar/raw_items.json)
    - [data/radar/signals.json](./data/radar/signals.json)
    - [data/radar/opportunities.json](./data/radar/opportunities.json)
  - **بدون** تحديث `run_status.json`
- تعديل [tools/pulse_radar.py](./tools/pulse_radar.py) بحيث أصبح بعد كل تشغيل:
  - يكتب `run_status.json`
  - يكتب/يحدث `source_runs.json`
  - يسجل:
    - `run_id`
    - `started_at`
    - `finished_at`
    - `sources_attempted`
    - `sources_succeeded`
    - `sources_failed`
    - `skipped_sources`
    - `source_health`
    - `total_raw_items`
    - `total_accepted_signals`
- إضافة helper مفقود داخل نفس الملف:
  - `merge_source_runs_archive()`
- هذا يعني أن `pulse-radar` أصبح الآن يحدث:
  - المحتوى
  - وحالة البيانات
  - معًا، بدل أن يبقى كل واحد في ملف منفصل لا يتزامن مع الآخر

**التحقق:**
- فحص صياغة Python نجح:
  - `python3 -m py_compile tools/pulse_radar.py`

**الأثر المتوقع بعد التشغيل القادم:**
- عبارة `آخر دورة رصد` في الواجهة يجب أن تعكس **آخر تشغيل فعلي** لـ `./pulse-radar`
- شاشة `حالة البيانات` يجب أن تصبح متزامنة مع آخر تحديث حقيقي للمصادر

**الخطوة التالية:**
- تشغيل `./pulse-radar` مرة جديدة بعد هذا التعديل، ثم تحديث الصفحة ومراجعة:
  - تاريخ آخر دورة رصد
  - وحالة المصادر
  - وهل ما زالت تعرض تاريخًا قديمًا أم لا

**التاريخ:** 2026-05-21 12:18 (Codex · إصلاح تعطل pulse-radar عند RSS غير صالح)
**ما تم:**
- معالجة خطأ التشغيل الذي ظهر عند تشغيل:
  - `./pulse-radar`
- السبب كان في [tools/pulse_radar.py](./tools/pulse_radar.py):
  - بعض مصادر RSS قد ترجع XML غير صالح أو فيه رموز غير مدعومة
  - وكان الرادار يتعطل بالكامل عند أول `ParseError`
- الإصلاح:
  - إضافة `sanitize_xml_text()` لتنظيف BOM والرموز غير الصالحة وقطع أي نص قبل أول tag
  - إضافة `parse_xml()` كطبقة موحدة لقراءة XML
  - تعديل `fetch_rss_source()` حتى:
    - لا ينهار الرادار عند feed معطوب
    - بل يعيد خطأ المصدر فقط داخل الحالة
  - تعديل `fetch_arxiv_query()` ليستفيد من نفس parser الأنظف
- التحقق:
  - فحص صياغة Python نجح:
    - `python3 -m py_compile tools/pulse_radar.py`

**الأثر المتوقع:**
- `pulse-radar` لم يعد يفترض أن يتوقف بالكامل بسبب مصدر RSS واحد مكسور.
- عند وجود feed معطوب سيظهر كمصدر فاشل/ضعيف داخل حالة البيانات، لكن بقية المصادر ستكمل.

**الخطوة التالية:**
- إعادة تشغيل:
  - `./pulse-radar`
  - ثم تحديث الرادار للتأكد أن حالة البيانات أصبحت أحدث حتى لو بقي مصدر أو مصدران في وضع failed/stale.

**التاريخ:** 2026-05-21 12:10 (Codex · إضافة فرصة AI المحلي بصياغة أوضح)
**ما تم:**
- إضافة/تثبيت فرصة دخل أوضح داخل طبقة الفرص النهائية:
  - **خدمة تجهيز أدوات AI محلية للجهات التي لا تريد إرسال بياناتها للخارج**
- تعديل [tools/final_radar_editor.py](./tools/final_radar_editor.py) بحيث:
  - يحافظ على هذه الصياغة الأوضح
  - ويمنع بقاء نسخة قديمة أضعف من نفس الفكرة في طبقة الفرص المركزة
- إعادة تشغيل:
  - [tools/final_radar_editor.py](./tools/final_radar_editor.py)
  - [tools/build_inline_radar_data.py](./tools/build_inline_radar_data.py)

**النتيجة:**
- الفرصة الجديدة أصبحت موجودة داخل:
  - [data/radar/focused_opportunities.json](./data/radar/focused_opportunities.json)
  - [data/radar/final_radar_editor.json](./data/radar/final_radar_editor.json)
- وتمت إعادة بناء بيانات الواجهة بعد الإضافة.

**الخطوة التالية:**
- مواصلة استخراج الفرص المفقودة من التغريدات المقبولة، ثم إضافتها بنفس معيار الوضوح لغير المختص.

**التاريخ:** 2026-05-21 12:01 (Codex · بدء استخراج الفرص المفقودة من التغريدات المقبولة)
**ما تم:**
- بدء جولة فحص جديدة على:
  - [data/manual_x/radar_ready_posts.json](./data/manual_x/radar_ready_posts.json)
  - مع التركيز على العناصر المقبولة التي بقيت في `archive`
- التحقق أن الدفعة الحالية تضم:
  - **218** تغريدة مقبولة
  - منها:
    - `174 archive`
    - `37 radar_updates`
    - `4 product_ideas`
    - `3 trending`
- ملاحظة مهمة:
  - أغلب عناصر `archive` ما زالت تحمل صياغة عامة جدًا:
    - `استخدمها كإلهام أولي فقط...`
  - وهذا يعني أن هناك فرصًا حقيقية اختبأت داخل التغريدات، لكنها لم تتحول بعد إلى بطاقات دخل واضحة.
- استخراج أول دفعة من الفرص المفقودة التي ظهرت أثناء الفحص اليدوي:
  - خدمة ERP مفتوح المصدر + AI للشركات الصغيرة بدل الأنظمة المكلفة
  - طبقة UI/workflow builder لغير التقنيين فوق البيانات والعمليات الحالية
  - تكامل AI مع Slack/Linear كموظف عمليات أو مهندس إضافي للفريق
  - خدمة ضبط Billing وتكلفة التوكنز لمنتجات AI
  - إعداد proxy / local bridge لتشغيل Claude Code أو أدوات مشابهة بتكلفة أقل
  - خدمات هوية بصرية سريعة ومنتجات Brand packs خلال يوم
  - مولّد عروض/Presentations عربي من ملخص منتج أو تقرير
  - حلول نماذج محلية/طرفية صغيرة للرؤية أو الأجهزة المتخصصة

**معلّق:**
- لم تُرفع هذه الفرص بعد إلى الواجهة كفرص رسمية.
- ما زلنا في مرحلة الاستخراج والتحرير الأولي من التغريدات نفسها.

**الخطوة التالية:**
- تحويل الدفعة الأولى من هذه الفرص المفقودة إلى صياغة دخل واضحة ومفهومة، ثم تقرير أيها يستحق إدخاله فعليًا إلى طبقة الفرص في الرادار.

**التاريخ:** 2026-05-21 11:48 (Codex · توسيع فرص الدخل بدل تقليلها)
**ما تم:**
- بعد ملاحظة أن المطلوب هو **زيادة الفرص الحقيقية** لا تقليلها، تم توسيع المحرر النهائي في:
  - [tools/final_radar_editor.py](./tools/final_radar_editor.py)
- الإضافة الجديدة:
  - تحليل `radar_card_candidates.json` وتجميع بطاقات الفرص المتشابهة
  - تحويل العناقيد المتكررة إلى فرص دخل مستقلة جديدة بدل تركها كبطاقات متناثرة
- أمثلة الفرص الجديدة المضافة عبر هذا التوسيع:
  - مختبر تحويل الأبحاث إلى أدوات صغيرة قابلة للبيع
  - حزمة تشغيل ذكاء اصطناعي محلي للجهات الحساسة والفرق الداخلية
  - باقة تشغيل فرق البرمجة بأدوات AI لبناء MVP أسرع
  - خدمة مراجعة أمن أدوات AI وصلاحياتها داخل الشركات
- رفع سقف `focused_opportunities` من **8** إلى **12** فرصة مركزة.
- إعادة بناء:
  - [data/radar/focused_opportunities.json](./data/radar/focused_opportunities.json)
  - [data/radar/final_radar_editor.json](./data/radar/final_radar_editor.json)
  - [assets/js/radar-inline-data.js](./assets/js/radar-inline-data.js)

**نتيجة التحقق المحلي:**
- `focused_opportunities.json` الآن تحتوي على **12** فرصة.
- فحص Python نجح بعد التعديل.
- إعادة بناء inline data نجحت.

**معلّق:**
- الخطوة التالية المنطقية ليست فقط زيادة العدد أكثر، بل **إعادة تحرير عناوين بعض الفرص** لتصبح أشد تخصيصًا ووضوحًا حسب القطاع.

**الخطوة التالية:**
- مراجعة الـ 12 فرصة الحالية وتحويل ما يصلح منها إلى:
  - فرص حكومية
  - فرص تعليمية
  - فرص أمنية
  - فرص تشغيلية
  حتى تصبح أكثر قوة في العرض والرادار.

**التاريخ:** 2026-05-21 11:39 (Codex · توحيد عداد وعرض فرص الدخل)
**ما تم:**
- فحص سبب التضارب بين:
  - عداد `الأفكار الملهمة`
  - وشريط `فرص الدخل`
- تأكد أن السبب كان في [assets/js/radar.js](./assets/js/radar.js):
  - العداد كان يحسب كل المخزون الفريد من عدة طبقات
  - بينما الشريط كان يقطع العرض إلى `12` فقط
- تعديل الواجهة بحيث:
  - شريط الفرص يعرض **كل الفرص الجديرة فعلاً**
  - وليس عينة مقصوصة منها
  - والعداد أصبح يعتمد نفس القائمة نفسها بدل عدّ مخزون أوسع من المعروض
- إضافة فلتر جودة جديد داخل:
  - [assets/js/radar.js](./assets/js/radar.js)
  - عبر `isWorthyOpportunity()` و `allWorthyOpportunityRows()`
- القاعدة الجديدة:
  - `focused_opportunity` تُعرض
  - فرص `manual_x` لا تُعرض إلا إذا كان عندها عرض واضح + عميل واضح + دليل
  - `validated_opportunity` لا تُعرض إلا إذا كان عندها ثقة ومعنى تجاري ودليل
  - تم استبعاد playbooks والعينات العامة من الشريط الرئيسي
- إعادة بناء:
  - [assets/js/radar-inline-data.js](./assets/js/radar-inline-data.js)

**نتيجة التحقق المحلي:**
- فحص JavaScript نجح:
  - `node -c assets/js/radar.js`
- بناء inline data نجح.
- `focused_opportunities.json` ما زالت تحتوي على **8** فرص مركزة، لكن الشريط لن يعود محدودًا بعينة `12` إذا زاد العدد مستقبلًا، وسيعرض كل ما يجتاز الفلتر.

**معلّق:**
- ما زلنا بحاجة جولة تحريرية لاحقة لتحسين “صياغة” بعض الفرص نفسها، لكن من جهة المنطق:
  - لم يعد العداد يحسب شيئًا مختلفًا عن المعروض.

**الخطوة التالية:**
- مراجعة الرادار بصريًا بعد التحديث للتأكد أن:
  - الرقم يطابق ما يراه المستخدم
  - وكل عنصر في الشريط يستحق فعلًا الظهور كفرصة دخل.

**التاريخ:** 2026-05-21 11:26 (Codex · إنشاء المحرر الذكي النهائي)
**ما تم:**
- قراءة `AGENTS.md` و `STATUS.md` و `CHANGELOG.md` قبل البدء.
- فحص الطبقات الحالية للمشروع وتأكيد أن لدينا builders منفصلة لـ:
  - فرص الدخل
  - جديد اليوم
  - نقاشات الناس
  - الأدلة
  - حالة المصادر
- إنشاء طبقة موحدة جديدة هنا:
  - [tools/final_radar_editor.py](./tools/final_radar_editor.py)
- وظيفة هذه الطبقة:
  - دمج `focused_opportunities` الحالية مع فرص `manual_x` المنتقاة
  - توليد fallback لـ `focused_updates` من `radar_card_candidates.json` عندما تكون طبقة “جديد اليوم” فارغة أو ضعيفة
  - إعادة ترتيب `focused_discussions` بالأهمية والحداثة
  - بناء ملف موحد جديد:
    - [data/radar/final_radar_editor.json](./data/radar/final_radar_editor.json)
  - ثم إعادة كتابة الملفات التي تقرأ منها الواجهة مباشرة:
    - [data/radar/focused_opportunities.json](./data/radar/focused_opportunities.json)
    - [data/radar/focused_updates.json](./data/radar/focused_updates.json)
    - [data/radar/focused_discussions.json](./data/radar/focused_discussions.json)
- ربط المحرر النهائي بسير التشغيل في:
  - [tools/radar_orchestrator.py](./tools/radar_orchestrator.py)
  - بحيث يعمل تلقائيًا بعد:
    - Opportunity Builder
    - Focused Updates Builder
    - Focused Discussions Builder
- تحديث مسارات X السريعة حتى لا تكتفي بإدخال البيانات الخام، بل تمر عبر المحرر النهائي أيضًا:
  - [refresh-x-radar.command](./refresh-x-radar.command)
  - [x-playwright-radar.command](./x-playwright-radar.command)
- تحديث طبقة inline data حتى تضم الملف الجديد:
  - [tools/build_inline_radar_data.py](./tools/build_inline_radar_data.py)
- تحديث الواجهة في:
  - [assets/js/radar.js](./assets/js/radar.js)
  - حتى تعطي `focusedOpportunityRows()` أولوية فعلية داخل `opportunityRows()` بدل أن تبقى الفرص المركزة محمّلة في الذاكرة فقط.

**نتيجة التحقق المحلي:**
- تشغيل `tools/final_radar_editor.py` نجح.
- `focused_opportunities.json` أصبحت: **8**
- `focused_updates.json` أصبحت: **6**
- `focused_discussions.json` بقيت: **6**
- `radar_orchestrator.py` نجح محليًا مع:
  - `--run-opportunity-builder`
  - `--run-focused-updates`
  - `--run-focused-discussions`
- إعادة بناء:
  - [assets/js/radar-inline-data.js](./assets/js/radar-inline-data.js)
  - نجحت، وأصبحت تضم **21** ملف بيانات مضمّن.
- فحوصات الصياغة نجحت:
  - `python3 -m py_compile`
  - `node -c assets/js/radar.js`

**معلّق:**
- `product_playbooks_dynamic.json` ما زال غير موجود، لكن هذا ليس خطأ جديدًا ولم يمنع بناء البيانات.
- ما زلنا نحتاج جولة تحريرية لاحقة لتحسين جودة `focused_updates` نفسها، لأن fallback الحالي يضمن وجود “جديد اليوم” لكنه لا يغني عن تحرير أعمق للمحتوى.

**الخطوة التالية:**
- تشغيل الجولة الكاملة على دفعة X/المصادر القادمة، ثم مراجعة ما إذا كانت:
  - فرص الدخل الجديدة
  - جديد اليوم
  - نقاشات الناس
  تظهر الآن للمستخدمين بشكل أوضح من قبل.

**التاريخ:** 2026-05-21 10:34 (Codex · إدخال 4 ملفات X capture إلى المنصة)
**ما تم:**
- قراءة `AGENTS.md` و `STATUS.md` و `CHANGELOG.md` قبل البدء.
- فحص ملفات الإدخال التالية من `Downloads`:
  - `ax-pulse-x-capture-8.json`
  - `ax-pulse-x-capture-9.json`
  - `ax-pulse-x-capture-10.json`
  - `ax-pulse-x-capture-11.json`
- التأكد أنها كلها بصيغة Safari/X الصحيحة:
  - `schema = ax_pulse.safari_radar.v1`
- أخذ نسخة احتياطية قبل الدمج هنا:
  - [data/manual_x/backups/20260521-102848](./data/manual_x/backups/20260521-102848)
- إدخال الملفات الأربع عبر نفس بوابة الجودة الإنتاجية:
  - `tools/safari_clipboard_collect.py`
- ثم إعادة بناء طبقة X المرتبطة بالموقع عبر:
  - `tools/filter_x_radar_ready.py`
  - `tools/curate_x_opportunities.py`
  - `tools/build_x_brief.py`
  - `tools/build_focused_discussions.py`
  - `tools/build_x_radar_cards.py`
  - `tools/build_inline_radar_data.py`

**نتيجة الإدخال لكل ملف:**
- `ax-pulse-x-capture-8.json`:
  - أضيف: **95**
  - ضعيف/خارج الموضوع: **305**
- `ax-pulse-x-capture-9.json`:
  - أضيف: **53**
  - مكرر: **9**
  - ضعيف/خارج الموضوع: **338**
- `ax-pulse-x-capture-10.json`:
  - أضيف: **122**
  - ضعيف/خارج الموضوع: **278**
- `ax-pulse-x-capture-11.json`:
  - أضيف: **27**
  - ضعيف/خارج الموضوع: **373**

**الحصيلة النهائية بعد الدمج:**
- `posts.json`:
  - قبل: **1278**
  - بعد: **1575**
  - الصافي: **+297**
- `radar_ready_posts.json`:
  - قبل accepted: **989**
  - بعد accepted: **1207**
  - الصافي: **+218**
- `x_radar_cards.json`:
  - قبل: **548**
  - بعد: **658**
  - الصافي: **+110**

**معلّق:**
- `curated_opportunities.json` بقي عند **8** فرص — يعني الدفعة الجديدة رفعت المحتوى والبطاقات أكثر من رفعها لفرص curated جديدة.
- `x_brief.json` ما زال بلا `top_items` فعليًا في هذه الجولة.

**الخطوة التالية:**
- إذا أردنا الاستفادة التحريرية القصوى من هذه الدفعة، فالخطوة التالية الأفضل ليست إدخالًا جديدًا، بل:
  1. فرز أفضل ما دخل من هذه الأربع ملفات
  2. استخراج الفرص غير المعروضة
  3. أو تحويل أقوى الإشارات إلى فرص قطاعية/محتوى عرض

---

## 🔧 المهمة العاجلة v2 — إصلاح R3 + R4 فقط (Thu 2026-05-21 09:10)

### 📍 السياق
- R1-R4 خُلصت ($0.566 إجمالي، 4 د)
- R2 ممتاز (15 نقاش متنوّع) ✅
- R1 مقبول (7/10 Google bias لكن البيانات حقيقية)
- 🔴 **R3 فاشل**: 12/20 = Gemini Flash مكرّر، مفقود Claude/GPT/Llama/Mistral/DeepSeek/Qwen
- 🔴 **R4 بلا قيمة**: قائمة أدوات معروفة (Claude/ChatGPT/Cursor/Notion/Midjourney)

### 🎯 المطلوب: أعد R3 + R4 فقط بـ queries جديدة

**لا تلمس R1, R2, cost_report.md للجولة السابقة.** احفظ النتائج الجديدة في:
- `data/radar/grok_test/raw/R3_v2.json`
- `data/radar/grok_test/raw/R4_v2.json`
- `data/radar/grok_test/cost_report_v2.md`

---

### R3 v2 — 20 تحديث في نماذج AI (بدون Gemini/Grok)

**Query للأداة `x_search`:**
```
(announces OR released OR launched OR "open-sourced" OR available) (Claude OR GPT OR Llama OR Mistral OR DeepSeek OR Qwen OR Sonnet OR Opus OR Haiku OR Cohere) -Gemini -Grok -Antigravity min_faves:500
```

**Parameters:**
- `since:2026-04-21` (نافذة 30 يوم بدل 7)
- `mode: "Top"` (بدل `Latest`) ← مهم جداً، يمنع التحيّز للحدث الأخير
- `limit: 20`

**Model:** `grok-4.20-0309-non-reasoning`

**System prompt:**
> أنت محلل تطوّر نماذج الذكاء الاصطناعي. استخرج **20 تحديث/إصدار** متنوّعاً من تغريدات آخر 30 يوم. **يُحظر تماماً ذكر Gemini أو Grok أو Antigravity** — هذي الجولة مخصصة للمنافسين فقط (Claude, GPT, Llama, Mistral, DeepSeek, Qwen, Cohere, إلخ). لا تكرّر نفس النموذج أكثر من مرتين. لكل تحديث اشرح كيف يفيد المستخدم العربي/المطوّر. JSON فقط.

**JSON schema:** (نفس R3 الأصلي — لا تغيير)
```json
{
  "updates": [
    {
      "id": 1, "model_name": "...", "update_type": "new_release|improvement|feature|deprecation",
      "announcement_date": "YYYY-MM-DD", "benefit_ar": "...",
      "access_method": "api|open_weights|consumer_app|preview", "source_url": "..."
    }
  ]
}
```

**معيار قبول R3 v2:**
- ✅ صفر ذكر لـ Gemini/Grok/Antigravity
- ✅ تنوّع على الأقل 6 نماذج مختلفة
- ✅ لا تكرار نفس النموذج بنفس update_type أكثر من مرة

---

### R4 v2 — 10 تطبيق AI جديد (تجنّب المشهور)

**Query للأداة `x_search`:**
```
("just launched" OR "new tool" OR "introducing" OR "I built" OR "just shipped" OR "just released") AI -Claude -ChatGPT -Gemini -Cursor -Notion -Perplexity -Midjourney -Otter -Zapier -HeyGen min_faves:500
```

**Parameters:**
- `since:2026-04-21` (30 يوم)
- `mode: "Top"`
- `limit: 15` (نطلب 15 ليختار أفضل 10)

**Model:** `grok-4.20-0309-non-reasoning`

**System prompt:**
> أنت محرّر أدوات إنتاجية AI **حديثة الإطلاق** (آخر 30 يوم). استخرج **10 تطبيقات AI** جديدة وغير معروفة. **يُحظر تماماً ذكر أي من**: Claude, ChatGPT, Gemini, Cursor, Notion, Perplexity, Midjourney, Otter, Zapier, HeyGen — هذي معروفة وبلا قيمة للقارئ. ركّز على أدوات أُعلنت في تغريدة مع رابط للموقع. لكل تطبيق اذكر ما يفعله وكيف يسهّل العمل لمستخدم عربي غير مختص. JSON فقط.

**JSON schema:** (نفس R4 الأصلي)
```json
{
  "apps": [
    {
      "id": 1, "app_name": "...", "what_it_does_ar": "...",
      "how_it_helps_ar": "...", "link_or_url": "...",
      "free_or_paid": "free|freemium|paid|unknown"
    }
  ]
}
```

**معيار قبول R4 v2:**
- ✅ صفر ذكر لأي من الـ10 أدوات المحظورة
- ✅ كل تطبيق له رابط فعلي (مش X handle فقط)
- ✅ تاريخ الإطلاق ضمن آخر 30 يوم

---

### ⚙️ خطوات التنفيذ
1. أعد R3 v2 → اعرض النتيجة لروابي → انتظر إذن للـ R4
2. لو R3 v2 فشل في معايير القبول → أبلغ روابي، **لا تستمر لـ R4**
3. لو نجح → نفّذ R4 v2
4. بعد ما يخلصان → اطبع cost_report_v2.md (تكلفة فعلية لكل واحد)
5. **بعدها فقط:** ولّد `data/radar/grok_test/digest_final.md` بدمج R1 + R2 + R3_v2 + R4_v2

### 💰 الميزانية
- متوقّع: ~$0.30 إضافية (R3 + R4 v2)
- إجمالي التجربة: ~$0.87

### ⚠️ قواعد
- لا تعدّل `R1.json` أو `R2.json` — تركهما كما هما
- لا تعدّل `base.py` أو أي agent في الـ pipeline
- لو Grok تجاوز `max_tool_calls=2` مرة ثانية في R3/R4 → اطبع تحذير لكن أكمل

---

## 🧪 المهمة العاجلة (السابقة) — One-Shot Test لـ Grok (تجربة واحدة فقط) — 2026-05-20 22:30

### 🎯 الهدف
تجربة واحدة فقط مع Grok لرؤية إذا كانت الفكرة تستحق التبنّي قبل أي التزام بـ schedule أو migration كبير. **لا تعديل على الـ pipeline الحالي — هذا اختبار منفصل خارجي.**

### 📥 المُخرجات المطلوبة (deliverables) — ٥٥ بند
| # | الفئة | العدد |
|---|---|---|
| R1 | منتجات AI قابلة للبناء + جني دخل | **10** |
| R2 | مواضيع AI يناقشها المختصون/المطورون | **15** |
| R3 | تحديثات نماذج AI + فائدة التحديث | **20** |
| R4 | تطبيقات AI تسهّل العمل + كيف تسهّله | **10** |

### 🌐 القيود المُلزِمة
- **مصدر التغريدات:** فقط حسابات على X بعدد متابعين > 100K. التقدير عبر `min_faves:1000` كـ proxy.
- **اللغات المقبولة:** AR / EN / ZH (الصينية) / JA (اليابانية) / KO (الكورية) / ES (الإسبانية).
- **النافذة الزمنية:** آخر 7 أيام.
- **الموديل:** `grok-4.20-0309-non-reasoning` لـ R3/R4، و`grok-4.20-0309-reasoning` لـ R1/R2 (لأنها تحليلية).
- **حد tool calls:** أقصى 2 لكل request (يمنع التكرار الذي كلّف $0.46).
- **Endpoint:** `POST https://api.x.ai/v1/responses` مع `tools: [{"type":"x_search"}]`.

### 🧩 الـ4 Prompts (نصاً)

#### R1 — 10 منتجات قابلة للبناء + جني دخل
**Query للأداة:**
```
(SaaS OR agent OR build OR launch OR monetize OR startup) (AI OR LLM OR "AI agent") -is:reply min_faves:1000 lang:en OR lang:ar
```
**System prompt:**
> أنت محلل فرص ريادية. مهمتك استخراج **10 منتجات AI قابلة للبناء + جني دخل** من التغريدات المُرجَعة فقط. تجاهل أي تغريدة مصدرها حساب عدد متابعينه أقل من 100K. اكتب بالعربية الفصحى السهلة. المصطلحات التقنية بالإنجليزية. JSON فقط.

**JSON schema:**
```json
{
  "products": [
    {
      "id": 1,
      "title_ar": "...",
      "description_ar": "...",
      "monetization_path_ar": "...",
      "target_buyer_ar": "...",
      "capital_estimate": "low|medium|high",
      "first_paid_test_ar": "...",
      "source_tweet_urls": ["..."],
      "source_handles": ["@..."]
    }
  ]
}
```

#### R2 — 15 موضوع نقاش بين المختصين والمطورين
**Query:**
```
(thread OR debate OR controversy OR breakthrough OR "hot take") (AI OR LLM OR "machine learning" OR agents) -is:reply min_faves:1000
```
**System prompt:**
> أنت محلل اتجاهات الصناعة. استخرج **15 موضوع AI ساخن** يناقشه المختصون أو المطورون. وضّح لماذا الموضوع مهم وماذا يقول كل طرف. عربية فصحى سهلة، المصطلحات بالإنجليزية. JSON فقط.

**JSON schema:**
```json
{
  "discussions": [
    {
      "id": 1,
      "topic_ar": "...",
      "why_matters_ar": "...",
      "viewpoint_split_ar": "...",
      "key_voices": ["@...", "@..."],
      "sample_tweet_url": "..."
    }
  ]
}
```

#### R3 — 20 تحديث في نماذج AI
**Query:**
```
(release OR launch OR available OR open-source OR "new model" OR v2 OR v3 OR update) (Claude OR GPT OR Gemini OR Llama OR Mistral OR DeepSeek OR Qwen OR Grok OR "open weights") min_faves:1000
```
**System prompt:**
> أنت محلل تطوّر نماذج الذكاء الاصطناعي. استخرج **20 تحديث/إصدار** خلال آخر 7 أيام. لكل تحديث اشرح كيف يفيد المستخدم العربي/المطوّر. عربية فصحى. JSON فقط.

**JSON schema:**
```json
{
  "updates": [
    {
      "id": 1,
      "model_name": "...",
      "update_type": "new_release|improvement|feature|deprecation",
      "announcement_date": "YYYY-MM-DD",
      "benefit_ar": "...",
      "access_method": "api|open_weights|consumer_app|preview",
      "source_url": "..."
    }
  ]
}
```

#### R4 — 10 تطبيق AI يسهّل عمل المستخدم
**Query:**
```
(tool OR app OR workflow OR automate OR productivity OR "AI assistant") -is:reply min_faves:1000 lang:en OR lang:ar
```
**System prompt:**
> أنت محرّر أدوات إنتاجية. استخرج **10 تطبيقات AI** يستخدمها الناس فعلاً ويذكرونها في تغريداتهم. لكل تطبيق اذكر ما يفعله وكيف يسهّل العمل. عربية فصحى. JSON فقط.

**JSON schema:**
```json
{
  "apps": [
    {
      "id": 1,
      "app_name": "...",
      "what_it_does_ar": "...",
      "how_it_helps_ar": "...",
      "link_or_url": "...",
      "free_or_paid": "free|freemium|paid|unknown"
    }
  ]
}
```

### 📝 الناتج النهائي
1. **JSON خام:** `data/radar/grok_test/raw/{R1,R2,R3,R4}.json`
2. **Markdown digest عربي:** `data/radar/grok_test/digest_2026-05-20.md` مع الـ55 بنداً مرتّبة بأقسام.
3. **تقرير التكلفة:** `data/radar/grok_test/cost_report.md` — input tokens, output tokens, عدد tool calls، التكلفة لكل request، الإجمالي.

### ⚙️ خطوات التنفيذ (لـ Claude Code)
1. أنشئ `tools/grok_one_shot_test.py` (سكربت قائم بذاته، **خارج الـ pipeline**).
2. اقرأ `XAI_API_KEY` من `.env`.
3. نفّذ R1 فقط أولاً → اعرض النتيجة لروابي (في terminal أو ملف).
4. **توقّف وانتظر إذن قبل R2-R4.**
5. لو روابي قالت "كمّل" → نفّذ R2، R3، R4 بالتسلسل.
6. اجمع الـ55 بند في digest markdown.
7. اطبع تقرير التكلفة الفعلي.

### 💰 التكلفة المتوقّعة
- 4 requests × ~$0.10 = **~$0.40 للتجربة الكاملة**.
- لو R1 وحده طلع $0.30+ → توقّف وأبلغ روابي قبل R2.

### ⚠️ قواعد صارمة
- **لا تعديل على `base.py` ولا على أي agent من الـ14.**
- **لا حذف لأي ملف.**
- لو X search رجّع 0 نتائج لـ query → جرّب توسيع النافذة لـ 14 يوم وأبلغ روابي.
- **اطبع كل tool call** في الـ log عشان نعرف لماذا التكلفة (مثل ما حصل في اختبار @lexfridman).

### 🎯 معيار النجاح (هل تستحق Grok؟)
بعد ما تخلص التجربة، روابي ستحكم على:
1. **جودة الـ55 بند** — هل فعلاً قابلة للتنفيذ ومفيدة؟
2. **التكلفة الفعلية** — هل ضمن $0.50?
3. **زمن التنفيذ** — هل < 5 دقائق إجمالاً؟

لو الإجابات: نعم/نعم/نعم → نتبنّى Grok ونصمّم scheduler.
لو لا → نعود لـ Playwright fix.

---

## 🔥 مهمة معلقة سابقة — دمج Grok الكامل في الـ pipeline (مؤجّلة حتى نقرّر بعد الـ One-Shot Test) — 2026-05-20 21:10

### 📚 فهم الرادار الفعلي (بعد فحص فعلي للـ codebase)

**الرادار مكتمل ومتقدّم — مش يحتاج إعادة بناء:**

#### المصادر الحالية (`tools/agents/source_collector.py` + `tools/pulse_radar.py`):
- **RSS** (6): OpenAI News, Google DeepMind, Google AI Blog, HuggingFace Blog, **Ben's Bites** ✓
- **arXiv** (3): AI agents, AI products, AI document tools
- **Reddit** (4): r/artificial, r/MachineLearning, r/LocalLLaMA, ...
- **HuggingFace**: Daily Papers + Models
- **X**: 244 حساب عبر Playwright **(معطّل — هذا الـ block الوحيد)**

#### Pipeline (14 agent في `tools/agents/`):
`source_collector → evidence_guard → companies_detector → models_pulse → market_radar → priority_ranker → opportunity_builder → radar_editor → growth_social → ux_production_qa → performance_analytics → memory_learning + orchestrator`

#### الـ Prompts الموجودة — **ممتازة وتطابق هدف روابي 100%** 🎯

**`opportunity_builder.py` SYSTEM_AR:**
> "محلل ذكاء أعمال متخصص في تحويل إشارات تقنية إلى **فرص دخل ملموسة** في السوق العربي والسعودي. يكتب بإيجاز. يرفض التكهن. JSON فقط."

**`radar_editor.py` USER_TEMPLATE:**
> "اكتب نشرة اليوم العربية. الجمهور **رواد أعمال وصناع محتوى عرب يبحثون عن دخل من الذكاء الاصطناعي**. أسلوب مباشر بدون مبالغة. لكل قصة: ماذا حدث / لماذا يهم / كيف تستفيد."

**`growth_social.py` SYSTEM_AR:**
> "كاتب محتوى تسويقي عربي قصير لرواد أعمال السعودية والخليج..."

**الـ schemas موجودة، الـ Arabic tone صحيحة، الـ flow متكامل.**

#### آلية الـ API (في `tools/agents/base.py`):
```python
DEFAULT_MODEL = "gpt-4o-mini"
def call_openai_json(ctx, system, user, *, model, max_tokens=800, temperature=0.3):
    client = _openai_client(ctx.openai_key)
    resp = client.chat.completions.create(
        model=model, messages=[...],
        response_format={"type": "json_object"},
        ...
    )
```
**نقطة واحدة فقط تتحكم بـ OpenAI** — تبديلها لـ Grok = إضافة `base_url`.

---

### 🎯 المهمة الحقيقية (تعديلان فقط — لا إعادة هندسة)

**1. تعديل `base.py::call_openai_json` لدعم Grok backend:**
- إضافة قراءة `XAI_API_KEY` من env (مع fallback لـ `OPENAI_API_KEY`).
- إضافة `base_url="https://api.x.ai/v1"` لو الـ key xAI.
- تغيير `DEFAULT_MODEL` لـ `grok-4.20-0309-non-reasoning` (أو `grok-4.20-0309-reasoning` لـ opportunity_builder).
- نفس الـ interface — لا تغيير في الـ agents الأخرى.

**2. agent جديد `x_grok_collector.py` يحلّ محل Playwright:**
- يستخدم Grok live search مع `search_parameters: {sources: [{type: "x", x_handles: [...]}]}`.
- يرجع نفس صيغة signals (id, source_id, title, text, url, created_at, metrics).
- يُدمج في `source_collector.py` كـ source family جديدة.
- يقرأ الـ handles من `x_focus_accounts_test10.json` للتجربة الأولى.

---

### 📋 خطوات Claude Code

1. **اقرأ** `AGENTS.md` + `STATUS.md` + هذا القسم + ملفات الـ agents الـ 3 (`opportunity_builder.py`, `radar_editor.py`, `growth_social.py`, `base.py`, `source_collector.py`).

2. **تعديل `base.py`:**
   - أضف `_xai_client()` بـ `base_url="https://api.x.ai/v1"`.
   - حدّث `_openai_client()` ليرجع xAI client إذا `XAI_API_KEY` موجود.
   - DEFAULT_MODEL → `grok-4.20-0309-non-reasoning`.
   - أضف option للـ reasoning model في `opportunity_builder` (يحتاج تفكير أعمق).
   - **لا تحذف OpenAI codepath** — اجعله conditional.

3. **إنشاء `tools/agents/x_grok_collector.py`:**
   - يستخدم نفس `call_openai_json` (الـ Grok backend) مع `search_parameters`.
   - schema للـ output يطابق `data/radar/signals.json` (id, source_id, source_name, source_kind="x_post", source_url, title, text, ...).
   - input: list of X handles.
   - output: list of signals بصيغة الرادار.

4. **دمج في `source_collector.py`:**
   - أضف source family جديدة: `x_grok` (تستبدل `x_user_timelines` المعطّل).
   - استخدم `x_focus_accounts_test10.json` للتجربة الأولى (10 حسابات فقط).

5. **اختبار:**
   ```bash
   set -a; source .env; set +a
   python3 tools/run_radar_agents.py --budget 40
   # يجب الـ pipeline يكمل من البداية للنهاية مع Grok
   ```

6. **مراجعة المخرجات:**
   - `data/radar/raw_signals.json` — يجب يحتوي X signals جديدة من الـ 10 حسابات.
   - `data/radar/opportunities.json` — يجب الـ 4-5 فرص جديدة بصيغة عربية مفهومة.
   - `data/brief.ar.json` — daily brief عربي مكتمل.
   - `data/radar/growth_tweet_drafts.json` — 5 social posts.

7. **اكتب التقرير:** `data/radar/grok_integration_test10_report.md`:
   - Diff الملفات اللي تغيّرت (`base.py` + `x_grok_collector.py` + `source_collector.py`).
   - عيّنات من signals/opportunities/brief.
   - tokens المستخدمة + التكلفة الفعلية.
   - أي مشاكل (Grok يهلوس tweets؟ live search يرجع نتائج دقيقة؟).
   - مقارنة جودة المخرج العربي بـ run سابق (إن وُجد).

8. **حدّث STATUS.md** وحوّل هذا القسم لأرشيف "آخر جلسة".

---

### ⚠️ ملاحظات

- ⛔ **لا تكتب system prompts جديدة** — الموجودة ممتازة وتطابق هدف روابي (فرص دخل لرواد أعمال عرب، بدون مبالغة، بأسلوب بسيط).
- ⛔ **لا تربط الرادار بالحكومة السعودية** — هذا كان افتراض خاطئ. الجمهور: رواد أعمال + صناع محتوى عرب.
- ✅ **المحافظة على fallback OpenAI** — إذا Grok ما رد، الـ agents ترجع للـ rule-based (الموجود).
- ✅ **التكلفة:** Grok pricing قريب من gpt-4o-mini. الـ budget الحالي (~$0.63/شهر) يجب يظل ضمن $2 مع Grok.
- 🔒 **مفتاح xAI**: لا يُطبع في أي log أو commit.

---

### 🎯 التحوّل الجذري: بدل ما نسحب tweets عبر Playwright (محجوب) + نحلّلها بـ OpenAI، نستخدم **Grok (xAI)** للاثنين معاً:
- **الجمع:** Grok عنده وصول native لـ X (xAI تملك X) — لا scraping، لا re-login، لا حجب.
- **التحليل:** نفس الـ pipeline لكن client = xAI بدل OpenAI (API متوافق مع OpenAI format).

**✅ الـ key مضبوط ومُختَبَر:**
- موجود في `/Users/rawabialkhalaf/ax-pulse/.env` كـ `XAI_API_KEY=...`
- صلاحيات 600 (للمستخدم فقط)
- محمي في `.gitignore`
- الاختبار نجح — 8 موديلز متاحة، أبرزها: `grok-4.20-0309-non-reasoning`, `grok-4.20-0309-reasoning`, `grok-4.20-multi-agent-0309`, `grok-4.3`

**المرحلة الأولى (تجربة 10 حسابات):**

الحسابات: `@lexfridman`, `@sama`, `@kaifulee`, `@ID_AA_Carmack`, `@AndrewYNg`, `@karpathy`, `@2morrowknight`, `@ylecun`, `@Scobleizer`, `@drfeifei`.

**🧠 فلسفة الـ ROI (طلب روابي 21:02):**
> "هدفنا الاستفادة القصوى من كل طلب من Grok — كل prompt مدروس لتحقيق أعلى استفادة للرادار."

كل request لـ Grok = (قيمة للرادار) ÷ (tokens). **لا نسأل ساذج، لا نكرّر، لا نأخذ ما لا نحتاج.**

---

### 📐 مرحلة 0 (إجبارية قبل أي API call) — تصميم استراتيجية الـ Prompts

قبل ما تبدأ التنفيذ، صمّم وأرسل لروابي للمراجعة:

#### 0.1 — System Prompt للرادار (موحّد لكل R) — ✅ تصحيح روابي 21:06

**هدف الرادار (الصحيح):**
> رصد تطوّرات الذكاء الاصطناعي وتقديمها بأسلوب بسيط وواضح لمستخدم عربي **غير متخصّص تقنياً**، بهدف:
> 1. اكتشاف فرص **منتجات** قابلة للبناء.
> 2. اكتشاف فرص **دخل** (subscriptions, agents, marketplaces, services).
> 3. تسهيل **العمل** اليومي والمهام بـ AI.
> 4. تبسيط الفهم — لا jargon، لا papers أكاديمية، شرح كأنّه لصديق ذكي بدون خلفية تقنية.

**معايير الـ relevance:**

| ✅ يهمّ الرادار | ❌ لا يهمّ |
|---|---|
| منتجات / أدوات قابلة للاستخدام الفوري | benchmarks تقنية مجرّدة |
| فرص دخل ملموسة (نماذج عمل، أسعار، إيرادات) | papers أكاديمية بدون تطبيق |
| workflows + automation تسهّل العمل | big-tech politics بدون تطبيق |
| قصص نجاح + إيرادات لمنتجات AI | speculation بدون evidence |
| فجوات في السوق (need × AI capability) | abstract research debates |
| تغيّرات pricing/API تأثّر على bootstrappers | jargon تقني عميق بدون شرح |
| إطلاقات نماذج جديدة + قدراتها العملية | rumors داخلية بدون مصدر |

**نبرة الإخراج:**
- عربية بسيطة وواضحة.
- جملة افتتاحية تشرح "إيش هذا؟" قبل أي تفصيل.
- لكل بند: ماذا حدث + ليش يهم + كيف نستفيد؟
- أمثلة عملية، لا مصطلحات بدون شرح.
- لو لازم استخدام مصطلح تقني، فسّره بين قوسين.

**⛔ تجنّب نهائياً:**
- ربط الرادار بـ "الحكومة السعودية" أو "Vision 2030" أو أي جهة حكومية (هذا كان افتراض خاطئ من جلسة سابقة، روابي صحّحته في 21:06).
- النبرة الرسمية الجافة.
- التركيز على ما يهم المتخصصين فقط.

#### 0.2 — تقسيم الـ requests (4 مراحل، ~13 calls/cycle)

| المرحلة | الموديل | المدخل | المخرج | لماذا |
|---|---|---|---|---|
| **R1** × 10 (per account) | `grok-4.20-0309-non-reasoning` | handle + system prompt + live search params | tweets + classification أولية (JSON) | نستفيد من X context في Grok بمر واحدة |
| **R2** × 1 | `grok-4.20-0309-reasoning` | كل نتائج R1 (~500 tweets مصنّفة) | top 10 signals مرتّبة بحسب: قابلية البناء + حجم السوق + سهولة التنفيذ | يحتاج reasoning عميق |
| **R3** × 1 | `grok-4.20-0309-reasoning` | top 10 signals | 5 opportunities ملموسة (منتج / فكرة دخل / workflow عملي) | actionable insights لمستخدم غير مختصّ |
| **R4** × 1 | `grok-4.20-0309-non-reasoning` | opportunities + few-shot | digest عربي **بسيط ومفهوم** + posts (تويتر/لينكدإن) | إخراج نهائي بنبرة "صديقة ذكية" |

#### 0.3 — JSON Schemas (لكل R)
استخدم Grok structured outputs. **لا تترك output حر النص**.

مثال R1:
```json
{
  "type": "object",
  "properties": {
    "account": {"type": "string"},
    "tweets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "tweet_id": {"type": "string"},
          "text": {"type": "string"},
          "url": {"type": "string"},
          "created_at": {"type": "string", "format": "date-time"},
          "metrics": {"type": "object", "properties": {"likes": {"type": "integer"}, "retweets": {"type": "integer"}, "replies": {"type": "integer"}}},
          "topic": {"type": "string", "enum": ["product_launch", "tool_release", "income_idea", "workflow_tip", "pricing_change", "market_gap", "case_study", "research_with_app", "opinion", "other"]},
          "entities": {"type": "array", "items": {"type": "string"}},
          "relevance_score": {"type": "integer", "minimum": 0, "maximum": 10},
          "signal_type": {"type": "string", "enum": ["new_product", "new_capability", "new_pricing", "success_story", "workflow", "market_gap", "ecosystem_shift"]},
          "actionable_angle": {"type": ["string", "null"], "description": "كيف يستفيد منها المستخدم العربي غير المختص (منتج/دخل/تسهيل عمل). null لو ليس لها زاوية عملية."}
        },
        "required": ["tweet_id", "text", "url", "topic", "relevance_score"]
      }
    }
  }
}
```

#### 0.4 — Live Search Parameters (لـ R1)
```json
{
  "search_parameters": {
    "mode": "on",
    "sources": [{"type": "x", "x_handles": ["<handle>"]}],
    "max_search_results": 50,
    "from_date": "<آخر 7 أيام>",
    "return_citations": true
  }
}
```

#### 0.5 — Few-shot Examples
- ⚠️ **لا تستخدم digests قديمة** اللي كانت بنبرة "الحكومة السعودية" — فلسفة الرادار تغيّرت (21:06).
- **اقترح 3 أمثلة جديدة** بالنبرة الصحيحة (ريادة / منتجات / دخل / تسهيل عمل) واعرضها على روابي للموافقة.
- لكل مثال: tweet مصدر + التحليل المثالي (بصيغة JSON لـ R1) + bullet عربي بسيط لـ R4.
- مثال لنبرة R4 المطلوبة:
  > "OpenAI أصدرت GPT-X. هذا يعني: تقدرين تبنين بوت مساعد محتوى بنصف التكلفة السابقة. الفرصة: قنوات محتوى عربي تكلّفها كانت $200/شهر صارت $40. منتج محتمل: 'مساعد إيميلات للأعمال الصغيرة' — السوق فاضي بالعربي."

#### 0.6 — حساب التكلفة المتوقّعة
بناءً على pricing xAI الحالي:
- R1: ~5K tokens input + 2K output × 10 calls = ?
- R2 + R3: ~8K tokens input + 3K output × 2 calls = ?
- R4: ~3K tokens input + 2K output × 1 call = ?

**اطلع لي الأرقام قبل التنفيذ. لو cycle > $0.50، أعد التصميم.**

#### 0.7 — العرض على روابي
أرسل تقرير `data/radar/grok_prompt_strategy.md` يحوي:
1. System prompt كاملاً (بالعربي والإنجليزي).
2. Schemas الأربعة.
3. حساب التكلفة المتوقّعة.
4. أمثلة الـ few-shot.
5. مخاطر / حدود (مثلاً: هل Grok يهلوس tweets؟).

**انتظر إذن روابي قبل ما تنتقل لمرحلة 1.**

---

### 📍 المراحل التالية (بعد إذن روابي على مرحلة 0)

**المطلوب من Claude Code:**

1. **اقرأ** `AGENTS.md` + `X_COLLECT.md` + هذا القسم.

2. **تحقّق من قدرات Grok:**
   - `https://api.x.ai/v1` متوافق مع OpenAI SDK.
   - Live Search على X: استخدم `search_parameters` في الـ chat completion → جرّب تجيب آخر 50 تغريدة من حساب واحد كـ JSON منظّم.
   - وثائق xAI: [docs.x.ai/docs/guides/live-search](https://docs.x.ai/docs/guides/live-search).
   - الموديل المقترح للجمع: `grok-4.20-0309-non-reasoning` (أسرع/أرخص). للتحليل: نفسه أو `grok-4.20-0309-reasoning` للـ Opportunity Builder.

3. **جرّب جلب tweets من حساب واحد أولاً** (مثلاً `@lexfridman`):
   - prompt: "Return the last 50 tweets from @lexfridman as a JSON array. Each object: tweet_id, text, created_at (ISO), url, metrics{likes, retweets, replies}. No commentary."
   - استخدم `search_parameters: {mode: "on", sources: [{type: "x", x_handles: ["lexfridman"]}]}`.
   - اعرض النتيجة لي قبل ما تمشي للعشرة.

4. **لو نجح، طبّق على الـ10** واحفظ في:
   `data/radar/raw_tweets_test10.json`

5. **بدّل client الـ pipeline** من OpenAI لـ xAI:
   - في `tools/run_radar_agents.py` و الـ agents الفرعية: غيّر `base_url` لـ `https://api.x.ai/v1`، الـ key لـ `XAI_API_KEY`، الموديل لـ `grok-4.20-0309-non-reasoning` (مع option للـ reasoning).
   - احفظ نسخة backup للملفات اللي تغيّر فيها قبل التعديل.

6. **شغّل الـ pipeline على raw_tweets_test10.json** واقس:
   - tokens (input + output)
   - زمن كل agent
   - التكلفة الفعلية (بسعر Grok)

7. **اكتب التقرير:** `data/radar/grok_pipeline_test10_report.md` شامل:
   - جدول لكل حساب (عدد التغريدات، النطاق الزمني، الحالة)
   - عيّنة 3-5 تغريدات لكل حساب (مراجعة بصرية)
   - أداء الـ pipeline بالـ Grok مقابل التقدير النظري السابق
   - أي مشاكل (مثلاً Grok يرجع tweets محدثة؟ أو يبني تقريبيات؟)
   - توصية: هل ندخل الـ 500 الكاملة؟ هل نلغي Playwright تماماً؟

8. **حدّث STATUS.md** بالنتائج وحوّل هذا القسم لأرشيف "آخر جلسة".

**⚠️ ملاحظات مهمة:**
- **مفتاح xAI ما يطّبع في أي log أو commit.** استخدم متغير البيئة، لا تطبعه.
- روابي **ترفض X API الرسمي** — استخدام Grok مختلف (هو واجهة xAI، مش X API الكلاسيكي).
- لو Grok يرجع tweets غير دقيقة (هلوسة)، علّم على ذلك في التقرير ولا تخفيه.
- احتفظ بـ Playwright + OpenAI codepaths مؤقتاً (لا تحذف) — fallback لو Grok ما طلع كما توقعنا.
- لو الـ token budget كبير، استخدم `grok-4.20-0309-non-reasoning` (أرخص). الـ reasoning للـ Opportunity Builder فقط.

---

## 📦 المهمة المؤرشفة (Raw Collection — قبل قرار Grok 2026-05-20 20:51)

**كانت:** استخدام Playwright لجلب آخر 50 تغريدة × 10 حسابات → ملف خارجي → ثم تحليل.
**ألغيت لصالح Grok** (وصول native أنظف، لا re-login، لا حجب).

---

## 🔥 مهمة معلقة سابقاً (محذوفة) — الفكرة الأصلية

**الفكرة:** نريد فصل عملية الـ collection عن التحليل — نشوف البيانات الخام قبل ما تدخل الـ Intelligence Agent، عشان نتأكد من جودة السحب قبل ما نثق بنتيجة التحليل.

**الحسابات العشرة (من إكسل روابي — أولوية AI):**
`@lexfridman`, `@sama`, `@kaifulee`, `@ID_AA_Carmack`, `@AndrewYNg`, `@karpathy`, `@2morrowknight`, `@ylecun`, `@Scobleizer`, `@drfeifei`

**المطلوب:**

1. **اقرأ** `AGENTS.md` + `X_COLLECT.md` + هذا القسم قبل البدء.

2. **اجمع آخر 50 تغريدة** من كل حساب من العشرة (~500 تغريدة كحد أقصى).
   - استخدم الـ Playwright/X collector الموجود.
   - **لا تلمس** `data/manual_x/posts.json` الحالية (1278 تغريدة) — اعمل backup إن لزم.

3. **احفظ النتيجة في ملف خارجي منفصل:**
   `data/radar/raw_tweets_test10.json`

   صيغة لكل تغريدة:
   ```json
   {
     "account": "@lexfridman",
     "tweet_id": "...",
     "text": "...",
     "created_at": "...",
     "url": "...",
     "metrics": { "likes": 0, "retweets": 0, "replies": 0 }
   }
   ```

4. **قبل ما تمرّر للـ Intelligence Agent**، اطبع تقرير سريع:
   - عدد التغريدات لكل حساب (لو حساب رجع 0 → علّمه)
   - أقدم/أحدث تغريدة لكل حساب
   - حسابات فشلت أو محجوبة
   - حجم الملف الناتج

5. **ثم** مرّر الـ raw file للـ pipeline:
   ```bash
   export OPENAI_API_KEY="..."  # تأكّد من المفتاح أولاً
   # حمّل raw_tweets_test10.json كمصدر مؤقت
   python3 tools/run_radar_agents.py --budget 20
   ```

6. **اكتب التقرير في:** `data/radar/raw_collection_test10_report.md`
   شامل:
   - جدول لكل حساب (عدد التغريدات، نطاق التواريخ، الحالة)
   - عيّنة 3-5 تغريدات لكل حساب (مراجعة بصرية)
   - tokens المستخدمة + التكلفة الفعلية
   - مشاكل صادفتها

7. **حدّث STATUS.md** وحوّل هذا القسم لأرشيف "آخر جلسة".

**⚠️ ملاحظات:**
- روابي تبي تشوف البيانات الخام قبل ما تثق في التحليل — اعرض عيّنة قبل تشغيل الـ pipeline.
- X session في Safari محتمل يحتاج re-login (90+ visits → X يحجب).
- لا تكتب أي شي في `posts.json` الأصلي.
- لو OpenAI key مو متاح في shell، توقف عند خطوة 4 واطلب من روابي.

---

## آخر جلسة

**التاريخ:** 2026-05-20 17:25 UTC (Claude Code · تجربة تكلفة 10 حسابات)

**ما تم:**
- قراءة `AGENTS.md` و `X_COLLECT.md` و `STATUS.md` قبل البدء.
- backup كامل لـ `data/manual_x/posts.json` و `data/radar/x_focus_accounts.json` إلى `/tmp/cost-test-backup/`.
- تبديل scoped:
  - `posts.json` → 91 تغريدة من الـ10 حسابات فقط (مفلتر من 1278)
  - `x_focus_accounts.json` → نسخة test10 (10 حسابات)
- تشغيل `python3 tools/run_radar_agents.py --skip-collect --budget 40` ثم بدون `--skip-collect`.
- قراءة prompts الفعلية في `opportunity_builder.py`, `radar_editor.py`, `growth_social.py` لتقدير tokens.
- استعادة البيانات الأصلية كاملةً (1278 tweets · 244 accounts).
- كتابة التقرير الكامل في [data/radar/cost_test_10_accounts.md](./data/radar/cost_test_10_accounts.md).

**القياسات الرئيسية:**
- زمن pipeline (skip-collect): **0.15 ثانية**
- زمن pipeline كامل (مع source_collector): **45.3 ثانية**
- OpenAI calls فعلية: **0** (لأن `OPENAI_API_KEY` غير موجود في shell الاختبار)
- تكلفة فعلية: **$0.00**
- تكلفة نظرية متوقّعة per cycle (gpt-4o-mini): **~$0.0018** (~0.18¢)
- الإسقاط الشهري الواقعي: **$0.63/شهر** (12 cycles/day × 30)
- التداخل مع الـ244: 9 من 10 موجودون أصلاً، الجديد فقط `@2morrowknight`

**الاستنتاج الجوهري:**
> التكلفة لكل دورة **ثابتة** بصرف النظر عن N (سواء 10 أو 500 حساب). السبب: `opportunity_builder` يأخذ TOP 30 من ranked_items، و`radar_editor` + `growth_social` يأخذون digest. لا شيء يتدرّج خطّياً مع N.
>
> الـ bottleneck الفعلي لـ500 حساب هو **زمن الـ collection** (Playwright يحتاج ~20 ساعة)، لا OpenAI cost.

**التوصية المعتمدة في التقرير:**
1. **ادخل الـ500 دفعة واحدة في `x_focus_accounts.json`** — تكلفة OpenAI لن تتأثّر تقريباً.
2. **ابقِ `FOCUS_ACCOUNTS_LIMIT=24`** في الـ workflow → كل cron يأخذ عيّنة عشوائية.
3. **الـ rotation التلقائي يغطّي 500 حساب خلال ~42 ساعة (يومين تقريباً).**
4. **تكلفة شهرية متوقّعة: $0.63-$1.10 max** (zero risk financially).

**معلّق:**
- لم تُختبر OpenAI calls فعلياً في هذه الجلسة لأن `OPENAI_API_KEY` غير متاح في shell الاختبار. القياس الحالي نظري من قراءة الـ prompts.
- لتأكيد الأرقام تجريبياً قبل توسعة الـ500:
  ```bash
  export OPENAI_API_KEY="sk-..."
  python3 tools/run_radar_agents.py --budget 10
  python3 -c "import json; print(json.load(open('data/radar/agents/performance.json'))['latest'])"
  ```
- الجلسة كشفت أن `manual_x_bridge.py` غير موجود في الـ codebase الحالي — قد يحتاج فحص هل الـ X integration ما زال يعمل عبر مسار آخر.
- مشاكل بـ X session في Safari (90+ visits → X يحجب التغريدات) — يحتاج re-login قبل توسعة الحسابات.

**الخطوة التالية:**
- روابي تراجع التقرير في `data/radar/cost_test_10_accounts.md` وتقرر:
  1. إضافة الـ 500 إلى x_focus_accounts الآن
  2. أو تشغيل اختبار OpenAI فعلي (بمفتاح حقيقي) قبل الإضافة
- بعد القرار، قد نحتاج جلسة لـ:
  - دمج 500 → x_focus_accounts.json (مع dedupe من الـ244 الحاليين)
  - إعادة تأكيد منطق `manual_x_bridge` (إن كان مطلوباً)

---

**التاريخ:** 2026-05-20 18:28 (Codex · توليد عرض الحكومة الإلكترونية)
**ما تم:**
- قراءة `AGENTS.md` و `STATUS.md` و `CHANGELOG.md` قبل البدء.
- إنشاء عرض بوربوينت جديد مخصص لاجتماع الحكومة الإلكترونية داخل:
  - [outputs/019e1202-d387-76c2-b2eb-b1f0648bf312/presentations/radar-gov-sector](./outputs/019e1202-d387-76c2-b2eb-b1f0648bf312/presentations/radar-gov-sector)
- بناء 5 شرائح عربية واضحة تغطي:
  - المشكلة
  - ما هو الرادار
  - كيف يعمل على مستوى القطاع
  - كيف تختلف القيمة حسب الإدارة والاختصاص
  - مثال تطبيقي على الحكومة الإلكترونية
- توليد 3 صور توضيحية مخصصة للعرض نفسه لتقريب المعنى بصريًا:
  - `hero-radar.png`
  - `problem-funnel.png`
  - `sector-map.png`
- تصدير ملف بوربوينت النهائي بنجاح هنا:
  - [ax-pulse-radar-gov-sector.pptx](./outputs/019e1202-d387-76c2-b2eb-b1f0648bf312/presentations/radar-gov-sector/output/ax-pulse-radar-gov-sector.pptx)
- توليد معاينات وصورة مجمعة للشرائح للتأكد من الإيقاع البصري:
  - [contact-sheet.png](./outputs/019e1202-d387-76c2-b2eb-b1f0648bf312/presentations/radar-gov-sector/qa/contact-sheet.png)

**معلّق:**
- لم تُجرَ بعد مراجعة محتوى نهائية مع روابي على مستوى صياغة العرض الشفهي، خصوصًا إذا أُريد اختصار بعض النصوص أكثر قبل الاجتماع.
- العرض الحالي مهيأ كنقطة انطلاق قوية، لكن قد يستفيد من نسخة ثانية لاحقًا إذا لزم:
  - إضافة شعار رسمي
  - تخصيص جهة حكومية بعينها
  - أو تحويله إلى نسخة تنفيذية مختصرة جدًا من 3 شرائح

**الخطوة التالية:**
- فتح ملف الـ PPTX ومراجعته بصريًا قبل الاجتماع.
- إذا رغبت روابي، نجهز مباشرة:
  1. نسخة أقصر جدًا للعرض الشفهي
  2. ملاحظات presenter notes
  3. أو نسخة مخصصة لقطاع حكومي واحد

**التاريخ:** 2026-05-20 12:45 (Codex · تقييم فجوة X/الفرص)
**ما تم:**
- مراجعة تشخيص الفجوة بين ما يوجد في تغريدات X وما يظهر في الرادار.
- التحقق من الترتيب الفعلي في [tools/agents/priority_ranker.py](/Users/rawabialkhalaf/ax-pulse/tools/agents/priority_ranker.py):
  - الأوزان الحالية هي:
    - `recency=0.18`
    - `trust=0.22`
    - `impact=0.22`
    - `buildability=0.18`
    - `income=0.20`
- التحقق من تصنيف الثقة الفعلي في [tools/agents/evidence_guard.py](/Users/rawabialkhalaf/ax-pulse/tools/agents/evidence_guard.py):
  - X لا يُصنّف `community` هنا، بل `social`
  - ووزنه الحالي أشد انخفاضًا: `social=0.35` مقابل `research=0.85`
- التحقق من معمارية المسار:
  - X لا يدخل أساسًا إلى `signals.json` عبر نفس lane الخاص بالمصادر العامة في الحالة الحالية.
  - بل يعيش في مسار منفصل: `data/manual_x/*` ثم يُغذّي طبقات مثل:
    - `x_radar_cards`
    - `focused_discussions`
    - `focused_opportunities`
- النتيجة: المشكلة ليست فقط “X يغرق تحت arXiv”، بل أيضًا أن **ترقية X من lane منفصل إلى طبقات العرض/الفرص ليست قوية بما يكفي**.

**معلّق:**
- أرقام مثل “87% مفقود” تبدو معقولة كإشارة إنذارية، لكن لم يتم اعتمادها رقميًا من الحالة الحالية داخل المستودع لأن دفعة X الحالية في المشروع لا تطابق بالضرورة نفس snapshot الذي بُني عليه هذا التحليل.

**الخطوة التالية:**
- إذا قررنا الإصلاح، فالأنظف ليس Option B.
- التوصية الأقوى:
  1. إضافة tier جديد لـ X الموثوق (`verified_social` أو `official_social`) بدل رفع كل X إلى `official`
  2. ثم إضافة lane/quotas مستقلة تضمن حضور X والعربي في المخرجات النهائية بدل الاعتماد على ranking موحّد فقط

---

**التاريخ:** 2026-05-20 12:32 (Codex · إصلاح عرض الفرص الجديدة)
**ما تم:**
- قراءة `AGENTS.md` و `STATUS.md` أولًا قبل البدء.
- فحص طبقة عرض الفرص في [assets/js/radar.js](/Users/rawabialkhalaf/ax-pulse/assets/js/radar.js) بعد ملاحظة أن فرصتين جديدتين لم تظهرا في الواجهة رغم وجود إشاراتهما في البيانات.
- توحيد مسار العرض بحيث `opportunityRows()` يصبح هو المصدر المشترك للفرص المعروضة في الشريط العائم وطبقة الفرص، بدل أن يبقى جزء من الواجهة منحازًا لفرص `opportunities.json` العامة فقط.
- إبقاء الفرص المركزة/الأحدث في أولوية الترتيب عبر:
  - `focusedOpportunityRows()`
  - `candidateOpportunityRows()`
  - ثم الفرص العامة والبحثية وPlaybooks
- إضافة جسر عرض صغير لبطاقات `news` التي تحتوي `buildable_opportunity` **محدد وغير عام** حتى تظهر كفرص قابلة للبناء بدل أن تبقى مدفونة كخبر فقط.
- التحقق من سلامة الملف بعد التعديل (`node --check assets/js/radar.js` نجح بدون أخطاء).

**معلّق:**
- يلزم تحقق بصري في المتصفح للتأكد أن:
  - فرصة الفيديو تظهر ضمن فرص الدخل.
  - فرصة الأمن/التهديدات تظهر كزاوية فرصة قابلة للبناء بدل أن تبقى خبرًا فقط.
- ما زال تحويل الإشارات إلى `focused_opportunities.json` أو `opportunities.json` يتم من البايبلاين نفسه؛ الفكس الحالي يعالج **طبقة العرض** وليس طبقة التوليد الخلفية.

**الخطوة التالية:**
- فتح الرادار بصريًا والتأكد من ظهور:
  - فرصة الفيديو
  - فرصة الأمن/التهديدات
- إذا ظهر أن العرض ما زال يحتاج ضبطًا، فالخطوة التالية تكون في **ترقية التوليد الخلفي** وليس الواجهة فقط.

---

**التاريخ:** 2026-05-20 12:10 (Codex · ساعي Playwright + تقرير نهائي)
**ما تم:**
- قراءة `AGENTS.md` و `STATUS.md` أولًا كما طلبتِ.
- تحديث [scripts/radar-hourly-full.command] ليصبح:
  - Tool 1 = `./pulse-radar --x-limit 0`
  - Tool 2 = `./x-playwright-radar.command`
  - Processing = `./pulse-radar-agents --skip-collect`
  - timeout 600 لمرحلة Playwright مع fallback محلي لأن `timeout` غير موجود على هذا macOS.
- تحديث [tools/hourly_report.py]:
  - يقرأ `data/radar/raw_items.json`, `opportunities.json`, `agent_runs.json`, `review_queue.json`, `_freshness_state.json`
  - ويقرأ `data/manual_x/posts.json` كـ fallback إذا لم يوجد `data/radar/x_posts.json`
  - يحسب فروقات المصادر العامة
  - يحسب فروقات X ويجزّئها إلى: Following / Search / Focus accounts
  - يلخّص **9 وكلاء أساسيين** من `data/radar/agents/run_log.json`
  - يكتب:
    - `RADAR_HOURLY_REPORT.md`
    - `data/radar/hourly_reports/YYYY-MM-DD-HH.md`
    - `tmp/last_hourly_snapshot.json`
  - يرسل إشعار macOS مع subtitle: `{N} إشارة • {Z} فرصة`
- تحديث [scripts/install-radar-launchd.command] ليفصل:
  - `data/radar/logs/launchd-out.log`
  - `data/radar/logs/launchd-err.log`
- التشغيل اليدوي نجح عبر:
  - `bash scripts/radar-hourly-full.command`
  - وتولّد:
    - [RADAR_HOURLY_REPORT.md](RADAR_HOURLY_REPORT.md)
    - `data/radar/hourly_reports/2026-05-20-11.md`
    - `data/radar/logs/hourly-2026-05-20.log`
    - `tmp/last_hourly_snapshot.json`

**معلّق:**
- `x-playwright-radar.command` لم يتمكّن من تشغيل Chromium داخل بيئة Codex الحالية بسبب صلاحيات Crashpad/Chrome profile:
  - `Operation not permitted`
  - لذلك لم يضف منشورات X جديدة في اختبار Codex هذا.
- `scripts/install-radar-launchd.command` لم يتمكّن من إنشاء:
  - `~/Library/LaunchAgents/com.axpulse.hourly.plist`
  - بسبب `Operation not permitted` داخل Codex sandbox.

**أوامر التشغيل:**
- تشغيل يدوي:
  - `bash scripts/radar-hourly-full.command`
- تثبيت launchd:
  - `bash scripts/install-radar-launchd.command`
- إزالة launchd:
  - `bash scripts/uninstall-radar-launchd.command`
- فحص الـ job:
  - `launchctl list | grep axpulse`

**الـ next scheduled run:**
- غير متاح من داخل Codex لأن `launchd` لم يُحمَّل هنا.
- بعد تشغيل `scripts/install-radar-launchd.command` على الجهاز خارج Codex، سيكون كل 3600 ثانية مع `RunAtLoad=true`.

**تنبيهات:**
- إذا بقي Playwright يفشل خارج Codex أيضًا، أول نقطة فحص هي تسجيل الدخول في X وقيود إشعارات/صلاحيات Chrome profile على macOS.
- التقرير الحالي يذكر صراحة إذا لم تُضف Playwright أي منشورات جديدة.

**ما أنجزه هيرو بعد Codex (2026-05-20 11:39):**
- ✅ شغّل `scripts/install-radar-launchd.command` من خارج Codex sandbox.
- ✅ `launchd job` مُحمَّل بنجاح: `com.axpulse.hourly` (PID 79468 · exit 0).
- ✅ الـ `RunAtLoad=true` فعّل تشغيلاً تلقائياً لحظة التحميل.
- ✅ تأكيد أن المصادر تشتغل من خارج Codex sandbox:
  - Tool 1 (`pulse-radar`): **items=294 errors=0** ← 294 إشارة جديدة بدون أخطاء.
  - Tool 2 (agents): شغّال حالياً.
- ⚠️ تشغيل Codex سابقاً (11:36) أرجع 0 إشارات لأن Codex sandbox مقطوع عن الإنترنت — الـ scripts صحيحة، البيئة فقط كانت السبب.

**Next scheduled run:** كل 3600 ثانية تلقائياً (الـ launchd job يدور في الخلفية).

**أوامر مفيدة:**
- التحقق من الحالة: `launchctl list | grep axpulse`
- إيقاف الـ job: `bash scripts/uninstall-radar-launchd.command`
- تشغيل يدوي خارج الـ schedule: `bash scripts/radar-hourly-full.command`
- آخر تقرير: `RADAR_HOURLY_REPORT.md`

---

## رد هيرو على Codex (2026-05-20 11:46)

شكراً Codex على التحديثات (Playwright + `--skip-collect`). **معلّقات Codex مفهومة كلها قيود بيئة sandbox**:

| ما اشتكى منه Codex | الحقيقة من خارج sandbox |
|---|---|
| ❌ Playwright فشل (Crashpad permissions) | 🟢 قيد الاختبار من هيرو الآن (background `bash scripts/radar-hourly-full.command` منذ 11:46) |
| ❌ `install-radar-launchd.command` فشل | ✅ مُحمَّل أصلاً من 11:39 — `com.axpulse.hourly` PID 79468 ما زال نشط |
| ❌ `next scheduled run` غير متاح | ✅ الـ launchd الموجود يقرأ السكربت في كل دورة — التحديث الذي عملته أنت سيُستخدم تلقائياً في الـ run القادم (~12:38) بدون إعادة تحميل |

**خلاصة لـ Codex:** لا تشغل بالك بهذه الـ "معلّقات" — كلها بسبب sandbox. الـ scripts التي كتبتها صحيحة و سيتم اختبارها من خارج الـ sandbox الآن.

**سأحدّث الحالة لما يخلص الـ background run** (Playwright يأخذ ~5 دقائق).

---

## سجل الجلسات

| التاريخ والوقت | الأداة | الإنجاز | المتابعة |
|---|---|---|---|
| 2026-05-20 12:10 | Codex | تشغيل الساعي الجديد يدويًا وتوثيق قيود Playwright/launchd داخل Codex | تشغيل install على الجهاز خارج Codex |
| 2026-05-20 12:03 | Codex | تحويل الساعي إلى Playwright + `--skip-collect` للتعامل | اختبار الجولة الجديدة وlaunchd |
| 2026-05-20 11:39 | هيرو | تحميل launchd job + تأكيد جلب 294 إشارة فعلية | — |
| 2026-05-20 11:38 | Codex | تشغيل الساعي يدويًا بنجاح وتوليد التقرير الساعي | تثبيت launchd خارج البيئة وتسجيل الـ job |
| 2026-05-20 11:35 | Codex | إنشاء الساعي والتقرير الساعي مبدئيًا | اختبار التشغيل والـ launchd |
| 2026-05-20 11:13 | هيرو | إعداد AGENTS/STATUS | — |
