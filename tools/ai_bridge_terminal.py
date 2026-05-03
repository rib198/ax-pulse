#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".ai-bridge"
STATE_FILE = STATE_DIR / "session.json"
ROLES = {"user", "claude", "codex"}
ROLE_ALIASES = {
    "user": "user",
    "me": "user",
    "انا": "user",
    "أنا": "user",
    "المستخدم": "user",
    "claude": "claude",
    "كلاود": "claude",
    "codex": "codex",
    "كوديكس": "codex",
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state():
    if not STATE_FILE.exists():
        return {"goal": "", "turns": [], "updated_at": now()}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"State file is corrupted: {STATE_FILE}")


def save_state(state):
    STATE_DIR.mkdir(exist_ok=True)
    state["updated_at"] = now()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text(args_text, stdin_allowed=True):
    if args_text:
        return " ".join(args_text).strip()
    if stdin_allowed and not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def role_label(role):
    return {
        "user": "أنت",
        "claude": "كلاود",
        "codex": "كوديكس",
    }.get(role, role.upper())


def normalize_role(role):
    normalized = ROLE_ALIASES.get(role)
    if not normalized:
        allowed = "، ".join(ROLE_ALIASES.keys())
        raise SystemExit(f"الدور غير معروف: {role}\nالأدوار المتاحة: {allowed}")
    return normalized


def cmd_goal(args):
    text = read_text(args.text)
    if not text:
        raise SystemExit("الاستخدام: ./bridge goal \"اكتب الهدف هنا\"")
    state = load_state()
    state["goal"] = text
    state["turns"].append({"role": "user", "text": text, "time": now()})
    save_state(state)
    print("تم حفظ الهدف.")
    print_next_hint(state)


def cmd_say(args):
    args.role = normalize_role(args.role)
    text = read_text(args.text)
    if not text:
        raise SystemExit(f"الاستخدام: ./bridge say {args.role} \"اكتب الرسالة هنا\"")
    state = load_state()
    state["turns"].append({"role": args.role, "text": text, "time": now()})
    if args.role == "user" and not state.get("goal"):
        state["goal"] = text
    save_state(state)
    print(f"تم حفظ رسالة من: {role_label(args.role)}.")
    print_next_hint(state)


def cmd_show(args):
    state = load_state()
    print_header(state)
    turns = state.get("turns", [])
    if args.last:
        turns = turns[-args.last :]
    if not turns:
        print("لا توجد رسائل بعد.")
        return
    for index, turn in enumerate(turns, start=1 if not args.last else max(1, len(state.get("turns", [])) - len(turns) + 1)):
        print()
        print(f"[{index}] {role_label(turn['role'])}  {turn.get('time', '')}")
        print("-" * 72)
        print(turn.get("text", ""))


def cmd_next(args):
    state = load_state()
    prompt = build_next_prompt(state, args.for_role)
    print(prompt)


def cmd_inbox(args):
    args.role = normalize_role(args.role)
    state = load_state()
    prompt = build_next_prompt(state, args.role)
    print()
    print(f"صندوق الرسائل لـ {role_label(args.role)}")
    print("=" * 72)
    print(prompt)
    print("=" * 72)
    print()
    print("بعد أن يرد هذا الطرف، احفظ رده بالأمر:")
    print(f"./bridge say {args.role} \"اكتب الرد هنا\"")


def cmd_reset(args):
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("تم مسح جلسة الوسيط.")


def cmd_export(args):
    state = load_state()
    out = ROOT / f"ai-bridge-export-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.json"
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


def copy_to_clipboard(text):
    if not shutil.which("pbcopy"):
        return False
    try:
        proc = subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False


def cmd_copy(args):
    args.role = normalize_role(args.role)
    state = load_state()
    prompt = build_next_prompt(state, args.role)
    copied = copy_to_clipboard(prompt)

    print()
    suffix = "  (نُسخت إلى الحافظة ✓)" if copied else "  (pbcopy غير متاح — لم تُنسخ)"
    print(f"رسالة {role_label(args.role)}{suffix}")
    print("=" * 72)
    print(prompt)
    print("=" * 72)
    print()
    if copied:
        print("الصق الرسالة في واجهة الطرف المطلوب، ثم احفظ ردّه بالأمر:")
    else:
        print("انسخ الرسالة يدوياً والصقها في واجهة الطرف المطلوب، ثم احفظ ردّه بالأمر:")
    print(f"./bridge say {args.role} \"اكتب الرد هنا\"")


def cmd_export_md(args):
    state = load_state()
    out = ROOT / f"ai-bridge-export-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"

    lines = []
    lines.append("# جلسة الوسيط بين كلاود وكوديكس")
    lines.append("")
    lines.append(f"**آخر تحديث:** `{state.get('updated_at', '-') }`")
    lines.append("")
    lines.append("## الهدف")
    lines.append("")
    goal = state.get("goal") or "_(لم يحدّد بعد)_"
    lines.append(goal)
    lines.append("")
    lines.append("## المحادثة")
    lines.append("")

    turns = state.get("turns", [])
    if not turns:
        lines.append("_(لا توجد رسائل بعد.)_")
    else:
        for index, turn in enumerate(turns, start=1):
            label = role_label(turn.get("role", "?"))
            time = turn.get("time", "")
            lines.append(f"### [{index}] {label}  ·  `{time}`")
            lines.append("")
            text = turn.get("text", "").strip()
            lines.append(text if text else "_(فارغ)_")
            lines.append("")
            lines.append("---")
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def print_header(state):
    print("وسيط التيرمنل بين كلاود وكوديكس")
    print("=" * 72)
    print(f"ملف الحفظ: {STATE_FILE}")
    print(f"آخر تحديث: {state.get('updated_at', '-')}")
    print(f"الهدف: {state.get('goal') or '(لم يحدد بعد)'}")


