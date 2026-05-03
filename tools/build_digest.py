#!/usr/bin/env python3
"""
AX Pulse — Daily Email Digest Builder

- Reads data/radar/signals.json + opportunities.json
- Builds a clean Arabic HTML email (mobile-first, RTL, inline CSS)
- Sends to all subscribers via Resend API

Env required:
- RESEND_API_KEY        (mandatory)
- DIGEST_FROM           (optional, default: AX Pulse <onboarding@resend.dev>)
- SITE_URL              (optional, default: https://rib198.github.io/ax-pulse)
- DRY_RUN               (optional, set to "1" to skip sending)

Stdlib only — no pip install required.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIGNALS_FILE = ROOT / "data" / "radar" / "signals.json"
OPPS_FILE = ROOT / "data" / "radar" / "opportunities.json"
SUBSCRIBERS_FILE = ROOT / "data" / "subscribers.json"

SITE_URL = os.environ.get("SITE_URL", "https://rib198.github.io/ax-pulse")
DIGEST_FROM = os.environ.get("DIGEST_FROM", "onboarding@resend.dev")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log(f"  ⚠ {path.name}: {exc}")
        return fallback


def localized_title(item, lang="ar") -> str:
    if lang == "ar" and item.get("title_ar"):
        return item["title_ar"]
    return item.get("title") or ""


def source_label(source_id: str) -> str:
    return {
        "x_recent_search": "X",
        "github_repos": "GitHub",
        "openai_news": "OpenAI",
        "google_deepmind": "DeepMind",
        "techcrunch_ai": "TechCrunch",
        "reddit_artificial": "Reddit AI",
        "reddit_machinelearning": "Reddit ML",
        "hn_algolia": "Hacker News",
        "anthropic_news": "Anthropic",
        "huggingface_blog": "Hugging Face",
        "tldr_ai": "TLDR AI",
    }.get(source_id, source_id or "Source")


def escape_html(text: str) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_html(signals, top_opp):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    top_signals = signals[:5]
    radar_url = f"{SITE_URL}/radar.html"

    # ---- top opportunity block ----
    if top_opp:
        opp_title = top_opp.get("title_ar") or top_opp.get("title_en") or "—"
        opp_signals = top_opp.get("signal_count", 0)
        opp_conf = int((top_opp.get("confidence") or 0) * 100)
        opp_html = f"""
        <tr>
          <td style="padding:32px 0 14px">
            <div style="color:#61f18b;font-size:11px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase;font-family:'JetBrains Mono',Menlo,monospace">▸ أفضل فرصة اليوم</div>
          </td>
        </tr>
        <tr>
          <td style="padding:0 0 8px">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:linear-gradient(180deg,rgba(97,241,139,0.10),rgba(97,241,139,0.02));border:1px solid rgba(97,241,139,0.32);border-radius:16px">
              <tr>
                <td style="padding:22px 24px">
                  <div style="color:#61f18b;font-size:11px;font-weight:600;font-family:'JetBrains Mono',Menlo,monospace;letter-spacing:0.06em;margin-bottom:10px">
                    {opp_signals} دليل &nbsp;·&nbsp; ثقة {opp_conf}%
                  </div>
                  <div style="color:#fff;font-size:18px;font-weight:700;line-height:1.55;margin-bottom:10px">{escape_html(opp_title)}</div>
                  <div style="color:rgba(230,239,255,0.74);font-size:13.5px;line-height:1.85">
                    فرصة مرصودة من إشارات حقيقية في مصادر AI الرسمية والمجتمعات التقنية. افتح الرادار لرؤية الأدلة الكاملة وخطوات التنفيذ.
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """
    else:
        opp_html = ""

    # ---- signals block ----
    signals_html = ""
    if top_signals:
        signals_html = """
        <tr>
          <td style="padding:32px 0 14px">
            <div style="color:#6eefff;font-size:11px;font-weight:600;letter-spacing:0.18em;text-transform:uppercase;font-family:'JetBrains Mono',Menlo,monospace">▸ أبرز 5 إشارات</div>
          </td>
        </tr>
        """
        rows = []
        for s in top_signals:
            url = s.get("source_url") or "#"
            src = source_label(s.get("source_id", ""))
            ttl = localized_title(s, lang="ar")
            rows.append(f"""
            <tr>
              <td style="padding:0">
                <a href="{escape_html(url)}" style="display:block;padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.06);text-decoration:none">
                  <div style="color:#6eefff;font-size:10px;font-weight:600;letter-spacing:0.16em;text-transform:uppercase;font-family:'JetBrains Mono',Menlo,monospace;margin-bottom:6px">{escape_html(src)}</div>
                  <div style="color:#fff;font-size:14.5px;font-weight:600;line-height:1.6">{escape_html(ttl)}</div>
                </a>
              </td>
            </tr>
            """)
        signals_html += f"""
        <tr>
          <td style="padding:0">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              {''.join(rows)}
            </table>
          </td>
        </tr>
        """

    # ---- final HTML (table-based, email-client safe) ----
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="dark only" />
  <meta name="supported-color-schemes" content="dark only" />
  <title>رادار الذكاء الاصطناعي · {today}</title>
</head>
<body style="margin:0;padding:0;background-color:#08090a;color:#eef7ff;font-family:-apple-system,BlinkMacSystemFont,'IBM Plex Sans Arabic','Segoe UI',Tahoma,Arial,sans-serif;direction:rtl">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#08090a">
    <tr>
      <td align="center" style="padding:32px 16px">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%">

          <!-- HEADER -->
          <tr>
            <td style="padding:0 0 24px;border-bottom:1px solid rgba(110,239,255,0.16)">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="right" style="vertical-align:middle">
                    <span style="display:inline-block;padding:6px 14px;background-color:rgba(110,239,255,0.10);border:1px solid rgba(110,239,255,0.32);border-radius:999px;color:#6eefff;font-size:11px;font-weight:600;letter-spacing:0.16em;font-family:'JetBrains Mono',Menlo,monospace">RADAR · {today}</span>
                  </td>
                  <td align="left" style="vertical-align:middle">
                    <span style="display:inline-block;padding:8px 14px;background:linear-gradient(180deg,rgba(110,239,255,0.16),rgba(110,239,255,0.06));border:1px solid rgba(110,239,255,0.28);border-radius:10px;color:#6eefff;font-size:13px;font-weight:700;font-family:'JetBrains Mono',Menlo,monospace;letter-spacing:0.06em">رادار</span>
                  </td>
                </tr>
              </table>
              <h1 style="margin:24px 0 8px;color:#ffffff;font-size:26px;font-weight:700;line-height:1.45">رادار الذكاء الاصطناعي</h1>
              <p style="margin:0;color:rgba(238,247,255,0.62);font-size:14px;line-height:1.75">5 إشارات + فرصة منتج يومياً، من مصادر AI الموثوقة. بدون ضجيج.</p>
            </td>
          </tr>

          {opp_html}

          {signals_html}

          <!-- CTA -->
          <tr>
            <td align="center" style="padding:40px 0 16px">
              <a href="{escape_html(radar_url)}" style="display:inline-block;padding:14px 30px;background:linear-gradient(180deg,#6eefff,#4cc8e0);color:#001017;font-weight:700;font-size:14px;text-decoration:none;border-radius:999px;letter-spacing:0.02em">
                افتح الرادار الكامل  ↗
              </a>
            </td>
          </tr>

          <!-- DIVIDER -->
          <tr>
            <td style="padding:24px 0 0">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="height:1px;background:linear-gradient(90deg,transparent,rgba(110,239,255,0.22),transparent);font-size:0;line-height:0">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding:24px 0 8px;color:rgba(238,247,255,0.42);font-size:11px;line-height:1.85">
              تستلم هذه الرسالة لأنك مشترك في <strong style="color:rgba(110,239,255,0.86);font-weight:600">رادار الذكاء الاصطناعي</strong>.
              <br/>
              المصادر: OpenAI، Anthropic، Google DeepMind، Hugging Face، X، Reddit، GitHub، Hacker News، arXiv.
            </td>
          </tr>
          <tr>
            <td style="padding:0 0 16px;color:rgba(238,247,255,0.32);font-size:11px">
              <a href="mailto:unsubscribe@axpulse?subject=unsubscribe" style="color:rgba(110,239,255,0.62);text-decoration:none">إلغاء الاشتراك</a>
              &nbsp;·&nbsp;
              <a href="{escape_html(SITE_URL)}" style="color:rgba(110,239,255,0.62);text-decoration:none">الموقع</a>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_via_resend(to_email, subject, html):
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY not set"

    payload = json.dumps(
        {"from": DIGEST_FROM, "to": [to_email], "subject": subject, "html": html}
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "AX-Pulse/1.0 (digest-sender)",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            return True, data.get("id", "ok")
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8")
        except Exception:
            err_body = str(exc)
        return False, f"HTTP {exc.code}: {err_body}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    sig = load_json(SIGNALS_FILE, {"items": []})
    opps = load_json(OPPS_FILE, {"opportunities": []})
    subs = load_json(SUBSCRIBERS_FILE, {"subscribers": []})

    signals = sig.get("items", [])
    opportunities = opps.get("opportunities", [])
    subscribers = [s for s in subs.get("subscribers", []) if isinstance(s, str) and "@" in s]

    log(f"  signals available: {len(signals)}")
    log(f"  opportunities:     {len(opportunities)}")
    log(f"  subscribers:       {len(subscribers)}")

    if not signals and not opportunities:
        log("  ⚠ no content — skipping send")
        return 0

    if not subscribers:
        log("  ⚠ no subscribers — skipping send")
        return 0

    html = build_html(signals, opportunities[0] if opportunities else None)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"رادار الذكاء الاصطناعي · {today}"

    if DRY_RUN:
        log("  → DRY_RUN — would send to:")
        for email in subscribers:
            log(f"    • {email}")
        out_file = ROOT / "tmp" / f"digest-{today}.html"
        out_file.parent.mkdir(exist_ok=True)
        out_file.write_text(html, encoding="utf-8")
        log(f"  ✓ preview written: {out_file.relative_to(ROOT)}")
        return 0

    if not RESEND_API_KEY:
        log("  ✗ RESEND_API_KEY missing — cannot send")
        return 1

    sent = 0
    failed = []
    for email in subscribers:
        ok, info = send_via_resend(email, subject, html)
        if ok:
            sent += 1
            log(f"  ✓ {email}  →  {info}")
        else:
            failed.append((email, info))
            log(f"  ✗ {email}  →  {info}")

    log(f"\n  ────────── ملخص ──────────")
    log(f"  مرسل: {sent}/{len(subscribers)}")
    log(f"  فشل:  {len(failed)}")
    return 0 if sent > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
