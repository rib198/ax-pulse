/* AX Pulse — bilingual data-driven dashboard engine */

const State = {
  lang: localStorage.getItem('axp_lang') || 'en',
  i18n: null,
  brief: null,
  opportunities: null,
  clusters: null,
  categories: null,
  radarSignals: [],
  radarGeneratedAt: null,
  filterCategory: 'all'
};

async function loadJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Failed to load ' + path);
  return res.json();
}

async function bootstrap() {
  const [i18n, opps, clusters, cats, radarOpps, radarSignals, config] = await Promise.all([
    loadJSON('data/i18n.json'),
    loadJSON('data/opportunities.json'),
    loadJSON('data/clusters.json'),
    loadJSON('data/categories.json'),
    loadOptionalJSON('data/radar/opportunities.json'),
    loadOptionalJSON('data/radar/signals.json'),
    loadOptionalJSON('data/config.json')
  ]);
  State.i18n = i18n;
  State.config = config || { subscription: { price_usd: 15, price_label_ar: '15 دولار', price_label_en: '$15' } };
  // Preserve raw radar opportunities so we can read tier/is_new/is_featured set by the agent pipeline.
  State.opportunities = radarOpps && radarOpps.opportunities && radarOpps.opportunities.length
    ? radarOpps.opportunities.map((o, i) => Object.assign(normalizeRadarOpportunity(o, i), {
        tier: o.tier || 'free',
        status: o.status || 'published',
        is_new: !!o.is_new,
        is_featured: !!o.is_featured
      }))
    : opps.opportunities;
  State.clusters = clusters.clusters;
  State.categories = cats.categories;
  State.radarSignals = radarSignals && radarSignals.items ? radarSignals.items : [];
  State.radarGeneratedAt = radarSignals ? radarSignals.generated_at : null;

  try {
    State.brief = await loadJSON(`data/brief.${State.lang}.json`);
  } catch (e) {
    State.brief = await loadJSON('data/brief.en.json');
  }

  applyLang();
  render();
  wireLangToggle();
  wireWaitlist();
}

async function loadOptionalJSON(path) {
  try {
    return await loadJSON(path);
  } catch (e) {
    return null;
  }
}

function t(key) {
  return (State.i18n[State.lang] && State.i18n[State.lang][key]) || key;
}

function applyLang() {
  const html = document.documentElement;
  html.setAttribute('lang', State.lang);
  html.setAttribute('dir', State.lang === 'ar' ? 'rtl' : 'ltr');
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-attr]').forEach(el => {
    const [attr, key] = el.dataset.i18nAttr.split(':');
    el.setAttribute(attr, t(key));
  });
}

function wireLangToggle() {
  const buttons = document.querySelectorAll('.lang-toggle button');
  buttons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === State.lang);
    btn.addEventListener('click', async () => {
      if (State.lang === btn.dataset.lang) return;
      State.lang = btn.dataset.lang;
      localStorage.setItem('axp_lang', State.lang);
      try {
        State.brief = await loadJSON(`data/brief.${State.lang}.json`);
      } catch (e) {}
      buttons.forEach(b => b.classList.toggle('active', b.dataset.lang === State.lang));
      applyLang();
      render();
    });
  });
}

function wireWaitlist() {
  const forms = document.querySelectorAll('.waitlist-form');
  forms.forEach(form => {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input');
      const btn = form.querySelector('button');
      if (!input.value || !input.value.includes('@')) return;
      const list = JSON.parse(localStorage.getItem('axp_waitlist') || '[]');
      list.push({ email: input.value, ts: Date.now() });
      localStorage.setItem('axp_waitlist', JSON.stringify(list));
      btn.textContent = State.lang === 'ar' ? 'تم ✓' : 'Joined ✓';
      btn.style.background = 'var(--ok)';
      input.value = '';
      setTimeout(() => {
        btn.textContent = t('waitlist_btn');
        btn.style.background = '';
      }, 2400);
    });
  });
}

function render() {
  const page = document.body.dataset.page;
  if (page === 'today') renderToday();
  if (page === 'trending') renderTrending();
  if (page === 'opportunities') renderOpportunities();
  if (page === 'categories') renderCategories();
  if (page === 'landing') renderLanding();
  if (page === 'mediator') renderMediator();
  // Always update sidebar active link
  document.querySelectorAll('.nav-item').forEach(el => {
    if (el.dataset.page === page) el.classList.add('active');
  });
}

/* ---------- Today's Brief ---------- */

function renderToday() {
  const root = document.getElementById('content');
  if (!root) return;

  if (State.radarSignals.length) {
    renderRadarToday(root);
    return;
  }

  const b = State.brief;
  const topOpps = State.opportunities.slice(0, 4);
  const topClusters = [...State.clusters].sort((a, b) => b.growth - a.growth).slice(0, 6);
  const dateLabel = formatDate(b.date);

  root.innerHTML = `
    <div class="brief-hero">
      <div class="brief-meta">
        <span class="live-dot"></span>
        <span>${dateLabel}</span>
        <span>·</span>
        <span>${t('live')}</span>
      </div>
      <h1 class="brief-headline">${escape(b.headline)}</h1>
      <p class="brief-summary">${escape(b.summary)}</p>
    </div>

    <div class="stats-grid">
      ${statTile(t('stat_tweets'), b.stats.tweets_analyzed.toLocaleString(), null)}
      ${statTile(t('stat_clusters'), b.stats.clusters_formed, null)}
      ${statTile(t('stat_top_cat'), categoryName(b.stats.top_category), null)}
      ${statTile(t('stat_langs'), b.stats.languages_breakdown, null)}
    </div>

    <div class="section-head">
      <h2 class="section-title">${t('section_top_opps')}</h2>
      <span class="section-subtitle">${t('section_top_opps_sub')}</span>
    </div>
    <div class="opp-list">
      ${topOpps.map((o, i) => oppRow(o, i + 1)).join('')}
    </div>

    <div class="section-head">
      <h2 class="section-title">${t('section_trending')}</h2>
      <span class="section-subtitle">${t('section_trending_sub')}</span>
    </div>
    <div class="cluster-grid">
      ${topClusters.map(clusterCard).join('')}
    </div>

    <div class="watch-card">
      <div class="brief-meta"><span>${t('watch_tomorrow')}</span></div>
      <p class="watch-text">${escape(b.watch_tomorrow)}</p>
    </div>
  `;
}

