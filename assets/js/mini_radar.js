/* Radar — mini-radar widget.
 *
 * Self-mounts a 140x140 canvas in the bottom-corner of any page that
 * loads this script. Shows:
 *   - a slow scanning sweep line (4s rotation)
 *   - dots for the last ~30 signals, positioned by:
 *       angle  = source category (deterministic hash)
 *       radius = priority (higher = closer to center)
 *   - 3 concentric rings (frame)
 *   - dots brighten when newly seen, dim with age
 *
 * Click → navigates to /radar.html.
 *
 * Reads data/radar/signals.json once. Re-fetches every 5 minutes.
 */
(function () {
  'use strict';

  if (document.querySelector('.mini-radar')) return; // already mounted

  // Skip on pages that ARE the full radar (avoid redundancy)
  const page = document.body && document.body.dataset.page;
  if (page === 'radar' || page === 'subscribe' || page === 'landing') return;

  const SIZE = 140;
  const CENTER = SIZE / 2;
  const MAX_R = CENTER - 8;

  // Build the DOM
  const wrap = document.createElement('a');
  wrap.className = 'mini-radar';
  wrap.href = 'radar.html';
  wrap.setAttribute('aria-label', 'Open full radar');
  wrap.dataset.event = 'subscribe_clicked'; // re-uses analytics fan-out
  wrap.dataset.eventOrigin = 'mini_radar';

  const canvas = document.createElement('canvas');
  canvas.width = SIZE * (window.devicePixelRatio || 1);
  canvas.height = SIZE * (window.devicePixelRatio || 1);
  canvas.style.width = SIZE + 'px';
  canvas.style.height = SIZE + 'px';
  wrap.appendChild(canvas);

  const label = document.createElement('span');
  label.className = 'mini-radar-label';
  label.textContent = '';
  wrap.appendChild(label);

  document.body.appendChild(wrap);

  const ctx = canvas.getContext('2d');
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

  let signals = [];
  let sweepAngle = 0;
  let lastFetch = 0;

  function deterministicAngle(sourceId) {
    let h = 0;
    const s = String(sourceId || 'x');
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xFFFFFFFF;
    return ((h % 360) / 360) * Math.PI * 2;
  }

  function categoryColor(item) {
    const k = (item.trust_tier || '').toLowerCase();
    if (k === 'official') return '#7CFF6B';
    if (k === 'research') return '#6eefff';
    if (k === 'press')    return '#fbbf24';
    if (k === 'social')   return '#f472b6';
    return '#a78bfa';
  }

  async function refreshSignals() {
    if (Date.now() - lastFetch < 4 * 60 * 1000) return;
    lastFetch = Date.now();
    try {
      const r = await fetch('data/radar/signals.json', { cache: 'no-cache' });
      if (!r.ok) return;
      const data = await r.json();
      signals = (data.items || []).slice(0, 30).map(it => ({
        id: it.id || it.source_id,
        angle: deterministicAngle(it.source_id),
        radius: MAX_R * (1 - Math.min(0.95, Math.max(0.1, (it.priority || it.opportunity_score || 0.3)))),
        color: categoryColor(it),
        seen_at: Date.now(),
      }));
      label.textContent = signals.length ? `${signals.length}` : '';
    } catch (e) {
      // silent — mini-radar is non-critical UI
    }
  }

  function draw() {
    ctx.clearRect(0, 0, SIZE, SIZE);

    // Outer ring + faint background
    ctx.fillStyle = 'rgba(8, 9, 10, 0.92)';
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, MAX_R, 0, Math.PI * 2);
    ctx.fill();

    // 3 concentric rings
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
    ctx.lineWidth = 1;
    for (let r = MAX_R; r > 0; r -= MAX_R / 3) {
      ctx.beginPath();
      ctx.arc(CENTER, CENTER, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cross axes
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.beginPath();
    ctx.moveTo(CENTER - MAX_R, CENTER); ctx.lineTo(CENTER + MAX_R, CENTER);
    ctx.moveTo(CENTER, CENTER - MAX_R); ctx.lineTo(CENTER, CENTER + MAX_R);
    ctx.stroke();

    // Sweep line — rotates 360° / 4s
    const sweepX = CENTER + Math.cos(sweepAngle) * MAX_R;
    const sweepY = CENTER + Math.sin(sweepAngle) * MAX_R;
    const grad = ctx.createLinearGradient(CENTER, CENTER, sweepX, sweepY);
    grad.addColorStop(0, 'rgba(124, 255, 107, 0.6)');
    grad.addColorStop(1, 'rgba(124, 255, 107, 0)');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(CENTER, CENTER);
    ctx.lineTo(sweepX, sweepY);
    ctx.stroke();

    // Sweep wedge — faint trailing arc behind the line
    ctx.fillStyle = 'rgba(124, 255, 107, 0.05)';
    ctx.beginPath();
    ctx.moveTo(CENTER, CENTER);
    ctx.arc(CENTER, CENTER, MAX_R, sweepAngle - 0.6, sweepAngle);
    ctx.closePath();
    ctx.fill();

    // Signal dots — brighter when sweep line is near them
    for (const s of signals) {
      const x = CENTER + Math.cos(s.angle) * s.radius;
      const y = CENTER + Math.sin(s.angle) * s.radius;
      // Distance from sweep angle (in radians, normalized to [0, π])
      let da = Math.abs(s.angle - sweepAngle) % (Math.PI * 2);
      if (da > Math.PI) da = Math.PI * 2 - da;
      const proximity = Math.max(0, 1 - da / 0.6);
      const baseAlpha = 0.55;
      const alpha = baseAlpha + proximity * 0.45;
      ctx.fillStyle = s.color.replace(')', `, ${alpha.toFixed(2)})`).replace('#', 'rgba(').replace(/^rgba\(([0-9a-f]+),/, (m, hex) => {
        const h = hex.replace('#', '');
        const num = parseInt(h.length === 3 ? h.split('').map(c=>c+c).join('') : h, 16);
        const r = (num >> 16) & 255, g = (num >> 8) & 255, b = num & 255;
        return `rgba(${r}, ${g}, ${b},`;
      });
      // Simpler: just draw with composite alpha
      ctx.globalAlpha = alpha;
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(x, y, 1.8 + proximity * 1.4, 0, Math.PI * 2);
      ctx.fill();
      // Glow around the brightest
      if (proximity > 0.7) {
        ctx.globalAlpha = 0.22;
        ctx.beginPath();
        ctx.arc(x, y, 4 + proximity * 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    // Center dot
    ctx.fillStyle = 'rgba(124, 255, 107, 0.9)';
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, 1.6, 0, Math.PI * 2);
    ctx.fill();
  }

  function tick() {
    sweepAngle += (Math.PI * 2) / (4 * 60); // 4s @ 60fps
    if (sweepAngle >= Math.PI * 2) sweepAngle -= Math.PI * 2;
    draw();
    requestAnimationFrame(tick);
  }

  // Respect reduced motion — draw once, no animation
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  refreshSignals().then(() => {
    if (prefersReduced) {
      draw();
    } else {
      requestAnimationFrame(tick);
    }
  });

  setInterval(refreshSignals, 5 * 60 * 1000);

  // Refetch when tab becomes visible (likely a long-open tab)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refreshSignals();
  });
})();
