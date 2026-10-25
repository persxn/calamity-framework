#!/usr/bin/env python3
"""timetable — see today's routine, set goals, read per-date shifts.

The routine comes from learner/schedule.md (the single source of truth the
coach maintains): a weekday shape and a weekend shape. Goals you set and
date-specific shifts live in learner/timetable.json, so they sync with the
rest of your progress and Claude can read/edit them.

  timetable                 today's routine + goals (default)
  timetable <date>          any day: a date, today/tomorrow/yesterday,
                            a weekday (mon..sun), or +N / -N days
  timetable week            the next 7 days at a glance
  timetable goal "text"     add a goal (today), optionally --at / --block / --date
  timetable goals [date]    list goals with their numbers
  timetable done N          tick goal N off  (undone N / drop N also)
  timetable note <date> "…" a one-line note on a day
  timetable path            where the files live
  timetable help

Shifting a whole day's blocks is Claude's job: ask it, and it writes the
override into learner/timetable.json. This tool shows it.

First interactive run copies itself to /var/x and adds the `timetable` alias
to ~/.zshrc (needs sudo once for /var/x); after that just type `timetable`.
"""
import datetime as dt
import filecmp
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
REPO = os.environ.get("CALAMITY_REPO", os.path.join(HOME, "calamity-framework"))
SCHEDULE = os.path.join(REPO, "learner", "schedule.md")
STORE = os.path.join(REPO, "learner", "timetable.json")
ZSHRC = os.path.join(HOME, ".zshrc")
INSTALL_PATH = "/var/x"          # where first run copies itself; the alias target
WIDTH = 64

# ── fog palette (truecolor), matching the desktop widgets ────────────────────
ICE = (230, 234, 240)      # primary text / values
STEEL = (159, 180, 212)    # headers / accent
SUB = (168, 178, 192)      # secondary text
AMBER = (216, 160, 122)    # the now-marker / current block
OVERLAY = (74, 82, 96)     # rules, past blocks, dim hints
GREEN = (150, 190, 160)    # a done goal

USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def c(s, rgb, bold=False):
    if not USE_COLOR:
        return s
    b = "\x1b[1m" if bold else ""
    return f"{b}\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{s}\x1b[0m"


def rule(glyph="─", rgb=OVERLAY):
    return c(glyph * WIDTH, rgb)


# ── dates ────────────────────────────────────────────────────────────────────
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_date(tok, base=None):
    base = base or dt.date.today()
    t = tok.strip().lower()
    if t in ("today", "now", ""):
        return base
    if t in ("tomorrow", "tmr", "tom"):
        return base + dt.timedelta(days=1)
    if t in ("yesterday", "yst"):
        return base - dt.timedelta(days=1)
    m = re.fullmatch(r"([+-]\d+)", t)
    if m:
        return base + dt.timedelta(days=int(m.group(1)))
    if t[:3] in WEEKDAYS:
        target = WEEKDAYS.index(t[:3])
        delta = (target - base.weekday()) % 7          # nearest upcoming (incl. today)
        return base + dt.timedelta(days=delta)
    try:
        return dt.date.fromisoformat(t)
    except ValueError:
        return None


def to_min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


