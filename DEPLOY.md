# AX Pulse — نشر سحابي 24/7 عبر GitHub Actions

النتيجة المتوقعة: الموقع يعمل على رابط عام، البيانات تتحدّث كل ساعتين تلقائياً، حتى لو ماكك مغلق.

---

## ما تم تجهيزه محلياً (جاهز للرفع)

| الملف | الدور |
|------|------|
| `.gitignore` | يستبعد `.ai-bridge/`, secrets, exports, ملفات النظام |
| `.github/workflows/refresh-radar.yml` | **cron كل ساعتين** يشغّل pulse_radar + translate_signals ويُحدّث `data/radar/*.json` |
| `.github/workflows/deploy-pages.yml` | ينشر الموقع كاملاً على GitHub Pages عند كل تحديث |
| Initial commit | `969ca0c` — 68 ملف |

---

## خطواتك (10 دقائق)

### 1. أنشئ مستودع GitHub جديد
- اذهب: <https://github.com/new>
- الاسم: `ax-pulse` (أو ما تشاء)
- نوعه: **Public** ⚠️ (مهم: GitHub Pages مجاني للـ public فقط بحساب free)
- لا تضع README ولا .gitignore (موجودين عندنا)
- اضغط **Create repository**

### 2. اربط المستودع المحلي بـ GitHub وادفع
```bash
cd /Users/rawabialkhalaf/ax-pulse
git remote add origin https://github.com/<YOUR_USERNAME>/ax-pulse.git
git push -u origin main
```
استبدل `<YOUR_USERNAME>` باسمك.

### 3. أضف X Bearer Token كـ Secret
- اذهب: `https://github.com/<YOUR_USERNAME>/ax-pulse/settings/secrets/actions`
- اضغط **New repository secret**
- الاسم: `X_BEARER_TOKEN`
- القيمة: التوكن من `developer.x.com` (الذي تستخدمه محلياً)
- **Add secret**

### 4. فعّل GitHub Pages
- اذهب: `https://github.com/<YOUR_USERNAME>/ax-pulse/settings/pages`
- **Source**: GitHub Actions (وليس "Deploy from a branch")
- اضغط Save

### 5. اختبر التشغيل اليدوي قبل cron
- اذهب: `https://github.com/<YOUR_USERNAME>/ax-pulse/actions`
- اختر **Refresh AI Radar**
- اضغط **Run workflow** → **Run workflow**
- انتظر 2-5 دقائق، يجب أن تظهر علامة ✓
- إذا نجح: ستجد commit جديد بعنوان `chore(radar): auto-refresh ...`

### 6. تحقق من الموقع المنشور
بعد دقيقتين من التشغيل الناجح، الموقع يعمل على:
```
https://<YOUR_USERNAME>.github.io/ax-pulse/
```
صفحات:
- `https://<YOUR_USERNAME>.github.io/ax-pulse/`            → الهبوط
- `https://<YOUR_USERNAME>.github.io/ax-pulse/dashboard.html`
- `https://<YOUR_USERNAME>.github.io/ax-pulse/radar.html`  → الرادار الحي

---

## الجدولة الفعلية

| النشاط | متى |
|--------|-----|
| تحديث البيانات | كل **ساعتين** (cron `0 */2 * * *`) |
| إعادة نشر الموقع | **فوراً** بعد كل commit (~1 دقيقة) |
| إجمالي زمن الاستجابة | ~2-5 دقائق من cron إلى ظهور التحديث |
| تشغيل يدوي | متاح من تبويب Actions في أي وقت |

---

## التكلفة

| العنصر | الحد المجاني | استخدامك المتوقع |
|-------|-------------|-----------------|
| GitHub Actions (public repo) | **بلا حدود** | ~3 دقائق × 12 تشغيل/يوم = 36 دقيقة/يوم ✓ |
| GitHub Pages bandwidth | 100 GB/شهر | بيانات JSON صغيرة، لا قلق |
| X API Basic | 10k tweets/شهر | 25 × 12 × 30 = 9000/شهر ضمن الحد |

**التكلفة الفعلية: $0 شهرياً** (إذا أبقيت المستودع public).

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| Action فشل في "Refresh radar" | افحص اللوغ — غالباً `X_BEARER_TOKEN` مفقود أو منتهي |
| `git push` رفضك بسبب credentials | استخدم Personal Access Token بدل كلمة المرور |
| Pages لا يظهر | تأكد أن Settings → Pages → Source = "GitHub Actions" |
| Cron لا يعمل | GitHub قد يؤخر cron في public repos أيام النشاط المنخفض — جرّب تشغيل يدوي أولاً |

---

## كيف تعرف أن كل شيء يعمل

1. **Actions tab** يظهر تشغيل ناجح كل ساعتين بعلامة ✓
2. **Commits** الجديدة بعنوان `chore(radar): auto-refresh YYYY-MM-DD HH:MM UTC`
3. **الموقع المنشور** على `<username>.github.io/ax-pulse/radar.html` يعرض signals بتواريخ حديثة جداً
4. **آخر تحديث** في الواجهة يتطابق تقريباً مع زمن آخر cron run
