#!/usr/bin/env python3
import argparse
import os
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "radar"
RAW_FILE = OUT_DIR / "raw_items.json"
SIGNALS_FILE = OUT_DIR / "signals.json"
OPPS_FILE = OUT_DIR / "opportunities.json"
CORPUS_FILE = OUT_DIR / "signals_corpus.json"
HISTORY_DIR = OUT_DIR / "history"

KEYWORDS = [
    "ai", "llm", "agent", "agents", "claude", "chatgpt", "openai", "anthropic",
    "cursor", "gemini", "deepmind", "sora", "veo", "model", "mcp", "codex",
    "ذكاء", "كلاود", "شات", "وكلاء", "نموذج",
    "人工知能", "生成ai", "自動化", "エージェント",
    "人工智能", "生成式ai", "自动化", "智能体",
    "인공지능", "생성형ai", "자동화", "에이전트",
]

PAIN = [
    "problem", "broken", "slow", "expensive", "hard", "difficult", "struggle",
    "wish", "need", "missing", "fails", "bad", "worse", "cost", "pricing",
    "مشكلة", "صعب", "بطيء", "غالي", "مكلف", "أحتاج", "احتاج", "أتمنى", "يفشل",
    "問題", "課題", "必要", "欲しい", "困る", "高い", "コスト", "機会",
    "问题", "痛点", "需要", "想要", "困难", "成本", "机会",
    "문제", "필요", "어려움", "비용", "기회",
]

LAUNCH = [
    "launch", "released", "announces", "introduces", "ships", "open source",
    "إطلاق", "أعلنت", "يصدر",
    "公開", "発表", "リリース",
    "发布", "推出", "开源",
    "출시", "공개", "발표",
]

INCOME = [
    "make money", "income", "revenue", "profit", "monetize", "paid", "sell",
    "client", "customers", "service", "agency", "freelance", "consulting",
    "saas", "subscription", "pricing", "business model", "use case", "workflow",
    "tool", "app", "application", "product", "ai-powered", "powered by ai",
    "uses ai", "built with ai", "framework", "system", "pipeline", "dataset",
    "benchmark", "open-source", "automation", "startup", "founder",
    "دخل", "ربح", "أرباح", "مال", "فلوس", "بيع", "عميل", "عملاء", "خدمة",
    "مشروع", "منتج", "مدعوم بالذكاء", "يستخدم الذكاء", "شركة ناشئة", "أداة",
    "تطبيق", "اشتراك", "تسعير", "وكالة", "استشارات", "عمل حر", "مستقل",
    "أتمتة", "نموذج عمل",
    "収益", "稼ぐ", "販売", "顧客", "ツール", "アプリ", "自動化", "スタートアップ",
    "收入", "赚钱", "盈利", "销售", "客户", "工具", "应用", "自动化", "创业",
    "수익", "돈", "판매", "고객", "도구", "앱", "자동화", "스타트업",
]

NOISE = [
    "self-promotion thread",
    "grand conspiracy",
    "subscribe to premium",
    "who to follow",
    "terms of service",
    "privacy policy",
    "keyboard shortcuts",
]

X_NOISE = [
    "chatgpt plus",
    "via login",
    "acc seller",
    "seller",
    "airdrop",
    "crypto",
    "blockchain",
    "nft",
    "fixture",
    "fixtures",
    "prediction",
    "predictions",
    "betting",
    "odds",
    "casino",
    "gambling",
    "50 llm projects",
    "source code to become a pro",
]

PRODUCT_TERMS = [
    "product", "tool", "app", "application", "saas", "platform", "service",
    "automation", "workflow", "agent", "agents", "customer", "client",
    "revenue", "income", "profit", "sell", "paid", "subscription",
    "ai-powered", "powered by ai", "uses ai", "built with ai", "framework",
    "system", "pipeline", "dataset", "benchmark", "open-source",
    "منتج", "أداة", "تطبيق", "منصة", "خدمة", "أتمتة", "سير عمل",
    "عميل", "عملاء", "دخل", "ربح", "بيع", "اشتراك", "مدعوم بالذكاء",
    "يستخدم الذكاء",
]

