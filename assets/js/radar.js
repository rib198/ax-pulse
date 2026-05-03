const RadarState = {
  layer: 'radar',
  lang: localStorage.getItem('axp_lang') || 'ar',
  signals: [],
  corpusSignals: [],
  timeline: [],
  opportunities: [],
  productPlaybooks: [],
  researchOpportunities: [],
  accounts: [],
  generatedAt: null,
  particles: [],
  tickerTimer: null,
  refreshTimer: null,
  timelineAutoTimer: null,
  timelinePauseTimer: null,
  activeTimelineIndex: 0,
  autoTimelinePaused: false,
  knownSignalIds: new Set(),
  lastLiveItems: [],
  archiveExpanded: false
};

const LAYERS = {
  radar: {
    title: { ar: 'رادار الذكاء الاصطناعي', en: 'AI Radar' },
    summary: {
      ar: 'News + Updates: تحديثات يومية ولحظية عن نماذج AI، الإصدارات الجديدة، الأدوات، الميزات، الأسعار، حدود الاستخدام، والروابط الرسمية.',
      en: 'News + Updates: daily and live updates on AI models, releases, tools, features, pricing, limits, and official links.'
    }
  },
  trending: {
    title: { ar: 'الرائج في X عن الذكاء الاصطناعي', en: 'Trending AI conversations on X' },
    summary: {
      ar: 'تعليقات ومنشورات الناس عن مواضيع الذكاء الاصطناعي ذات التفاعل الكبير، لالتقاط المزاج العام وما يجذب الانتباه.',
      en: 'High-engagement public conversations about AI, used to detect attention, objections, and market curiosity.'
    }
  },
  opportunities: {
    title: { ar: 'ابتكار المنتجات المدعومة بالذكاء الاصطناعي وزد دخلك', en: 'Invent AI-powered products and grow income' },
    summary: {
      ar: 'فرص مرتبة حسب رأس المال المطلوب، مع وصف، خطوات تنفيذ، أدوات مطلوبة، تقدير ربح، وأمثلة نجاح قابلة للدراسة.',
      en: 'Income opportunities organized by required capital, with description, execution steps, tools, profit estimate, and successful examples.'
    }
  },
  sources: {
    title: { ar: 'مصادر الإشارات', en: 'Signal sources' },
    summary: {
      ar: 'مصادر الأخبار والتحديثات: مواقع رسمية، X، GitHub، Reddit، arXiv، Hugging Face، ومصادر مجانية موثوقة.',
      en: 'News and update sources: official sites, X, GitHub, Reddit, arXiv, Hugging Face, and trusted free sources.'
    }
  },
  signals: {
    title: { ar: 'بث الإشارات الحية', en: 'Live signal stream' },
    summary: {
      ar: 'آخر الإشارات الخام التي وصلت للرادار قبل تحويلها إلى أخبار أو رائج أو فرص منتجات.',
      en: 'Latest raw signals before they are shaped into news, trends, or product opportunities.'
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
  nav_radar: { ar: 'الرادار', en: 'Radar' },
  nav_trending: { ar: 'الرائج', en: 'Trending' },
  nav_opportunities: { ar: 'المنتجات والدخل', en: 'Products & income' },
  nav_sources: { ar: 'المصادر', en: 'Sources' },
  nav_signals: { ar: 'إشارات', en: 'Signals' },
  // Footer / portrait
  dashboard_link: { ar: 'لوحة التحكم', en: 'Dashboard' },
  loading_data: { ar: 'جارٍ تحميل البيانات...', en: 'Loading data...' },
  rotate_phone_h1: { ar: 'لفّي الهاتف', en: 'Rotate your phone' },
  rotate_phone_p: {
    ar: 'تجربة الرادار مصممة للعمل بالعرض حتى تبقى الأرض والبيانات واضحة.',
    en: 'The radar experience is designed in landscape so the globe and data stay clear.'
  }
};

const FALLBACK_TAGS = ['Claude', 'Codex', 'Cursor', 'Agents', 'OpenAI', 'GitHub', 'MCP', 'LLM'];

const DEFAULT_TRENDS = [
  { ar: 'نقاشات X حول وكلاء الذكاء الاصطناعي', en: 'X conversations around AI agents' },
  { ar: 'تفاعل مرتفع حول أدوات توليد الفيديو', en: 'High engagement around AI video tools' },
  { ar: 'انتقادات وتجارب المستخدمين مع أدوات AI', en: 'User reactions and objections around AI tools' },
  { ar: 'أسئلة الناس عن الربح باستخدام AI', en: 'Public questions about making income with AI' },
  { ar: 'مقارنات النماذج والأدوات في المنشورات المتداولة', en: 'Viral model and tool comparisons' }
];

const DEFAULT_OPPORTUNITIES = [
  { title: { ar: 'منتج متابعة اجتماعات مدعوم بـ AI', en: 'AI-powered meeting follow-up product' }, category: { ar: 'منتج SaaS', en: 'SaaS product' }, time: { ar: '3 أيام MVP', en: '3-day MVP' }, profit: { ar: 'اشتراك 19-49$/مستخدم' , en: '$19-$49/user subscription' } },
  { title: { ar: 'تطبيق إنشاء محتوى للمتاجر يستخدم AI', en: 'AI content app for stores' }, category: { ar: 'تطبيق/تسويق', en: 'App/marketing' }, time: { ar: 'أسبوع اختبار', en: '1-week test' }, profit: { ar: '199$/شهر أو 25$/فيديو' , en: '$199/month or $25/video' } },
  { title: { ar: 'خدمة تنفيذ أتمتة AI للشركات الصغيرة', en: 'AI automation implementation service' }, category: { ar: 'خدمة مدعومة بـ AI', en: 'AI-powered service' }, time: { ar: 'يوم واحد', en: '1 day' }, profit: { ar: 'إعداد 500$ + متابعة شهرية' , en: '$500 setup + monthly support' } },
  { title: { ar: 'حزمة قواعد CLAUDE.md عربية لمكاتب البرمجة', en: 'Arabic CLAUDE.md ruleset for dev shops' }, category: { ar: 'منتج رقمي', en: 'Digital product' }, time: { ar: 'يومان', en: '2 days' }, profit: { ar: '49$ مرة + رسوم ترقية', en: '$49 one-off + upgrade fees' } },
  { title: { ar: 'وكيل صوتي خليجي لحجوزات معارض السيارات', en: 'Khaleeji voice agent for auto dealerships' }, category: { ar: 'خدمة B2B', en: 'B2B service' }, time: { ar: 'أسبوع تكامل', en: '1-week integration' }, profit: { ar: '2,500 ريال/مقعد/شهرياً', en: 'SAR 2,500/seat/month' } },
  { title: { ar: 'مساعد امتثال رؤية 2030 لكتابة كراسات الشروط', en: 'Vision 2030 compliance writer for RFPs' }, category: { ar: 'منتج للحكومة/الاستشارات', en: 'Govt/consulting product' }, time: { ar: '5 أيام', en: '5 days' }, profit: { ar: '8,000 ريال+/مقعد', en: 'SAR 8,000+/seat' } },
  { title: { ar: 'محرر فيديوهات تعليمية AI للمدربين العرب', en: 'AI educational video editor for Arab trainers' }, category: { ar: 'أداة محتوى', en: 'Content tool' }, time: { ar: '4 أيام', en: '4 days' }, profit: { ar: '99$/شهر + إضافات', en: '$99/month + add-ons' } },
  { title: { ar: 'مولّد سياسات داخلية AI للمصانع والمستشفيات', en: 'AI internal policy generator for clinics/factories' }, category: { ar: 'خدمة بـ AI', en: 'AI service' }, time: { ar: 'يومان', en: '2 days' }, profit: { ar: '1,200$ مشروع + اشتراك', en: '$1,200 project + retainer' } },
  { title: { ar: 'لوحة قياس ROI لاستخدام AI داخل الفرق', en: 'AI usage ROI dashboard for teams' }, category: { ar: 'أداة قياس', en: 'Analytics tool' }, time: { ar: '3 أيام', en: '3 days' }, profit: { ar: '79$/شهر/فريق', en: '$79/month/team' } },
  { title: { ar: 'مجتمع مدفوع لمشاركة workflows عربية مع Claude', en: 'Paid community for Arabic Claude workflows' }, category: { ar: 'مجتمع/اشتراك', en: 'Community/subscription' }, time: { ar: 'يوم إطلاق', en: 'Launch in 1 day' }, profit: { ar: '15$/شهر · 100+ عضو شهرياً', en: '$15/month · 100+ members/mo' } }
];

const DEFAULT_SIGNALS = [
  { ar: 'زيادة الحديث عن AI Agents خلال آخر ساعتين.', en: 'AI Agents conversation increased during the last two hours.' },
  { ar: 'مشاريع GitHub جديدة مرتبطة بتوليد الفيديو.', en: 'New GitHub projects tied to video generation.' },
  { ar: 'ارتفاع البحث عن أدوات أتمتة التسويق.', en: 'Search interest is rising for marketing automation tools.' }
];

function t(key, ...args) {
  const entry = I18N[key];
  if (!entry) return key;
  const value = entry[RadarState.lang] || entry.en || entry.ar;
  return typeof value === 'function' ? value(...args) : value;
}

async function loadJSON(path, fallback) {
  try {
    const res = await fetch(path, { cache: 'no-store' });
    if (!res.ok) throw new Error(path);
    return await res.json();
  } catch (err) {
    return fallback;
  }
}

async function loadRadarData() {
  const [signals, corpus, timeline, opportunities, productPlaybooks, dynamicPlaybooks, researchOpportunities, accounts] = await Promise.all([
    loadJSON('data/radar/signals.json', { items: [], count: 0 }),
    loadJSON('data/radar/signals_corpus.json', { items: [], count: 0 }),
    loadJSON('data/radar/model_timeline.json', { items: [] }),
    loadJSON('data/radar/opportunities.json', { opportunities: [] }),
    loadJSON('data/radar/product_playbooks.json', { playbooks: [] }),
    loadJSON('data/radar/product_playbooks_dynamic.json', { playbooks: [] }),
    loadJSON('data/radar/research_opportunities.json', { opportunities: [] }),
    loadJSON('data/radar/x_focus_accounts.json', { accounts: [] })
  ]);
  const chosenPlaybooks = (dynamicPlaybooks.playbooks || []).length ? dynamicPlaybooks : productPlaybooks;
  return { signals, corpus, timeline, opportunities, productPlaybooks: chosenPlaybooks, researchOpportunities, accounts };
}

async function bootRadar() {
  const { signals, corpus, timeline, opportunities, productPlaybooks, researchOpportunities, accounts } = await loadRadarData();

  RadarState.signals = signals.items || [];
  RadarState.corpusSignals = sortSignalsByFreshness(corpus.items || RadarState.signals);
  RadarState.timeline = sortTimeline(timeline.items || []);
  RadarState.generatedAt = signals.generated_at;
  RadarState.opportunities = opportunities.opportunities || [];
  RadarState.productPlaybooks = productPlaybooks.playbooks || [];
  RadarState.researchOpportunities = researchOpportunities.opportunities || [];
  RadarState.accounts = accounts.accounts || [];
  RadarState.knownSignalIds = new Set(RadarState.signals.map(signalKey));

  applyLang();
  wireLayers();
  wireLangToggle();
  wireDetailModal();
  renderLayer('radar');
  setupParticles();
  startLiveRefresh();
}

function startLiveRefresh() {
  if (RadarState.refreshTimer) window.clearInterval(RadarState.refreshTimer);
  RadarState.refreshTimer = window.setInterval(refreshRadarData, 30000);
}

async function refreshRadarData() {
  const { signals, corpus, timeline, opportunities, productPlaybooks, researchOpportunities, accounts } = await loadRadarData();
  const nextSignals = signals.items || [];
  const nextGeneratedAt = signals.generated_at;
  const nextIds = new Set(nextSignals.map(signalKey));
  const newItems = nextSignals.filter((item) => !RadarState.knownSignalIds.has(signalKey(item))).slice(0, 4);
  const changed = nextGeneratedAt && nextGeneratedAt !== RadarState.generatedAt;

  if (!changed && !newItems.length) return;

  RadarState.signals = nextSignals;
  RadarState.corpusSignals = sortSignalsByFreshness(corpus.items || nextSignals);
  RadarState.timeline = sortTimeline(timeline.items || RadarState.timeline);
  RadarState.generatedAt = nextGeneratedAt;
  RadarState.opportunities = opportunities.opportunities || RadarState.opportunities;
  RadarState.productPlaybooks = productPlaybooks.playbooks || RadarState.productPlaybooks;
  RadarState.researchOpportunities = researchOpportunities.opportunities || RadarState.researchOpportunities;
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
    const key = 'nav_' + layer;
    if (I18N[key]) btn.textContent = t(key);
  });
  // Footer
  const dashLink = document.querySelector('.radar-footer a');
  if (dashLink) dashLink.textContent = t('dashboard_link');
  // Portrait guard
  const portraitH1 = document.querySelector('.portrait-guard h1');
  const portraitP = document.querySelector('.portrait-guard p');
  if (portraitH1) portraitH1.textContent = t('rotate_phone_h1');
  if (portraitP) portraitP.textContent = t('rotate_phone_p');
  // Lang toggle active state
  document.querySelectorAll('.radar-lang button').forEach((b) => {
    b.classList.toggle('active', b.dataset.lang === RadarState.lang);
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
  clearTicker();
  scheduleTimelineAutoplay();
  document.querySelectorAll('[data-layer]').forEach((button) => {
    if (button.parentElement && button.parentElement.classList.contains('radar-lang')) return;
    button.classList.toggle('active', button.dataset.layer === layer);
  });

  const meta = LAYERS[layer] || LAYERS.radar;
  document.getElementById('layer-title').textContent = meta.title[RadarState.lang] || meta.title.en;
  document.getElementById('layer-summary').textContent = meta.summary[RadarState.lang] || meta.summary.en;
  document.getElementById('radar-updated').textContent = updateLabel();

  renderCards(layer);
  renderDock(layer);
  renderRadarTags(layer);
  renderSourceSpokes(layer);
  renderFloatingStrip(layer);
}

function scheduleTimelineAutoplay() {
  if (RadarState.timelineAutoTimer) window.clearInterval(RadarState.timelineAutoTimer);
  RadarState.timelineAutoTimer = null;
  if (RadarState.layer !== 'radar' || !RadarState.timeline.length) return;

  RadarState.timelineAutoTimer = window.setInterval(() => {
    if (RadarState.layer !== 'radar' || RadarState.autoTimelinePaused) return;
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
    return `<span class="tag tag-pos-${index} ${klass}">#${escapeHTML(tag)}<em>${escapeHTML(count)}</em></span>`;
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

function renderCards(layer) {
  const left = document.getElementById('card-left');
  const right = document.getElementById('card-right');
  const bottom = document.getElementById('card-bottom');
  const topSignals = RadarState.signals.slice(0, 6);
  const topOpp = RadarState.opportunities[0];
  const allSignals = archiveSignals();
  const sources = countBy(allSignals, 'source_id');

  if (layer === 'opportunities') {
    const oppRows = opportunityRows();
    left.innerHTML = opportunityCard(oppRows[0]);
    right.innerHTML = opportunityCard(oppRows[1]);
    bottom.innerHTML = opportunityCard(oppRows[2]);
    return;
  }

  if (layer === 'sources') {
    left.innerHTML = listCard(t('active_sources'), Object.entries(sources).slice(0, 4).map(([id, count]) => [sourceName(id), `${count} ${t('signals_word')}`]));
    right.innerHTML = listCard(t('focused_x_accounts'), RadarState.accounts.slice(0, 4).map((a) => [`@${a.username}`, `${formatNumber(a.followers_count)} ${t('followers')}`]));
    bottom.innerHTML = card(t('collection_strategy'), t('layered_not_random'), t('monitor_strategy_text'));
    return;
  }

  if (layer === 'signals') {
    left.innerHTML = card(t('the_signals'), `${RadarState.signals.length} / ${allSignals.length}`, RadarState.lang === 'ar' ? 'الجديد أولًا، والأرشيف محفوظ للتوسيع' : 'Fresh first, archive preserved');
    right.innerHTML = listCard(t('latest_pulse'), visibleSignals().slice(0, 3).map((s) => [sourceName(s.source_id), localizedTitle(s)]));
    bottom.innerHTML = card(t('signal_strength'), `${Math.round((topSignals[0]?.opportunity_score || 0) * 100)}%`, topSignals[0]?.signal_type || t('monitoring'));
    return;
  }

  if (layer === 'trending') {
    const trends = trendRows();
    const xSignals = RadarState.signals.filter((s) => s.source_id === 'x_recent_search');
    left.innerHTML = listCard(RadarState.lang === 'ar' ? 'تعليقات عالية التفاعل' : 'High-engagement comments', trends.slice(0, 3).map((tag, idx) => [`#${tag}`, trendEngagementLabel(idx)]));
    right.innerHTML = card(RadarState.lang === 'ar' ? 'مصدر الرائج' : 'Trend source', 'X', RadarState.lang === 'ar' ? `${xSignals.length || 'قيد الجمع'} إشارات من منشورات وتفاعلات الناس` : `${xSignals.length || 'collecting'} signals from public posts and reactions`);
    bottom.innerHTML = card(RadarState.lang === 'ar' ? 'لماذا نتابعه؟' : 'Why it matters', RadarState.lang === 'ar' ? 'المزاج العام' : 'Public demand', RadarState.lang === 'ar' ? 'الرائج يكشف ما يلفت انتباه الناس، وما يشتكون منه، وما قد يتحول إلى طلب أو فرصة.' : 'Trending conversations reveal attention, objections, and demand that may become an opportunity.');
    return;
  }

  // Default: radar layer
  const timeline = timelineRows();
  left.innerHTML = timelineCard(timeline[0]);
  right.innerHTML = timelineCard(timeline[1]);
  bottom.innerHTML = timelineCard(timeline[2]);
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
      ${showArrows ? '<button type="button" class="panel-arrow panel-arrow-prev" aria-label="السابق" data-dir="-1">‹</button>' : ''}
      <div class="panel-feed" id="panel-feed-scroll">
        ${items.map((item, idx) => panelChip(item, layer, idx)).join('')}
      </div>
      ${showArrows ? '<button type="button" class="panel-arrow panel-arrow-next" aria-label="التالي" data-dir="1">›</button>' : ''}
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
  if (layer === 'opportunities') return opportunityRows();
  if (layer === 'radar' && RadarState.timeline.length) return timelineRows().slice(0, RadarState.archiveExpanded ? 12 : 6);
  if (['radar', 'signals'].includes(layer)) return visibleSignals().slice(0, RadarState.archiveExpanded ? 12 : 6);
  return RadarState.signals.slice(0, 6);
}

function panelChip(item, layer, idx) {
  if (layer === 'opportunities') {
    return `
      <button type="button" class="signal-chip opportunity-chip" data-detail-idx="${idx}">
        <span>${escapeHTML(item.category)}</span>
        <p>${escapeHTML(item.title)}</p>
        <small>${escapeHTML(item.buyer || '')}</small>
        <small>${escapeHTML(item.inspiration || item.profit || item.time || '')}</small>
      </button>
    `;
  }
  if (layer === 'radar' && item.date) {
    return `
      <article class="signal-chip timeline-chip timeline-${escapeAttr(item.category)}" role="button" tabindex="0" data-timeline-idx="${idx}">
        <span>${escapeHTML(timelineCategoryLabel(item.category))} · ${escapeHTML(formatTimelineDate(item.date))}</span>
        <p>${escapeHTML(localizedTimelineTitle(item))}</p>
        <small>${escapeHTML(timelineShortSummary(item))}</small>
        ${item.source_url ? `<a class="timeline-source-link" href="${escapeAttr(item.source_url)}" target="_blank" rel="noreferrer">${escapeHTML(RadarState.lang === 'ar' ? 'المصدر' : 'Source')}</a>` : ''}
      </article>
    `;
  }
  return `
    <a class="signal-chip" href="${escapeAttr(item.source_url || item.url || '#')}" target="_blank" rel="noreferrer">
      <span>${escapeHTML(sourceName(item.source_id))}</span>
      <p>${escapeHTML(localizedTitle(item))}</p>
      ${layer === 'radar' ? `<small>${escapeHTML(newsUpdateKind(item))}</small>` : ''}
    </a>
  `;
}

function openOpportunityDetail(item, idx = 0) {
  if (!item) return;
  const lang = RadarState.lang;
  const isAr = lang === 'ar';

  document.getElementById('detail-source').textContent = item.category || (isAr ? 'فرصة' : 'Opportunity');
  document.getElementById('detail-title').textContent = item.title || '';
  document.getElementById('detail-original').hidden = true;

  const meta = document.getElementById('detail-meta');
  const parts = [];
  const L = (ar, en) => isAr ? ar : en;
  if (item.capital)    parts.push(`${L('رأس المال', 'Capital')}: ${item.capital}`);
  if (item.profit)     parts.push(`${L('الربح المتوقع', 'Profit')}: ${item.profit}`);
  if (item.time)       parts.push(`${L('الخطوة الأولى', 'First step')}: ${item.time}`);
  if (item.confidence) parts.push(`${L('الثقة', 'Confidence')}: ${Math.round(item.confidence * 100)}%`);
  if (item.source)     parts.push(item.source);
  meta.innerHTML = parts.map((p) => `<span>${escapeHTML(p)}</span>`).join('');

  const sections = [];
  const sect = (label, body) => body ? `${label}\n${body}` : '';
  if (item.why)      sections.push(sect(L('لماذا الآن:', 'Why now:'), item.why));
  if (item.product)  sections.push(sect(L('المنتج المقترح:', 'Proposed product:'), item.product));
  if (item.buyer)    sections.push(sect(L('المشتري المستهدف:', 'Target buyer:'), item.buyer));
  if (item.tools)    sections.push(sect(L('الأدوات المطلوبة:', 'Tools needed:'), item.tools));
  if (item.examples) sections.push(sect(L('أمثلة:', 'Examples:'), item.examples));
  if (item.inspiration) sections.push(sect(L('إلهام مشابه:', 'Similar inspiration:'), item.inspiration));
  if (item.sourceLinks && item.sourceLinks.length) sections.push(sect(L('مصادر الإلهام:', 'Inspiration sources:'), formatSourceLinks(item.sourceLinks)));
  if (item.saudi)    sections.push(sect(L('عدسة السعودية:', 'Saudi money lens:'), item.saudi));
  if (item.playbook && item.playbook.length) {
    sections.push(sect(L('خطة 7 أيام:', '7-day playbook:'), formatPlaybook(item.playbook)));
  }
  document.getElementById('detail-text').textContent = sections.filter(Boolean).join('\n\n');

  const link = document.getElementById('detail-link');
  if (item.url) {
    link.href = item.url;
    link.textContent = isAr ? 'افتح المصدر ↗' : 'Open source ↗';
    link.style.display = '';
  } else {
    link.style.display = 'none';
  }

  const modal = document.getElementById('detail-modal');
  // Alternate side: even idx → right of globe, odd idx → left of globe
  const side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.side = side;
  modal.hidden = false;
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
    url: link.url || ''
  })).filter((link) => link.label || link.url);
}

function formatSourceLinks(links) {
  return links.map((link, index) => {
    const source = link.source ? ` · ${link.source}` : '';
    const url = link.url ? `\n${link.url}` : '';
    return `${index + 1}. ${link.label}${source}${url}`;
  }).join('\n');
}

function openTimelineDetail(item, idx = 0, auto = false) {
  if (!item) return;
  const isAr = RadarState.lang === 'ar';
  const L = (ar, en) => isAr ? ar : en;

  document.getElementById('detail-source').textContent = `${timelineCategoryLabel(item.category)} · ${item.vendor || ''}`;
  document.getElementById('detail-title').textContent = localizedTimelineTitle(item);
  document.getElementById('detail-original').hidden = true;

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
    `${L('ما الذي يرصده الرادار؟', 'What the radar tracks?')}\n${timelineRadarTakeaway(item)}`
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
  modal.dataset.side = (idx % 2 === 0) ? 'right' : 'left';
  modal.dataset.kind = 'timeline';
  modal.hidden = false;
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
      ? `يراقب الرادار هذا كتحديث قابل للتأثير على اختيار الأداة أو تسعير المنتج. ${base}`
      : `The radar tracks this as an update that can affect tool choice or product pricing. ${base}`;
  }
  return isAr
    ? 'يراقبه الرادار لأنه قد يغير أدوات البناء أو جودة المنتج أو سرعة التنفيذ.'
    : 'The radar tracks it because it may change build tools, product quality, or execution speed.';
}

function closeDetail() {
  const modal = document.getElementById('detail-modal');
  if (!modal) return;
  modal.classList.remove('open');
  setTimeout(() => { modal.hidden = true; }, 320);
}

function wireDetailModal() {
  const modal = document.getElementById('detail-modal');
  if (!modal) return;
  modal.addEventListener('click', (e) => {
    if (e.target.dataset && e.target.dataset.close === '1') closeDetail();
  });
  const closeBtn = document.getElementById('detail-close');
  if (closeBtn) closeBtn.addEventListener('click', closeDetail);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeDetail();
  });
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

