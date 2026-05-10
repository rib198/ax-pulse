/* Radar — chat assistant drawer.
 *
 * Lightweight UI on top of an OpenAI-backed serverless function.
 * Falls back to a "demo answer" when the function isn't deployed,
 * so the drawer is functional locally even without a backend.
 *
 * History stays in localStorage — never sent to a third party except
 * the assistant itself, and never persisted on the server.
 */
(function () {
  'use strict';

  const HIST_KEY = 'radar_chat_history_v1';
  const QUOTA_KEY = 'radar_chat_quota_v1';
  const ENDPOINT  = '/api/chat';
  const FREE_DAILY_LIMIT = 5;
  const SUB_DAILY_LIMIT = 50;

  const fab    = document.getElementById('chat-fab');
  const drawer = document.getElementById('chat-drawer');
  const close  = document.getElementById('chat-close');
  const body   = document.getElementById('chat-body');
  const form   = document.getElementById('chat-form');
  const input  = document.getElementById('chat-input');
  const sugBox = document.getElementById('chat-suggestions');
  const status = document.getElementById('chat-status');
  const quota  = document.getElementById('chat-quota');
  const quotaText = document.getElementById('chat-quota-text');

  if (!fab || !drawer || !form || !input) return;

  let busy = false;
  let pendingFocus = null;  // item the user came from (when opened via askAbout)

  /* ---------- Helpers ---------- */

  function isSubscriber() {
    return !!(window.RadarSubscription && window.RadarSubscription.IsUserSubscribed && window.RadarSubscription.IsUserSubscribed());
  }

  function todayKey() {
    return new Date().toISOString().slice(0, 10);
  }

  function readQuota() {
    try {
      const raw = JSON.parse(localStorage.getItem(QUOTA_KEY) || '{}');
      if (raw.day !== todayKey()) return { day: todayKey(), used: 0 };
      return raw;
    } catch (e) { return { day: todayKey(), used: 0 }; }
  }

  function writeQuota(q) {
    try { localStorage.setItem(QUOTA_KEY, JSON.stringify(q)); } catch (e) {}
  }

  function dailyLimit() { return isSubscriber() ? SUB_DAILY_LIMIT : FREE_DAILY_LIMIT; }

  function refreshQuotaUI() {
    const q = readQuota();
    const limit = dailyLimit();
    const remaining = Math.max(0, limit - q.used);
    if (remaining <= Math.max(2, Math.floor(limit / 4))) {
      quotaText.textContent = isSubscriber()
        ? `بقي لك ${remaining} سؤال اليوم`
        : `بقي لك ${remaining} من ${limit} أسئلة مجانية اليوم`;
      quota.hidden = false;
      const cta = document.getElementById('chat-quota-cta');
      if (cta) cta.style.display = isSubscriber() ? 'none' : 'inline';
    } else {
      quota.hidden = true;
    }
    return remaining;
  }

  function readHistory() {
    try { return JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); }
    catch (e) { return []; }
  }

  function writeHistory(list) {
    try { localStorage.setItem(HIST_KEY, JSON.stringify(list.slice(-50))); } catch (e) {}
  }

  function escape(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function linkify(text) {
    return escape(text)
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>')
      .replace(/\n/g, '<br>');
  }

  /* ---------- Render ---------- */

  function renderHistory() {
    const hist = readHistory();
    if (!hist.length) {
      body.innerHTML = `
        <div class="chat-welcome">
          <div class="chat-welcome-title">مرحبًا 👋 أنا مساعدك الذكي للرادار</div>
          <div class="chat-welcome-text">
            خبيرك المرافق — أشرح الأخبار التقنية، أبسّط المحتوى، أساعدك في وضع خطط عمل وخطط تفكير،
            أناقش الأفكار معك، وأكتب لك مسودات المحتوى. اختر دورًا من أدناه أو اسألني أيّ شيء.
          </div>
          <div class="chat-welcome-roles">
            <span>🎓 شارح</span>
            <span>🪞 مبسِّط</span>
            <span>🧭 مخطّط</span>
            <span>💡 شريك تفكير</span>
            <span>🛠 صانع أدوات</span>
            <span>✍️ كاتب مسودات</span>
          </div>
        </div>
      `;
      return;
    }
    body.innerHTML = hist.map(m => msgBubble(m)).join('');
    body.scrollTop = body.scrollHeight;
  }

  function msgBubble(m) {
    const isAssistant = m.role === 'assistant';
    const note = m.note ? `<div class="chat-bubble-note">${escape(m.note)}</div>` : '';
    const err  = m.error ? '<div class="chat-bubble-err">تعذّر الاستجابة. حاول مرة أخرى.</div>' : '';
    return `
      <div class="chat-msg chat-msg-${isAssistant ? 'assistant' : 'user'}">
        ${isAssistant ? '<span class="chat-avatar"></span>' : ''}
        <div class="chat-bubble">
          ${linkify(m.content || '')}
          ${note}
          ${err}
        </div>
      </div>
    `;
  }

  function appendMsg(msg) {
    const hist = readHistory();
    hist.push(msg);
    writeHistory(hist);
    body.insertAdjacentHTML('beforeend', msgBubble(msg));
    body.scrollTop = body.scrollHeight;
    if (sugBox) sugBox.style.display = 'none';
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'chat-msg chat-msg-assistant chat-typing';
    el.id = 'chat-typing';
    el.innerHTML = `
      <span class="chat-avatar"></span>
      <div class="chat-bubble"><span class="chat-typing-dots"><i></i><i></i><i></i></span></div>
    `;
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  }

  function hideTyping() {
    const el = document.getElementById('chat-typing');
    if (el) el.remove();
  }

  /* ---------- Networking ---------- */

  async function fetchContext() {
    /* Pulled fresh per request — small payload, ensures relevance. */
    async function tryGet(path) {
      try { const r = await fetch(path, { cache: 'no-cache' }); return r.ok ? await r.json() : null; }
      catch (e) { return null; }
    }
    const [signals, events, insights, opportunities, performance] = await Promise.all([
      tryGet('data/radar/signals.json'),
      tryGet('data/radar/agents/events.json'),
      tryGet('data/radar/agents/insights.json'),
      tryGet('data/radar/opportunities.json'),
      tryGet('data/radar/agents/performance.json'),
    ]);
    return {
      generated_at: signals && signals.generated_at,
      top_signals: ((signals && signals.items) || []).slice(0, 10).map(s => ({
        title: s.title, source: s.source_name || s.source_id, url: s.source_url,
        priority: s.priority, tier: s.tier, posted_at: s.posted_at,
      })),
      top_events: ((events && events.events) || []).slice(0, 6).map(e => ({
        type: e.type, subject: e.subject, label_ar: e.label_ar,
        evidence: e.evidence_count, confidence: e.confidence, last_updated: e.last_updated,
      })),
      latest_insight: insights && insights.current ? insights.current.insight_ar : null,
      top_opportunities: ((opportunities && opportunities.opportunities) || []).slice(0, 5).map(o => ({
        title: o.title_ar || o.title_en, thesis: o.thesis_ar || '',
        confidence: o.confidence, tier: o.tier,
      })),
      run_summary: performance && performance.latest ? {
        items: performance.latest.items_total,
        opportunities: performance.latest.opportunities_total,
      } : null,
    };
  }

  function activeView() {
    /* Snapshot of "what is the user looking at right now" — passed to the
     * assistant so it can ground its answer in the user's current view. */
    const RS = window.RadarState || {};
    return {
      layer: RS.layer || null,
      lang: localStorage.getItem('axp_lang') || 'ar',
      focused: RS.focusedDetail ? {
        kind: RS.focusedDetail.kind,
        title: RS.focusedDetail.title,
        label: RS.focusedDetail.label,
        summary: (RS.focusedDetail.summary || '').slice(0, 600),
        url: RS.focusedDetail.url,
      } : null,
    };
  }

  async function callAssistant(messages) {
    const context = await fetchContext();
    const view = activeView();
    let res;
    try {
      res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          context,
          active_view: view,
          subscriber: isSubscriber(),
          locale: localStorage.getItem('axp_lang') || 'ar',
        }),
      });
    } catch (e) {
      // Pure network failure (no fetch at all) — show local fallback content
      // as a soft-fail with a quiet note rather than a red error label.
      return { ok: true, soft: 'network', text: localResponse(messages, context, view), note: 'وضع محلي · لا اتصال بالإنترنت أو الخادم' };
    }
    // 429 → rate limit (we still have a friendly message to show)
    if (res.status === 429) {
      const data = await res.json().catch(() => ({}));
      return { ok: true, soft: 'rate_limit', text: data.message || 'تجاوزت الحد اليومي.', note: 'الحد اليومي' };
    }

    // 404 / 405 / 501 → backend isn't deployed (or method not allowed by a
    // local static server). Always treat as soft fallback so the drawer
    // still surfaces useful content.
    if ([404, 405, 501].includes(res.status)) {
      return { ok: true, soft: 'not_deployed', text: localResponse(messages, context, view), note: 'وضع محلي · انشر api/chat.js لتفعيل المساعد الذكي' };
    }

    // Any other non-2xx → server-side hiccup. Still better to show local
    // content with a transparent note than a dead-end red error.
    if (!res.ok) {
      return { ok: true, soft: 'upstream', text: localResponse(messages, context, view), note: `الخادم رجع ${res.status} · سنعرض ملخصًا محليًا حتى يستقر` };
    }

    const data = await res.json().catch(() => ({}));
    return { ok: true, text: data.reply || '—' };
  }

  function localResponse(messages, context, view) {
    /* Friendly placeholder used when the serverless function isn't deployed.
       Surfaces the radar's actual data so the drawer is useful even offline. */
    const lines = [];
    lines.push('🛰 المساعد يعمل في الوضع المحلي (الـ API لم يُنشر بعد). إليك ملخصًا من الرادار:');
    if (view && view.focused) {
      const f = view.focused;
      lines.push(`\n• تنظر الآن إلى: ${f.label || f.kind} — "${f.title}"`);
      if (f.summary) lines.push(`  ${f.summary.slice(0, 240)}`);
      if (f.url) lines.push(`  المصدر: ${f.url}`);
    }
    if (context.latest_insight) lines.push(`\n• ملاحظة الرادار اليوم: ${context.latest_insight}`);
    if (context.top_events && context.top_events.length) {
      lines.push('\n• أحدث الأحداث:');
      context.top_events.slice(0, 3).forEach(e => lines.push(`  – ${e.label_ar || e.type} على ${e.subject} (${e.evidence} دليل، ثقة ${(e.confidence*100|0)}%)`));
    }
    if (context.top_opportunities && context.top_opportunities.length && !(view && view.focused)) {
      lines.push('\n• أبرز الفرص:');
      context.top_opportunities.slice(0, 3).forEach(o => lines.push(`  – ${o.title} (ثقة ${(o.confidence*100|0)}%)`));
    }
    lines.push('\nلتفعيل المساعد الذكي الكامل، انشر `api/chat.js` على Vercel وأضف `OPENAI_API_KEY` (راجع SETUP.md).');
    return lines.join('\n');
  }

  /* ---------- Suggestion sets ---------- */

  const DEFAULT_SUGGESTIONS = [
    { prompt: 'لخّص لي ما الجديد المهم في الرادار اليوم بلغة بسيطة، وما المغزى التجاري لكل عنصر.', label: '🪞 بسّط لي ما الجديد' },
    { prompt: 'بناءً على إشارات الرادار وأحداثه، ضع لي خطة عمل 7 أيام أبدأ بها بفكرة قابلة للتنفيذ.', label: '🧭 خطة عمل 7 أيام' },
    { prompt: 'فكّر معي بصوت عالٍ: ما الأنماط أو الفرص التي قد لا أراها بنفسي في هذه البيانات؟', label: '💡 فكّر معي' },
    { prompt: 'اكتب لي مسودة منشور X عربي يلخّص أبرز إشارة اليوم بصوت ريادي مهني.', label: '✍️ اكتب مسودة منشور' },
    { prompt: 'اقترح ثلاث فرص دخل قابلة للتنفيذ من الإشارات الحالية.', label: '🎯 ثلاث فرص للتنفيذ' },
    { prompt: 'ما أحدث الأحداث المرصودة وما أهميتها التجارية؟', label: '📌 أحدث الأحداث' },
  ];

  const FOLLOWUP_SUGGESTIONS = [
    { prompt: 'اشرح أكثر، أعطِني تفاصيل إضافية.', label: 'اشرح أكثر' },
    { prompt: 'ما الخطوة الأولى العملية للبدء؟', label: 'خطوة أولى عملية' },
    { prompt: 'ما المخاطر أو التحديات المحتملة؟', label: 'المخاطر المحتملة' },
    { prompt: 'هل توجد أمثلة مشابهة نجحت سابقًا؟', label: 'أمثلة مشابهة' },
  ];

  function focusedSuggestions(focused) {
    if (!focused) return DEFAULT_SUGGESTIONS;
    const subject = focused.title;
    if (focused.kind === 'opportunity') {
      return [
        { prompt: `كيف أبدأ في تنفيذ هذه الفرصة: ${subject}؟`, label: 'كيف أبدأ؟' },
        { prompt: `ما المخاطر المحتملة في فرصة "${subject}"؟`, label: 'المخاطر' },
        { prompt: `ما حجم السوق المحتمل لـ "${subject}" في السعودية والخليج؟`, label: 'حجم السوق المحلي' },
        { prompt: `اقترح خطة 7 أيام للبدء بـ "${subject}".`, label: 'خطة 7 أيام' },
      ];
    }
    if (focused.kind === 'event') {
      return [
        { prompt: `ما الأهمية التجارية لهذا الحدث: ${subject}؟`, label: 'الأهمية التجارية' },
        { prompt: `كيف يؤثر هذا على شركات الذكاء الاصطناعي الأخرى؟`, label: 'التأثير على المنافسين' },
        { prompt: `هل توجد فرص ناتجة عن "${subject}"؟`, label: 'فرص محتملة' },
        { prompt: `اشرح هذا الحدث بالتفصيل.`, label: 'اشرح بالتفصيل' },
      ];
    }
    if (focused.kind === 'timeline' || focused.kind === 'signal') {
      return [
        { prompt: `لخّص لي هذه الإشارة: ${subject}.`, label: 'لخّص هذه الإشارة' },
        { prompt: `ما العلاقة المحتملة بين هذه الإشارة وفرص الدخل؟`, label: 'العلاقة بفرص الدخل' },
        { prompt: `ابحث عن إشارات مشابهة في الرادار.`, label: 'إشارات مشابهة' },
        { prompt: `ما رأيك التحليلي في هذا الخبر؟`, label: 'الرأي التحليلي' },
      ];
    }
    return DEFAULT_SUGGESTIONS;
  }

  function renderSuggestions(set) {
    if (!sugBox) return;
    sugBox.innerHTML = set.map(s => `<button class="chat-chip" data-prompt="${escape(s.prompt)}">${escape(s.label)}</button>`).join('');
    sugBox.querySelectorAll('.chat-chip').forEach(btn => {
      btn.addEventListener('click', () => send(btn.dataset.prompt || btn.textContent));
    });
    sugBox.style.display = '';
  }

  function renderFollowups() {
    if (!sugBox) return;
    sugBox.innerHTML = FOLLOWUP_SUGGESTIONS.map(s => `<button class="chat-chip chat-chip-follow" data-prompt="${escape(s.prompt)}">${escape(s.label)}</button>`).join('');
    sugBox.querySelectorAll('.chat-chip').forEach(btn => {
      btn.addEventListener('click', () => send(btn.dataset.prompt || btn.textContent));
    });
    sugBox.style.display = '';
  }

  /* ---------- Submit ---------- */

  async function send(text) {
    text = (text || '').trim();
    if (!text || busy) return;
    const remaining = refreshQuotaUI();
    if (remaining <= 0) {
      const limitMsg = isSubscriber()
        ? 'وصلت للحد اليومي. يعود غدًا.'
        : `وصلت للحد المجاني (${FREE_DAILY_LIMIT}/يوم). اشترك للحصول على ${SUB_DAILY_LIMIT} سؤال يوميًا.`;
      appendMsg({ role: 'assistant', content: limitMsg, error: true, ts: Date.now() });
      return;
    }

    appendMsg({ role: 'user', content: text, ts: Date.now() });
    input.value = '';
    autoSizeTextarea();
    busy = true;
    status.textContent = 'يفكّر…';
    status.classList.add('chat-status-thinking');
    showTyping();

    try {
      const messages = readHistory().map(({ role, content }) => ({ role, content }));
      const res = await callAssistant(messages);
      hideTyping();
      appendMsg({
        role: 'assistant',
        content: res.text,
        error: res.ok === false,
        note: res.note || null,
        ts: Date.now(),
      });
      // Only count against quota when we actually got a real LLM reply
      // (not soft fallbacks like not_deployed / rate_limit / network).
      if (res.ok && !res.soft) {
        const q = readQuota();
        q.used += 1;
        writeQuota(q);
        refreshQuotaUI();
      }
      // After every assistant reply, surface follow-up prompts. The user can
      // either click one or type a new question — either way the conversation
      // stays grounded in what was just discussed.
      renderFollowups();
    } finally {
      busy = false;
      status.textContent = 'متصل';
      status.classList.remove('chat-status-thinking');
    }
  }

  /* ---------- UI wiring ---------- */

  function open(opts) {
    opts = opts || {};
    drawer.hidden = false;
    fab.setAttribute('aria-expanded', 'true');
    document.body.classList.add('has-chat-open');
    requestAnimationFrame(() => drawer.classList.add('chat-open'));
    if (window.RadarAnalytics) window.RadarAnalytics.contentViewed && window.RadarAnalytics.contentViewed('chat_open', 'free');

    // Swap the suggestion set based on what (if anything) the user is
    // currently focused on. If askAbout supplied a context, those chips
    // are tightly tailored to the kind of item.
    const focused = opts.focused || (window.RadarState && window.RadarState.focusedDetail) || null;
    renderSuggestions(focusedSuggestions(focused));

    // If askAbout passed a starter prompt, drop it into the input
    // (the user reads it first, then sends). If they want auto-send,
    // we expose `autoSend: true`.
    if (opts.prompt) {
      input.value = opts.prompt;
      autoSizeTextarea();
      if (opts.autoSend) {
        setTimeout(() => send(opts.prompt), 100);
      }
    }
    setTimeout(() => input.focus(), 250);
  }

  function close_() {
    drawer.classList.remove('chat-open');
    fab.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('has-chat-open');
    setTimeout(() => { drawer.hidden = true; }, 220);
  }

  function autoSizeTextarea() {
    input.style.height = 'auto';
    input.style.height = Math.min(160, input.scrollHeight) + 'px';
  }

  fab.addEventListener('click', () => {
    if (drawer.hidden) open(); else close_();
  });

  // Public API for the rest of the radar to summon the assistant
  // pre-loaded with whatever the user is looking at.
  window.RadarChat = {
    open(opts) { open(opts || {}); },
    close() { close_(); },
    askAbout(item, customPrompt) {
      if (!item) return;
      const isAr = (localStorage.getItem('axp_lang') || 'ar') === 'ar';
      const subject = item.title || item.subject || '';
      let prompt = customPrompt;
      if (!prompt) {
        // Pre-fill a context-aware opener — the user can edit before sending.
        if (item.kind === 'opportunity') {
          prompt = isAr
            ? `اشرح لي هذه الفرصة: "${subject}". كيف أبدأ، وما الخطوة الأولى العملية؟`
            : `Explain this opportunity: "${subject}". How would I start, and what's the first practical step?`;
        } else if (item.kind === 'event') {
          prompt = isAr
            ? `ما الأهمية التجارية لهذا الحدث: "${subject}"؟ وما الفرص المحتملة منه؟`
            : `What's the commercial significance of this event: "${subject}"? What opportunities could come from it?`;
        } else if (item.kind === 'timeline' || item.kind === 'signal') {
          prompt = isAr
            ? `لخّص هذه الإشارة: "${subject}"، وما رأيك التحليلي فيها؟`
            : `Summarize this signal: "${subject}", and your analytical take.`;
        } else {
          prompt = isAr ? `ناقش معي: "${subject}"` : `Discuss with me: "${subject}"`;
        }
      }
      open({ focused: item, prompt: prompt, autoSend: false });
    },
  };
  close.addEventListener('click', close_);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !drawer.hidden) close_();
  });
  if (sugBox) {
    sugBox.querySelectorAll('.chat-chip').forEach(btn => {
      btn.addEventListener('click', () => send(btn.dataset.prompt || btn.textContent));
    });
  }
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    send(input.value);
  });
  input.addEventListener('input', autoSizeTextarea);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input.value);
    }
  });

  renderHistory();
  refreshQuotaUI();
})();