RSS_SOURCES = [
    {
        "id": "openai_news",
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "kind": "official",
    },
    {
        "id": "google_deepmind",
        "name": "Google DeepMind",
        "url": "https://blog.google/technology/google-deepmind/rss/",
        "kind": "official",
    },
    {
        "id": "google_ai_blog",
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "kind": "official",
    },
    {
        "id": "huggingface_blog",
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "kind": "official",
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://www.bensbites.com/feed",
        "kind": "newsletter",
    },
    {
        "id": "techcrunch_ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "kind": "news",
    },
    # ----- Free additional sources (no API keys, no rate-limit hassle) -----
    {
        "id": "lobsters_ai",
        "name": "Lobste.rs AI",
        "url": "https://lobste.rs/t/ai.rss",
        "kind": "community",
    },
    {
        "id": "indiehackers",
        "name": "Indie Hackers",
        "url": "https://www.indiehackers.com/feed.xml",
        "kind": "community",
    },
    {
        "id": "producthunt_ai",
        "name": "Product Hunt AI",
        "url": "https://www.producthunt.com/feed?category=artificial-intelligence",
        "kind": "community",
    },
    {
        "id": "devto_ai",
        "name": "Dev.to AI",
        "url": "https://dev.to/feed/tag/ai",
        "kind": "community",
    },
    {
        "id": "github_blog_ai",
        "name": "GitHub Blog (AI)",
        "url": "https://github.blog/ai-and-ml/feed/",
        "kind": "official",
    },
    {
        "id": "anthropic_news",
        "name": "Anthropic",
        "url": "https://www.anthropic.com/news/rss.xml",
        "kind": "official",
    },
    {
        "id": "mit_news_ai",
        "name": "MIT News AI",
        "url": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
        "kind": "official",
    },
    {
        "id": "smol_ai",
        "name": "smol.ai newsletter",
        "url": "https://buttondown.email/ainews/rss",
        "kind": "newsletter",
    },
]

ARXIV_QUERIES = [
    {
        "id": "arxiv_ai_agents",
        "name": "arXiv AI agents",
        "query": 'all:"AI agents" AND (all:workflow OR all:automation OR all:tool OR all:application OR all:framework)',
    },
    {
        "id": "arxiv_ai_products",
        "name": "arXiv AI product research",
        "query": '(all:"AI-powered" OR all:"artificial intelligence") AND (all:product OR all:service OR all:application OR all:platform OR all:tool)',
    },
    {
        "id": "arxiv_ai_document_tools",
        "name": "arXiv document and business AI",
        "query": '(all:"large language model" OR all:"vision language model") AND (all:document OR all:table OR all:workflow OR all:automation OR all:enterprise)',
    },
]

REDDIT_SOURCES = [
    {
        "id": "reddit_artificial",
        "name": "Reddit r/artificial",
        "url": "https://www.reddit.com/r/artificial/hot.json?limit=25",
        "kind": "social_forum",
    },
    {
        "id": "reddit_machinelearning",
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=25",
        "kind": "social_forum",
    },
    {
        "id": "reddit_localllama",
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=25",
        "kind": "social_forum",
    },
    {
        "id": "reddit_singularity",
        "name": "Reddit r/singularity",
        "url": "https://www.reddit.com/r/singularity/hot.json?limit=25",
        "kind": "social_forum",
    },
]

HUGGINGFACE_MODEL_QUERIES = [
    {"filter": "text-generation", "name": "Hugging Face text generation models"},
    {"filter": "image-text-to-text", "name": "Hugging Face multimodal models"},
    {"filter": "text-to-image", "name": "Hugging Face image models"},
]

DEFAULT_X_QUERY = (
    '(AI OR "artificial intelligence" OR LLM OR agents OR Claude OR ChatGPT OR OpenAI '
    'OR Anthropic OR Cursor OR Codex OR Gemini OR "ذكاء اصطناعي" OR "الذكاء الاصطناعي" '
    'OR 人工知能 OR 生成AI OR エージェント OR 人工智能 OR 生成式AI OR 智能体 OR 인공지능 OR 생성형AI OR 에이전트) '
    '(make money OR income OR revenue OR profit OR monetize OR paid OR sell OR product OR "AI-powered" OR "powered by AI" OR "uses AI" OR "built with AI" OR client '
    'OR customers OR service OR agency OR freelance OR consulting OR SaaS OR startup '
    'OR tool OR app OR automation OR workflow OR "business opportunity" '
    'OR دخل OR ربح OR أرباح OR مال OR بيع OR منتج OR "مدعوم بالذكاء" OR "يستخدم الذكاء" OR عميل OR عملاء OR خدمة OR مشروع '
    'OR شركة ناشئة OR أداة OR تطبيق OR اشتراك OR أتمتة OR فرصة '
    'OR 問題 OR 課題 OR 必要 OR 欲しい OR コスト OR 機会 '
    'OR 问题 OR 痛点 OR 需要 OR 成本 OR 机会 '
    'OR 문제 OR 필요 OR 비용 OR 기회) '
    '-is:retweet -from:grok'
)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_text(url, timeout=20):
    req = Request(url, headers={"User-Agent": "AX-Pulse-Radar/0.1 by local user"})
    with urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", errors="replace")


def contains_ai(text):
    low = text.lower()
    return any(k.lower() in low or k in text for k in KEYWORDS)