function renderRadarToday(root) {
  const topOpps = State.opportunities.slice(0, 4);
  const topSignals = State.radarSignals.slice(0, 8);
  const sourceCount = new Set(State.radarSignals.map(s => s.source_name)).size;
  const topOppTitle = topOpps[0] ? (State.lang === 'ar' ? topOpps[0].title_ar : topOpps[0].title_en) : '—';
  const generated = State.radarGeneratedAt ? formatDateTime(State.radarGeneratedAt) : formatDate(new Date().toISOString());

  root.innerHTML = `
    <div class="brief-hero">
      <div class="brief-meta">
        <span class="live-dot"></span>
        <span>${escape(generated)}</span>
        <span>·</span>
        <span>${escape(t('radar_verified'))}</span>
      </div>
      <h1 class="brief-headline">${escape(t('radar_headline'))}</h1>
      <p class="brief-summary">${escape(t('radar_summary'))}</p>
    </div>

    <div class="stats-grid">
      ${statTile(t('stat_signals'), State.radarSignals.length.toLocaleString(), null)}
      ${statTile(t('stat_sources'), sourceCount.toLocaleString(), null)}
      ${statTile(t('stat_top_opportunity'), topOppTitle, null)}
      ${statTile(t('stat_refresh'), generated, null)}
    </div>

    <div class="section-head">
      <h2 class="section-title">${t('section_top_opps')}</h2>
      <span class="section-subtitle">${t('radar_opps_sub')}</span>
    </div>
    <div class="opp-list">
      ${topOpps.map((o, i) => oppRow(o, i + 1)).join('')}
    </div>

    <div class="section-head">
      <h2 class="section-title">${t('section_live_signals')}</h2>
      <span class="section-subtitle">${t('section_live_signals_sub')}</span>
    </div>
    <div class="signal-grid">
      ${topSignals.map(signalCard).join('')}
    </div>

    <div class="watch-card">
      <div class="brief-meta"><span>${t('watch_tomorrow')}</span></div>
      <p class="watch-text">${escape(t('radar_watch'))}</p>
    </div>
  `;
}

/* ---------- Trending ---------- */

function renderTrending() {
  const root = document.getElementById('content');
  if (!root) return;

  if (State.radarSignals.length) {
    const sortedSignals = [...State.radarSignals].sort((a, b) => (b.opportunity_score || 0) - (a.opportunity_score || 0));
    root.innerHTML = `
      <div class="section-head">
        <div>
          <h2 class="section-title">${t('section_live_signals')}</h2>
          <span class="section-subtitle">${sortedSignals.length} ${t('signals')} · ${t('section_live_signals_sub')}</span>
        </div>
      </div>
      ${subscribeBanner()}
      <div class="signal-grid">
        ${sortedSignals.map(signalCard).join('')}
      </div>
    `;
    return;
  }
  if (!State.clusters || State.clusters.length === 0) {
    root.innerHTML = `
      <div class="section-head"><div><h2 class="section-title">${t('section_live_signals')}</h2></div></div>
      ${emptyState('tactical_no_signals_title', 'tactical_no_signals_desc')}
    `;
    return;
  }

  const cats = ['all', ...State.categories.map(c => c.id)];
  const filtered = State.filterCategory === 'all'
    ? State.clusters
    : State.clusters.filter(c => c.category === State.filterCategory);
  const sorted = [...filtered].sort((a, b) => b.growth - a.growth);

  root.innerHTML = `
    <div class="section-head">
      <div>
        <h2 class="section-title">${t('section_trending')}</h2>
        <span class="section-subtitle">${sorted.length} ${t('tweets')} · ${t('section_trending_sub')}</span>
      </div>
    </div>
    <div class="filter-row">
      ${cats.map(id => {
        const isAll = id === 'all';
        const label = isAll ? t('filter_all') : categoryName(id);
        const active = State.filterCategory === id ? 'active' : '';
        return `<button class="filter-pill ${active}" data-cat="${id}">${escape(label)}</button>`;
      }).join('')}
    </div>
    <div class="cluster-grid">
      ${sorted.map(clusterCard).join('')}
    </div>
  `;

  root.querySelectorAll('.filter-pill').forEach(p => {
    p.addEventListener('click', () => {
      State.filterCategory = p.dataset.cat;
      renderTrending();
    });
  });
}

/* ---------- Opportunities ---------- */

function renderOpportunities() {
  const root = document.getElementById('content');
  if (!root) return;
  if (window.RadarAnalytics) window.RadarAnalytics.pricingViewed();
  const opps = State.opportunities || [];
  root.innerHTML = `
    <div class="section-head">
      <div>
        <h2 class="section-title">${t('section_top_opps')}</h2>
        <span class="section-subtitle">${t('section_top_opps_sub')}</span>
      </div>
    </div>
    ${subscribeBanner()}
    ${opps.length === 0 ? emptyState('tactical_no_opps_title', 'tactical_no_opps_desc') : `
      <div class="opp-list">
        ${opps.map(o => oppRow(o, o.rank, true)).join('')}
      </div>
    `}
  `;
}

/* ---------- Categories ---------- */

function renderCategories() {
  const root = document.getElementById('content');
  if (!root) return;
  root.innerHTML = `
    <div class="section-head">
      <div>
        <h2 class="section-title">${t('section_categories')}</h2>
        <span class="section-subtitle">${t('section_categories_sub')}</span>
      </div>
    </div>
    <div class="cluster-grid">
      ${State.categories.map((c, i) => categoryCard(c, i + 1)).join('')}
    </div>
  `;
}

/* ---------- Landing ---------- */

function renderLanding() {
  // Swap headline based on lang (already in HTML data attrs, applyLang handles it)
}

/* ---------- AI Bridge (Mediator) ---------- */

