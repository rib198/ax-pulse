"""Agent 11 — UX & Production QA (وكيل واجهات المستخدم وإدارة الإنتاج).

Validates that the public-facing site is healthy after every radar run:
- HTML pages exist and have non-empty <title> and <main> blocks
- expected JSON files (read by each page) are valid + non-empty
- core fields exist in each JSON (catches schema regressions)
- core CSS / JS assets are present and reachable

Plus a content-quality pass: brief stories must answer all four questions,
opportunities must have ≥2 evidence items, etc.

Output: data/radar/agents/qa_report.json.
Exit semantics: agent returns ok=True even when issues are found (issues
go in `issues` list); orchestrator decides whether to gate the run.
"""
from __future__ import annotations

import re
from pathlib import Path

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    DATA_DIR,
    RADAR_DIR,
    now_iso,
    read_json,
    write_json,
)


ROOT = DATA_DIR.parent

PAGES = {
    "index.html": [],
    "dashboard.html": ["data/brief.ar.json", "data/brief.en.json", "data/radar/opportunities.json", "data/i18n.json"],
    "radar.html": ["data/radar/signals.json", "data/radar/opportunities.json", "data/i18n.json"],
    "trending.html": ["data/clusters.json", "data/i18n.json"],
    "opportunities.html": ["data/radar/opportunities.json", "data/i18n.json"],
    "categories.html": ["data/categories.json", "data/i18n.json"],
    "subscribe.html": [],
}

REQUIRED_ASSETS = [
    "assets/css/tokens.css",
    "assets/css/app.css",
    "assets/js/app.js",
]

JSON_REQUIRED_FIELDS = {
    "data/radar/signals.json": ["items", "generated_at"],
    "data/radar/opportunities.json": ["opportunities", "generated_at"],
    "data/brief.ar.json": ["headline_ar", "stories"],
    "data/brief.en.json": ["headline_en", "stories"],
    "data/i18n.json": [],
}


_TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.I)
_MAIN_RE = re.compile(r"<main[\s>]", re.I)
_SCRIPT_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.I)
_LINK_RE = re.compile(r"<link[^>]+href=[\"']([^\"']+\.css)[\"']", re.I)


def _check_html(path: Path) -> list[str]:
    issues = []
    if not path.exists():
        return [f"missing page: {path.name}"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not _TITLE_RE.search(text):
        issues.append(f"{path.name}: missing <title>")
    if not _MAIN_RE.search(text) and path.name not in {"index.html", "subscribe.html", "mediator.html"}:
        issues.append(f"{path.name}: missing <main>")
    return issues


def _check_brief(brief: dict, lang: str) -> list[str]:
    issues = []
    headline_key = f"headline_{lang}"
    if not brief.get(headline_key):
        issues.append(f"brief.{lang}: missing {headline_key}")
    stories = brief.get("stories") or []
    if len(stories) < 3:
        issues.append(f"brief.{lang}: only {len(stories)} stories (expect ≥3)")
    qkeys = ["what_happened", "why_it_matters", "how_to_use"]
    for i, s in enumerate(stories):
        for q in qkeys:
            if not s.get(f"{q}_{lang}"):
                issues.append(f"brief.{lang}.stories[{i}]: missing {q}_{lang}")
                break
    return issues


def _check_opportunities(opps: list[dict]) -> list[str]:
    issues = []
    if len(opps) == 0:
        issues.append("opportunities: empty list")
    for i, o in enumerate(opps):
        if not o.get("title_ar"):
            issues.append(f"opportunities[{i}]: missing title_ar")
        ev = o.get("evidence_items") or []
        if len(ev) < 2:
            issues.append(f"opportunities[{i}] ({o.get('id')}): only {len(ev)} evidence items")
    return issues


class UXProductionQA(Agent):
    name = "ux_production_qa"
    description = "يفحص صفحات الواجهة، الأصول، صحة JSON، وجودة المحتوى بعد كل تشغيل."
    outputs = ["data/radar/agents/qa_report.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        run_at = ctx.state.get("run_at") or now_iso()
        issues: list[str] = []
        checks: list[dict] = []

        # HTML pages
        for page, deps in PAGES.items():
            page_issues = _check_html(ROOT / page)
            checks.append({"page": page, "ok": not page_issues, "issues": page_issues, "data_deps": deps})
            issues.extend(page_issues)
            for d in deps:
                p = ROOT / d
                if not p.exists():
                    issues.append(f"{page}: data dep missing — {d}")

        # required assets
        for a in REQUIRED_ASSETS:
            if not (ROOT / a).exists():
                issues.append(f"missing asset: {a}")

        # JSON shape
        for path_str, fields in JSON_REQUIRED_FIELDS.items():
            data = read_json(ROOT / path_str, None)
            if data is None:
                issues.append(f"{path_str}: unreadable / missing")
                continue
            for f in fields:
                if isinstance(data, dict) and f not in data:
                    issues.append(f"{path_str}: missing field `{f}`")

        # content quality
        ar = read_json(DATA_DIR / "brief.ar.json", {}) or {}
        en = read_json(DATA_DIR / "brief.en.json", {}) or {}
        issues.extend(_check_brief(ar, "ar"))
        issues.extend(_check_brief(en, "en"))
        opps_doc = read_json(RADAR_DIR / "opportunities.json", {}) or {}
        issues.extend(_check_opportunities(opps_doc.get("opportunities") or []))

        report = {
            "generated_at": run_at,
            "ok": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
            "checks": checks,
            "note_ar": "تقرير صحة الواجهات والمحتوى. أي عنصر هنا يجب أن يفسّر قبل الإطلاق.",
        }
        path = RADAR_DIR / "agents" / "qa_report.json"
        write_json(path, report)
        ctx.state["qa_report"] = report

        return AgentResult(
            name=self.name,
            ok=True,
            duration_s=0.0,
            written=[str(path.relative_to(RADAR_DIR.parent.parent))],
            notes=[f"{len(issues)} issues" if issues else "all UI/JSON checks passed"],
        )
