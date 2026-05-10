"""Agent 2 — كاشف الشركات (Companies Detector).

Pulls company / product / model mentions out of signals and tracks them
over time. Pure rules + dictionary, no OpenAI cost (the LLM budget is
reserved for the editor and opportunity builder).

Output: data/radar/agents/companies.json — used by Companies/Market panels.
"""
from __future__ import annotations

import re
from collections import Counter

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    RADAR_DIR,
    now_iso,
    read_json,
    truncate,
    write_json,
)


# Seed dictionary — extended each run with whatever the regex finds.
KNOWN_ENTITIES = {
    "openai": {"kind": "company", "products": ["chatgpt", "gpt-4", "gpt-4o", "sora", "codex", "o1", "o3"]},
    "anthropic": {"kind": "company", "products": ["claude", "claude code", "claude opus", "claude sonnet", "claude haiku", "mcp"]},
    "google": {"kind": "company", "products": ["gemini", "deepmind", "veo", "imagen", "notebooklm"]},
    "deepmind": {"kind": "lab", "products": []},
    "meta": {"kind": "company", "products": ["llama", "ray-ban", "code llama"]},
    "mistral": {"kind": "company", "products": ["mistral large", "mixtral", "codestral"]},
    "xai": {"kind": "company", "products": ["grok"]},
    "perplexity": {"kind": "company", "products": []},
    "cursor": {"kind": "tool", "products": []},
    "cohere": {"kind": "company", "products": ["command"]},
    "huggingface": {"kind": "platform", "products": []},
    "stability ai": {"kind": "company", "products": ["stable diffusion"]},
    "midjourney": {"kind": "tool", "products": []},
    "runway": {"kind": "tool", "products": ["gen-3"]},
    "elevenlabs": {"kind": "tool", "products": []},
    "replicate": {"kind": "platform", "products": []},
    "github": {"kind": "platform", "products": ["copilot"]},
    "microsoft": {"kind": "company", "products": ["azure ai", "copilot"]},
    "nvidia": {"kind": "company", "products": []},
    "groq": {"kind": "company", "products": []},
    "together": {"kind": "company", "products": []},
}


_CAP_WORD = re.compile(r"\b([A-Z][a-zA-Z0-9\-]{2,}(?:\s+[A-Z][a-zA-Z0-9\-]{2,}){0,2})\b")
_PRICE = re.compile(r"\$\s*\d+(?:\.\d+)?(?:\s*/\s*(?:mo|month|yr|year|user|seat))?", re.IGNORECASE)


def _detect_in_text(text: str) -> tuple[set[str], set[str], list[str]]:
    low = (text or "").lower()
    companies: set[str] = set()
    products: set[str] = set()
    for name, meta in KNOWN_ENTITIES.items():
        if name in low:
            if meta["kind"] in {"company", "lab", "platform"}:
                companies.add(name)
            else:
                products.add(name)
            for p in meta.get("products", []):
                if p in low:
                    products.add(p)
    prices = _PRICE.findall(text or "")
    return companies, products, prices


class CompaniesDetector(Agent):
    name = "companies_detector"
    description = "يستخرج الشركات/الأدوات/المنتجات/الأسعار المذكورة في الإشارات ويُحدّث ملف الشركات."
    inputs = ["ctx.state.tagged_items"]
    outputs = ["data/radar/agents/companies.json"]

    def run(self, ctx: AgentContext) -> AgentResult:
        items = ctx.state.get("tagged_items") or ctx.state.get("ranked_items") or []
        run_at = ctx.state.get("run_at") or now_iso()
        path = RADAR_DIR / "agents" / "companies.json"
        prev = read_json(path, {"companies": {}})
        store: dict = prev.get("companies") or {}

        company_counts: Counter[str] = Counter()
        product_counts: Counter[str] = Counter()
        price_examples: dict[str, list[str]] = {}

        for it in items:
            text = (it.get("title") or "") + " " + (it.get("text") or "")
            companies, products, prices = _detect_in_text(text)
            for c in companies:
                company_counts[c] += 1
            for p in products:
                product_counts[p] += 1
            if prices:
                key = next(iter(companies | products), None)
                if key:
                    price_examples.setdefault(key, []).extend(prices[:2])

            for name in companies | products:
                entry = store.setdefault(name, {
                    "name": name,
                    "kind": KNOWN_ENTITIES.get(name, {}).get("kind", "unknown"),
                    "first_seen": run_at,
                    "mentions": 0,
                    "last_titles": [],
                    "prices": [],
                })
                entry["mentions"] += 1
                entry["last_seen"] = run_at
                t = truncate(it.get("title") or "", 120)
                if t and t not in entry["last_titles"]:
                    entry["last_titles"] = ([t] + entry["last_titles"])[:5]
                if name in price_examples:
                    for px in price_examples[name]:
                        if px not in entry["prices"]:
                            entry["prices"] = (entry["prices"] + [px])[-6:]

        out = {
            "generated_at": run_at,
            "note_ar": "ذكر الشركات والمنتجات والأسعار في إشارات الرادار مع تتبّع تراكمي.",
            "top_companies": company_counts.most_common(15),
            "top_products": product_counts.most_common(15),
            "companies": store,
        }
        write_json(path, out)

        ctx.state["companies"] = out
        notes = [
            f"detected {len(company_counts)} companies, {len(product_counts)} products this run",
            f"store size: {len(store)}",
        ]
        return AgentResult(name=self.name, ok=True, duration_s=0.0, written=[str(path.relative_to(RADAR_DIR.parent.parent))], notes=notes)
