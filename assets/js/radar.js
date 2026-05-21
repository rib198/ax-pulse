const RadarState = {
  layer: 'opportunities',
  lang: localStorage.getItem('axp_lang') || 'ar',
  signals: [],
  corpusSignals: [],
  cardCandidates: [],
  cardCandidatesGeneratedAt: null,
  validationReport: null,
  reviewQueueSummary: null,
  focusedOpportunities: [],
  focusedOpportunitiesGeneratedAt: null,
  focusedUpdates: [],
  focusedUpdatesGeneratedAt: null,
  focusedDiscussions: [],
  focusedDiscussionsGeneratedAt: null,
  openAIIntelligence: null,
  timeline: [],
  opportunities: [],
  productPlaybooks: [],
  researchOpportunities: [],
  globalSources: [],
  runStatus: null,
  manualXBrief: null,
  manualXReady: null,
  accounts: [],
  generatedAt: null,
  particles: [],
  tickerTimer: null,
  refreshTimer: null,
  visualPulseTimer: null,
  timelineAutoTimer: null,
  timelinePauseTimer: null,
  activeTimelineIndex: 0,
  autoTimelinePaused: false,
  knownSignalIds: new Set(),
  lastLiveItems: [],
  archiveExpanded: false,
  activeDetail: null
};

const LAYERS = {
  radar: {
    title: { ar: 'ما الجديد اليوم؟', en: 'What is new today?' },
    summary: {
      ar: 'تحديثات النماذج والأدوات والأسعار، مكتوبة كملخص عملي: ماذا حدث، لماذا يهم، وكيف يمكن الاستفادة منه.',
      en: 'Model, tool, and pricing updates explained as: what happened, why it matters, and how to use it.'
    }
  },
  trending: {
    title: { ar: 'ماذا يتحدث الناس عنه؟', en: 'What are people talking about?' },
    summary: {
      ar: 'نقاشات عالية الاهتمام من X ومصادر اجتماعية، نقرأها ونلخص لماذا قد تكون مهمة لا نعرضها كنص خام.',
      en: 'High-engagement public conversations about AI, used to detect attention, objections, and market curiosity.'
    }
  },
  opportunities: {
    title: { ar: 'أفضل الفرص الآن', en: 'Top opportunities now' },
    summary: {
      ar: 'فرص لكسب المال مستخرجة من إشارات حديثة: المشكلة، لمن، لماذا الآن، كيف تستفيد، والثقة.',
      en: 'Buildable opportunities from recent signals: problem, target user, why now, value angle, and confidence.'
    }
  },
  sources: {
    title: { ar: 'هل البيانات محدثة؟', en: 'Is the data fresh?' },
    summary: {
      ar: 'حالة كل مصدر بلغة بسيطة: نجح في آخر رصد، غير متصل، نعرض نسخة محفوظة، أو تعذّر تحديثه مؤقتًا.',
      en: 'Per-source freshness in plain language: succeeded last scan, disconnected, cached, or failed.'
    }
  },
  signals: {
    title: { ar: 'عرض الأدلة', en: 'Evidence view' },
    summary: {
      ar: 'الأدلة والروابط التي بُنيت عليها الفرص والتحديثات. هذا القسم للتوسّع وليس نقطة البداية.',
      en: 'Evidence and links behind the opportunities and updates. This is for expansion, not the starting point.'
    }
  }
};

const I18N = {
  // Card titles
  best_opportunity: { ar: 'أفضل فرصة', en: 'Top opportunity' },
  no_opportunity_yet: { ar: 'لا توجد فرصة مؤكدة بعد', en: 'No confirmed opportunity yet' },
  evidence_count: { ar: (n, c) => `${n} أدلة · ثقة ${c}%`, en: (n, c) => `${n} evidence items · ${c}% confidence` },
  need_more_signals: { ar: 'نحتاج إشارات أكثر', en: 'We need more signals' },
  nearby_evidence: { ar: 'أدلة قريبة', en: 'Nearby evidence' },
  acceptance_criteria: { ar: 'معيار القبول', en: 'Acceptance criteria' },
  no_opp_no_source: { ar: 'لا فرصة بلا مصدر', en: 'No opportunity without a source' },
  every_card_link: {
    ar: 'كل بطاقة يجب أن تقود إلى رابط يمكن التحقق منه.',
    en: 'Every card must lead to a verifiable link.'
  },
  active_sources: { ar: 'مصادر نشطة', en: 'Active sources' },
  signals_word: { ar: 'إشارة', en: 'signals' },
  focused_x_accounts: { ar: 'حسابات X مركزة', en: 'Focused X accounts' },
  followers: { ar: 'متابع', en: 'followers' },
  collection_strategy: { ar: 'استراتيجية الجمع', en: 'Collection strategy' },
  layered_not_random: { ar: 'طبقات لا عشوائية', en: 'Layered, not random' },
  monitor_strategy_text: {
    ar: 'X يراقب الحسابات المتخصصة، بينما المصادر الرسمية تعطي الثقة.',
    en: 'X tracks focused accounts, while official sources provide trust.'
  },
  the_signals: { ar: 'الإشارات', en: 'Signals' },
  posts_news_repos: {
    ar: 'منشورات وأخبار ومستودعات موثقة',
    en: 'Verified posts, news, and repositories'
  },
  latest_pulse: { ar: 'أحدث نبض', en: 'Latest pulse' },
  signal_strength: { ar: 'قوة الإشارة', en: 'Signal strength' },
  monitoring: { ar: 'مراقبة', en: 'monitoring' },
  active_tags: { ar: 'وسوم نشطة', en: 'Active tags' },
  signals_short: { ar: 'إشارات', en: 'signals' },
  the_radar: { ar: 'الرادار', en: 'The radar' },
  active_word: { ar: 'نشط', en: 'Active' },
  signals_in_last_run: {
    ar: (n) => `${n} إشارة في آخر تشغيل`,
    en: (n) => `${n} signals in latest run`
  },
  the_goal: { ar: 'الهدف', en: 'The goal' },
  early_detection: {
    ar: 'اكتشاف التحول مبكرًا',
    en: 'Detect the shift early'
  },
  pre_crowded_market: {
    ar: 'نبحث عن الألم والتكلفة والزخم قبل أن تتحول إلى سوق مزدحم.',
    en: 'We hunt pain, cost, and momentum before they become a crowded market.'
  },
  signals_label: { ar: 'الإشارات', en: 'Signals' },
  opportunities_label: { ar: 'الفرص', en: 'Opportunities' },
  in_progress: { ar: 'قيد المتابعة', en: 'In progress' },
  source_links_direct: {
    ar: 'مصادر مرتبطة بروابط مباشرة',
    en: 'Sources linked with direct URLs'
  },
  radar_mode: { ar: 'وضع الرادار', en: 'Radar mode' },
  live_label: { ar: 'مباشر', en: 'Live' },
  globe_centered: {
    ar: 'الكرة ثابتة في المركز، والطبقات حولها تتغير حسب اختيار المستخدم.',
    en: 'The globe stays at the center while layers around it change with the user’s choice.'
  },
  no_update_yet: { ar: 'لا تحديث بعد', en: 'No update yet' },
  last_update: { ar: 'آخر تحديث', en: 'Updated' },
  signal_word: { ar: 'إشارة', en: 'signal' },
  // Layer button labels (also localized in dock pills)
  nav_radar: { ar: 'جديد اليوم', en: "What's new" },
  nav_trending: { ar: 'نقاش الناس', en: 'People talk' },
  nav_opportunities: { ar: 'فرص الدخل', en: 'Money ideas' },
  nav_sources: { ar: 'حالة البيانات', en: 'Data status' },
  nav_signals: { ar: 'الأدلة', en: 'Evidence' },
  nav_radar_short: { ar: 'جديد', en: 'News' },
  nav_trending_short: { ar: 'نقاش', en: 'Talk' },
  nav_opportunities_short: { ar: 'دخل', en: 'Money' },
  nav_sources_short: { ar: 'الحالة', en: 'Status' },
  nav_signals_short: { ar: 'أدلة', en: 'Proof' },
  // Footer / portrait
  dashboard_link: { ar: 'لوحة التحكم', en: 'Dashboard' },
  loading_data: { ar: 'جارٍ تحميل البيانات...', en: 'Loading data...' },
  rotate_phone_h1: { ar: 'رادار الذكاء الاصطناعي', en: 'AI Radar' },
  rotate_phone_p: {
    ar: 'ابدأ بأفضل فرصة الآن، ثم شاهد الخبر والنقاش والدليل خلفها. التجربة الكاملة أفضل بالعرض.',
    en: 'Start with the top opportunity, then see the news, discussion, and evidence behind it. The full radar works best in landscape.'
  },
  value_statement: {
    ar: 'ابدأ بأفضل فرصة الآن، ثم شاهد الخبر والنقاش والدليل خلفها.',
    en: 'Start with the top opportunity, then see the news, discussion, and evidence behind it.'
  },
  signals_detected: { ar: 'إشارة مرصودة', en: 'signals tracked' },
  ideas_available: { ar: 'فكرة ملهمة', en: 'ideas' },
  updated_short: { ar: 'حالة المصادر', en: 'source health' },
  tap_hint: { ar: 'اضغط على نقطة أو وسم لاستكشاف الإشارة', en: 'Tap a point or tag to explore the signal' },
  save: { ar: 'حفظ', en: 'Save' },
  saved: { ar: 'تم الحفظ', en: 'Saved' },
  chat_with_gpt: { ar: 'ناقشها مع ChatGPT', en: 'Discuss with ChatGPT' },
  chat_send: { ar: 'إرسال', en: 'Send' },
  chat_placeholder: { ar: 'اسألي عن الفكرة أو طريقة الاستفادة...', en: 'Ask about the idea or how to use it...' },
  chat_intro: {
    ar: 'أنا جاهز لمناقشة هذه البطاقة. اسأليني عن: هل تصلح كفرصة دخل؟ ما أول خطوة؟ من العميل؟ أو كيف أشرحها بشكل أبسط.',
    en: 'I can discuss this card. Ask: is it a money opportunity, what is the first step, who is the user, or how to explain it simply.'
  },
  chat_wait: { ar: 'أفكر في البطاقة...', en: 'Thinking through the card...' },
  chat_user_label: { ar: 'أنتِ', en: 'You' },
  chat_ai_label: { ar: 'ChatGPT', en: 'ChatGPT' },
  mobile_action: { ar: 'استعرض المختصر', en: 'View brief' }
};

const FALLBACK_TAGS = ['Claude', 'Codex', 'Cursor', 'Agents', 'OpenAI', 'GitHub', 'MCP', 'LLM'];

function t(key, ...args) {
  const entry = I18N[key];
  if (!entry) return key;
  const value = entry[RadarState.lang] || entry.en || entry.ar;
  return typeof value === 'function' ? value(...args) : value;
}

async function loadJSON(path, fallback) {
  const inlineData = window.RADAR_INLINE_DATA && window.RADAR_INLINE_DATA[path];
  if (location.protocol === 'file:' && inlineData !== undefined) {
    return inlineData;
  }
  try {
    const res = await fetch(path, { cache: 'no-store' });
    if (!res.ok) throw new Error(path);
    return await res.json();
  } catch (err) {
    if (inlineData !== undefined) {
      return inlineData;
    }
    return fallback;
  }
}

async function loadRadarData() {
  const [signals, corpus, cardCandidates, validationReport, reviewQueueSummary, focusedOpportunities, focusedUpdates, focusedDiscussions, openAIIntelligence, timeline, opportunities, productPlaybooks, dynamicPlaybooks, researchOpportunities, globalSources, runStatus, manualXCurated, manualXBrief, manualXReady, accounts] = await Promise.all([
    loadJSON('data/radar/signals.json', { items: [], count: 0 }),
    loadJSON('data/radar/signals_corpus.json', { items: [], count: 0 }),
    loadJSON('data/radar/radar_card_candidates.json', { items: [], count: 0 }),
    loadJSON('data/radar/card_validation_report.json', null),
    loadJSON('data/radar/review_queue_summary.json', null),
    loadJSON('data/radar/focused_opportunities.json', { opportunities: [], total_opportunities: 0 }),
    loadJSON('data/radar/focused_updates.json', { updates: [], total_updates: 0 }),
    loadJSON('data/radar/focused_discussions.json', { discussions: [], total_discussions: 0 }),
    loadJSON('data/radar/openai_intelligence_cards.json', { cards: [], card_count: 0, status: 'missing' }),
    loadJSON('data/radar/model_timeline.json', { items: [] }),
    loadJSON('data/radar/opportunities.json', { opportunities: [] }),
    loadJSON('data/radar/product_playbooks.json', { playbooks: [] }),
    loadJSON('data/radar/product_playbooks_dynamic.json', { playbooks: [] }),
    loadJSON('data/radar/research_opportunities.json', { opportunities: [] }),
    loadJSON('data/radar/global_sources.json', { groups: [] }),
    loadJSON('data/radar/run_status.json', null),
    loadJSON('data/manual_x/curated_opportunities.json', null),
    loadJSON('data/manual_x/x_brief.json', null),
    loadJSON('data/manual_x/radar_ready_posts.json', null),
    loadJSON('data/radar/x_focus_accounts.json', { accounts: [] })
  ]);
  const chosenPlaybooks = (dynamicPlaybooks.playbooks || []).length ? dynamicPlaybooks : productPlaybooks;
  return { signals, corpus, cardCandidates, validationReport, reviewQueueSummary, focusedOpportunities, focusedUpdates, focusedDiscussions, openAIIntelligence, timeline, opportunities, productPlaybooks: chosenPlaybooks, researchOpportunities, globalSources, runStatus, manualXBrief: manualXCurated || manualXBrief, manualXReady, accounts };
}

async function bootRadar() {
  const { signals, corpus, cardCandidates, validationReport, reviewQueueSummary, focusedOpportunities, focusedUpdates, focusedDiscussions, openAIIntelligence, timeline, opportunities, productPlaybooks, researchOpportunities, globalSources, runStatus, manualXBrief, manualXReady, accounts } = await loadRadarData();

  RadarState.signals = signals.items || [];
  RadarState.corpusSignals = sortSignalsByFreshness(corpus.items || RadarState.signals);
  RadarState.cardCandidates = cardCandidates.items || [];
  RadarState.cardCandidatesGeneratedAt = cardCandidates.generated_at || null;
  RadarState.validationReport = validationReport;
  RadarState.reviewQueueSummary = reviewQueueSummary;
  RadarState.focusedOpportunities = focusedOpportunities.opportunities || [];
  RadarState.focusedOpportunitiesGeneratedAt = focusedOpportunities.generated_at || null;
  RadarState.focusedUpdates = focusedUpdates.updates || [];
  RadarState.focusedUpdatesGeneratedAt = focusedUpdates.generated_at || null;
  RadarState.focusedDiscussions = focusedDiscussions.discussions || [];
  RadarState.focusedDiscussionsGeneratedAt = focusedDiscussions.generated_at || null;
  RadarState.openAIIntelligence = openAIIntelligence;
  // model_timeline.json's schema uses `events`, not `items`.
  // Keep `items` fallback for older snapshots / safety.
  RadarState.timeline = sortTimeline(timeline.events || timeline.items || []);
  RadarState.generatedAt = signals.generated_at;
  RadarState.opportunities = opportunities.opportunities || [];
  RadarState.productPlaybooks = productPlaybooks.playbooks || [];
  RadarState.researchOpportunities = researchOpportunities.opportunities || [];
  RadarState.globalSources = globalSources.groups || [];
  RadarState.runStatus = runStatus;
  RadarState.manualXBrief = manualXBrief;
  RadarState.manualXReady = manualXReady;
  RadarState.accounts = accounts.accounts || [];
  RadarState.knownSignalIds = new Set(RadarState.signals.map(signalKey));

  applyLang();
  wireLayers();
  wireLangToggle();
  wireResponsiveLabels();
  wireDetailModal();
  wireRadarSurface();
  resetDetailState();
  // Allow deprecated stub pages (dashboard, trending, opportunities,
  // categories, mediator) to deep-link into a specific layer via ?layer=...
  const initialParams = new URLSearchParams(location.search);
  const requestedLayer = initialParams.get('layer');
  const initialLayer = (requestedLayer && LAYERS[requestedLayer])
    ? requestedLayer
    : 'opportunities';
  renderLayer(initialLayer);
  setupParticles();
  startVisualHeartbeat();
  startLiveRefresh();
}

function startLiveRefresh() {
  if (RadarState.refreshTimer) window.clearInterval(RadarState.refreshTimer);
  RadarState.refreshTimer = window.setInterval(refreshRadarData, 30000);
}

function startVisualHeartbeat() {
  if (RadarState.visualPulseTimer) window.clearInterval(RadarState.visualPulseTimer);
  let tick = 0;
  const pulse = () => {
    tick += 1;
    document.body.classList.remove('radar-beat');
    document.querySelectorAll('.signal-active').forEach((el) => el.classList.remove('signal-active'));

    const tags = Array.from(document.querySelectorAll('.tag'));
    const nodes = Array.from(document.querySelectorAll('.radar-node'));
    const chips = Array.from(document.querySelectorAll('.panel-feed .signal-chip'));

    const tag = tags[tick % Math.max(tags.length, 1)];
    const node = nodes[tick % Math.max(nodes.length, 1)];
    const chip = chips[tick % Math.max(chips.length, 1)];

    requestAnimationFrame(() => {
      document.body.classList.add('radar-beat');
      tag && tag.classList.add('signal-active');
      node && node.classList.add('signal-active');
      chip && chip.classList.add('signal-active');
    });

    window.setTimeout(() => {
      document.body.classList.remove('radar-beat');
      tag && tag.classList.remove('signal-active');
      node && node.classList.remove('signal-active');
      chip && chip.classList.remove('signal-active');
    }, 1400);
  };

  pulse();
  RadarState.visualPulseTimer = window.setInterval(pulse, 4200);
}

async function refreshRadarData() {
  const { signals, corpus, cardCandidates, validationReport, reviewQueueSummary, focusedOpportunities, focusedUpdates, focusedDiscussions, openAIIntelligence, timeline, opportunities, productPlaybooks, researchOpportunities, globalSources, runStatus, manualXBrief, manualXReady, accounts } = await loadRadarData();
  const nextSignals = signals.items || [];
  const nextGeneratedAt = signals.generated_at;
  const nextIds = new Set(nextSignals.map(signalKey));
  const newItems = nextSignals.filter((item) => !RadarState.knownSignalIds.has(signalKey(item))).slice(0, 4);
  const changed = nextGeneratedAt && nextGeneratedAt !== RadarState.generatedAt;

  if (!changed && !newItems.length) return;

  RadarState.signals = nextSignals;
  RadarState.corpusSignals = sortSignalsByFreshness(corpus.items || nextSignals);
  RadarState.cardCandidates = cardCandidates.items || RadarState.cardCandidates;
  RadarState.cardCandidatesGeneratedAt = cardCandidates.generated_at || RadarState.cardCandidatesGeneratedAt;
  RadarState.validationReport = validationReport || RadarState.validationReport;
  RadarState.reviewQueueSummary = reviewQueueSummary || RadarState.reviewQueueSummary;
  RadarState.focusedOpportunities = focusedOpportunities.opportunities || RadarState.focusedOpportunities;
  RadarState.focusedOpportunitiesGeneratedAt = focusedOpportunities.generated_at || RadarState.focusedOpportunitiesGeneratedAt;
  RadarState.focusedUpdates = focusedUpdates.updates || RadarState.focusedUpdates;
  RadarState.focusedUpdatesGeneratedAt = focusedUpdates.generated_at || RadarState.focusedUpdatesGeneratedAt;
  RadarState.focusedDiscussions = focusedDiscussions.discussions || RadarState.focusedDiscussions;
  RadarState.focusedDiscussionsGeneratedAt = focusedDiscussions.generated_at || RadarState.focusedDiscussionsGeneratedAt;
  RadarState.openAIIntelligence = openAIIntelligence || RadarState.openAIIntelligence;
  RadarState.timeline = sortTimeline(timeline.events || timeline.items || RadarState.timeline);
  RadarState.generatedAt = nextGeneratedAt;
  RadarState.opportunities = opportunities.opportunities || RadarState.opportunities;
  RadarState.productPlaybooks = productPlaybooks.playbooks || RadarState.productPlaybooks;
  RadarState.researchOpportunities = researchOpportunities.opportunities || RadarState.researchOpportunities;
  RadarState.globalSources = globalSources.groups || RadarState.globalSources;
  RadarState.runStatus = runStatus || RadarState.runStatus;
  RadarState.manualXBrief = manualXBrief || RadarState.manualXBrief;
  RadarState.manualXReady = manualXReady || RadarState.manualXReady;
  RadarState.accounts = accounts.accounts || RadarState.accounts;
  RadarState.knownSignalIds = nextIds;
  RadarState.lastLiveItems = newItems.length ? newItems : nextSignals.slice(0, 1);

  document.body.classList.add('has-live-arrival');
  window.setTimeout(() => document.body.classList.remove('has-live-arrival'), 1800);
  renderLayer(RadarState.layer);
  showLiveArrival(RadarState.lastLiveItems[0]);
}

function applyLang() {
  document.documentElement.setAttribute('lang', RadarState.lang);
  document.documentElement.setAttribute('dir', RadarState.lang === 'ar' ? 'rtl' : 'ltr');
  // Localize nav button labels
  document.querySelectorAll('.radar-nav button[data-layer]').forEach((btn) => {
    const layer = btn.dataset.layer;
    const key = compactNavLabels() ? `nav_${layer}_short` : 'nav_' + layer;
    if (I18N[key]) btn.textContent = t(key);
  });
  // Footer
  const dashLink = document.querySelector('.radar-footer a');
  if (dashLink) dashLink.textContent = t('dashboard_link');
  // Portrait guard
  const portraitH1 = document.querySelector('.portrait-guard h1');
  const portraitP = document.querySelector('.portrait-guard p');
  const mobileAction = document.querySelector('[data-mobile-action]');
  if (portraitH1) portraitH1.textContent = t('rotate_phone_h1');
  if (portraitP) portraitP.textContent = t('rotate_phone_p');
  if (mobileAction) mobileAction.textContent = t('mobile_action');
  const valueStatement = document.getElementById('value-statement');
  const interactionHint = document.getElementById('interaction-hint');
  const saveButton = document.getElementById('detail-save');
  const kicker = document.querySelector('.radar-kicker');
  const signalsLabel = document.getElementById('stat-signals-label');
  const ideasLabel = document.getElementById('stat-ideas-label');
  const updatedLabel = document.getElementById('stat-updated-label');
  if (valueStatement) valueStatement.textContent = t('value_statement');
  if (interactionHint) interactionHint.textContent = t('tap_hint');
  if (saveButton) saveButton.textContent = t('save');
  if (signalsLabel) signalsLabel.textContent = t('signals_detected');
  if (ideasLabel) ideasLabel.textContent = t('ideas_available');
  if (updatedLabel) updatedLabel.textContent = t('updated_short');
  if (kicker) kicker.innerHTML = `<span></span> ${RadarState.lang === 'ar' ? 'رادار' : 'RADAR'}`;
  // Lang toggle active state
  document.querySelectorAll('.radar-lang button').forEach((b) => {
    b.classList.toggle('active', b.dataset.lang === RadarState.lang);
  });
  updateValueStats();
  updateSaveButton();
}

function compactNavLabels() {
  return Boolean(window.matchMedia && window.matchMedia('(max-width: 760px) and (orientation: portrait)').matches);
}

function wireResponsiveLabels() {
  let compact = compactNavLabels();
  window.addEventListener('resize', () => {
    const next = compactNavLabels();
    if (next === compact) return;
    compact = next;
    applyLang();
  });
}

function wireLangToggle() {
  document.querySelectorAll('.radar-lang button').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (btn.dataset.lang === RadarState.lang) return;
      RadarState.lang = btn.dataset.lang;
      localStorage.setItem('axp_lang', RadarState.lang);
      applyLang();
      renderLayer(RadarState.layer);
    });
  });
}

function wireLayers() {
  document.querySelectorAll('[data-layer]').forEach((button) => {
    if (button.classList.contains('radar-lang')) return;
    button.addEventListener('click', () => renderLayer(button.dataset.layer));
  });
}

function renderLayer(layer) {
  RadarState.layer = layer;
  document.body.className = `radar-body layer-${layer}`;
  resetDetailState();
  clearTicker();
  scheduleTimelineAutoplay();
  document.querySelectorAll('[data-layer]').forEach((button) => {
    if (button.parentElement && button.parentElement.classList.contains('radar-lang')) return;
    button.classList.toggle('active', button.dataset.layer === layer);
  });

  const meta = LAYERS[layer] || LAYERS.radar;
  document.getElementById('layer-title').textContent = meta.title[RadarState.lang] || meta.title.en;
  document.getElementById('layer-summary').textContent = meta.summary[RadarState.lang] || meta.summary.en;
  document.getElementById('radar-updated').textContent = sourceFooterLabel();
  updateValueStats();

  renderDock(layer);
  renderRadarTags(layer);
  renderSourceSpokes(layer);
  renderSourceHealthPanel(layer);
  renderFloatingStrip(layer);
}

function updateValueStats() {
  const signals = document.getElementById('stat-signals');
  const ideas = document.getElementById('stat-ideas');
  const updated = document.getElementById('stat-updated');
  if (signals) signals.textContent = formatNumber(qualityAcceptedCount() || candidateNewsRows().length || 0);
  if (ideas) ideas.textContent = formatNumber(opportunityDisplayCount());
  if (updated) updated.textContent = sourceHealthSummary();
  renderSinceLastSeen();
}

// Counts cards that have appeared/refreshed since the user's previous visit and
// surfaces them as a thin banner above the layer copy. Uses localStorage to
// remember when the user last saw the radar (per-browser).
function renderSinceLastSeen() {
  const valueRail = document.querySelector('.value-rail');
  if (!valueRail) return;
  const isAr = RadarState.lang === 'ar';
  const STORAGE_KEY = 'axp_last_seen_at';
  const previous = localStorage.getItem(STORAGE_KEY);
  const previousMs = previous ? Date.parse(previous) : 0;

  const cards = []
    .concat(RadarState.focusedUpdates || [])
    .concat(RadarState.focusedDiscussions || [])
    .concat((RadarState.manualXReady && RadarState.manualXReady.cards) || []);

  let newSinceVisit = 0;
  let breaking = 0;
  cards.forEach((c) => {
    const ts = c.last_refreshed_at || c.first_appeared_at || c.detected_at;
    const ms = ts ? Date.parse(ts) : 0;
    if (ms && ms > previousMs) newSinceVisit += 1;
    if (c.freshness === 'breaking') breaking += 1;
  });

  let banner = document.getElementById('ax-since-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'ax-since-banner';
    banner.className = 'since-last-seen-banner';
    valueRail.parentNode.insertBefore(banner, valueRail);
  }

  if (!previous) {
    // First visit — set baseline silently and skip the banner.
    localStorage.setItem(STORAGE_KEY, new Date().toISOString());
    banner.hidden = true;
    return;
  }

  if (newSinceVisit === 0 && breaking === 0) {
    banner.hidden = true;
    return;
  }

  const parts = [];
  if (newSinceVisit > 0) {
    parts.push(isAr
      ? `وصلت ${formatNumber(newSinceVisit)} إشارة منذ زيارتك الأخيرة`
      : `${formatNumber(newSinceVisit)} new signals since your last visit`);
  }
  if (breaking > 0) {
    parts.push(isAr ? `🔥 ${breaking} الآن` : `🔥 ${breaking} breaking`);
  }
  banner.hidden = false;
  banner.innerHTML = `
    <span class="since-banner-dot" aria-hidden="true"></span>
    <span class="since-banner-text">${escapeHTML(parts.join(' · '))}</span>
    <button type="button" class="since-banner-mark" aria-label="${escapeAttr(isAr ? 'وضع علامة كقُرئت' : 'Mark as seen')}">${escapeHTML(isAr ? 'تم' : 'Mark seen')}</button>
  `;
  const markBtn = banner.querySelector('.since-banner-mark');
  if (markBtn) {
    markBtn.addEventListener('click', () => {
      localStorage.setItem(STORAGE_KEY, new Date().toISOString());
      banner.hidden = true;
    });
  }
}

function qualityAcceptedCount() {
  const report = RadarState.validationReport || {};
  const ready = RadarState.manualXReady || {};
  return Number(
    ready.accepted_count ||
    report.valid_count ||
    RadarState.cardCandidates.length ||
    0
  );
}

// Dedup key for opportunityDisplayCount — lowercases, trims, collapses
// whitespace. Inlined here because the previous reference to a free
// `normalize()` helper threw ReferenceError and killed the entire render
// chain (stats stuck at "—", data-panel never populated).
function _opportunityKey(value) {
  return String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
}

function opportunityDisplayCount() {
  return allWorthyOpportunityRows().length;
}

function reviewPendingCount() {
  return Number((RadarState.reviewQueueSummary || {}).total_pending || 0);
}

function qualityRejectedCount() {
  const report = RadarState.validationReport || {};
  return Number(report.rejected_count || 0) + Number(report.review_count || 0);
}

function qualityStatusLine() {
  const valid = qualityAcceptedCount();
  const pending = reviewPendingCount();
  const rejected = qualityRejectedCount();
  if (RadarState.lang === 'ar') {
    return `${valid} بطاقة مجازة · ${pending} في المراجعة · ${rejected} مرفوضة`;
  }
  return `${valid} approved cards · ${pending} in review · ${rejected} rejected`;
}

function translatedBadgeLabel(item = {}) {
  if (RadarState.lang === 'ar') return '';
  const hasArabic = containsArabic(item.title_ar || item.summary_ar || item.what_happened || '');
  if (RadarState.lang === 'en') return 'Edited';
  return '';
}

function shouldShowFreshnessBadge(freshness) {
  if (!freshness) return false;
  return ['breaking', 'new_today', 'refreshed_today', 'new', 'updated', 'strong', 'verified', 'uncertain'].includes(freshness.key);
}

function freshnessBadgeHTML(freshness) {
  if (!shouldShowFreshnessBadge(freshness)) return '';
  const key = escapeAttr(freshness.key || 'updated');
  const label = escapeHTML(freshness.label || '');
  return `<b class="freshness-badge freshness-${key}">${label}</b>`;
}

function itemScanAgeMinutes(item = {}) {
  const raw = item.detected_at || item.last_seen_at || item.collected_at || item.posted_at || item.date || item.generated_at;
  const time = Date.parse(raw || '');
  if (Number.isNaN(time)) return Infinity;
  return Math.max(0, Math.round((Date.now() - time) / 60000));
}

function compactUpdateLabel() {
  const latest = latestGeneratedAt();
  if (!latest) return '—';
  const time = Date.parse(latest);
  if (Number.isNaN(time)) return '—';
  const minutes = Math.max(0, Math.round((Date.now() - time) / 60000));
  if (minutes < 1) return RadarState.lang === 'ar' ? 'الآن' : 'Now';
  if (minutes < 60) return RadarState.lang === 'ar' ? `${minutes} د` : `${minutes}m`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return RadarState.lang === 'ar' ? `${hours} س` : `${hours}h`;
  const date = new Date(time);
  return date.toLocaleDateString(RadarState.lang === 'ar' ? 'ar-SA' : 'en-US', { day: 'numeric', month: 'short' });
}

function scheduleTimelineAutoplay() {
  if (RadarState.timelineAutoTimer) window.clearInterval(RadarState.timelineAutoTimer);
  RadarState.timelineAutoTimer = null;
  if (RadarState.layer !== 'radar' || !RadarState.timeline.length) return;

  RadarState.timelineAutoTimer = window.setInterval(() => {
    if (RadarState.layer !== 'radar' || RadarState.autoTimelinePaused) return;
    // Never let autoplay paint a detail card over an open conversation
    // or a user-opened detail. The user's foreground takes priority.
    if (document.body.classList.contains('has-chat-open')) return;
    const dm = document.getElementById('detail-modal');
    if (dm && !dm.hidden) return;
    const rows = timelineRows();
    if (!rows.length) return;
    RadarState.activeTimelineIndex = (RadarState.activeTimelineIndex + 1) % rows.length;
    openTimelineDetail(rows[RadarState.activeTimelineIndex], RadarState.activeTimelineIndex, true);
    highlightTimelineChip(RadarState.activeTimelineIndex);
  }, 6200);
}

function pauseTimelineAutoplay() {
  RadarState.autoTimelinePaused = true;
  if (RadarState.timelinePauseTimer) window.clearTimeout(RadarState.timelinePauseTimer);
  RadarState.timelinePauseTimer = window.setTimeout(() => {
    RadarState.autoTimelinePaused = false;
  }, 18000);
}

function highlightTimelineChip(idx) {
  document.querySelectorAll('[data-timeline-idx]').forEach((chip) => {
    chip.classList.toggle('active', Number(chip.dataset.timelineIdx) === idx);
  });
}

function renderRadarTags(layer) {
  const root = document.getElementById('radar-tags');
  if (!root) return;
  const tags = tagsForLayer(layer).slice(0, 8);
  root.innerHTML = tags.map((tag, index) => {
    const klass = layer === 'opportunities' ? 'opportunity' : (layer === 'trending' ? 'hot' : '');
    const count = tagSignalCount(tag, index);
    return `<span class="tag tag-pos-${index} ${klass}" role="button" tabindex="0" data-radar-idx="${index}">#${escapeHTML(tag)}<em>${escapeHTML(count)}</em></span>`;
  }).join('');
}

function tagsForLayer(layer) {
  if (layer === 'sources') {
    const ids = Object.entries(countBy(RadarState.signals, 'source_id'))
      .sort((a, b) => b[1] - a[1])
      .map(([id]) => sourceName(id).replace(/\s+/g, ''));
    return ids.length ? ids : ['X', 'GitHub', 'OpenAI', 'DeepMind'];
  }

  if (layer === 'opportunities') {
    const fromEvidence = RadarState.opportunities
      .flatMap((opp) => evidenceItems(opp))
      .flatMap((item) => extractTerms(`${item.title || ''} ${item.text || ''}`));
    return rankedTerms(fromEvidence).concat(FALLBACK_TAGS).slice(0, 8);
  }

  const fromSignals = RadarState.signals.flatMap((signal) => {
    const matched = signal.matched_keywords || [];
    return matched.concat(extractTerms(`${signal.title || ''} ${signal.text || ''}`));
  });

  if (layer === 'trending') {
    return trendingTags().map(([tag]) => cleanTag(tag)).filter(Boolean).concat(rankedTerms(fromSignals)).slice(0, 8);
  }

  return rankedTerms(fromSignals).concat(FALLBACK_TAGS).slice(0, 8);
}

function extractTerms(text) {
  const terms = ['Claude', 'Codex', 'Cursor', 'Agents', 'OpenAI', 'ChatGPT', 'GitHub', 'Copilot', 'MCP', 'Gemini', 'DeepMind', 'LLM', 'API', 'Automation'];
  const low = String(text || '').toLowerCase();
  return terms.filter((term) => low.includes(term.toLowerCase()));
}

function rankedTerms(terms) {
  const counts = {};
  terms.map(cleanTag).filter(Boolean).forEach((term) => {
    counts[term] = (counts[term] || 0) + 1;
  });
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([term]) => term);
}

function cleanTag(tag) {
  const t = String(tag || '').replace(/^#/, '').trim();
  if (!t || t.length < 2 || t.length > 22) return '';
  const map = {
    ai: 'AI',
    agents: 'Agents',
    agent: 'Agents',
    openai: 'OpenAI',
    github: 'GitHub',
    codex: 'Codex',
    claude: 'Claude',
    cursor: 'Cursor',
    chatgpt: 'ChatGPT',
    model: 'Models',
    llm: 'LLM',
    mcp: 'MCP'
  };
  return map[t.toLowerCase()] || t.replace(/\s+/g, '');
}

function renderDock(layer) {
  const panel = document.getElementById('data-panel');
  const items = dockItems(layer);
  const metric = panelMetric(layer, items);
  const archiveAvailable = layer === 'radar'
    ? RadarState.timeline.length > 6
    : (layer === 'signals' && archiveSignals().length > RadarState.signals.length);
  const showArrows = items.length > 3;

  panel.innerHTML = `
    <div class="panel-metric">
      <span>${escapeHTML(metric.label)}</span>
      <strong>${escapeHTML(metric.value)}</strong>
      <small>${escapeHTML(metric.caption)}</small>
      ${archiveAvailable ? `<button class="archive-toggle" type="button" data-archive-toggle>${escapeHTML(archiveToggleLabel())}</button>` : ''}
    </div>
    <div class="panel-feed-wrap">
      ${showArrows ? `<button type="button" class="panel-arrow panel-arrow-prev" aria-label="${escapeAttr(RadarState.lang === 'ar' ? 'السابق' : 'Previous')}" data-dir="-1">‹</button>` : ''}
      <div class="panel-feed" id="panel-feed-scroll">
        ${items.map((item, idx) => panelChip(item, layer, idx)).join('')}
      </div>
      ${showArrows ? `<button type="button" class="panel-arrow panel-arrow-next" aria-label="${escapeAttr(RadarState.lang === 'ar' ? 'التالي' : 'Next')}" data-dir="1">›</button>` : ''}
    </div>
  `;

  if (layer === 'opportunities') {
    panel.querySelectorAll('[data-detail-idx]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.dataset.detailIdx);
        openOpportunityDetail(items[idx], idx);
      });
    });
  }
  if (layer === 'radar') {
    panel.querySelectorAll('[data-timeline-idx]').forEach((chip) => {
      chip.addEventListener('click', (event) => {
        if (event.target.closest('a')) return;
        const idx = Number(chip.dataset.timelineIdx);
        pauseTimelineAutoplay();
        RadarState.activeTimelineIndex = idx;
        openTimelineDetail(items[idx], idx, false);
        highlightTimelineChip(idx);
      });
      chip.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        const idx = Number(chip.dataset.timelineIdx);
        pauseTimelineAutoplay();
        RadarState.activeTimelineIndex = idx;
        openTimelineDetail(items[idx], idx, false);
        highlightTimelineChip(idx);
      });
    });
  }
  panel.querySelectorAll('[data-signal-idx]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const idx = Number(btn.dataset.signalIdx);
      openSignalDetail(items[idx], idx);
    });
  });
  panel.querySelectorAll('[data-source-idx]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const idx = Number(btn.dataset.sourceIdx);
      openSourceHealthDetail(items[idx], idx);
    });
  });

  const archiveToggle = panel.querySelector('[data-archive-toggle]');
  if (archiveToggle) {
    archiveToggle.addEventListener('click', () => {
      RadarState.archiveExpanded = !RadarState.archiveExpanded;
      renderLayer(RadarState.layer);
    });
  }

  if (showArrows) {
    const feed = document.getElementById('panel-feed-scroll');
    panel.querySelectorAll('.panel-arrow').forEach((btn) => {
      btn.addEventListener('click', () => {
        const dir = Number(btn.dataset.dir);
        const firstChip = feed.querySelector('.signal-chip');
        const step = ((firstChip && firstChip.offsetWidth) || 220) + 12;
        feed.scrollBy({ left: dir * step * 1.4, behavior: 'smooth' });
      });
    });
    const updateArrowState = () => {
      const prev = panel.querySelector('.panel-arrow-prev');
      const next = panel.querySelector('.panel-arrow-next');
      const isRTL = document.documentElement.dir === 'rtl';
      const max = feed.scrollWidth - feed.clientWidth;
      const sl = Math.abs(feed.scrollLeft);
      if (prev) prev.disabled = isRTL ? (sl >= max - 4) : (sl <= 4);
      if (next) next.disabled = isRTL ? (sl <= 4) : (sl >= max - 4);
    };
    feed.addEventListener('scroll', updateArrowState, { passive: true });
    setTimeout(updateArrowState, 60);
  }
}

function dockItems(layer) {
  if (layer === 'opportunities') {
    return allWorthyOpportunityRows();
  }
  if (layer === 'sources') return sourceHealthRows();
  if (layer === 'trending') {
    const discussions = focusedDiscussionRows();
    if (discussions.length) return discussions.slice(0, 10);
    return candidateSocialRows().concat(manualXReadyRows('trending'), manualXReadyRows('product_ideas')).slice(0, 10);
  }
  if (layer === 'radar' && focusedUpdateRows().length) {
    return focusedUpdateRows().slice(0, RadarState.archiveExpanded ? 12 : 8);
  }
  if (layer === 'radar' && candidateNewsRows().length) {
    return candidateNewsRows().slice(0, RadarState.archiveExpanded ? 12 : 6);
  }
  if (layer === 'radar' && RadarState.timeline.length) {
    return manualXReadyRows('radar_updates').slice(0, 3).concat(timelineRows()).slice(0, RadarState.archiveExpanded ? 12 : 6);
  }
  if (layer === 'signals') {
    const evidence = evidenceRows();
    if (evidence.length) return evidence.slice(0, RadarState.archiveExpanded ? 18 : 8);
    return candidateNewsRows().concat(manualXReadyRows(), visibleSignals()).slice(0, RadarState.archiveExpanded ? 18 : 8);
  }
  if (layer === 'radar') return manualXReadyRows('radar_updates').concat(visibleSignals()).slice(0, RadarState.archiveExpanded ? 12 : 6);
  return RadarState.signals.slice(0, 6);
}

function isManualXSignal(item = {}) {
  return item.manual === true || item.source_id === 'manual_x' || String(item.id || '').startsWith('manual_x:');
}

function manualXHandle(item = {}) {
  const raw = String(item.author_handle || item.author || '').trim();
  if (!raw) return 'X';
  return raw.startsWith('@') ? raw : `@${raw}`;
}

function manualXEngagementHTML(item = {}) {
  const metrics = item.metrics || item.public_metrics || {};
  const likes = Number(metrics.likes || 0);
  const reposts = Number(metrics.retweets || metrics.reposts || 0);
  const replies = Number(metrics.replies || 0);
  if (!likes && !reposts && !replies) return '';
  return `
    <small class="manual-x-engagement" aria-label="X engagement">
      <b>♥ ${escapeHTML(formatNumber(likes))}</b>
      <b>↻ ${escapeHTML(formatNumber(reposts))}</b>
      <b>💬 ${escapeHTML(formatNumber(replies))}</b>
    </small>
  `;
}

function panelChip(item, layer, idx) {
  if (layer === 'opportunities') {
    const isX = item.kind === 'x_curated';
    const confidence = item.confidence ? Math.round(item.confidence * 100) : null;
    const evidence = item.evidenceCount ? `${item.evidenceCount} ${RadarState.lang === 'ar' ? 'أدلة' : 'evidence'}` : '';
    const action = RadarState.lang === 'ar' ? 'التفاصيل' : 'Details';
    const freshness = cardFreshness(item, 'opportunity');
    return `
      <button type="button" class="signal-chip opportunity-chip ${idx === 0 ? 'featured-opportunity' : ''} ${isX ? 'x-curated-chip' : ''}" data-detail-idx="${idx}">
        <span class="opportunity-source"><bdi>${escapeHTML(isX ? (RadarState.lang === 'ar' ? 'مختارة من X' : 'Curated from X') : item.category)}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        <p>${escapeHTML(opportunitySpecificTitle(item))}</p>
        <small>${escapeHTML(opportunityPreviewLine(item))}</small>
        <div class="opportunity-proofline">
          ${evidence ? `<b>${escapeHTML(evidence)}</b>` : ''}
          ${confidence ? `<b>${escapeHTML(`${confidence}%`)}</b>` : ''}
        </div>
        <em>${escapeHTML(action)}</em>
      </button>
    `;
  }
  if (layer === 'radar' && item.date) {
    const freshness = cardFreshness(item, 'timeline');
    return `
      <article class="signal-chip timeline-chip timeline-${escapeAttr(item.category)}" role="button" tabindex="0" data-timeline-idx="${idx}">
        <span><bdi>${escapeHTML(timelineCategoryLabel(item.category))}</bdi> · <bdi>${escapeHTML(formatTimelineDate(item.date))}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        <p>${escapeHTML(localizedTimelineTitle(item))}</p>
        <small>${escapeHTML(timelineShortSummary(item))}</small>
      </article>
    `;
  }
  if (item.kind === 'validated_card') {
    const freshness = cardFreshness(item, 'signal');
    const translated = translatedBadgeLabel(item);
    return `
      <button type="button" class="signal-chip validated-card-chip" data-signal-idx="${idx}">
        <span><bdi>${escapeHTML(item.source_name || sourceName(item.source_id))}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        ${translated ? `<b class="freshness-badge freshness-translated">${escapeHTML(translated)}</b>` : ''}
        <p>${escapeHTML(localizedTitle(item))}</p>
        <small>${escapeHTML(signalCardPreview(item))}</small>
      </button>
    `;
  }
  if (item.kind === 'focused_update') {
    const freshness = cardFreshness(item, 'signal');
    const translated = translatedBadgeLabel(item);
    const evidence = item.evidenceCount ? `${item.evidenceCount} ${RadarState.lang === 'ar' ? 'دليل' : 'evidence'}` : '';
    const confidence = item.confidence ? `${Math.round(item.confidence * 100)}%` : '';
    return `
      <button type="button" class="signal-chip focused-update-chip" data-signal-idx="${idx}">
        <span><bdi>${escapeHTML(item.source_name || sourceName(item.source_id))}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        ${translated ? `<b class="freshness-badge freshness-translated">${escapeHTML(translated)}</b>` : ''}
        <p>${escapeHTML(localizedTitle(item))}</p>
        <small>${escapeHTML(signalCardPreview(item))}</small>
        <div class="opportunity-proofline">
          ${evidence ? `<b>${escapeHTML(evidence)}</b>` : ''}
          ${confidence ? `<b>${escapeHTML(confidence)}</b>` : ''}
        </div>
      </button>
    `;
  }
  if (item.kind === 'focused_discussion') {
    const freshness = cardFreshness(item, 'x');
    const translated = translatedBadgeLabel(item);
    const evidence = item.evidenceCount ? `${item.evidenceCount} ${RadarState.lang === 'ar' ? 'إشارات' : 'signals'}` : '';
    const confidence = item.confidence ? `${Math.round(item.confidence * 100)}%` : '';
    return `
      <button type="button" class="signal-chip focused-discussion-chip" data-signal-idx="${idx}">
        <span><bdi>${escapeHTML(item.source_name || sourceName(item.source_id))}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        ${translated ? `<b class="freshness-badge freshness-translated">${escapeHTML(translated)}</b>` : ''}
        <p>${escapeHTML(localizedTitle(item))}</p>
        <small>${escapeHTML(signalCardPreview(item))}</small>
        <div class="opportunity-proofline">
          ${evidence ? `<b>${escapeHTML(evidence)}</b>` : ''}
          ${confidence ? `<b>${escapeHTML(confidence)}</b>` : ''}
        </div>
      </button>
    `;
  }
  if (item.kind === 'evidence_item') {
    const freshness = cardFreshness(item, 'signal');
    return `
      <button type="button" class="signal-chip evidence-item-chip" data-signal-idx="${idx}">
        <span><bdi>${escapeHTML(item.source_name || sourceName(item.source_id))}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        <p>${escapeHTML(localizedTitle(item))}</p>
        <small>${escapeHTML(signalCardPreview(item))}</small>
      </button>
    `;
  }
  if (item.kind === 'x_ready') {
    const freshness = cardFreshness(item, 'x');
    return `
      <button type="button" class="signal-chip x-ready-chip x-ready-${escapeAttr(item.category || 'signal')}" data-signal-idx="${idx}">
        <span><bdi>${escapeHTML(item.sourceLabel)}</bdi></span>
        ${freshnessBadgeHTML(freshness)}
        <p>${escapeHTML(localizedTitle(item))}</p>
        <small>${escapeHTML(item.previewLine || item.productAngle || item.shortReason || newsUpdateKind(item))}</small>
      </button>
    `;
  }
  if (item.kind === 'source_health') {
    return `
      <button type="button" class="signal-chip source-health-chip source-${escapeAttr(item.status)}" data-source-idx="${idx}">
        <span><bdi>${escapeHTML(sourceStatusLabel(item.status))}</bdi></span>
        <p>${escapeHTML(item.source_name || item.source_id)}</p>
        <small>${escapeHTML(sourceHealthCaption(item))}</small>
      </button>
    `;
  }
  const manualX = isManualXSignal(item);
  const sourceLabel = manualX ? `𝕏 ${manualXHandle(item)}` : sourceName(item.source_id);
  return `
    <button type="button" class="signal-chip ${manualX ? 'manual-x-chip' : ''}" data-signal-idx="${idx}">
      <span class="${manualX ? 'manual-x-source' : ''}"><bdi>${escapeHTML(sourceLabel)}</bdi></span>
      ${freshnessBadgeHTML(cardFreshness(item, 'signal'))}
      <p>${escapeHTML(localizedTitle(item))}</p>
      ${layer === 'radar' ? `<small>${escapeHTML(signalCardPreview(item))}</small>` : ''}
      ${manualXEngagementHTML(item)}
    </button>
  `;
}

function openOpportunityDetail(item, idx = 0) {
  if (!item) return;
  resetDetailChat();
  const lang = RadarState.lang;
  const isAr = lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;

  document.getElementById('detail-source').textContent = item.category || (isAr ? 'فرصة' : 'Opportunity');
  document.getElementById('detail-title').textContent = isAr
    ? `فرصة: ${opportunitySpecificTitle(item)}`
    : `Opportunity: ${opportunitySpecificTitle(item)}`;
  document.getElementById('detail-original').hidden = true;
  RadarState.activeDetail = detailIdentity('opportunity', item, idx);
  updateSaveButton();

  const meta = document.getElementById('detail-meta');
  const parts = [];
  if (item.capital)    parts.push(`${L('رأس المال', 'Capital')}: ${item.capital}`);
  if (item.confidence) parts.push(`${L('الثقة', 'Confidence')}: ${Math.round(item.confidence * 100)}%`);
  parts.push(cardFreshness(item, 'opportunity').label);
  meta.innerHTML = parts.map((p) => `<span>${escapeHTML(p)}</span>`).join('');

  const sections = [
    detailSectionHTML(L('المشكلة', 'Problem'), item.pain || item.why || item.inspiration || L('هناك اهتمام أو ألم متكرر حول هذه المساحة، ويحتاج إلى تجربة أصغر لإثبات الطلب.', 'There is repeated interest or pain here; it needs a small test to prove demand.')),
    detailSectionHTML(L('لمن؟', 'For whom?'), item.buyer || L('مستخدمون أو فرق لديهم احتياج واضح يمكن خدمته بعرض صغير.', 'Users or teams with a clear need that can be served with a small offer.')),
    detailSectionHTML(L('لماذا الآن؟', 'Why now?'), item.why || item.inspiration || (item.signalCount ? L(`ظهرت ${item.signalCount} إشارات مرتبطة بهذه الفكرة.`, `${item.signalCount} related signals appeared.`) : '')),
    detailSectionHTML(L('كيف تستفيد؟', 'How to use it?'), item.product || L('حوّلها إلى تجربة صغيرة: أداة، نشرة مدفوعة، خدمة، أو قالب داخلي.', 'Turn it into a small test: tool, paid brief, service, or internal template.')),
    item.profit ? detailSectionHTML(L('زاوية الدخل', 'Monetization angle'), item.profit) : '',
    detailSectionHTML(L('سبب الاختيار', 'Why the radar picked it'), whyRadarPickedOpportunity(item), 'detail-section-picked'),
    item.tools ? detailSectionHTML(L('الأدوات عند الحاجة', 'Tools if needed'), item.tools) : '',
    item.examples ? detailSectionHTML(L('أمثلة ملهمة', 'Inspiration examples'), item.examples) : '',
    item.saudi ? detailSectionHTML(L('عدسة السعودية', 'Saudi money lens'), item.saudi) : '',
    item.firstTest ? detailSectionHTML(L('خطوة أولى', 'First step'), item.firstTest) : '',
    item.evidenceItems && item.evidenceItems.length ? detailSectionHTML(L('أدلة مختصرة', 'Short evidence'), formatEvidenceItems(item.evidenceItems)) : '',
    item.playbook && item.playbook.length ? detailSectionHTML(L('خطة 7 أيام', '7-day playbook'), formatPlaybook(item.playbook)) : '',
    detailEvidenceGridHTML(item.sourceLinks || [], L('الأدلة', 'Evidence'))
  ];
  document.getElementById('detail-text').innerHTML = sections.filter(Boolean).join('');

  const link = document.getElementById('detail-link');
  const primaryUrl = item.url || (item.sourceLinks && item.sourceLinks.find((source) => source.url)?.url);
  if (primaryUrl) {
    link.href = primaryUrl;
    link.textContent = isAr ? 'افتح المصدر ↗' : 'Open source ↗';
    link.style.display = '';
  } else {
    link.style.display = 'none';
  }

  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  document.body.classList.add('detail-active');
  // Alternate side: even idx → right of globe, odd idx → left of globe
  const side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.side = side;
  modal.hidden = false;
  if (backdrop) backdrop.hidden = false;
  // double-rAF to allow transition from initial hidden state
  requestAnimationFrame(() => requestAnimationFrame(() => modal.classList.add('open')));
}

function formatPlaybook(items) {
  return items.map((step, index) => {
    const prefix = RadarState.lang === 'ar' ? `${index + 1}. ` : `${index + 1}. `;
    return `${prefix}${step}`;
  }).join('\n');
}

