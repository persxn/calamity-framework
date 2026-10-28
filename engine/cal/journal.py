"""What happened, by date: one day's record, a history table, and the monthly journal files.

A model answering "what did I do in October?" should read thirty lines, not replay the log. So the
engine derives, from the event log alone:

    day <date>                    the day's shape (cal.day) and, below it, what was recorded that day
    history --by day|week|month   one row per period, optionally for one skill or one track
    learner/journal/<YYYY-MM>.md  a month on one page: a summary, then one line per active day

The journal is rebuilt by `rebuild` (which /sync runs) and, like PROGRESS.md, depends only on the
log, the tree and the profile, never on the clock or the machine: two machines holding the same
events write the same files. Nobody edits it by hand.
"""
from __future__ import annotations

import os
import re
from datetime import date, timedelta

from .store import Repo, write_text
from .util import CalError, fmt_minutes, pct, table

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def journal_dir(repo: Repo) -> str:
    return os.path.join(repo.learner, "journal")


# ---------------------------------------------------------------- one record per learner day


def _blank(day: str) -> dict:
    return {"day": day, "minutes": 0.0, "sessions": 0, "answers": 0, "ok": 0, "new": 0, "reviews": 0,
            "taught": [], "consolidated": [], "lectures": 0, "lecture_min": 0, "practice": 0, "practice_ok": 0,
            "workout": 0, "mocks": [], "passes": [], "feedback": 0}


def _match(key: str, skill: str | None, track: str | None, tree) -> bool:
    sid = key.split("/", 1)[0]
    if skill and sid != skill:
        return False
    if track:
        node = tree.nodes.get(sid)
        return node is not None and node.track == track
    return True


