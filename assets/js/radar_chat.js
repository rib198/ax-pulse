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
          <div class="chat-welcome-title">مرحبًا 👋</div>
          <div class="chat-welcome-text">أنا مساعد الرادار. أعرف الإشارات والفرص والأحداث المرصودة الآن. اسألني أو ابدأ من اقتراح أدناه.</div>
        </div>
      `;
      return;
    }
    body.innerHTML = hist.map(m => msgBubble(m)).join('');
    body.scrollTop = body.scrollHeight;
  }

  function msgBubble(m) {
    const isAssistant = m.role === 'assistant';
    return `
      <div class="chat-msg chat-msg-${isAssistant ? 'assistant' : 'user'}">
        ${isAssistant ? '<span class="chat-avatar"></span>' : ''}
        <div class="chat-bubble">
          ${linkify(m.content || '')}
          ${m.error ? '<div class="chat-bubble-err">تعذّر الاستجابة. حاول مرة أخرى.</div>' : ''}
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

  async function callAssistant(messages) {
    const context = await fetchContext();
    let res;
    try {
      res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          context,
          subscriber: isSubscriber(),
          locale: localStorage.getItem('axp_lang') || 'ar',
        }),
      });
    } catch (e) {
      return { ok: false, error: 'network', text: localResponse(messages, context) };
    }
    if (res.status === 404) {
      return { ok: false, error: 'not_deployed', text: localResponse(messages, context) };
    }
    if (res.status === 429) {
      const data = await res.json().catch(() => ({}));
      return { ok: false, error: 'rate_limit', text: data.message || 'تجاوزت الحد اليومي.' };
    }
    if (!res.ok) {
      return { ok: false, error: 'http_' + res.status, text: 'تعذّر الاتصال بالمساعد.' };
    }
    const data = await res.json().catch(() => ({}));
    return { ok: true, text: data.reply || '—' };
  }

  function localResponse(messages, context) {
    /* Friendly placeholder used when the serverless function isn't deployed.
       Surfaces the radar's actual data so the drawer is useful even offline. */
    const last = messages[messages.length - 1] || { content: '' };
    const q = (last.content || '').toLowerCase();
    const lines = [];
    lines.push('🛰 المساعد يعمل حاليًا في الوضع المحلي (الـ API لم يُنشر بعد). هذه نظرة سريعة من بيانات الرادار:');
    if (context.latest_insight) lines.push(`\n• ملاحظة الرادار: ${context.latest_insight}`);
    if (context.top_events && context.top_events.length) {
      lines.push('\n• أحدث الأحداث المرصودة:');
      context.top_events.slice(0, 3).forEach(e => lines.push(`  – ${e.label_ar || e.type} على ${e.subject} (${e.evidence} دليل، ثقة ${(e.confidence*100|0)}%)`));
    }
    if (context.top_opportunities && context.top_opportunities.length) {
      lines.push('\n• أبرز الفرص:');
      context.top_opportunities.slice(0, 3).forEach(o => lines.push(`  – ${o.title} (ثقة ${(o.confidence*100|0)}%)`));
    }
    lines.push('\nلتفعيل المساعد الذكي الكامل، انشر `api/chat.js` على Vercel وأضف `OPENAI_API_KEY` كـ env var (راجع SETUP.md).');
    return lines.join('\n');
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
      appendMsg({ role: 'assistant', content: res.text, error: !res.ok, ts: Date.now() });
      if (res.ok) {
        const q = readQuota();
        q.used += 1;
        writeQuota(q);
        refreshQuotaUI();
      }
    } finally {
      busy = false;
      status.textContent = 'متصل';
      status.classList.remove('chat-status-thinking');
    }
  }

  /* ---------- UI wiring ---------- */

  function open() {
    drawer.hidden = false;
    fab.setAttribute('aria-expanded', 'true');
    document.body.classList.add('has-chat-open');
    requestAnimationFrame(() => drawer.classList.add('chat-open'));
    if (window.RadarAnalytics) window.RadarAnalytics.contentViewed && window.RadarAnalytics.contentViewed('chat_open', 'free');
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