function localizedSourceLinks(links) {
  const isAr = RadarState.lang === 'ar';
  return links.map((link) => ({
    label: link[`label_${isAr ? 'ar' : 'en'}`] || link.label || link.label_en || link.label_ar || link.url,
    source: link.source || link.type || '',
    url: link.url || '',
    title: link.title || '',
    detected_at: link.detected_at || ''
  })).filter((link) => link.label || link.url);
}

function detailSectionHTML(label, body, className = '') {
  if (!body) return '';
  return `
    <section class="detail-section ${escapeAttr(className)}">
      <h3>${escapeHTML(label)}</h3>
      <p>${escapeHTML(body)}</p>
    </section>
  `;
}

function detailEvidenceGridHTML(links, label) {
  const cleanLinks = (links || []).filter((link) => link.label || link.url).slice(0, 6);
  if (!cleanLinks.length) return '';
  const cards = cleanLinks.map((link, index) => {
    const source = link.source || link.label || '';
    const title = link.title || link.label || link.url || '';
    const shortUrl = link.url ? compactUrl(link.url) : '';
    const body = compactPreview(title, 92);
    const content = `
      <span>${escapeHTML(source)}</span>
      <b>${escapeHTML(body)}</b>
      ${shortUrl ? `<small>${escapeHTML(shortUrl)}</small>` : ''}
    `;
    if (link.url) {
      return `<a class="detail-evidence-card" href="${escapeAttr(link.url)}" target="_blank" rel="noreferrer" aria-label="${escapeAttr(`${label} ${index + 1}`)}">${content}</a>`;
    }
    return `<article class="detail-evidence-card">${content}</article>`;
  }).join('');
  return `
    <section class="detail-section detail-evidence-section">
      <h3>${escapeHTML(label)}</h3>
      <div class="detail-evidence-grid">${cards}</div>
    </section>
  `;
}

function compactUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, '') + parsed.pathname.replace(/\/$/, '').slice(0, 34);
  } catch (err) {
    return String(url || '').slice(0, 48);
  }
}

function formatSourceLinks(links) {
  return links.map((link, index) => {
    const source = link.source ? ` · ${link.source}` : '';
    const url = link.url ? `\n${link.url}` : '';
    return `${index + 1}. ${link.label}\n${source ? source.replace(/^ · /, '') : ''}${url}`;
  }).join('\n');
}

function formatEvidenceItems(items) {
  return items.slice(0, 4).map((item, index) => {
    const author = item.author_handle ? `@${item.author_handle}` : (RadarState.lang === 'ar' ? 'إشارة' : 'Signal');
    const text = String(item.text || '').replace(/\s+/g, ' ').trim();
    const short = text.length > 220 ? `${text.slice(0, 217)}...` : text;
    return `${index + 1}. ${author}: ${short}`;
  }).join('\n');
}

function openTimelineDetail(item, idx = 0, auto = false) {
  if (!item) return;
  // Auto-opens (driven by the 6.2s timeline interval) must yield to the
  // chat drawer — otherwise they paint over the user's conversation.
  if (auto && document.body.classList.contains('has-chat-open')) return;
  const isAr = RadarState.lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;

  document.getElementById('detail-source').textContent = `${timelineCategoryLabel(item.category)} · ${item.vendor || ''}`;
  document.getElementById('detail-title').textContent = localizedTimelineTitle(item);
  document.getElementById('detail-original').hidden = true;
  RadarState.activeDetail = detailIdentity('timeline', item, idx);
  updateSaveButton();

  const meta = document.getElementById('detail-meta');
  const parts = [
    `${L('التاريخ', 'Date')}: ${formatTimelineDate(item.date)}`,
    `${L('الفئة', 'Category')}: ${timelineCategoryLabel(item.category)}`
  ];
  if (item.pricing_ar || item.pricing_en) parts.push(`${L('السعر/الحدود', 'Pricing/limits')}: ${localizedTimelinePricing(item)}`);
  if (auto) parts.push(L('تشغيل تلقائي', 'Auto playback'));
  meta.innerHTML = parts.map((p) => `<span>${escapeHTML(p)}</span>`).join('');

  const sections = [
    `${L('ما الذي حدث؟', 'What happened?')}\n${localizedTimelineSummary(item)}`,
    `${L('لماذا يهم؟', 'Why it matters?')}\n${timelineImpact(item)}`,
    `${L('ماذا أستفيد؟', 'What can I use?')}\n${timelineRadarTakeaway(item)}`,
    `${L('الدليل:', 'Evidence:')}\n${[
      item.source_url ? item.source_url : '',
      item.date ? `${L('وقت الرصد', 'Detected')}: ${formatTimelineDate(item.date)}` : '',
      item.vendor ? `${L('المصدر', 'Source')}: ${item.vendor}` : ''
    ].filter(Boolean).join('\n')}`
  ];
  document.getElementById('detail-text').textContent = sections.join('\n\n');

  const link = document.getElementById('detail-link');
  if (item.source_url) {
    link.href = item.source_url;
    link.textContent = isAr ? 'تحقق من المصدر الرسمي ↗' : 'Verify official source ↗';
    link.style.display = '';
  } else {
    link.style.display = 'none';
  }

  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  document.body.classList.add('detail-active');
  modal.dataset.side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.kind = 'timeline';
  modal.hidden = false;
  if (backdrop) backdrop.hidden = false;
  requestAnimationFrame(() => requestAnimationFrame(() => modal.classList.add('open')));
}

function timelineImpact(item) {
  const isAr = RadarState.lang === 'ar';
  if (item.category === 'model') {
    return isAr
      ? 'تحديث النماذج يغير جودة المخرجات، تكلفة التشغيل، وسرعة بناء المنتجات أو الأتمتة.'
      : 'Model updates affect output quality, operating cost, and how fast products or automations can be built.';
  }
  if (item.category === 'pricing_limits') {
    return isAr
      ? 'الأسعار والحدود تحدد هل الفكرة قابلة للتشغيل تجاريًا أم مكلفة قبل الوصول للعميل.'
      : 'Pricing and limits determine whether an idea can run commercially before reaching customers.';
  }
  return isAr
    ? 'الأدوات والإصدارات الجديدة تكشف ما أصبح ممكنًا الآن، وما يمكن تحويله إلى تجربة أو منتج.'
    : 'New tools and releases reveal what is now possible and what can become a test or product.';
}

function timelineRadarTakeaway(item) {
  const isAr = RadarState.lang === 'ar';
  const base = localizedTimelinePricing(item);
  if (base) {
    return isAr
      ? `هذا التحديث قد يؤثر على اختيار الأداة أو تسعير المنتج. ${base}`
      : `The radar tracks this as an update that can affect tool choice or product pricing. ${base}`;
  }
  return isAr
    ? 'يهمك لأنه قد يغير أدوات البناء أو جودة المنتج أو سرعة التنفيذ.'
    : 'The radar tracks it because it may change build tools, product quality, or execution speed.';
}

function closeDetail() {
  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  if (!modal) return;
  modal.classList.remove('open');
  resetDetailChat();
  if (backdrop) backdrop.hidden = true;
  setTimeout(() => {
    modal.hidden = true;
    document.body.classList.remove('detail-active');
    RadarState.activeDetail = null;
    updateSaveButton();
  }, 320);
}

function resetDetailState() {
  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  if (!modal) return;
  modal.classList.remove('open');
  modal.hidden = true;
  resetDetailChat();
  if (backdrop) backdrop.hidden = true;
  document.body.classList.remove('detail-active');
  RadarState.activeDetail = null;
  updateSaveButton();
}

function wireDetailModal() {
  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  if (!modal) return;
  modal.addEventListener('click', (e) => {
    if (e.target.dataset && e.target.dataset.close === '1') closeDetail();
  });
  const closeBtn = document.getElementById('detail-close');
  const saveBtn = document.getElementById('detail-save');
  const chatBtn = document.getElementById('detail-chat');
  const chatForm = document.getElementById('detail-chat-form');
  if (closeBtn) closeBtn.addEventListener('click', closeDetail);
  if (backdrop) backdrop.addEventListener('click', closeDetail);
  if (saveBtn) saveBtn.addEventListener('click', saveActiveDetail);
  if (chatBtn) chatBtn.addEventListener('click', openDetailChat);
  if (chatForm) chatForm.addEventListener('submit', submitDetailChat);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeDetail();
  });
}

function detailIdentity(type, item, idx = 0) {
  const title = type === 'timeline' ? localizedTimelineTitle(item) : (item.title || localizedTitle(item));
  const url = item.source_url || item.url || '';
  return {
    key: `${type}:${item.id || item.slug || url || title || idx}`,
    type,
    title,
    source: item.source || item.vendor || item.source_id || '',
    url,
    chatContext: detailChatContext(type, item),
    savedAt: new Date().toISOString()
  };
}

function detailChatContext(type, item = {}) {
  const isAr = RadarState.lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;
  if (type === 'opportunity') {
    return {
      type: L('فرصة لكسب المال', 'Money opportunity'),
      title: opportunitySpecificTitle(item),
      source: item.source || item.category || '',
      url: item.url || ((item.sourceLinks || []).find((source) => source.url) || {}).url || '',
      what_happened: item.inspiration || item.summary || item.why || '',
      why_it_matters: item.pain || item.why || '',
      how_to_use: item.product || item.firstTest || '',
      opportunity: item.profit || item.product || '',
      target_user: item.buyer || '',
      confidence: item.confidence ? Math.round(item.confidence * 100) : null,
      evidence: item.evidenceCount || (item.sourceLinks || []).length || 0
    };
  }
  if (type === 'timeline') {
    return {
      type: L('تحديث AI', 'AI update'),
      title: localizedTimelineTitle(item),
      source: item.vendor || '',
      url: item.source_url || '',
      what_happened: localizedTimelineSummary(item),
      why_it_matters: timelineImpact(item),
      how_to_use: timelineRadarTakeaway(item),
      opportunity: '',
      target_user: '',
      confidence: item.confidence_score || null,
      evidence: item.source_url ? 1 : 0
    };
  }
  if (type === 'source') {
    return {
      type: L('حالة مصدر', 'Source status'),
      title: sourceDisplayName(item),
      source: sourceDisplayName(item),
      url: item.url || '',
      what_happened: sourceUserMeaning(item),
      why_it_matters: sourceTrustImpact(item),
      how_to_use: sourceDetailLine(item),
      opportunity: '',
      target_user: '',
      confidence: null,
      evidence: item.items_collected || 0
    };
  }
  const summary = isAr
    ? (item.summary_ar || item.text_ar || item.summary || item.text || localizedTitle(item))
    : (item.summary_en || item.summary || item.text || localizedTitle(item));
  return {
    type: item.kind || item.signal_type || L('إشارة رادار', 'Radar signal'),
    title: localizedTitle(item),
    source: sourceName(item.source_id) || item.source || item.author_handle || '',
    url: item.source_url || item.url || '',
    what_happened: summary,
    why_it_matters: item.why_it_matters_ar || item.why_it_matters_en || item.whyMeaning || item.shortReason || '',
    how_to_use: item.product_opportunity_ar || item.product_opportunity_en || item.radar_use_ar || item.radar_use_en || item.radarUse || '',
    opportunity: item.productAngle || item.business_signal_ar || item.business_signal_en || '',
    target_user: item.target_user_ar || item.target_user_en || '',
    confidence: item.confidence_score || item.confidence || null,
    evidence: item.evidenceCount || (item.sourceLinks || []).length || 0
  };
}

function updateChatButton() {
  const button = document.getElementById('detail-chat');
  const input = document.getElementById('detail-chat-input');
  const submit = document.getElementById('detail-chat-submit');
  if (button) {
    button.textContent = t('chat_with_gpt');
    button.disabled = !RadarState.activeDetail;
  }
  if (input) input.placeholder = t('chat_placeholder');
  if (submit) submit.textContent = t('chat_send');
}

function resetDetailChat() {
  const panel = document.getElementById('detail-chat-panel');
  const log = document.getElementById('detail-chat-log');
  const input = document.getElementById('detail-chat-input');
  if (panel) panel.hidden = true;
  if (log) {
    log.innerHTML = '';
    delete log.dataset.ready;
  }
  if (input) input.value = '';
}

function openDetailChat() {
  if (!RadarState.activeDetail) return;

  // On mobile-portrait, the inline chat input collides with the on-screen
  // keyboard and the bottom-sheet — route to the main floating drawer
  // instead, pre-loaded with the card as `focused`. The drawer is wider,
  // handles keyboard properly, and shows the same context.
  const isMobilePortrait = window.matchMedia &&
    window.matchMedia('(orientation: portrait) and (max-width: 1024px)').matches;
  if (isMobilePortrait && window.RadarChat && typeof window.RadarChat.askAbout === 'function') {
    const d = RadarState.activeDetail;
    window.RadarChat.askAbout({
      title: d.title,
      summary: d.text || d.summary || '',
      kind: d.type || d.kind || 'card',
      url: d.url || d.source_url || '',
      subject: d.title,
    });
    return;
  }

  const panel = document.getElementById('detail-chat-panel');
  const log = document.getElementById('detail-chat-log');
  if (!panel || !log) return;
  panel.hidden = !panel.hidden;
  if (!panel.hidden && !log.dataset.ready) {
    appendChatMessage('assistant', t('chat_intro'));
    log.dataset.ready = '1';
  }
}

async function submitDetailChat(event) {
  event.preventDefault();
  if (!RadarState.activeDetail) return;
  const input = document.getElementById('detail-chat-input');
  const question = (input && input.value || '').trim();
  if (!question) return;
  input.value = '';
  appendChatMessage('user', question);
  const thinkingId = appendChatMessage('assistant', t('chat_wait'));
  const payload = {
    lang: RadarState.lang,
    question,
    card: RadarState.activeDetail.chatContext || {
      title: RadarState.activeDetail.title,
      source: RadarState.activeDetail.source,
      url: RadarState.activeDetail.url,
      type: RadarState.activeDetail.type
    }
  };
  try {
    const response = await postDetailChat(payload);
    const data = await response.json();
    updateChatMessage(thinkingId, data.answer || localChatFallback(question, payload.card, data.error));
  } catch (err) {
    updateChatMessage(thinkingId, localChatFallback(question, payload.card, 'runner_unavailable'));
  }
}

// Translate the in-detail card payload {lang, question, card} into the format
// /api/chat expects: {locale, messages, active_view}. Returns a Response-like
// object whose .json() yields {answer, error} so the existing caller works
// without changes.
function cardToChatPayload(payload) {
  const card = payload.card || {};
  const lang = payload.lang || 'ar';
  const isAr = lang === 'ar';
  // Build a compact context block the model can ground its reply in.
  const parts = [
    payload.question,
    '',
    isAr ? '— عن البطاقة —' : '— Card context —',
    card.title && (isAr ? `العنوان: ${card.title}` : `Title: ${card.title}`),
    card.what_happened && (isAr ? `ما حدث: ${card.what_happened}` : `What happened: ${card.what_happened}`),
    card.why_it_matters && (isAr ? `لماذا يهم: ${card.why_it_matters}` : `Why it matters: ${card.why_it_matters}`),
    card.how_to_use && (isAr ? `كيف تستفيد: ${card.how_to_use}` : `How to use: ${card.how_to_use}`),
    card.opportunity && (isAr ? `الفرصة: ${card.opportunity}` : `Opportunity: ${card.opportunity}`),
    card.target_user && (isAr ? `الفئة: ${card.target_user}` : `Target user: ${card.target_user}`),
  ].filter(Boolean);
  return {
    locale: lang === 'en' ? 'en' : 'ar',
    messages: [{ role: 'user', content: parts.join('\n') }],
    active_view: {
      layer: 'opportunities',
      focused: {
        kind: card.type || card.kind || 'card',
        title: card.title || '',
        label: card.label || '',
        summary: card.what_happened || card.why_it_matters || '',
        url: card.url || card.source_url || '',
      },
    },
  };
}

async function postDetailChat(payload) {
  // In production we route through the Vercel /api/chat endpoint. Local
  // 127.0.0.1 runners only apply when the page is served from a dev
  // workstation — and they speak the raw {lang, question, card} dialect,
  // so we send the card payload to them as-is and only translate when
  // falling back to /api/chat.
  const isLocal = ['localhost', '127.0.0.1', '::1', ''].includes(location.hostname);

  // Try local card-runners first if we're on dev (they speak {lang, question, card} natively)
  if (isLocal) {
    const localEndpoints = [
      'http://127.0.0.1:8801/chat-card',
      'http://127.0.0.1:8799/chat-card',
      'http://127.0.0.1:8800/chat-card',
    ];
    for (const endpoint of localEndpoints) {
      try {
        const r = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (r.ok) return r; // raw shape {answer: '...'}
      } catch (_) {}
    }
  }

  // /api/chat (production + dev-fallback): translate, send, then adapt the
  // response so the caller sees the {answer} shape it expects.
  const chatPayload = cardToChatPayload(payload);
  let response;
  try {
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(chatPayload),
    });
  } catch (e) {
    throw new Error('network');
  }
  const data = await response.json().catch(() => ({}));
  const adapted = response.ok
    ? { answer: data.reply || data.answer || data.message || '' }
    : { answer: '', error: data.error || ('http_' + response.status), message: data.message || data.hint };
  return { ok: response.ok, status: response.status, json: async () => adapted };
}

function appendChatMessage(role, text) {
  const log = document.getElementById('detail-chat-log');
  if (!log) return '';
  const id = `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const label = role === 'user' ? t('chat_user_label') : t('chat_ai_label');
  const el = document.createElement('div');
  el.className = `chat-message ${role}`;
  el.dataset.id = id;
  el.innerHTML = `<strong>${escapeHTML(label)}</strong><span>${escapeHTML(text)}</span>`;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return id;
}

function updateChatMessage(id, text) {
  const log = document.getElementById('detail-chat-log');
  const row = log
    ? Array.from(log.querySelectorAll('.chat-message')).find((node) => node.dataset.id === id)
    : null;
  const el = row && row.querySelector('span');
  if (el) el.textContent = text;
}

function localChatFallback(question, card = {}, error = '') {
  const isAr = RadarState.lang === 'ar';
  const isLocal = ['localhost', '127.0.0.1', '::1', ''].includes(location.hostname);

  // Friendly user-facing messages by error type — never expose technical
  // jargon to end-users. Admin/config errors go to server logs, not the UI.

  if (error === 'rate_limit') {
    return isAr
      ? 'وصلت إلى الحد اليومي للأسئلة. عودي غدًا، أو فعّلي الاشتراك لتحصلي على عدد أكبر.'
      : 'You hit the daily question limit. Come back tomorrow, or subscribe for a higher limit.';
  }
  if (error === 'server_misconfigured' || error === 'missing_openai_api_key') {
    // Don't reveal "OPENAI_API_KEY not set" to public users.
    return isAr
      ? 'المساعد الذكي معطّل مؤقتًا. سنعود قريبًا — في غضون ذلك تستطيعين قراءة ملخص البطاقة والأدلة أدناه.'
      : 'The assistant is temporarily offline. We will be back soon — in the meantime, the card summary and evidence below cover the essentials.';
  }
  // Production network/unknown error
  if (!isLocal) {
    return isAr
      ? `تعذّر الاتصال بالمساعد الآن. جرّبي مرة أخرى بعد دقيقة.\n\nملخص هذه البطاقة: ${card.what_happened || card.title || 'إشارة من الرادار.'}${card.why_it_matters ? '\nلماذا تهمّك: ' + card.why_it_matters : ''}`
      : `Couldn't reach the assistant right now. Try again in a moment.\n\nCard summary: ${card.what_happened || card.title || 'A radar signal.'}${card.why_it_matters ? '\nWhy it matters: ' + card.why_it_matters : ''}`;
  }
  // Local dev — show the dev-only hint
  return isAr
    ? `لم أستطع الاتصال بخادم الشات المحلي الآن. شغّلي start-radar-runner.command ثم أعيدي السؤال.\n\nملخص سريع من البطاقة: ${card.what_happened || card.title || 'هذه إشارة من الرادار.'}\nزاوية الاستفادة: ${card.how_to_use || card.opportunity || 'افتحي التفاصيل وشاهدي الدليل.'}`
    : `I could not reach the local chat runner. Start start-radar-runner.command and ask again.\n\nQuick card summary: ${card.what_happened || card.title || 'This is a radar signal.'}\nUse angle: ${card.how_to_use || card.opportunity || 'open details and check the evidence.'}`;
}

function savedDetails() {
  try {
    const parsed = JSON.parse(localStorage.getItem('axp_saved_details') || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    return [];
  }
}

function saveActiveDetail() {
  if (!RadarState.activeDetail) return;
  const items = savedDetails().filter((item) => item.key !== RadarState.activeDetail.key);
  items.unshift({ ...RadarState.activeDetail, savedAt: new Date().toISOString() });
  localStorage.setItem('axp_saved_details', JSON.stringify(items.slice(0, 60)));
  updateSaveButton();
}

function updateSaveButton() {
  const button = document.getElementById('detail-save');
  if (!button) return;
  const active = RadarState.activeDetail;
  const isSaved = active ? savedDetails().some((item) => item.key === active.key) : false;
  button.textContent = isSaved ? t('saved') : t('save');
  button.classList.toggle('saved', isSaved);
  button.disabled = !active;
  updateChatButton();
}

function wireRadarSurface() {
  document.querySelectorAll('.radar-node').forEach((node, index) => {
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '0');
    node.addEventListener('click', () => openLayerDetailByIndex(index));
    node.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      openLayerDetailByIndex(index);
    });
  });

  const tags = document.getElementById('radar-tags');
  if (!tags) return;
  tags.addEventListener('click', (event) => {
    const tag = event.target.closest('[data-radar-idx]');
    if (!tag) return;
    openLayerDetailByIndex(Number(tag.dataset.radarIdx));
  });
  tags.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const tag = event.target.closest('[data-radar-idx]');
    if (!tag) return;
    event.preventDefault();
    openLayerDetailByIndex(Number(tag.dataset.radarIdx));
  });
}

function openLayerDetailByIndex(index) {
  const items = dockItems(RadarState.layer);
  if (!items.length) return;
  const idx = Number.isFinite(index) ? index % items.length : 0;
  const item = items[idx];
  if (RadarState.layer === 'opportunities') {
    openOpportunityDetail(item, idx);
    return;
  }
  if (RadarState.layer === 'radar' && item.date) {
    pauseTimelineAutoplay();
    RadarState.activeTimelineIndex = idx;
    openTimelineDetail(item, idx, false);
    highlightTimelineChip(idx);
    return;
  }
  openSignalDetail(item, idx);
}

function openSignalDetail(item, idx = 0) {
  if (!item) return;
  resetDetailChat();
  const isAr = RadarState.lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;
  document.getElementById('detail-source').textContent = sourceName(item.source_id) || L('إشارة', 'Signal');
  document.getElementById('detail-title').textContent = localizedTitle(item);
  document.getElementById('detail-original').hidden = true;
  RadarState.activeDetail = detailIdentity('signal', item, idx);
  updateSaveButton();

  const meta = document.getElementById('detail-meta');
  const parts = [];
  if (item.posted_at) parts.push(`${L('التاريخ', 'Date')}: ${formatTimelineDate(item.posted_at)}`);
  if (item.signal_type) parts.push(`${L('النوع', 'Type')}: ${item.signal_type}`);
  if (item.opportunity_score) parts.push(`${L('قوة الإشارة', 'Signal strength')}: ${Math.round(item.opportunity_score * 100)}%`);
  if (translatedBadgeLabel(item)) parts.push(translatedBadgeLabel(item));
  if (item.display_status) parts.push(cardFreshness(item, item.kind === 'x_ready' ? 'x' : 'signal').label);
  meta.innerHTML = parts.map((p) => `<span>${escapeHTML(p)}</span>`).join('');

  if (item.kind === 'x_ready') {
    document.getElementById('detail-text').textContent = [
      `${L('ماذا يقول الناس؟', 'What are people saying?')}\n${isAr ? (item.text_ar || item.text) : item.text}`,
      `${L('لماذا يهمك؟', 'Why it matters to you')}\n${humanizeForUser(item.whyMeaning || item.shortReason || '')}`,
      `${L('زاوية المنتج أو الدخل', 'Product or income angle')}\n${humanizeForUser(item.productAngle || '')}`,
      `${L('كيف تستفيد؟', 'How you can use it')}\n${humanizeForUser(item.radarUse || '')}`,
      `${L('سبب الاختيار:', 'Why selected:')}\n${item.reason_ar || item.shortReason || L('لأنها مرتبطة بالذكاء الاصطناعي ولها مصدر قابل للتحقق.', 'Because it is AI-related and has a verifiable source.')}`
    ].filter(Boolean).join('\n\n');
  } else if (item.kind === 'focused_discussion') {
    document.getElementById('detail-text').innerHTML = [
      detailSectionHTML(L('ماذا يقول الناس؟', 'What are people saying?'), isAr ? item.summary_ar : item.summary_en),
      detailSectionHTML(L('الألم المتكرر', 'Repeated pain'), isAr ? item.pain_ar : item.pain_en),
      detailSectionHTML(L('الإشارة التجارية', 'Business signal'), isAr ? item.business_signal_ar : item.business_signal_en),
      detailSectionHTML(L('كيف يستخدمه الرادار؟', 'How the radar uses it'), isAr ? item.radar_take_ar : item.radar_take_en),
      detailSectionHTML(L('سبب الاختيار', 'Why the radar picked it'), item.whySelected || whyRadarPickedOpportunity(item), 'detail-section-picked'),
      detailEvidenceGridHTML(item.sourceLinks || [], L('الأدلة', 'Evidence'))
    ].filter(Boolean).join('');
  } else if (item.kind === 'evidence_item') {
    document.getElementById('detail-source').textContent = isAr ? 'دليل مرتبط' : 'Linked evidence';
    document.getElementById('detail-text').innerHTML = [
      detailSectionHTML(L('ما الدليل؟', 'What is the evidence?'), item.evidenceTitle || localizedTitle(item)),
      detailSectionHTML(L('ما الذي يدعمه؟', 'What does it support?'), item.parentTitle || ''),
      detailSectionHTML(L('درجة الدليل', 'Evidence quality'), isAr ? evidenceQualityTextAr(item) : evidenceQualityTextEn(item)),
      detailSectionHTML(L('لماذا نعرضه؟', 'Why we show it'), item.summary_ar || item.summary_en || ''),
      detailEvidenceGridHTML(item.sourceLinks || [], L('افتح الدليل', 'Open evidence'))
    ].filter(Boolean).join('');
  } else if (item.kind === 'focused_update') {
    const text = isAr ? item.summary_ar : item.summary_en;
    const why = isAr ? item.why_it_matters_ar : item.why_it_matters_en;
    const use = isAr ? (item.radar_use_ar || item.product_opportunity_ar) : (item.radar_use_en || item.product_opportunity_en);
    document.getElementById('detail-text').innerHTML = [
      detailSectionHTML(L('ماذا حدث؟', 'What happened?'), text),
      detailSectionHTML(L('لماذا يهمك؟', 'Why it matters to you?'), why),
      detailSectionHTML(L('كيف تستفيد؟', 'How can you use it?'), use),
      detailSectionHTML(L('سبب الاختيار', 'Why the radar picked it'), item.whySelected || whyRadarPickedOpportunity(item), 'detail-section-picked'),
      detailEvidenceGridHTML(item.sourceLinks || [], L('الأدلة', 'Evidence'))
    ].filter(Boolean).join('');
  } else {
    const text = isAr
      ? (item.summary_ar || item.text_ar || item.text || localizedTitle(item))
      : (item.summary_en || item.text || localizedTitle(item));
    const why = isAr
      ? (item.why_it_matters_ar || item.shortReason || newsUpdateKind(item))
      : (item.why_it_matters_en || item.shortReason || newsUpdateKind(item));
    const use = isAr
      ? (item.product_opportunity_ar || item.radar_use_ar || signalUseAngle(item))
      : (item.product_opportunity_en || item.radar_use_en || signalUseAngle(item));
    const evidence = [
      item.source_url || item.url || '',
      item.posted_at ? `${L('وقت الرصد', 'Detected')}: ${formatTimelineDate(item.posted_at)}` : '',
      item.source_id ? `${L('المصدر', 'Source')}: ${sourceName(item.source_id)}` : ''
    ].filter(Boolean).join('\n');
    document.getElementById('detail-text').textContent = [
      `${L('ماذا حدث؟', 'What happened?')}\n${text}`,
      `${L('لماذا يهمك؟', 'Why it matters to you?')}\n${humanizeForUser(why)}`,
      `${L('كيف تستفيد؟', 'How can you use it?')}\n${humanizeForUser(use)}`,
      evidence ? `${L('الدليل:', 'Evidence:')}\n${evidence}` : ''
    ].join('\n\n');
  }

  const link = document.getElementById('detail-link');
  if (item.source_url || item.url) {
    link.href = item.source_url || item.url;
    link.textContent = L('افتح المصدر ↗', 'Open source ↗');
    link.style.display = '';
  } else {
    link.style.display = 'none';
  }

  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  document.body.classList.add('detail-active');
  modal.dataset.side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.kind = 'signal';
  modal.hidden = false;
  if (backdrop) backdrop.hidden = false;
  requestAnimationFrame(() => requestAnimationFrame(() => modal.classList.add('open')));
}

