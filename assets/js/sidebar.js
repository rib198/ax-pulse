/* AX Pulse — sidebar injector (shared across dashboard pages) */

function injectSidebar() {
  const slot = document.getElementById('sidebar-slot');
  if (!slot) return;
  slot.innerHTML = `
    <aside class="sidebar">
      <a class="brand" href="dashboard.html">
        <div class="brand-mark" data-i18n="brand_mark">AX</div>
        <div class="brand-name">
          <span data-i18n="brand">AX Pulse</span>
          <small data-i18n="brand_sub">AI Trend Intelligence</small>
        </div>
      </a>

      <div class="nav-section">
        <div class="nav-section-title" data-i18n="nav_main">Intelligence</div>
        <a class="nav-item" data-page="today" href="dashboard.html">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="3" width="12" height="2" rx="0.5"/>
            <rect x="2" y="7" width="8" height="2" rx="0.5"/>
            <rect x="2" y="11" width="10" height="2" rx="0.5"/>
          </svg>
          <span data-i18n="nav_today">Today's Brief</span>
        </a>
        <a class="nav-item" data-page="radar" href="radar.html">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="8" cy="8" r="5.5"/>
            <circle cx="8" cy="8" r="1.5"/>
            <path d="M8 2.5v2M13.5 8h-2M8 13.5v-2M2.5 8h2"/>
          </svg>
          <span>Live Radar</span>
        </a>
        <a class="nav-item" data-page="trending" href="trending.html">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <polyline points="2,12 6,7 9,10 14,3"/>
            <polyline points="10,3 14,3 14,7"/>
          </svg>
          <span data-i18n="nav_trending">Trending Now</span>
        </a>
        <a class="nav-item" data-page="opportunities" href="opportunities.html">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M8 1l2 5 5 0.5-3.8 3.4 1.1 5.1L8 12.5 3.7 15l1.1-5.1L1 6.5 6 6z"/>
          </svg>
          <span data-i18n="nav_opportunities">Opportunities</span>
        </a>
        <a class="nav-item" data-page="categories" href="categories.html">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="2" width="5" height="5" rx="1"/>
            <rect x="9" y="2" width="5" height="5" rx="1"/>
            <rect x="2" y="9" width="5" height="5" rx="1"/>
            <rect x="9" y="9" width="5" height="5" rx="1"/>
          </svg>
          <span data-i18n="nav_categories">Categories</span>
        </a>
      </div>

      <div class="nav-spacer"></div>

      <div class="upgrade-card">
        <h4 data-i18n="upgrade_title">Unlock Pro</h4>
        <p data-i18n="upgrade_desc">Custom alerts, Arabic mode, Notion export.</p>
        <a class="btn btn-primary" href="index.html#pricing">
          <span data-i18n="upgrade_btn">Upgrade $29/mo</span>
        </a>
      </div>
    </aside>
  `;
}

document.addEventListener('DOMContentLoaded', injectSidebar);
