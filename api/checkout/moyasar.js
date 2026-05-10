/* Moyasar Checkout — invoice creation
 *
 * Deploy target: Vercel Functions or Netlify Functions (Node 18+).
 *
 * Required environment variables:
 *   MOYASAR_SECRET_KEY     — sk_test_... or sk_live_... (Moyasar dashboard)
 *   MOYASAR_PUBLISHABLE_KEY— pk_test_... or pk_live_... (frontend, optional)
 *   SITE_URL               — https://radar.example.com (no trailing slash)
 *   MOYASAR_CALLBACK_URL   — https://radar.example.com/api/checkout/moyasar-callback
 *
 * Optional:
 *   ALLOWED_ORIGIN         — CORS allowlist; defaults to SITE_URL
 *   PRICE_AMOUNT           — amount in halalas/cents (default 1500 = $15.00)
 *   PRICE_CURRENCY         — SAR | USD | AED | KWD | BHD | OMR | EUR | GBP (default SAR)
 *
 * Flow:
 *   1) Frontend POSTs here.
 *   2) We create a Moyasar Invoice with success_url + back_url + callback_url.
 *   3) Moyasar returns a hosted-checkout URL.
 *   4) We return { url } and the frontend redirects the browser to it.
 *   5) After payment, Moyasar redirects user to success_url and POSTs the
 *      invoice update to MOYASAR_CALLBACK_URL (handled by moyasar-callback.js).
 *
 * Why Invoices and not the Payments API directly:
 *   - Hosted checkout means we never touch card data → no PCI scope.
 *   - Customers get the full Moyasar UI (mada, Apple Pay, Visa, MC).
 *   - Works on Vercel Edge / Netlify with no extra dependencies.
 */

const MOYASAR_API = 'https://api.moyasar.com/v1/invoices';

function readBody(req) {
  return new Promise((resolve) => {
    if (req.body && typeof req.body === 'object') return resolve(req.body);
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf-8');
      try { resolve(raw ? JSON.parse(raw) : {}); }
      catch (e) { resolve({}); }
    });
  });
}

module.exports = async function handler(req, res) {
  const allowedOrigin = process.env.ALLOWED_ORIGIN || process.env.SITE_URL || '*';
  res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  const secret = process.env.MOYASAR_SECRET_KEY;
  const siteUrl = process.env.SITE_URL || '';
  const callback = process.env.MOYASAR_CALLBACK_URL || (siteUrl ? `${siteUrl}/api/checkout/moyasar-callback` : '');

  if (!secret || !siteUrl) {
    return res.status(500).json({
      error: 'server_misconfigured',
      hint: 'Set MOYASAR_SECRET_KEY, SITE_URL (and optionally MOYASAR_CALLBACK_URL).',
    });
  }

  // Amount in smallest unit. SAR/USD = halalas/cents → 1500 = 15.00.
  const amount = Number(process.env.PRICE_AMOUNT || 1500);
  const currency = (process.env.PRICE_CURRENCY || 'SAR').toUpperCase();

  let payload = {};
  try { payload = await readBody(req); } catch (e) { /* ignore */ }

  // Build the form-urlencoded body Moyasar expects.
  const form = new URLSearchParams();
  form.set('amount', String(amount));
  form.set('currency', currency);
  form.set('description', payload.description || 'Radar Subscription · 30 days');
  form.set('callback_url', callback);
  form.set('success_url',  `${siteUrl}/account.html?status=success&provider=moyasar`);
  form.set('back_url',     `${siteUrl}/subscribe.html?status=cancelled&provider=moyasar`);
  if (payload.email) form.set('metadata[email]', String(payload.email).slice(0, 120));
  if (payload.origin) form.set('metadata[origin]', String(payload.origin).slice(0, 60));
  form.set('metadata[product]', 'radar_monthly_v1');

  let upstream;
  try {
    upstream = await fetch(MOYASAR_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + Buffer.from(secret + ':').toString('base64'),
      },
      body: form.toString(),
    });
  } catch (err) {
    return res.status(502).json({ error: 'upstream_unreachable', message: err.message });
  }

  let data;
  try { data = await upstream.json(); }
  catch (e) {
    const text = await upstream.text().catch(() => '');
    return res.status(502).json({ error: 'upstream_bad_json', body: text.slice(0, 200) });
  }

  if (!upstream.ok) {
    // Moyasar returns helpful error shapes — pass them through.
    return res.status(502).json({
      error: 'moyasar_error',
      status: upstream.status,
      moyasar: data,
    });
  }

  if (!data || !data.url) {
    return res.status(502).json({ error: 'moyasar_no_url', moyasar: data });
  }

  return res.status(200).json({
    provider: 'moyasar',
    url: data.url,
    invoice_id: data.id,
    amount: data.amount,
    currency: data.currency,
    status: data.status,
  });
};
