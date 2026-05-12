/* Radar — telemetry bar + heartbeat + source strip + tactical state.
 *
 * Self-contained. Reads:
 *   data/radar/signals.json           → counts, last_run, source breakdown
 *   data/radar/agents/run_log.json    → agent results, openai calls
 *   data/config.json                  → product name, refresh cycle
 *
 * Mounts itself at #telemetry-slot if present, otherwise prepends to body.
 * Updates:
 *   - relative timestamps every 15s
 *   - heartbeat health class every 60s
 *   - signal count is fixed per page-load (next refresh = new fetch)
 */
(function (global) {
  'use strict';

  const REFRESH_INTERVAL_MS = 2 * 60 * 60 * 1000; // 2h cron cadence
  const HEALTHY_AGE_MS = 3 * 60 * 60 * 1000;
  const STALE_AGE_MS = 6 * 60 * 60 * 1000;

  // Source brand groupings — keep this short enough to fit on one line.
  const SOURCE_GROUPS = [
    { id: 'openai',     label: 'OpenAI',  match: ['openai_news'] },
    { id: 'anthropic',  label: 'Anthropic', match: ['anthropic_news'] },
    { id: 'google',     label: 'Google',  match: ['google_deepmind', 'google_ai_blog'] },
    { id: 'hf',         label: 'HF',      match: ['huggingface_blog', 'huggingface_daily_papers', 'huggingface_models'] },
    { id: 'arxiv',      label: 'arXiv',   match_prefix: 'arxiv_' },
    { id: 'hn',         label: 'HN',      match: ['hn_algolia'] },
    { id: 'reddit',     label: 'Reddit',  match_prefix: 'reddit_' },
    { id: 'github',     label: 'GitHub',  match: ['github_repos', 'github_blog_ai'] },
    { id: 'x',          label: 'X',       match: ['x_recent_search'] },
  ];

  function lang() {
    return localStorage.getItem('axp_lang') || (document.documentElement.getAttribute('lang') || 'ar');
  }

  function t(key) {
    const i18n = global.__radarI18n || {};
    const l = lang();
    return (i18n[l] && i18n[l][key]) || (i18n.en && i18n.en[key]) || key;
  }

  async function fetchJSON(path) {
    try {
      const r = await fetch(path, { cache: 'no-cache' });
      if (!r.ok) return null;
      return await r.json();
    } catch (e) { return null; }
  }

  /* ----- Relative time helpers ----- */

  function relTime(iso) {
    if (!iso) return '—';
    const now = Date.now();
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return '—';
    const diff = Math.max(0, now - then);
    const s = Math.floor(diff / 1000);
    const m = Math.floor(s / 60);
    const h = Math.floor(m / 60);
    const d = Math.floor(h / 24);
    const ar = lang() === 'ar';
    if (s < 60)  return ar ? `قبل ${s} ثانية`  : `${s}s ago`;
    if (m < 60)  return ar ? `قبل ${m} دقيقة` : `${m}m ago`;
    if (h < 24)  return ar ? `قبل ${h} ساعة` : `${h}h ago`;
    return ar ? `قبل ${d} يوم` : `${d}d ago`;
  }

  function timeUntil(iso) {
    const now = Date.now();
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return '—';
    let diff = then - now;
    if (diff <= 0) return lang() === 'ar' ? 'قريباً' : 'soon';
    const m = Math.floor(diff / 60000);
    const h = Math.floor(m / 60);
    const ar = lang() === 'ar';
    if (m < 60) return ar ? `بعد ${m} دقيقة` : `in ${m}m`;
    return ar ? `بعد ${h}س ${m % 60}د` : `in ${h}h ${m % 60}m`;
  }

  function healthClass(runAtISO) {
    if (!runAtISO) return 'tel-stale';
    const age = Date.now() - new Date(runAtISO).getTime();
    if (age < HEALTHY_AGE_MS) return 'tel-live';
    if (age < STALE_AGE_MS) return 'tel-aging';
    return 'tel-stale';
  }

  /* ----- Source activity ----- */

  function countSources(items) {
    const counts = {};
    for (const it of items || []) {
      const sid = it.source_id || '';
      counts[sid] = (counts[sid] || 0) + 1;
    }
    return SOURCE_GROUPS.map(group => {
      let n = 0;
      if (group.match) for (const m of group.match) n += counts[m] || 0;
      if (group.match_prefix) {
        for (const k of Object.keys(counts)) {
          if (k.startsWith(group.match_prefix)) n += counts[k];
        }
      }
      return { ...group, count: n };
    });
  }

  /* ----- Render ----- */

  function render(state) {
    const ar = lang() === 'ar';
    const health = healthClass(state.run_at);
    const next = state.run_at ? new Date(new Date(state.run_at).getTime() + REFRESH_INTERVAL_MS).toISOString() : null;

    const sourcesHTML = state.sources.map(g => {
      const active = g.count > 0;
      return `<span class="tel-src ${active ? 'tel-src-on' : 'tel-src-off'}" title="${g.label}: ${g.count} ${ar ? 'إشارة' : 'signals'}">
        <span class="tel-src-dot"></span>${g.label}
      </span>`;
    }).join('');

    const labelLive = ar ? 'مباشر' : 'LIVE';
    const labelAging = ar ? 'تحديث متأخر' : 'AGING';
    const labelStale = ar ? 'بيانات قديمة' : 'STALE';
    const statusLabel = health === 'tel-live' ? labelLive : (health === 'tel-aging' ? labelAging : labelStale);

    return `
      <div class="telemetry ${health}">
        <div class="tel-row">
          <span class="tel-status">
            <span class="tel-dot"></span>
            <span class="tel-status-label">${statusLabel}</span>
          </span>

          <span class="tel-stat">
            <span class="tel-stat-value" data-counttarget="${state.signal_count}">0</span>
            <span class="tel-stat-label">${ar ? 'إشارة' : 'signals'}</span>
          </span>

          <span class="tel-stat">
            <span class="tel-stat-value" data-counttarget="${state.opp_count}">0</span>
            <span class="tel-stat-label">${ar ? 'فرصة' : 'opportunities'}</span>
          </span>

          <span class="tel-stat tel-stat-time">
            <span class="tel-stat-label">${ar ? 'آخر مسح' : 'last sweep'}</span>
            <span class="tel-stat-value tel-time" data-timestamp="${state.run_at || ''}">${relTime(state.run_at)}</span>
          </span>

          <span class="tel-stat tel-stat-time">
            <span class="tel-stat-label">${ar ? 'المسح القادم' : 'next sweep'}</span>
            <span class="tel-stat-value tel-time-future" data-future-timestamp="${next || ''}">${timeUntil(next)}</span>
          </span>

          <span class="tel-sources">${sourcesHTML}</span>
        </div>
      </div>
      <div class="heartbeat ${health}"></div>
    `;
  }

  /* ----- Count-up ----- */

  function animateCount(el, target, duration = 800) {
    const start = performance.now();
    const from = 0;
    const easing = (t) => 1 - Math.pow(1 - t, 3); // ease-out cubic
    function tick(now) {
      const p = Math.min(1, (now - start) / duration);
      const v = Math.round(from + (target - from) * easing(p));
      el.textContent = v.toLocaleString(lang() === 'ar' ? 'ar-SA' : 'en-US');
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* ----- Boot ----- */

  async function mount() {
    const i18nDoc = await fetchJSON('data/i18n.json');
    if (i18nDoc) global.__radarI18n = i18nDoc;

    const [signals, runLog, opps] = await Promise.all([
      fetchJSON('data/radar/signals.json'),
      fetchJSON('data/radar/agents/run_log.json'),
      fetchJSON('data/radar/opportunities.json'),
    ]);

    if (!signals) return; // no data yet — don't render telemetry rather than show stale

    const state = {
      run_at: signals.generated_at || (runLog && runLog.run_at) || null,
      signal_count: signals.count || (signals.items || []).length || 0,
      opp_count: (opps && opps.opportunities && opps.opportunities.length) || 0,
      sources: countSources(signals.items),
    };

    let slot = document.getElementById('telemetry-slot');
    if (!slot) {
      slot = document.createElement('div');
      slot.id = 'telemetry-slot';
      document.body.insertBefore(slot, document.body.firstChild);
    }
    slot.innerHTML = render(state);

    // Trigger count-up
    slot.querySelectorAll('[data-counttarget]').forEach(el => {
      const target = parseInt(el.dataset.counttarget, 10) || 0;
      animateCount(el, target);
    });

    // Periodic refresh of relative timestamps
    setInterval(() => {
      document.querySelectorAll('[data-timestamp]').forEach(el => {
        el.textContent = relTime(el.dataset.timestamp);
      });
      document.querySelectorAll('[data-future-timestamp]').forEach(el => {
        el.textContent = timeUntil(el.dataset.futureTimestamp);
      });
    }, 15000);

    // Periodic health re-evaluation (in case page is left open across sweeps)
    setInterval(() => {
      const tel = document.querySelector('.telemetry');
      const hb = document.querySelector('.heartbeat');
      if (!tel || !hb) return;
      tel.className = `telemetry ${healthClass(state.run_at)}`;
      hb.className = `heartbeat ${healthClass(state.run_at)}`;
    }, 60000);
  }

  // Boot after DOM ready (idempotent)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  // Expose helpers for app.js (timestamp ticker, count-up)
  global.RadarTelemetry = {
    relTime,
    timeUntil,
    animateCount,
    healthClass,
    refreshTimestamps() {
      document.querySelectorAll('[data-timestamp]').forEach(el => { el.textContent = relTime(el.dataset.timestamp); });
      document.querySelectorAll('[data-future-timestamp]').forEach(el => { el.textContent = timeUntil(el.dataset.futureTimestamp); });
    }
  };

  /* ----- Click radial wave (global) ----- */

  document.addEventListener('click', (e) => {
    const target = e.target.closest('button, a.btn, a.locked-cta-button, a.subscribe-banner-cta, .pricing-cta');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    const wave = document.createElement('span');
    wave.className = 'click-wave';
    const size = Math.max(rect.width, rect.height) * 1.2;
    wave.style.width = wave.style.height = size + 'px';
    wave.style.left = (e.clientX - rect.left - size / 2) + 'px';
    wave.style.top = (e.clientY - rect.top - size / 2) + 'px';
    target.style.position = target.style.position || 'relative';
    target.appendChild(wave);
    setTimeout(() => wave.remove(), 500);
  }, { passive: true });
})(typeof window !== 'undefined' ? window : this);
