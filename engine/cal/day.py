"""The day's shape: blocks from learner/schedule.md, goals and notes from learner/timetable.json.

The schedule's front matter holds the blocks, one line each:

    weekday:
      - "09:15-09:45 | Recall | due reviews across everything"
      - "09:45-12:15 | GATE block A | new theory and lectures, each tested after"
    weekend:
      - "09:15-09:45 | Recall | due reviews"
    sat:                     optional: one day of the week with a shape of its own (mon ... sun)
      - ...

Its body stays the learner's own view. A schedule written as tables under `## Weekday` and
`## Weekend` headings (the earlier timetable format) is read too, and `day migrate` turns it into
front matter. learner/timetable.json keeps, per date, goals, a note and, when that day's shape
changes, its own blocks:

    {"goals": {"2026-10-27": [{"text": "...", "at": "HH:MM", "block": "...", "done": false}]},
     "overrides": {"2026-10-27": {"note": "...", "blocks": [{"time": "09:00-10:00", "name": "...", "purpose": "..."}]}}}

The engine and tools/timetable.py read both through this module, so there is one parser. The day
is the learner's day: it rolls over at `day_start_hour`, so a block that ends after midnight still
belongs to the evening it began in.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta

from . import fm
from .store import read_text, write_text
from .util import CalError

WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
BLOCK = re.compile(r"^\s*(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})\s*\|\s*([^|]*?)\s*(?:\|\s*(.*?))?\s*$")


def schedule_path(repo) -> str:
    return os.path.join(repo.learner, "schedule.md")


def store_path(repo) -> str:
    return os.path.join(repo.learner, "timetable.json")


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def parse_block(text) -> dict | None:
    """'HH:MM-HH:MM | name | purpose' as a block, or None."""
    m = BLOCK.match(str(text))
    if not m or not m.group(3):
        return None
    start, end, name, purpose = m.group(1), m.group(2), m.group(3), m.group(4) or ""
    if not (0 <= _minutes(start) < 24 * 60 and 0 <= _minutes(end) <= 24 * 60):
        return None
    purpose = purpose.strip()
    return {"start": start.zfill(5), "end": end.zfill(5), "name": re.sub(r"\*+", "", name).strip(),
            "purpose": "" if purpose in ("-", "—") else re.sub(r"\*+", "", purpose)}


def _table_blocks(lines) -> list:
    """Blocks from markdown table rows: | HH:MM-HH:MM | name | purpose |."""
    out = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) >= 2:
            block = parse_block(" | ".join(cells[:3]))
            if block:
                out.append(block)
    return out


def _sections(body: str) -> dict:
    """'weekday' / 'weekend' -> the table blocks under a level-2 heading that starts with that word."""
    out, current, lines = {}, None, body.split("\n")
    for line in lines:
        if line.startswith("## "):
            word = line[3:].strip().lower()
            current = "weekday" if word.startswith("weekday") else "weekend" if word.startswith("weekend") else None
            continue
        if line.startswith("# "):
            current = None
        if current:
            out.setdefault(current, []).append(line)
    return {k: _table_blocks(v) for k, v in out.items()}


def load_schedule(repo):
    """(front matter, body, problem). A front matter that cannot be read is reported, not fatal."""
    path = schedule_path(repo)
    if not os.path.isfile(path):
        return {}, "", None
    text = fm.decode(repo.read_bytes(path) or b"", repo.rel(path), lenient=True)
    try:
        meta, body = fm.parse(text, repo.rel(path))
        return meta, body, None
    except fm.FrontMatterError as exc:
        try:
            _, body, _ = fm.split(text)
        except fm.FrontMatterError:
            body = text
        return {}, body, "%s; `day migrate` rewrites its front matter in the one format" % exc


def base_blocks(repo, day: date):
    """(blocks, where they came from) for this date from the schedule alone."""
    meta, body, _ = load_schedule(repo)
    kind = "weekend" if day.weekday() >= 5 else "weekday"
    for key in (WEEK[day.weekday()], kind):
        lines = meta.get(key)
        if isinstance(lines, list) and lines:
            return [b for b in (parse_block(x) for x in lines) if b], "schedule.md (%s)" % key
    tables = _sections(body).get(kind) or []
    if tables:
        return tables, "schedule.md (%s table)" % kind
    return [], "no blocks in schedule.md"


def load_store(repo) -> dict:
    path = store_path(repo)
    data = {}
    if os.path.isfile(path):
        try:
            data = json.loads(read_text(path) or "{}")
        except ValueError:
            raise CalError("%s is not valid JSON; fix it or move it aside" % repo.rel(path))
    if not isinstance(data, dict):
        raise CalError("%s should hold a JSON object" % repo.rel(path))
    data.setdefault("goals", {})
    data.setdefault("overrides", {})
    return data


def save_store(repo, data: dict) -> None:
    write_text(store_path(repo), json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def blocks_for(repo, day: date, store: dict | None = None):
    """(blocks, source, note) for a date: its own blocks in timetable.json, else the schedule's."""
    store = load_store(repo) if store is None else store
    override = store["overrides"].get(day.isoformat()) or {}
    note = str(override.get("note") or "")
    own = [parse_block("%s | %s | %s" % (b.get("time", ""), b.get("name", ""), b.get("purpose", "")))
           for b in override.get("blocks") or [] if isinstance(b, dict)]
    own = [b for b in own if b]
    if own:
        return own, "timetable.json (this date)", note
    blocks, source = base_blocks(repo, day)
    return blocks, source, note


