/* Waitlist signup — serverless POST endpoint.
 *
 * Persistent storage strategy: Resend Audiences. Each signup is added as a
 * contact to the configured audience so you have a real exportable list and
 * can later broadcast the launch announcement to everyone with one click in
 * the Resend dashboard. We also send the operator a notification email per
 * signup so you see new signups in real time.
 *
 * Required Vercel env vars:
 *   RESEND_API_KEY      — re_... from resend.com (free tier covers 3k/mo)
 *   RESEND_AUDIENCE_ID  — uuid of the audience to add contacts into
 *                         (create one at resend.com/audiences, copy the ID)
 *
 * Optional:
 *   WAITLIST_TO         — destination for the operator notification email
 *                         (defaults to rawabialkhalaf3@gmail.com)
 *   DIGEST_FROM         — sender email (defaults to onboarding@resend.dev
 *                         which works without DNS setup)
 *
 * Graceful degradation: every missing piece returns 200 so the form UX keeps
 * working. The "delivered" field in the response says what actually happened:
 *   audience+email | audience_only | email_only | log_only
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

  console.log("[waitlist]", JSON.stringify(entry));

  const key = process.env.RESEND_API_KEY;
  if (!key) {
    res.status(200).json({ ok: true, delivered: "log_only", note: "RESEND_API_KEY not set" });
    return;
  }

  // Parallel: add to audience (persistent list) + email operator (immediate ping).
  // Either failing on its own doesn't break the other.
  const audienceId = process.env.RESEND_AUDIENCE_ID;
  const to = process.env.WAITLIST_TO || DEFAULT_TO;
  const from = process.env.DIGEST_FROM || "الرادار <onboarding@resend.dev>";

  const tasks = [];

  // Task 1 — add to Resend Audience (the persistent list)
  if (audienceId) {
    tasks.push(
      fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
        method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
        body: JSON.stringify({ email, unsubscribed: false }),
      }).then(async (r) => {
        // 200/201 = created. 422 = already in audience (treat as success).
        if (r.ok || r.status === 422) return { task: "audience", ok: true };
        const body = await r.text();
        console.error("[waitlist] audience_error", r.status, body.slice(0, 200));
        return { task: "audience", ok: false, status: r.status };
      }).catch((e) => {
        console.error("[waitlist] audience_throw", e?.message || e);
        return { task: "audience", ok: false, error: "network" };
      })
    );
  }

  // Task 2 — operator notification email
  tasks.push(
    fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
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
          "",
          audienceId ? "↳ Also added to your Resend audience for broadcast later." : "↳ (No audience configured — set RESEND_AUDIENCE_ID for persistent storage.)",
        ].join("\n"),
        reply_to: email,
      }),
    }).then(async (r) => {
      if (r.ok) return { task: "email", ok: true };
      const body = await r.text();
      console.error("[waitlist] email_error", r.status, body.slice(0, 200));
      return { task: "email", ok: false, status: r.status };
    }).catch((e) => {
      console.error("[waitlist] email_throw", e?.message || e);
      return { task: "email", ok: false, error: "network" };
    })
  );

  const results = await Promise.all(tasks);
  const audienceOk = results.find((r) => r.task === "audience")?.ok === true;
  const emailOk    = results.find((r) => r.task === "email")?.ok === true;

  let delivered;
  if (audienceOk && emailOk) delivered = "audience+email";
  else if (audienceOk)        delivered = "audience_only";
  else if (emailOk)           delivered = "email_only";
  else                        delivered = "log_only";

  res.status(200).json({
    ok: true,
    delivered,
    audience_configured: Boolean(audienceId),
  });
}