def score_item(text, source):
    low = text.lower()
    pain_hits = [p for p in PAIN if p.lower() in low or p in text]
    launch_hits = [p for p in LAUNCH if p.lower() in low or p in text]
    income_hits = [p for p in INCOME if p.lower() in low or p in text]
    ai_hits = [k for k in KEYWORDS if k.lower() in low or k in text]
    score = min(1.0, len(ai_hits) * 0.04 + len(pain_hits) * 0.10 + len(launch_hits) * 0.06 + len(income_hits) * 0.18)
    if not income_hits and source not in {"github_repos"}:
        score *= 0.55
    if source in {"hn_algolia", "github_repos"}:
        score += 0.08
    return round(min(score, 1.0), 2), pain_hits, launch_hits, ai_hits + income_hits


def is_noise(title, text=""):
    low = " ".join([title or "", text or ""]).lower()
    return any(term in low for term in NOISE)


def is_product_income_signal(item):
    body = " ".join([
        item.get("title") or "",
        item.get("text") or "",
        " ".join(item.get("matched_keywords") or []),
    ])
    low = body.lower()
    if any(term in low for term in X_NOISE):
        return False
    has_product_term = any(term in low or term in body for term in PRODUCT_TERMS)
    if not has_product_term and item.get("source_id") not in {"openai_news", "google_deepmind", "techcrunch_ai"}:
        return False

    score = item.get("opportunity_score") or 0
    if score < 0.35:
        return False

    if item.get("source_id") == "x_recent_search":
        metrics = item.get("metrics") or {}
        engagement = sum(metrics.get(k, 0) or 0 for k in [
            "like_count", "retweet_count", "reply_count", "quote_count", "bookmark_count"
        ])
        impressions = metrics.get("impression_count") or 0
        if engagement < 2 and impressions < 50:
            return False

    return True


def is_ai_news_update_signal(item):
    body = " ".join([
        item.get("title") or "",
        item.get("text") or "",
        " ".join(item.get("matched_keywords") or []),
    ])
    if not contains_ai(body) or is_noise(item.get("title"), item.get("text")):
        return False
    if any(term in body.lower() for term in X_NOISE):
        return False
    source_id = item.get("source_id")
    source_kind = item.get("source_kind")
    if source_kind in {"official", "newsletter", "model_hub", "scientific_paper"}:
        return True
    score = item.get("opportunity_score") or 0
    if source_id == "x_recent_search":
        metrics = item.get("metrics") or {}
        engagement = sum(metrics.get(k, 0) or 0 for k in [
            "like_count", "retweet_count", "reply_count", "quote_count", "bookmark_count"
        ])
        impressions = metrics.get("impression_count") or 0
        return engagement >= 5 or impressions >= 200
    if source_id and source_id.startswith("reddit_"):
        metrics = item.get("metrics") or {}
        return (metrics.get("score") or 0) >= 5 or (metrics.get("comments") or 0) >= 5
    return score >= 0.16


def normalize_item(source_id, source_name, source_kind, title, url, text="", external_id="", posted_at=None, metrics=None):
    body = " ".join([title or "", text or ""]).strip()
    score, pain_hits, launch_hits, ai_hits = score_item(body, source_id)
    signal_type = "pain" if pain_hits else ("launch" if launch_hits else "news")
    return {
        "id": f"{source_id}:{external_id or abs(hash(url or title))}",
        "source_id": source_id,
        "source_name": source_name,
        "source_kind": source_kind,
        "source_url": url,
        "external_id": str(external_id or ""),
        "title": title or "",
        "text": text or "",
        "posted_at": posted_at,
        "collected_at": now(),
        "matched_keywords": sorted(set(ai_hits + pain_hits + launch_hits)),
        "signal_type": signal_type,
        "opportunity_score": score,
        "metrics": metrics or {},
        "verification_status": "source_linked",
    }


def fetch_rss_source(source, limit=20):
    try:
        xml = fetch_text(source["url"])
    except Exception as exc:
        return [], {"source": source["id"], "error": str(exc)}
    root = ET.fromstring(xml)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = re.sub("<[^>]+>", " ", item.findtext("description") or "")
        pub = item.findtext("pubDate")
        if contains_ai(title + " " + desc) and not is_noise(title, desc):
            items.append(normalize_item(source["id"], source["name"], source["kind"], title, link, desc[:700], link, pub))
    return items, None


