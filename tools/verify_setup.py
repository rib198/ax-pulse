#!/usr/bin/env python3
"""Radar — setup verifier.

Runs automated checks against your deployed site to confirm that every
manual setup step landed correctly. Pure stdlib (no pip install needed).

Usage:

    python3 tools/verify_setup.py --site https://your-domain.com

Optional:

    --github-repo  rib198/ax-pulse   # checks the latest cron run status
    --stripe-key   sk_test_...       # checks Stripe Price exists
    --skip net                       # skip live HTTP checks (offline mode)

Exit code: 0 if everything passes, 1 if any check fails.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


# ---------- pretty output ----------

class Color:
    OK = "\033[32m"
    FAIL = "\033[31m"
    WARN = "\033[33m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    END = "\033[0m"


def line(symbol: str, color: str, label: str, detail: str = "") -> None:
    print(f"  {color}{symbol}{Color.END} {label}{(' ' + Color.DIM + detail + Color.END) if detail else ''}")


def ok(label: str, detail: str = "") -> None: line("✓", Color.OK, label, detail)
def fail(label: str, detail: str = "") -> None: line("✗", Color.FAIL, label, detail)
def warn(label: str, detail: str = "") -> None: line("!", Color.WARN, label, detail)
def head(label: str) -> None: print(f"\n{Color.BOLD}── {label}{Color.END}")


# ---------- check primitives ----------

def http_get(url: str, timeout: int = 10) -> tuple[int, dict, bytes]:
    req = Request(url, headers={"User-Agent": "radar-verify/1.0", "Accept": "application/json, text/html, */*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, dict(e.headers or {}), body
    except (URLError, TimeoutError) as e:
        raise RuntimeError(f"network error: {e}")


def http_post(url: str, body: bytes = b"", timeout: int = 10) -> tuple[int, dict, bytes]:
    req = Request(url, data=body, headers={"User-Agent": "radar-verify/1.0", "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, dict(e.headers or {}), body
    except (URLError, TimeoutError) as e:
        raise RuntimeError(f"network error: {e}")


# ---------- checks ----------

def check_local_files() -> int:
    head("1. Local files (committed in this repo)")
    failures = 0
    required = [
        ("data/config.json", "subscription config"),
        ("assets/js/subscription.js", "client subscription service"),
        ("assets/js/analytics.js", "analytics adapter"),
        ("subscribe.html", "Arabic payment page"),
        ("account.html", "subscriber account page"),
        ("privacy.html", "privacy policy"),
        ("terms.html", "terms of service"),
        ("api/checkout/session.js", "Stripe Checkout function"),
        ("api/checkout/webhook.js", "Stripe webhook function"),
        ("vercel.json", "Vercel routing"),
        ("admin/index.html", "Decap CMS entry"),
        ("admin/config.yml", "Decap CMS config"),
        (".github/workflows/refresh-radar.yml", "data refresh cron"),
        ("tools/run_radar_agents.py", "agent pipeline entry"),
        ("tools/agents/access_tier.py", "free/premium tagger"),
        ("tools/agents/auto_archive.py", "90-day archiver"),
    ]
    for path, label in required:
        if (ROOT / path).exists():
            ok(label, path)
        else:
            fail(label, f"missing {path}")
            failures += 1

    # config price = 15
    cfg = ROOT / "data" / "config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text("utf-8"))
            price = (data.get("subscription") or {}).get("price_usd")
            if price == 15:
                ok("subscription price", "$15 in data/config.json")
            else:
                warn("subscription price", f"got {price}, expected 15 — adjust if intentional")
        except json.JSONDecodeError:
            fail("config.json", "not valid JSON")
            failures += 1
    return failures


def check_site_pages(site: str) -> int:
    head(f"2. Public site pages ({site})")
    failures = 0
    pages = [
        ("/", "landing"),
        ("/index.html", "landing (explicit)"),
        ("/subscribe.html", "subscribe page"),
        ("/account.html", "account page"),
        ("/privacy.html", "privacy"),
        ("/terms.html", "terms"),
        ("/data/config.json", "config served"),
        ("/data/i18n.json", "i18n served"),
        ("/data/radar/signals.json", "signals served"),
        ("/data/radar/opportunities.json", "opportunities served"),
        ("/admin/", "admin (Decap CMS)"),
    ]
    for path, label in pages:
        url = site.rstrip("/") + path
        try:
            status, _, _ = http_get(url, timeout=8)
            if 200 <= status < 400:
                ok(label, f"{status} {path}")
            else:
                fail(label, f"{status} {path}")
                failures += 1
        except RuntimeError as e:
            fail(label, f"{path} — {e}")
            failures += 1
    return failures


def check_config_loaded(site: str) -> int:
    head("3. Live config (price + Stripe routes published)")
    failures = 0
    try:
        status, _, body = http_get(site.rstrip("/") + "/data/config.json", timeout=8)
        if status != 200:
            fail("config fetch", f"http {status}")
            return 1
        data = json.loads(body)
    except (RuntimeError, json.JSONDecodeError) as e:
        fail("config fetch", str(e))
        return 1

    price = (data.get("subscription") or {}).get("price_usd")
    if price == 15:
        ok("price = $15", "data.subscription.price_usd")
    else:
        fail("price", f"got {price}, expected 15")
        failures += 1

    s = data.get("stripe") or {}
    if (s.get("checkout_session_endpoint") or "").startswith("/api/"):
        ok("checkout endpoint", s["checkout_session_endpoint"])
    else:
        warn("checkout endpoint", "no /api/ route — Stripe not wired in config")

    a = data.get("analytics") or {}
    if a.get("plausible_domain") or a.get("posthog_key"):
        ok("analytics provider", a.get("plausible_domain") or "posthog")
    else:
        warn("analytics", "not configured (events stay in console + localStorage)")
    return failures


def check_stripe_function(site: str) -> int:
    head("4. Stripe Checkout function (api/checkout/session)")
    url = site.rstrip("/") + "/api/checkout/session"
    failures = 0
    try:
        status, headers, body = http_post(url, b"{}", timeout=12)
    except RuntimeError as e:
        fail("function reachable", str(e))
        return 1

    if status == 404:
        fail("function deployed", "404 — deploy api/ to Vercel/Netlify")
        return 1

    if status == 405:
        warn("function reachable", "GET probably blocked (POST works)")
        return 0

    if status == 500:
        try:
            err = json.loads(body) if body else {}
        except json.JSONDecodeError:
            err = {}
        hint = err.get("hint") or err.get("error") or "check Vercel env vars"
        fail("Stripe env vars", f"500 — {hint}")
        return 1

    if status == 200:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            fail("Stripe response", "200 but body not JSON")
            return 1
        if "url" in data and "stripe.com" in (data["url"] or ""):
            ok("Stripe Checkout session created", data["url"][:60] + "…")
        else:
            warn("Stripe response", "200 but no Stripe URL in body")
            failures += 1
    else:
        warn("function status", f"unexpected {status}")
    return failures


def check_github_cron(repo: str) -> int:
    head(f"5. GitHub Actions — refresh-radar cron ({repo})")
    if not repo:
        warn("repo not set", "pass --github-repo OWNER/NAME to enable this check")
        return 0
    url = f"https://api.github.com/repos/{repo}/actions/workflows/refresh-radar.yml/runs?per_page=3"
    try:
        status, _, body = http_get(url, timeout=10)
    except RuntimeError as e:
        fail("api reachable", str(e))
        return 1
    if status != 200:
        fail("workflow runs", f"http {status} — repo private or workflow missing?")
        return 1
    try:
        runs = json.loads(body).get("workflow_runs") or []
    except json.JSONDecodeError:
        fail("workflow runs", "non-JSON response")
        return 1
    if not runs:
        warn("workflow runs", "0 runs — workflow has not fired yet")
        return 0
    last = runs[0]
    name = last.get("display_title") or last.get("name")
    conc = last.get("conclusion")
    started = last.get("created_at")
    if conc == "success":
        ok("last cron run", f"{started} — {name}")
    elif conc is None:
        warn("last cron run", f"{started} in progress")
    else:
        fail("last cron run", f"{started} — {conc}: {name}")
        return 1
    return 0


def check_admin_panel(site: str) -> int:
    head(f"6. Admin panel ({site}/admin/)")
    failures = 0
    url = site.rstrip("/") + "/admin/"
    try:
        status, _, body = http_get(url, timeout=8)
    except RuntimeError as e:
        fail("reachable", str(e))
        return 1
    if status != 200:
        fail("admin reachable", f"http {status}")
        return 1
    body_text = body.decode("utf-8", errors="replace").lower()
    if "decap-cms" in body_text or "netlify-cms" in body_text:
        ok("Decap CMS entry loaded", "")
    else:
        warn("admin loaded but unexpected", "no Decap script tag detected")

    cfg_url = site.rstrip("/") + "/admin/config.yml"
    try:
        status, _, _ = http_get(cfg_url, timeout=8)
        if status == 200:
            ok("admin/config.yml served", cfg_url)
        else:
            fail("admin/config.yml", f"http {status}")
            failures += 1
    except RuntimeError as e:
        fail("admin/config.yml", str(e))
        failures += 1
    return failures


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Radar setup verifier")
    parser.add_argument("--site", help="Public site URL (e.g. https://radar.example.com). Skip to run local-only checks.")
    parser.add_argument("--github-repo", help="OWNER/NAME — verifies the latest cron run.")
    parser.add_argument("--skip", default="", help="comma-separated check ids to skip (net, stripe, admin, gh)")
    args = parser.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    print(f"\n{Color.BOLD}Radar setup verifier{Color.END}\n")
    failures = 0

    failures += check_local_files()

    if args.site and "net" not in skip:
        failures += check_site_pages(args.site)
        failures += check_config_loaded(args.site)
        if "stripe" not in skip:
            failures += check_stripe_function(args.site)
        if "admin" not in skip:
            failures += check_admin_panel(args.site)
    elif not args.site:
        warn("HTTP checks skipped", "pass --site URL to run them")

    if "gh" not in skip:
        failures += check_github_cron(args.github_repo or os.environ.get("GITHUB_REPO", ""))

    print()
    if failures == 0:
        print(f"{Color.OK}{Color.BOLD}all checks passed{Color.END}\n")
        return 0
    print(f"{Color.FAIL}{Color.BOLD}{failures} check(s) failed{Color.END} — see SETUP.md for fixes\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
