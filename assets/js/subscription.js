/* Radar — SubscriptionService
 *
 * Frontend-only subscription state. This module is deliberately small and
 * self-contained so it's easy to swap when a real backend lands.
 *
 * Important: until a serverless `/api/checkout/session` endpoint exists,
 * StartCheckout() will simply route to subscribe.html. Real payment goes
 * through Stripe Checkout — never collect card data here.
 *
 * SECURITY NOTE
 * Frontend gating is UX, not security. Anyone can read the JSON. Do not
 * put truly private content in data/* and rely on this alone — wire a
 * real backend before that point. We document this clearly so the
 * intent is preserved across handovers.
 */
(function (global) {
  'use strict';

  const STORAGE_KEY = 'radar_subscription_v1';
  const ANALYTICS_KEY = 'radar_events_v1';

  let cachedConfig = null;

  async function loadConfig() {
    if (cachedConfig) return cachedConfig;
    try {
      const res = await fetch('data/config.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('config http ' + res.status);
      cachedConfig = await res.json();
    } catch (err) {
      // Hard-fail safe defaults; UI should still render free content.
      cachedConfig = {
        product: { name_en: 'Radar', name_ar: 'الرادار' },
        subscription: { enabled: true, price_usd: 15, price_label_ar: '15 دولار', price_label_en: '$15', billing_cycle: 'monthly', free_preview_count: 3 },
        stripe: { success_path: '/account.html?status=success', cancel_path: '/subscribe.html?status=cancelled' },
        features: { show_locked_previews: true, show_new_badge_days: 3 }
      };
    }
    return cachedConfig;
  }

  function readState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const obj = JSON.parse(raw);
      if (!obj || typeof obj !== 'object') return null;
      return obj;
    } catch (e) {
      return null;
    }
  }

  function writeState(state) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
  }

  function clearState() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
  }

  function isExpired(state) {
    if (!state) return true;
    if (!state.expires_at) return false; // no expiry set → treat as active until set
    return Date.now() >= new Date(state.expires_at).getTime();
  }

  /** Public: returns true if the current browser holds an active subscription marker. */
  function IsUserSubscribed() {
    const s = readState();
    if (!s || s.status !== 'active') return false;
    if (isExpired(s)) return false;
    return true;
  }

  /** Public: returns subscription state object for UI display, or null. */
  function GetSubscriptionState() {
    return readState();
  }

  /**
   * Public: should this content item be visible to the current user?
   * Honors backwards-compat defaults: missing tier = "free".
   */
  function CanAccessContent(content) {
    if (!content) return false;
    if (content.status && content.status !== 'published') {
      // archived stays available to subscribers; drafts hidden from everyone
      if (content.status === 'draft') return false;
      // archived → subscribers only
      return IsUserSubscribed();
    }
    const tier = content.tier || 'free';
    if (tier === 'free') return true;
    return IsUserSubscribed();
  }

  /**
   * Public: kicks off the paid checkout flow.
   * - If a server endpoint is configured, POST to it, then redirect.
   * - Otherwise route to subscribe.html (the static fallback).
   */
  async function StartCheckout(meta) {
    const cfg = await loadConfig();
    Analytics('checkout_started', meta || {});
    const endpoint = cfg.stripe && cfg.stripe.checkout_session_endpoint;
    if (endpoint && endpoint.startsWith('/api/')) {
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ price_usd: cfg.subscription.price_usd, ...meta })
        });
        if (res.ok) {
          const data = await res.json();
          if (data && data.url) {
            window.location.assign(data.url);
            return { ok: true };
          }
        }
      } catch (e) { /* fall through to static page */ }
    }
    // Static fallback — surface the subscribe page
    window.location.assign('subscribe.html');
    return { ok: false, fallback: true };
  }

  /**
   * Public: called by the success page after Stripe Checkout returns.
   * In a real deployment, the server should set this via a webhook +
   * a signed cookie or a tiny "/api/me" endpoint. Until then we accept
   * a `?status=success&session_id=...` redirect as a soft-activation.
   */
  function HandlePaymentSuccess(payload) {
    const now = new Date();
    const expires = new Date(now);
    expires.setDate(expires.getDate() + 31); // optimistic monthly window
    const state = {
      status: 'active',
      since: now.toISOString(),
      expires_at: expires.toISOString(),
      session_id: (payload && payload.session_id) || null,
      source: (payload && payload.source) || 'stripe_checkout'
    };
    writeState(state);
    Analytics('payment_success', { session_id: state.session_id });
    return state;
  }

  function HandlePaymentFailure(reason) {
    Analytics('payment_failed', { reason: reason || 'unknown' });
    return { ok: false, reason: reason || 'unknown' };
  }

  function CancelLocalSubscription() {
    Analytics('subscription_cancelled_local', {});
    clearState();
  }

  /* ----- Lightweight analytics (browser-side, no third-party by default) ----- */

  function Analytics(event, props) {
    try {
      const list = JSON.parse(localStorage.getItem(ANALYTICS_KEY) || '[]');
      list.push({ event, props: props || {}, ts: Date.now() });
      // cap history so localStorage doesn't bloat
      const capped = list.slice(-200);
      localStorage.setItem(ANALYTICS_KEY, JSON.stringify(capped));
    } catch (e) {}
    // Fan out to a real provider if you wire one in:
    if (global.plausible) { try { global.plausible(event, { props: props || {} }); } catch (e) {} }
    if (global.posthog && global.posthog.capture) { try { global.posthog.capture(event, props || {}); } catch (e) {} }
    // Always log to console in dev for visibility
    if (global.console && console.debug) console.debug('[radar.event]', event, props || {});
  }

  /* ----- Boot: load analytics providers if configured ----- */

  async function _loadAnalyticsProviders() {
    const cfg = await loadConfig();
    const a = cfg.analytics || {};
    if (a.plausible_domain && !global.plausible) {
      const s = document.createElement('script');
      s.defer = true;
      s.setAttribute('data-domain', a.plausible_domain);
      s.src = a.plausible_script || 'https://plausible.io/js/script.js';
      document.head.appendChild(s);
      // Stub immediately so events queued before script loads aren't lost.
      global.plausible = global.plausible || function () { (global.plausible.q = global.plausible.q || []).push(arguments); };
    }
    if (a.posthog_key && !global.posthog) {
      const host = a.posthog_host || 'https://app.posthog.com';
      const script = document.createElement('script');
      script.async = true;
      script.src = `${host.replace(/\/$/, '')}/static/array.js`;
      document.head.appendChild(script);
      global.posthog = global.posthog || { capture: function () { (global.posthog._q = global.posthog._q || []).push(['capture', arguments]); }, init: function (k, o) { setTimeout(() => global.posthog.__SV && global.posthog.init(k, o), 50); } };
      try { global.posthog.init(a.posthog_key, { api_host: host }); } catch (e) {}
    }
  }

  /* ----- Boot: handle ?status=success on the success page automatically ----- */

  function _handleReturnFromCheckout() {
    if (!global.location || !global.location.search) return;
    const qs = new URLSearchParams(global.location.search);
    const status = qs.get('status');
    if (status === 'success') {
      HandlePaymentSuccess({ session_id: qs.get('session_id'), source: 'stripe_checkout' });
    } else if (status === 'cancelled') {
      HandlePaymentFailure('user_cancelled');
    }
  }

  global.RadarSubscription = {
    loadConfig,
    IsUserSubscribed,
    GetSubscriptionState,
    CanAccessContent,
    StartCheckout,
    HandlePaymentSuccess,
    HandlePaymentFailure,
    CancelLocalSubscription,
    Analytics
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      _handleReturnFromCheckout();
      _loadAnalyticsProviders();
    });
  } else {
    _handleReturnFromCheckout();
    _loadAnalyticsProviders();
  }
})(typeof window !== 'undefined' ? window : this);
