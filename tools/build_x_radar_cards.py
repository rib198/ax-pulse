#!/usr/bin/env python3
"""
Build per-tweet radar cards from radar-ready X posts.

For every accepted X post we produce a card that answers:
  - tool_or_topic : the named tool / model / idea (best-effort extraction)
  - what_happened_ar : a single Arabic sentence describing the concrete event
  - why_it_matters_ar : why this is interesting for an Arabic builder
  - how_to_use_ar : a small, concrete next step the user can take
  - evidence_url + tweet_id + author + original text (for verification)

Output: data/manual_x/x_radar_cards.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READY_FILE = ROOT / "data" / "manual_x" / "radar_ready_posts.json"
POSTS_FILE = ROOT / "data" / "manual_x" / "posts.json"
OUT_FILE = ROOT / "data" / "manual_x" / "x_radar_cards.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freshness import (  # noqa: E402
    annotate_card,
    load_freshness_state,
    save_freshness_state,
)


# ---------------------------------------------------------------------------
# Known tool / model registry.
# Order matters slightly: we match the most specific names first.
# ---------------------------------------------------------------------------
KNOWN_TOOLS = [
    "Claude Code", "Claude Sonnet", "Claude Opus", "Claude Haiku", "Claude",
    "GPT-5.5", "GPT-5", "GPT-4o", "GPT-4", "ChatGPT", "OpenAI",
    "Gemini 2.5", "Gemini 2", "Gemini Pro", "Gemini",
    "Grok 3", "Grok 4", "Grok",
    "Sora 2", "Sora",
    "Veo 3", "Veo 2", "Veo",
    "Runway", "Midjourney",
    "Cursor", "Codex", "Copilot", "Devin", "Cline", "Aider", "Replit Agent",
    "Bolt.new", "Lovable", "v0.dev", "v0",
    "Hugging Face", "HuggingFace",
    "Mistral", "DeepSeek", "Qwen", "Llama 3", "Llama",
    "n8n", "LangChain", "LangGraph", "CrewAI", "AutoGen",
    "Perplexity", "Notebook LM", "NotebookLM",
    "MCP", "RAG",
]


# Patterns that strongly suggest a launch/update/announcement
LAUNCH_PATTERNS = [
    r"\bjust launch(ed|ing)?\b",
    r"\bintroduc(?:ing|e)\b",
    r"\bnow available\b",
    r"\bavailable now\b",
    r"\bship(?:ped|ping)?\b",
    r"\bwe (?:built|just built|made|just made)\b",
    r"\bI (?:built|just built|made|just made)\b",
    r"\brelease(?:d|s)?\b",
    r"\bpublic beta\b",
    r"\bearly access\b",
    r"\bwait[\- ]?list (?:open|now)\b",
    r"\bأطلق(?:نا|ت)?\b",
    r"\bمتاح الآن\b",
    r"\bبنينا\b",
    r"\bبنيت\b",
]

PRICING_PATTERNS = [
    r"\bpricing\b", r"\bprice\b", r"\bsubscription\b", r"\bcredits?\b",
    r"\brate limit", r"\bfree tier\b", r"\bسعر\b", r"\bاشتراك\b", r"\bمجاني\b"
]

PAIN_PATTERNS = [
    r"\bdoesn'?t work\b", r"\bpainful\b", r"\bfrustrat", r"\btoo expensive\b",
    r"\bmissing\b", r"\bwish\b", r"\bneed\b", r"\bمشكلة\b", r"\bأحتاج\b",
    r"\bأتمنى\b", r"\bناقص\b"
]

OPPORTUNITY_PATTERNS = [
    r"\bincome\b", r"\bbusiness\b", r"\bstartup\b", r"\bservice\b",
    r"\brevenue\b", r"\bmaking \$", r"\b\$\d", r"\bدخل\b", r"\bمشروع\b",
    r"\bخدمة\b"
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def detect_lang(text: str) -> str:
    if re.search(r"[؀-ۿ]", text or ""):
        return "ar"
    if re.search(r"[぀-ヿ一-鿿가-힯]", text or ""):
        return "asia"
    return "en"


def extract_tool(text: str) -> str | None:
    if not text:
        return None
    low = text
    for tool in KNOWN_TOOLS:
        # Word-boundary match, case-insensitive
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(tool)}(?![A-Za-z0-9])", low, re.IGNORECASE):
            return tool
    # "introducing X" / "launching X" / "we built X"
    m = re.search(
        r"(?:introducing|launching|we (?:just )?built|i (?:just )?built|presenting)\s+([A-Z][A-Za-z0-9\.\-]{2,30}(?:\s+[A-Z][A-Za-z0-9\.\-]{2,30})?)",
        text,
    )
    if m:
        candidate = m.group(1).strip(" .,;:")
        # Reject any candidate that runs across line breaks (tweet text often
        # has the tool name on one line and the next sentence on another).
        if "\n" in candidate or "\r" in candidate:
            candidate = candidate.splitlines()[0].strip(" .,;:")
        # Drop trailing dot if it's the only punctuation (e.g., "E2B." → "E2B")
        candidate = candidate.rstrip(".")
        if candidate and len(candidate) >= 2:
            return candidate
    return None


def detect_event(text: str) -> str:
    low = text.lower()
    if any(re.search(p, low) for p in LAUNCH_PATTERNS):
        return "launch"
    if any(re.search(p, low) for p in PRICING_PATTERNS):
        return "pricing"
    if any(re.search(p, low) for p in OPPORTUNITY_PATTERNS):
        return "opportunity"
    if any(re.search(p, low) for p in PAIN_PATTERNS):
        return "pain"
    if re.search(r"\b(agent|agents|agentic)\b|وكلاء|وكيل", low):
        return "agent_discussion"
    return "discussion"


_URL_RE = re.compile(r"https?://\S+")
_HANDLE_RE = re.compile(r"^@\w+\s*$")
_NOISE_LINES = {"·", "—", "·"}


def _is_skippable_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _HANDLE_RE.match(stripped):
        return True
    # Pure URL lines
    if _URL_RE.fullmatch(stripped):
        return True
    # A short line that is mostly a URL (>= 80% url length)
    url_match = _URL_RE.search(stripped)
    if url_match and len(url_match.group(0)) >= len(stripped) * 0.8:
        return True
    if stripped in _NOISE_LINES:
        return True
    # Short metadata-style fragments (e.g., "2h", "May 7", "1.2K")
    if len(stripped) <= 6:
        return True
    return False


def first_meaningful_line(text: str, limit: int = 220) -> str:
    candidates = []
    for line in (text or "").splitlines():
        if _is_skippable_line(line):
            continue
        candidates.append(line.strip())
    # Prefer the longest of the first three meaningful lines so we get content,
    # not the author handle or a tiny one-word reply.
    head = candidates[:3]
    if head:
        best = max(head, key=len)
        # Strip trailing URL if present
        best = _URL_RE.sub("", best).strip(" .,;:—-")
        if best:
            return best[:limit]
    return (text or "").strip()[:limit]


# ---------------------------------------------------------------------------
# Arabic copywriter
# ---------------------------------------------------------------------------

def clean_sentence(text: str, limit: int = 210) -> str:
    text = (text or "").strip()
    text = _URL_RE.sub("", text)
    text = re.sub(r"^[^@]{0,120}@\w+\s*·\s*[^.。]+[.。]\s*", "", text)
    text = re.sub(r"^Translated from [^.。]+[.。]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .،,;:-")
    text = re.sub(r"^(Arabic post:|Translated from [^.]+\.?)\s*", "", text, flags=re.IGNORECASE)
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].strip(" .،,;:-") + "..."
    return text


def truncate_words(text: str, limit: int = 88) -> str:
    text = clean_sentence(text, limit=limit + 40)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].strip(" .،,;:-") + "..."


def is_weak_editorial_summary(text: str) -> bool:
    text = text or ""
    weak_phrases = [
        "يحتاج تسمية أوضح",
        "محتوى مرتبط بأداة",
        "إشارة من @",
        "تحديث AI مرصود",
        # Template fallbacks from filter_x_radar_ready.py that produce identical
        # titles when one author posts many tweets touching the same theme.
        "تزايد الاهتمام بتعلّم بناء المنتجات",
        "إشارة حول تزايد الاهتمام",
        "محتوى مرتبط بأداة أو استخدام للذكاء",
    ]
    return any(phrase in text for phrase in weak_phrases)


def ar_what_happened(tool: str | None, event: str, snippet_ar: str) -> str:
    label = tool or "أداة/فكرة AI"
    snippet = clean_sentence(snippet_ar)
    if snippet and detect_lang(snippet) != "ar":
        snippet = ""
    tail = f" {snippet}" if snippet else ""
    if event == "launch":
        return f"ظهر إطلاق أو تحديث مرتبط بـ {label}.{tail}"
    if event == "pricing":
        return f"ظهر نقاش حول سعر أو اشتراك أو حدود استخدام {label}.{tail}"
    if event == "opportunity":
        return f"رصدنا إشارة يمكن تحويلها إلى خدمة أو منتج حول {label}.{tail}"
    if event == "pain":
        return f"ظهر ألم أو طلب متكرر يمكن البناء عليه حول {label}.{tail}"
    if event == "agent_discussion":
        return f"النقاش يدور حول وكلاء AI وطريقة تشغيلهم عمليًا مع {label}.{tail}"
    return f"رصدنا نقاشًا مرتبطًا بالذكاء الاصطناعي حول {label}.{tail}"


def ar_why_it_matters(tool: str | None, event: str, tags: list[str]) -> str:
    label = tool or "هذا التحديث"
    if event == "launch":
        return f"{label} يكشف ميزة أو منتج جديدًا قابل للتجربة الآن، وهذا قد يفتح زاوية محتوى أو خدمة قبل أن يلاحظه السوق العربي."
    if event == "pricing":
        return f"{label} يلامس قرار الشراء؛ الفهم المبكر للسعر يساعدك على اختيار الأداة الأرخص أو تغليف خدمة بهامش واضح."
    if event == "opportunity":
        return f"{label} يقترح ربط أداة AI بحاجة سوقية محددة، وهذا أقرب لفرصة دخل من خبر تقني عام."
    if event == "pain":
        return f"{label} يكشف ألمًا حقيقيًا لمستخدم — أي ألم متكرر هو فرصة منتج أو خدمة عربية أبسط."
    if event == "agent_discussion":
        return f"{label} يندرج في موجة بناء الوكلاء؛ الفرصة هنا في تغليف طريقة التشغيل لا في إعادة بناء نموذج عام."
    if "video" in tags:
        return "الفيديو والدبلجة من أكثر فرص الدخل وضوحًا للمحتوى العربي."
    if "voice" in tags:
        return "الصوت والدبلجة والتعريب لها طلب متكرر من صناع المحتوى والشركات."
    return "الإشارة تكشف اهتمامًا متكررًا قد يتحول لاحقًا إلى فرصة محتوى أو منتج عربي."


def ar_how_to_use(tool: str | None, event: str, tags: list[str]) -> str:
    label = tool or "الفكرة"
    if event == "launch":
        return f"جرّب {label} اليوم على مهمة صغيرة، ثم وثّق التجربة بمنشور/فيديو عربي قبل غيرك."
    if event == "pricing":
        return f"قارن سعر {label} بأقرب بديل، وقدّم للعميل الحسبة بشكل واضح لتختصر قراره."
    if event == "opportunity":
        return f"اختر شريحة عملاء واحدة (متجر، مطعم، عيادة، مستقل) وحوّل {label} إلى عرض خدمة بسعر ثابت."
    if event == "pain":
        return f"اكتب الألم بكلمات العميل ثم اقترح حلًا صغيرًا مبنيًا على {label}، حتى لو كان قالبًا أو ورقة عمل."
    if event == "agent_discussion":
        return f"حضّر نموذج تشغيل صغيرًا (CLAUDE.md / قواعد / workflows) لـ {label} لفريق عربي محدد."
    if "video" in tags:
        return "اختر قناة عربية واحدة وقدّم لها خدمة دبلجة/تعريب فيديو واحد كنموذج اختبار."
    if "voice" in tags:
        return "ابدأ بصوت قصير واحد لعميل تعرفه وحوّله لخدمة شهرية بسيطة."
    return "احفظها كإشارة مبكرة، وراقب تكرار نفس الفكرة من حسابات مختلفة قبل أن تستثمر فيها."


def ar_title(tool: str | None, event: str, tags: list[str]) -> str:
    if tool:
        label = tool
        if event == "launch":
            return f"{label} — إصدار/إطلاق جديد يستحق التجربة"
        if event == "pricing":
            return f"{label} — نقاش حول السعر والقيمة"
        if event == "opportunity":
            return f"{label} — فرصة دخل أو خدمة قابلة للبناء"
        if event == "pain":
            return f"{label} — ألم متكرر يمكن تحويله لمنتج"
        if event == "agent_discussion":
            return f"{label} — نقاش حول وكلاء AI وطريقة التشغيل"
        if "video" in tags:
            return f"{label} — إشارة فيديو/دبلجة"
        if "voice" in tags:
            return f"{label} — إشارة صوت/تعريب"
        return f"{label} — إشارة AI مرصودة"
    # No tool was extracted — write a single self-contained Arabic title
    # instead of the awkward "إشارة AI — إشارة AI مرصودة" duplication.
    if event == "launch":
        return "إطلاق أو تحديث AI جديد يستحق التجربة"
    if event == "pricing":
        return "نقاش حول السعر والقيمة في أداة AI"
    if event == "opportunity":
        return "فرصة دخل أو خدمة قابلة للبناء حول AI"
    if event == "pain":
        return "ألم متكرر في أدوات AI يمكن تحويله لمنتج"
    if event == "agent_discussion":
        return "نقاش حول وكلاء AI وطريقة التشغيل"
    if "video" in tags:
        return "إشارة AI حول الفيديو والدبلجة"
    if "voice" in tags:
        return "إشارة AI حول الصوت والتعريب"
    return "إشارة AI مرصودة من X"


def title_from_item(tool: str | None, event: str, tags: list[str], item: dict) -> str:
    raw_summary = item.get("summary_ar") or ""
    raw_opportunity = item.get("product_opportunity_ar") or ""
    # The upstream filter writes a generic fallback ("إشارة من @user: محتوى
    # مرتبط بأداة...") for tweets it can't characterise specifically. Using
    # that as the title produces exactly the kind of vague card we want to
    # avoid on the radar, so drop it here.
    if is_weak_editorial_summary(raw_summary):
        raw_summary = ""
    if is_weak_editorial_summary(raw_opportunity):
        raw_opportunity = ""
    summary = clean_sentence(raw_summary)
    opportunity = clean_sentence(raw_opportunity)
    if event == "opportunity":
        seed = opportunity or summary
        seed = re.sub(r"^(فكرة خدمة|خدمة|فرصة)\s*[:：]\s*", "", seed).strip()
        if seed:
            return "فرصة: " + truncate_words(seed, 82)
    if tool:
        return ar_title(tool, event, tags)
    if summary:
        summary = re.sub(r"^(إشارة حول|فكرة خدمة)\s*[:：]?\s*", "", summary).strip()
        return truncate_words(summary, 88)
    return ar_title(tool, event, tags)


def is_generic_radar_title(title: str) -> bool:
    title = title or ""
    generic_titles = [
        "إشارة AI مرصودة من X",
        "إطلاق أو تحديث AI جديد يستحق التجربة",
        "نقاش حول السعر والقيمة في أداة AI",
        "فرصة دخل أو خدمة قابلة للبناء حول AI",
        "ألم متكرر في أدوات AI يمكن تحويله لمنتج",
        "نقاش حول وكلاء AI وطريقة التشغيل",
    ]
    return title in generic_titles


# ---------------------------------------------------------------------------
# Build cards
# ---------------------------------------------------------------------------

def make_card(item: dict) -> dict | None:
    text = (item.get("text") or "").strip()
    if not text:
        return None
    tool = extract_tool(text)
    event = detect_event(text)
    tags = list(item.get("opportunity_tags") or [])
    snippet = first_meaningful_line(text, limit=240)
    snippet_ar = snippet  # we keep the original; the radar UI handles RTL fine.
    quality = float(item.get("quality_score") or item.get("pain_signal_score") or 0.0)
    handle = (item.get("author_handle") or "").lstrip("@")
    tweet_id = str(item.get("tweet_id") or "")
    if tweet_id and not tweet_id.isdigit():
        return None
    url = item.get("url") or ""
    if not url and tweet_id and handle:
        url = f"https://x.com/{handle}/status/{tweet_id}"
    if not url:
        return None
    stored_summary = item.get("summary_ar") or ""
    if is_weak_editorial_summary(stored_summary):
        stored_summary = ""
    summary_ar = clean_sentence(stored_summary or ar_what_happened(tool, event, snippet_ar))
    why_ar = clean_sentence(item.get("why_it_matters_ar") or ar_why_it_matters(tool, event, tags), limit=260)
    opportunity_ar = clean_sentence(item.get("product_opportunity_ar") or "", limit=260)
    how_ar = opportunity_ar or ar_how_to_use(tool, event, tags)
    confidence_score = int(round(min(1.0, max(0.4, quality + 0.05)) * 100))
    event_labels_ar = {
        "launch": "إطلاق أو تحديث",
        "pricing": "سعر أو حدود",
        "opportunity": "فرصة دخل",
        "pain": "ألم مستخدم",
        "agent_discussion": "نقاش وكلاء",
        "discussion": "نقاش AI",
    }
    title_ar = title_from_item(tool, event, tags, item)
    # The raw archive may keep broad social posts, but the radar UI should not
    # surface cards that still read as "generic AI signal". Those belong in the
    # archive/review queue until an editor can name the concrete tool, pain, or
    # business angle.
    if is_generic_radar_title(title_ar):
        return None
    card = {
        "id": f"x_card_{item.get('tweet_id') or item.get('id') or ''}".strip("_"),
        "kind": "x_signal",
        "tool_or_topic": tool or "",
        "event_type": event,
        "event_type_ar": event_labels_ar.get(event, "إشارة AI"),
        "title_ar": title_ar,
        "what_happened_ar": summary_ar,
        "why_it_matters_ar": why_ar,
        "how_to_use_ar": how_ar,
        "buildable_opportunity_ar": opportunity_ar,
        "evidence_text": snippet[:600],
        "evidence_url": url,
        "source_url": url,
        "source_label": f"X / @{handle}" if handle else "X",
        "author_handle": handle,
        "tweet_id": item.get("tweet_id") or "",
        "collected_at": item.get("collected_at") or "",
        "confidence": round(confidence_score / 100, 2),
        "confidence_score": confidence_score,
        "tags": tags,
        "tool_name": tool or "",
        "lang_original": detect_lang(text),
        "verification_status": item.get("verification_status") or "playwright_visible_x",
        "display_status": "new" if item.get("source_type") in {"x_playwright", "search", "focus", "following"} else "cached",
        "why_selected_ar": clean_sentence(item.get("reason_ar") or "اختارها الرادار لأنها مرتبطة بالذكاء الاصطناعي ولديها دليل يمكن الرجوع إليه.", limit=220),
    }
    return card


def main():
    ready = load_json(READY_FILE, {"accepted": []})
    posts = load_json(POSTS_FILE, {"items": []}).get("items", [])

    # Index posts by tweet_id so we can use the canonical schema if available
    posts_by_id = {p.get("tweet_id"): p for p in posts if p.get("tweet_id")}

    cards = []
    for accepted in ready.get("accepted", []):
        # Pull richer metadata from posts.json if we have it
        canonical = posts_by_id.get(accepted.get("tweet_id"), {})
        merged = {**canonical, **accepted}
        card = make_card(merged)
        if card:
            cards.append(card)

    # Anti-flood cap: when a single author posts many tweets that resolve to
    # the same (event_type, no-tool) bucket, only keep their best 2. Otherwise
    # one prolific account (e.g. an SEO/marketing handle posting 90+ AI-agent
    # tweets in a row) drowns the radar with identical-looking cards.
    bucket = {}
    capped = []
    PER_BUCKET_LIMIT = 2
    for c in cards:
        # Cards with a specific tool name are kept (they're already concrete).
        # The cap only targets the generic "agent_discussion / no tool" pattern.
        if c.get("tool_or_topic"):
            capped.append(c)
            continue
        key = (c.get("author_handle") or "", c.get("event_type") or "")
        bucket.setdefault(key, [])
        if len(bucket[key]) < PER_BUCKET_LIMIT:
            bucket[key].append(c)
            capped.append(c)
    skipped_flood = len(cards) - len(capped)
    cards = capped

    # Annotate every card with freshness based on its underlying tweet timestamp
    freshness_state = load_freshness_state()
    for card in cards:
        # Each X card has exactly one piece of evidence — the tweet itself.
        evidence = [{
            "tweet_id": card.get("tweet_id"),
            "url": card.get("evidence_url"),
            "collected_at": card.get("collected_at"),
        }]
        annotate_card(card, freshness_state, evidence=evidence)
    save_freshness_state(freshness_state)

    # Sort: freshness first, then event type, then confidence
    freshness_priority = {
        "breaking": 0, "new_today": 1, "refreshed_today": 2,
        "this_week": 3, "older": 4,
    }
    event_priority = {
        "launch": 0, "opportunity": 1, "pain": 2,
        "agent_discussion": 3, "pricing": 4, "discussion": 5,
    }
    cards.sort(key=lambda c: (
        freshness_priority.get(c.get("freshness", "older"), 9),
        event_priority.get(c["event_type"], 9),
        -float(c.get("confidence") or 0),
        c.get("collected_at") or "",
    ))

    payload = {
        "generated_at": now_iso(),
        "source": "manual_x_radar_cards",
        "input_ready_count": len(ready.get("accepted", [])),
        "card_count": len(cards),
        "fresh_24h_count": sum(1 for c in cards if c.get("freshness") in {"breaking", "new_today", "refreshed_today"}),
        "breaking_count": sum(1 for c in cards if c.get("freshness") == "breaking"),
        "skipped_flood_cards": skipped_flood,
        "rules_ar": [
            "كل بطاقة تذكر أداة/موضوعًا واضحًا، ماذا حدث، لماذا يهم، وكيف تستفيد.",
            "البطاقة دائمًا مرتبطة بتغريدة قابلة للتحقق منها.",
            "البطاقات الأحدث تُعرض أولًا (breaking → new_today → refreshed_today).",
        ],
        "cards": cards,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_FILE.relative_to(ROOT)),
        "card_count": len(cards),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
