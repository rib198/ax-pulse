# AX Pulse — Daily Email Digest Setup

النتيجة: المشتركون يستلمون نشرة عربية يومية في 9:30 صباحاً، تحوي أهم 5 إشارات + الفرصة الأولى، مع رابط للموقع.

---

## ما تم بناؤه (محلياً)

| الملف | الدور |
|------|------|
| `tools/build_digest.py` | يبني HTML عربي + يرسل عبر Resend API (stdlib فقط) |
| `data/subscribers.json` | قائمة المشتركين (يبدأ ببريدك) |
| `subscribe.html` | صفحة هبوط للاشتراك (Formspree form) |
| `.github/workflows/daily-digest.yml` | cron يومي 6:30 UTC = 9:30 KSA |

---

## خطواتك (15 دقيقة)

### 1. إنشاء حساب Resend (إرسال الإيميل)
- اذهب: <https://resend.com/signup>
- سجّل بـ بريدك (`ibrrawabi@gmail.com`)
- بعد التسجيل: <https://resend.com/api-keys> → **Create API Key**
  - Name: `ax-pulse-prod`
  - Permission: `Sending access`
- انسخ المفتاح (يبدأ بـ `re_...`) — لن يظهر مرة أخرى

**الحدود المجانية:** 3,000 إيميل/شهر، 100/يوم. كافٍ للمرحلة الأولى.

### 2. إضافة المفتاح كـ Secret في GitHub
- اذهب: <https://github.com/rib198/ax-pulse/settings/secrets/actions>
- **New repository secret**:
  - Name: `RESEND_API_KEY`
  - Secret: ألصق المفتاح
  - **Add secret**

### 3. إنشاء نموذج Formspree (لجمع المشتركين من subscribe.html)
- اذهب: <https://formspree.io/register>
- سجّل بـ بريدك
- بعد الدخول: **+ New Form**
  - Form name: `AX Pulse Subscribers`
  - Email recipient: `ibrrawabi@gmail.com`
  - Click **Create Form**
- انسخ الـ Form ID من الرابط (مثل `xkgwabcd`)

### 4. ضع Form ID في subscribe.html
```bash
cd /Users/rawabialkhalaf/ax-pulse
# استبدل YOUR_FORMSPREE_ID بـ ID الذي حصلت عليه
sed -i '' 's|YOUR_FORMSPREE_ID|xkgwabcd|g' subscribe.html
git add subscribe.html
git commit -m "chore: wire Formspree subscribe form"
git push
```

### 5. اختبار محلي للـ digest (قبل الإرسال الحقيقي)
```bash
cd /Users/rawabialkhalaf/ax-pulse
DRY_RUN=1 python3 tools/build_digest.py
# يكتب tmp/digest-<التاريخ>.html — افتحه في المتصفح للمعاينة
open tmp/digest-2026-05-03.html
```

### 6. تشغيل أول إيميل حقيقي يدوياً (اختبار GitHub Actions)
- اذهب: <https://github.com/rib198/ax-pulse/actions/workflows/daily-digest.yml>
- اضغط **Run workflow** → **Run workflow**
- انتظر دقيقة، ثم تحقق من بريدك (`ibrrawabi@gmail.com`)
- يجب أن تستلم النشرة كاملة

---

## كيف يصل المشترك الجديد للقائمة

```
زائر يدخل subscribe.html
   ↓ يدخل بريده
Formspree يستقبل الإرسال
   ↓ يرسلك إيميل: "مشترك جديد: x@example.com"
أنت تنسخ البريد + تضيفه يدوياً لـ data/subscribers.json
   ↓ git commit + push
الـ daily-digest workflow التالي يرسل له تلقائياً
```

**لماذا يدوي؟** لتفادي bots + spam في البداية. عند 50+ مشترك سننتقل لأتمتة كاملة.

---

## التكلفة

| الخدمة | الحد المجاني | استخدامك |
|--------|-------------|----------|
| Resend | 3,000 إيميل/شهر | 30 إيميل/يوم × 30 = 900/شهر ✓ |
| Formspree | 50 إرسال/شهر | كافٍ للنمو الأولي ✓ |
| GitHub Actions | بلا حدود (public repo) | <2 دقيقة/يوم ✓ |
| **الإجمالي** | | **$0** |

---

## التحسينات المؤجلة

- ✗ تخصيص اللغة (AR/EN) لكل مشترك
- ✗ تتبع open rate / click rate (Resend يدعمه — يحتاج enabling)
- ✗ زر إلغاء الاشتراك في الإيميل
- ✗ Domain verification في Resend (الآن يرسل من `onboarding@resend.dev`)
- ✗ Auto-add subscribers (بدل يدوي عبر JSON)

كلها قابلة للتنفيذ لاحقاً عند الحاجة.