def learner_date(repo, when) -> date:
    return (when - timedelta(hours=int(repo.cfg("day_start_hour", 4)))).date()


def parse_day(token: str | None, repo, when) -> date:
    """today, tomorrow, yesterday, +N, -N, mon..sun (the next one, today included), or YYYY-MM-DD."""
    base = learner_date(repo, when)
    t = (token or "today").strip().lower()
    if t in ("today", ""):
        return base
    if t == "tomorrow":
        return base + timedelta(days=1)
    if t == "yesterday":
        return base - timedelta(days=1)
    if re.fullmatch(r"[+-]\d{1,3}", t):
        return base + timedelta(days=int(t))
    if t[:3] in WEEK:
        return base + timedelta(days=(WEEK.index(t[:3]) - base.weekday()) % 7)
    try:
        return date.fromisoformat(t)
    except ValueError:
        raise CalError("not a day: %r (today, tomorrow, +2, fri or 2026-11-03)" % token)


def _spans(blocks, day: date):
    """Each block's (start, end) as datetimes on the learner day; a block may end after midnight."""
    out, last = [], None
    for b in blocks:
        start = datetime.combine(day, datetime.min.time()) + timedelta(minutes=_minutes(b["start"]))
        if last is not None and start < last - timedelta(hours=12):   # the list has passed midnight
            start += timedelta(days=1)
        end = start + timedelta(minutes=(_minutes(b["end"]) - _minutes(b["start"])) % (24 * 60))
        out.append((start, end))
        last = start
    return out


def position(blocks, day: date, when):
    """(index of the block under way or None, index of the next one or None) at `when`."""
    naive = when.replace(tzinfo=None)
    spans = _spans(blocks, day)
    now = next((i for i, (s, e) in enumerate(spans) if s <= naive < e), None)
    upcoming = next((i for i, (s, _) in enumerate(spans) if s > naive), None)
    return now, upcoming


def now_lines(repo, when) -> list:
    """The brief's lines: where the learner is in the day, and the day's note."""
    day = learner_date(repo, when)
    try:
        blocks, _, note = blocks_for(repo, day)
    except (CalError, OSError):
        return []
    out = []
    if blocks:
        now, upcoming = position(blocks, day, when)
        nxt = (" · next: %s %s" % (blocks[upcoming]["name"], blocks[upcoming]["start"])) if upcoming is not None else ""
        if now is not None:
            b = blocks[now]
            out.append("Now: %s (%s-%s)%s" % (b["name"], b["start"], b["end"], nxt))
        else:
            out.append("Now: between blocks%s" % (nxt or " · the day's blocks are over"))
    if note:
        out.append("Day note: %s" % note)
    return out


def view(repo, day: date, when) -> dict:
    store = load_store(repo)
    blocks, source, note = blocks_for(repo, day, store)
    now, upcoming = position(blocks, day, when) if day == learner_date(repo, when) else (None, None)
    rows = [dict(b, now=(i == now)) for i, b in enumerate(blocks)]
    _, _, problem = load_schedule(repo)
    return {"date": day.isoformat(), "weekday": WEEK[day.weekday()], "source": source, "blocks": rows,
            "now": now, "next": upcoming, "note": note, "goals": store["goals"].get(day.isoformat(), []),
            "problem": problem}