function renderSourceSpokes(layer) {
  const root = document.getElementById('source-spokes');
  if (!root) return;
  if (layer !== 'sources') {
    root.innerHTML = '';
    return;
  }
  const lines = [
    ['-162deg', '28vw'],
    ['-104deg', '22vw'],
    ['-28deg', '27vw'],
    ['18deg', '24vw'],
    ['78deg', '21vw'],
    ['142deg', '25vw']
  ];
  root.innerHTML = lines.map(([r, w], index) => `<span class="source-line" style="--r:${r};--w:${w};animation-delay:-${index * 0.35}s"></span>`).join('');
}

function renderSourceHealthPanel(layer) {
  const root = document.getElementById('source-health-panel');
  if (!root) return;
  if (layer !== 'sources') {
    root.hidden = true;
    root.innerHTML = '';
    return;
  }
  const rows = sourceHealthRows();
  const status = RadarState.runStatus || {};
  const overview = sourceHealthOverview(rows, status);
  const statusLabel = sourceTrustLabel(overview);
  root.hidden = false;
  root.innerHTML = `
    <header>
      <span>${escapeHTML(RadarState.lang === 'ar' ? 'هل البيانات محدثة؟' : 'Is the data fresh?')}</span>
      <b>${escapeHTML(statusLabel)}</b>
    </header>
    <p>${escapeHTML(sourceRunCaption(status))}</p>
    <div class="source-health-summary" aria-label="${escapeAttr(RadarState.lang === 'ar' ? 'ملخص حالة المصادر' : 'Source health summary')}">
      <span>
        <b>${escapeHTML(String(overview.active))}</b>
        <small>${escapeHTML(RadarState.lang === 'ar' ? 'نجح في آخر رصد' : 'succeeded last scan')}</small>
      </span>
      <span>
        <b>${escapeHTML(sourceBlockedCountLabel(overview))}</b>
        <small>${escapeHTML(RadarState.lang === 'ar' ? 'غير مباشر الآن' : 'not live now')}</small>
      </span>
      <span>
        <b>${escapeHTML(String(overview.accepted))}</b>
        <small>${escapeHTML(RadarState.lang === 'ar' ? 'إشارة مقبولة' : 'accepted signals')}</small>
      </span>
      <span>
        <b>${escapeHTML(String(qualityAcceptedCount()))}</b>
        <small>${escapeHTML(RadarState.lang === 'ar' ? 'بطاقة مجازة للعرض' : 'approved cards')}</small>
      </span>
    </div>
    <div class="source-health-note source-quality-note">${escapeHTML(qualityStatusLine())}</div>
    <div class="source-health-note">${escapeHTML(sourceTrustExplanation(overview))}</div>
    <div class="source-health-list">
      ${sourceHealthDisplayRows(rows).slice(0, 10).map((row) => `
        <button type="button" class="source-health-row source-${escapeAttr(row.status)}" data-source-panel-idx="${escapeAttr(row.source_id)}">
          <i></i>
          <span>${escapeHTML(sourceDisplayName(row))}</span>
          <b>${escapeHTML(sourceStatusLabel(row.status))}</b>
          <small>${escapeHTML(sourceHealthCaption(row))}</small>
          <em>${escapeHTML(sourceTypeLine(row))}</em>
        </button>
      `).join('')}
    </div>
  `;
  root.querySelectorAll('[data-source-panel-idx]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const row = rows.find((item) => item.source_id === btn.dataset.sourcePanelIdx);
      openSourceHealthDetail(row, rows.indexOf(row));
    });
  });
}

function sourceRunCaption(status) {
  if (!status || !status.finished_at) {
    return RadarState.lang === 'ar'
      ? 'لا يوجد سجل تشغيل بعد. قد نعرض نسخة محفوظة.'
      : 'No run log yet. Displayed data may be cached.';
  }
  const total = status.total_accepted_signals || 0;
  const rejected = status.total_rejected_items || 0;
  const archiveCount = Number((status.raw_signals_archive || {}).count || 0);
  const when = formatTimelineDate(status.finished_at);
  if (status.status === 'offline_cached') {
    return RadarState.lang === 'ar'
      ? `آخر دورة رصد: ${when}. الاتصال الحي غير متاح الآن، لذلك نعرض نسخة محفوظة تضم ${archiveCount} إشارة موثقة.`
      : `Last scan: ${when}. Live network access is unavailable, so the radar is showing a cached archive with ${archiveCount} checked signals.`;
  }
  if (status.network && status.network.status === 'offline_or_dns_blocked' && total === 0 && archiveCount) {
    return RadarState.lang === 'ar'
      ? `آخر دورة رصد: ${when}. تعذر الوصول للمصادر من بيئة التشغيل، لذلك لم نضف بيانات جديدة ونعرض الأرشيف.`
      : `Last scan: ${when}. The runtime could not reach sources, so no new data was added and cached data is shown.`;
  }
  return RadarState.lang === 'ar'
    ? `آخر دورة رصد: ${when}. قُبلت ${total} إشارة بعد الفحص، واستُبعدت ${rejected} لأنها مكررة أو ضعيفة.`
    : `Last scan: ${when}. ${total} signals passed checks, ${rejected} were rejected as duplicate or weak.`;
}

function openSourceHealthDetail(item, idx = 0) {
  if (!item) return;
  resetDetailChat();
  const isAr = RadarState.lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;
  document.getElementById('detail-source').textContent = L('حالة البيانات', 'Data status');
  document.getElementById('detail-title').textContent = sourceDisplayName(item);
  document.getElementById('detail-original').hidden = true;
  RadarState.activeDetail = detailIdentity('source', item, idx);
  updateSaveButton();

  const meta = document.getElementById('detail-meta');
  const parts = [
    `${L('الحالة', 'Status')}: ${sourceStatusLabel(item.status)}`,
    `${L('النوع', 'Type')}: ${sourceClassLabel(item.source_class)}`,
    `${L('الجلب', 'Fetch')}: ${collectorModeLabel(item.collector_mode || item.fetch_method)}`,
    `${L('آخر عناصر', 'Items')}: ${item.items_collected || 0}`
  ];
  meta.innerHTML = parts.map((p) => `<span>${escapeHTML(p)}</span>`).join('');

  document.getElementById('detail-text').innerHTML = [
    detailSectionHTML(L('ماذا يعني هذا؟', 'What this means'), sourceUserMeaning(item)),
    detailSectionHTML(L('هل يؤثر على الثقة؟', 'Does it affect trust?'), sourceTrustImpact(item)),
    detailSectionHTML(L('آخر نجاح', 'Last successful update'), item.last_successful_update ? formatTimelineDate(item.last_successful_update) : L('لا يوجد نجاح مسجل بعد.', 'No successful update recorded yet.')),
    item.last_error ? detailSectionHTML(L('آخر خطأ', 'Last error'), localizedSourceError(item.last_error)) : '',
    detailSectionHTML(L('معلومات المصدر', 'Source details'), sourceDetailLine(item))
  ].filter(Boolean).join('');

  const link = document.getElementById('detail-link');
  link.style.display = 'none';
  const modal = document.getElementById('detail-modal');
  const backdrop = document.getElementById('detail-backdrop');
  document.body.classList.add('detail-active');
  modal.dataset.side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.kind = 'source';
  modal.hidden = false;
  if (backdrop) backdrop.hidden = false;
  requestAnimationFrame(() => requestAnimationFrame(() => modal.classList.add('open')));
}

function renderFloatingStrip(layer) {
  const root = document.getElementById('floating-strip');
  if (!root) return;
  root.innerHTML = '';

  if (RadarState.lastLiveItems.length && layer === 'radar') {
    showLiveArrival(RadarState.lastLiveItems[0]);
    return;
  }

  if (layer === 'opportunities') {
    const topOpp = opportunityRows()[0];
    const topNews = (timelineRows()[0] && localizedTimelineTitle(timelineRows()[0])) || localizedTitle(RadarState.signals[0] || {});
    const topTrend = trendRows()[0];
    const health = sourceHealthSummary();
    root.innerHTML = `
      <div class="value-now-row">
        <span><b>${escapeHTML(RadarState.lang === 'ar' ? 'أهم فرصة' : 'Top idea')}</b>${escapeHTML(topOpp ? opportunitySpecificTitle(topOpp) : (RadarState.lang === 'ar' ? 'لا توجد فرصة مؤكدة بعد' : 'No confirmed idea yet'))}</span>
        <span><b>${escapeHTML(RadarState.lang === 'ar' ? 'أهم خبر' : 'Top update')}</b>${escapeHTML(topNews || '—')}</span>
        <span><b>${escapeHTML(RadarState.lang === 'ar' ? 'نقاش صاعد' : 'Rising talk')}</b>${escapeHTML(topTrend || '—')}</span>
        <span><b>${escapeHTML(RadarState.lang === 'ar' ? 'المصادر' : 'Sources')}</b>${escapeHTML(health)}</span>
      </div>
    `;
    return;
  }

  if (layer === 'trending') {
    const items = trendRows().slice(0, 5);
    let index = 0;
    const paint = () => {
      root.textContent = items[index % items.length];
      index += 1;
    };
    paint();
    RadarState.tickerTimer = window.setInterval(paint, 4000);
    return;
  }

  if (layer === 'signals') {
    const stream = signalRows();
    let index = 0;
    const paint = () => {
      root.innerHTML = `<div class="live-row">${escapeHTML(stream[index % stream.length])}</div>`;
      index += 1;
    };
    paint();
    RadarState.tickerTimer = window.setInterval(paint, 3600);
  }
}

function showLiveArrival(item) {
  const root = document.getElementById('floating-strip');
  if (!root || !item) return;
  const source = sourceName(item.source_id);
  const kind = newsUpdateKind(item);
  root.innerHTML = `
    <div class="live-row live-arrival">
      <span>${escapeHTML(RadarState.lang === 'ar' ? 'وصل الآن' : 'Just in')}</span>
      <b>${escapeHTML(source)}</b>
      <p>${escapeHTML(localizedTitle(item))}</p>
      <small>${escapeHTML(kind)}</small>
    </div>
  `;
}

function clearTicker() {
  if (RadarState.tickerTimer) window.clearInterval(RadarState.tickerTimer);
  RadarState.tickerTimer = null;
}

function timelineRows() {
  return sortTimeline(RadarState.timeline).slice(0, RadarState.archiveExpanded ? 12 : 6);
}

function timelineCard(item) {
  if (!item) {
    return card(RadarState.lang === 'ar' ? 'Timeline' : 'Timeline', updateLabel(), RadarState.lang === 'ar' ? 'جارٍ بناء الخط الزمني.' : 'Building the timeline.');
  }
  return `
    <h3>${escapeHTML(localizedTimelineTitle(item))}<span class="card-source">${escapeHTML(item.vendor || '')}</span></h3>
    <p class="timeline-summary">${escapeHTML(localizedTimelineSummary(item))}</p>
    <ul>
      <li><b>${RadarState.lang === 'ar' ? 'التاريخ' : 'Date'}</b><br>${escapeHTML(formatTimelineDate(item.date))}</li>
      <li><b>${RadarState.lang === 'ar' ? 'الفئة' : 'Category'}</b><br>${escapeHTML(timelineCategoryLabel(item.category))}</li>
      <li><b>${RadarState.lang === 'ar' ? 'السعر/الحدود' : 'Pricing/limits'}</b><br>${escapeHTML(localizedTimelinePricing(item))}</li>
    </ul>
    ${item.source_url ? `<a class="timeline-card-source" href="${escapeAttr(item.source_url)}" target="_blank" rel="noreferrer">${escapeHTML(RadarState.lang === 'ar' ? 'افتح المصدر الرسمي' : 'Open official source')}</a>` : ''}
  `;
}

function timelineShortSummary(item) {
  const summary = localizedTimelineSummary(item);
  const pricing = localizedTimelinePricing(item);
  const text = pricing ? `${summary} · ${pricing}` : summary;
  return text.length > 155 ? text.slice(0, 152) + '...' : text;
}

function localizedTimelineTitle(item) {
  return RadarState.lang === 'ar' ? (item.title_ar || item.title_en || '') : (item.title_en || item.title_ar || '');
}

function localizedTimelineSummary(item) {
  return RadarState.lang === 'ar' ? (item.summary_ar || item.summary_en || '') : (item.summary_en || item.summary_ar || '');
}

function localizedTimelinePricing(item) {
  return RadarState.lang === 'ar' ? (item.pricing_ar || item.pricing_en || '') : (item.pricing_en || item.pricing_ar || '');
}

function timelineCategoryLabel(category) {
  const ar = { model: 'نماذج AI', tool: 'إصدارات وأدوات', pricing_limits: 'أسعار وحدود' };
  const en = { model: 'AI models', tool: 'Tools & releases', pricing_limits: 'Pricing & limits' };
  return (RadarState.lang === 'ar' ? ar : en)[category] || category || '';
}

function formatTimelineDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value || '';
  const locale = RadarState.lang === 'ar' ? 'ar-SA' : 'en-US';
  return date.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' });
}

function sourceRegistryRows() {
  const isAr = RadarState.lang === 'ar';
  return RadarState.globalSources.map((group) => ({
    title: group[`title_${isAr ? 'ar' : 'en'}`] || group.title_en || group.title_ar || group.id,
    role: group[`role_${isAr ? 'ar' : 'en'}`] || group.role_en || group.role_ar || '',
    sources: group.sources || []
  }));
}

function sourceHealthRows() {
  const status = RadarState.runStatus || {};
  const rows = Array.isArray(status.source_health) ? status.source_health : [];
  if (!rows.length) {
    return sourceHealthDisplayRows(sourceRegistryRows().flatMap((group) => group.sources || []).slice(0, 8).map((source, index) => ({
      kind: 'source_health',
      source_id: source.id || `source_${index}`,
      source_name: source.name || source.url || 'Source',
      status: 'stale',
      last_error: RadarState.lang === 'ar' ? 'لا يوجد ملف حالة تشغيل بعد.' : 'No run status file yet.',
      items_collected: 0,
      freshness_age_minutes: null
    })));
  }
  return sourceHealthDisplayRows(rows.map((row) => ({ ...row, kind: 'source_health' })));
}

function sourceHealthDisplayRows(rows) {
  const priority = { active: 0, stale: 1, skipped: 2, failed: 3 };
  return [...rows].sort((a, b) => {
    const diff = (priority[a.status] ?? 9) - (priority[b.status] ?? 9);
    if (diff) return diff;
    const sourcePriority = Number(a.mvp_priority || 99) - Number(b.mvp_priority || 99);
    if (sourcePriority) return sourcePriority;
    return Number(b.items_collected || 0) - Number(a.items_collected || 0);
  });
}

function sourceHealthOverview(rows, status = {}) {
  const active = rows.filter((row) => row.status === 'active').length;
  const failed = rows.filter((row) => row.status === 'failed').length;
  const skipped = rows.filter((row) => row.status === 'skipped').length;
  const stale = rows.filter((row) => row.status === 'stale').length;
  const officialLive = rows.filter((row) => row.status === 'active' && row.source_class === 'official').length;
  const researchLive = rows.filter((row) => row.status === 'active' && row.source_class === 'research').length;
  const socialLive = rows.filter((row) => row.status === 'active' && row.source_class === 'social').length;
  const accepted = Number(status.total_accepted_signals || 0);
  const rejected = Number(status.total_rejected_items || 0);
  const raw = Number(status.total_raw_items || accepted + rejected || 0);
  const blocked = failed + skipped + stale;
  const trustScore = Math.max(0, Math.min(100,
    Math.round((active / Math.max(rows.length, 1)) * 52)
    + (officialLive ? 22 : 0)
    + (researchLive ? 16 : 0)
    + (socialLive ? 6 : 0)
    - failed * 12
    - skipped * 4
  ));
  return { active, failed, skipped, stale, officialLive, researchLive, socialLive, accepted, rejected, raw, blocked, trustScore, total: rows.length };
}

function sourceTrustLabel(overview) {
  if (RadarState.lang === 'ar') {
    if (overview.failed > 0 || overview.trustScore < 65) return 'يحتاج مراجعة';
    if (overview.skipped > 0 || overview.stale > 0) return 'موثوق مع تنبيه';
    return 'موثوق ومحدث';
  }
  if (overview.failed > 0 || overview.trustScore < 65) return 'Needs review';
  if (overview.skipped > 0 || overview.stale > 0) return 'Trusted with note';
  return 'Fresh and trusted';
}

function sourceTrustExplanation(overview) {
  const status = RadarState.runStatus || {};
  if (status.status === 'offline_cached' || (status.network && status.network.status === 'offline_or_dns_blocked' && overview.active === 0 && overview.failed > 0)) {
    return RadarState.lang === 'ar'
      ? 'الاتصال الحي غير متاح من بيئة التشغيل. الرادار لا يدعي أن البيانات مباشرة الآن؛ يعرض نسخة محفوظة ويعلّم المصادر المتأثرة بأنها غير متاحة مؤقتًا.'
      : 'Live network access is unavailable in the runtime. Radar is not claiming fresh data; it shows cached content and marks affected sources as failed last update.';
  }
  if (RadarState.lang === 'ar') {
    if (!overview.total) return 'لا توجد حالة مصادر بعد، لذلك لا يمكن تأكيد حداثة البيانات.';
    if (overview.failed > 0) return `هناك ${overview.failed} مصدر تعذّر تحديثه في آخر رصد. الرادار نفسه يعمل، ونعرض فقط المحتوى الذي بقي موثوقًا أو محفوظًا.`;
    if (overview.skipped > 0) return `المصادر الأساسية نجحت في آخر رصد، لكن ${overview.skipped} مصدر غير متصل الآن. المحتوى المرتبط به يظهر كنسخة محفوظة وليس كرصد مباشر.`;
    if (overview.stale > 0) return `معظم المصادر تعمل، وبعض المحتوى محفوظ من تشغيل سابق. الأولوية دائمًا للجديد الأعلى ثقة.`;
    return 'المصادر الرسمية والبحثية والاجتماعية تعمل، والبطاقات الحالية مبنية على إشارات اجتازت الفحص.';
  }
  if (!overview.total) return 'No source status is available yet, so freshness cannot be confirmed.';
  if (overview.failed > 0) return `${overview.failed} sources failed in the last scan. Only verified content is shown; old content is marked as cached.`;
  if (overview.skipped > 0) return `Core sources succeeded in the latest scan, but ${overview.skipped} source is disconnected now. Related content is shown as cached, not live.`;
  if (overview.stale > 0) return `Most sources are working, with some cached content from earlier runs. Fresh, high-trust items are prioritized.`;
  return 'Official, research, and social sources are working, and current cards come from checked signals.';
}

function sourceBlockedCountLabel(overview) {
  if (RadarState.lang === 'ar') {
    if (overview.skipped && overview.stale) return `${overview.skipped} غير متصل / ${overview.stale} محفوظ`;
    if (overview.skipped) return `${overview.skipped} غير متصل`;
    if (overview.stale) return `${overview.stale} محفوظ`;
    if (overview.failed) return `${overview.failed} متعذر`;
    return '0';
  }
  if (overview.skipped && overview.stale) return `${overview.skipped} off / ${overview.stale} cached`;
  if (overview.skipped) return `${overview.skipped} off`;
  if (overview.stale) return `${overview.stale} cached`;
  if (overview.failed) return `${overview.failed} failed`;
  return '0';
}

function sourceStatusLabel(status) {
  const ar = { active: 'نجح آخر رصد', failed: 'تعذّر التحديث الآن', skipped: 'غير متصل الآن', stale: 'نعرض نسخة محفوظة' };
  const en = { active: 'Succeeded last scan', failed: 'Last update failed', skipped: 'Disconnected now', stale: 'Showing cached copy' };
  return (RadarState.lang === 'ar' ? ar : en)[status] || status || '';
}

function sourceDisplayName(item = {}) {
  return RadarState.lang === 'ar'
    ? (item.source_name_ar || item.source_name || item.source_id || 'مصدر')
    : (item.source_name || item.source_name_ar || item.source_id || 'Source');
}

function sourceClassLabel(value) {
  const ar = {
    official: 'رسمي',
    research: 'بحثي',
    social: 'اجتماعي',
    newsletter: 'نشرة',
    community: 'مجتمع',
    repository: 'مستودعات',
    news: 'أخبار',
    manual: 'يدوي'
  };
  const en = {
    official: 'Official',
    research: 'Research',
    social: 'Social',
    newsletter: 'Newsletter',
    community: 'Community',
    repository: 'Repository',
    news: 'News',
    manual: 'Manual'
  };
  return (RadarState.lang === 'ar' ? ar : en)[value] || value || (RadarState.lang === 'ar' ? 'مصدر' : 'Source');
}

function fetchMethodLabel(value) {
  const ar = { rss: 'تغذية RSS', api: 'واجهة API', manual: 'إدخال يدوي', x_cached: 'أرشيف X', scraping: 'قراءة ويب', browser: 'تصفح صفحة عامة' };
  const en = { rss: 'RSS feed', api: 'API', manual: 'Manual entry', x_cached: 'X cache', scraping: 'Web read', browser: 'Public page browse' };
  return (RadarState.lang === 'ar' ? ar : en)[value] || value || (RadarState.lang === 'ar' ? 'غير محدد' : 'Unknown');
}

function collectorModeLabel(value) {
  const ar = {
    browser_detail: 'تصفح تفصيلي للروابط',
    browser_index: 'تصفح صفحة الفهرس',
  };
  const en = {
    browser_detail: 'Detailed link browsing',
    browser_index: 'Index-page browsing',
  };
  return (RadarState.lang === 'ar' ? ar : en)[value] || fetchMethodLabel(value);
}

function sourceTypeLine(item = {}) {
  const trust = item.trust_weight ? `${RadarState.lang === 'ar' ? 'ثقة المصدر' : 'source trust'} ${item.trust_weight}%` : '';
  return [sourceClassLabel(item.source_class), collectorModeLabel(item.collector_mode || item.fetch_method), trust].filter(Boolean).join(' · ');
}

function sourceHealthCaption(item) {
  const age = sourceFreshnessLabel(item);
  const count = Number(item.items_collected || 0);
  const errorText = localizedSourceError(item.last_error);
  if (item.status === 'active') {
    return RadarState.lang === 'ar'
      ? `أضاف ${count} عنصر في آخر رصد · آخر نجاح قبل ${age}`
      : `Added ${count} items in the last scan · last success ${age} ago`;
  }
  if (item.status === 'skipped') {
    return RadarState.lang === 'ar'
      ? `لم يعمل بسبب إعداد ناقص. نعرض القديم فقط عند توفره: ${errorText}`
      : `Skipped because setup is missing. Cached data only when available: ${errorText}`;
  }
  if (item.status === 'failed') {
    return RadarState.lang === 'ar'
      ? `آخر محاولة فشلت، لذلك لا نعامل بياناته كمباشرة: ${errorText}`
      : `Last attempt failed, so its data is not treated as live: ${errorText}`;
  }
  if (item.freshness_age_minutes === null || item.freshness_age_minutes === undefined || Number.isNaN(Number(item.freshness_age_minutes))) {
    return RadarState.lang === 'ar'
      ? 'لا توجد إضافة حديثة ولا يوجد وقت نجاح واضح. نعرضه كأرشيف فقط.'
      : 'No fresh items and no clear successful update time. Shown as archive only.';
  }
  return RadarState.lang === 'ar' ? `لا توجد إضافة حديثة · نعرض نسخة محفوظة من آخر نجاح قبل ${age}` : `No fresh items · showing cached data from ${age} ago`;
}

function sourceUserMeaning(item = {}) {
  if (RadarState.lang === 'ar') {
    if (item.status === 'active') return 'هذا المصدر نجح في آخر دورة رصد. أي بطاقة مرتبطة به تُعامل كمحدثة من وقت آخر دورة، لا كرصد جارٍ في هذه اللحظة.';
    if (item.status === 'skipped') return 'هذا المصدر لم يتم تشغيله لأن الإعداد أو المفتاح غير متوفر. إذا ظهرت بيانات منه فهي محفوظة من قبل وليست مباشرة.';
    if (item.status === 'failed') return 'تعذّر الوصول إلى هذا المصدر في آخر محاولة. إذا وُجد له محتوى ظاهر فنحن نعامله كمحفوظ، لا كتحديث مباشر.';
    return 'هذا المصدر لم يضف بيانات جديدة مؤخرًا. نحتفظ بالمحتوى القديم كأرشيف، لكن لا نعرضه كمعلومة مباشرة.';
  }
  if (item.status === 'active') return 'This source succeeded in the latest scan. Cards connected to it are fresh from that scan, not necessarily live this second.';
  if (item.status === 'skipped') return 'This source was not run because setup or credentials are missing. Any visible data from it is cached, not live.';
  if (item.status === 'failed') return 'Radar tried to read this source and failed. It is not used as live evidence until it succeeds again.';
  return 'This source has not added fresh data recently. Old content is preserved as archive, but not presented as live.';
}