def records(repo: Repo, tree, state, skill: str | None = None, track: str | None = None) -> dict:
    """{learner day: record} for every day with anything recorded. With a skill or a track, only the answers,
    teaching and consolidation that belong to it (time, lectures, practice and workouts are not split)."""
    narrowed = bool(skill or track)
    out = {}

    def rec(dt, on=None):
        key = on if isinstance(on, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", on) else state.day(dt)
        r = out.get(key)
        if r is None:
            r = out[key] = _blank(key)
        return r

    if not narrowed:
        for key, ds in state.days.items():
            r = out.setdefault(key, _blank(key))
            r.update(minutes=ds.active_min, sessions=ds.sessions, answers=ds.attempts, ok=ds.ok, new=ds.new,
                     reviews=ds.reviews, lectures=ds.src_done, lecture_min=ds.src_min, workout=ds.workout_min)
    errors = list(repo.event_errors)
    events = repo.events()
    repo.event_errors = errors      # reading the log again must not forget what the replay found wrong
    for e in events:
        t, dt = e["t"], e["_dt"]
        if t == "attempt" and narrowed:
            if e["id"] in state._voided or e.get("kind") == "placement":
                continue
            key = state.canon(str(e.get("topic") or ""))
            if not _match(key, skill, track, tree):
                continue
            r = rec(dt)
            r["answers"] += 1
            r["ok"] += 1 if e.get("ok") else 0
            ts = state.topics.get(key)
            first = ts is not None and ts.first_ts is not None and ts.first_ts == dt
            r["new" if first else "reviews"] += 1
        elif t == "covered" and (e.get("by") or "tutor") != "source":
            key = state.canon(str(e.get("topic") or ""))
            if _match(key, skill, track, tree):
                r = rec(dt)
                if key not in r["taught"]:
                    r["taught"].append(key)
        elif narrowed:
            continue
        elif t == "practice_attempt" and e.get("result") != "skipped":
            r = rec(dt)
            n = len(e.get("qs") or [])
            r["practice"] += n
            r["practice_ok"] += n if e.get("result") == "solved" else 0
        elif t == "mock":
            rec(dt, e.get("date"))["mocks"].append("%s %s/%s" % (e.get("paper") or "mock", _num(e.get("score")), _num(e.get("max"))))
        elif t == "gate_pass" and e.get("done"):
            rec(dt, e.get("done"))["passes"].append("%s pass %s" % (state.canon_skill(str(e.get("skill"))), e.get("n")))
        elif t == "feedback":
            rec(dt)["feedback"] += 1
    for key in state.topics:
        if not _match(key, skill, track, tree):
            continue
        at = state.consolidated_at(key)
        if at is not None:
            rec(at)["consolidated"].append(key)
    for r in out.values():
        r["consolidated"].sort()
    return out


def _num(value) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "?"
    return ("%d" % f) if f == int(f) else ("%.2f" % f)


def _active(r: dict) -> bool:
    return bool(r["answers"] or r["taught"] or r["consolidated"] or r["lectures"] or r["practice"] or r["workout"]
                or r["mocks"] or r["passes"] or r["minutes"] >= 5)


def _short(keys, n: int = 4) -> str:
    shown = ", ".join(keys[:n])
    return shown + (" +%d" % (len(keys) - n) if len(keys) > n else "")


def line(r: dict) -> str:
    """One day in one line, the parts that happened only."""
    bits = []
    if r["minutes"] >= 1:
        bits.append("%s in %d session%s" % (fmt_minutes(r["minutes"]), r["sessions"], "" if r["sessions"] == 1 else "s"))
    if r["answers"]:
        bits.append("%d answers %s (%d new, %d reviews)" % (r["answers"], pct(r["ok"] / float(r["answers"])), r["new"],
                                                             r["reviews"]))
    if r["taught"]:
        bits.append("taught %s" % _short(r["taught"]))
    if r["consolidated"]:
        bits.append("consolidated %s" % _short(r["consolidated"], 3))
    if r["lectures"]:
        bits.append("%d lecture%s%s" % (r["lectures"], "" if r["lectures"] == 1 else "s",
                                        (" (%s)" % fmt_minutes(r["lecture_min"])) if r["lecture_min"] else ""))
    if r["practice"]:
        bits.append("practice %d (%d solved)" % (r["practice"], r["practice_ok"]))
    for m in r["mocks"]:
        bits.append("mock %s" % m)
    for p in r["passes"]:
        bits.append(p + " done")
    if r["workout"]:
        bits.append("workout %d min" % r["workout"])
    if r["feedback"]:
        bits.append("feedback %d" % r["feedback"])
    return " · ".join(bits) or "nothing recorded"


def day_lines(repo: Repo, tree, state, day: date) -> list:
    """`day <date>`: what was recorded that day, under its shape."""
    r = records(repo, tree, state).get(day.isoformat())
    if r is None or not _active(r):
        return []
    return ["recorded: " + line(r)]


# ---------------------------------------------------------------- periods


def _period(day: str, by: str) -> str:
    if by == "day":
        return day
    if by == "month":
        return day[:7]
    d = date.fromisoformat(day)
    return (d - timedelta(days=d.weekday())).isoformat()


def totals(rs) -> dict:
    t = _blank("")
    t["days"] = 0
    for r in rs:
        if not _active(r):
            continue
        t["days"] += 1
        for k in ("minutes", "answers", "ok", "new", "reviews", "lectures", "lecture_min", "practice", "practice_ok",
                  "workout", "feedback", "sessions"):
            t[k] += r[k]
        for k in ("taught", "consolidated", "mocks", "passes"):
            t[k] += [x for x in r[k] if x not in t[k]]
    return t


def history(repo: Repo, tree, state, start: date | None, end: date | None, by: str = "week",
            skill: str | None = None, track: str | None = None) -> str:
    if by not in ("day", "week", "month"):
        raise CalError("--by day, week or month")
    if skill and skill not in tree.nodes:
        raise CalError("no skill %s in the tree" % skill)
    rs = records(repo, tree, state, skill, track)
    days = sorted(k for k in rs if (start is None or k >= start.isoformat()) and (end is None or k <= end.isoformat()))
    groups = {}
    for k in days:
        groups.setdefault(_period(k, by), []).append(rs[k])
    narrowed = bool(skill or track)
    rows = []
    for period in sorted(groups):
        t = totals(groups[period])
        if not t["days"]:
            continue
        acc = pct(t["ok"] / float(t["answers"])) if t["answers"] else "-"
        row = [period, t["days"]] + ([] if narrowed else [fmt_minutes(t["minutes"]) if t["minutes"] else "-"])
        row += [t["answers"] or "-", acc, t["new"] or "-", t["reviews"] or "-", len(t["taught"]) or "-",
                len(t["consolidated"]) or "-"]
        if not narrowed:
            row += [t["lectures"] or "-", t["practice"] or "-", t["workout"] or "-"]
        rows.append(row)
    scope = (" for %s" % (skill or "the %s track" % track)) if narrowed else ""
    span = "%s to %s" % (start.isoformat() if start else "the start", end.isoformat() if end else "now")
    if not rows:
        return "nothing recorded%s from %s" % (scope, span)
    head = ["day" if by == "day" else "week of" if by == "week" else "month", "days"]
    head += [] if narrowed else ["active"]
    head += ["answers", "right", "new", "reviews", "taught", "secured"]
    head += [] if narrowed else ["lectures", "practice", "workout"]
    out = ["History%s, %s, by %s" % (scope, span, by), table(rows, head)]
    if narrowed:
        out.append("(time, lectures, practice and workouts are not split by skill)")
    return "\n".join(out)


# ---------------------------------------------------------------- the journal files


def render_month(month: str, rs: list, tree) -> str:
    t = totals(rs)
    lines = ["# Journal %s" % month, "",
             "_Rebuilt from the event log by the engine (`rebuild`). Do not edit: it is overwritten._", "",
             "## Month", ""]
    lines.append("- %d active day%s · %s active · %d session%s" % (
        t["days"], "" if t["days"] == 1 else "s", fmt_minutes(t["minutes"]), t["sessions"], "" if t["sessions"] == 1 else "s"))
    if t["answers"]:
        lines.append("- %d answers, %s right · %d new topics answered · %d reviews" % (
            t["answers"], pct(t["ok"] / float(t["answers"])), t["new"], t["reviews"]))
    if t["taught"] or t["consolidated"]:
        lines.append("- %d topic%s taught · %d secured (consolidated)" % (
            len(t["taught"]), "" if len(t["taught"]) == 1 else "s", len(t["consolidated"])))
    by_skill = {}
    for k in t["taught"] + t["consolidated"]:
        by_skill[k.split("/", 1)[0]] = by_skill.get(k.split("/", 1)[0], 0) + 1
    if by_skill:
        top = sorted(by_skill.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        lines.append("- skills worked on: %s" % ", ".join(
            "%s (%d)" % ((tree.nodes[s].title if s in tree.nodes else s), n) for s, n in top))
    if t["lectures"]:
        lines.append("- %d lectures logged%s" % (t["lectures"], (" (%s stated)" % fmt_minutes(t["lecture_min"]))
                                                   if t["lecture_min"] else ""))
    if t["practice"]:
        lines.append("- %d practice questions, %d solved" % (t["practice"], t["practice_ok"]))
    if t["mocks"]:
        lines.append("- mocks: %s" % ", ".join(t["mocks"]))
    if t["passes"]:
        lines.append("- revision passes done: %s" % ", ".join(t["passes"]))
    if t["workout"]:
        lines.append("- workouts: %d min" % t["workout"])
    lines += ["", "## Days", ""]
    for r in sorted(rs, key=lambda r: r["day"]):
        if _active(r):
            d = date.fromisoformat(r["day"])
            lines.append("- %s %s · %s" % (r["day"], WEEKDAYS[d.weekday()], line(r)))
    return "\n".join(lines) + "\n"


def write_all(repo: Repo, tree, state) -> list:
    """Write learner/journal/<YYYY-MM>.md for every month with activity; leave unchanged files alone and
    remove a month file that no longer has any (events moved by a rename, a void). Returns the paths written."""
    rs = records(repo, tree, state)
    months = {}
    for k, r in rs.items():
        if _active(r):
            months.setdefault(k[:7], []).append(r)
    folder = journal_dir(repo)
    written = []
    for month, group in sorted(months.items()):
        path = os.path.join(folder, "%s.md" % month)
        text = render_month(month, group, tree)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                if fh.read() == text:
                    continue
        except OSError:
            pass
        write_text(path, text)
        written.append(path)
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            if re.match(r"^\d{4}-\d{2}\.md$", name) and name[:7] not in months:
                os.remove(os.path.join(folder, name))
    return written
