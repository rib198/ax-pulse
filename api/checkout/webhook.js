/* Stripe Webhook — subscription state sync
 *
 * Deploy target: Vercel Functions or Netlify Functions (Node 18+).
 *
 * In Stripe Dashboard → Developers → Webhooks, add a new endpoint
 * pointing to https://your-domain/api/checkout/webhook and subscribe to:
 *   checkout.session.completed
 *   customer.subscription.created
 *   customer.subscription.updated
 *   customer.subscription.deleted
 *   invoice.payment_failed
 *
 * Required environment variables:
 *   STRIPE_SECRET_KEY
 *   STRIPE_WEBHOOK_SECRET   — whsec_... (from the webhook endpoint settings)
 *
 * Persist the subscription state somewhere durable. This stub only logs.
 * Recommended: write to a small KV (Vercel KV / Cloudflare KV / Supabase row).
 * Until that's wired, the frontend will rely on the success URL redirect
 * to set localStorage state on the user's browser (best-effort).
 */
const Stripe = require('stripe');

// Vercel: tell it not to parse the body (we need the raw bytes for signature verification).
module.exports.config = { api: { bodyParser: false } };

async function readRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  const secret = process.env.STRIPE_SECRET_KEY;
  const wh = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret || !wh) return res.status(500).json({ error: 'server_misconfigured' });

  const stripe = new Stripe(secret, { apiVersion: '2024-06-20' });
  const sig = req.headers['stripe-signature'];

  let event;
  try {
    const buf = await readRawBody(req);
    event = stripe.webhooks.constructEvent(buf, sig, wh);
  } catch (err) {
    console.error('[stripe.webhook] signature error', err.message);
    return res.status(400).send(`Webhook signature verification failed: ${err.message}`);
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const s = event.data.object;
        // TODO: persist { customer: s.customer, email: s.customer_details?.email, subscription: s.subscription, status: 'active' }
        console.log('[stripe] checkout.session.completed', { customer: s.customer, subscription: s.subscription });
        break;
      }
      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const sub = event.data.object;
        // TODO: upsert subscription record { id: sub.id, customer: sub.customer, status: sub.status, current_period_end: sub.current_period_end }
        console.log('[stripe] subscription.upsert', { id: sub.id, status: sub.status });
        break;
      }
      case 'customer.subscription.deleted': {
        const sub = event.data.object;
        // TODO: mark subscription cancelled / expired
        console.log('[stripe] subscription.deleted', { id: sub.id });
        break;
      }
      case 'invoice.payment_failed': {
        const inv = event.data.object;
        // TODO: notify the customer; downgrade access after the grace period Stripe enforces.
        console.log('[stripe] invoice.payment_failed', { customer: inv.customer });
        break;
      }
      default:
        // Receive every event, ignore the ones we don't act on.
        break;
    }
    return res.status(200).json({ received: true });
  } catch (err) {
    console.error('[stripe.webhook] handler error', err);
    return res.status(500).json({ error: 'handler_error', message: err.message });
  }
};