function renderFloatingStrip(layer) {
  const root = document.getElementById('floating-strip');
  if (!root) return;
  root.innerHTML = '';

  if (RadarState.lastLiveItems.length && layer === 'radar') {
    showLiveArrival(RadarState.lastLiveItems[0]);
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

function panelMetric(layer, items) {
  if (layer === 'opportunities') {
    return {
      label: RadarState.lang === 'ar' ? 'أفكار دخل' : 'Income ideas',
      value: String(items.length),
      caption: RadarState.lang === 'ar' ? 'مرتبة حسب رأس المال والربح المحتمل' : 'Ranked by capital and profit potential'
    };
  }
  if (layer === 'sources') {
    return {
      label: RadarState.lang === 'ar' ? 'المصادر' : 'Sources',
      value: String(Object.keys(countBy(archiveSignals(), 'source_id')).length),
      caption: RadarState.lang === 'ar' ? 'قنوات مراقبة نشطة مع أرشيف محفوظ' : 'Active channels with preserved archive'
    };
  }
  if (layer === 'trending') {
    return {
      label: RadarState.lang === 'ar' ? 'الرائج' : 'Trending',
      value: String(trendingTags().length),
      caption: RadarState.lang === 'ar' ? 'تعليقات X عالية التفاعل' : 'High-engagement X conversations'
    };
  }
  return {
    label: RadarState.lang === 'ar' ? 'Timeline' : 'Timeline',
    value: RadarState.timeline.length ? String(RadarState.timeline.length) : (RadarState.archiveExpanded ? String(archiveSignals().length) : String(RadarState.signals.length)),
    caption: RadarState.archiveExpanded
      ? (RadarState.lang === 'ar' ? 'عرض خط زمني أوسع مع الأرشيف' : 'Showing wider timeline and archive')
      : (RadarState.lang === 'ar' ? 'آخر 3 أشهر: نماذج، أدوات، أسعار وحدود' : 'Last 3 months: models, tools, pricing and limits')
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
  const fromData = trendingTags().map(([tag]) => cleanTag(tag)).filter(Boolean);
  const fallback = DEFAULT_TRENDS.map((item) => item[RadarState.lang] || item.en);
  return fromData.concat(fallback).slice(0, 6);
}

function signalRows() {
  const live = RadarState.lastLiveItems.map(localizedTitle).filter(Boolean);
  const fromData = RadarState.signals.slice(0, 5).map(localizedTitle).filter(Boolean);
  const fallback = DEFAULT_SIGNALS.map((item) => item[RadarState.lang] || item.en);
  return live.concat(fromData, fallback).slice(0, 6);
}

function signalKey(item) {
  return item && (item.id || item.source_url || item.title || '');
}

function opportunityRows() {
  const fromPlaybooks = RadarState.productPlaybooks.slice(0, 12).map((item) => productPlaybookRow(item));
  const fromData = RadarState.opportunities.slice(0, 4).map((opp) => ({
    title: RadarState.lang === 'ar' ? (opp.title_ar || opp.title_en) : (opp.title_en || opp.title_ar),
    category: RadarState.lang === 'ar' ? 'فرصة مرصودة' : 'Detected opportunity',
    capital: RadarState.lang === 'ar' ? (opp.capital_ar || opportunityCapitalAr(opp)) : opportunityCapitalEn(opp),
    product: RadarState.lang === 'ar' ? opportunityProductAr(opp) : opportunityProductEn(opp),
    buyer: RadarState.lang === 'ar' ? opportunityBuyerAr(opp) : opportunityBuyerEn(opp),
    time: RadarState.lang === 'ar' ? opportunityFirstStepAr(opp) : opportunityFirstStepEn(opp),
    profit: RadarState.lang === 'ar' ? (opp.pricing_ar || radarMoneyLabel(opp.id)) : radarMoneyLabel(opp.id),
    tools: RadarState.lang === 'ar' ? (opp.tools_ar || opportunityToolsAr(opp)) : opportunityToolsEn(opp),
    examples: RadarState.lang === 'ar' ? (opp.examples_ar || opportunityExamplesAr(opp)) : opportunityExamplesEn(opp),
    why: RadarState.lang === 'ar' ? opportunityWhyAr(opp) : opportunityWhyEn(opp),
    confidence: opp.confidence,
    signalCount: opp.signal_count,
    source: `${opp.signal_count || 0} ${RadarState.lang === 'ar' ? 'دليل' : 'evidence'}`
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
  const fallback = DEFAULT_OPPORTUNITIES.map((item) => ({
    title: item.title[RadarState.lang] || item.title.en,
    category: item.category[RadarState.lang] || item.category.en,
    capital: RadarState.lang === 'ar' ? 'منخفض' : 'Low',
    product: RadarState.lang === 'ar' ? 'عرض صغير يمكن بيعه قبل بناء منصة كاملة' : 'A small offer to sell before building a full platform',
    buyer: RadarState.lang === 'ar' ? 'عميل لديه ألم واضح ويقبل تجربة مدفوعة' : 'A buyer with clear pain who can pay for a pilot',
    time: item.time[RadarState.lang] || item.time.en,
    profit: item.profit[RadarState.lang] || item.profit.en,
    tools: RadarState.lang === 'ar' ? 'ChatGPT أو Claude، صفحة هبوط، نموذج دفع بسيط' : 'ChatGPT or Claude, landing page, simple payment flow',
    examples: RadarState.lang === 'ar' ? 'قوالب مدفوعة، خدمة شهرية، أتمتة لفريق صغير' : 'Paid templates, monthly service, automation for a small team',
    why: RadarState.lang === 'ar' ? 'فرصة افتراضية تظهر فقط عند نقص البيانات.' : 'Fallback opportunity shown only when data is thin.'
  }));
  return fromPlaybooks.concat(interleaveRows(fromData, fromResearch), fallback).slice(0, 16);
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

function opportunityProductEn(opp) {
  return {
    ai_income_services: 'A packaged service that uses AI to deliver repeated client work',
    ai_income_tools: 'A small AI-powered tool or workflow template',
    ai_income_automation: 'An AI automation that removes repeated manual work',
    ai_income_content: 'A content, ad, or short-video production package'
  }[opp.id] || opp.sellable_product_ar || 'A paid offer backed by a verifiable signal';
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
  }[opp.id] || opp.buyer_ar || 'A buyer with visible public pain';
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
  }[opp.id] || opp.first_paid_test_ar || 'Quick paid pilot with one customer';
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
  }[opp.id] || opp.why_it_matters_ar || 'Accepted because it is backed by linked signals, not a loose opinion.';
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
  if (item.source_id === 'x_recent_search') return 'منشور من X عن منتج أو خدمة تستخدم الذكاء الاصطناعي';
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
  return {
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
    arxiv_papers: 'arXiv'
  }[id] || id || 'Source';
}

function updateLabel() {
  if (!RadarState.generatedAt) return t('no_update_yet');
  const date = new Date(RadarState.generatedAt);
  if (Number.isNaN(date.getTime())) return RadarState.generatedAt;
  const locale = RadarState.lang === 'ar' ? 'ar-SA' : 'en-US';
  return t('last_update') + ' ' + date.toLocaleString(locale, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
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