def text(v: dict, finish: str | None = None) -> str:
    lines = ["%s %s · %s" % (v["weekday"].capitalize(), v["date"], v["source"])]
    if v["problem"]:
        lines.append("note: %s" % v["problem"])
    for i, b in enumerate(v["blocks"]):
        mark = "▸" if b["now"] else (" " if v["now"] is None or i > v["now"] else "·")
        lines.append("%s %s-%s  %s%s" % (mark, b["start"], b["end"], b["name"], ("  — " + b["purpose"]) if b["purpose"] else ""))
    if not v["blocks"]:
        lines.append("  no blocks: write them into learner/schedule.md (framework/rules/scheduler.md shows how)")
    if v["note"]:
        lines.append("day note: %s" % v["note"])
    for n, g in enumerate(v["goals"], 1):
        where = (" @%s" % g["at"]) if g.get("at") else (" [%s]" % g["block"]) if g.get("block") else ""
        lines.append("goal %d: [%s] %s%s" % (n, "x" if g.get("done") else " ", g.get("text", ""), where))
    if finish:
        lines.append(finish)
    return "\n".join(lines)


def set_note(repo, day: date, note: str) -> str:
    store = load_store(repo)
    override = store["overrides"].setdefault(day.isoformat(), {})
    if note.strip():
        override["note"] = note.strip()
    else:
        override.pop("note", None)
        if not override:
            store["overrides"].pop(day.isoformat())
    save_store(repo, store)
    return "note for %s %s" % (day.isoformat(), "saved" if note.strip() else "removed")


def add_goal(repo, day: date, goal: str, at: str | None = None, block: str | None = None) -> str:
    if not goal.strip():
        raise CalError("say what the goal is: day goal \"finish DL lecture 2\"")
    if at and not re.fullmatch(r"\d{1,2}:\d{2}", at):
        raise CalError("--at takes a time such as 14:30")
    store = load_store(repo)
    goals = store["goals"].setdefault(day.isoformat(), [])
    goals.append({"text": goal.strip(), "at": at.zfill(5) if at else None, "block": block, "done": False})
    save_store(repo, store)
    return "goal %d for %s: %s" % (len(goals), day.isoformat(), goal.strip())


def mark_goal(repo, day: date, number: int, done: bool) -> str:
    store = load_store(repo)
    goals = store["goals"].get(day.isoformat(), [])
    if not 1 <= number <= len(goals):
        raise CalError("%s has %d goal(s); there is no goal %d" % (day.isoformat(), len(goals), number))
    goals[number - 1]["done"] = done
    save_store(repo, store)
    return "goal %d %s: %s" % (number, "done" if done else "not done", goals[number - 1]["text"])


def migrate(repo, write: bool = False) -> str:
    """Rewrite the schedule's front matter in the one format: each value on one line, and the weekday and
    weekend tables of the body as block lists. The body is kept as it is."""
    path = schedule_path(repo)
    if not os.path.isfile(path):
        raise CalError("there is no learner/schedule.md yet (the coach skill writes one with the learner)")
    raw = fm.decode(repo.read_bytes(path) or b"", repo.rel(path), lenient=True)
    head, body, _ = fm.split(raw)
    meta, order, key = {}, [], None
    for line in head:                          # values continued on indented lines are joined into one
        m = re.match(r"^([A-Za-z0-9_][A-Za-z0-9_.\-]*)\s*:(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key = m.group(1)
            order.append(key)
            meta[key] = [m.group(2).strip()]
        elif key and line.strip():
            meta[key].append(line.strip())
    tables = _sections(body)
    lines = []
    for key in order:
        parts = meta[key]
        if parts[0] == "" and all(p.startswith("- ") for p in parts[1:]):     # already a block list
            lines.append("%s:" % key)
            lines.extend("  " + p for p in parts[1:])
        else:
            value = " ".join(p for p in parts if p)
            try:
                value = fm.dump_value(fm.parse_value(value)) if value else ""
            except fm.FrontMatterError:
                value = fm.dump_value(value)
            lines.append("%s: %s" % (key, value))
    added = []
    for kind in ("weekday", "weekend"):
        if kind not in meta and tables.get(kind):
            lines.append("%s:" % kind)
            lines.extend('  - "%s-%s | %s%s"' % (b["start"], b["end"], b["name"].replace('"', "'"),
                                                  (" | " + b["purpose"].replace('"', "'")) if b["purpose"] else "")
                         for b in tables[kind])
            added.append("%s (%d blocks)" % (kind, len(tables[kind])))
    new = "---\n" + "\n".join(lines) + "\n---\n" + body
    fm.parse(new, repo.rel(path))              # the result must read back
    if new == raw:
        return "learner/schedule.md is in the one format already"
    summary = "front matter: %s" % (", ".join(added) if added else "values joined onto one line each")
    if write:
        write_text(path, new)
        return "rewrote learner/schedule.md (%s); the body is unchanged" % summary
    return "would rewrite learner/schedule.md (%s); run `day migrate --write` to do it\n\n%s" % (
        summary, "---\n" + "\n".join(lines) + "\n---")
