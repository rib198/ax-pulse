#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS_FILE = ROOT / "data" / "radar" / "x_focus_accounts.json"


def main():
    parser = argparse.ArgumentParser(description="Build an X recent-search query from focus accounts.")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--layer", choices=["top", "companies", "builders", "experts"], default="top")
    args = parser.parse_args()
    data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    all_accounts = data.get("accounts", [])
    layer_names = {
        "companies": {"OpenAI", "AnthropicAI", "GoogleDeepMind", "GitHub", "huggingface", "lmarena_ai"},
        "builders": {"cursor_ai", "Replit", "vercel", "huggingface", "GitHub"},
        "experts": {"sama", "gdb", "karpathy", "AndrewYNg", "ylecun", "emollick", "simonw", "swyx", "hardmaru", "shl"},
    }
    if args.layer == "top":
        accounts = all_accounts[:args.top]
    else:
        wanted = {name.lower() for name in layer_names[args.layer]}
        accounts = [a for a in all_accounts if a.get("username", "").lower() in wanted][:args.top]
    authors = " OR ".join(f"from:{a['username']}" for a in accounts if a.get("username"))
    terms = (
        "AI OR LLM OR agent OR agents OR Claude OR ChatGPT OR OpenAI OR Anthropic "
        "OR Cursor OR Codex OR Gemini OR automation OR workflow OR model OR MCP "
        "OR 生成AI OR 人工智能 OR 인공지능 OR ذكاء"
    )
    money_terms = (
        '"make money" OR income OR revenue OR profit OR monetize OR paid OR sell '
        'OR product OR "AI-powered" OR "powered by AI" OR "uses AI" OR "built with AI" '
        'OR client OR customers OR service OR agency OR freelance OR consulting '
        'OR SaaS OR startup OR tool OR app OR automation OR "business model" '
        'OR دخل OR ربح OR أرباح OR مال OR بيع OR منتج OR "مدعوم بالذكاء" OR "يستخدم الذكاء" OR عميل OR عملاء OR خدمة '
        'OR مشروع OR أداة OR تطبيق OR اشتراك OR أتمتة OR "شركة ناشئة"'
    )
    print(f"({authors}) ({terms}) ({money_terms}) -is:retweet -from:grok")


if __name__ == "__main__":
    main()
