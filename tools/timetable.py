#!/usr/bin/env python3
"""timetable — an interactive day planner over your Calamity routine.

Run `timetable` in a terminal and it opens a curses TUI: move through the
day's time-slots, attach goals to a slot, add unscheduled goals, tick them
off, and leave a note on any day (an exam, an event, time you'll lose) so
Claude can see it. Arrow left/right moves between days.

The routine comes from learner/schedule.md (the source of truth the coach
maintains); goals, notes and date-specific shifts live in
learner/timetable.json, so they sync with the rest of your progress.

Keys in the TUI:
  ↑ ↓ / j k   move between slots and goals
  ← → / h l   previous / next day        t / T   today / jump to a date
  ⏎ or a      slot → add a goal to it; goal → toggle done
  A           add an unscheduled goal     space   toggle a goal done
  e / d       edit / delete a goal        n       set the day's note
  ?           key help                    q       quit (saves as you go)

Without a terminal (a pipe, or Claude running it) it prints the day instead.
Scripting commands still work:
  timetable print [date]    print a day (date, today/tomorrow, mon..sun, +N)
  timetable week            the next 7 days at a glance
  timetable goal "text"     add a goal   (--at HH:MM / --block "name" / --date)
  timetable goals [date] · done N · undone N · drop N · note <date> "…"
  timetable path · help

`timetable install` puts a small `timetable` launcher in ~/.local/bin
(nothing else on the system changes) and prints the line that puts that
folder on your PATH if it is not there yet. The blocks come from the engine
(`python3 engine/calamity.py day <date> --json`), so the TUI, the brief and
`day` read learner/schedule.md the same way.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")


def _repo():
    """The checkout this file belongs to; CALAMITY_ROOT (or the older CALAMITY_REPO) points elsewhere."""
    env = os.environ.get("CALAMITY_ROOT") or os.environ.get("CALAMITY_REPO")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if os.path.isfile(os.path.join(here, "engine", "calamity.py")):
        return here
    return os.path.join(HOME, "calamity-framework")


REPO = _repo()
ENGINE = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "engine", "calamity.py")
SCHEDULE = os.path.join(REPO, "learner", "schedule.md")
STORE = os.path.join(REPO, "learner", "timetable.json")
LAUNCHER = os.path.join(HOME, ".local", "bin", "timetable")
WIDTH = 64

# ── fog palette (truecolor), for the static print output ─────────────────────
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


# ── the day's blocks, from the engine (one parser for everything) ────────────
def engine_day(date):
    """The engine's view of a day (`day <date> --json`), or None when it cannot be read."""
    env = dict(os.environ, CALAMITY_ROOT=REPO)
    try:
        out = subprocess.run([sys.executable, ENGINE, "day", date.isoformat(), "--json"], cwd=REPO, env=env,
                             capture_output=True, text=True, encoding="utf-8", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


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
    """The day's blocks (its own, if the date was shifted, else the schedule's) and its override entry."""
    ov = store["overrides"].get(date.isoformat())
    data = engine_day(date) or {}
    blocks = [{"start": b["start"], "end": b["end"], "name": b["name"], "purpose": b["purpose"]}
              for b in data.get("blocks", [])]
    return blocks, ov


# ── engine footer (best-effort) ──────────────────────────────────────────────
def engine_line():
    try:
        out = subprocess.run([sys.executable, ENGINE, "statusline"], cwd=REPO,
                             env=dict(os.environ, CALAMITY_ROOT=REPO), capture_output=True, text=True, timeout=6)
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


# ── static rendering (the non-tty fallback and `print`) ──────────────────────
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
    goals = store["goals"].get(date.isoformat(), [])
    for i, b in enumerate(blocks):
        is_cur = i == cur
        try:
            past = is_today and to_min(b["end"]) <= now_min and to_min(b["end"]) > to_min(b["start"])
        except ValueError:
            past = False
        mark = c("▸", AMBER, bold=True) if is_cur else " "
        glyph = c("■", AMBER) if is_cur else c("·", OVERLAY)
        if is_cur:
            name = c(b["name"], ICE, bold=True)
            tstr = c(b["start"], AMBER, bold=True)
        elif past:
            name = c(b["name"], OVERLAY)
            tstr = c(b["start"], OVERLAY)
        else:
            name = c(b["name"], ICE)
            tstr = c(b["start"], SUB)
        print(f"  {mark} {tstr}  {glyph}  {name}")
        for g in [x for x in goals if x.get("block") == b["name"]]:
            box = c("✓", GREEN) if g.get("done") else c("○", SUB)
            txt = c(g["text"], OVERLAY) if g.get("done") else c(g["text"], ICE)
            print(f"        {box} {txt}")

    print("  " + rule())
    head = "goals" if is_today else "goals " + date.isoformat()
    print("  " + c(head, STEEL, bold=True))
    gen = [g for g in goals if not g.get("block")]
    if not goals:
        print("  " + c("none yet", OVERLAY))
    for g in gen:
        box = c("✓", GREEN) if g.get("done") else c("○", SUB)
        txt = c(g["text"], OVERLAY) if g.get("done") else c(g["text"], ICE)
        print(f"   {box} {txt}")

    print("  " + rule())
    el = engine_line() if is_today else ""
    if el:
        print("  " + c("engine  " + el, OVERLAY))
    print("  " + c("plan  timetable", SUB) + c("    ·    shift a day  ask Claude", OVERLAY))
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
        note = (ov or {}).get("note")
        tag = "today" if n == 0 else d.strftime("%a")
        label = f"{tag:<5} {d.isoformat()}"
        gtxt = f"{done}/{len(goals)} goals" if goals else "—"
        line = f"  {c(label, ICE if n == 0 else SUB)}  {c(shape, AMBER if shifted else OVERLAY):<10}  {c(gtxt, SUB)}"
        if note:
            line += c("   » " + note[:28], AMBER)
        print(line)
    print("  " + rule())
    print()


# ── interactive TUI (curses) ─────────────────────────────────────────────────
# Terminal colours approximate the fog palette — truecolor isn't portable in
# curses, so we map to the nearest xterm-256 indices (or the 8 base colours).
curses = None
CP = {}


def _init_colors():
    try:
        curses.start_color()
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = 0
    if curses.COLORS >= 256:
        spec = {"steel": 110, "amber": 179, "sub": 246, "dim": 240, "green": 108, "ice": 253}
    else:
        spec = {"steel": curses.COLOR_CYAN, "amber": curses.COLOR_YELLOW,
                "sub": curses.COLOR_WHITE, "dim": curses.COLOR_BLUE,
                "green": curses.COLOR_GREEN, "ice": curses.COLOR_WHITE}
    for i, (name, fg) in enumerate(spec.items(), 1):
        try:
            curses.init_pair(i, fg, bg)
            CP[name] = curses.color_pair(i)
        except curses.error:
            CP[name] = 0


def _prompt(stdscr, label, prefill=""):
    """A one-line editable field on the bottom row. Enter submits, Esc cancels."""
    curses.curs_set(1)
    buf = list(prefill)
    res = None
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.move(h - 1, 0)
        stdscr.clrtoeol()
        shown = (label + "".join(buf))
        if len(shown) > w - 2:
            shown = shown[-(w - 2):]
        try:
            stdscr.addnstr(h - 1, 0, shown, w - 1, CP.get("amber", 0))
        except curses.error:
            pass
        stdscr.refresh()
        try:
            ch = stdscr.get_wch()
        except curses.error:
            continue
        if isinstance(ch, str):
            if ch in ("\n", "\r"):
                res = "".join(buf).strip()
                break
            if ch == "\x1b":                       # Esc → cancel
                res = None
                break
            if ch in ("\x7f", "\b"):
                if buf:
                    buf.pop()
            elif ch.isprintable():
                buf.append(ch)
        else:                                       # special key (int)
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                if buf:
                    buf.pop()
    curses.curs_set(0)
    return res


def _put(stdscr, y, x, text, attr):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w and text:
        try:
            stdscr.addnstr(y, x, text, max(0, w - 1 - x), attr)
        except curses.error:
            pass


def _put_right(stdscr, y, text, attr, pad=2):
    _, w = stdscr.getmaxyx()
    _put(stdscr, y, max(0, w - pad - len(text)), text, attr)


def _meter(done, total, width=7):
    if total <= 0:
        return ""
    f = max(0, min(width, round(width * done / total)))
    return "▓" * f + "░" * (width - f)


def _build(state):
    """Return (lines, selectables, meta): each body line is (segments, sel_id)."""
    date, store = state["date"], state["store"]
    blocks, ov = day_blocks(date, store)
    goals = store["goals"].get(date.isoformat(), [])
    is_today = date == dt.date.today()
    now_min = dt.datetime.now().hour * 60 + dt.datetime.now().minute
    cur = current_index(blocks, now_min) if is_today else -1

    lines, sels = [], []

    def add(segs, ref=None):
        sid = None
        if ref is not None:
            sid = len(sels)
            sels.append(ref)
        lines.append((segs, sid))

    if not blocks:
        add([("no routine in schedule.md for this day", CP["dim"])])
    for i, b in enumerate(blocks):
        is_cur = i == cur
        try:
            past = is_today and to_min(b["start"]) < to_min(b["end"]) <= now_min
        except ValueError:
            past = False
        if is_cur:
            node, ncol, tcol = "●", CP["amber"] | curses.A_BOLD, CP["amber"]
        elif past:
            node, ncol, tcol = "·", CP["dim"], CP["dim"]
        else:
            node, ncol, tcol = "○", CP["ice"], CP["sub"]
        segs = [(node + "  ", tcol), (b["start"] + "  ", tcol), (b["name"], ncol)]
        if is_cur:
            segs.append(("   now " + dt.datetime.now().strftime("%H:%M"), CP["amber"]))
        add(segs, ref=("slot", b))
        for g in [x for x in goals if x.get("block") == b["name"]]:
            box = "✓" if g.get("done") else "○"
            bc = CP["green"] if g.get("done") else CP["sub"]
            tc = CP["dim"] if g.get("done") else CP["ice"]
            add([("      " + box + "  ", bc), (g["text"], tc)], ref=("goal", g))

    gen = [g for g in goals if not g.get("block")]
    add([("", 0)])
    add([("unscheduled", CP["steel"] | curses.A_BOLD)])
    if not gen:
        add([("   press A to add a goal not tied to a slot", CP["dim"])])
    for g in gen:
        box = "✓" if g.get("done") else "○"
        bc = CP["green"] if g.get("done") else CP["sub"]
        tc = CP["dim"] if g.get("done") else CP["ice"]
        add([("   " + box + "  ", bc), (g["text"], tc)], ref=("goal", g))

    shifted = bool(ov and ov.get("blocks"))
    shape = "weekend · reset" if date.weekday() >= 5 else "weekday"
    if shifted:
        shape = (ov.get("label") or "shifted day") + " · override"
    meta = {"note": ov.get("note") if ov else None, "shape": shape, "shifted": shifted,
            "done": sum(1 for g in goals if g.get("done")), "total": len(goals)}
    return lines, sels, meta


def _draw(stdscr, state):
    lines, sels, meta = _build(state)
    state["sels"] = sels
    state["sel"] = max(0, min(state["sel"], len(sels) - 1)) if sels else 0

    sel_line = next((li for li, (_, sid) in enumerate(lines)
                     if sid is not None and sid == state["sel"]), None)

    h, w = stdscr.getmaxyx()
    top_rows, bot_rows = 4, 3                 # header: blank/title/note/rule — footer: rule/engine/keys
    body_h = max(1, h - top_rows - bot_rows)
    top = state["top"]
    if sel_line is not None:
        if sel_line < top:
            top = sel_line
        elif sel_line >= top + body_h:
            top = sel_line - body_h + 1
    top = max(0, min(top, max(0, len(lines) - body_h)))
    state["top"] = top

    stdscr.erase()

    # header: title · date (left), shape badge (right); note + goals meter; a rule
    _put(stdscr, 1, 2, "timetable", CP["steel"] | curses.A_BOLD)
    _put(stdscr, 1, 12, "· " + state["date"].strftime("%A %-d %B").lower(), CP["sub"])
    _put_right(stdscr, 1, meta["shape"], CP["amber"] if meta["shifted"] else CP["sub"])
    note = meta["note"]
    _put(stdscr, 2, 2, "✎  " + (note or "no note — press n to log an exam / event"),
         CP["amber"] if note else CP["dim"])
    if meta["total"]:
        _put_right(stdscr, 2, f"{_meter(meta['done'], meta['total'])}  "
                   f"{meta['done']}/{meta['total']}", CP["sub"])
    _put(stdscr, 3, 2, "─" * (w - 4), CP["dim"])

    # body (scrolls); the selected row gets a soft amber bar and bold text
    for row in range(body_h):
        li = top + row
        if li >= len(lines):
            break
        y = top_rows + row
        segs, sid = lines[li]
        selected = sid is not None and sid == state["sel"]
        if selected:
            _put(stdscr, y, 0, "▌", CP["amber"] | curses.A_BOLD)
        x = 3
        for text, attr in segs:
            if not text:
                continue
            _put(stdscr, y, x, text, attr | (curses.A_BOLD if selected else 0))
            x += len(text)

    # footer: a rule, the engine line, the keys
    _put(stdscr, h - 3, 2, "─" * (w - 4), CP["dim"])
    if state.get("engine"):
        _put(stdscr, h - 2, 2, "· " + state["engine"], CP["dim"])
    _put(stdscr, h - 1, 2,
         "↑↓ move   ← → day   ⏎/a goal   A add   space done   "
         "e edit   d del   n note   t today   ? keys   q quit", CP["sub"])
    stdscr.refresh()


def _help_overlay(stdscr):
    keys = [
        ("↑ ↓  / j k", "move between slots and goals"),
        ("← →  / h l", "previous / next day"),
        ("t  /  T", "jump to today  /  to a date you type"),
        ("⏎  or  a", "slot: add a goal to it · goal: toggle done"),
        ("A", "add an unscheduled goal for the day"),
        ("space", "toggle the selected goal done"),
        ("e  /  d", "edit / delete the selected goal"),
        ("n", "set the day's note — exam, event, lost time"),
        ("q", "quit  (everything saves as you go)"),
    ]
    h, w = stdscr.getmaxyx()
    bh, bw = len(keys) + 4, min(w - 2, 60)
    y0, x0 = max(0, (h - bh) // 2), max(0, (w - bw) // 2)
    win = curses.newwin(bh, bw, y0, x0)
    win.erase()
    win.box()
    try:
        win.addnstr(0, 2, " keys ", bw - 4, CP["steel"] | curses.A_BOLD)
        for i, (k, desc) in enumerate(keys, 2):
            win.addnstr(i, 2, k, 12, CP["amber"])
            win.addnstr(i, 15, desc, bw - 17, CP["sub"])
    except curses.error:
        pass
    win.refresh()
    win.getch()


def _tui(stdscr, start_date):
    curses.curs_set(0)
    stdscr.keypad(True)
    _init_colors()
    state = {"date": start_date, "sel": 0, "top": 0,
             "store": load_store(), "sels": [], "engine": engine_line()}

    while True:
        _draw(stdscr, state)
        try:
            k = stdscr.getch()
        except KeyboardInterrupt:
            break
        sels = state["sels"]
        sel = state["sel"]
        ref = sels[sel] if 0 <= sel < len(sels) else None
        store = state["store"]
        iso = state["date"].isoformat()

        if k in (ord("q"), ord("Q")):
            break
        elif k in (curses.KEY_DOWN, ord("j")):
            state["sel"] = min(len(sels) - 1, sel + 1) if sels else 0
        elif k in (curses.KEY_UP, ord("k")):
            state["sel"] = max(0, sel - 1)
        elif k in (curses.KEY_RIGHT, ord("l")):
            state["date"] += dt.timedelta(days=1)
            state["sel"] = state["top"] = 0
        elif k in (curses.KEY_LEFT, ord("h")):
            state["date"] -= dt.timedelta(days=1)
            state["sel"] = state["top"] = 0
        elif k == ord("t"):
            state["date"] = dt.date.today()
            state["sel"] = state["top"] = 0
        elif k == ord("T"):
            r = _prompt(stdscr, "jump to (YYYY-MM-DD / mon / +7): ")
            d = parse_date(r) if r else None
            if d:
                state["date"] = d
                state["sel"] = state["top"] = 0
        elif k == ord("n"):
            ov = store["overrides"].get(iso, {})
            r = _prompt(stdscr, "note (exam/event; empty clears): ", prefill=ov.get("note", ""))
            if r is not None:
                o = store["overrides"].setdefault(iso, {})
                if r:
                    o["note"] = r
                else:
                    o.pop("note", None)
                    if not o:
                        store["overrides"].pop(iso, None)
                save_store(store)
        elif k in (10, 13, ord("a")):
            if ref and ref[0] == "slot":
                b = ref[1]
                r = _prompt(stdscr, f"goal for {b['name']}: ")
                if r:
                    store["goals"].setdefault(iso, []).append(
                        {"text": r, "at": b["start"], "block": b["name"], "done": False})
                    save_store(store)
            elif ref and ref[0] == "goal":
                ref[1]["done"] = not ref[1].get("done")
                save_store(store)
        elif k == ord("A"):
            r = _prompt(stdscr, "new unscheduled goal: ")
            if r:
                store["goals"].setdefault(iso, []).append(
                    {"text": r, "at": None, "block": None, "done": False})
                save_store(store)
        elif k == ord(" "):
            if ref and ref[0] == "goal":
                ref[1]["done"] = not ref[1].get("done")
                save_store(store)
        elif k == ord("e"):
            if ref and ref[0] == "goal":
                r = _prompt(stdscr, "edit goal: ", prefill=ref[1]["text"])
                if r:
                    ref[1]["text"] = r
                    save_store(store)
        elif k in (ord("d"), curses.KEY_DC):
            if ref and ref[0] == "goal":
                lst = store["goals"].get(iso, [])
                try:
                    lst.remove(ref[1])
                except ValueError:
                    pass
                if not lst:
                    store["goals"].pop(iso, None)
                save_store(store)
                state["sel"] = max(0, sel - 1)
        elif k == ord("?"):
            _help_overlay(stdscr)
        # KEY_RESIZE and anything else: just redraw


def run_tui(start_date):
    global curses
    import curses as _curses
    curses = _curses
    curses.wrapper(_tui, start_date)


def launch(date):
    if (sys.stdout.isatty() and sys.stdin.isatty()
            and not os.environ.get("TIMETABLE_NO_TUI")):
        try:
            run_tui(date)
            return
        except Exception as e:                     # curses unavailable / tiny term
            print(c(f"timetable: TUI unavailable ({e}); printing instead.", AMBER),
                  file=sys.stderr)
    render(date, load_store())


# ── CLI subcommands (scripting / non-tty) ────────────────────────────────────
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


# ── install: a launcher on PATH, nothing else ───────────────────────────────
def install():
    if os.name == "nt":
        print("On Windows, run it as:  py -3 \"%s\"  (or python instead of py -3)" % os.path.realpath(__file__))
        return
    os.makedirs(os.path.dirname(LAUNCHER), exist_ok=True)
    with open(LAUNCHER, "w", encoding="utf-8") as fh:
        fh.write('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, os.path.realpath(__file__)))
    os.chmod(LAUNCHER, 0o755)
    print(c("installed: %s (runs this copy of tools/timetable.py)" % LAUNCHER, STEEL))
    if os.path.dirname(LAUNCHER) not in os.environ.get("PATH", "").split(os.pathsep):
        print("~/.local/bin is not on your PATH yet. Add this line to your shell's start-up file:")
        print('  bash or zsh (~/.bashrc, ~/.zshrc):  export PATH="$HOME/.local/bin:$PATH"')
        print("  fish:                               fish_add_path ~/.local/bin")


HELP = __doc__


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else None

    if cmd in ("help", "-h", "--help"):
        print(HELP)
        return
    if cmd == "path":
        print(f"schedule  {SCHEDULE}\nstore     {STORE}\nlauncher  {LAUNCHER}\nrepo      {REPO}")
        return
    if cmd == "install":
        install()
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
    if cmd == "print":
        d = parse_date(args[1]) if len(args) > 1 else dt.date.today()
        if not d:
            die(f"not a date: {args[1]}")
        render(d, load_store())
        return

    # default: open the TUI (or print, without a terminal), at today or a date
    if cmd is None:
        launch(dt.date.today())
        return
    d = parse_date(cmd)
    if d is None:
        die(f"unknown command or date: {cmd}  (try: timetable help)")
    launch(d)


if __name__ == "__main__":
    main()
