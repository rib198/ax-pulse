# الاشتراك والدفع — كيفية الربط بـ Stripe

> هذه الصفحة موجهة للمطوّر/المالك. لا تُنشر للمستخدم النهائي.

## الوضع الحالي

تم تجهيز كامل الواجهة + منطق العميل (`assets/js/subscription.js`) + الصفحات (`subscribe.html`, `account.html`).
**الدفع الحقيقي غير مفعّل بعد** لأنه يحتاج خادمًا (الموقع الحالي ثابت على GitHub Pages).

عند الضغط على «اشترك الآن» الآن:
- يُسجَّل حدث `checkout_started` محلياً.
- في غياب backend ينعكس المستخدم لصفحة `subscribe.html` (fallback).
- إذا أعدت توجيهه يدوياً بـ `?status=success&session_id=...` يفعّل اشتراكه محلياً (لأغراض الاختبار).

## ما تحتاج إنجازه لتفعيل الدفع الحقيقي

### 1) إنشاء حساب Stripe + منتج
1. سجّل على <https://stripe.com> ثم أنشئ منتجاً باسم *Radar Subscription* بسعر **$15/شهر**.
2. خذ `price_id` (يبدأ بـ `price_...`).
3. خذ المفاتيح: `pk_test_...` (publishable) و `sk_test_...` (secret) و `whsec_...` (webhook).

ضعها في `.env` (لا تلتزمها للريبو):

```
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

### 2) إضافة وظائف Serverless

أضف هاتين الوظيفتين في Vercel أو Netlify Functions:

#### `api/checkout/session.js` — إنشاء جلسة Stripe Checkout

```js
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();
  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{ price: process.env.STRIPE_PRICE_ID, quantity: 1 }],
    success_url: `${process.env.SITE_URL}/account.html?status=success&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url:  `${process.env.SITE_URL}/subscribe.html?status=cancelled`,
    locale: 'ar'
  });
  res.json({ url: session.url });
}
```

#### `api/checkout/webhook.js` — استقبال أحداث Stripe

```js
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export const config = { api: { bodyParser: false } };

export default async function handler(req, res) {
  const sig = req.headers['stripe-signature'];
  const buf = await getRawBody(req);
  let event;
  try {
    event = stripe.webhooks.constructEvent(buf, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    return res.status(400).send(`Webhook error: ${err.message}`);
  }

  switch (event.type) {
    case 'checkout.session.completed':
    case 'customer.subscription.created':
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted':
      // TODO: persist subscription state in your DB keyed by customer email
      break;
  }
  res.json({ received: true });
}
```

### 3) ربط الواجهة

`assets/js/subscription.js` يقرأ `data/config.json` تلقائياً ويبحث عن `stripe.checkout_session_endpoint`.
عندما يكون المسار يبدأ بـ `/api/...` فإن `StartCheckout()` ينادي الخادم ويعيد توجيه المستخدم
إلى الرابط القادم من Stripe.

عُدّل `data/config.json` إن لزم لتغيير `success_path` أو `cancel_path`.

### 4) (اختياري) تخزين الاشتراك في قاعدة بيانات

الـ frontend الحالي يحفظ الحالة في `localStorage`. هذا كافٍ للعرض ولكنه ليس مصدر حقيقة.
عند تجهيز قاعدة بيانات (Supabase أو غيرها):

- أضف endpoint `/api/me` يُرجع حالة المستخدم بناءً على cookie أو email magic-link.
- استبدل `IsUserSubscribed()` ليقرأ من `/api/me` بدلاً من localStorage.

## ملاحظات أمنية

- **حماية المحتوى المدفوع على موقع ثابت غير ممكنة بالكامل.** أي شخص يستطيع قراءة JSON الخام.
  حالياً نعتمد على إخفاء العرض في الواجهة. لحماية حقيقية:
  - انقل الفرص/الإشارات المدفوعة إلى endpoint محمي بـ Bearer token مرتبط باشتراك المستخدم.
  - أو وزّع المحتوى عبر بريد الـ digest فقط (الذي يحتاج اشتراكاً للوصول).
- **لا تضع مفاتيح حقيقية في `data/config.json`** — هذا ملف عام يقرأه المتصفح.
- **استخدم Webhook signature verification دائماً** قبل تعديل حالة الاشتراك في قاعدة بياناتك.

## الاختبار اليدوي

محاكاة اشتراك ناجح بدون Stripe:
1. افتح `account.html`.
2. شغّل في console:
   ```js
   RadarSubscription.HandlePaymentSuccess({ session_id: 'cs_test_local' });
   location.reload();
   ```
3. ستظهر الحالة «اشتراك فعّال». المحتوى المدفوع سيُكشف.

محاكاة إلغاء/فشل:
```js
RadarSubscription.CancelLocalSubscription();
location.reload();
```

## السعر — مكان واحد فقط

سعر الاشتراك يُقرأ من `data/config.json` → `subscription.price_usd` و `price_label_ar` و `price_label_en`.
لا تكتبه في الكود مرة أخرى. أي مكان يحتاج عرض السعر يستخدم المساعد `priceLabel()` في `assets/js/app.js` أو يقرأ
الـ config مباشرة.