const Bridge = {
  STORE_KEY: 'axp_bridge_history',
  load() {
    try { return JSON.parse(localStorage.getItem(this.STORE_KEY) || '[]'); }
    catch (e) { return []; }
  },
  save(list) { localStorage.setItem(this.STORE_KEY, JSON.stringify(list)); },
  clear() { localStorage.removeItem(this.STORE_KEY); },
  templates: {
    review: {
      claude: (text) => `Please review the following code/text generated by Claude. Be concise and specific. Look for:\n  • bugs and edge cases\n  • better idioms or simpler patterns\n  • missing error handling at boundaries\n\nAfter your review, give a clear verdict: ship / revise / rewrite.\n\n--- Begin Claude output ---\n${text}\n--- End Claude output ---`,
      codex: (text) => `Codex reviewed the previous Claude output. Read its feedback below and respond with: (a) which points you accept, (b) which you reject and why, (c) the next revised version.\n\n--- Begin Codex review ---\n${text}\n--- End Codex review ---`
    },
    implement: {
      claude: (text) => `Claude produced the spec below. Implement it as production-ready code. Match the existing style conventions and include short tests where useful.\n\n--- Begin spec ---\n${text}\n--- End spec ---`,
      codex: (text) => `Codex produced the implementation below. Verify it matches the original intent, run mental tests on edge cases, and either approve it or list precise revisions needed.\n\n--- Begin implementation ---\n${text}\n--- End implementation ---`
    },
    critique: {
      claude: (text) => `Continue this multi-AI critique loop. Below is the latest message from Claude. Respond with one paragraph that pushes the design forward — challenge an assumption, or propose a sharper alternative.\n\n--- Latest from Claude ---\n${text}`,
      codex: (text) => `Continue this multi-AI critique loop. Below is the latest message from Codex. Respond with one paragraph: either accept its point and integrate it, or counter with a stronger argument.\n\n--- Latest from Codex ---\n${text}`
    },
    code_only: {
      claude: (text) => extractCodeBlocks(text) || text,
      codex: (text) => extractCodeBlocks(text) || text
    },
    raw: {
      claude: (text) => text,
      codex: (text) => text
    }
  }
};

function extractCodeBlocks(text) {
  const matches = [...text.matchAll(/```[\w]*\n([\s\S]*?)```/g)];
  if (matches.length === 0) return null;
  return matches.map(m => m[1].trim()).join('\n\n---\n\n');
}

function renderMediator() {
  const root = document.getElementById('content');
  if (!root) return;
  const history = Bridge.load();
  const last = history[history.length - 1];
  const lastSource = last ? last.source : null;
  const status = !last ? 'idle' : (last.source === 'claude' ? 'awaiting_codex' : 'awaiting_claude');
  const totalChars = history.reduce((sum, h) => sum + (h.text || '').length, 0);

  root.innerHTML = `
    <div class="brief-hero">
      <div class="brief-meta">
        <span class="live-dot"></span>
        <span data-i18n="nav_mediator">AI Bridge</span>
      </div>
      <h1 class="brief-headline">${escape(t('mediator_title'))}</h1>
      <p class="brief-summary">${escape(t('mediator_sub'))}</p>
    </div>

    <div class="stats-grid">
      ${statTile(t('stat_rounds'), String(history.length), null)}
      ${statTile(t('stat_status'), t('status_' + status), null)}
      ${statTile(t('stat_last_source'), lastSource ? t('source_' + lastSource) : '—', null)}
      ${statTile(t('stat_total_chars'), totalChars.toLocaleString(), null)}
    </div>

    <div class="bridge-composer">
      <div class="section-head">
        <div>
          <h2 class="section-title">${escape(t('compose_title'))}</h2>
          <span class="section-subtitle">${escape(t('compose_sub'))}</span>
        </div>
      </div>

      <div class="bridge-row">
        <label class="bridge-label">${escape(t('source_label'))}</label>
        <div class="bridge-source-toggle">
          <button class="filter-pill active" data-source="claude">${escape(t('source_claude'))}</button>
          <button class="filter-pill" data-source="codex">${escape(t('source_codex'))}</button>
        </div>
      </div>

      <textarea id="bridge-input" class="bridge-textarea" rows="8" placeholder="${escape(t('paste_placeholder'))}"></textarea>

      <div class="bridge-row bridge-row-controls">
        <div class="bridge-template">
          <label class="bridge-label">${escape(t('template_label'))}</label>
          <select id="bridge-template" class="bridge-select">
            <option value="review">${escape(t('template_review'))}</option>
            <option value="implement">${escape(t('template_implement'))}</option>
            <option value="critique">${escape(t('template_critique'))}</option>
            <option value="code_only">${escape(t('template_code_only'))}</option>
            <option value="raw">${escape(t('template_raw'))}</option>
          </select>
        </div>
        <div class="bridge-actions">
          <button class="btn btn-ghost" id="bridge-clear">${escape(t('btn_clear'))}</button>
          <button class="btn btn-ghost" id="bridge-save">${escape(t('btn_save_log'))}</button>
          <button class="btn btn-primary" id="bridge-format">${escape(t('btn_format_copy'))}</button>
        </div>
      </div>

      <div id="bridge-toast" class="bridge-toast"></div>
    </div>

    <div class="section-head" style="margin-top: 32px;">
      <div>
        <h2 class="section-title">${escape(t('timeline_title'))}</h2>
        <span class="section-subtitle">${escape(t('timeline_sub'))}</span>
      </div>
      ${history.length ? `<button class="btn btn-subtle" id="bridge-clear-history">${escape(t('btn_clear_history'))} ×</button>` : ''}
    </div>

    <div class="bridge-timeline">
      ${history.length === 0
        ? `<div class="bridge-empty">${escape(t('timeline_empty'))}</div>`
        : history.slice().reverse().map((h, i) => bridgeItem(h, history.length - i)).join('')}
    </div>
  `;

  wireBridge();
}

function bridgeItem(h, round) {
  const time = new Date(h.ts).toLocaleTimeString(State.lang === 'ar' ? 'ar-SA' : 'en-US', { hour: '2-digit', minute: '2-digit' });
  const preview = (h.text || '').slice(0, 240);
  const isLong = (h.text || '').length > 240;
  const otherSource = h.source === 'claude' ? 'codex' : 'claude';
  return `
    <div class="bridge-item" data-id="${h.id}">
      <div class="bridge-item-head">
        <div class="bridge-item-meta">
          <span class="bridge-source-badge bridge-source-${h.source}">${escape(t('source_' + h.source))}</span>
          <span class="cluster-meta">${escape(t('round_label'))} #${round} · ${time} · ${(h.text || '').length.toLocaleString()} ${escape(t('chars_label'))}</span>
        </div>
        <div class="bridge-item-actions">
          <button class="btn btn-subtle bridge-copy" data-id="${h.id}">${escape(t('btn_copy'))}</button>
          <button class="btn btn-subtle bridge-forward" data-id="${h.id}" data-target="${otherSource}">${escape(t('btn_forward_' + otherSource))}</button>
        </div>
      </div>
      <pre class="bridge-item-text" data-collapsed="${isLong}">${escape(preview)}${isLong ? '…' : ''}</pre>
      ${isLong ? `<button class="btn btn-subtle bridge-toggle" data-id="${h.id}">${escape(t('show_full'))}</button>` : ''}
    </div>
  `;
}

