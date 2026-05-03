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
DIGEST_FROM = os.environ.get("DIGEST_FROM", "AX Pulse <onboarding@resend.dev>")
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

    # ---- inline-styled email-safe HTML ----
    css_body = (
        "margin:0;padding:0;background:#0a0e16;font-family:-apple-system,BlinkMacSystemFont,"
        "'Segoe UI','IBM Plex Sans Arabic',Arial,sans-serif;color:#eef7ff;direction:rtl;"
    )
    css_wrap = "max-width:600px;margin:0 auto;padding:24px;"
    css_header = "padding:20px 0 24px;border-bottom:1px solid rgba(110,239,255,0.18);"
    css_kicker = (
        "color:#6eefff;font-size:11px;font-weight:600;letter-spacing:0.18em;"
        "text-transform:uppercase;font-family:'JetBrains Mono','Menlo',monospace;"
    )
    css_h1 = (
        "color:#fff;font-size:22px;font-weight:700;margin:8px 0 0;line-height:1.4;"
    )
    css_subtitle = "color:rgba(238,247,255,0.65);font-size:13px;margin:6px 0 0;"

    css_section_head = (
        "color:#6eefff;font-size:11px;font-weight:600;letter-spacing:0.16em;"
        "text-transform:uppercase;margin:28px 0 12px;font-family:'JetBrains Mono',monospace;"
    )

    css_opp_card = (
        "background:linear-gradient(180deg,rgba(97,241,139,0.08),rgba(97,241,139,0.02));"
        "border:1px solid rgba(97,241,139,0.32);border-radius:14px;padding:18px 20px;margin:0 0 24px;"
    )
    css_opp_title = (
        "color:#fff;font-size:17px;font-weight:700;margin:0 0 8px;line-height:1.5;"
    )
    css_opp_meta = (
        "color:rgba(97,241,139,0.86);font-size:12px;font-weight:600;margin:0 0 10px;"
        "font-family:'JetBrains Mono',monospace;"
    )
    css_opp_text = (
        "color:rgba(238,247,255,0.78);font-size:13.5px;line-height:1.7;margin:0;"
    )

    css_signal = (
        "border-bottom:1px solid rgba(255,255,255,0.06);padding:14px 0;"
        "display:block;text-decoration:none;color:#eef7ff;"
    )
    css_signal_source = (
        "color:#6eefff;font-size:10px;font-weight:600;letter-spacing:0.14em;"
        "text-transform:uppercase;font-family:'JetBrains Mono',monospace;"
    )
    css_signal_title = (
        "color:#fff;font-size:14.5px;font-weight:600;margin:6px 0 0;line-height:1.55;"
    )

    css_cta = (
        "display:inline-block;background:linear-gradient(180deg,#6eefff,#4cc8e0);"
        "color:#001017;font-weight:700;font-size:14px;padding:13px 24px;border-radius:999px;"
        "text-decoration:none;margin:8px 0;"
    )
    css_footer = (
        "border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:18px;"
        "color:rgba(238,247,255,0.40);font-size:11px;line-height:1.7;"
    )

    # ---- top opportunity section ----
    if top_opp:
        opp_title = top_opp.get("title_ar") or top_opp.get("title_en") or "—"
        opp_signals = top_opp.get("signal_count", 0)
        opp_conf = int((top_opp.get("confidence") or 0) * 100)
        opp_html = f"""
        <div style="{css_section_head}">أفضل فرصة اليوم</div>
        <div style="{css_opp_card}">
          <div style="{css_opp_meta}">
            {opp_signals} دليل · ثقة {opp_conf}%
          </div>
          <div style="{css_opp_title}">{escape_html(opp_title)}</div>
          <p style="{css_opp_text}">
            فرصة مرصودة من إشارات حقيقية في مصادر AI الرسمية والمجتمعات التقنية.
            افتح اللوحة لرؤية الأدلة كاملة والخطوات.
          </p>
        </div>
        """
    else:
        opp_html = ""

    # ---- signals section ----
    signals_html = ""
    if top_signals:
        signals_html = f'<div style="{css_section_head}">أبرز 5 إشارات</div>'
        for s in top_signals:
            url = s.get("source_url") or "#"
            src = source_label(s.get("source_id", ""))
            ttl = localized_title(s, lang="ar")
            signals_html += f"""
            <a href="{escape_html(url)}" style="{css_signal}">
              <div style="{css_signal_source}">{escape_html(src)}</div>
              <div style="{css_signal_title}">{escape_html(ttl)}</div>
            </a>
            """

    # ---- final HTML ----
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AX Pulse — نَبض اليوم</title>
</head>
<body style="{css_body}">
  <div style="{css_wrap}">

    <div style="{css_header}">
      <div style="{css_kicker}">AX PULSE · {today}</div>
      <h1 style="{css_h1}">نَبض الذكاء الاصطناعي اليوم</h1>
      <p style="{css_subtitle}">5 إشارات + فرصة مرتبة من مصادر حقيقية، بدون ضجيج.</p>
    </div>

    {opp_html}
    {signals_html}

    <div style="text-align:center;margin:32px 0 0;">
      <a href="{escape_html(SITE_URL)}/radar.html" style="{css_cta}">افتح الرادار الكامل ↗</a>
    </div>

    <div style="{css_footer}">
      تستلم هذه الرسالة لأنك مشترك في AX Pulse — نشرة الذكاء الاصطناعي اليومية.
      <br/>المصادر: OpenAI، Anthropic، Google DeepMind، Hugging Face، X، Reddit، GitHub، Hacker News، arXiv.
      <br/>للإلغاء: <a href="mailto:unsubscribe@axpulse?subject=unsubscribe" style="color:#6eefff;text-decoration:none;">أزل بريدي</a>
    </div>

  </div>
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
        return False, f"HTTP {exc.code}: {err_body[:200]}"
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
    subject = f"AX Pulse · نَبض الذكاء الاصطناعي · {today}"

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