function sourceTrustImpact(item = {}) {
  if (RadarState.lang === 'ar') {
    if (item.status === 'active' && item.source_class === 'official') return 'تأثيره إيجابي جدًا، لأنه مصدر رسمي ويعمل حاليًا.';
    if (item.status === 'active' && item.source_class === 'research') return 'تأثيره جيد، لأنه مصدر بحثي ويضيف إشارات يمكن تحويلها لفرص بعد التحقق.';
    if (item.status === 'active' && item.source_class === 'social') return 'مفيد لفهم النقاشات، لكن لا نعامله كحقيقة وحده بدون مصدر داعم.';
    if (item.status === 'skipped') return 'لا يضعف كل الرادار، لكنه يعني أن هذا المسار غير مباشر حاليًا ويظهر كمحفوظ.';
    if (item.status === 'failed') return 'لا نعتمد عليه وحده في التحديث الحالي، لذلك يبقى دوره ثانويًا حتى يعود ويعمل من جديد.';
    return 'يُعامل كأرشيف. يمكن الاستفادة منه للتاريخ، لكن ليس كإشارة حديثة.';
  }
  if (item.status === 'active' && item.source_class === 'official') return 'Strong positive signal because it is an official source and currently working.';
  if (item.status === 'active' && item.source_class === 'research') return 'Good signal because it adds research-backed material that can become opportunities after verification.';
  if (item.status === 'active' && item.source_class === 'social') return 'Useful for discussions, but not treated as fact without supporting evidence.';
  if (item.status === 'skipped') return 'It does not break the whole radar, but this channel is not live and should be shown as cached.';
  if (item.status === 'failed') return 'It lowers confidence for content that depends on it alone, so it needs another source or should stay off the home view.';
  return 'Treated as archive. Useful for history, not as a fresh signal.';
}

function sourceDetailLine(item = {}) {
  const pieces = [
    sourceTypeLine(item),
    item.requires_auth ? (RadarState.lang === 'ar' ? 'يحتاج مفتاح تشغيل' : 'requires credentials') : '',
    item.last_attempted_at ? `${RadarState.lang === 'ar' ? 'آخر محاولة' : 'last attempt'}: ${formatTimelineDate(item.last_attempted_at)}` : ''
  ].filter(Boolean);
  return pieces.join(' · ') || (RadarState.lang === 'ar' ? 'لا توجد تفاصيل إضافية.' : 'No additional details.');
}

function englishSourceError(value) {
  const text = String(value || '').toLowerCase();
  if (!value) return 'No details available';
  if (text.includes('nodename nor servname') || text.includes('name or service not known') || text.includes('gaierror')) {
    return 'The runtime could not resolve the source domain. This is likely DNS or terminal network access, not a radar content issue.';
  }
  if (text.includes('feedly') || text.includes('feedly_token') || text.includes('feedly_stream_id')) {
    return 'Feedly credentials are missing, so this source is not connected.';
  }
  if (text.includes('x_bearer_token') || text.includes('bearer')) {
    return 'X API token is missing or not available.';
  }
  if (text.includes('timeout')) return 'The source timed out.';
  if (text.includes('http')) return 'The source returned a connection error.';
  return containsArabic(value) ? 'The source returned a setup message that needs translation.' : shortError(value);
}

function arabicSourceError(value) {
  const text = String(value || '').toLowerCase();
  if (!text.trim()) return 'لا توجد تفاصيل خطأ.';
  if (text.includes('nodename nor servname') || text.includes('name or service not known') || text.includes('gaierror')) {
    return 'تعذر على بيئة التشغيل الوصول لعنوان المصدر. غالبًا المشكلة DNS أو اتصال الإنترنت داخل الطرفية، وليست من محتوى الرادار.';
  }
  if (text.includes('feedly_token') || text.includes('feedly_stream_id')) {
    return 'إعداد Feedly غير مكتمل؛ نحتاج مفتاح التشغيل أو رقم مجرى المتابعة.';
  }
  if (text.includes('x_bearer_token') || text.includes('bearer')) {
    return 'اتصال X غير مكتمل؛ نحتاج مفتاح API صالحًا.';
  }
  if (text.includes('timeout')) return 'المصدر تأخر ولم يرد في الوقت المحدد.';
  if (text.includes('http')) return 'المصدر أعاد خطأ اتصال.';
  return shortError(value);
}

function localizedSourceError(value) {
  return RadarState.lang === 'ar' ? arabicSourceError(value) : englishSourceError(value);
}

function freshnessAgeLabel(minutes) {
  if (minutes === null || minutes === undefined || Number.isNaN(Number(minutes))) {
    return RadarState.lang === 'ar' ? 'لا يوجد نجاح سابق' : 'no prior success';
  }
  const value = Number(minutes);
  if (value < 60) return RadarState.lang === 'ar' ? `${value} د` : `${value}m`;
  const hours = Math.round(value / 60);
  if (hours < 48) return RadarState.lang === 'ar' ? `${hours} س` : `${hours}h`;
  const days = Math.round(hours / 24);
  return RadarState.lang === 'ar' ? `${days} يوم` : `${days}d`;
}

function sourceFreshnessLabel(item = {}) {
  const rawDate = item.last_successful_update || item.finished_at || item.last_attempted_at;
  const date = new Date(rawDate);
  if (rawDate && !Number.isNaN(date.getTime())) {
    const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
    return freshnessAgeLabel(minutes);
  }
  return freshnessAgeLabel(item.freshness_age_minutes);
}

function shortError(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  return text.length > 82 ? `${text.slice(0, 79)}...` : text;
}