def fetch_arxiv_query(source, limit=15):
    params = urlencode({
        "search_query": source["query"],
        "start": "0",
        "max_results": str(limit),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    xml = fetch_text("https://export.arxiv.org/api/query?" + params, timeout=25)
    root = ET.fromstring(xml)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = []
    for entry in root.findall("atom:entry", ns):
        title = re.sub(r"\s+", " ", entry.findtext("atom:title", default="", namespaces=ns)).strip()
        summary = re.sub(r"\s+", " ", entry.findtext("atom:summary", default="", namespaces=ns)).strip()
        entry_id = entry.findtext("atom:id", default="", namespaces=ns).strip()
        published = entry.findtext("atom:published", default="", namespaces=ns).strip()
        if not contains_ai(title + " " + summary) or is_noise(title, summary):
            continue
        items.append(normalize_item(
            "arxiv_papers",
            source["name"],
            "scientific_paper",
            title,
            entry_id,
            text=summary[:1200],
            external_id=entry_id.rsplit("/", 1)[-1],
            posted_at=published,
            metrics={"query_id": source["id"]},
        ))
    return items


def fetch_huggingface_daily_papers(limit=20):
    data = json.loads(fetch_text("https://huggingface.co/api/daily_papers", timeout=25))
    items = []
    for row in data[:limit]:
        paper = row.get("paper") or {}
        paper_id = paper.get("id") or ""
        title = paper.get("title") or ""
        summary = paper.get("summary") or ""
        url = f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
        if not contains_ai(title + " " + summary) or is_noise(title, summary):
            continue
        items.append(normalize_item(
            "huggingface_daily_papers",
            "Hugging Face Daily Papers",
            "scientific_paper",
            title,
            url,
            text=summary[:1200],
            external_id=paper_id,
            posted_at=paper.get("submittedOnDailyAt") or paper.get("publishedAt"),
            metrics={
                "upvotes": row.get("upvotes") or paper.get("upvotes"),
                "authors": ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3] if a.get("name")]),
            },
        ))
    return items


def fetch_huggingface_models(limit=20):
    items = []
    per_query = max(3, min(int(limit or 20), 20))
    for query in HUGGINGFACE_MODEL_QUERIES:
        params = urlencode({
            "sort": "lastModified",
            "direction": "-1",
            "limit": str(per_query),
            "filter": query["filter"],
        })
        data = json.loads(fetch_text("https://huggingface.co/api/models?" + params, timeout=25))
        for model in data:
            model_id = model.get("modelId") or model.get("id") or ""
            tags = model.get("tags") or []
            pipeline = model.get("pipeline_tag") or query["filter"]
            title = f"{model_id} — {pipeline}"
            text = " ".join([
                "Hugging Face model update",
                pipeline,
                " ".join(tags[:12]),
                f"downloads {model.get('downloads') or 0}",
                f"likes {model.get('likes') or 0}",
            ])
            if not model_id or not contains_ai(title + " " + text):
                continue
            items.append(normalize_item(
                "huggingface_models",
                query["name"],
                "model_hub",
                title,
                f"https://huggingface.co/{model_id}",
                text=text[:900],
                external_id=model_id,
                posted_at=model.get("lastModified"),
                metrics={
                    "downloads": model.get("downloads"),
                    "likes": model.get("likes"),
                    "pipeline_tag": pipeline,
                    "tags": tags[:12],
                },
            ))
        time.sleep(0.15)
    return items


def fetch_hn(limit=50):
    query = quote("(AI OR LLM OR Claude OR OpenAI OR Anthropic OR agents OR Cursor OR Gemini)")
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={query}&tags=story&hitsPerPage={limit}"
    data = json.loads(fetch_text(url))
    items = []
    for hit in data.get("hits", []):
        title = hit.get("title") or hit.get("story_title") or ""
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        if not contains_ai(title) or is_noise(title):
            continue
        items.append(normalize_item(
            "hn_algolia", "Hacker News", "social_news", title, link,
            text=hit.get("story_text") or "",
            external_id=hit.get("objectID"),
            posted_at=hit.get("created_at"),
            metrics={"points": hit.get("points"), "comments": hit.get("num_comments")},
        ))
    return items


def fetch_github(limit=30):
    query = quote("AI OR LLM OR agent OR Claude OR MCP")
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page={limit}"
    data = json.loads(fetch_text(url))
    items = []
    for repo in data.get("items", []):
        title = repo.get("full_name", "")
        desc = repo.get("description") or ""
        if not contains_ai(title + " " + desc) or is_noise(title, desc):
            continue
        items.append(normalize_item(
            "github_repos", "GitHub Repositories", "code", title, repo.get("html_url"),
            text=desc,
            external_id=repo.get("id"),
            posted_at=repo.get("updated_at"),
            metrics={"stars": repo.get("stargazers_count"), "forks": repo.get("forks_count"), "language": repo.get("language")},
        ))
    return items


def fetch_reddit_source(source):
    data = json.loads(fetch_text(source["url"]))
    items = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        title = post.get("title", "")
        text = post.get("selftext", "") or post.get("url", "")
        if not contains_ai(title + " " + text) or is_noise(title, text):
            continue
        items.append(normalize_item(
            source["id"], source["name"], source["kind"], title,
            "https://www.reddit.com" + post.get("permalink", ""),
            text=text[:900],
            external_id=post.get("id"),
            posted_at=datetime.fromtimestamp(post.get("created_utc", 0), timezone.utc).isoformat(timespec="seconds") if post.get("created_utc") else None,
            metrics={"score": post.get("score"), "comments": post.get("num_comments"), "subreddit": post.get("subreddit")},
        ))
    return items