function wireBridge() {
  const root = document.getElementById('content');
  let activeSource = 'claude';

  root.querySelectorAll('.bridge-source-toggle button').forEach(b => {
    b.addEventListener('click', () => {
      root.querySelectorAll('.bridge-source-toggle button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      activeSource = b.dataset.source;
    });
  });

  document.getElementById('bridge-clear').addEventListener('click', () => {
    document.getElementById('bridge-input').value = '';
  });

  document.getElementById('bridge-save').addEventListener('click', () => {
    const text = document.getElementById('bridge-input').value.trim();
    if (!text) return;
    const list = Bridge.load();
    list.push({ id: 'r_' + Date.now(), source: activeSource, text, ts: Date.now() });
    Bridge.save(list);
    bridgeToast(t('saved_msg'));
    setTimeout(() => renderMediator(), 800);
  });

  document.getElementById('bridge-format').addEventListener('click', async () => {
    const text = document.getElementById('bridge-input').value.trim();
    if (!text) return;
    const tplKey = document.getElementById('bridge-template').value;
    const tpl = Bridge.templates[tplKey];
    const formatted = tpl[activeSource](text);
    try {
      await navigator.clipboard.writeText(formatted);
      bridgeToast(t('copied_msg'));
      // also save to log
      const list = Bridge.load();
      list.push({ id: 'r_' + Date.now(), source: activeSource, text, ts: Date.now() });
      Bridge.save(list);
      setTimeout(() => renderMediator(), 1200);
    } catch (e) {
      bridgeToast('Clipboard blocked — please copy manually');
    }
  });

  const clearBtn = document.getElementById('bridge-clear-history');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm(t('confirm_clear'))) {
        Bridge.clear();
        renderMediator();
      }
    });
  }

  root.querySelectorAll('.bridge-copy').forEach(b => {
    b.addEventListener('click', async () => {
      const item = Bridge.load().find(x => x.id === b.dataset.id);
      if (!item) return;
      try {
        await navigator.clipboard.writeText(item.text);
        bridgeToast(t('copied_msg'));
      } catch (e) {}
    });
  });

  root.querySelectorAll('.bridge-forward').forEach(b => {
    b.addEventListener('click', async () => {
      const item = Bridge.load().find(x => x.id === b.dataset.id);
      if (!item) return;
      const tplKey = document.getElementById('bridge-template').value;
      const tpl = Bridge.templates[tplKey];
      // Forward means: take this item's text and format it as if it just arrived from item.source
      const formatted = tpl[item.source](item.text);
      try {
        await navigator.clipboard.writeText(formatted);
        bridgeToast(t('copied_msg'));
      } catch (e) {}
    });
  });

  root.querySelectorAll('.bridge-toggle').forEach(b => {
    b.addEventListener('click', () => {
      const id = b.dataset.id;
      const item = Bridge.load().find(x => x.id === id);
      const pre = root.querySelector(`.bridge-item[data-id="${id}"] .bridge-item-text`);
      if (!item || !pre) return;
      const collapsed = pre.dataset.collapsed === 'true';
      if (collapsed) {
        pre.textContent = item.text;
        pre.dataset.collapsed = 'false';
        b.textContent = t('hide_full');
      } else {
        pre.textContent = item.text.slice(0, 240) + '…';
        pre.dataset.collapsed = 'true';
        b.textContent = t('show_full');
      }
    });
  });
}

