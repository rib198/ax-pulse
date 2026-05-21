# STATUS — AX Pulse

> ملف الحالة الحيّ. حدّثه بعد كل جلسة Claude Code أو Codex.

## آخر جلسة

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
