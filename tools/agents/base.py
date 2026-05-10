"""Shared infrastructure for radar agents.

Every agent inherits from `Agent` and implements `run(context)`.
The orchestrator owns the AgentContext, calls agents in dependency order,
and persists outputs to data/radar/ so existing HTML/email pipelines keep working.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RADAR_DIR = DATA_DIR / "radar"
AGENT_DIR = RADAR_DIR / "agents"

DEFAULT_MODEL = "gpt-4o-mini"
HEAVY_MODEL = "gpt-4o"
OPENAI_BUDGET_ITEMS = 40


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class AgentResult:
    name: str
    ok: bool
    duration_s: float
    written: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class AgentContext:
    run_at: str
    openai_key: str | None
    openai_calls: int = 0
    openai_budget: int = OPENAI_BUDGET_ITEMS
    log: list[dict[str, Any]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)

    def can_call_openai(self, n: int = 1) -> bool:
        if not self.openai_key:
            return False
        return self.openai_calls + n <= self.openai_budget

    def record_openai(self, n: int = 1) -> None:
        self.openai_calls += n


_OPENAI_SDK = None


def _openai_client(api_key: str):
    global _OPENAI_SDK
    if _OPENAI_SDK is None:
        try:
            from openai import OpenAI  # type: ignore
            _OPENAI_SDK = OpenAI
        except ImportError:
            return None
    return _OPENAI_SDK(api_key=api_key)


def call_openai_json(
    ctx: AgentContext,
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 800,
    temperature: float = 0.3,
) -> dict | None:
    """Single OpenAI chat call returning parsed JSON. Returns None on any failure
    so callers can fall back to rules without crashing the pipeline."""
    if not ctx.openai_key:
        return None
    client = _openai_client(ctx.openai_key)
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content or "{}"
        ctx.record_openai(1)
        return json.loads(content)
    except Exception:
        return None


class Agent:
    name: str = "agent"
    description: str = ""
    inputs: list[str] = []
    outputs: list[str] = []

    def run(self, ctx: AgentContext) -> AgentResult:  # pragma: no cover - interface
        raise NotImplementedError

    def execute(self, ctx: AgentContext) -> AgentResult:
        t0 = time.time()
        try:
            res = self.run(ctx)
            res.duration_s = round(time.time() - t0, 3)
            return res
        except Exception as exc:
            return AgentResult(
                name=self.name,
                ok=False,
                duration_s=round(time.time() - t0, 3),
                error=f"{type(exc).__name__}: {exc}",
            )


def load_signals() -> dict:
    return read_json(RADAR_DIR / "signals.json", {"items": []})


def load_corpus() -> dict:
    return read_json(RADAR_DIR / "signals_corpus.json", {"items": []})


def load_opportunities() -> dict:
    return read_json(RADAR_DIR / "opportunities.json", {"opportunities": []})


def truncate(text: str, n: int = 280) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


def safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur
