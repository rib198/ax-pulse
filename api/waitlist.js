/* Waitlist signup — serverless POST endpoint.
 *
 * Forwards a new signup to the operator's inbox via Resend so emails actually
 * land somewhere (previously the form only wrote to the user's own localStorage).
 *
 * Required Vercel env vars:
 *   RESEND_API_KEY    — re_... from resend.com (free tier covers 3k/mo)
 *   WAITLIST_TO       — destination email address (defaults to support email below)
 *
 * Optional:
 *   DIGEST_FROM       — sender email (defaults to onboarding@resend.dev which
 *                       works without DNS setup; for production move to a
 *                       verified domain like "hello@yourdomain.com")
 *
 * Graceful degradation: if RESEND_API_KEY is missing, the signup is logged to
 * Vercel's runtime logs and a 200 is still returned (so the UX keeps working
 * while the operator finishes Resend setup).
 */

const DEFAULT_TO = "rawabialkhalaf3@gmail.com";

export default async function handler(req, res) {
  // CORS
  res.setHeader("Access-Control-Allow-Origin", process.env.ALLOWED_ORIGIN || "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ ok: false, error: "method_not_allowed" });
    return;
  }

  // Parse body (Vercel may give us a string or already-parsed object)
  let payload = req.body;
  if (typeof payload === "string") {
    try { payload = JSON.parse(payload); } catch { payload = {}; }
  }
  payload = payload || {};

  const email = String(payload.email || "").trim().toLowerCase();
  const source = String(payload.source || "unknown");

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 200) {
    res.status(400).json({ ok: false, error: "invalid_email" });
    return;
  }

  const entry = {
    email,
    source,
    ts: new Date().toISOString(),
    ua: (req.headers["user-agent"] || "").slice(0, 200),
    ref: req.headers.referer || "",
    ip: (req.headers["x-forwarded-for"] || "").split(",")[0].trim().slice(0, 64),
  };

  // Always log so signups are recoverable from Vercel's runtime logs even if
  // email delivery fails (or RESEND_API_KEY isn't set yet).
  console.log("[waitlist]", JSON.stringify(entry));

  const key = process.env.RESEND_API_KEY;
  if (!key) {
    res.status(200).json({ ok: true, delivered: "log_only", note: "RESEND_API_KEY not set" });
    return;
  }

  const to = process.env.WAITLIST_TO || DEFAULT_TO;
  const from = process.env.DIGEST_FROM || "الرادار <onboarding@resend.dev>";

  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to,
        subject: `Waitlist signup: ${email}`,
        text: [
          "تسجيل جديد في قائمة انتظار الرادار",
          "",
          `Email:  ${email}`,
          `Source: ${source}`,
          `Time:   ${entry.ts}`,
          `Ref:    ${entry.ref}`,
          `IP:     ${entry.ip}`,
          `UA:     ${entry.ua}`,
        ].join("\n"),
        reply_to: email,
      }),
    });

    if (!r.ok) {
      const body = await r.text();
      console.error("[waitlist] resend_error", r.status, body.slice(0, 200));
      res.status(200).json({ ok: true, delivered: "log_only", error: "resend_failed" });
      return;
    }

    res.status(200).json({ ok: true, delivered: "email" });
  } catch (e) {
    console.error("[waitlist] error", e?.message || e);
    res.status(200).json({ ok: true, delivered: "log_only", error: "network" });
  }
}
