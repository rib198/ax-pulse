/* Moyasar Callback — invoice/payment status update
 *
 * Deploy target: Vercel Functions or Netlify Functions (Node 18+).
 *
 * Moyasar POSTs here after every invoice/payment status change. Verify
 * by re-fetching the invoice from Moyasar with the secret key — never
 * trust the body alone.
 *
 * Required env vars:
 *   MOYASAR_SECRET_KEY     — sk_test_... or sk_live_...
 *
 * Optional but recommended:
 *   MOYASAR_CALLBACK_TOKEN — shared secret. If set, Moyasar should be
 *                            configured to send it as a header or query
 *                            param so we can short-circuit forged requests.
 *
 * What this function does today (no DB attached):
 *   - Verifies the invoice with Moyasar API.
 *   - Logs the verified status for inspection.
 *   - Returns 200 OK so Moyasar stops retrying.
 *
 * What you wire up next (when KV / DB is ready):
 *   - On status === 'paid': mark the customer subscribed for 30 days.
 *   - On status === 'failed' / 'refunded': downgrade.
 *
 * Until a DB is wired, the frontend uses the success URL redirect
 * (?status=success) to set a 30-day local subscription marker.
 */

function readBody(req) {
  return new Promise((resolve) => {
    if (req.body && typeof req.body === 'object') return resolve(req.body);
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf-8');
      // Moyasar callbacks are JSON by default but can be form-urlencoded.
      try { return resolve(JSON.parse(raw || '{}')); } catch (e) {}
      const params = new URLSearchParams(raw);
      const obj = {};
      for (const [k, v] of params) obj[k] = v;
      resolve(obj);
    });
  });
}

async function verifyInvoice(secret, invoiceId) {
  const r = await fetch(`https://api.moyasar.com/v1/invoices/${encodeURIComponent(invoiceId)}`, {
    headers: { 'Authorization': 'Basic ' + Buffer.from(secret + ':').toString('base64') },
  });
  if (!r.ok) return { ok: false, status: r.status };
  return { ok: true, data: await r.json() };
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  const secret = process.env.MOYASAR_SECRET_KEY;
  if (!secret) return res.status(500).json({ error: 'server_misconfigured' });

  // Optional shared-secret check.
  const expected = process.env.MOYASAR_CALLBACK_TOKEN;
  if (expected) {
    const provided = req.headers['x-moyasar-callback-token'] || (req.query && req.query.token);
    if (provided !== expected) return res.status(401).json({ error: 'unauthorized' });
  }

  const body = await readBody(req);
  const invoiceId = body.id || body.invoice_id || (body.data && body.data.id);
  if (!invoiceId) return res.status(400).json({ error: 'missing_invoice_id' });

  // Re-fetch from Moyasar to confirm the body wasn't spoofed.
  let verified;
  try { verified = await verifyInvoice(secret, invoiceId); }
  catch (e) { return res.status(502).json({ error: 'verify_unreachable', message: e.message }); }

  if (!verified.ok) {
    return res.status(502).json({ error: 'verify_failed', status: verified.status });
  }

  const inv = verified.data;
  const status = inv && inv.status;

  // TODO: persist subscription state. Suggested shape:
  //   { customer: inv.metadata?.email, invoice: inv.id, status,
  //     paid_at: inv.updated_at, expires_at: paid_at + 30 days,
  //     amount: inv.amount, currency: inv.currency }
  //
  // For now, just log and acknowledge.
  console.log('[moyasar.callback]', { id: inv.id, status, currency: inv.currency, amount: inv.amount, email: inv.metadata && inv.metadata.email });

  return res.status(200).json({ received: true, invoice_id: inv.id, status });
};
