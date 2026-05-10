/* Radar — System Pulse page renderer.
 *
 * Reads what the agent pipeline writes:
 *   data/radar/agents/run_log.json
 *   data/radar/agents/performance.json
 *   data/radar/agents/learnings.json
 *   data/radar/agents/events.json
 *   data/radar/agents/insights.json
 *   data/radar/agents/qa_report.json
 *
 * Surfaces "the system itself": each agent's last run, latency, output,
 * source reliability, run-over-run trend, OpenAI cost burn.
 */
(function () {
  'use strict';

  const ROOT = document.getElementById('content');
  if (!ROOT) return;

  async function fetchJSON(path) {
    try {
      const r = await fetch(path, { cache: 'no-cache' });
      if (!r.ok) return null;
      return await r.json();
    } catch (e) { return null; }
  }

  function lang() { return localStorage.getItem('axp_lang') || 'ar'; }
  function isAr() { return lang() === 'ar'; }
  function fmt(n)  { return (n || 0).toLocaleString(isAr() ? 'ar-SA' : 'en-US'); }

  function relTime(iso) {
    if (!iso) return '—';
    const t = (window.RadarTelemetry && window.RadarTelemetry.relTime);
    return t ? t(iso) : iso;
  }

  function escape(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function statusDot(status) {
    return status === 'ok' ? '<span class="sp-dot sp-dot-ok"></span>'
         : status === 'warn' ? '<span class="sp-dot sp-dot-warn"></span>'
         : '<span class="sp-dot sp-dot-err"></span>';
  }

  function bar(value, max, klass) {
    const pct = Math.min(1, max ? value / max : 0);
    return `<div class="sp-bar ${klass || ''}"><div class="sp-bar-fill" style="width:${(pct*100).toFixed(1)}%"></div></div>`;
  }

  /* ---------- Sections ---------- */

  function renderHero(insight, runLog, totalAgents) {
    const ar = isAr();
    const insightAr = (insight && insight.insight_ar) || '';
    const insightEn = (insight && insight.insight_en) || '';
    const text = ar ? insightAr : (insightEn || insightAr);
    const fallback = ar ? 'النظام في وضع المراقبة العادية.' : 'System nominal — passive monitoring.';
    return `
      <section class="sp-hero">
        <div class="sp-hero-head">
          <div class="sp-hero-eyebrow">
            <span class="sp-dot sp-dot-ok"></span>
            <span>${ar ? 'ملاحظة الرادار' : 'Radar observation'}</span>
            <span class="sp-hero-meta">${relTime(insight && insight.generated_at)}</span>
          </div>
          <h1 class="sp-hero-text">${escape(text || fallback)}</h1>
        </div>
        <div class="sp-hero-stats">
          <div><span class="sp-stat-value">${fmt(totalAgents)}</span><span class="sp-stat-label">${ar ? 'وكلاء نشطين' : 'active agents'}</span></div>
          <div><span class="sp-stat-value">${fmt((runLog && runLog.openai_calls) || 0)}</span><span class="sp-stat-label">${ar ? 'نداء OpenAI' : 'OpenAI calls'}</span></div>
          <div><span class="sp-stat-value">${runLog && runLog.run_at ? relTime(runLog.run_at) : '—'}</span><span class="sp-stat-label">${ar ? 'آخر تشغيل' : 'last run'}</span></div>
        </div>
      </section>
    `;
  }

  function renderAgents(runLog) {
    const ar = isAr();
    const results = (runLog && runLog.results) || [];
    if (!results.length) return '';
    const rows = results.map(r => {
      const status = r.error ? 'err' : (r.notes && r.notes.some(n => /warn|fail/i.test(n)) ? 'warn' : 'ok');
      const note = (r.notes && r.notes[0]) || (r.error || '—');
      const written = (r.written || []).map(w => `<code class="sp-path">${escape(w)}</code>`).join(' ') || '';
      return `
        <div class="sp-agent-row">
          <div class="sp-agent-name">${statusDot(status)}<span>${escape(r.agent)}</span></div>
          <div class="sp-agent-time">${(r.duration_s || 0).toFixed(2)}s</div>
          <div class="sp-agent-note">${escape(note)}</div>
          <div class="sp-agent-written">${written}</div>
        </div>
      `;
    }).join('');
    return `
      <section class="sp-section">
        <h2 class="sp-h2">${ar ? 'حالة الوكلاء' : 'Agent status'} <span class="sp-h2-meta">${results.length}</span></h2>
        <div class="sp-agent-table">
          <div class="sp-agent-row sp-agent-row-head">
            <div>${ar ? 'الوكيل' : 'agent'}</div>
            <div>${ar ? 'الزمن' : 'duration'}</div>
            <div>${ar ? 'الملاحظة' : 'note'}</div>
            <div>${ar ? 'مخرجات' : 'wrote'}</div>
          </div>
          ${rows}
        </div>
      </section>
    `;
  }

  function renderSourceReliability(learnings) {
    const ar = isAr();
    const top = (learnings && learnings.top_reliable_sources) || [];
    const weak = (learnings && learnings.weakest_sources) || [];
    if (!top.length && !weak.length) return '';
    const row = ([id, score]) => `
      <div class="sp-rel-row">
        <span class="sp-rel-name">${escape(id)}</span>
        ${bar(score, 1, score >= 0.6 ? 'sp-bar-ok' : (score >= 0.3 ? 'sp-bar-warn' : 'sp-bar-err'))}
        <span class="sp-rel-value">${(score*100).toFixed(0)}%</span>
      </div>
    `;
    return `
      <section class="sp-section">
        <h2 class="sp-h2">${ar ? 'موثوقية المصادر' : 'Source reliability'}</h2>
        <div class="sp-rel-grid">
          <div>
            <h3 class="sp-h3">${ar ? 'الأكثر موثوقية' : 'Most reliable'}</h3>
            ${top.map(row).join('')}
          </div>
          <div>
            <h3 class="sp-h3">${ar ? 'الأضعف' : 'Weakest'}</h3>
            ${weak.map(row).join('')}
          </div>
        </div>
      </section>
    `;
  }

  function renderRunsHistogram(perf) {
    const ar = isAr();
    const runs = (perf && perf.runs) || [];
    if (!runs.length) return '';
    const max = Math.max(...runs.map(r => r.items_total || 0));
    const bars = runs.map((r, i) => {
      const h = max ? ((r.items_total || 0) / max) * 100 : 0;
      const total = r.items_total || 0;
      return `<span class="sp-hist-bar" style="height:${h.toFixed(1)}%" title="${escape(r.run_at)} — ${total} ${ar ? 'إشارة' : 'signals'}"></span>`;
    }).join('');
    return `
      <section class="sp-section">
        <h2 class="sp-h2">${ar ? 'تاريخ التشغيلات' : 'Run history'} <span class="sp-h2-meta">${runs.length}</span></h2>
        <div class="sp-hist">${bars}</div>
        <div class="sp-hist-meta">${ar ? 'كل عمود = تشغيل واحد، الارتفاع = عدد الإشارات. الأحدث على اليمين.' : 'Each bar = one run. Height = signal count. Newest on the right.'}</div>
      </section>
    `;
  }

  function renderEvents(events) {
    if (!events || !events.length) return '';
    const ar = isAr();
    const cards = events.slice(0, 6).map(e => `
      <div class="sp-event-card ${e.is_new ? 'sp-event-new' : ''}">
        <div class="sp-event-head">
          <span class="sp-event-icon">${escape(e.icon || '·')}</span>
          <span class="sp-event-label">${escape(ar ? e.label_ar : e.label_en)}</span>
          <span class="sp-event-confidence">${(e.confidence*100).toFixed(0)}%</span>
        </div>
        <div class="sp-event-subject">${escape(e.subject)}</div>
        <div class="sp-event-meta">
          <span>${e.evidence_count} ${ar ? 'دليل' : 'evidence'}</span>
          <span>·</span>
          <span data-timestamp="${escape(e.last_updated || '')}">${relTime(e.last_updated)}</span>
        </div>
      </div>
    `).join('');
    return `
      <section class="sp-section">
        <h2 class="sp-h2">${ar ? 'الأحداث المرصودة' : 'Detected events'} <span class="sp-h2-meta">${events.length}</span></h2>
        <div class="sp-event-grid">${cards}</div>
      </section>
    `;
  }

  function renderQA(qa) {
    if (!qa) return '';
    const ar = isAr();
    const ok = qa.ok;
    const items = (qa.issues || []).slice(0, 8);
    return `
      <section class="sp-section">
        <h2 class="sp-h2">${ar ? 'فحص الواجهات' : 'UI/Content QA'}
          <span class="sp-h2-meta ${ok ? 'sp-ok' : 'sp-err'}">${ok ? (ar ? 'سليم' : 'pass') : `${qa.issue_count || 0} ${ar ? 'ملاحظة' : 'issues'}`}</span>
        </h2>
        ${items.length ? `<ul class="sp-qa-list">${items.map(i => `<li>${escape(i)}</li>`).join('')}</ul>` : `<div class="sp-empty">${ar ? 'الواجهات والمحتوى يجتازان كل الفحوص.' : 'All UI and content checks pass.'}</div>`}
      </section>
    `;
  }

  /* ---------- Boot ---------- */

  async function boot() {
    ROOT.innerHTML = `<div class="tactical-loading"><span>● ${isAr() ? 'يجمع حالة النظام' : 'gathering system state'}…</span><div class="scan-bar"></div></div>`;
    const [runLog, perf, learnings, events, insights, qa] = await Promise.all([
      fetchJSON('data/radar/agents/run_log.json'),
      fetchJSON('data/radar/agents/performance.json'),
      fetchJSON('data/radar/agents/learnings.json'),
      fetchJSON('data/radar/agents/events.json'),
      fetchJSON('data/radar/agents/insights.json'),
      fetchJSON('data/radar/agents/qa_report.json'),
    ]);

    const insight = insights && insights.current;
    const totalAgents = (runLog && runLog.results && runLog.results.length) || 0;
    const eventsList = (events && events.events) || [];

    ROOT.innerHTML = [
      renderHero(insight, runLog, totalAgents),
      renderAgents(runLog),
      renderEvents(eventsList),
      renderSourceReliability(learnings),
      renderRunsHistogram(perf),
      renderQA(qa),
    ].join('');

    // Refresh relative timestamps on this page too
    if (window.RadarTelemetry && window.RadarTelemetry.refreshTimestamps) {
      setTimeout(window.RadarTelemetry.refreshTimestamps, 100);
    }
    if (window.RadarAnalytics) window.RadarAnalytics.contentViewed('system_pulse', 'free');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