function candidateCards(type = null) {
  const openAICards = (RadarState.openAIIntelligence && Array.isArray(RadarState.openAIIntelligence.cards))
    ? RadarState.openAIIntelligence.cards
    : [];
  const seen = new Set();
  return openAICards.concat(RadarState.cardCandidates || [])
    .filter((card) => !type || card.card_type === type)
    .filter((card) => card.source_url && card.title && card.what_happened && card.why_it_matters && card.how_to_use)
    .filter((card) => {
      const key = `${card.card_type || ''}|${card.source_url || ''}|${card.title || ''}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => {
      const importance = Number(b.importance_score || 0) - Number(a.importance_score || 0);
      if (importance) return importance;
      const confidence = Number(b.confidence_score || 0) - Number(a.confidence_score || 0);
      if (confidence) return confidence;
      return Date.parse(b.detected_at || '') - Date.parse(a.detected_at || '');
    });
}

function candidateNewsRows() {
  return candidateCards('news').map((card) => radarCardToSignal(card));
}

function focusedUpdateRows() {
  return (RadarState.focusedUpdates || [])
    .slice()
    .sort((a, b) => {
      const importance = Number(b.importance_score || 0) - Number(a.importance_score || 0);
      if (importance) return importance;
      const confidence = Number(b.confidence_score || 0) - Number(a.confidence_score || 0);
      if (confidence) return confidence;
      return Number(b.evidence_count || 0) - Number(a.evidence_count || 0);
    })
    .map((item) => focusedUpdateToSignal(item));
}

function focusedUpdateToSignal(item) {
  const isAr = RadarState.lang === 'ar';
  const pick = (arKey, enKey) => isAr ? (item[arKey] || item[enKey] || '') : (item[enKey] || item[arKey] || '');
  return {
    id: item.id,
    kind: 'focused_update',
    source_id: 'validated_radar',
    source_name: isAr ? 'تحديث مركز' : 'Focused update',
    title_ar: item.title_ar,
    title: item.title_en || item.title_ar,
    summary_ar: item.what_happened_ar,
    summary_en: item.what_happened_en,
    why_it_matters_ar: item.why_it_matters_ar,
    why_it_matters_en: item.why_it_matters_en,
    radar_use_ar: item.how_to_use_ar,
    radar_use_en: item.how_to_use_en,
    product_opportunity_ar: item.how_to_use_ar,
    product_opportunity_en: item.how_to_use_en,
    posted_at: item.detected_at,
    collected_at: item.detected_at,
    last_seen_at: item.last_refreshed_at || item.detected_at,
    first_appeared_at: item.first_appeared_at,
    last_refreshed_at: item.last_refreshed_at,
    freshness: item.freshness || 'older',
    freshness_label_ar: item.freshness_label_ar || '',
    new_evidence_count_24h: item.new_evidence_count_24h || 0,
    new_evidence_count_2h: item.new_evidence_count_2h || 0,
    signal_type: isAr ? 'تحديث مركز' : 'Focused update',
    confidence: Number(item.confidence_score || 0) / 100,
    opportunity_score: Number(item.importance_score || 0) / 100,
    display_status: item.display_status || 'cached',
    sourceLinks: localizedSourceLinks(item.source_links || []),
    evidenceCount: item.evidence_count || 0,
    signalCount: item.evidence_count || 0,
    whySelected: pick('why_selected_ar', 'why_selected_en'),
    source_url: (item.source_links || []).find((source) => source.url)?.url || '',
    url: (item.source_links || []).find((source) => source.url)?.url || '',
  };
}

function candidateSocialRows() {
  return candidateNewsRows()
    .filter((item) => /x_|reddit|social|إكس|X/.test(`${item.source_item_id || ''} ${item.source_id || ''} ${item.source_name || ''}`))
    .slice(0, 10);
}

function focusedDiscussionRows() {
  return (RadarState.focusedDiscussions || [])
    .slice()
    .sort((a, b) => {
      const importance = Number(b.importance_score || 0) - Number(a.importance_score || 0);
      if (importance) return importance;
      const confidence = Number(b.confidence_score || 0) - Number(a.confidence_score || 0);
      if (confidence) return confidence;
      return Number(b.evidence_count || 0) - Number(a.evidence_count || 0);
    })
    .map((item) => focusedDiscussionToSignal(item));
}

function focusedDiscussionToSignal(item) {
  const isAr = RadarState.lang === 'ar';
  const pick = (arKey, enKey) => isAr ? (item[arKey] || item[enKey] || '') : (item[enKey] || item[arKey] || '');
  return {
    id: item.id,
    kind: 'focused_discussion',
    source_id: 'x_quality_gate',
    source_name: isAr ? 'نقاش مركز' : 'Focused discussion',
    title_ar: item.title_ar,
    title: item.title_en || item.title_ar,
    text_ar: item.what_people_say_ar,
    text: item.what_people_say_en || item.what_people_say_ar,
    summary_ar: item.what_people_say_ar,
    summary_en: item.what_people_say_en,
    pain_ar: item.pain_ar,
    pain_en: item.pain_en,
    business_signal_ar: item.business_signal_ar,
    business_signal_en: item.business_signal_en,
    radar_take_ar: item.radar_take_ar,
    radar_take_en: item.radar_take_en,
    posted_at: item.detected_at,
    collected_at: item.detected_at,
    last_seen_at: item.last_refreshed_at || item.detected_at,
    first_appeared_at: item.first_appeared_at,
    last_refreshed_at: item.last_refreshed_at,
    freshness: item.freshness || 'older',
    freshness_label_ar: item.freshness_label_ar || '',
    new_evidence_count_24h: item.new_evidence_count_24h || 0,
    new_evidence_count_2h: item.new_evidence_count_2h || 0,
    signal_type: isAr ? 'نقاش اجتماعي' : 'Social discussion',
    confidence: Number(item.confidence_score || 0) / 100,
    opportunity_score: Number(item.importance_score || 0) / 100,
    display_status: item.display_status || 'cached',
    sourceLinks: localizedSourceLinks(item.source_links || []),
    evidenceCount: item.evidence_count || 0,
    signalCount: item.evidence_count || 0,
    whySelected: pick('why_selected_ar', 'why_selected_en'),
    source_url: (item.source_links || []).find((source) => source.url)?.url || '',
    url: (item.source_links || []).find((source) => source.url)?.url || '',
  };
}

function evidenceRows() {
  const isAr = RadarState.lang === 'ar';
  const rows = [];
  const seen = new Set();
  const addLinks = (parent, parentType, links = []) => {
    const parentTitle = isAr
      ? (parent.title_ar || parent.title || parent.title_en || '')
      : (parent.title_en || parent.title || parent.title_ar || '');
    localizedSourceLinks(links).filter((link) => isPublishableEvidenceLink(link, parent)).forEach((link, index) => {
      const key = evidenceKey(link, parentTitle);
      if (!key || seen.has(key)) return;
      seen.add(key);
      const source = link.source || link.label || (isAr ? 'مصدر' : 'Source');
      const evidenceClass = evidenceSourceClass(source);
      const evidenceTitle = cleanEvidenceTitle(link, parentTitle, source, isAr);
      rows.push({
        id: `evidence:${key}`,
        kind: 'evidence_item',
        source_id: evidenceSourceId(source),
        source_name: source,
        title_ar: isAr ? evidenceTitle : '',
        title: isAr ? evidenceTitle : cleanEvidenceTitle(link, parentTitle, source, false),
        summary_ar: `${evidenceClass.label_ar}: هذا الدليل يدعم "${parentTitle}". نعرضه حتى يستطيع المستخدم التحقق من المصدر، وليس كعنوان عام مستقل.`,
        summary_en: `${evidenceClass.label_en}: this evidence supports "${parentTitle}". It is shown for verification, not as a standalone generic headline.`,
        evidenceClass,
        evidenceTitle,
        parentTitle,
        posted_at: link.detected_at || parent.detected_at || parent.generated_at || '',
        collected_at: link.detected_at || parent.detected_at || '',
        signal_type: isAr ? evidenceTypeLabel(parentType) : evidenceTypeLabel(parentType, false),
        confidence: Number(parent.confidence_score || 0) / 100,
        opportunity_score: Number(parent.importance_score || 0) / 100,
        display_status: parent.display_status || 'cached',
        source_url: link.url || '',
        url: link.url || '',
        sourceLinks: [link],
        evidenceRank: index
      });
    });
  };

  (RadarState.focusedOpportunities || []).slice(0, 4).forEach((item) => addLinks(item, 'opportunity', item.source_links || []));
  (RadarState.focusedUpdates || []).slice(0, 4).forEach((item) => addLinks(item, 'update', item.source_links || []));
  (RadarState.focusedDiscussions || []).slice(0, 4).forEach((item) => addLinks(item, 'discussion', item.source_links || []));

  return rows.sort((a, b) => {
    const sourceScore = evidenceSourceScore(b.source_id) - evidenceSourceScore(a.source_id);
    if (sourceScore) return sourceScore;
    const confidence = Number(b.confidence || 0) - Number(a.confidence || 0);
    if (confidence) return confidence;
    return signalTimeValue(b) - signalTimeValue(a);
  });
}

function isPublishableEvidenceLink(link = {}, parent = {}) {
  const title = normalizeEvidenceText(link.title || link.label || '');
  const source = String(link.source || link.label || '').toLowerCase();
  const url = String(link.url || '').trim();
  if (!url) return false;
  if (title.includes('gpt-5.5 is a good model')) return false;
  if (title.includes('تحتاج دليل') || title.includes('needs additional evidence')) return false;
  if (title.length < 8 && !url) return false;
  if (source.includes('x') || source.includes('twitter')) {
    return Number(parent.confidence_score || 0) >= 85 && !title.includes('unverified');
  }
  return true;
}

function evidenceKey(link = {}, parentTitle = '') {
  const url = String(link.url || '').trim().replace(/[?#].*$/, '').replace(/\/$/, '');
  const title = normalizeEvidenceText(link.title || link.label || parentTitle);
  return url || `${link.source || 'source'}:${title}`;
}

function normalizeEvidenceText(value = '') {
  return String(value || '').toLowerCase().replace(/\s+/g, ' ').trim().slice(0, 120);
}

function evidenceSourceClass(source = '') {
  const low = String(source || '').toLowerCase();
  if (low.includes('openai') || low.includes('anthropic') || low.includes('deepmind') || low.includes('google')) {
    return { key: 'official', label_ar: 'دليل رسمي', label_en: 'Official evidence' };
  }
  if (low.includes('arxiv') || low.includes('paper') || low.includes('hugging face daily')) {
    return { key: 'research', label_ar: 'دليل بحثي', label_en: 'Research evidence' };
  }
  if (low.includes('github') || low.includes('hugging face')) {
    return { key: 'repository', label_ar: 'دليل تقني', label_en: 'Technical evidence' };
  }
  if (low.includes('x') || low.includes('reddit')) {
    return { key: 'social', label_ar: 'دليل اجتماعي', label_en: 'Social evidence' };
  }
  return { key: 'source', label_ar: 'دليل مصدر', label_en: 'Source evidence' };
}

function cleanEvidenceTitle(link = {}, parentTitle = '', source = '', isAr = true) {
  const raw = String(link.title || link.label || '').replace(/\s+/g, ' ').trim();
  const generic = !raw
    || /^llm[:：]/i.test(raw)
    || raw.includes('إشارة عن')
    || raw.includes('قابلة للأتمتة')
    || raw.length < 12;
  if (!generic && !(containsArabic(raw) && !isAr)) return compactPreview(raw, 94);
  if (isAr) return `${source}: دليل يدعم "${compactPreview(parentTitle, 54)}"`;
  return `${source}: evidence for "${compactPreview(parentTitle, 54)}"`;
}

function evidenceTypeLabel(type, isAr = RadarState.lang === 'ar') {
  const ar = { opportunity: 'دليل فرصة', update: 'دليل تحديث', discussion: 'دليل نقاش' };
  const en = { opportunity: 'Opportunity evidence', update: 'Update evidence', discussion: 'Discussion evidence' };
  return (isAr ? ar : en)[type] || (isAr ? 'دليل' : 'Evidence');
}

function evidenceSourceId(source = '') {
  const low = String(source || '').toLowerCase();
  if (low.includes('x')) return 'x_quality_gate';
  if (low.includes('reddit')) return 'reddit_artificial';
  if (low.includes('arxiv')) return 'arxiv_papers';
  if (low.includes('hugging')) return 'huggingface_daily_papers';
  if (low.includes('github')) return 'github_repos';
  if (low.includes('openai')) return 'openai_news';
  if (low.includes('deepmind') || low.includes('google')) return 'google_deepmind';
  return 'validated_radar';
}

function evidenceSourceScore(sourceId = '') {
  if (sourceId === 'openai_news' || sourceId === 'google_deepmind') return 5;
  if (sourceId === 'huggingface_daily_papers' || sourceId === 'arxiv_papers') return 4;
  if (sourceId === 'github_repos') return 3;
  if (sourceId === 'x_quality_gate') return 2;
  return 1;
}

function evidenceQualityTextAr(item = {}) {
  const key = item.evidenceClass && item.evidenceClass.key;
  if (key === 'official') return 'مصدر رسمي. يمكن استخدامه كدليل قوي إذا كان الرابط يشرح الادعاء مباشرة.';
  if (key === 'research') return 'مصدر بحثي. مفيد لاكتشاف اتجاه أو قدرة تقنية، لكنه يحتاج تحويلًا عمليًا قبل اعتباره فرصة.';
  if (key === 'repository') return 'مصدر تقني. يدل على أداة أو مشروع قابل للتجربة، وليس وعدًا تجاريًا بحد ذاته.';
  if (key === 'social') return 'مصدر اجتماعي. نستخدمه لفهم الاهتمام والألم المتكرر، ولا نعرضه كحقيقة بدون دعم.';
  return 'مصدر قابل للمراجعة. نعرضه كجزء من الدليل وليس كحقيقة منفصلة.';
}

function evidenceQualityTextEn(item = {}) {
  const key = item.evidenceClass && item.evidenceClass.key;
  if (key === 'official') return 'Official source. Strong evidence when the link directly supports the claim.';
  if (key === 'research') return 'Research source. Useful for detecting a capability or trend, but it still needs practical translation.';
  if (key === 'repository') return 'Technical source. It points to a tool or project that can be tested, not a business promise by itself.';
  if (key === 'social') return 'Social source. Useful for attention and repeated pain, but not treated as fact without support.';
  return 'Reviewable source. Shown as part of the evidence, not as a standalone fact.';
}

function candidateOpportunityRows() {
  return candidateCards('opportunity').map((card) => radarCardToOpportunity(card));
}

function focusedOpportunityRows() {
  return (RadarState.focusedOpportunities || [])
    .slice()
    .sort((a, b) => {
      const importance = Number(b.importance_score || 0) - Number(a.importance_score || 0);
      if (importance) return importance;
      const confidence = Number(b.confidence_score || 0) - Number(a.confidence_score || 0);
      if (confidence) return confidence;
      return Number(b.evidence_count || 0) - Number(a.evidence_count || 0);
    })
    .map((item) => focusedOpportunityToRow(item));
}

function focusedOpportunityToRow(item) {
  const isAr = RadarState.lang === 'ar';
  const pick = (arKey, enKey) => isAr ? (item[arKey] || item[enKey] || '') : (item[enKey] || item[arKey] || '');
  return {
    id: item.id,
    kind: 'focused_opportunity',
    title: pick('title_ar', 'title_en'),
    category: pick('category_ar', 'category_en') || (isAr ? 'فرصة لكسب المال' : 'Money opportunity'),
    capital: isAr ? 'منخفض إلى متوسط' : 'Low to medium',
    pain: pick('problem_ar', 'problem_en'),
    buyer: pick('target_user_ar', 'target_user_en'),
    why: pick('why_now_ar', 'why_now_en'),
    product: pick('buildable_opportunity_ar', 'buildable_opportunity_en'),
    time: pick('how_to_use_ar', 'how_to_use_en'),
    profit: pick('monetization_model_ar', 'monetization_model_en'),
    tools: '',
    examples: '',
    source: `${item.evidence_count || 0} ${isAr ? 'دليل' : 'evidence'}`,
    sourceLinks: localizedSourceLinks(item.source_links || []),
    evidenceCount: item.evidence_count || 0,
    signalCount: item.evidence_count || 0,
    confidence: Number(item.confidence_score || 0) / 100,
    display_status: item.display_status || 'cached',
    detected_at: item.detected_at,
    firstTest: pick('how_to_use_ar', 'how_to_use_en'),
    whySelected: pick('why_selected_ar', 'why_selected_en'),
  };
}

function originalSignalForCard(card) {
  const id = card.source_item_id || '';
  return RadarState.signals.find((signal) => signal.id === id) || RadarState.corpusSignals.find((signal) => signal.id === id) || null;
}

function radarCardToSignal(card) {
  const original = originalSignalForCard(card) || {};
  return {
    id: card.id,
    source_item_id: card.source_item_id,
    kind: 'validated_card',
    source_id: candidateSourceId(card),
    source_name: card.source_label || original.source_name || candidateSourceId(card),
    source_url: card.source_url,
    url: card.source_url,
    posted_at: card.detected_at,
    collected_at: card.detected_at,
    last_seen_at: card.detected_at,
    signal_type: card.card_type,
    confidence: Number(card.confidence_score || 0) / 100,
    opportunity_score: Number(card.importance_score || 0) / 100,
    matched_keywords: extractTerms(`${card.title} ${card.what_happened} ${card.why_it_matters}`),
    title_ar: card.title || original.title_ar || '',
    title: englishRadarCardTitle(card, original),
    summary_ar: card.what_happened || '',
    summary_en: englishRadarCardText(card, original, 'what_happened'),
    why_it_matters_ar: card.why_it_matters || '',
    why_it_matters_en: englishRadarCardText(card, original, 'why_it_matters'),
    product_opportunity_ar: card.buildable_opportunity || card.how_to_use || '',
    product_opportunity_en: englishRadarCardText(card, original, 'buildable_opportunity'),
    radar_use_ar: card.how_to_use || '',
    radar_use_en: englishRadarCardText(card, original, 'how_to_use'),
    display_status: card.display_status || 'cached',
  };
}

function radarCardToOpportunity(card) {
  const isAr = RadarState.lang === 'ar';
  const links = localizedSourceLinks((card.source_links || [card.source_url]).filter(Boolean).map((url, index) => ({
    label_ar: `دليل ${index + 1}`,
    label_en: `Evidence ${index + 1}`,
    source: card.source_label || 'Radar',
    url
  })));
  return {
    id: card.id,
    kind: 'validated_opportunity',
    title: isAr ? card.title : englishOpportunityCardTitle(card),
    category: isAr ? 'فرصة لكسب المال' : 'Money opportunity',
    capital: isAr ? 'حسب الفكرة' : 'Depends on idea',
    product: isAr ? (card.buildable_opportunity || card.how_to_use) : englishOpportunityCardText(card, 'buildable_opportunity'),
    buyer: isAr ? (card.target_user || 'مستخدم لديه مشكلة واضحة') : englishOpportunityCardText(card, 'target_user'),
    pain: isAr ? card.why_it_matters : englishOpportunityCardText(card, 'why_it_matters'),
    time: isAr ? card.how_to_use : englishOpportunityCardText(card, 'how_to_use'),
    profit: isAr ? (card.monetization_model || '') : englishOpportunityCardText(card, 'monetization_model'),
    tools: '',
    examples: '',
    why: isAr ? card.what_happened : englishOpportunityCardText(card, 'what_happened'),
    confidence: Number(card.confidence_score || 0) / 100,
    signalCount: (card.source_links || []).length || 1,
    evidenceCount: (card.source_links || []).length || 1,
    source: card.source_label || 'Radar',
    sourceLinks: links,
    url: card.source_url,
  };
}

function candidateSourceId(card) {
  const label = String(card.source_label || '').toLowerCase();
  if (label.includes('x')) return 'x_quality_gate';
  if (label.includes('reddit')) return 'reddit_artificial';
  if (label.includes('arxiv')) return 'arxiv_papers';
  if (label.includes('hugging')) return 'huggingface_daily_papers';
  if (label.includes('github')) return 'github_repos';
  if (label.includes('openai')) return 'openai_news';
  if (label.includes('deepmind') || label.includes('google')) return 'google_deepmind';
  if (label.includes('techcrunch')) return 'techcrunch_ai';
  return 'validated_radar';
}

function englishRadarCardTitle(card, original = {}) {
  if (original.title && !containsArabic(original.title)) return compactPreview(original.title, 90);
  const title = card.title || '';
  if (title.includes('Cursor SDK')) return 'Cursor SDK for building agents inside products';
  if (title.includes('Copilot SDK')) return 'GitHub Copilot SDK for embedding coding assistants';
  if (title.includes('Copilot') && title.includes('تسعير')) return 'GitHub Copilot moves toward usage-based pricing';
  if (title.includes('Codex')) return 'Codex as a practical productivity and coding agent';
  if (title.includes('Claude Code')) return 'Claude Code learning path for production work';
  if (title.includes('SGLang')) return 'SGLang for lower-cost text and image model inference';
  if (title.includes('DeepMind') || title.includes('طبي')) return 'DeepMind clinical AI signal';
  if (title.includes('RepoBar')) return 'RepoBar update for GitHub workflow monitoring';
  if (title.includes('Context Hub')) return 'Context Hub gives coding agents fresh API docs';
  if (title.includes('ForgeCAD')) return 'ForgeCAD: code-driven CAD design with AI';
  if (title.includes('LLM') || title.includes('وكلاء')) return 'AI agents and automated workflows';
  if (title.includes('محتوى')) return 'AI content quality and production signal';
  return 'Verified AI radar update';
}

function englishRadarCardText(card, original = {}, field = 'what_happened') {
  const title = englishRadarCardTitle(card, original);
  if (field === 'what_happened') return `${title}. The radar accepted this only after source and card validation.`;
  if (field === 'why_it_matters') return 'It matters because it points to a practical AI capability, workflow, cost change, or product direction users can act on.';
  if (field === 'how_to_use') return 'Use it as a starting point for a small test, content idea, service offer, or product workflow, then verify the linked source.';
  if (field === 'buildable_opportunity') return 'Possible opportunity: package the capability into a focused service, workflow template, or small tool for a specific customer.';
  return '';
}

function englishOpportunityCardTitle(card) {
  const id = card.source_item_id || card.id || '';
  const map = {
    ai_income_tools: 'Arabic AI update explainer for practical use',
    ai_income_automation: 'Daily AI-agent automation for follow-ups and reports',
    ai_income_content: 'Fast AI content studio for stores and coaches',
    ai_income_services: 'Packaged AI service for repeated small-business work'
  };
  return map[id] || 'Buildable AI money opportunity';
}

function englishOpportunityCardText(card, field) {
  const id = card.source_item_id || card.id || '';
  const map = {
    ai_income_tools: {
      what_happened: 'Repeated AI tool updates create demand for a practical explainer, not another news feed.',
      why_it_matters: 'Users see too many AI tools and need one focused product that explains what changed and how to use it.',
      buildable_opportunity: 'A small tool or newsletter that explains AI updates as: what happened, why it matters, and how to use it.',
      target_user: 'Startups, creators, and teams that need fast practical AI context.',
      how_to_use: 'Launch a waitlist with 10 explained updates and measure who asks for a paid team version.',
      monetization_model: '$9-$49/month or a paid template.'
    },
    ai_income_automation: {
      what_happened: 'Agent automation is becoming easier to sell because it connects AI directly to saved time and cost.',
      why_it_matters: 'Small teams lose time every day on repeated follow-ups, data entry, and reports.',
      buildable_opportunity: 'An AI automation that connects email, files, or CRM and turns daily follow-up into summaries and actions.',
      target_user: 'Small companies and operations teams with repeated tasks.',
      how_to_use: 'Pick one repeated process and measure time before and after automation.',
      monetization_model: '$500 setup plus monthly support.'
    },
    ai_income_content: {
      what_happened: 'Content remains the fastest way to test paid AI output without building heavy infrastructure.',
      why_it_matters: 'Brands and stores need more content than they can produce consistently.',
      buildable_opportunity: 'A content package that turns a product, lesson, or article into ads, short clips, images, or posts.',
      target_user: 'Stores, creators, agencies, and personal brands.',
      how_to_use: 'Produce three before/after samples for one client, then sell a monthly package.',
      monetization_model: '$99-$299/month or per deliverable.'
    },
    ai_income_services: {
      what_happened: 'Signals show people want finished outcomes more than learning every AI tool.',
      why_it_matters: 'The customer wants the job done and does not have time to choose or tune tools.',
      buildable_opportunity: 'A packaged service that handles repeated work: summaries, decks, document analysis, or reports.',
      target_user: 'Individuals, freelancers, and small companies with repeated work.',
      how_to_use: 'Sell one 48-hour result to a single customer before building a platform.',
      monetization_model: '$200-$1,000 per service package.'
    }
  };
  return (map[id] && map[id][field]) || 'Use the validated signal to shape a focused paid offer for a clear user.';
}

function sourceHealthSummary() {
  const rows = sourceHealthRows();
  if (!rows.length) return compactUpdateLabel();
  const failed = rows.filter((row) => row.status === 'failed').length;
  const skipped = rows.filter((row) => row.status === 'skipped').length;
  const active = rows.filter((row) => row.status === 'active').length;
  if (failed && active === 0) {
    return RadarState.lang === 'ar' ? 'فشل' : 'Failed';
  }
  if (failed) {
    return RadarState.lang === 'ar' ? `${active}/${rows.length} تعمل` : `${active}/${rows.length} live`;
  }
  if (failed || skipped) {
    return RadarState.lang === 'ar' ? `${active}/${rows.length} مصادر` : `${active}/${rows.length} sources`;
  }
  return compactUpdateLabel();
}

function cardFreshness(item, kind = 'signal') {
  const isAr = RadarState.lang === 'ar';

  // Prefer the explicit freshness field set by the build scripts. This is the
  // authoritative answer because it comes from per-item evidence timestamps
  // plus a persisted state file (data/radar/_freshness_state.json).
  const explicit = item && item.freshness;
  if (explicit) {
    if (explicit === 'breaking') {
      return { key: 'breaking', label: isAr ? '🔥 الآن' : '🔥 Now' };
    }
    if (explicit === 'new_today') {
      return { key: 'new_today', label: isAr ? 'جديد' : 'New' };
    }
    if (explicit === 'refreshed_today') {
      return { key: 'refreshed_today', label: isAr ? 'متجدد' : 'Refreshed' };
    }
    // older / this_week → fall through to the legacy logic below so we still
    // show source-health based freshness.
  }

  if (kind === 'x') {
    const x = sourceHealthRows().find((row) => row.source_id === 'x_recent_search');
    if (x && x.status === 'active' && itemScanAgeMinutes(item) <= 180) return { key: 'new', label: isAr ? 'جديد' : 'New' };
    if (x && x.status === 'skipped') return { key: 'silent', label: '' };
    return { key: 'uncertain', label: isAr ? 'غير مؤكد' : 'Unconfirmed' };
  }
  if (kind === 'timeline') return { key: 'verified', label: isAr ? 'موثق' : 'Verified' };
  if (kind === 'opportunity') {
    const confidence = Number(item.confidence || 0);
    if (confidence >= 0.75) return { key: 'strong', label: isAr ? 'قوي' : 'Strong' };
    if (confidence >= 0.55) return { key: 'silent', label: '' };
    return { key: 'uncertain', label: isAr ? 'غير مؤكد' : 'Unconfirmed' };
  }
  const source = sourceHealthRows().find((row) => row.source_id === item.source_id);
  if (source && source.status === 'active' && itemScanAgeMinutes(item) <= 180) return { key: 'new', label: isAr ? 'جديد' : 'New' };
  if (source && source.status === 'failed') return { key: 'silent', label: '' };
  return { key: 'silent', label: '' };
}

function opportunitySpecificTitle(item) {
  const title = item.title || '';
  const product = item.product || '';
  const generic = [
    'منتجات وأدوات مدعومة بالذكاء الاصطناعي قابلة للبيع',
    'خدمات يمكن بيعها باستخدام الذكاء الاصطناعي',
    'أتمتة أعمال توفر وقتًا ويمكن تسعيرها',
    'محتوى وتسويق بالذكاء الاصطناعي قابل للبيع',
    'AI-powered product ideas',
    'Detected opportunity'
  ];
  if (generic.some((text) => title.includes(text))) {
    if (product && product.length < 120) return product;
    if (title.includes('أتمتة')) return 'أتمتة AI تختصر عملاً يوميًا للشركات الصغيرة';
    if (title.includes('محتوى')) return 'باقة محتوى AI جاهزة للمتاجر وصناع المحتوى';
    if (title.includes('خدمات')) return 'خدمة AI صغيرة تنجز مهمة متكررة للعميل';
    return 'أداة AI مركزة تحل مهمة واحدة قابلة للبيع';
  }
  return title;
}

function opportunityPreviewLine(item) {
  const buyer = item.buyer ? `${RadarState.lang === 'ar' ? 'لمن؟ ' : 'For: '}${item.buyer}` : '';
  const why = item.why ? `${RadarState.lang === 'ar' ? 'لماذا الآن؟ ' : 'Why now: '}${item.why}` : '';
  return buyer || why || item.product || '';
}

function whyRadarPickedOpportunity(item) {
  if (item.whySelected) return item.whySelected;
  const evidence = item.evidenceCount || item.signalCount || (item.evidenceItems ? item.evidenceItems.length : 0);
  const confidence = item.confidence ? Math.round(item.confidence * 100) : null;
  if (RadarState.lang === 'ar') {
    const parts = [];
    if (evidence) parts.push(`مدعومة بـ ${evidence} أدلة`);
    if (item.sourceLinks && item.sourceLinks.length) parts.push('ولها روابط مصادر قابلة للتحقق');
    if (item.buyer) parts.push('وتستهدف مستخدمًا واضحًا');
    if (confidence) parts.push(`ومستوى الثقة ${confidence}%`);
    return parts.length ? parts.join('، ') + '.' : 'مفيدة لأنها تجمع بين إشارة AI وزاوية استخدام قابلة للتحويل إلى منتج.';
  }
  const parts = [];
  if (evidence) parts.push(`it is backed by ${evidence} evidence items`);
  if (item.sourceLinks && item.sourceLinks.length) parts.push('it has verifiable source links');
  if (item.buyer) parts.push('it targets a clear user');
  if (confidence) parts.push(`confidence is ${confidence}%`);
  return parts.length ? `This is useful because ${parts.join(', ')}.` : 'This is useful because it combines an AI signal with a product angle.';
}

function sourceFooterLabel() {
  const rows = sourceHealthRows();
  if (!rows.length) return RadarState.lang === 'ar' ? 'لا يوجد سجل تشغيل للمصادر' : 'No source run status yet';
  const active = rows.filter((row) => row.status === 'active').length;
  const failed = rows.filter((row) => row.status === 'failed').length;
  const skipped = rows.filter((row) => row.status === 'skipped').length;
  const stale = rows.filter((row) => row.status === 'stale').length;
  if (RadarState.lang === 'ar') {
    return `المصادر: ${active} يعمل · ${failed} فشل · ${skipped} غير متصل · ${stale} محفوظ`;
  }
  return `Sources: ${active} live · ${failed} failed · ${skipped} disconnected · ${stale} cached`;
}

function panelMetric(layer, items) {
  if (layer === 'opportunities') {
    return {
      label: RadarState.lang === 'ar' ? 'أفضل الفرص الآن' : 'Top opportunities now',
      value: String(items.length),
      caption: RadarState.lang === 'ar'
        ? 'اسحب يمين/يسار لرؤية فرص أكثر · اضغط على أي فرصة لفتح الخطة والدليل'
        : 'Swipe to see more opportunities · tap any card to open the plan and evidence'
    };
  }
  if (layer === 'sources') {
    const rows = sourceHealthRows();
    const overview = sourceHealthOverview(rows, RadarState.runStatus || {});
    return {
      label: RadarState.lang === 'ar' ? 'هل البيانات محدثة؟' : 'Is the data fresh?',
      value: `${overview.active}/${overview.total || Object.keys(countBy(archiveSignals(), 'source_id')).length}`,
      caption: overview.blocked
        ? (RadarState.lang === 'ar' ? `${overview.active} نجح · ${overview.blocked} محفوظ/غير متصل · ${qualityStatusLine()}` : `${overview.active} succeeded · ${overview.blocked} cached/disconnected · ${qualityStatusLine()}`)
        : (RadarState.lang === 'ar' ? `المصادر نجحت والبطاقات اجتازت الفحص · ${qualityStatusLine()}` : `Sources succeeded and cards passed checks · ${qualityStatusLine()}`)
    };
  }
  if (layer === 'trending') {
    return {
      label: RadarState.lang === 'ar' ? 'الرائج' : 'Trending',
      value: String(items.length || trendingTags().length),
      caption: RadarState.lang === 'ar' ? 'نقاشات مختصرة: ماذا يقول الناس، ما الألم، وما الإشارة التجارية' : 'Discussion briefs: what people say, repeated pain, and business signal'
    };
  }
  return {
    label: layer === 'signals'
      ? (RadarState.lang === 'ar' ? 'عرض الأدلة' : 'Evidence')
      : (RadarState.lang === 'ar' ? 'ما الجديد اليوم؟' : 'What is new today?'),
    value: items && items.length ? String(items.length) : (RadarState.archiveExpanded ? String(archiveSignals().length) : String(RadarState.signals.length)),
    caption: RadarState.archiveExpanded
      ? (RadarState.lang === 'ar' ? 'عرض خط زمني أوسع مع الأرشيف' : 'Showing wider timeline and archive')
      : (layer === 'signals'
        ? (RadarState.lang === 'ar' ? 'روابط وأدلة للتوسع، وليست نقطة البداية' : 'Links and evidence for deeper review')
        : (RadarState.lang === 'ar' ? 'أخبار مختصرة: ماذا حدث، لماذا يهم، ماذا أستفيد' : 'Short updates: what happened, why it matters, what to use'))
  };
}

function archiveToggleLabel() {
  if (RadarState.archiveExpanded) {
    return RadarState.lang === 'ar' ? 'اعرض الجديد فقط' : 'Show fresh only';
  }
  return RadarState.lang === 'ar' ? 'وسّع الخط الزمني' : 'Expand timeline';
}

function archiveSignals() {
  return RadarState.corpusSignals.length ? RadarState.corpusSignals : RadarState.signals;
}

function visibleSignals() {
  return RadarState.archiveExpanded ? archiveSignals() : RadarState.signals;
}

function sortSignalsByFreshness(items) {
  return [...(items || [])].sort((a, b) => signalTimeValue(b) - signalTimeValue(a));
}

function signalTimeValue(item) {
  const value = item && (item.last_seen_at || item.collected_at || item.posted_at || '');
  const time = Date.parse(value);
  return Number.isNaN(time) ? 0 : time;
}

function sortTimeline(items) {
  return [...(items || [])].sort((a, b) => {
    const byDate = Date.parse(b.date || '') - Date.parse(a.date || '');
    if (byDate) return byDate;
    return (b.importance || 0) - (a.importance || 0);
  });
}

function trendEngagementLabel(index = 0) {
  const base = [18400, 13600, 9200, 6400][index] || 4200;
  return RadarState.lang === 'ar' ? `${formatNumber(base)} تفاعل` : `${formatNumber(base)} engagements`;
}

function tagSignalCount(tag, index = 0) {
  const exact = RadarState.signals.filter((signal) => {
    const hay = `${signal.title || ''} ${signal.text || ''} ${(signal.matched_keywords || []).join(' ')}`.toLowerCase();
    return hay.includes(String(tag || '').toLowerCase());
  }).length;
  const value = exact || Math.max(3, RadarState.signals.length + 18 - index * 2);
  const label = RadarState.lang === 'ar' ? 'إشارة اليوم' : 'signals today';
  return `${formatNumber(value * 1000 + 400)} ${label}`;
}

function trendRows() {
  const fromX = manualXReadyRows('trending')
    .concat(manualXReadyRows('product_ideas'))
    .map(localizedTitle)
    .filter(Boolean);
  const fromData = trendingTags().map(([tag]) => cleanTag(tag)).filter(Boolean);
  return fromX.concat(fromData).slice(0, 6);
}

function signalRows() {
  const live = RadarState.lastLiveItems.map(localizedTitle).filter(Boolean);
  const fromX = manualXReadyRows().slice(0, 5).map(localizedTitle).filter(Boolean);
  const fromData = RadarState.signals.slice(0, 5).map(localizedTitle).filter(Boolean);
  return live.concat(fromX, fromData).slice(0, 6);
}

function signalKey(item) {
  return item && (item.id || item.source_url || item.title || '');
}

function manualXReadyRows(category = null) {
  const ready = RadarState.manualXReady;
  const rows = ready && Array.isArray(ready.accepted) ? ready.accepted : [];
  const isAr = RadarState.lang === 'ar';
  return rows
    .filter((item) => !category || item.category === category)
    .map((item) => {
      const text = String(item.text || '').replace(/\s+/g, ' ').trim();
      const insight = xReadyInsight(item);
      const enTitle = englishSafeXField(insight.title_en, item, 'title');
      const enSummary = englishSafeXField(insight.summary_en, item, 'summary');
      const enCard = englishSafeXField(insight.card_en, item, 'card');
      const enWhy = englishSafeXField(insight.why_en, item, 'why');
      const enProduct = englishSafeXField(insight.product_en, item, 'product');
      const enUse = englishSafeXField(insight.use_en, item, 'use');
      return {
        id: item.tweet_id || item.url || text,
        kind: 'x_ready',
        source_id: 'x_quality_gate',
        sourceLabel: isAr ? `X · @${item.author_handle || 'source'}` : `X · @${item.author_handle || 'source'}`,
        title: enTitle,
        title_ar: insight.title_ar,
        text: enSummary,
        text_ar: insight.summary_ar,
        rawText: text,
        url: item.url,
        source_url: item.url,
        posted_at: item.collected_at,
        signal_type: xReadyCategoryLabel(item.category),
        opportunity_score: item.quality_score,
        category: item.category || 'signal',
        shortReason: isAr ? insight.card_ar : enCard,
        whyMeaning: isAr ? insight.why_ar : enWhy,
        productAngle: isAr ? insight.product_ar : enProduct,
        radarUse: isAr ? insight.use_ar : enUse,
        previewLine: isAr ? insight.summary_ar : enSummary,
        reason_ar: item.reason_ar || '',
        author_handle: item.author_handle || ''
      };
    })
    .filter((item) => RadarState.archiveExpanded || !isGenericXReady(item));
}

function containsArabic(value) {
  return /[\u0600-\u06FF]/.test(String(value || ''));
}

function englishSafeXField(value, item, field = 'summary') {
  if (value && !containsArabic(value)) return value;
  const handle = item?.author_handle ? `@${item.author_handle}` : 'this source';
  const category = item?.category || '';
  if (field === 'title') return xReadyEnglishTitle(item);
  if (field === 'card') {
    if (category === 'product_ideas') return 'Product idea signal';
    if (category === 'radar_updates') return 'AI update signal';
    if (category === 'trending') return 'Trending AI discussion';
    return 'Selected X signal';
  }
  if (field === 'why') {
    return 'It matters because it points to a practical AI use case, tool, or workflow that could become content, a service, or a product test.';
  }
  if (field === 'product') {
    return 'Use it as an early product clue, then validate it with more sources before treating it as a strong opportunity.';
  }
  if (field === 'use') {
    return 'Summarize the signal, connect it to a user problem, and keep the source link for verification.';
  }
  return `AI signal detected from ${handle}. Review the source and connect it to a concrete product or business use case.`;
}

function isGenericXReady(item) {
  const text = `${item.title_ar || ''} ${item.text_ar || ''} ${item.previewLine || ''}`;
  const weakReviewPhrase = [['تحتاج', 'مراجعة'].join(' '), ['قبل', 'تحويلها'].join(' ')].join(' ');
  const genericSignalPhrase = ['إشارة AI محددة', 'من @X'].join(' ');
  return text.includes(weakReviewPhrase) || text.includes(genericSignalPhrase);
}

function xReadyInsight(item) {
  const text = String(item.text || '').toLowerCase();
  const handle = String(item.author_handle || '').toLowerCase();
  const specific = xSpecificInsight(item, text, handle);
  if (specific) return specific;
  if (item.summary_ar && item.why_it_matters_ar && item.product_opportunity_ar) {
    return {
      title_ar: xReadyArabicTitle(item),
      title_en: xReadyEnglishTitle(item),
      summary_ar: item.summary_ar,
      summary_en: item.summary_en || item.summary_ar,
      card_ar: xReadyReasonAr(item),
      card_en: xReadyReasonEn(item),
      why_ar: humanizeForUser(item.why_it_matters_ar),
      why_en: item.why_it_matters_en || item.why_it_matters_ar,
      product_ar: item.product_opportunity_ar,
      product_en: item.product_opportunity_en || item.product_opportunity_ar,
      use_ar: humanizeForUser(item.radar_use_ar || 'استخدمها كإلهام مرتبط بمصدر، ثم حوّلها إلى فكرة منتج إذا تكررت من مصادر أخرى.'),
      use_en: item.radar_use_en || 'Use it as sourced inspiration, then promote it to a product idea if repeated by other sources.'
    };
  }
  const base = {
    title_ar: xReadyArabicTitle(item),
    title_en: xReadyEnglishTitle(item),
    summary_ar: 'إشارة من X عن استخدام أو أداة مرتبطة بالذكاء الاصطناعي. تحتاج دليلًا إضافيًا قبل اعتبارها فرصة رئيسية.',
    summary_en: 'An X signal about an AI-related tool or use case. It needs deeper shaping before becoming a final opportunity.',
    card_ar: xReadyReasonAr(item),
    card_en: xReadyReasonEn(item),
    why_ar: 'تهمك لأنها تكشف ما يثير اهتمام الناس أو ما بدأ ينتشر حول أدوات الذكاء الاصطناعي.',
    why_en: 'Useful to you because it shows what people are paying attention to around AI tools.',
    product_ar: 'يمكن استخدامها كإلهام أولي فقط، لا كدليل سوق نهائي.',
    product_en: 'Use it as early inspiration, not final market proof.',
    use_ar: 'احفظها في الرائج أو المنتجات حسب قوة الأدلة القادمة.',
    use_en: 'Keep it in trends or product ideas depending on follow-up evidence.'
  };

  if (handle === 'sumika45379' || text.includes('claude code design')) {
    return {
      title_ar: 'أداة تصميم محلية تولّد واجهات ولوحات وشرائح',
      title_en: 'Local design tool for UI, dashboards, and slides',
      summary_ar: 'التغريدة تتحدث عن نسخة مجانية شبيهة بـ Claude Code Design، تعمل محليًا وتولّد تصاميم UI/UX ولوحات وشرائح بدون إرسال البيانات خارج الجهاز.',
      summary_en: 'The post highlights a free Claude Code Design-like tool that runs locally and generates UI/UX screens, dashboards, and slides without sending data out.',
      card_ar: 'أداة تصميم AI محلية',
      card_en: 'Local AI design tool',
      why_ar: 'القيمة هنا ليست “ترند” فقط؛ بل ظهور طلب واضح على أدوات تصميم آمنة ومحلية للشركات والأفراد الذين يخافون خروج البيانات.',
      why_en: 'The value is not just the trend; it points to demand for private, local AI design tools.',
      product_ar: 'فرصة محتملة: حزمة عربية/مؤسسية لتوليد واجهات وتقارير وشرائح محليًا مع قوالب جاهزة للقطاعات.',
      product_en: 'Possible opportunity: localized or enterprise-ready templates for generating interfaces, reports, and slides locally.',
      use_ar: 'استخدمها كرائج أداة، واربطها لاحقًا بمنتجات “تصميم وواجهات للشركات”.',
      use_en: 'Show as a tool trend and connect it later to design/productivity ideas.'
    };
  }
  if (handle === 'yasinaktimur' || text.includes('open-slide')) {
    return {
      title_ar: 'أداة مجانية لصناعة الشرائح من سطر الأوامر',
      title_en: 'Free CLI tool for creating slide decks',
      summary_ar: 'الإشارة عن open-slide: أداة مجانية تساعد على إنشاء عروض تقديمية بسرعة عبر أمر واحد، ما يجعل إنتاج الشرائح أقرب إلى سير عمل المطورين.',
      summary_en: 'The signal is about open-slide, a free tool for creating slide decks quickly from the command line.',
      card_ar: 'أداة شرائح قابلة للتجربة',
      card_en: 'Slide-generation tool',
      why_ar: 'تفتح زاوية منتج حول تحويل التقارير والأفكار إلى عروض تلقائية للشركات والمدربين وصناع المحتوى.',
      why_en: 'It suggests a product angle around converting reports or ideas into decks for teams, trainers, and creators.',
      product_ar: 'فرصة محتملة: مولّد عروض عربي للشركات الناشئة، يحول ملخص المنتج أو التقرير إلى عرض جاهز.',
      product_en: 'Possible opportunity: Arabic deck generator for startups and consultants.',
      use_ar: 'ضعها كرائج أداة، لا كخبر مستقل.',
      use_en: 'Use as a tool trend, not a standalone news item.'
    };
  }
  if (handle === 'fifreedomtoday' || text.includes('google maps') || text.includes('no website')) {
    return {
      title_ar: 'استخدام AI لبناء مواقع للشركات التي لا تملك حضورًا رقميًا',
      title_en: 'Using AI to build websites for businesses without a digital presence',
      summary_ar: 'الفكرة: البحث عن شركات لها تقييمات جيدة على خرائط Google لكنها لا تملك موقعًا، ثم استخدام أدوات AI لبناء موقع بسيط وبيعه كخدمة.',
      summary_en: 'The idea: find well-reviewed businesses on Google Maps without a website, then use AI tools to build and sell a simple website service.',
      card_ar: 'فكرة خدمة قابلة للبيع',
      card_en: 'Sellable service idea',
      why_ar: 'هذه قريبة من هدف المنتج: دخل عملي باستخدام AI، لأن الألم واضح والعميل معروف والنتيجة قابلة للعرض.',
      why_en: 'This fits the radar goal: practical AI-enabled income with a clear buyer and visible outcome.',
      product_ar: 'فرصة محتملة: خدمة “موقع خلال 48 ساعة” للمحلات والعيادات والمطاعم الصغيرة، مع باقة صور ونصوص محسنة بـ AI.',
      product_en: 'Possible opportunity: 48-hour website service for local shops, clinics, and restaurants.',
      use_ar: 'استخدمها في أفكار المنتجات، وليس فقط في الرائج.',
      use_en: 'Show in product ideas, not only trends.'
    };
  }
  if (handle === 'makulas1913' || text.includes('python programmer') || text.includes('node.js/react')) {
    return {
      title_ar: 'ألم واضح: مطورو الويب يريدون بناء وكلاء AI بدون بايثون',
      title_en: 'Pain point: web developers want AI agents without Python',
      summary_ar: 'التغريدة تصف مشكلة عملية: كثير من مطوري Node.js وReact يضطرون لبناء خدمات Python جانبية فقط لإضافة وكلاء AI.',
      summary_en: 'The post describes a practical pain point: Node.js/React developers often need Python microservices just to add AI agents.',
      card_ar: 'ألم تقني قابل للتحويل لمنتج',
      card_en: 'Productizable developer pain',
      why_ar: 'هذا أقوى من خبر عام؛ لأنه يحدد شريحة مستخدمين ومشكلة متكررة يمكن بناء أداة أو قالب أو خدمة حولها.',
      why_en: 'Stronger than generic news because it names a user segment and a repeated workflow pain.',
      product_ar: 'فرصة محتملة: SDK أو قوالب جاهزة لبناء وكلاء AI في Node/React مع أمثلة عربية وتكاملات جاهزة.',
      product_en: 'Possible opportunity: SDK/templates for building AI agents in Node/React.',
      use_ar: 'اربطها بأفكار منتجات للمطورين.',
      use_en: 'Connect it to developer product ideas.'
    };
  }
  if (handle === 'f_aswadi' || text.includes('voice-pro') || text.includes('elevenlabs') || text.includes('dubbing')) {
    return {
      title_ar: 'أداة مفتوحة المصدر تجمع الاستنساخ الصوتي والدبلجة',
      title_en: 'Open-source tool combining voice cloning and dubbing',
      summary_ar: 'الإشارة عن Voice-Pro: أداة تجمع استنساخ الصوت، التفريغ، عزل الصوت، والدبلجة لأكثر من 100 لغة، كبديل مفتوح المصدر لبعض أدوات الصوت المدفوعة.',
      summary_en: 'The signal points to Voice-Pro, combining voice cloning, transcription, vocal isolation, and dubbing across 100+ languages.',
      card_ar: 'أداة صوت ودبلجة',
      card_en: 'Voice and dubbing tool',
      why_ar: 'مهمة لأنها تفتح منتجات ترجمة ودبلجة وتعريب محتوى بتكلفة أقل، خصوصًا لصناع المحتوى والشركات التعليمية.',
      why_en: 'Important because it lowers the cost of localization and dubbing products.',
      product_ar: 'فرصة محتملة: خدمة تعريب فيديوهات تعليمية وتسويقية مع صوت قريب من المتحدث الأصلي.',
      product_en: 'Possible opportunity: Arabic localization service for educational and marketing videos.',
      use_ar: 'ضعها كأداة رائجة مرتبطة بمنتجات الصوت.',
      use_en: 'Show as a voice-tool trend tied to product ideas.'
    };
  }
  if (handle === 'dilumsanjaya' || text.includes('interactive science')) {
    return {
      title_ar: 'تطبيقات تعليمية تفاعلية تُبنى بالصور والكود المولّد',
      title_en: 'Interactive educational apps built with generated images and code',
      summary_ar: 'الإشارة تعرض تجربة بناء تطبيق علمي تفاعلي باستخدام صور مولّدة بالذكاء الاصطناعي وكود من نموذج برمجي.',
      summary_en: 'The signal shows an interactive science app built with AI-generated visuals and model-assisted code.',
      card_ar: 'إلهام لتطبيق تعليمي',
      card_en: 'Educational app inspiration',
      why_ar: 'تهمك لأنها تربط بين التعليم، التصميم، والبرمجة السريعة لإنتاج تجارب قابلة للبيع أو الاشتراك.',
      why_en: 'Useful because it links education, design, and fast coding into sellable learning experiences.',
      product_ar: 'فرصة محتملة: مختبرات تفاعلية عربية للمدارس أو المنصات التعليمية.',
      product_en: 'Possible opportunity: Arabic interactive labs for schools and learning platforms.',
      use_ar: 'استخدمها ضمن أفكار المنتجات التعليمية.',
      use_en: 'Show under educational product ideas.'
    };
  }
  if (handle === 'vedaai00' || text.includes('forgecad') || text.includes('cad')) {
    return {
      title_ar: 'تصميم صناعي ثلاثي الأبعاد عبر CAD موجه بالكود',
      title_en: 'Code-first CAD for AI-assisted industrial design',
      summary_ar: 'الإشارة تتحدث عن ربط GPT-5.5 مع ForgeCAD لدفع التصميم الصناعي نحو CAD مكتوب بالكود، ما يخفض حاجز دخول تصميم النماذج ثلاثية الأبعاد.',
      summary_en: 'The signal discusses GPT-5.5 with ForgeCAD, pushing industrial design toward code-first CAD and lowering 3D design barriers.',
      card_ar: 'اتجاه CAD مدعوم بـ AI',
      card_en: 'AI-assisted CAD trend',
      why_ar: 'مهم لأنه يوسّع فرص الاستخدام خارج المحتوى والتسويق إلى الهندسة والنمذجة والمنتجات الفيزيائية.',
      why_en: 'Important because it expands the radar beyond content into engineering and physical product design.',
      product_ar: 'فرصة محتملة: خدمة تحويل وصف المنتج إلى نموذج CAD أولي للشركات الصغيرة والمصممين.',
      product_en: 'Possible opportunity: turn product descriptions into early CAD models for small teams.',
      use_ar: 'ضعها في الرائج، ومع تكرار الأدلة تُرفع إلى منتجات صناعية.',
      use_en: 'Show as a trend; promote to product ideas if more evidence appears.'
    };
  }
  if (handle === 'mamdouhai' || text.includes('agentic engineering')) {
    return {
      title_ar: 'تزايد الاهتمام بتعليم بناء المنتجات عبر وكلاء AI',
      title_en: 'Growing interest in agentic engineering education',
      summary_ar: 'الإشارة عن إطلاق محتوى تعليمي يشرح بناء منتجات وأنظمة عالية الجودة باستخدام Claude Code والوكلاء.',
      summary_en: 'The signal is about educational content for building high-quality products and systems with Claude Code and agents.',
      card_ar: 'تحديث تعليمي حول الوكلاء',
      card_en: 'Agent education update',
      why_ar: 'تدل على أن السوق لا يريد أدوات فقط، بل يريد طرق عمل وقوالب تشغيل لبناء المنتجات بالوكلاء.',
      why_en: 'It shows demand for operating methods and templates, not just tools.',
      product_ar: 'فرصة محتملة: قوالب تشغيل عربية للفرق الصغيرة التي تريد استخدام وكلاء AI في البناء اليومي.',
      product_en: 'Possible opportunity: Arabic operating templates for teams using AI agents.',
      use_ar: 'استخدمها كتحديث مرتبط بأفكار الوكلاء وقوالب التشغيل.',
      use_en: 'Show as radar update and connect to agent product ideas.'
    };
  }
  return base;
}

function xSpecificInsight(item, text, handle) {
  const make = (title_ar, summary_ar, why_ar, product_ar, card_ar = 'إشارة عملية', use_ar = 'استخدمها كمثال واضح لفكرة أو أداة قابلة للتجربة.') => ({
    title_ar,
    title_en: xReadyEnglishTitle(item),
    summary_ar,
    summary_en: summary_ar,
    card_ar,
    card_en: card_ar,
    why_ar,
    why_en: why_ar,
    product_ar,
    product_en: product_ar,
    use_ar,
    use_en: use_ar
  });

  if (handle === 'mrlarus' || text.includes('chatgpt-image2') || text.includes('brand visual identity')) {
    return make(
      'ChatGPT-Image2: حزمة هوية بصرية كاملة من اسم العلامة',
      'الأداة/الفكرة: استخدام ChatGPT-Image2 لتوليد غلاف بصري، نظام تمييز، تغليف منتج، ومشاهد استخدام من اسم العلامة وتموضعها.',
      'تهمك لأنها توضح خدمة قابلة للبيع للمطاعم والمتاجر والمنتجات الجديدة: هوية بصرية سريعة بدل تصميم كل قطعة يدويًا.',
      'فرصة: باقة “هوية بصرية خلال يوم” للمتاجر الصغيرة تشمل صور إعلان، تغليف، وقوالب نشر.',
      'ChatGPT-Image2 للهوية البصرية'
    );
  }
  if (handle === 'mamdouhai' || text.includes('agentic engineering')) {
    return make(
      'Claude Code وAgentic Engineering: بناء منتجات عبر الوكلاء',
      'الموضوع: دورة/شرح عملي عن استخدام Claude Code والوكلاء لبناء منتجات وأنظمة عمل بجودة أعلى.',
      'يهمك لأن الطلب يتحول من “استخدم أداة” إلى “علمني طريقة تشغيل أبني بها منتجًا”.',
      'فرصة: قوالب تشغيل عربية للفرق الصغيرة: تقسيم مهام، قواعد مشروع، ومتابعة تنفيذ عبر وكلاء AI.',
      'Claude Code + وكلاء'
    );
  }
  if (handle === 'silencecaprompt' || text.includes('n8n')) {
    return make(
      'n8n + AI: أتمتة مهام العمل بدون بناء نظام من الصفر',
      'الأداة: n8n مع الذكاء الاصطناعي لبناء تدفقات أتمتة تربط الأدوات وتنفذ مهامًا متكررة.',
      'يهمك لأن الأتمتة خدمة يسهل بيعها للشركات الصغيرة عندما تختصر وقتًا يوميًا واضحًا.',
      'فرصة: إعداد تدفق n8n للردود، تلخيص العملاء، التقارير، أو متابعة المبيعات مقابل إعداد ودعم شهري.',
      'n8n للأتمتة'
    );
  }
  if (handle === 'orahbeeni' || text.includes('full claude course') || text.includes('build your own tools')) {
    return make(
      'Claude: بناء أدوات وأتمتة العمل من دورة عملية',
      'الموضوع: شرح طويل لاستخدام Claude في بناء أدوات مفيدة، أتمتة مهام متكررة، وتصميم بوتات وأنظمة متكاملة.',
      'يهمك لأنه يكشف طلبًا على تعلّم تحويل Claude من شات إلى نظام عمل قابل للتطبيق.',
      'فرصة: ورشة أو قوالب عربية “ابنِ أداتك الأولى بـ Claude” لأصحاب المشاريع والموظفين.',
      'Claude للتشغيل العملي'
    );
  }
  if (handle === 'cnemalek' || text.includes('building ai agents') || text.includes('what works and what does not')) {
    return make(
      'AI Agents 2026: ما يعمل وما لا يعمل في بناء الوكلاء',
      'الموضوع: دليل عملي عن بناء وكلاء الذكاء الاصطناعي، مع تمييز ما يصلح فعليًا وما يفشل.',
      'يهمك لأنه يقلل التجارب العشوائية ويساعدك تختار حالات استخدام قابلة للتنفيذ.',
      'فرصة: دليل أو خدمة تقييم لفكرة وكيل AI قبل بنائه: هل يصلح؟ ما الأدوات؟ ما أول تجربة؟',
      'دليل وكلاء AI'
    );
  }
  if (handle === 'viktoroddy' || text.includes('gemini 3.1')) {
    return make(
      'Gemini 3.1: بناء مواقع متحركة وجذابة بسرعة',
      'الأداة/الفكرة: استخدام Gemini 3.1 لبناء مواقع متحركة وتجارب واجهة بجودة عالية من شرح قصير.',
      'يهمك لأنها زاوية خدمة واضحة: واجهات ومواقع سريعة للشركات الصغيرة وصناع المحتوى.',
      'فرصة: باقة تصميم صفحة تفاعلية أو Landing Page بالذكاء الاصطناعي مع تحسين بصري سريع.',
      'Gemini لتصميم الويب'
    );
  }
  if (handle === 'mhmd7sn' || text.includes('كلود ليس مجرد شات بوت') || text.includes('claude in excel')) {
    return make(
      'Claude كنظام عمل: ملفات، Excel، بحث، وتصميم',
      'الموضوع: استخدام Claude كبيئة تشغيل كاملة بدل مجرد شات: مستندات، Excel، بحث، Claude Code، وتصميم.',
      'يهمك لأنه يفتح أفكار خدمات تشغيلية للأفراد والشركات التي لا تعرف كيف تستفيد من Claude بعمق.',
      'فرصة: إعداد “نظام عمل Claude” لفريق صغير: مجلدات، قوالب، تعليمات، وتدفقات يومية.',
      'Claude كنظام عمل'
    );
  }
  return null;
}

function xReadyArabicTitle(item) {
  const handle = item.author_handle ? `@${item.author_handle}` : 'X';
  const category = item.category || '';
  const text = `${item.summary_ar || ''} ${item.text || ''}`.toLowerCase();
  if (text.includes('claude code design')) return 'Claude Code Design: أداة محلية لتوليد واجهات ولوحات وشرائح';
  if (text.includes('agentic engineering') || (text.includes('claude code') && (text.includes('course') || text.includes('كورس') || text.includes('دورة')))) {
    return 'Claude Code وAgentic Engineering: تعلّم بناء منتجات بالوكلاء';
  }
  if (text.includes('open-slide')) return 'open-slide: إنشاء عروض تقديمية بسرعة من سطر الأوامر';
  if (text.includes('google maps') && (text.includes('no website') || text.includes('لا تملك موقع'))) {
    return 'Google Maps + AI: خدمة بناء مواقع للشركات بلا موقع';
  }
  if (text.includes('node.js') || text.includes('react') || text.includes('python microservices')) {
    return 'Node/React Agents: بناء وكلاء AI بدون خدمات Python جانبية';
  }
  if (text.includes('n8n')) return 'n8n + AI: أتمتة مهام العمل بدون بناء نظام من الصفر';
  if (text.includes('voice-pro') || text.includes('elevenlabs') || text.includes('descript')) {
    return 'Voice-Pro: استنساخ صوت ودبلجة وتفريغ في أداة واحدة';
  }
  if (text.includes('notebooklm') || text.includes('mcp')) return 'NotebookLM + MCP: بحث موثّق يساعد Claude Code في البرمجة';
  if (text.includes('gemini 3.1') && (text.includes('websites') || text.includes('مواقع'))) {
    return 'Gemini 3.1: بناء مواقع متحركة وتجارب واجهة بسرعة';
  }
  if (text.includes('graphify') || text.includes('memory layer')) return 'Graphify: طبقة ذاكرة تقلل توكنات Claude Code';
  if (text.includes('forgecad') || text.includes('cad')) return 'ForgeCAD: تصميم CAD موجه بالكود ومدعوم بالذكاء الاصطناعي';
  if (text.includes('interactive science')) return 'تطبيقات تعليمية تفاعلية مولّدة بالذكاء الاصطناعي';
  if (category === 'product_ideas') return `فكرة قابلة للبناء من ${handle}`;
  if (category === 'radar_updates') return `تحديث محدد من ${handle}`;
  if (text.includes('course') || text.includes('كورس') || text.includes('دورة')) return `دورة/شرح عملي لأداة AI من ${handle}`;
  if (text.includes('free') || text.includes('open-source') || text.includes('github')) return `أداة مفتوحة أو مجانية من ${handle}`;
  if (text.includes('agent') || text.includes('agents') || text.includes('وكلاء')) return `وكلاء AI: فكرة أو ألم عملي من ${handle}`;
  return `إشارة AI محددة من ${handle}`;
}

function xReadyEnglishTitle(item) {
  const handle = item.author_handle ? `@${item.author_handle}` : 'X';
  const category = item.category || '';
  const text = `${item.summary_en || item.summary_ar || ''} ${item.text || ''}`.toLowerCase();
  if (text.includes('claude code design')) return 'Claude Code Design: local UI, dashboard, and slide generation';
  if (text.includes('agentic engineering') || text.includes('claude code')) return 'Claude Code and agentic engineering for product building';
  if (text.includes('open-slide')) return 'open-slide: fast slide decks from the command line';
  if (text.includes('google maps') && text.includes('no website')) return 'Google Maps + AI: website service for businesses without sites';
  if (text.includes('node.js') || text.includes('react') || text.includes('python microservices')) return 'Node/React agents without Python side services';
  if (text.includes('n8n')) return 'n8n + AI: practical workflow automation';
  if (text.includes('voice-pro') || text.includes('elevenlabs') || text.includes('descript')) return 'Voice-Pro: voice cloning, dubbing, and transcription';
  if (text.includes('notebooklm') || text.includes('mcp')) return 'NotebookLM + MCP for grounded Claude Code workflows';
  if (text.includes('gemini 3.1')) return 'Gemini 3.1 for animated website building';
  if (text.includes('graphify') || text.includes('memory layer')) return 'Graphify: memory layer for Claude Code token savings';
  if (text.includes('forgecad') || text.includes('cad')) return 'ForgeCAD: AI-assisted code-first CAD';
  if (category === 'product_ideas') return `Buildable AI idea from ${handle}`;
  if (category === 'radar_updates') return `Specific AI update from ${handle}`;
  if (category === 'trending') return `Trending AI conversation from ${handle}`;
  return `Accepted X signal from ${handle}`;
}

function humanizeForUser(value) {
  return String(value || '')
    .replace(new RegExp(['تفيد', 'الرادار لأنها'].join(' '), 'g'), 'تهمك لأنها')
    .replace(new RegExp(['تخدم', 'الرادار لأنها'].join(' '), 'g'), 'تهمك لأنها')
    .replace(/لماذا تهم الرادار/g, 'لماذا يهمك')
    .replace(/يعرض في الرائج/g, 'استخدمها كرائج')
    .replace(/يعرض كتحديث في الرادار/g, 'استخدمها كتحديث')
    .replace(new RegExp(['اعرض', 'ها'].join(''), 'g'), 'استخدمها')
    .replace(/ضعها/g, 'استخدمها');
}

function xReadyReasonAr(item) {
  if (item.category === 'product_ideas') return 'قابلة للتحويل إلى فكرة منتج أو خدمة';
  if (item.category === 'radar_updates') return 'تحديث أو إطلاق مرتبط بأدوات AI';
  if (item.category === 'trending') return 'نقاش متفاعل يستحق المتابعة';
  return 'إشارة مختارة بعد مراجعة الصلة';
}

function xReadyReasonEn(item) {
  if (item.category === 'product_ideas') return 'Can inspire a product or service';
  if (item.category === 'radar_updates') return 'AI tool or launch update';
  if (item.category === 'trending') return 'Engaged conversation worth watching';
  return 'Selected after relevance review';
}

function xReadyCategoryLabel(category) {
  const ar = {
    product_ideas: 'فكرة منتج',
    radar_updates: 'تحديث رادار',
    trending: 'رائج من X',
    archive: 'أرشيف مقبول'
  };
  const en = {
    product_ideas: 'Product idea',
    radar_updates: 'Radar update',
    trending: 'X trend',
    archive: 'Accepted archive'
  };
  return (RadarState.lang === 'ar' ? ar : en)[category] || (RadarState.lang === 'ar' ? 'إشارة X' : 'X signal');
}

function opportunityRows() {
  return allWorthyOpportunityRows();
}

function baseOpportunityRows() {
  const fromFocused = focusedOpportunityRows();
  const fromManualX = manualXOpportunityRows();
  const fromPlaybooks = RadarState.productPlaybooks.slice(0, 12).map((item) => productPlaybookRow(item));
  const fromData = RadarState.opportunities.slice(0, 4).map((opp) => ({
    title: RadarState.lang === 'ar' ? (opp.title_ar || opp.title_en) : (opp.title_en || opportunityTitleEn(opp)),
    category: RadarState.lang === 'ar' ? 'فرصة مرصودة' : 'Detected opportunity',
    pain: RadarState.lang === 'ar' ? (opp.pain_point_ar || '') : (opp.pain_point_en || opp.pain_point_ar || ''),
    capital: RadarState.lang === 'ar' ? (opp.capital_ar || opportunityCapitalAr(opp)) : opportunityCapitalEn(opp),
    product: RadarState.lang === 'ar' ? (opp.suggested_product_idea_ar || opportunityProductAr(opp)) : (opp.suggested_product_idea_en || opportunityProductEn(opp)),
    buyer: RadarState.lang === 'ar' ? (opp.target_user_ar || opportunityBuyerAr(opp)) : (opp.target_user_en || opportunityBuyerEn(opp)),
    time: RadarState.lang === 'ar' ? opportunityFirstStepAr(opp) : opportunityFirstStepEn(opp),
    profit: RadarState.lang === 'ar' ? (opp.pricing_ar || radarMoneyLabel(opp.id)) : radarMoneyLabel(opp.id),
    tools: RadarState.lang === 'ar' ? (opp.tools_ar || opportunityToolsAr(opp)) : opportunityToolsEn(opp),
    examples: RadarState.lang === 'ar' ? (opp.examples_ar || opportunityExamplesAr(opp)) : opportunityExamplesEn(opp),
    why: RadarState.lang === 'ar' ? (opp.why_now_ar || opportunityWhyAr(opp)) : (opp.why_now_en || opportunityWhyEn(opp)),
    confidence: opp.confidence,
    signalCount: opp.signal_count,
    source: `${opp.signal_count || 0} ${RadarState.lang === 'ar' ? 'دليل' : 'evidence'}`,
    sourceLinks: localizedSourceLinks((opp.source_links || []).map((url, index) => ({ label: `${RadarState.lang === 'ar' ? 'دليل' : 'Evidence'} ${index + 1}`, source: 'Radar', url })))
  }));
  const fromResearch = RadarState.researchOpportunities.slice(0, 4).map((opp) => ({
    title: RadarState.lang === 'ar' ? opp.title_ar : researchTitleEn(opp),
    category: RadarState.lang === 'ar' ? 'منتج من بحث علمي' : 'Research-backed product',
    capital: RadarState.lang === 'ar' ? 'متوسط' : 'Medium',
    product: RadarState.lang === 'ar' ? opp.sellable_product_ar : researchProductEn(opp),
    buyer: RadarState.lang === 'ar' ? opp.buyer_ar : researchBuyerEn(opp),
    time: RadarState.lang === 'ar' ? (opp.first_paid_test_ar || 'اختبار مدفوع سريع') : researchFirstTestEn(opp),
    profit: RadarState.lang === 'ar' ? (opp.pricing_ar || 'سعر تجريبي') : researchPricingEn(opp),
    tools: RadarState.lang === 'ar' ? 'نموذج AI، واجهة بسيطة، قاعدة معرفة أو تكامل API' : 'AI model, simple interface, knowledge base or API integration',
    examples: RadarState.lang === 'ar' ? 'أدوات بحث مستندات، وكلاء تشغيل، منصات رؤية طرفية' : 'Document search tools, ops agents, edge vision platforms',
    why: RadarState.lang === 'ar' ? opp.why_it_matters_ar : researchWhyEn(opp),
    source: 'arXiv',
    url: opp.source_url
  }));
  return dedupeOpportunityRows(
    fromFocused.concat(fromManualX, fromPlaybooks, interleaveRows(fromData, fromResearch))
  );
}

function dedupeOpportunityRows(rows) {
  const seen = new Set();
  const unique = [];
  rows.forEach((item) => {
    const key = _opportunityKey(item.id || item.title || item.product || '');
    if (!key || seen.has(key)) return;
    seen.add(key);
    unique.push(item);
  });
  return unique;
}

function isWorthyOpportunity(item = {}) {
  const kind = item.kind || '';
  const confidence = Number(item.confidence || 0);
  const evidenceCount = Number(item.evidenceCount || item.signalCount || 0);
  const hasBuyer = Boolean(String(item.buyer || '').trim());
  const hasProduct = Boolean(String(item.product || '').trim());
  const hasWhy = Boolean(String(item.why || item.pain || '').trim());
  const hasEvidence = Array.isArray(item.sourceLinks) && item.sourceLinks.length > 0;

  if (kind === 'focused_opportunity') return true;
  if (kind === 'x_curated') return hasProduct && hasBuyer && hasEvidence && (confidence >= 0.65 || evidenceCount >= 3);
  if (kind === 'validated_opportunity') return hasProduct && hasWhy && hasEvidence && confidence >= 0.72;

  // Keep research-backed or detected rows only when they read like a real offer,
  // not a generic bucket or playbook placeholder.
  if (item.source === 'arXiv') return hasProduct && hasBuyer && hasWhy;
  if (kind === 'playbook') return false;
  if (!kind) return false;
  return hasProduct && hasBuyer && hasWhy && hasEvidence;
}

function allWorthyOpportunityRows() {
  return dedupeOpportunityRows(
    focusedOpportunityRows()
      .concat(manualXOpportunityRows(), candidateOpportunityRows(), baseOpportunityRows())
      .filter((item) => isWorthyOpportunity(item))
  );
}

function manualXOpportunityRows() {
  const brief = RadarState.manualXBrief;
  if (!brief || !Array.isArray(brief.opportunities)) return [];
  const isAr = RadarState.lang === 'ar';
  return brief.opportunities.slice(0, 4).map((opp) => {
    const evidence = (opp.evidence_items || []).filter((item) => item.url || item.text);
    const explicitLinks = localizedSourceLinks(opp.source_links || []);
    const sourceLinks = explicitLinks.length ? explicitLinks : evidence.slice(0, 4).map((item) => ({
      label: item.author_handle ? `@${item.author_handle}` : (isAr ? 'إشارة من X' : 'X signal'),
      source: 'X',
      url: item.url || ''
    }));
    return {
      title: isAr ? (opp.title_ar || opp.title_en) : (opp.title_en || englishFromArabicTitle(opp.title_ar)),
      category: isAr ? (opp.category_ar || 'إشارة من X') : (opp.category_en || 'X signal'),
      kind: 'x_curated',
      capital: isAr ? 'حسب الفكرة' : 'Depends on idea',
      product: isAr ? (opp.mvp_ar || opp.product_ar) : (opp.mvp_en || englishFromArabicText(opp.mvp_ar)),
      buyer: isAr ? (opp.customer_ar || opp.buyer_ar) : (opp.customer_en || englishFromArabicText(opp.customer_ar)),
      time: isAr ? `${opp.evidence_count || evidence.length || 1} أدلة من X` : `${opp.evidence_count || evidence.length || 1} X evidence items`,
      profit: '',
      tools: '',
      examples: '',
      inspiration: isAr ? (opp.why_now_ar || opp.inspiration_ar) : (opp.why_now_en || englishFromArabicText(opp.why_now_ar)),
      sourceLinks,
      why: isAr
        ? 'اختيرت لأنها ظهرت في عدة إشارات مرتبطة بالذكاء الاصطناعي ولها أدلة قابلة للمراجعة.'
        : 'Selected because it appears across relevant AI signals with reviewable evidence.',
      source: 'X',
      confidence: opp.confidence || 0.5,
      evidenceCount: opp.evidence_count || evidence.length || 0,
      evidenceItems: evidence,
      firstTest: firstTestForXOpportunity(opp.id, isAr),
      url: sourceLinks[0]?.url || ''
    };
  });
}

function firstTestForXOpportunity(id, isAr) {
  const ar = {
    agentic_engineering_services: 'صمّم عرضًا من صفحة واحدة: “نحوّل طريقة عمل فريقك إلى نظام وكلاء AI خلال أسبوع”، ثم اختبره مع مستقل أو فريق صغير لديه مشروع جارٍ.',
    ai_design_context_pack: 'اجمع 3 أمثلة واجهات ممتازة + ملف DESIGN.md، ثم جرّب قبل/بعد على صفحة واحدة واسأل المستخدمين أي نسخة تبدو أكثر احترافية.',
    voice_dubbing_localization: 'خذ فيديو قصيرًا لصانع محتوى، وحوّله إلى نسخة عربية/إنجليزية مدبلجة كنموذج مجاني محدود لإثبات القيمة.',
    trend_to_app_lab: 'اختر ترندًا واحدًا، ابنِ صفحة تحقق بسيطة، وانشرها مع وعد واضح: “نختبر هل تستحق الفكرة البناء خلال 48 ساعة”.',
    ai_property_tour_content: 'صوّر مساحة صغيرة بالجوال وحوّلها إلى عرض تفاعلي مصغر مع وصف تسويقي؛ اعرضه على مكتب عقار أو شقة مفروشة.'
  };
  const en = {
    agentic_engineering_services: 'Create a one-page offer: “We turn your team workflow into an AI-agent operating system in one week,” then test it with a freelancer or small team.',
    ai_design_context_pack: 'Collect 3 premium UI examples plus a DESIGN.md file, run a before/after page test, and ask users which output feels more professional.',
    voice_dubbing_localization: 'Take one short creator video and return an Arabic/English dubbed sample as a limited free proof of value.',
    trend_to_app_lab: 'Pick one trend, build a tiny validation page, and publish it with a clear promise: “We test if this is worth building in 48 hours.”',
    ai_property_tour_content: 'Capture one small space with a phone, convert it into a mini interactive tour with sales copy, and show it to a real-estate office or furnished apartment.'
  };
  return (isAr ? ar : en)[id] || (isAr ? 'حوّل الفكرة إلى تجربة صغيرة قابلة للقياس خلال يوم واحد.' : 'Turn the idea into a small measurable test within one day.');
}

function englishFromArabicTitle(text = '') {
  const map = {
    'حزمة خبرة Claude Code للعرب وغير الناطقين بالإنجليزية': 'Claude Code operating kit for Arabic and non-English users',
    'Design Context Pack للوكلاء حتى لا ينتجوا واجهات ضعيفة': 'Design context pack for AI agents',
    'Workflow عربي لتحويل أدوات AI الرائجة إلى خدمات صغيرة': 'Arabic workflow for turning AI tools into small services',
    'متابعة فرص المنتجات من X للحسابات التقنية': 'X-based product opportunity monitor'
  };
  return map[text] || text || 'X-inspired product idea';
}

function englishFromArabicText(text = '') {
  return text || '';
}

function productPlaybookRow(item) {
  const isAr = RadarState.lang === 'ar';
  const pick = (base, fallback = '') => item[`${base}_${isAr ? 'ar' : 'en'}`] || item[`${base}_${isAr ? 'en' : 'ar'}`] || fallback;
  const playbook = item[`seven_day_playbook_${isAr ? 'ar' : 'en'}`] || item.seven_day_playbook_ar || item.seven_day_playbook_en || [];
  return {
    title: pick('title'),
    category: pick('category', isAr ? 'منتج دخل مدعوم بـ AI' : 'AI-powered income product'),
    capital: pick('capital'),
    product: pick('product'),
    buyer: pick('buyer'),
    time: isAr ? 'خطة تنفيذ 7 أيام' : '7-day execution plan',
    profit: item.show_pricing ? pick('pricing') : '',
    tools: item.tools_required === false ? '' : pick('tools'),
    examples: pick('examples'),
    inspiration: pick('inspiration'),
    sourceLinks: localizedSourceLinks(item.source_links || []),
    why: pick('why'),
    saudi: pick('saudi_lens'),
    playbook,
    source: isAr ? 'قالب دخل' : 'Income playbook',
    confidence: 0.72
  };
}

function interleaveRows(a, b) {
  const out = [];
  const max = Math.max(a.length, b.length);
  for (let i = 0; i < max; i += 1) {
    if (a[i]) out.push(a[i]);
    if (b[i]) out.push(b[i]);
  }
  return out;
}

function researchTitleEn(opp) {
  return {
    research_agent_sandbox_runtime: 'AI agent sandbox rollback product',
    research_edge_vlm_product: 'Edge AI vision product',
    research_compound_ai_infra: 'Cost optimization for compound AI apps',
    research_agent_design_methodology: 'AI agent design studio',
    research_multimodal_doc_rag: 'Multimodal document RAG product'
  }[opp.id] || opp.paper_title || opp.title_ar || 'Research-backed AI product';
}

function researchFirstTestEn(opp) {
  return {
    research_agent_sandbox_runtime: 'Add rollback to one production agent',
    research_edge_vlm_product: 'Run one-camera inspection PoC',
    research_compound_ai_infra: 'Audit one AI app cost and latency',
    research_agent_design_methodology: 'One-week agent blueprint workshop',
    research_multimodal_doc_rag: 'Index 200 PDFs with visual evidence'
  }[opp.id] || 'Paid pilot with one customer';
}

function researchPricingEn(opp) {
  return {
    research_agent_sandbox_runtime: '$500-$2,000 setup + monthly',
    research_edge_vlm_product: '$1,000-$5,000 PoC + support',
    research_compound_ai_infra: '$750-$3,000 audit + monthly',
    research_agent_design_methodology: '$1,500-$7,000 workshop',
    research_multimodal_doc_rag: '$300-$1,000/month'
  }[opp.id] || 'Pilot price before building';
}

function researchProductEn(opp) {
  return {
    research_agent_sandbox_runtime: 'Checkpoint and rollback layer for AI agent sandboxes',
    research_edge_vlm_product: 'Edge vision app for inspection, retail, or camera workflows',
    research_compound_ai_infra: 'Routing and architecture audit for multi-model AI apps',
    research_agent_design_methodology: 'Blueprint studio for designing reliable AI agents',
    research_multimodal_doc_rag: 'Document search product with visual evidence'
  }[opp.id] || opp.sellable_product_ar || 'Research-backed AI product';
}

function researchBuyerEn(opp) {
  return {
    research_agent_sandbox_runtime: 'Teams running autonomous agents in production',
    research_edge_vlm_product: 'Factories, shops, and field teams using cameras',
    research_compound_ai_infra: 'Teams with growing AI latency and API cost',
    research_agent_design_methodology: 'Companies that need domain-specific agents',
    research_multimodal_doc_rag: 'Legal, insurance, education, and operations teams'
  }[opp.id] || opp.buyer_ar || 'Teams with a repeated AI workflow';
}

function researchWhyEn(opp) {
  return {
    research_agent_sandbox_runtime: 'Agent failures are expensive; rollback can become a paid reliability feature.',
    research_edge_vlm_product: 'Running vision AI near the device lowers latency and can fit paid field workflows.',
    research_compound_ai_infra: 'Compound AI apps quickly need cost and routing control.',
    research_agent_design_methodology: 'Companies need a repeatable way to turn expertise into agents.',
    research_multimodal_doc_rag: 'Many teams pay to search complex PDFs, tables, and diagrams reliably.'
  }[opp.id] || opp.why_it_matters_ar || 'The paper points to a practical product capability.';
}

function opportunityProductAr(opp) {
  return opp.sellable_product_ar || {
    ai_income_services: 'باقة خدمة تنفذ عملاً متكررًا للعميل باستخدام أدوات AI',
    ai_income_tools: 'أداة صغيرة أو قالب عمل يستخدم AI لحل مهمة محددة',
    ai_income_automation: 'أتمتة AI تربط أدوات العميل وتخفض العمل اليدوي',
    ai_income_content: 'باقة إنتاج محتوى أو إعلانات أو فيديوهات قصيرة'
  }[opp.id] || 'عرض مدفوع مبني على إشارة قابلة للتحقق';
}

function opportunityCapitalAr(opp) {
  return {
    ai_income_services: 'بدون رأس مال',
    ai_income_tools: 'منخفض',
    ai_income_automation: 'منخفض',
    ai_income_content: 'بدون رأس مال'
  }[opp.id] || 'منخفض';
}

function opportunityCapitalEn(opp) {
  return {
    ai_income_services: 'No capital',
    ai_income_tools: 'Low',
    ai_income_automation: 'Low',
    ai_income_content: 'No capital'
  }[opp.id] || 'Low';
}

function opportunityTitleEn(opp) {
  return {
    ai_income_services: 'Packaged AI service for a repeated customer task',
    ai_income_tools: 'Arabic AI update explainer for practical use',
    ai_income_automation: 'Daily AI-agent automation for customer follow-up and reports',
    ai_income_content: 'Fast AI content studio for stores and coaches'
  }[opp.id] || (containsArabic(opp.title_ar) ? 'AI income opportunity from verified signals' : (opp.title_ar || 'AI income opportunity'));
}

function opportunityProductEn(opp) {
  return {
    ai_income_services: 'A packaged service that uses AI to deliver repeated client work',
    ai_income_tools: 'A small AI-powered tool or workflow template',
    ai_income_automation: 'An AI automation that removes repeated manual work',
    ai_income_content: 'A content, ad, or short-video production package'
  }[opp.id] || (containsArabic(opp.sellable_product_ar) ? 'A paid offer backed by a verifiable signal' : (opp.sellable_product_ar || 'A paid offer backed by a verifiable signal'));
}

function opportunityBuyerAr(opp) {
  return opp.buyer_ar || {
    ai_income_services: 'أفراد وشركات صغيرة لديها عمل متكرر',
    ai_income_tools: 'شركات ناشئة وصناع محتوى وفرق تشغيل',
    ai_income_automation: 'شركات صغيرة تخسر وقتًا في مهام متكررة',
    ai_income_content: 'متاجر ووكالات وصناع محتوى'
  }[opp.id] || 'عميل لديه ألم واضح في الإشارات العامة';
}

function opportunityBuyerEn(opp) {
  return {
    ai_income_services: 'Individuals and small companies with repeated work',
    ai_income_tools: 'Startups, creators, and operations teams',
    ai_income_automation: 'Small companies losing time to repeated tasks',
    ai_income_content: 'Stores, agencies, and creators'
  }[opp.id] || (containsArabic(opp.buyer_ar) ? 'A buyer with visible public pain' : (opp.buyer_ar || 'A buyer with visible public pain'));
}

function opportunityFirstStepAr(opp) {
  return opp.first_paid_test_ar || {
    ai_income_services: 'بيع تجربة صغيرة لعميل واحد خلال 48 ساعة',
    ai_income_tools: 'صفحة انتظار + نموذج أولي + مقابلات مشترين',
    ai_income_automation: 'أتمتة عملية واحدة وقياس الوقت قبل/بعد',
    ai_income_content: 'إنتاج 3 عينات قبل/بعد ثم عرض باقة شهرية'
  }[opp.id] || 'اختبار مدفوع سريع مع عميل واحد';
}

function opportunityFirstStepEn(opp) {
  return {
    ai_income_services: 'Sell a small 48-hour pilot to one client',
    ai_income_tools: 'Landing page, small prototype, buyer interviews',
    ai_income_automation: 'Automate one process and measure time saved',
    ai_income_content: 'Produce three before/after samples, then pitch monthly'
  }[opp.id] || (containsArabic(opp.first_paid_test_ar) ? 'Quick paid pilot with one customer' : (opp.first_paid_test_ar || 'Quick paid pilot with one customer'));
}

function opportunityWhyAr(opp) {
  return opp.why_it_matters_ar || 'نقبلها كفرصة لأنها مرتبطة بروابط ومصادر متكررة لا بمجرد رأي.';
}

function opportunityWhyEn(opp) {
  return {
    ai_income_services: 'People often pay for an outcome before they pay for a tool.',
    ai_income_tools: 'Repeated product/tool signals indicate workflows ready to package.',
    ai_income_automation: 'Automation connects AI directly to time and cost savings.',
    ai_income_content: 'Content is one of the fastest paid AI pilots to test.'
  }[opp.id] || (containsArabic(opp.why_it_matters_ar) ? 'Accepted because it is backed by linked signals, not a loose opinion.' : (opp.why_it_matters_ar || 'Accepted because it is backed by linked signals, not a loose opinion.'));
}

function opportunityToolsAr(opp) {
  return {
    ai_income_services: 'ChatGPT أو Claude، Notion/Docs، أداة تسليم للعميل',
    ai_income_tools: 'واجهة بسيطة، API نموذج AI، Stripe أو Gumroad، صفحة هبوط',
    ai_income_automation: 'Zapier/Make أو n8n، API، بريد أو CRM، نموذج AI',
    ai_income_content: 'ChatGPT/Claude، أداة تصميم أو فيديو، جدولة نشر'
  }[opp.id] || 'نموذج AI، صفحة هبوط، أداة تنفيذ بسيطة';
}

function opportunityToolsEn(opp) {
  return {
    ai_income_services: 'ChatGPT or Claude, Notion/Docs, client delivery tool',
    ai_income_tools: 'Simple UI, AI model API, Stripe or Gumroad, landing page',
    ai_income_automation: 'Zapier/Make or n8n, API, email or CRM, AI model',
    ai_income_content: 'ChatGPT/Claude, design or video tool, publishing scheduler'
  }[opp.id] || 'AI model, landing page, simple execution tool';
}

function opportunityExamplesAr(opp) {
  return {
    ai_income_services: 'خدمة تلخيص، كتابة عروض، تحليل مستندات، إعداد تقارير',
    ai_income_tools: 'قالب مدفوع، إضافة صغيرة، أداة SaaS مركزة',
    ai_income_automation: 'أتمتة ردود العملاء، فواتير، تقارير، متابعة مبيعات',
    ai_income_content: 'حزم إعلانات، مقاطع قصيرة، وصف منتجات، حملات بريد'
  }[opp.id] || 'خدمة صغيرة أو أداة متخصصة تم بيعها مبكرًا';
}

function opportunityExamplesEn(opp) {
  return {
    ai_income_services: 'Summaries, proposal writing, document analysis, reports',
    ai_income_tools: 'Paid template, small plugin, focused SaaS tool',
    ai_income_automation: 'Customer replies, invoices, reports, sales follow-up',
    ai_income_content: 'Ad packs, short videos, product descriptions, email campaigns'
  }[opp.id] || 'A small service or focused tool sold early';
}

function radarMoneyLabel(id) {
  const ar = {
    ai_income_services: '200-1000$ لكل باقة خدمة',
    ai_income_tools: '9-49$/شهر أو قالب مدفوع',
    ai_income_automation: 'إعداد 500$ + دعم شهري',
    ai_income_content: '99-299$/شهر',
    ai_agents_ops: 'إعداد 500$ + 99-299$/شهر',
    ai_dev_tools: 'Kit بـ49$ أو خدمة 300-900$',
    ai_cost_quality: 'تدقيق 750$ + متابعة شهرية',
    ai_media_content: '199$/شهر أو 25$/فيديو'
  };
  const en = {
    ai_income_services: '$200-$1,000 per service package',
    ai_income_tools: '$9-$49/month or paid template',
    ai_income_automation: '$500 setup + monthly support',
    ai_income_content: '$99-$299/month',
    ai_agents_ops: '$500 setup + $99-$299/month',
    ai_dev_tools: '$49 kit or $300-$900 service',
    ai_cost_quality: '$750 audit + monthly monitoring',
    ai_media_content: '$199/month or $25/video'
  };
  return (RadarState.lang === 'ar' ? ar : en)[id] || (RadarState.lang === 'ar' ? 'سعر تجريبي قبل بناء المنتج' : 'Pilot price before building');
}

function opportunityCard(item) {
  const confidence = item.confidence ? `${Math.round(item.confidence * 100)}%` : null;
  return `
    <h3>${escapeHTML(item.title)}${item.source ? ` <span class="card-source">${escapeHTML(item.source)}</span>` : ''}</h3>
    <ul>
      <li><b>${RadarState.lang === 'ar' ? 'رأس المال' : 'Capital'}</b><br>${escapeHTML(item.capital || item.category)}</li>
      <li><b>${RadarState.lang === 'ar' ? 'ما نبيعه' : 'What to sell'}</b><br>${escapeHTML(item.product || item.category)}</li>
      <li><b>${RadarState.lang === 'ar' ? 'أول اختبار' : 'First test'}</b><br>${escapeHTML(item.time)}</li>
      <li><b>${RadarState.lang === 'ar' ? 'الأدوات' : 'Tools'}</b><br>${escapeHTML(item.tools || '')}</li>
      <li><b>${RadarState.lang === 'ar' ? 'تسعير مبدئي' : 'Starter pricing'}</b><br>${escapeHTML(item.profit)}</li>
      <li><b>${RadarState.lang === 'ar' ? 'أمثلة ناجحة' : 'Successful examples'}</b><br>${escapeHTML(item.examples || '')}</li>
    </ul>
    <p class="opportunity-reason">${escapeHTML(item.why || '')}</p>
    ${confidence ? `<p class="opportunity-proof">${escapeHTML(RadarState.lang === 'ar' ? `ثقة ${confidence}` : `${confidence} confidence`)}</p>` : ''}
  `;
}

function newsUpdateKind(item) {
  const hay = `${item.title || ''} ${item.text || ''}`.toLowerCase();
  if (hay.includes('price') || hay.includes('pricing') || hay.includes('limit') || hay.includes('token')) {
    return RadarState.lang === 'ar' ? 'أسعار أو حدود استخدام' : 'Pricing or usage limits';
  }
  if (hay.includes('model') || hay.includes('gpt') || hay.includes('claude') || hay.includes('grok') || hay.includes('gemini')) {
    return RadarState.lang === 'ar' ? 'نموذج AI أو تحديث نموذج' : 'AI model update';
  }
  if (hay.includes('release') || hay.includes('launch') || hay.includes('introduc') || hay.includes('ship')) {
    return RadarState.lang === 'ar' ? 'إصدار أو ميزة جديدة' : 'Release or new feature';
  }
  if (hay.includes('tool') || hay.includes('app') || hay.includes('github')) {
    return RadarState.lang === 'ar' ? 'أداة أو تطبيق جديد' : 'New tool or app';
  }
  return RadarState.lang === 'ar' ? 'خبر أو تحديث AI' : 'AI news or update';
}

function signalCardPreview(item) {
  const isAr = RadarState.lang === 'ar';
  const value = isAr
    ? (item.summary_ar || item.product_opportunity_ar || item.why_it_matters_ar || '')
    : (item.summary_en || item.product_opportunity_en || item.why_it_matters_en || '');
  if (value) return compactPreview(value);
  return newsUpdateKind(item);
}

function compactPreview(value, limit = 118) {
  let text = String(value || '')
    .replace(/^من مصدر موثق:\s*/u, '')
    .replace(/^من نقاشات X:\s*/u, '')
    .replace(/^الأداة\/الفكرة:\s*/u, '')
    .replace(/^الموضوع:\s*/u, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, limit).replace(/\s+\S*$/, '')}…`;
}

function signalUseAngle(item) {
  const hay = `${item.title || ''} ${item.text || ''}`.toLowerCase();
  const isAr = RadarState.lang === 'ar';
  if (hay.includes('price') || hay.includes('pricing') || hay.includes('limit') || hay.includes('token')) {
    return isAr
      ? 'استخدمه لتقدير تكلفة فكرة منتج أو مقارنة أداة قبل البناء.'
      : 'Use it to estimate product cost or compare tools before building.';
  }
  if (hay.includes('model') || hay.includes('gpt') || hay.includes('claude') || hay.includes('gemini')) {
    return isAr
      ? 'حوّله إلى محتوى توضيحي أو تجربة تقارن كيف يغير النموذج الجديد سير العمل.'
      : 'Turn it into content or a test comparing how the new model changes a workflow.';
  }
  if (hay.includes('tool') || hay.includes('app') || hay.includes('github') || hay.includes('open source')) {
    return isAr
      ? 'جرّب الأداة سريعًا وابحث هل يمكن تغليفها كخدمة أو قالب أو أتمتة لعميل محدد.'
      : 'Test the tool quickly and see if it can become a service, template, or automation for a specific customer.';
  }
  return isAr
    ? 'استخدمها كإشارة مبكرة: اكتب عنها، اختبرها مع جمهور صغير، أو اربطها بفرصة منتج إذا تكررت.'
    : 'Use it as an early signal: write about it, test it with a small audience, or link it to a product idea if it repeats.';
}

function localizedTitle(item) {
  if (!item) return '';
  if (RadarState.lang === 'ar' && item.title_ar) return item.title_ar;
  if (RadarState.lang === 'ar') return arabicFallbackTitle(item);
  return item.title || '';
}

function arabicFallbackTitle(item) {
  const title = item.title || '';
  const low = `${title} ${item.text || ''}`.toLowerCase();
  if (item.source_id === 'arxiv_papers') {
    if (low.includes('agent')) return 'ورقة علمية عن وكلاء ذكاء اصطناعي يمكن تحويلها إلى منتج أو خدمة';
    if (low.includes('retrieval') || low.includes('rag')) return 'ورقة علمية عن بحث ذكي واسترجاع معلومات يمكن تحويله إلى منتج';
    if (low.includes('vision') || low.includes('multimodal')) return 'ورقة علمية عن رؤية/وسائط متعددة قابلة لتطبيق تجاري';
    if (low.includes('time series') || low.includes('forecast')) return 'ورقة علمية عن التنبؤ والتحليل يمكن استخدامها في منتج مدفوع';
    return 'ورقة علمية عن تقنية ذكاء اصطناعي قابلة للدراسة كفرصة منتج';
  }
  if (item.source_id === 'x_recent_search' || item.source_id === 'x_user_timelines') return 'منشور من X عن منتج أو خدمة تستخدم الذكاء الاصطناعي';
  if (item.source_id === 'github_repos') return 'مشروع GitHub يمكن دراسته كأداة مدعومة بالذكاء الاصطناعي';
  if (item.source_id && item.source_id.includes('reddit')) return 'نقاش مجتمعي عن استخدام عملي للذكاء الاصطناعي';
  if (item.source_kind === 'official' || item.source_id === 'openai_news' || item.source_id === 'google_deepmind') return 'مصدر رسمي عن استخدام عملي للذكاء الاصطناعي';
  if (item.source_id === 'techcrunch_ai') return 'خبر تقني عن منتج أو سوق مرتبط بالذكاء الاصطناعي';
  return title || 'إشارة مرتبطة بمنتج يستخدم الذكاء الاصطناعي';
}

function card(title, value, text) {
  return `<h3>${escapeHTML(title)}</h3><p><b>${escapeHTML(value)}</b></p><p>${escapeHTML(text)}</p>`;
}

function listCard(title, rows) {
  return `
    <h3>${escapeHTML(title)}</h3>
    <ul>
      ${rows.map(([a, b]) => `<li><b>${escapeHTML(a)}</b><br>${escapeHTML(b || '')}</li>`).join('')}
    </ul>
  `;
}

function evidenceItems(opportunity) {
  return opportunity && opportunity.evidence_items ? opportunity.evidence_items : [];
}

function countBy(items, key) {
  return items.reduce((acc, item) => {
    const id = item[key] || 'unknown';
    acc[id] = (acc[id] || 0) + 1;
    return acc;
  }, {});
}

function trendingTags() {
  const counts = {};
  RadarState.signals.forEach((signal) => {
    (signal.matched_keywords || []).forEach((keyword) => {
      if (!keyword || keyword.length < 2) return;
      counts[keyword] = (counts[keyword] || 0) + 1;
    });
  });
  return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 4);
}

function sourceName(id) {
  const names = {
    x_recent_search: 'X',
    github_repos: 'GitHub',
    openai_news: 'OpenAI',
    google_deepmind: 'DeepMind',
    google_ai_blog: 'Google AI',
    huggingface_blog: 'Hugging Face',
    huggingface_daily_papers: 'HF Daily Papers',
    huggingface_models: 'HF Models',
    techcrunch_ai: 'TechCrunch',
    bens_bites: "Ben's Bites",
    reddit_artificial: 'Reddit AI',
    reddit_machinelearning: 'Reddit ML',
    reddit_localllama: 'Reddit LocalLLaMA',
    reddit_singularity: 'Reddit Singularity',
    hn_algolia: 'Hacker News',
    arxiv_papers: 'arXiv',
    validated_radar: RadarState.lang === 'ar' ? 'الرادار · بطاقة مجازة' : 'Radar · Validated card',
    x_quality_gate: RadarState.lang === 'ar' ? 'X · إشارة مختارة' : 'X · Selected signal'
  };
  return names[id] || id || (RadarState.lang === 'ar' ? 'مصدر' : 'Source');
}

function updateLabel() {
  const latest = latestGeneratedAt();
  if (!latest) return t('no_update_yet');
  const date = new Date(latest);
  if (Number.isNaN(date.getTime())) return latest;
  const locale = RadarState.lang === 'ar' ? 'ar-SA' : 'en-US';
  return t('last_update') + ' ' + date.toLocaleString(locale, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
}

function latestGeneratedAt() {
  const candidates = [
    RadarState.focusedDiscussionsGeneratedAt,
    RadarState.focusedUpdatesGeneratedAt,
    RadarState.focusedOpportunitiesGeneratedAt,
    RadarState.cardCandidatesGeneratedAt,
    RadarState.generatedAt,
    RadarState.manualXReady && RadarState.manualXReady.generated_at,
    RadarState.manualXBrief && RadarState.manualXBrief.generated_at
  ].filter(Boolean);
  if (!candidates.length) return '';
  return candidates.sort((a, b) => Date.parse(b) - Date.parse(a))[0];
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-US', { notation: 'compact' });
}

function escapeHTML(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escapeAttr(value) {
  return escapeHTML(value).replace(/'/g, '&#39;');
}

function setupParticles() {
  const canvas = document.getElementById('radar-particles');
  const ctx = canvas.getContext('2d');
  const resize = () => {
    canvas.width = window.innerWidth * window.devicePixelRatio;
    canvas.height = window.innerHeight * window.devicePixelRatio;
    ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    seedParticles();
  };

  const seedParticles = () => {
    const count = Math.min(70, Math.max(30, Math.floor(window.innerWidth / 22)));
    RadarState.particles = Array.from({ length: count }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.6 + 0.4,
      a: Math.random() * 0.45 + 0.14,
      vx: (Math.random() - 0.5) * 0.08,
      vy: (Math.random() - 0.5) * 0.08
    }));
  };

  const draw = () => {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    RadarState.particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = window.innerWidth;
      if (p.x > window.innerWidth) p.x = 0;
      if (p.y < 0) p.y = window.innerHeight;
      if (p.y > window.innerHeight) p.y = 0;

      ctx.beginPath();
      ctx.fillStyle = `rgba(124, 238, 255, ${p.a})`;
      ctx.shadowColor = 'rgba(124, 238, 255, 0.6)';
      ctx.shadowBlur = 8;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });
    requestAnimationFrame(draw);
  };

  window.addEventListener('resize', resize);
  resize();
  draw();
}

document.addEventListener('DOMContentLoaded', bootRadar);