def fetch_feedly(limit=25):
    token = os.environ.get("FEEDLY_TOKEN")
    stream_id = os.environ.get("FEEDLY_STREAM_ID")
    if not token or not stream_id:
        return [], {"source": "feedly", "error": "FEEDLY_TOKEN أو FEEDLY_STREAM_ID غير موجود؛ تم تخطي Feedly."}
    url = f"https://cloud.feedly.com/v3/streams/contents?streamId={quote(stream_id)}&count={limit}"
    req = Request(url, headers={"Authorization": f"OAuth {token}", "User-Agent": "AX-Pulse-Radar/0.1"})
    with urlopen(req, timeout=20) as res:
        data = json.loads(res.read().decode("utf-8", errors="replace"))
    items = []
    for entry in data.get("items", []):
        title = entry.get("title", "")
        summary = ((entry.get("summary") or {}).get("content") or "")
        url = (entry.get("alternate") or [{}])[0].get("href") or entry.get("originId")
        if not contains_ai(title + " " + summary) or is_noise(title, summary):
            continue
        items.append(normalize_item(
            "feedly", "Feedly AI Stream", "ai_filtered_feed", title, url,
            text=re.sub("<[^>]+>", " ", summary)[:900],
            external_id=entry.get("id"),
            posted_at=datetime.fromtimestamp(entry.get("published", 0) / 1000, timezone.utc).isoformat(timespec="seconds") if entry.get("published") else None,
            metrics={"engagement": entry.get("engagement")},
        ))
    return items, None


