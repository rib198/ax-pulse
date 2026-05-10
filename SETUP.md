# دليل الإعداد — مرة واحدة فقط

> الزمن الكلي: ~25–35 دقيقة لشخص لديه حسابات GitHub فقط. الباقي مجاني.

بعد كل خطوة شغّل:

```bash
python3 tools/verify_setup.py --site https://radar.example.com --github-repo rib198/ax-pulse
```

سيُعلمك بالضبط ما الذي مرّ وما الذي يحتاج إصلاح.

---

## الخطوة 1 — مفتاح OpenAI كـ GitHub Secret (دقيقتان)

**ليه:** الوكلاء 7/8/12 يستخدمون OpenAI لكتابة الفرص والنشرة العربية. بدون المفتاح يسقط النظام تلقائياً لقواعد محلية (يعمل لكن أقل ذكاءً).

**اسم السكريت المقبول:** `AX_POST_AI` أو `OPENAI_API_KEY` — الـ workflow يقبل الاثنين (`secrets.AX_POST_AI || secrets.OPENAI_API_KEY`).

### الأسرع — عبر `gh` CLI

```bash
brew install gh   # إن لم يكن مثبتاً
gh auth login
gh secret set AX_POST_AI -R rib198/ax-pulse
# سيطلب منك لصق المفتاح، ثم Enter
```

### البديل — من واجهة GitHub

1. <https://github.com/rib198/ax-pulse/settings/secrets/actions>
2. **New repository secret**
3. Name: `AX_POST_AI` (أو `OPENAI_API_KEY` — الاثنان يعملان)
4. Secret: ألصق مفتاحك (يبدأ بـ `sk-...`)
5. **Add secret**

### كيف تتحقق

شغّل الـ workflow يدوياً:

```bash
gh workflow run refresh-radar.yml -R rib198/ax-pulse
gh run list -R rib198/ax-pulse --workflow refresh-radar.yml --limit 1
```

أو عبر الموقع: <https://github.com/rib198/ax-pulse/actions/workflows/refresh-radar.yml> → **Run workflow**.

في الـ summary يجب أن ترى `openai calls: 5+`.

---

## الخطوة 2 — نشر الـ API على Vercel (5 دقائق)

**ليه:** صفحة الاشتراك تنادي `/api/checkout/session` لإنشاء جلسة دفع آمنة. هذه الوظيفة تحتاج Node.js — لا تعمل على GitHub Pages.

### الأسرع — Deploy to Vercel button

افتح هذا الرابط في المتصفح:

```
https://vercel.com/new/clone?repository-url=https://github.com/rib198/ax-pulse&project-name=radar&env=STRIPE_SECRET_KEY,STRIPE_PRICE_ID,STRIPE_WEBHOOK_SECRET,SITE_URL,OPENAI_API_KEY&envDescription=Stripe%20keys%20from%20stripe.com/dashboard,%20SITE_URL%20is%20your%20final%20domain
```

سيفتح Vercel، يطلب منك تسجيل الدخول بـ GitHub، ثم يطلب env vars (الخطوة 3 توضح من أين).

### البديل — `vercel` CLI

```bash
npm i -g vercel
cd /Users/rawabialkhalaf/ax-pulse
vercel login
vercel --prod
# اتبع التعليمات؛ سيكتشف vercel.json تلقائياً
```

بعد النشر، Vercel يعطيك URL مثل `https://radar.vercel.app` — احفظه (سنحتاجه في `SITE_URL`).

### كيف تتحقق

```bash
curl -X POST https://radar.vercel.app/api/checkout/session
# يجب أن ترجع 500 + رسالة "server_misconfigured" (لأننا لم نضع env vars بعد).
# هذا متوقع — الخطوة 3 تكملها.
```

---

## الخطوة 3 — مفاتيح Moyasar (الموصى به للسوق السعودي/الخليجي)

**ليه:** Moyasar يدعم mada و Apple Pay و Visa و Mastercard، يقبل البطاقات المحلية بدون اضطراب، ولا تخزّن أنت بيانات البطاقة (PCI scope = صفر).

### 3.1 إنشاء حساب + الحصول على المفاتيح

1. <https://moyasar.com/register> — وقّع حسابًا.
2. ابدأ بـ **وضع الاختبار (Test mode)** من dashboard.
3. **Settings → API Keys** → انسخ:
   - `pk_test_...` (Publishable key)
   - `sk_test_...` (Secret key)

### 3.2 إضافتها في Vercel

#### الأسرع — `vercel` CLI

```bash
cd /Users/rawabialkhalaf/ax-pulse
vercel env add MOYASAR_SECRET_KEY production
# الصق sk_test_...
vercel env add MOYASAR_PUBLISHABLE_KEY production
# الصق pk_test_...
vercel env add SITE_URL production
# الصق https://radar.vercel.app
vercel env add MOYASAR_CALLBACK_URL production
# الصق https://radar.vercel.app/api/checkout/moyasar-callback
vercel env add PRICE_AMOUNT production
# 1500   (15.00 SAR — أو غيّره: 5625 لـ 56.25 ريال ≈ $15)
vercel env add PRICE_CURRENCY production
# SAR    (أو USD، AED، KWD، BHD، OMR، EUR، GBP)
vercel --prod
```