def print_next_hint(state):
    last = last_turn(state)
    if not last:
        return
    if last["role"] == "claude":
        print("الدور التالي: كوديكس يراجع. شغّل: ./bridge inbox codex")
    elif last["role"] == "codex":
        print("الدور التالي: كلاود يطبق التحسينات. شغّل: ./bridge inbox claude")
    else:
        print("الدور التالي: كلاود ينفذ. شغّل: ./bridge inbox claude")


def last_turn(state):
    turns = state.get("turns", [])
    return turns[-1] if turns else None


def latest_from(state, role):
    for turn in reversed(state.get("turns", [])):
        if turn.get("role") == role:
            return turn.get("text", "")
    return ""


def build_next_prompt(state, for_role):
    goal = state.get("goal") or "No goal has been set yet."
    last = last_turn(state)
    claude = latest_from(state, "claude")
    codex = latest_from(state, "codex")

    if for_role == "claude":
        if codex:
            return f"""أنت كلاود. طبّق التحسينات التي طلبها كوديكس.

الهدف:
{goal}

آخر مراجعة من كوديكس:
{codex}

بعد الانتهاء، أرسل:
1. ملخص التغييرات.
2. الملفات التي عدلتها.
3. الاختبارات أو الفحوصات التي شغّلتها.
4. أي شيء لم تستطع إنجازه وسببه."""
        return f"""أنت كلاود. نفّذ هدف المستخدم.

الهدف:
{goal}

بعد الانتهاء، أرسل:
1. ملخص التغييرات.
2. الملفات التي عدلتها.
3. الاختبارات أو الفحوصات التي شغّلتها.
4. أي عوائق."""

    if for_role == "codex":
        if claude:
            return f"""أنت كوديكس. راجع آخر تنفيذ من كلاود مقارنة بالهدف.

الهدف:
{goal}

آخر رسالة من كلاود:
{claude}

أعد الرد بهذا الشكل:
1. هل التنفيذ مقبول أم لا.
2. العيوب المحددة أو النواقص.
3. التحسينات الدقيقة التي يجب على كلاود تنفيذها.
4. الاختبارات أو الفحوصات المطلوبة قبل القبول."""
        return f"""أنت كوديكس. لا يوجد تنفيذ من كلاود حتى الآن.

الهدف:
{goal}

اطلب من كلاود تنفيذًا أوليًا، واطلب منه ملخصًا واضحًا، والملفات المعدلة، والفحوصات."""

    if last:
        return last.get("text", "")
    return goal


def build_parser():
    parser = argparse.ArgumentParser(
        prog="./bridge",
        description="وسيط تيرمنل محلي بين كلاود وكوديكس.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    goal = sub.add_parser("goal", help="حفظ الهدف المشترك.")
    goal.add_argument("text", nargs="*")
    goal.set_defaults(func=cmd_goal)

    say = sub.add_parser("say", help="إضافة رسالة من أحد الأطراف.")
    say.add_argument("role")
    say.add_argument("text", nargs="*")
    say.set_defaults(func=cmd_say)

    show = sub.add_parser("show", help="عرض سجل المحادثة.")
    show.add_argument("--last", type=int, default=0, help="عرض آخر N رسائل فقط.")
    show.set_defaults(func=cmd_show)

    inbox = sub.add_parser("inbox", help="عرض الرسالة المطلوبة للطرف التالي.")
    inbox.add_argument("role")
    inbox.set_defaults(func=cmd_inbox)

    next_cmd = sub.add_parser("next", help="طباعة الرسالة المطلوبة فقط بدون شرح.")
    next_cmd.add_argument("for_role", choices=["claude", "codex", "كلاود", "كوديكس"])
    next_cmd.set_defaults(func=cmd_next)

    export = sub.add_parser("export", help="تصدير الجلسة كاملة إلى JSON.")
    export.set_defaults(func=cmd_export)

    export_md = sub.add_parser("export-md", help="تصدير الجلسة إلى Markdown عربي.")
    export_md.set_defaults(func=cmd_export_md)

    copy = sub.add_parser("copy", help="بناء رسالة inbox ونسخها إلى الحافظة (pbcopy).")
    copy.add_argument("role")
    copy.set_defaults(func=cmd_copy)

    reset = sub.add_parser("reset", help="مسح جلسة الوسيط.")
    reset.set_defaults(func=cmd_reset)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "for_role", None):
        args.for_role = normalize_role(args.for_role)
    args.func(args)


if __name__ == "__main__":
    main()