# ── schedule.md → blocks ─────────────────────────────────────────────────────
def _parse_table(lines):
    blocks = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [x.strip() for x in s.strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower() == "time" or set(cells[0]) <= set("-: "):
            continue
        times = cells[0].replace("–", "-").replace("—", "-")
        parts = [p.strip() for p in times.split("-")]
        if len(parts) != 2 or not re.match(r"\d\d?:\d\d", parts[0]):
            continue
        name = re.sub(r"\*+", "", cells[1]).strip()
        purpose = re.sub(r"\*+", "", cells[2]).strip() if len(cells) > 2 else ""
        if purpose in ("—", "-", ""):
            purpose = ""
        blocks.append({"start": parts[0], "end": parts[1], "name": name, "purpose": purpose})
    return blocks


def base_blocks(is_weekend):
    """Weekday / weekend blocks parsed from schedule.md."""
    try:
        with open(SCHEDULE, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    lines = text.splitlines()
    heads = [(i, ln) for i, ln in enumerate(lines) if ln.startswith("## ")]
    want = "weekend" if is_weekend else "weekday"
    start = end = None
    for idx, (i, ln) in enumerate(heads):
        if ln[3:].strip().lower().startswith(want):
            start = i
            end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
            break
    if start is None:
        return []
    return _parse_table(lines[start:end])


# ── store (goals + overrides) ────────────────────────────────────────────────
def load_store():
    try:
        with open(STORE, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("goals", {})
    d.setdefault("overrides", {})
    return d


def save_store(d):
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, STORE)


def day_blocks(date, store):
    """Override blocks for this date if Claude set any, else the base shape."""
    ov = store["overrides"].get(date.isoformat())
    if ov and ov.get("blocks"):
        out = []
        for b in ov["blocks"]:
            times = b.get("time", "").replace("–", "-").replace("—", "-")
            parts = [p.strip() for p in times.split("-")]
            if len(parts) == 2:
                out.append({"start": parts[0], "end": parts[1],
                            "name": re.sub(r"\*+", "", b.get("name", "")).strip(),
                            "purpose": b.get("purpose", "")})
        return out, ov
    return base_blocks(date.weekday() >= 5), ov


# ── engine footer (best-effort) ──────────────────────────────────────────────
def engine_line():
    try:
        out = subprocess.run(["python3", "engine/calamity.py", "statusline"],
                             cwd=REPO, capture_output=True, text=True, timeout=6)
        if out.returncode != 0:
            return ""
        keep = []
        for t in out.stdout.strip().split("·"):
            t = t.strip()
            if t.lower().startswith("try"):   # drop the model suggestion tail
                break
            if t and not t.lower().startswith("cal"):
                keep.append(t)
        return "  ".join(keep)
    except Exception:
        return ""


# ── rendering ────────────────────────────────────────────────────────────────
def current_index(blocks, now_min):
    for i, b in enumerate(blocks):
        try:
            s, e = to_min(b["start"]), to_min(b["end"])
        except ValueError:
            continue
        if e <= s:  # crosses midnight
            if now_min >= s or now_min < e:
                return i
        elif s <= now_min < e:
            return i
    return -1


def goal_tag(g):
    if g.get("at"):
        return "· " + g["at"]
    if g.get("block"):
        return "· " + g["block"]
    return ""


def render(date, store):
    blocks, ov = day_blocks(date, store)
    is_today = date == dt.date.today()
    now_min = dt.datetime.now().hour * 60 + dt.datetime.now().minute
    cur = current_index(blocks, now_min) if is_today else -1

    shape = "weekend · reset" if date.weekday() >= 5 else "weekday"
    shifted = bool(ov and ov.get("blocks"))
    if shifted:
        shape = (ov.get("label") or "shifted day") + " · override"
    left = "timetable · " + date.strftime("%A %-d %B")
    pad = max(1, WIDTH - len(left) - len(shape))
    print()
    print("  " + c(left, STEEL, bold=True) + " " * pad + c(shape, AMBER if shifted else SUB))
    print("  " + rule())

    if is_today and cur >= 0:
        b = blocks[cur]
        nowtxt = f"now {dt.datetime.now():%H:%M} · {b['name']}"
        print("  " + c(nowtxt, AMBER, bold=True) + (c("  " + b["purpose"], OVERLAY) if b["purpose"] else ""))
        print("  " + rule())
    if ov and ov.get("note"):
        print("  " + c("» " + ov["note"], SUB))
        print("  " + rule())

    if not blocks:
        print("  " + c("no routine found in schedule.md for this day", OVERLAY))
    for i, b in enumerate(blocks):
        is_cur = i == cur
        try:
            past = is_today and to_min(b["end"]) <= now_min and to_min(b["end"]) > to_min(b["start"])
        except ValueError:
            past = False
        mark = c("▸", AMBER, bold=True) if is_cur else " "
        glyph = c("■", AMBER) if is_cur else c("·", OVERLAY)
        if is_cur:
            tcol, ncol = AMBER, ICE
            name = c(b["name"], ncol, bold=True)
            tstr = c(b["start"], tcol, bold=True)
        elif past:
            name = c(b["name"], OVERLAY)
            tstr = c(b["start"], OVERLAY)
        else:
            name = c(b["name"], ICE)
            tstr = c(b["start"], SUB)
        print(f"  {mark} {tstr}  {glyph}  {name}")

    # goals
    goals = store["goals"].get(date.isoformat(), [])
    print("  " + rule())
    head = "goals today" if is_today else "goals " + date.isoformat()
    print("  " + c(head, STEEL, bold=True))
    if not goals:
        print("  " + c("none yet — timetable goal \"...\"", OVERLAY))
    for i, g in enumerate(goals, 1):
        done = g.get("done")
        box = c("✓", GREEN) if done else c("○", SUB)
        num = c(f"{i}", OVERLAY)
        txt = c(g["text"], OVERLAY) if done else c(g["text"], ICE)
        tag = c(" " + goal_tag(g), OVERLAY) if goal_tag(g) else ""
        print(f"   {box} {num}  {txt}{tag}")

    # footer
    print("  " + rule())
    el = engine_line() if is_today else ""
    if el:
        print("  " + c("engine  " + el, OVERLAY))
    print("  " + c("goal  timetable goal \"…\"", SUB) + c("    ·    shift a day  ask Claude", OVERLAY))
    print()


def render_week(store):
    base = dt.date.today()
    print()
    print("  " + c("timetable · next 7 days", STEEL, bold=True))
    print("  " + rule())
    for n in range(7):
        d = base + dt.timedelta(days=n)
        _, ov = day_blocks(d, store)
        goals = store["goals"].get(d.isoformat(), [])
        done = sum(1 for g in goals if g.get("done"))
        shifted = bool(ov and ov.get("blocks"))
        shape = "weekend" if d.weekday() >= 5 else "weekday"
        if shifted:
            shape = (ov.get("label") or "shifted")
        tag = "today" if n == 0 else d.strftime("%a")
        label = f"{tag:<5} {d.isoformat()}"
        gtxt = f"{done}/{len(goals)} goals" if goals else "—"
        line = f"  {c(label, ICE if n == 0 else SUB)}  {c(shape, AMBER if shifted else OVERLAY):<10}  {c(gtxt, SUB)}"
        print(line)
    print("  " + rule())
    print()


# ── arg helpers ──────────────────────────────────────────────────────────────
def pop_opt(args, name):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            val = args[i + 1]
            del args[i:i + 2]
            return val
    return None


def cmd_goal(args):
    date_tok = pop_opt(args, "--date") or "today"
    at = pop_opt(args, "--at")
    block = pop_opt(args, "--block")
    text = " ".join(args).strip()
    if not text:
        die("give the goal text:  timetable goal \"finish DL lecture 2\"")
    date = parse_date(date_tok)
    if not date:
        die(f"not a date: {date_tok}")
    store = load_store()
    store["goals"].setdefault(date.isoformat(), []).append(
        {"text": text, "at": at, "block": block, "done": False})
    save_store(store)
    render(date, store)


def cmd_mark(args, done):
    date_tok = pop_opt(args, "--date") or "today"
    if not args or not args[0].isdigit():
        die("which goal number?  e.g. timetable done 2")
    n = int(args[0])
    date = parse_date(date_tok)
    store = load_store()
    goals = store["goals"].get(date.isoformat(), [])
    if not (1 <= n <= len(goals)):
        die(f"no goal {n} on {date.isoformat()}")
    goals[n - 1]["done"] = done
    save_store(store)
    render(date, store)


def cmd_drop(args):
    date_tok = pop_opt(args, "--date") or "today"
    if not args or not args[0].isdigit():
        die("which goal number?  e.g. timetable drop 2")
    n = int(args[0])
    date = parse_date(date_tok)
    store = load_store()
    goals = store["goals"].get(date.isoformat(), [])
    if not (1 <= n <= len(goals)):
        die(f"no goal {n} on {date.isoformat()}")
    goals.pop(n - 1)
    save_store(store)
    render(date, store)


def cmd_note(args):
    if len(args) < 2:
        die("usage:  timetable note <date> \"a short note\"")
    date = parse_date(args[0])
    if not date:
        die(f"not a date: {args[0]}")
    text = " ".join(args[1:]).strip()
    store = load_store()
    ov = store["overrides"].setdefault(date.isoformat(), {})
    ov["note"] = text
    save_store(store)
    render(date, store)


def die(msg):
    print(c("timetable: " + msg, AMBER), file=sys.stderr)
    sys.exit(1)


# ── self-install (first interactive run) ─────────────────────────────────────
ALIAS_BEGIN = "# >>> timetable alias >>>"
ALIAS_BLOCK = f"""{ALIAS_BEGIN}
alias timetable='{INSTALL_PATH}'
# <<< timetable alias <<<
"""


def ensure_alias():
    try:
        existing = ""
        if os.path.exists(ZSHRC):
            with open(ZSHRC, encoding="utf-8") as fh:
                existing = fh.read()
        if ALIAS_BEGIN in existing or "alias timetable=" in existing:
            return False
        with open(ZSHRC, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("\n" + ALIAS_BLOCK)
        return True
    except OSError:
        return False


def bootstrap():
    # Only on a real terminal, and never when explicitly disabled (tests/pipes).
    if os.environ.get("TIMETABLE_NO_BOOTSTRAP"):
        return
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return
    here = os.path.realpath(__file__)
    if os.path.exists(INSTALL_PATH) and here == os.path.realpath(INSTALL_PATH):
        return  # already running as the installed copy
    need_copy = not os.path.exists(INSTALL_PATH) or not filecmp.cmp(here, INSTALL_PATH, shallow=False)
    if need_copy:
        print(c(f"timetable: installing to {INSTALL_PATH} (sudo once)…", SUB), file=sys.stderr)
        r = subprocess.run(["sudo", "install", "-m", "0755", here, INSTALL_PATH])
        if r.returncode != 0:
            print(c("timetable: /var/x copy skipped (no sudo). Alias not set.", AMBER), file=sys.stderr)
            return
    if ensure_alias():
        print(c(f"timetable: alias added to ~/.zshrc → {INSTALL_PATH}.  "
                "run `source ~/.zshrc` (or open a new shell).", STEEL), file=sys.stderr)


HELP = __doc__


def main():
    bootstrap()
    args = sys.argv[1:]
    cmd = args[0] if args else "today"

    if cmd in ("help", "-h", "--help"):
        print(HELP)
        return
    if cmd == "path":
        print(f"schedule  {SCHEDULE}\nstore     {STORE}\ninstalled {INSTALL_PATH}\nrepo      {REPO}")
        return
    if cmd == "install":
        # force the bootstrap even if non-interactive was the reason it skipped
        os.environ.pop("TIMETABLE_NO_BOOTSTRAP", None)
        here = os.path.realpath(__file__)
        subprocess.run(["sudo", "install", "-m", "0755", here, INSTALL_PATH])
        ensure_alias()
        print(c(f"installed to {INSTALL_PATH}; alias in ~/.zshrc", STEEL))
        return
    if cmd == "week":
        render_week(load_store())
        return
    if cmd == "goal":
        cmd_goal(args[1:])
        return
    if cmd in ("done", "undone"):
        cmd_mark(args[1:], cmd == "done")
        return
    if cmd == "drop":
        cmd_drop(args[1:])
        return
    if cmd == "note":
        cmd_note(args[1:])
        return
    if cmd == "goals":
        d = parse_date(args[1]) if len(args) > 1 else dt.date.today()
        if not d:
            die(f"not a date: {args[1]}")
        render(d, load_store())
        return

    # otherwise: a date (today/tomorrow/mon/2026-10-28/+2 …)
    d = parse_date(cmd)
    if d is None:
        die(f"unknown command or date: {cmd}  (try: timetable help)")
    render(d, load_store())


if __name__ == "__main__":
    main()
