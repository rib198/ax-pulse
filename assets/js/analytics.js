/* Radar — analytics adapter
 *
 * Thin wrapper exposing named events that the rest of the UI calls.
 * Default behavior: log to console + localStorage (via RadarSubscription.Analytics).
 * Wire to Plausible / PostHog by setting window.plausible or window.posthog
 * before this script loads.
 */
(function (global) {
  'use strict';
  function emit(name, props) {
    const sub = global.RadarSubscription;
    if (sub && typeof sub.Analytics === 'function') {
      sub.Analytics(name, props || {});
    } else if (global.console && console.debug) {
      console.debug('[radar.event]', name, props || {});
    }
  }
  global.RadarAnalytics = {
    contentViewed:        (id, tier) => emit('content_viewed',           { id, tier: tier || 'free' }),
    premiumAttempted:     (id)       => emit('premium_content_attempted',{ id }),
    subscribeClicked:     (origin)   => emit('subscribe_clicked',        { origin: origin || 'unknown' }),
    checkoutStarted:      (meta)     => emit('checkout_started',         meta || {}),
    paymentSuccess:       (meta)     => emit('payment_success',          meta || {}),
    paymentFailed:        (reason)   => emit('payment_failed',           { reason: reason || 'unknown' }),
    accountViewed:        ()         => emit('account_viewed',           {}),
    pricingViewed:        ()         => emit('pricing_viewed',           {})
  };
})(typeof window !== 'undefined' ? window : this);
