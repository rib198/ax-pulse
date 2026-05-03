#!/usr/bin/env python3
"""Enrich product playbooks with Claude when ANTHROPIC_API_KEY is available.

The script is intentionally safe by default:
- no API key: exits cleanly and keeps the manual playbooks
- dry run: validates input and prints what would be enriched
- live mode: writes a separate dynamic file so the curated base is not lost
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "radar" / "product_playbooks.json"
OUTPUT = ROOT / "data" / "radar" / "product_playbooks_dynamic.json"


SYSTEM_PROMPT = (
    "You enrich inspirational AI product ideas for an Arabic-first product called "
    "AI Radar. Keep the tone inspiring and concise, avoid guaranteed income, avoid "
    "unnecessary pricing, and mention tools only when they are essential to understand "
    "the idea. Preserve the same JSON shape."
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_prompt(data: dict) -> str:
    trimmed = {
        "note": data.get("note_en") or data.get("note_ar"),
        "playbooks": [
            {
                "id": item.get("id"),
                "title_ar": item.get("title_ar"),
                "title_en": item.get("title_en"),
                "buyer_ar": item.get("buyer_ar"),
                "product_ar": item.get("product_ar"),
                "pricing_ar": item.get("pricing_ar"),
                "saudi_lens_ar": item.get("saudi_lens_ar"),
            }
            for item in data.get("playbooks", [])
        ],
    }
    return (
        "Return JSON only with key playbooks. For each playbook, keep the same id "
        "and improve: why_ar/en, inspiration_ar/en, saudi_lens_ar/en, examples_ar/en, "
        "and seven_day_playbook_ar/en. Leave pricing empty unless it is essential. "
        "Do not add unverifiable success claims.\n\n"
        + json.dumps(trimmed, ensure_ascii=False)
    )


def call_anthropic(api_key: str, prompt: str, model: str) -> dict:
    body = {
        "model": model,
        "max_tokens": 5000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        payload = json.loads(res.read().decode("utf-8"))
    text_parts = [part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text"]
    text = "\n".join(text_parts).strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1].rsplit("\n", 1)[0]
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich AI income playbooks with Claude.")
    parser.add_argument("--live", action="store_true", help="Call Anthropic API and write dynamic output.")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Anthropic model name.")
    args = parser.parse_args()

    data = load_json(INPUT)
    playbooks = data.get("playbooks", [])
    if not playbooks:
        print("No playbooks found.")
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"playbooks: {len(playbooks)}")
    if not args.live:
      print("dry_run: true")
      print("next: run with --live after setting ANTHROPIC_API_KEY")
      return 0
    if not api_key:
        print("ANTHROPIC_API_KEY is missing; kept manual playbooks.")
        return 0

    try:
        enriched = call_anthropic(api_key, build_prompt(data), args.model)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"Claude enrichment failed: {exc}", file=sys.stderr)
        return 1

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "anthropic_api",
        "model": args.model,
        "playbooks": enriched.get("playbooks", []),
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