def fetch_x_recent_search(limit=25, query=None):
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN")
    if not token:
        return [], {"source": "x_recent_search", "error": "X_BEARER_TOKEN غير موجود؛ تم تخطي X API."}

    max_results = max(10, min(int(limit or 25), 100))
    params = {
        "query": query or os.environ.get("X_QUERY") or DEFAULT_X_QUERY,
        "max_results": str(max_results),
        "tweet.fields": "created_at,public_metrics,author_id,conversation_id,lang",
        "expansions": "author_id",
        "user.fields": "username,name,verified,public_metrics",
    }
    url = "https://api.x.com/2/tweets/search/recent?" + urlencode(params)
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "AX-Pulse-Radar/0.2",
        },
    )
    try:
        with urlopen(req, timeout=25) as res:
            data = json.loads(res.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        detail = ""
        try:
            detail_data = json.loads(exc.read().decode("utf-8", errors="replace"))
            detail = detail_data.get("detail") or detail_data.get("title") or ""
        except Exception:
            detail = ""
        if exc.code == 402:
            msg = "X API رفض الطلب: الحساب يحتاج رصيد/خطة مدفوعة للبحث الحديث (HTTP 402 Payment Required)."
        elif exc.code in {401, 403}:
            msg = "X API رفض التوكن أو الصلاحيات. تأكدي من Bearer Token وصلاحية قراءة التغريدات."
        elif exc.code == 429:
            msg = "X API أوقف الطلب مؤقتًا بسبب حد الاستخدام. جربي لاحقًا أو خففي --x-limit."
        else:
            msg = f"X API HTTP {exc.code}: {detail or exc.reason}"
        return [], {"source": "x_recent_search", "error": msg}
    except URLError as exc:
        return [], {"source": "x_recent_search", "error": f"تعذر الاتصال بـ X API: {exc.reason}"}

    users = {
        user.get("id"): user
        for user in data.get("includes", {}).get("users", [])
        if user.get("id")
    }
    items = []
    seen_usernames = set()
    for tweet in data.get("data", []):
        text = tweet.get("text", "")
        if not contains_ai(text) or is_noise(text):
            continue
        if any(term in text.lower() for term in X_NOISE):
            continue
        if score_item(text, "x_recent_search")[0] < 0.2:
            continue
        author = users.get(tweet.get("author_id"), {})
        username = author.get("username")
        username_key = username.lower() if username else ""
        if username_key and username_key in seen_usernames:
            continue
        tweet_id = tweet.get("id", "")
        tweet_url = (
            f"https://x.com/{username}/status/{tweet_id}"
            if username and tweet_id
            else f"https://x.com/i/web/status/{tweet_id}"
        )
        metrics = tweet.get("public_metrics") or {}
        if username:
            metrics["username"] = username
        if author.get("name"):
            metrics["author_name"] = author.get("name")
        # Skip @grok replies that slip past -from:grok in the query
        if username and username.lower() == "grok":
            continue
        if username_key:
            seen_usernames.add(username_key)
        # Skip tweets with zero human engagement (noise filter, no extra API)
        engagement = (
            metrics.get("like_count", 0)
            + metrics.get("retweet_count", 0)
            + metrics.get("reply_count", 0)
            + metrics.get("quote_count", 0)
            + metrics.get("bookmark_count", 0)
        )
        impressions = metrics.get("impression_count", 0) or 0
        if engagement < 2 and impressions < 50:
            continue
        items.append(normalize_item(
            "x_recent_search",
            "X Recent Search",
            "social_public_api",
            text[:120].replace("\n", " "),
            tweet_url,
            text=text[:900],
            external_id=tweet_id,
            posted_at=tweet.get("created_at"),
            metrics=metrics,
        ))
    return items, None


def dedupe(items):
    seen = set()
    out = []
    for item in items:
        key = item.get("source_url") or item.get("id")
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def load_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def merge_corpus(new_items, run_at):
    corpus = load_json(CORPUS_FILE, {"items": []})
    by_key = {}
    for item in corpus.get("items", []):
        key = item.get("source_url") or item.get("id")
        if key:
            by_key[key] = item

    for item in new_items:
        key = item.get("source_url") or item.get("id")
        if not key:
            continue
        existing = by_key.get(key)
        if existing:
            existing["seen_count"] = int(existing.get("seen_count") or 1) + 1
            existing["last_seen_at"] = run_at
            existing["opportunity_score"] = max(existing.get("opportunity_score") or 0, item.get("opportunity_score") or 0)
            existing["metrics"] = item.get("metrics") or existing.get("metrics") or {}
            existing["matched_keywords"] = sorted(set((existing.get("matched_keywords") or []) + (item.get("matched_keywords") or [])))
            if item.get("title_ar") and not existing.get("title_ar"):
                existing["title_ar"] = item["title_ar"]
        else:
            item = dict(item)
            item["first_seen_at"] = run_at
            item["last_seen_at"] = run_at
            item["seen_count"] = 1
            by_key[key] = item

    merged = sorted(
        by_key.values(),
        key=lambda x: ((x.get("seen_count") or 1), (x.get("opportunity_score") or 0), x.get("last_seen_at") or ""),
        reverse=True,
    )
    out = {
        "generated_at": run_at,
        "count": len(merged),
        "note_ar": "قاعدة تراكمية لا تُحذف عند تحديث الرادار. تستخدم لقياس تكرار الإشارات ونمو الفرص بمرور الوقت.",
        "items": merged,
    }
    CORPUS_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def write_history_snapshot(run_at, items, errors):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = run_at.replace(":", "").replace("+", "Z")
    path = HISTORY_DIR / f"{stamp}.json"
    payload = {
        "generated_at": run_at,
        "count": len(items),
        "errors": errors,
        "items": items,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_opportunities(items):
    buckets = {
        "ai_income_services": {
            "title_ar": "خدمات يمكن بيعها باستخدام الذكاء الاصطناعي",
            "needles": ["service", "agency", "client", "consulting", "freelance", "خدمة", "عميل", "عملاء", "وكالة", "استشارات", "مستقل"],
            "capital_ar": "بدون رأس مال",
            "sellable_product_ar": "باقة خدمة تنفذ عملاً متكررًا للعميل باستخدام أدوات AI",
            "buyer_ar": "أفراد، مستقلون، وشركات صغيرة لديها عمل متكرر ولا تملك فريق AI",
            "first_paid_test_ar": "بيع تجربة صغيرة لعميل واحد: نتيجة جاهزة خلال 48 ساعة",
            "tools_ar": "ChatGPT أو Claude، Notion/Docs، أداة تسليم للعميل",
            "pricing_ar": "200-1000$ لكل باقة خدمة",
            "examples_ar": "خدمة تلخيص، كتابة عروض، تحليل مستندات، إعداد تقارير",
            "why_it_matters_ar": "الإشارات تكشف أن الناس يريدون نتيجة عملية أكثر من رغبتهم في تعلم الأدوات نفسها.",
        },
        "ai_income_tools": {
            "title_ar": "منتجات وأدوات مدعومة بالذكاء الاصطناعي قابلة للبيع",
            "needles": ["tool", "app", "application", "product", "ai-powered", "powered by ai", "uses ai", "built with ai", "framework", "system", "pipeline", "dataset", "benchmark", "open-source", "saas", "subscription", "pricing", "أداة", "تطبيق", "منتج", "مدعوم بالذكاء", "يستخدم الذكاء", "اشتراك", "تسعير"],
            "capital_ar": "منخفض",
            "sellable_product_ar": "أداة صغيرة أو قالب عمل يستخدم AI لحل مهمة محددة قابلة للتكرار",
            "buyer_ar": "شركات ناشئة، صناع محتوى، وفرق تبحث عن اختصار عملي في سير العمل",
            "first_paid_test_ar": "صفحة انتظار + نموذج أولي بسيط + 5 مقابلات مع مشترين محتملين",
            "tools_ar": "واجهة بسيطة، API نموذج AI، Stripe أو Gumroad، صفحة هبوط",
            "pricing_ar": "9-49$/شهر أو قالب مدفوع",
            "examples_ar": "قالب مدفوع، إضافة صغيرة، أداة SaaS مركزة",
            "why_it_matters_ar": "تكرار ذكر الأدوات والمنتجات يعني أن السوق يبحث عن حلول جاهزة لا عن خبر فقط.",
        },
        "ai_income_automation": {
            "title_ar": "أتمتة أعمال توفر وقتًا ويمكن تسعيرها",
            "needles": ["automation", "workflow", "agent", "agents", "mcp", "أتمتة", "سير عمل", "وكلاء"],
            "capital_ar": "منخفض",
            "sellable_product_ar": "أتمتة AI تربط أدوات العميل وتخفض عملاً يدويًا يوميًا",
            "buyer_ar": "شركات صغيرة وفرق تشغيل لديها مهام متكررة وفواتير وقت عالية",
            "first_paid_test_ar": "اختيار عملية واحدة وقياس الوقت قبل/بعد الأتمتة",
            "tools_ar": "Zapier/Make أو n8n، API، بريد أو CRM، نموذج AI",
            "pricing_ar": "إعداد 500$ + دعم شهري",
            "examples_ar": "أتمتة ردود العملاء، فواتير، تقارير، متابعة مبيعات",
            "why_it_matters_ar": "الأتمتة قابلة للبيع سريعًا لأنها تربط مباشرة بين AI وتوفير وقت أو تكلفة.",
        },
        "ai_income_content": {
            "title_ar": "محتوى وتسويق بالذكاء الاصطناعي قابل للبيع",
            "needles": ["content", "video", "voice", "image", "sora", "veo", "design", "audio", "marketing", "محتوى", "فيديو", "تصميم", "تسويق", "صوت"],
            "capital_ar": "بدون رأس مال",
            "sellable_product_ar": "باقة إنتاج محتوى أو إعلانات أو فيديوهات قصيرة بمساعدة AI",
            "buyer_ar": "متاجر، صناع محتوى، وكالات، وعلامات شخصية تحتاج نشرًا أسرع",
            "first_paid_test_ar": "إنتاج 3 عينات قبل/بعد لعميل واحد ثم عرض باقة شهرية",
            "tools_ar": "ChatGPT/Claude، أداة تصميم أو فيديو، جدولة نشر",
            "pricing_ar": "99-299$/شهر أو سعر لكل مخرج",
            "examples_ar": "حزم إعلانات، مقاطع قصيرة، وصف منتجات، حملات بريد",
            "why_it_matters_ar": "المحتوى أسرع مسار لاختبار الدفع لأنه لا يحتاج بنية تقنية كبيرة في البداية.",
        },
    }
    opps = []
    for key, meta in buckets.items():
        ev = []
        for item in items:
            hay = (item["title"] + " " + item["text"]).lower()
            if item.get("opportunity_score", 0) >= 0.25 and any(n in hay for n in meta["needles"]):
                ev.append(item)
        if not ev:
            continue
        ev = sorted(ev, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:8]
        avg = round(sum(e["opportunity_score"] for e in ev) / len(ev), 2)
        if len(ev) < 3 or avg < 0.32:
            continue
        opps.append({
            "id": key,
            "title_ar": meta["title_ar"],
            "capital_ar": meta["capital_ar"],
            "sellable_product_ar": meta["sellable_product_ar"],
            "buyer_ar": meta["buyer_ar"],
            "first_paid_test_ar": meta["first_paid_test_ar"],
            "tools_ar": meta["tools_ar"],
            "pricing_ar": meta["pricing_ar"],
            "examples_ar": meta["examples_ar"],
            "why_it_matters_ar": meta["why_it_matters_ar"],
            "signal_count": len(ev),
            "avg_score": avg,
            "confidence": min(0.85, round(0.35 + len(ev) * 0.06 + avg * 0.25, 2)),
            "evidence_items": [
                {
                    "source_id": e["source_id"],
                    "title": e["title"],
                    "url": e["source_url"],
                    "signal_type": e["signal_type"],
                    "score": e["opportunity_score"],
                    "metrics": e.get("metrics", {}),
                }
                for e in ev
            ],
        })
    opps = sorted(opps, key=lambda o: (o["confidence"], o["avg_score"]), reverse=True)
    if opps:
        return opps

    evidence = sorted(items, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:8]
    if not evidence:
        return []
    return [{
        "id": "monitor_more_signals",
        "title_ar": "إشارات AI تحتاج متابعة قبل تحويلها إلى فرصة",
        "signal_count": len(evidence),
        "avg_score": round(sum(e.get("opportunity_score", 0) for e in evidence) / len(evidence), 2),
        "confidence": 0.45,
        "evidence_items": [
            {
                "source_id": e["source_id"],
                "title": e["title"],
                "url": e["source_url"],
                "signal_type": e["signal_type"],
                "score": e["opportunity_score"],
                "metrics": e.get("metrics", {}),
            }
            for e in evidence
        ],
    }]


def run(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    errors = []
    items = []
    for source in RSS_SOURCES:
        got, err = fetch_rss_source(source, limit=args.limit)
        items.extend(got)
        if err:
            errors.append(err)
        time.sleep(0.2)
    for source in ARXIV_QUERIES:
        try:
            items.extend(fetch_arxiv_query(source, limit=min(args.limit, 15)))
        except Exception as exc:
            errors.append({"source": source["id"], "error": str(exc)})
        time.sleep(0.4)
    try:
        items.extend(fetch_huggingface_daily_papers(limit=min(args.limit, 20)))
    except Exception as exc:
        errors.append({"source": "huggingface_daily_papers", "error": str(exc)})
    try:
        items.extend(fetch_huggingface_models(limit=min(args.limit, 20)))
    except Exception as exc:
        errors.append({"source": "huggingface_models", "error": str(exc)})
    got, err = fetch_feedly(limit=args.limit)
    items.extend(got)
    if err and args.include_feedly_notice:
        errors.append(err)
    x_queries = args.x_query or [None]
    for query in x_queries:
        got, err = fetch_x_recent_search(limit=args.x_limit, query=query)
        items.extend(got)
        if err and args.include_x_notice:
            errors.append(err)
        time.sleep(0.2)
    for source in REDDIT_SOURCES:
        try:
            items.extend(fetch_reddit_source(source))
        except Exception as exc:
            errors.append({"source": source["id"], "error": str(exc)})
        time.sleep(0.2)
    try:
        items.extend(fetch_hn(limit=args.limit))
    except Exception as exc:
        errors.append({"source": "hn_algolia", "error": str(exc)})
    try:
        items.extend(fetch_github(limit=min(args.limit, 30)))
    except Exception as exc:
        errors.append({"source": "github_repos", "error": str(exc)})

    items = [
        item
        for item in dedupe(items)
        if is_ai_news_update_signal(item)
    ]
    if not items and errors and not args.allow_empty:
        print("items=0 errors=" + str(len(errors)))
        print("لم يتم استبدال ملفات data/radar لأن كل المصادر فشلت أو رجعت فارغة. استخدم --allow-empty إذا أردت الكتابة رغم ذلك.")
        print(RAW_FILE)
        print(SIGNALS_FILE)
        print(OPPS_FILE)
        return
    run_at = now()
    corpus_items = merge_corpus(items, run_at)
    history_path = write_history_snapshot(run_at, items, errors)
    display_items = sorted(
        corpus_items,
        key=lambda x: (
            x.get("last_seen_at") or x.get("collected_at") or x.get("posted_at") or "",
            x.get("opportunity_score") or 0,
            x.get("seen_count") or 1,
        ),
        reverse=True,
    )[:120]

    raw = {"generated_at": run_at, "count": len(items), "errors": errors, "items": items}
    RAW_FILE.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    signals = {
        "generated_at": run_at,
        "count": len(display_items),
        "corpus_count": len(corpus_items),
        "history_snapshot": str(history_path.relative_to(ROOT)),
        "note_ar": "يعرض هذا الملف أحدث الإشارات أولًا من القاعدة التراكمية. لا يتم حذف الإشارات القديمة؛ يمكن الاطلاع عليها من signals_corpus.json.",
        "items": display_items,
    }
    SIGNALS_FILE.write_text(json.dumps(signals, ensure_ascii=False, indent=2), encoding="utf-8")
    opportunities = {
        "generated_at": run_at,
        "source": "pulse_radar_v0",
        "note_ar": "فرص مبنية على قاعدة تراكمية من إشارات منتجات/خدمات/أدوات تستخدم الذكاء الاصطناعي. التكرار عبر الوقت يرفع قوة الإشارة.",
        "corpus_count": len(corpus_items),
        "opportunities": build_opportunities(corpus_items),
    }
    OPPS_FILE.write_text(json.dumps(opportunities, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"items={len(items)} errors={len(errors)}")
    print(RAW_FILE)
    print(SIGNALS_FILE)
    print(OPPS_FILE)


def main():
    parser = argparse.ArgumentParser(description="AX Pulse Radar v0: collect AI signals from free official/public sources.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--x-limit", type=int, default=25, help="Number of recent X posts to request when X_BEARER_TOKEN is set.")
    parser.add_argument("--x-query", action="append", help="Override/add an X recent-search query. Repeat to run several small language-specific searches.")
    parser.add_argument("--include-x-notice", action="store_true", help="Include X skipped notice in errors when token/env is missing.")
    parser.add_argument("--include-feedly-notice", action="store_true", help="Include Feedly skipped notice in errors when token/env is missing.")
    parser.add_argument("--allow-empty", action="store_true", help="Write empty radar files even if all sources fail.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