#### البديل — واجهة Vercel

Project → **Settings → Environment Variables** → أضف كل واحد على Production.

### 3.3 إعداد الـ callback في Moyasar Dashboard

1. <https://dashboard.moyasar.com/settings/webhook> أو **Settings → Webhooks**
2. **Add Endpoint**:
   - URL: `https://radar.vercel.app/api/checkout/moyasar-callback`
   - Events: اختر «Invoice paid»، «Invoice failed»، «Payment paid»
3. (اختياري) في **Settings → Callbacks** أضف نفس الـ URL لتأكيد المعاملات.

### كيف تتحقق

```bash
curl -X POST https://radar.vercel.app/api/checkout/moyasar -H 'Content-Type: application/json' -d '{}'
# يجب أن ترجع 200 + JSON يحوي "url": "https://api.moyasar.com/v1/invoice/inv_..."
# افتح الـ url في المتصفح → ستظهر صفحة Moyasar للدفع التجريبي.
# استخدم بطاقة test: 4111 1111 1111 1111، CVV أي 3 أرقام، تاريخ مستقبلي.
```

أو شغّل المُتحقق:

```bash
python3 tools/verify_setup.py --site https://radar.vercel.app --skip gh,admin
```

ستظهر `✓ Stripe Checkout session created` (الفاحص يعمل بشكل عام لأي provider يرجع `url`).

### 3.4 تبديل المزوّد

`data/config.json.payment_provider` افتراضيًا `"moyasar"`. لتجربة Stripe بدلًا عنه، غيّره إلى `"stripe"` وعد للخطوة الـ Stripe الأصلية (محفوظة أدناه).

---

## (اختياري) Stripe — في حال أردت تجربة المزوّد البديل (8–10 دقائق)

**ليه:** الدفع الفعلي يحتاج 4 قيم من Stripe.

### 3.1 إنشاء حساب + منتج

1. <https://dashboard.stripe.com/register> — وقّع حساب (مجاني، يدعم البطاقات السعودية).
2. ابق في **وضع الاختبار** (Test mode toggle أعلى يمين الصفحة).
3. **Products** → **+ Add product**
   - Name: `Radar Subscription`
   - Description: `الاشتراك الشهري في الرادار`
   - Pricing: **Recurring**, **15.00 USD**, **Monthly**
   - Save product
4. في صفحة المنتج، انسخ **Price ID** (يبدأ بـ `price_...`).

### 3.2 المفاتيح

من <https://dashboard.stripe.com/apikeys>:
- **Publishable key** (`pk_test_...`) — للواجهة (اختياري حالياً).
- **Secret key** (`sk_test_...`) — للخادم.

### 3.3 إضافتها في Vercel

#### الأسرع — `vercel` CLI

```bash
cd /Users/rawabialkhalaf/ax-pulse
vercel env add STRIPE_SECRET_KEY production
# الصق sk_test_...
vercel env add STRIPE_PRICE_ID production
# الصق price_...
vercel env add SITE_URL production
# الصق https://radar.vercel.app   (الـ URL من الخطوة 2)
vercel --prod   # إعادة النشر بالقيم الجديدة
```

#### البديل — واجهة Vercel

Project → **Settings** → **Environment Variables** → أضف كل واحد على Production.

### كيف تتحقق

```bash
curl -X POST https://radar.vercel.app/api/checkout/session
# يجب أن ترجع 200 + JSON يحوي "url": "https://checkout.stripe.com/..."
```

أو شغّل المُتحقق:

```bash
python3 tools/verify_setup.py --site https://radar.vercel.app --skip gh,admin
```

سيظهر `✓ Stripe Checkout session created`.

---

## الخطوة 4 — Stripe Webhook (3 دقائق)

**ليه:** عند نجاح الدفع أو فشل التجديد، Stripe يرسل حدثاً لخادمك. بدون webhook لا تستطيع تتبّع التجديدات/الإلغاءات.

### الأسرع — `stripe` CLI

```bash
brew install stripe/stripe-cli/stripe
stripe login

# للاختبار محلياً:
stripe listen --forward-to https://radar.vercel.app/api/checkout/webhook
# يطبع whsec_... — انسخها
```

### البديل — واجهة Stripe

1. <https://dashboard.stripe.com/webhooks> → **+ Add endpoint**
2. Endpoint URL: `https://radar.vercel.app/api/checkout/webhook`
3. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Add endpoint
5. في صفحة الـ endpoint، اضغط **Reveal signing secret** → انسخ `whsec_...`

### إضافة المفتاح في Vercel

```bash
vercel env add STRIPE_WEBHOOK_SECRET production
# الصق whsec_...
vercel --prod
```

### كيف تتحقق

من Stripe Dashboard → الـ webhook → **Send test webhook** → اختر `checkout.session.completed` → **Send test event**. يجب أن يظهر **2xx response**.

أو من CLI:

```bash
stripe trigger checkout.session.completed
```

---

