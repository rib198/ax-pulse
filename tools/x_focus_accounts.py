#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / ".ax-pulse-x-token"
OUT_FILE = ROOT / "data" / "radar" / "x_focus_accounts.json"

USERNAMES = [
    "OpenAI",
    "AnthropicAI",
    "GoogleDeepMind",
    "huggingface",
    "LangChainAI",
    "cursor_ai",
    "Replit",
    "GitHub",
    "vercel",
    "sama",
    "gdb",
    "karpathy",
    "AndrewYNg",
    "ylecun",
    "emollick",
    "simonw",
    "swyx",
    "ClementDelangue",
    "jeremyphoward",
    "hardmaru",
    "shl",
    "lmarena_ai",
    "latentspacepod",
]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_token():
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("TWITTER_BEARER_TOKEN")
    if token:
        return token.strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def fetch_users(token, usernames):
    params = {
        "usernames": ",".join(usernames),
        "user.fields": "description,public_metrics,verified,verified_type,created_at",
    }
    url = "https://api.x.com/2/users/by?" + urlencode(params)
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "AX-Pulse-Focus-Accounts/0.1",
        },
    )
    with urlopen(req, timeout=25) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def account_kind(username):
    companies = {
        "openai", "anthropicai", "googledeepmind", "huggingface", "langchainai",
        "cursor_ai", "replit", "github", "vercel", "lmarena_ai", "latentspacepod",
    }
    return "company_or_project" if username.lower() in companies else "individual"


def main():
    token = read_token()
    if not token:
        print("X token is missing. Run ./setup-x-token.command first.", file=sys.stderr)
        return 1
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = fetch_users(token, USERNAMES)
    except HTTPError as exc:
        print(f"X API HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"X API network error: {exc.reason}", file=sys.stderr)
        return 1

    accounts = []
    for user in data.get("data", []):
        metrics = user.get("public_metrics") or {}
        username = user.get("username", "")
        accounts.append({
            "id": user.get("id"),
            "username": username,
            "name": user.get("name"),
            "kind": account_kind(username),
            "description": user.get("description", ""),
            "verified": user.get("verified", False),
            "verified_type": user.get("verified_type"),
            "followers_count": metrics.get("followers_count", 0),
            "following_count": metrics.get("following_count", 0),
            "tweet_count": metrics.get("tweet_count", 0),
            "listed_count": metrics.get("listed_count", 0),
            "url": f"https://x.com/{username}",
        })
    accounts.sort(key=lambda x: x.get("followers_count", 0), reverse=True)
    payload = {
        "generated_at": now(),
        "source": "x_api_users_by_username",
        "count": len(accounts),
        "errors": data.get("errors", []),
        "accounts": accounts,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"accounts={len(accounts)} errors={len(payload['errors'])}")
    print(OUT_FILE)
    for account in accounts[:10]:
        print(f"@{account['username']}: {account['followers_count']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
