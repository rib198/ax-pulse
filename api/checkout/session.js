/* Stripe Checkout — session creation
 *
 * Deploy target: Vercel Functions or Netlify Functions (Node 18+).
 *
 * Required environment variables:
 *   STRIPE_SECRET_KEY     — sk_test_... or sk_live_...
 *   STRIPE_PRICE_ID       — price_... (your $15/month Stripe Price ID)
 *   SITE_URL              — e.g. https://radar.example.com  (no trailing slash)
 *
 * Optional:
 *   ALLOWED_ORIGIN        — origin allowed to call this endpoint (CORS).
 *                           Defaults to SITE_URL.
 *
 * The frontend posts to this with no body. The function returns the
 * Stripe Checkout URL; the frontend then redirects the browser to it.
 *
 * NOTE: this is a STUB ready to deploy. To install dependencies:
 *   npm i stripe
 * (Vercel/Netlify auto-install from the repo's package.json on deploy.)
 */
const Stripe = require('stripe');

module.exports = async function handler(req, res) {
  const allowedOrigin = process.env.ALLOWED_ORIGIN || process.env.SITE_URL || '*';
  res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  const secret = process.env.STRIPE_SECRET_KEY;
  const priceId = process.env.STRIPE_PRICE_ID;
  const siteUrl = process.env.SITE_URL || '';
  if (!secret || !priceId || !siteUrl) {
    return res.status(500).json({ error: 'server_misconfigured', hint: 'Set STRIPE_SECRET_KEY, STRIPE_PRICE_ID, SITE_URL.' });
  }

  const stripe = new Stripe(secret, { apiVersion: '2024-06-20' });

  try {
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${siteUrl}/account.html?status=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url:  `${siteUrl}/subscribe.html?status=cancelled`,
      locale: 'ar',
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      automatic_tax: { enabled: false }, // enable once your Stripe Tax setup is done
    });
    return res.status(200).json({ url: session.url, session_id: session.id });
  } catch (err) {
    console.error('[stripe.session] error', err);
    return res.status(500).json({ error: 'stripe_error', message: err.message });
  }
};