## الخطوة 5 — لوحة الإدارة (Decap CMS) — 5 دقائق

**ليه:** تحرير المحتوى من واجهة ويب بدلاً من تعديل JSON يدوياً.

### الخيار الأبسط — Netlify Identity

1. <https://app.netlify.com/start> — وقّع وقم بربط الريبو.
2. بعد النشر، افتح Site settings → **Identity** → **Enable Identity**.
3. **Identity** → **Settings and usage** → **Enable Git Gateway**.
4. **Identity** → **Invite users** → ضع بريدك → سيصلك دعوة، اقبلها واضبط كلمة المرور.

> ملاحظة: لا تحتاج Netlify كنشر رئيسي — Vercel يكفي. لكن Netlify Identity يبقى مجاناً ويوفر الـ auth لـ Decap.

### الخيار البديل — GitHub OAuth (بدون Netlify)

عدّل `admin/config.yml` ليستخدم backend `github` بدل `git-gateway`، ثم انشر OAuth proxy. تفاصيل: <https://decapcms.org/docs/github-backend/>

### كيف تتحقق

افتح `https://radar.vercel.app/admin/` — يجب أن تظهر لوحة دخول، تسجّل بالبريد المدعو، تتحرّر `data/config.json` و الفرص اليدوية و i18n.

---

## الخطوة 6 — Plausible Analytics (دقيقتان، اختياري)

**ليه:** متابعة الأحداث الحقيقية (subscribe_clicked, payment_success). بدونها الأحداث تبقى في console + localStorage.

### Plausible (مجاني 30 يوم، ثم $9/شهر — أو استخدم PostHog المجاني)

1. <https://plausible.io/register>
2. أضف موقعاً → ضع نطاقك (مثلاً `radar.vercel.app`).
3. عدّل `data/config.json`:
   ```json
   "analytics": {
     "plausible_domain": "radar.vercel.app",
     "plausible_script": "https://plausible.io/js/script.js"
   }
   ```
4. ادفع التغيير، Vercel ينشر تلقائياً.

### PostHog (مجاني حتى مليون حدث/شهر)

1. <https://app.posthog.com/signup>
2. خذ Project API key.
3. عدّل `data/config.json`:
   ```json
   "analytics": {
     "posthog_key": "phc_...",
     "posthog_host": "https://app.posthog.com"
   }
   ```

### كيف تتحقق

افتح موقعك في علامة تبويب جديدة، اضغط على «اشترك». ادخل لوحة Plausible/PostHog → سترى `pageview` + `subscribe_clicked`.

---

## التحقق الشامل

في النهاية شغّل:

```bash
python3 tools/verify_setup.py \
  --site https://radar.vercel.app \
  --github-repo rib198/ax-pulse
```

ستحصل على تقرير من 6 أقسام: ملفات محلية، صفحات الموقع، الـ config المنشور، Stripe، GitHub Actions، لوحة الإدارة. كل ما هو ✓ يعمل، وكل ✗ يأتي مع تلميح للإصلاح.

---

## مرجع سريع — متغيرات البيئة

| المتغير | أين | متى يلزم |
|---|---|---|
| `AX_POST_AI` (أو `OPENAI_API_KEY`) | GitHub Secrets + Vercel env | للوكلاء الذكية + مساعد الرادار `/api/chat` |
| `X_BEARER_TOKEN` | GitHub Secrets | اختياري — لجلب X بـ API الرسمي |
| `STRIPE_SECRET_KEY` | Vercel env | إنشاء جلسات الدفع |
| `STRIPE_PRICE_ID` | Vercel env | السعر $15/شهر من Stripe |
| `STRIPE_WEBHOOK_SECRET` | Vercel env | التحقق من توقيع أحداث Stripe |
| `SITE_URL` | Vercel env | لـ success/cancel redirects |
| `RESEND_API_KEY` | GitHub Secrets | إرسال النشرة اليومية بالبريد |

**لا تضع أيًا منها في الكود أو في الريبو.** كلها تُحفظ في Secrets/env vars خاصة بالمنصة.

---

## استكشاف الأخطاء

| العَرَض | المعنى | الإصلاح |
|---|---|---|
| `verify_setup.py: ✗ Stripe env vars: 500` | Vercel نشر الكود لكن المتغيرات غير مضبوطة | الخطوة 3.3 |
| `verify_setup.py: ✗ admin reachable: 404` | Vercel لم ينسخ مجلد `admin/` | تأكد من `vercel.json` ولا توجد قاعدة rewrite تخفيه |
| `gh run list: failure` | الـ workflow فشل | افتح run في GitHub، اقرأ السجل، عادةً secret ناقص |
| Stripe webhook returns 400 | توقيع غير صحيح | تأكد أن `STRIPE_WEBHOOK_SECRET` في Vercel هو نفس الـ `whsec_...` للـ endpoint |
| لوحة الإدارة تظهر فارغة | Netlify Identity لم يفعّل Git Gateway | الخطوة 5، بند 3 |

عند أي شك، شغّل `python3 tools/verify_setup.py --site ...` — ستظهر الرسالة الدقيقة.