function bridgeToast(msg) {
  const el = document.getElementById('bridge-toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('visible'), 1800);
}

/* ---------- Component renderers ---------- */

function statTile(label, value, delta) {
  const deltaHtml = delta != null
    ? `<span class="stat-delta ${delta >= 0 ? 'up' : 'down'}">${delta >= 0 ? '+' : ''}${delta}%</span>`
    : '';
  return `
    <div class="stat-tile">
      <div class="stat-label">${escape(label)}</div>
      <div class="stat-value">${escape(value)} ${deltaHtml}</div>
    </div>
  `;
}

function oppRow(o, rank, expanded = false) {
  const title = State.lang === 'ar' ? o.title_ar : o.title_en;
  const desc = State.lang === 'ar' ? o.desc_ar : o.desc_en;
  const audience = State.lang === 'ar' ? o.audience_ar : o.audience_en;
  const money = State.lang === 'ar' ? o.money_ar : o.money_en;
  const catName = categoryName(o.category);
  const isTop = rank <= 3;
  const evidence = Array.isArray(o.evidence_items) ? o.evidence_items.slice(0, 3) : [];
  const tier = o.tier || 'free';
  const allowed = canAccess(o);
  const badges = badgesFor(o);

  if (!allowed) {
    if (window.RadarAnalytics) window.RadarAnalytics.premiumAttempted(o.id || ('opp_' + rank));
    const previewSnippet = (desc || '').slice(0, (State.config && State.config.subscription && State.config.subscription.free_preview_chars) || 200);
    return `
      <div class="opp-row opp-row-locked">
        <div class="opp-rank ${isTop ? 'top' : ''}">${rank}</div>
        <div class="opp-body">
          <div class="opp-row-head">
            <span class="cat" data-cat="${o.category}">${escape(catName)}</span>
            ${badges}
          </div>
          ${lockedCard(title, previewSnippet, { origin: 'opportunity_row', short: false })}
        </div>
      </div>
    `;
  }

  if (window.RadarAnalytics) window.RadarAnalytics.contentViewed(o.id || ('opp_' + rank), tier);
  const highSignalClass = isHighSignal(o) ? ' opp-row-high-signal' : '';
  return `
    <div class="opp-row${highSignalClass}">
      <div class="opp-rank ${isTop ? 'top' : ''}">${rank}</div>
      <div class="opp-body">
        <div class="opp-row-head">
          <span class="cat" data-cat="${o.category}">${escape(catName)}</span>
          ${badges}
          <span class="cluster-meta">${o.evidence} ${t('evidence')}</span>
        </div>
        <div class="opp-title">${escape(title)}</div>
        <div class="opp-desc">${escape(desc)}</div>
        ${money ? moneyPath(money) : ''}
        ${expanded ? `<div class="cluster-meta" style="margin-top:6px;">${t('audience')}: ${escape(audience)}</div>` : ''}
        ${expanded && evidence.length ? `<div class="evidence-list">${evidence.map(evidenceLink).join('')}</div>` : ''}
      </div>
      <div class="opp-scores">
        ${scoreChip(t('score_novelty'), o.scores.novelty)}
        ${scoreChip(t('score_momentum'), o.scores.momentum)}
        ${scoreChip(t('score_monetize'), o.scores.monetizability)}
        ${scoreChip(t('score_ease'), o.scores.ease)}
        <div class="score-total">
          <span class="score-total-label">${t('score_total')}</span>
          <span class="score-total-value">${o.scores.total}</span>
        </div>
      </div>
    </div>
  `;
}

function evidenceLink(item) {
  return `
    <a class="evidence-link" href="${escape(item.url)}" target="_blank" rel="noreferrer">
      <span>${escape(sourceLabel(item.source_id))}</span>
      <strong>${escape(item.title)}</strong>
    </a>
  `;
}

function moneyPath(money) {
  return `
    <div class="money-path">
      <div class="money-path-label">${State.lang === 'ar' ? 'مسار المال' : 'Money path'}</div>
      <div class="money-path-grid">
        <span><b>${State.lang === 'ar' ? 'نبيع' : 'Sell'}</b>${escape(money.offer)}</span>
        <span><b>${State.lang === 'ar' ? 'يدفع' : 'Buyer'}</b>${escape(money.buyer)}</span>
        <span><b>${State.lang === 'ar' ? 'البداية' : 'Start'}</b>${escape(money.first_step)}</span>
        <span><b>${State.lang === 'ar' ? 'الربح' : 'Revenue'}</b>${escape(money.pricing)}</span>
      </div>
    </div>
  `;
}

function detectLang(text) {
  if (!text) return 'en';
  if (/[؀-ۿ]/.test(text)) return 'ar';
  if (/[぀-ゟ゠-ヿ]/.test(text)) return 'ja';
  if (/[가-힯]/.test(text)) return 'ko';
  if (/[一-鿿]/.test(text)) return 'zh';
  return 'en';
}

function langBadge(code) {
  const labels = { en: 'EN', ar: 'ع', ja: '日', ko: '한', zh: '中' };
  return labels[code] || code.toUpperCase();
}

function translateUrl(text, targetLang) {
  const t = (text || '').slice(0, 1500);
  return `https://translate.google.com/?sl=auto&tl=${targetLang}&op=translate&text=${encodeURIComponent(t)}`;
}

function signalCard(item) {
  const tier = item.tier || 'free';
  const allowed = canAccess(item);
  if (!allowed) {
    if (window.RadarAnalytics) window.RadarAnalytics.premiumAttempted(item.id || item.source_id || 'signal');
    const previewChars = (State.config && State.config.subscription && State.config.subscription.free_preview_chars) || 180;
    const titleAr = item.title_ar || '';
    const useAr = State.lang === 'ar' && titleAr;
    const lockedTitle = useAr ? titleAr : (item.title || '');
    const lockedSnippet = (item.text || '').slice(0, previewChars);
    const badges = badgesFor(item);
    return `
      <div class="signal-card-wrap signal-card-locked">
        <div class="cluster-head" style="margin-bottom:8px;">
          <span class="cat" data-cat="${radarCategory(item)}">${escape(item.source_name || sourceLabel(item.source_id))}</span>
          ${badges}
        </div>
        ${lockedCard(lockedTitle, lockedSnippet, { origin: 'signal_card', short: true })}
      </div>
    `;
  }
  if (window.RadarAnalytics) window.RadarAnalytics.contentViewed(item.id || item.source_id || 'signal', tier);
  const score = Math.round((item.opportunity_score || 0) * 100);
  const postedISO = item.posted_at || item.collected_at || '';
  const posted = postedISO ? formatDateTime(postedISO) : '';
  const itemLang = detectLang(`${item.title} ${item.text || ''}`);
  const userLang = State.lang;
  // Use Arabic translation if user is in Arabic mode AND item has been translated
  const isArabicMode = userLang === 'ar';
  const titleAr = item.title_ar || '';
  const showAr = isArabicMode && titleAr && itemLang !== 'ar';
  const displayedTitle = showAr ? titleAr : item.title;
  // Original title shown as muted secondary line when translated
  const originalLine = showAr
    ? `<div class="signal-original" lang="${itemLang}" dir="${itemLang === 'ar' ? 'rtl' : 'ltr'}">${escape(item.title)}</div>`
    : '';
  // Fallback translate button only if NO Arabic translation available
  const needsFallback = isArabicMode && !titleAr && itemLang !== 'ar';
  const translateBtn = needsFallback
    ? `<a class="signal-translate" href="${translateUrl(`${item.title}\n\n${(item.text || '').slice(0, 800)}`, userLang)}" target="_blank" rel="noreferrer" title="ترجم عبر Google Translate">ترجم ↗</a>`
    : '';
  const badges = badgesFor(item);
  return `
    <div class="signal-card-wrap">
      <a class="signal-card" href="${escape(item.source_url)}" target="_blank" rel="noreferrer">
        <div class="cluster-head">
          <span class="cat" data-cat="${radarCategory(item)}">${escape(item.source_name || sourceLabel(item.source_id))}</span>
          <span class="signal-meta-right">
            <span class="signal-lang signal-lang-${itemLang}">${langBadge(itemLang)}</span>
            <span class="cluster-growth ${score >= 70 ? 'hot' : 'up'}">${score}%</span>
          </span>
        </div>
        ${badges}
        <div class="cluster-topic">${escape(displayedTitle)}</div>
        ${originalLine}
        <div class="cluster-meta">${escape(item.signal_type || 'signal')} · <span${timeAttr(postedISO)}>${escape(posted)}</span></div>
        <p class="signal-text">${escape((item.text || '').slice(0, 210))}${(item.text || '').length > 210 ? '...' : ''}</p>
        <div class="cluster-voices">${escape((item.matched_keywords || []).slice(0, 8).join(' · '))}</div>
      </a>
      ${translateBtn}
    </div>
  `;
}

function normalizeRadarOpportunity(o, i) {
  const category = mapOpportunityCategory(o.id);
  const total = Math.max(18, Math.round((o.confidence || 0.5) * 40));
  const evidenceItems = o.evidence_items || [];
  const firstEvidence = evidenceItems[0] ? evidenceItems[0].title : '';
  return {
    id: o.id,
    rank: i + 1,
    category,
    title_en: radarTitleEn(o.id) || o.title_ar,
    title_ar: o.title_ar,
    desc_en: `Detected from ${o.signal_count || evidenceItems.length} linked public signals. Top evidence: ${firstEvidence}`,
    desc_ar: `فرصة مستخرجة من ${o.signal_count || evidenceItems.length} إشارة عامة موثقة. أقوى دليل: ${firstEvidence}`,
    audience_en: radarAudienceEn(o.id),
    audience_ar: radarAudienceAr(o.id),
    money_en: moneyPathEn(o.id),
    money_ar: moneyPathAr(o.id),
    scores: {
      novelty: Math.min(10, Math.max(5, Math.round((o.avg_score || 0.4) * 10) + 2)),
      momentum: Math.min(10, Math.max(5, Math.round((o.confidence || 0.5) * 10))),
      monetizability: monetizationScore(o.id),
      ease: easeScore(o.id),
      total
    },
    evidence: o.signal_count || evidenceItems.length,
    evidence_items: evidenceItems
  };
}

function moneyPathEn(id) {
  return {
    ai_agents_ops: {
      offer: 'Agent cost-control setup and monitoring dashboard',
      buyer: 'AI-heavy engineering teams',
      first_step: 'Audit one agent workflow and set token/action limits',
      pricing: '$500 setup + $99-$299/month'
    },
    ai_income_services: {
      offer: 'AI implementation/service package for a narrow business task',
      buyer: 'Individuals, freelancers, and small businesses with repeated work',
      first_step: 'Offer one manual AI-powered service before building software',
      pricing: '$200-$1,000 per package'
    },
    ai_income_tools: {
      offer: 'AI-powered product/app around a repeated use case',
      buyer: 'Startups, creators, or teams already searching for the workflow',
      first_step: 'Build a clickable MVP and charge for early access',
      pricing: '$9-$49/month or paid template'
    },
    ai_income_automation: {
      offer: 'Workflow automation using AI agents and integrations',
      buyer: 'Small companies losing time on repeated operations',
      first_step: 'Automate one painful process and document time saved',
      pricing: '$500 setup + monthly support'
    },
    ai_income_content: {
      offer: 'AI content production package with clear deliverables',
      buyer: 'Stores, creators, agencies, and personal brands',
      first_step: 'Sell 10 posts/videos/designs before building a platform',
      pricing: '$99-$299/month'
    },
    ai_dev_tools: {
      offer: 'Claude/Codex operating kit: repo rules, prompts, reviews',
      buyer: 'Small dev shops and solo founders',
      first_step: 'Sell a template kit plus one implementation call',
      pricing: '$49 kit or $300-$900 service'
    },
    ai_cost_quality: {
      offer: 'AI spend reduction report and routing rules',
      buyer: 'Teams paying growing API bills',
      first_step: 'Analyze logs, classify tasks, recommend cheaper model routes',
      pricing: '$750 audit + monthly monitoring'
    },
    ai_media_content: {
      offer: 'Short-form AI content production package',
      buyer: 'Creators, stores, agencies',
      first_step: 'Produce 10 clips from one product or topic',
      pricing: '$199/month or $25/video'
    }
  }[id] || {
    offer: 'A packaged service around the repeated pain',
    buyer: 'People already showing the pain in public signals',
    first_step: 'Create one landing page and test paid interest',
    pricing: 'Pilot price before SaaS'
  };
}

function moneyPathAr(id) {
  return {
    ai_agents_ops: {
      offer: 'إعداد مراقبة تكلفة وتحكم للوكلاء',
      buyer: 'فرق هندسية تستخدم وكلاء AI بكثافة',
      first_step: 'فحص سير عمل واحد ووضع حدود تكلفة/إجراءات',
      pricing: 'إعداد 500$ + اشتراك 99-299$/شهر'
    },
    ai_income_services: {
      offer: 'باقة خدمة/تطبيق AI لمهمة تجارية محددة',
      buyer: 'أفراد ومستقلون وشركات صغيرة لديها عمل متكرر',
      first_step: 'بيع خدمة يدوية مدعومة بالذكاء الاصطناعي قبل بناء برنامج',
      pricing: '200-1000$ لكل باقة'
    },
    ai_income_tools: {
      offer: 'منتج أو تطبيق مدعوم بالذكاء الاصطناعي حول استخدام متكرر',
      buyer: 'شركات ناشئة وصنّاع محتوى وفرق تبحث عن هذا المسار',
      first_step: 'بناء MVP بسيط وبيع وصول مبكر',
      pricing: '9-49$/شهر أو قالب مدفوع'
    },
    ai_income_automation: {
      offer: 'أتمتة سير عمل باستخدام وكلاء AI وتكاملات',
      buyer: 'شركات صغيرة تخسر وقتًا في عمليات متكررة',
      first_step: 'أتمتة عملية مؤلمة واحدة وتوثيق الوقت الموفر',
      pricing: 'إعداد 500$ + دعم شهري'
    },
    ai_income_content: {
      offer: 'باقة إنتاج محتوى AI بمخرجات واضحة',
      buyer: 'متاجر وصنّاع محتوى ووكالات وعلامات شخصية',
      first_step: 'بيع 10 منشورات/فيديوهات/تصاميم قبل بناء منصة',
      pricing: '99-299$/شهر'
    },
    ai_dev_tools: {
      offer: 'حزمة تشغيل Claude/Codex: قواعد مستودع، برومبتات، مراجعة',
      buyer: 'شركات تطوير صغيرة ومؤسسون مستقلون',
      first_step: 'بيع Kit جاهز مع جلسة تطبيق واحدة',
      pricing: '49$ للحزمة أو 300-900$ كخدمة'
    },
    ai_cost_quality: {
      offer: 'تقرير خفض تكلفة AI وقواعد اختيار النموذج',
      buyer: 'فرق لديها فواتير API متزايدة',
      first_step: 'تحليل السجلات وتصنيف المهام واقتراح routing أرخص',
      pricing: 'تدقيق 750$ + متابعة شهرية'
    },
    ai_media_content: {
      offer: 'باقة إنتاج محتوى قصير بالذكاء الاصطناعي',
      buyer: 'صنّاع محتوى، متاجر، وكالات',
      first_step: 'إنتاج 10 مقاطع من منتج أو موضوع واحد',
      pricing: '199$/شهر أو 25$/فيديو'
    }
  }[id] || {
    offer: 'خدمة مغلفة حول الألم المتكرر',
    buyer: 'أشخاص يظهر لديهم الألم في الإشارات العامة',
    first_step: 'صفحة هبوط واحدة واختبار استعداد الدفع',
    pricing: 'سعر تجريبي قبل بناء SaaS'
  };
}

function mapOpportunityCategory(id) {
  return {
    ai_income_services: 'ai_business',
    ai_income_tools: 'ai_tools',
    ai_income_automation: 'ai_automation',
    ai_income_content: 'ai_video',
    ai_agents_ops: 'ai_agents',
    ai_dev_tools: 'ai_coding',
    ai_cost_quality: 'ai_business',
    ai_media_content: 'ai_video'
  }[id] || 'ai_tools';
}

function radarCategory(item) {
  if (item.source_id && item.source_id.includes('reddit')) return 'ai_agents';
  if (item.source_id === 'github_repos') return 'ai_coding';
  if (item.source_kind === 'official') return 'ai_business';
  return 'ai_tools';
}

function sourceLabel(id) {
  return {
    reddit_artificial: 'Reddit r/artificial',
    reddit_machinelearning: 'Reddit r/MachineLearning',
    hn_algolia: 'Hacker News',
    github_repos: 'GitHub',
    arxiv_papers: 'arXiv',
    openai_news: 'OpenAI',
    google_deepmind: 'DeepMind',
    google_ai_blog: 'Google AI',
    huggingface_blog: 'Hugging Face',
    huggingface_daily_papers: 'HF Daily Papers',
    huggingface_models: 'HF Models',
    techcrunch_ai: 'TechCrunch',
    bens_bites: "Ben's Bites",
    reddit_localllama: 'Reddit r/LocalLLaMA',
    reddit_singularity: 'Reddit r/singularity',
    feedly: 'Feedly'
  }[id] || id || 'Source';
}

function radarTitleEn(id) {
  return {
    ai_income_services: 'AI-powered services people can sell',
    ai_income_tools: 'Sellable AI-powered products and apps',
    ai_income_automation: 'Business automations that can be priced',
    ai_income_content: 'AI content and marketing offers',
    ai_agents_ops: 'Running AI agents as production operations',
    ai_dev_tools: 'AI development tools around Claude, Cursor, and Codex',
    ai_cost_quality: 'Reducing AI model cost and quality failures',
    ai_media_content: 'AI audio, video, and design production'
  }[id];
}

function radarAudienceEn(id) {
  return {
    ai_income_services: 'Individuals, freelancers, and small teams packaging AI as a service',
    ai_income_tools: 'Startups and indie builders looking for AI-powered product ideas',
    ai_income_automation: 'Small businesses willing to pay for time-saving workflows',
    ai_income_content: 'Creators, stores, and agencies buying faster production',
    ai_agents_ops: 'Teams deploying agents that call tools, APIs, and workflows',
    ai_dev_tools: 'Developers using Claude Code, Cursor, Codex, Gemini, and repo agents',
    ai_cost_quality: 'AI-heavy companies worried about spend, reliability, and controls',
    ai_media_content: 'Creators and small teams producing media with AI'
  }[id] || 'AI builders and operators';
}

function radarAudienceAr(id) {
  return {
    ai_income_services: 'أفراد ومستقلون وفرق صغيرة يغلّفون AI كخدمة مدفوعة',
    ai_income_tools: 'شركات ناشئة وبناة مستقلون يبحثون عن أفكار منتجات مدعومة بالذكاء الاصطناعي',
    ai_income_automation: 'شركات صغيرة مستعدة للدفع مقابل أتمتة توفر الوقت',
    ai_income_content: 'صنّاع محتوى ومتاجر ووكالات تشترى إنتاجًا أسرع',
    ai_agents_ops: 'الفرق التي تشغل وكلاء يستدعون أدوات وواجهات API وسير عمل',
    ai_dev_tools: 'المطورون الذين يستخدمون Claude Code وCursor وCodex وGemini',
    ai_cost_quality: 'الشركات التي تستخدم AI بكثافة وتقلق من التكلفة والجودة والتحكم',
    ai_media_content: 'المبدعون والفرق الصغيرة التي تنتج محتوى بالذكاء الاصطناعي'
  }[id] || 'بناة ومشغلو منتجات الذكاء الاصطناعي';
}

function monetizationScore(id) {
  return { ai_income_services: 9, ai_income_tools: 8, ai_income_automation: 9, ai_income_content: 8, ai_agents_ops: 9, ai_dev_tools: 8, ai_cost_quality: 9, ai_media_content: 7 }[id] || 7;
}

function easeScore(id) {
  return { ai_income_services: 8, ai_income_tools: 6, ai_income_automation: 7, ai_income_content: 8, ai_agents_ops: 6, ai_dev_tools: 8, ai_cost_quality: 7, ai_media_content: 7 }[id] || 7;
}

function scoreChip(label, value) {
  const klass = value >= 8 ? 'high' : value >= 6 ? 'mid' : 'low';
  return `
    <div class="score-chip ${klass}">
      <span class="score-chip-label">${escape(label)}</span>
      <span class="score-chip-value">${value}</span>
    </div>
  `;
}

function clusterCard(c) {
  const topic = State.lang === 'ar' ? c.topic_ar : c.topic_en;
  const voices = State.lang === 'ar' ? c.voices_ar : c.voices_en;
  const catName = categoryName(c.category);
  const growthClass = c.growth >= 300 ? 'hot' : 'up';
  const max = Math.max(...c.spark);
  const sparkBars = c.spark.map(v => `<div class="spark-bar" style="height:${(v / max) * 100}%"></div>`).join('');
  return `
    <div class="cluster-card">
      <div class="cluster-head">
        <span class="cat" data-cat="${c.category}">${escape(catName)}</span>
        <span class="cluster-growth ${growthClass}">▲ +${c.growth}%</span>
      </div>
      <div class="cluster-topic">${escape(topic)}</div>
      <div class="cluster-meta">${c.tweet_count} ${t('tweets')} · ${(c.engagement / 1000).toFixed(1)}k ${t('engagement')}</div>
      <div class="spark">${sparkBars}</div>
      <div class="cluster-voices">${t('top_voices')}: ${escape(voices)}</div>
    </div>
  `;
}

function categoryCard(c, rank) {
  const name = State.lang === 'ar' ? c.name_ar : c.name_en;
  const deltaClass = c.delta >= 0 ? 'up' : 'down';
  const deltaArrow = c.delta >= 0 ? '▲' : '▼';
  const deltaAbs = Math.abs(c.delta);
  const sign = c.delta >= 0 ? '+' : '−';
  return `
    <div class="cluster-card category-card">
      <div class="cluster-head">
        <span class="cat" data-cat="${c.id}">${escape(name)}</span>
        <span class="cluster-growth ${deltaClass}">${deltaArrow} ${sign}${deltaAbs}%</span>
      </div>
      <div class="category-count">${c.count.toLocaleString()}</div>
      <div class="cluster-meta">${t('tweets')} · ${State.lang === 'ar' ? 'المرتبة' : 'Rank'} #${rank}</div>
    </div>
  `;
}

/* ---------- Helpers ---------- */

function categoryName(id) {
  const c = State.categories.find(x => x.id === id);
  if (!c) return id;
  return State.lang === 'ar' ? c.name_ar : c.name_en;
}

function formatDate(iso) {
  const d = new Date(iso);
  const opts = { year: 'numeric', month: 'long', day: 'numeric' };
  if (State.lang === 'ar') {
    return d.toLocaleDateString('ar-SA', opts);
  }
  return d.toLocaleDateString('en-US', opts).toUpperCase();
}

function formatDateTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const locale = State.lang === 'ar' ? 'ar-SA' : 'en-US';
  return d.toLocaleString(locale, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function escape(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ---------- Subscription / gating helpers ---------- */

function isSubscribed() {
  try { return !!(window.RadarSubscription && window.RadarSubscription.IsUserSubscribed()); }
  catch (e) { return false; }
}

function canAccess(item) {
  try {
    if (window.RadarSubscription && window.RadarSubscription.CanAccessContent) {
      return window.RadarSubscription.CanAccessContent(item);
    }
  } catch (e) {}
  // Safe default: free if no tier info, otherwise gated.
  const tier = item && item.tier;
  return !tier || tier === 'free';
}

function priceLabel() {
  const c = State.config && State.config.subscription;
  if (!c) return State.lang === 'ar' ? '15 دولار' : '$15';
  return State.lang === 'ar' ? (c.price_label_ar || '15 دولار') : (c.price_label_en || '$15');
}

function badgesFor(item) {
  if (!item) return '';
  const out = [];
  // High-signal badge (confidence ≥ 0.75) takes precedence visually
  if ((item.confidence || 0) >= 0.75) {
    out.push(`<span class="badge badge--high-signal">${t('tactical_high_signal')}</span>`);
  }
  if (item.is_featured) out.push(`<span class="badge badge--featured">${t('badge_featured')}</span>`);
  if (item.is_new)      out.push(`<span class="badge badge--new">${t('badge_new')}</span>`);
  if (item.tier === 'premium') {
    out.push(`<span class="badge badge--premium"><span class="lock-icon"></span>${t('badge_premium')}</span>`);
  } else if (item.tier === 'free') {
    out.push(`<span class="badge badge--free">${t('badge_free')}</span>`);
  }
  return out.length ? `<div class="badge-row">${out.join('')}</div>` : '';
}

function isHighSignal(o) {
  return (o && (o.confidence || 0) >= 0.75);
}

function lockedCard(title, snippet, opts) {
  opts = opts || {};
  const cta = opts.short ? t('locked_short_cta') : `${t('locked_cta')}`;
  const desc = opts.desc || t('locked_desc');
  return `
    <div class="locked-card">
      <div class="locked-preview">
        <div class="locked-title">${escape(title || t('locked_title'))}</div>
        <div class="locked-snippet">${escape(snippet || '')}</div>
      </div>
      <div class="locked-cta-row">
        <div class="locked-cta-text">${escape(desc)}</div>
        <a class="locked-cta-button" href="subscribe.html" data-event="subscribe_clicked" data-event-origin="${escape(opts.origin || 'locked_card')}">
          <span class="lock-icon"></span>${escape(cta)}
        </a>
      </div>
    </div>
  `;
}

function subscribeBanner() {
  if (isSubscribed()) return '';
  const subText = State.lang === 'ar'
    ? `افتح المحتوى الكامل بـ <strong>${priceLabel()}</strong>${State.config && State.config.subscription ? '/شهر' : ''}`
    : `Unlock full content for <strong>${priceLabel()}</strong>${State.config && State.config.subscription ? '/month' : ''}`;
  const small = State.lang === 'ar'
    ? 'إلغاء في أي وقت · الدفع عبر Stripe'
    : 'Cancel anytime · Payments via Stripe';
  const cta = State.lang === 'ar' ? t('subscribe_cta') : 'Subscribe';
  return `
    <div class="subscribe-banner">
      <div class="subscribe-banner-text">${subText}<small>${escape(small)}</small></div>
      <a class="subscribe-banner-cta" href="subscribe.html" data-event="subscribe_clicked" data-event-origin="banner">
        <span class="lock-icon"></span>${escape(cta)}
      </a>
    </div>
  `;
}

function emptyState(titleKey, descKey) {
  return `
    <div class="state-card">
      <div class="state-title">${escape(t(titleKey))}</div>
      <div class="state-desc">${escape(t(descKey))}</div>
    </div>
  `;
}

function tacticalLoading() {
  return `
    <div class="tactical-loading">
      <span>● ${escape(t('tactical_scanning'))}…</span>
      <div class="scan-bar"></div>
    </div>
  `;
}

/* When the brief or signals carry posted timestamps, mark them so telemetry
 * can refresh their relative display every 15s. */
function timeAttr(iso) {
  return iso ? ` data-timestamp="${escape(iso)}"` : '';
}

// Wire data-event attributes to RadarAnalytics if loaded
document.addEventListener('click', (e) => {
  const a = e.target && (e.target.closest && e.target.closest('[data-event]'));
  if (!a) return;
  const event = a.dataset.event;
  if (!event || !window.RadarAnalytics) return;
  const origin = a.dataset.eventOrigin;
  if (event === 'subscribe_clicked' && window.RadarAnalytics.subscribeClicked) {
    window.RadarAnalytics.subscribeClicked(origin || 'unknown');
  }
});

document.addEventListener('DOMContentLoaded', bootstrap);
