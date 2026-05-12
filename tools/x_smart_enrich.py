#!/usr/bin/env python3
"""Smart X enricher — re-scores manually-captured tweets on five axes.

Reads data/manual_x/posts.json, computes:

    radar_score = 0.30 * pain
                + 0.20 * launch
                + 0.25 * relevance
                + 0.15 * quality
                + 0.10 * arab_market

It also:
  - auto-fills `matched_keywords` from the AI/pain/launch/dev/business vocab
  - auto-fills `opportunity_tags` with entities (companies/models) mentioned
  - reclassifies `signal_type` (pain | launch | discussion | news)
  - detects spam patterns and demotes them
  - detects near-duplicates and marks them `is_duplicate_of` (only the highest-
    scoring of a cluster keeps a non-zero score)
  - sorts the items array by radar_score so the top of the file is the strongest

Writes back to the same file in-place. Originals are preserved; new fields are
added (or refreshed). Run any time — idempotent.

Subcommands:
  python3 tools/x_smart_enrich.py            # enrich + write back
  python3 tools/x_smart_enrich.py --report   # enrich + show top 10
  python3 tools/x_smart_enrich.py --dry-run  # enrich in memory, don't save
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_PATH = ROOT / "data" / "manual_x" / "posts.json"

# ---------- Vocab ----------
# Curated for the AI builder space. Keep concise — too broad = noise.

AI_TERMS = [
    "ai", "llm", "agent", "agents", "model", "models", "claude", "chatgpt", "gpt",
    "openai", "anthropic", "gemini", "deepmind", "mistral", "llama", "grok",
    "huggingface", "hf", "rag", "mcp", "prompt", "prompts", "fine-tune", "embedding",
    "vector", "ذكاء", "نموذج", "وكيل", "وكلاء",
]
PAIN_TERMS = [
    "broken", "bug", "buggy", "frustrat", "annoying", "wish", "wishlist",
    "need a", "needs a", "missing", "fails", "fail", "slow", "expensive",
    "overpriced", "hate", "impossible", "painful", "problem", "issues",
    "stuck", "lost hours", "took forever", "doesn't work", "regret",
    "مشكلة", "صعب", "بطيء", "غالي", "مكلف", "أتمنى", "محتاج", "احتاج", "يفشل",
]
LAUNCH_TERMS = [
    "launch", "launched", "launching", "released", "release", "announce",
    "announced", "introducing", "introduce", "introduces", "ships", "shipped",
    "available now", "now live", "drops", "dropping", "v2", "v3", "1.0", "2.0",
    "إطلاق", "أعلنت", "أصدر", "متاح",
]
OPPORTUNITY_TERMS = [
    "would pay", "would love", "should build", "could build", "needs someone",
    "looking for", "wish there was", "if only", "missing tool", "gap in",
    "underrated", "untapped", "no one is",
    "أتمنى أحد", "يحتاج", "فرصة", "ما عندي",
]
DEV_TOOL_TERMS = [
    "cursor", "claude code", "claude-code", "windsurf", "copilot", "github",
    "vscode", "vs code", "warp", "zed", "vercel", "netlify", "supabase",
    "stripe", "moyasar", "next.js", "nextjs", "react", "fastapi", "lovable",
]
BUSINESS_TERMS = [
    "saas", "subscription", "pricing", "customer", "customers", "revenue",
    "founder", "founders", "startup", "indie hacker", "indiehacker",
    "monetize", "monetization", "freemium", "paid", "client", "clients",
    "build in public", "product hunt", "producthunt",
    "اشتراك", "تسعير", "عميل", "عملاء", "ربح", "خدمة", "مشروع",
]
ARAB_GEO = [
    "saudi", "ksa", "uae", "emirates", "dubai", "qatar", "kuwait", "bahrain",
    "oman", "gcc", "mena", "khaleej", "gulf",
    "السعودية", "الإمارات", "دبي", "قطر", "الكويت", "البحرين", "عُمان", "الخليج",
]

# Known entities the radar already tracks — boost when mentioned by name
KNOWN_ENTITIES = {
    "openai", "anthropic", "google", "deepmind", "meta", "mistral", "xai",
    "perplexity", "cursor", "windsurf", "lovable", "cohere", "huggingface",
    "stability ai", "midjourney", "runway", "elevenlabs", "replicate",
    "github", "microsoft", "nvidia", "groq", "together",
    "claude", "gpt-4", "gpt-4o", "gpt-5", "o1", "o3", "gemini", "veo", "sora",
    "llama", "mixtral", "grok", "stable diffusion", "mcp",
}

# Spam / low-signal patterns
SPAM_PATTERNS = [
    r"follow\s+for\s+follow",
    r"f4f",
    r"check\s+my\s+(profile|bio)",
    r"link\s+in\s+bio",
    r"dm\s+for\s+(price|details|info)",
    r"i\s+made\s+\$\d+",
    r"buy\s+followers",
    r"airdrop",
    r"\b\$[a-z]{2,6}\b.{0,80}\bto\s+the\s+moon\b",   # crypto shill
    r"send\s+me\s+\d+\s+sol\b",
]

# ---------- Helpers ----------

ARABIC_RE = re.compile(r"[؀-ۿ]")
URL_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"@\w+")


def _density(text_lower: str, terms: list[str], word_count: int) -> float:
    """Count distinct term hits, normalize against text length."""
    if not text_lower or not word_count:
        return 0.0
    hits = sum(1 for t in terms if t in text_lower)
    raw = hits / max(word_count, 1) * 12
    return min(1.0, raw)


def _engagement_score(metrics: dict) -> float:
    """Log-scaled engagement. 1 → 0, 100 → 0.5, 10k → 1.0"""
    likes = metrics.get("likes") or 0
    reposts = metrics.get("reposts") or 0
    replies = metrics.get("replies") or 0
    quotes = metrics.get("quotes") or 0
    weighted = likes + 3 * reposts + 2 * replies + 2 * quotes
    if weighted <= 0:
        return 0.0
    return min(1.0, math.log10(weighted + 1) / 4.0)


def _detect_lang(text: str) -> str:
    """Cheap language detector — good enough for routing."""
    if ARABIC_RE.search(text):
        return "ar"
    if re.search(r"[一-鿿]", text):
        return "zh"
    if re.search(r"[぀-ゟ゠-ヿ]", text):
        return "ja"
    if re.search(r"[가-힯]", text):
        return "ko"
    return "en"


def _is_spam(text_lower: str) -> bool:
    return any(re.search(p, text_lower) for p in SPAM_PATTERNS)


def _signal_type(pain: float, launch: float, opportunity: float, has_question: bool) -> str:
    if pain >= 0.30: return "pain"
    if launch >= 0.25: return "launch"
    if opportunity >= 0.20: return "opportunity"
    if has_question: return "discussion"
    return "news"


def _found(text_lower: str, vocab: list[str]) -> list[str]:
    return [t for t in vocab if t in text_lower]


# ---------- Core enricher ----------

def enrich_one(post: dict) -> dict:
    text = (post.get("text") or "").strip()
    text_clean = MENTION_RE.sub("", URL_RE.sub("", text))
    text_lower = text.lower()
    words = re.findall(r"\w+", text_clean.lower())
    word_count = len(words)

    # ----- Per-axis -----
    pain = _density(text_lower, PAIN_TERMS, word_count)
    launch = _density(text_lower, LAUNCH_TERMS, word_count)
    opportunity = _density(text_lower, OPPORTUNITY_TERMS, word_count)
    pain_combined = min(1.0, pain + 0.5 * opportunity)

    relevance = (
        0.55 * _density(text_lower, AI_TERMS, word_count)
        + 0.25 * _density(text_lower, DEV_TOOL_TERMS, word_count)
        + 0.20 * _density(text_lower, BUSINESS_TERMS, word_count)
    )

    arab_market = 0.0
    if ARABIC_RE.search(text):
        arab_market = 1.0
    elif any(g in text_lower for g in ARAB_GEO):
        arab_market = 0.6

    # ----- Quality -----
    metrics = post.get("public_metrics") or {}
    eng = _engagement_score(metrics)

    has_url = bool(URL_RE.search(text))
    has_entity = any(e in text_lower for e in KNOWN_ENTITIES)
    is_spammy = _is_spam(text_lower)

    # Sweet-spot text length: 40-300 words = ~ a real thought.
    if 40 <= word_count <= 300:
        len_score = 1.0
    elif 15 <= word_count < 40 or 300 < word_count <= 500:
        len_score = 0.6
    else:
        len_score = 0.2

    quality = (
        0.30 * len_score
        + 0.20 * (1.0 if has_url else 0.4)
        + 0.20 * (1.0 if has_entity else 0.3)
        + 0.20 * eng
        + 0.10 * (0.0 if is_spammy else 1.0)
    )

    # ----- Composite radar score -----
    radar_score = (
        0.30 * pain_combined
        + 0.20 * launch
        + 0.25 * relevance
        + 0.15 * quality
        + 0.10 * arab_market
    )

    if is_spammy:
        radar_score *= 0.2   # heavy demotion, never zero

    # ----- Extracted enrichments -----
    found_keywords = sorted(set(
        _found(text_lower, AI_TERMS)
        + _found(text_lower, PAIN_TERMS)
        + _found(text_lower, LAUNCH_TERMS)
        + _found(text_lower, DEV_TOOL_TERMS)
        + _found(text_lower, BUSINESS_TERMS)
    ))[:20]

    found_entities = sorted({e for e in KNOWN_ENTITIES if e in text_lower})

    has_question = "?" in text or "؟" in text
    signal_type = _signal_type(pain_combined, launch, opportunity, has_question)

    # ----- Write back (preserve originals, layer enrichment) -----
    post["radar_score"] = round(radar_score, 4)
    post["pain_signal_score"] = max(float(post.get("pain_signal_score") or 0), round(pain_combined, 4))
    post["matched_keywords"] = sorted(set((post.get("matched_keywords") or []) + found_keywords))[:25]
    post["opportunity_tags"] = sorted(set((post.get("opportunity_tags") or []) + found_entities))[:15]
    post["signal_type"] = signal_type
    if not post.get("lang"):
        post["lang"] = _detect_lang(text)
    post["enrichment"] = {
        "radar_score": round(radar_score, 4),
        "pain": round(pain_combined, 4),
        "launch": round(launch, 4),
        "opportunity": round(opportunity, 4),
        "relevance": round(relevance, 4),
        "quality": round(quality, 4),
        "arab_market": round(arab_market, 4),
        "engagement": round(eng, 4),
        "len_score": round(len_score, 4),
        "is_spam": is_spammy,
        "entities": found_entities,
        "word_count": word_count,
        "signal_type": signal_type,
        "enriched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": 2,
    }
    return post


# ---------- Duplicate detection ----------

def detect_duplicates(posts: list[dict]) -> int:
    """Cluster tweets with similar prefixes. The highest-scoring of each cluster
    keeps its score; others are demoted and marked with is_duplicate_of."""
    fingerprints: dict[tuple, list[int]] = {}
    for i, p in enumerate(posts):
        text = p.get("text") or ""
        norm = URL_RE.sub("", text.lower())
        norm = MENTION_RE.sub("", norm)
        norm = re.sub(r"[^\w\s؀-ۿ]+", " ", norm).strip()
        words = norm.split()
        if not words:
            continue
        # 10-word prefix as fingerprint
        fp = tuple(words[:10])
        if fp in fingerprints:
            fingerprints[fp].append(i)
        else:
            fingerprints[fp] = [i]

    dups = 0
    for cluster in fingerprints.values():
        if len(cluster) <= 1:
            continue
        # Keep the highest radar_score post as canonical; demote others.
        ordered = sorted(cluster, key=lambda i: -posts[i].get("radar_score", 0))
        primary_id = posts[ordered[0]].get("tweet_id")
        for idx in ordered[1:]:
            posts[idx]["is_duplicate_of"] = primary_id
            posts[idx]["radar_score"] = round(posts[idx].get("radar_score", 0) * 0.1, 4)
            dups += 1
    return dups


# ---------- Main flow ----------

def enrich_file(path: Path, write: bool = True) -> tuple[dict, dict]:
    """Returns (enriched_doc, stats). The doc is always in-memory truth even
    if write=False — callers should use the returned doc for reporting."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    posts = doc.get("items") or []
    if not posts:
        return doc, {"posts": 0, "msg": "empty"}

    for p in posts:
        enrich_one(p)
    duplicates = detect_duplicates(posts)
    posts.sort(key=lambda p: -p.get("radar_score", 0))

    doc["items"] = posts
    doc["enriched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc["enrichment_version"] = 2

    if write:
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    scores = [p.get("radar_score", 0) for p in posts]
    stats = {
        "posts": len(posts),
        "duplicates": duplicates,
        "avg_score": round(sum(scores) / len(scores), 4),
        "high_signal": sum(1 for s in scores if s >= 0.35),
        "spam": sum(1 for p in posts if p.get("enrichment", {}).get("is_spam")),
        "ar_lang": sum(1 for p in posts if p.get("lang") == "ar"),
    }
    return doc, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Smart enricher for hand-captured X tweets.")
    parser.add_argument("--report", action="store_true", help="Print top 10 + stats after enriching.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write back.")
    parser.add_argument("--path", default=str(POSTS_PATH), help="Path to posts.json")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"not found: {path}")
        return 1

    doc, stats = enrich_file(path, write=not args.dry_run)
    print(f"enriched {stats['posts']} tweets — "
          f"avg radar_score {stats['avg_score']}, "
          f"{stats['high_signal']} ≥ 0.35, "
          f"{stats['duplicates']} dedup'd, "
          f"{stats['spam']} flagged spam, "
          f"{stats['ar_lang']} Arabic")

    if args.report:
        items = doc.get("items") or []
        print("\nTop 10 by radar_score:")
        for i, p in enumerate(items[:10], 1):
            e = p.get("enrichment", {})
            text = (p.get("text") or "")[:90].replace("\n", " ")
            handle = p.get("author_handle") or "?"
            print(f"  {i:>2}. {p.get('radar_score', 0):.3f}  "
                  f"[{p.get('signal_type', '?'):<10}] "
                  f"@{handle:<20}  {text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
