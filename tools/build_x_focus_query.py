#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS_FILE = ROOT / "data" / "radar" / "x_focus_accounts.json"

LAYER_NAMES = {
    "official": {
        "OpenAI", "AnthropicAI", "GoogleDeepMind", "GitHub", "huggingface", "cursor_ai", "vercel",
        "sama", "gdb", "demishassabis", "OfficialLoganK", "AravSrinivas", "mustafasuleyman",
    },
    "builders": {
        "hwchase17", "simonw", "jxnlco", "swyx", "levelsio", "rileybrown", "yoheinakajima",
        "tibo_maker", "jerryjliu0", "gregisenberg", "rauchg", "mckaywrigley", "skirano",
        "amasad", "garrytan", "danshipper", "petergyang", "mattshumer_", "Suhail",
        "rrhoover", "andrewchen", "lennysan", "antonosika",
    },
    "coding": {
        "bcherny", "realGeorgeHotz", "ggerganov", "steipete", "paulgauthier", "altryne",
        "ScottWu46", "zachlloydtweets", "clattner_llvm", "sh_reya", "chipro", "HamelHusain",
        "ankrgyl", "Raza_Habib", "spolu", "btaylor",
    },
    "research": {
        "rasbt", "karpathy", "AndrewYNg", "drfeifei", "ylecun", "fchollet", "ID_AA_Carmack",
        "kaifulee", "JeffDean", "goodfellow_ian", "soumithchintala", "OriolVinyalsML",
        "NandoDF", "lilianweng", "maximelabonne", "_philschmid", "abhi1thakur", "natolambert",
        "Teknium1", "vikhyatk", "tri_dao", "Tim_Dettmers", "OfirPress", "mikeknoop",
        "jackclarkSF", "carlini", "ykilcher",
    },
    "creative": {
        "iamneubert", "LinusEkenstam", "bilawalsidhu", "clairesilver12", "HBCoop_",
        "icreatelife", "refikanadol", "sougwen", "genekogan", "nickfloats", "javilopen",
        "Ror_Fly", "DonAllenIII", "PaigePiskin", "thedorbrothers", "juliewdesign_",
        "paultrillo", "niceaunties", "rainisto", "fabianstelzer",
    },
    "business": {
        "rowancheung", "bentossell", "thatroblennon", "alliekmiller", "emollick", "nathanbenaich",
        "EMostaque", "levie", "mattturck", "kevinweil", "joshwoodward", "alexalbert__",
        "nabeelqu", "minchoi", "heyBarsee", "heykahn", "nonmayorpete", "noahedelman02",
        "nathanlands", "itsandrewgao", "AIHighlight", "Scobleizer", "PeterDiamandis",
        "waitin4agi_", "DataChaz", "Whats_AI", "sirajraval", "Sentdex", "svpino",
        "adamdangelo", "lexfridman", "geoffreyhinton", "GaryMarcus", "timnitGebru",
        "katecrawford", "erikbryn", "DaphneKoller", "etzioni", "mrogati", "miketamir",
        "_KarenHao", "math_rachel", "quaesita", "RichardSocher", "seb_ruder", "yoavgo",
        "svlevine", "chelseabfinn", "AnimaAnandkumar", "pmddomingos", "paulroetzer",
        "BernardMarr", "pascal_bornet", "YuHelenYu", "Ronald_vanLoon",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Build an X recent-search query from focus accounts.")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument(
        "--layer",
        choices=["top", "official", "builders", "coding", "research", "creative", "business"],
        default="top",
    )
    args = parser.parse_args()
    data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    all_accounts = data.get("accounts", [])
    if args.layer == "top":
        accounts = all_accounts[:args.top]
    else:
        wanted = {name.lower() for name in LAYER_NAMES[args.layer]}
        accounts = [a for a in all_accounts if a.get("username", "").lower() in wanted][:args.top]
        if len(accounts) < args.top:
            existing = {a.get("username", "").lower() for a in accounts}
            for username in LAYER_NAMES[args.layer]:
                if username.lower() in existing:
                    continue
                accounts.append({"username": username})
                if len(accounts) >= args.top:
                    break
    authors = " OR ".join(f"from:{a['username']}" for a in accounts if a.get("username"))
    terms = (
        'AI OR LLM OR agent OR Claude OR GPT OR Gemini OR tool OR app OR product '
        'OR startup OR automation OR workflow OR MCP OR "AI-powered" OR ذكاء'
    )
    print(f"({authors}) ({terms}) -is:retweet -from:grok")


if __name__ == "__main__":
    main()
