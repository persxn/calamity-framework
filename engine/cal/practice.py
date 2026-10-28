"""Practice sets: outside material (a previous-paper book, a PDF of questions, a CSES section) tracked as
metadata only. The engine stores which questions there are, which topics and pages they belong to and how
each attempt went; never a question's text.

Every question comes back. A wrong, guessed or skipped one is revisited after 2 days, then 7, then 21; one
solved the first time after 10 days, then 30. A question retires after two right revisits in a row (a guessed
revisit moves it along without counting). A set whose key is official (previous GATE papers) credits the
mapped topics as verified evidence, as `cf credit` does for Codeforces; any other set schedules the topics
but is not evidence, like an oral `quick` check.

Events: practice_set (add or change a set), practice_map (question ranges -> topics, type, pages),
practice_attempt (one logged result for some questions). learner/practice/<set>.md is a view the engine
writes from them.
"""
from __future__ import annotations

import os
import re
from datetime import timedelta

from . import fsrs
from .store import Repo, write_text
from .util import SKILL_ID_RE, CalError, csv_list, fmt_delta, table

KINDS = ("pyq", "book", "sheet", "course", "other")
KEYS = ("official", "unofficial", "none")
RESULTS = ("solved", "wrong", "guessed", "skipped")
TYPES = ("mcq", "msq", "nat", "short", "code", "proof", "other")
WRONG_LADDER = (2, 7, 21)       # days to the next revisit of a question that went wrong, guessed or skipped
RIGHT_LADDER = (10, 30)         # ... of one solved at the first attempt
RETIRE_STREAK = 2


def parse_questions(text, n_items: int) -> list:
    """'1-10,12,15-18' -> [1..10, 12, 15..18], each within 1..n_items. Raises CalError."""
    out = []
    for part in csv_list(str(text).replace(" ", ",")):
        m = re.match(r"^(\d+)(?:-(\d+))?$", part)
        if not m:
            raise CalError("questions are numbers and ranges such as 1-10,12,15-18; got %r" % part)
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if lo < 1 or hi < lo or hi > n_items:
            raise CalError("question %s is outside this set (1-%d)" % (part, n_items))
        out.extend(q for q in range(lo, hi + 1) if q not in out)
    if not out:
        raise CalError("say which questions: 1-10, 12, ...")
    return out


def fold(rec: dict, result: str, dt) -> None:
    """Apply one attempt to a question's record (the revisit policy)."""
    rec["n"] = rec.get("n", 0) + 1
    rec["last"], rec["result"] = dt, result
    first = rec.get("first") is None
    if first:
        rec["first"] = result
        rec["ladder"] = "right" if result == "solved" else "wrong"
        rec["pos"], rec["streak"] = 0, 0
    else:
        if result == "solved":
            rec["streak"] += 1
        else:
            rec["streak"] = 0
            if result != "guessed":
                rec["ladder"], rec["pos"] = "wrong", -1      # back to the start of the short ladder
        rec["pos"] += 1
    if not first and rec["streak"] >= RETIRE_STREAK:
        rec["retired"], rec["due"] = True, None
        return
    rec["retired"] = False
    ladder = RIGHT_LADDER if rec["ladder"] == "right" else WRONG_LADDER
    rec["due"] = dt + timedelta(days=ladder[min(rec["pos"], len(ladder) - 1)])


def topics_for(pset: dict, q: int) -> dict:
    """The mapping for one question: {topics, type, pages} (the latest range that covers it wins)."""
    found = {"topics": [], "type": None, "pages": ""}
    for r in pset["map"]:
        if r["from"] <= q <= r["to"]:
            found = {"topics": list(r.get("topics") or []), "type": r.get("type"), "pages": r.get("pages") or ""}
    return found


# ---------------------------------------------------------------- commands


def _get(state, ident: str) -> dict:
    pset = state.practice.get(ident)
    if pset is None:
        have = ", ".join(sorted(state.practice)) or "none yet"
        raise CalError("unknown practice set %r (sets: %s); add it with practice add" % (ident, have))
    return pset


def add(repo: Repo, state, ident: str, title: str | None, kind: str, items, key: str, source: str | None) -> str:
    if not SKILL_ID_RE.match(ident or "") or "." in ident:
        raise CalError("a set id is lower-case words joined by '-', such as os-pyq")
    old = state.practice.get(ident)
    try:
        n = int(str(items).split("-")[-1]) if items is not None else (old["meta"]["items"] if old else 0)
    except ValueError:
        raise CalError("--items is the number of questions, or a range such as 1-120")
    if n < 1:
        raise CalError("say how many questions the set has: --items 120")
    if kind not in KINDS:
        raise CalError("--kind is one of %s" % ", ".join(KINDS))
    if key not in KEYS:
        raise CalError("--key is official (an official answer key, such as previous GATE papers), unofficial or none")
    meta = {"title": title or (old["meta"]["title"] if old else ident), "kind": kind, "items": n, "key": key,
            "source": source or (old["meta"].get("source") if old else "") or ""}
    repo.append("practice_set", set=ident, title=meta["title"], kind=kind, items=n, answer_key=key,
                source=meta["source"])
    write_view(repo, ident, meta, old["map"] if old else [])
    verb = "changed" if old else "added"
    return ("practice set %s: %s (%d questions, %s key)\nmap its questions to topics: practice map %s --file "
            "<ranges.json>" % (verb, ident, n, key, ident))


def map_ranges(repo: Repo, tree, state, ident: str, rows) -> str:
    pset = _get(state, ident)
    n = pset["meta"]["items"]
    if not isinstance(rows, list) or not rows:
        raise CalError('a map is a JSON list: [{"from": 1, "to": 10, "topics": ["skill/topic"], "type": "mcq", '
                       '"pages": "41-44"}]')
    clean = []
    for r in rows:
        if not isinstance(r, dict):
            raise CalError("each map entry is an object with from, to and topics")
        try:
            lo, hi = int(r["from"]), int(r.get("to", r["from"]))
        except (KeyError, TypeError, ValueError):
            raise CalError("each map entry needs from (and to) question numbers")
        if lo < 1 or hi < lo or hi > n:
            raise CalError("range %s-%s is outside this set (1-%d)" % (lo, hi, n))
        topics = [tree.topic(k).key for k in csv_list(r.get("topics"))]
        kind = r.get("type")
        if kind is not None and kind not in TYPES:
            raise CalError("type is one of %s" % ", ".join(TYPES))
        pages = str(r.get("pages") or "")
        if len(pages) > 40:
            raise CalError("pages is a page reference such as 41-44, not text")
        extra = set(r) - {"from", "to", "topics", "type", "pages"}
        if extra:
            raise CalError("a map entry holds only from, to, topics, type and pages (no question text): %s"
                           % ", ".join(sorted(extra)))
        clean.append({"from": lo, "to": hi, "topics": topics, "type": kind, "pages": pages})
    repo.append("practice_map", set=ident, ranges=clean)
    write_view(repo, ident, pset["meta"], pset["map"] + clean)
    mapped = sum(r["to"] - r["from"] + 1 for r in clean)
    return "mapped %d question(s) of %s in %d range(s)" % (mapped, ident, len(clean))


def log(repo: Repo, tree, state, when, ident: str, questions, result: str, err: str | None = None,
        secs=None, note: str | None = None) -> str:
    from . import session

    pset = _get(state, ident)
    if result not in RESULTS:
        raise CalError("the result is one of %s" % ", ".join(RESULTS))
    if err and err not in session.ERROR_TAGS:
        raise CalError("--err must be one of: %s" % ", ".join(session.ERROR_TAGS))
    if note and len(note) > 200:
        raise CalError("a note is one line about the mistake (at most 200 characters), never the question")
    qs = parse_questions(questions, pset["meta"]["items"])
    repo.append("practice_attempt", when=when, set=ident, qs=qs, result=result, err=err if result != "solved" else None,
                secs=secs, note=note)
    # The topics: one attempt per topic for this logged batch. Official keys are evidence; others schedule only.
    lines = ["logged %s %s: %s" % (ident, _ranges(qs), result)]
    if result != "skipped":
        by_topic = {}
        for q in qs:
            for k in topics_for(pset, q)["topics"]:
                if tree.has_topic(k):
                    by_topic.setdefault(k, []).append(q)
        official = pset["meta"]["key"] == "official"
        ok = result == "solved"
        for key, qq in by_topic.items():
            grade = fsrs.GOOD if ok else (fsrs.HARD if result == "guessed" else fsrs.AGAIN)
            good = ok or result == "guessed"
            session._record(repo, tree, state, when, key, [key], good, grade, 0, None,
                            practice="%s:%s" % (ident, _ranges(qq)), verified=official or None,
                            quick=None if official else True, err=(err or "unclassified") if not good else None,
                            note=note if not good else None, kind="practice")
        if by_topic:
            lines.append("%s: %s" % ("evidence for" if official else "scheduled (not evidence: the key is not "
                                     "official)", ", ".join(sorted(by_topic))))
        else:
            lines.append("these questions are not mapped to topics yet (practice map), so no topic is credited")
    return "\n".join(lines)


def due(state, when, ident: str | None = None) -> list:
    """[(set id, [(question, pages), ...])] of revisits due by `when`, soonest set first."""
    out = []
    for sid, pset in sorted(state.practice.items()):
        if ident and sid != ident:
            continue
        qs = sorted(q for q, rec in pset["qs"].items() if rec.get("due") is not None and rec["due"] <= when)
        if qs:
            out.append((sid, [(q, topics_for(pset, q)["pages"]) for q in qs]))
    return out


def due_text(state, when) -> str:
    rows = due(state, when)
    if not rows:
        nxt = [rec["due"] for p in state.practice.values() for rec in p["qs"].values() if rec.get("due")]
        return "No practice question is due." + (" Next revisit %s." % fmt_delta(min(nxt) - when) if nxt else "")
    lines = []
    for sid, qs in rows:
        title = state.practice[sid]["meta"]["title"]
        pages = sorted({p for _, p in qs if p})
        lines.append("redo %s from %s%s" % (", ".join("Q%d" % q for q, _ in qs[:15]) + (" ..." if len(qs) > 15 else ""),
                                            title, " (pp. %s)" % ", ".join(pages) if pages else ""))
        lines.append("  then: practice log %s <questions> solved|wrong|guessed|skipped" % sid)
    return "\n".join(lines)


def status_text(state, when, ident: str | None = None) -> str:
    if not state.practice:
        return "No practice sets yet: practice add <id> --title \"...\" --items N --key official|unofficial|none"
    rows = []
    for sid, pset in sorted(state.practice.items()):
        if ident and sid != ident:
            continue
        n = pset["meta"]["items"]
        recs = pset["qs"].values()
        tried = [r for r in recs if r.get("first") and r["first"] != "skipped"]
        first_ok = sum(1 for r in tried if r["first"] == "solved")
        skipped = sum(1 for r in recs if r.get("result") == "skipped")
        retired = sum(1 for r in recs if r.get("retired"))
        due_now = sum(1 for r in recs if r.get("due") is not None and r["due"] <= when)
        mapped = len({q for r in pset["map"] for q in range(r["from"], r["to"] + 1)})
        passes = max([r["n"] for r in recs] or [0])
        rows.append([sid, pset["meta"]["key"], "%d/%d" % (len(pset["qs"]), n),
                     ("%d%%" % round(100.0 * first_ok / len(tried))) if tried else "-", str(skipped), str(retired),
                     str(due_now), "%d/%d" % (mapped, n), str(passes)])
    if not rows:
        raise CalError("unknown practice set %r" % ident)
    return table(rows, ["set", "key", "attempted", "first-try", "skipped", "retired", "due", "mapped", "most passes"]) \
        + "\n'first-try' = solved at the first attempt, of those attempted; a question retires after %d right " \
          "revisits in a row." % RETIRE_STREAK


def stats_text(tree, state) -> str:
    """Per topic, across all sets: questions attempted and first-try accuracy."""
    per = {}
    for pset in state.practice.values():
        for q, rec in pset["qs"].items():
            if not rec.get("first") or rec["first"] == "skipped":
                continue
            for k in topics_for(pset, q)["topics"]:
                row = per.setdefault(k, [0, 0])
                row[0] += 1
                row[1] += 1 if rec["first"] == "solved" else 0
    if not per:
        return "No mapped practice question has been attempted yet."
    rows = [[k, str(n), "%d%%" % round(100.0 * ok / n)] for k, (n, ok) in sorted(per.items())]
    return table(rows, ["topic", "attempted", "first-try"])


def _ranges(qs) -> str:
    qs = sorted(qs)
    out, start, prev = [], None, None
    for q in qs + [None]:
        if start is None:
            start = prev = q
        elif q is not None and q == prev + 1:
            prev = q
        else:
            out.append(str(start) if start == prev else "%d-%d" % (start, prev))
            start = prev = q
    return ",".join(out)


def write_view(repo: Repo, ident: str, meta: dict, ranges) -> None:
    """learner/practice/<set>.md: what the set is and how its questions map. Metadata only."""
    lines = ["---", "id: %s" % ident, "title: \"%s\"" % meta["title"].replace('"', "'"), "kind: %s" % meta["kind"],
             "items: %d" % meta["items"], "key: %s" % meta["key"],
             "source: \"%s\"" % (meta.get("source") or "").replace('"', "'"), "---", "",
             "Written by the engine (practice add, practice map); do not edit. Only metadata belongs here: never "
             "a question's text.", "", "# Map", ""]
    for r in ranges:
        lines.append("- Q%s%s: %s%s" % (r["from"] if r["from"] == r["to"] else "%d-%d" % (r["from"], r["to"]),
                                         (" (%s)" % r["type"]) if r.get("type") else "", ", ".join(r["topics"]) or "unmapped",
                                         (" · pp. %s" % r["pages"]) if r.get("pages") else ""))
    if not ranges:
        lines.append("(not mapped yet)")
    write_text(os.path.join(repo.root, "learner", "practice", ident + ".md"), "\n".join(lines) + "\n")


# ---------------------------------------------------------------- session types (the developer track's doctrine)

SESSION_TYPES = {
    "system-day": "a real system taken apart: what it is for, its constraints, the design and its trade-offs",
    "classic": "a classic read: a paper, an RFC or an engineering post, with at least three new ideas",
    "outage": "an outage study: the failure chain reconstructed, the decision behind each link",
    "oss": "open-source immersion: a real repository read, built, run and changed",
    "vocab": "engineering vocabulary: about five terms, each with its mental model, an example and a check",
}


def session_log(repo: Repo, tree, when, kind: str, minutes, topic, ideas, note) -> str:
    """Record one session of a developer-doctrine type. Its notes go in the topic's fragment, and its testable
    ideas to the examiner as seeds: the session itself is not evidence."""
    if kind not in SESSION_TYPES:
        raise CalError("a session type is one of %s" % ", ".join(SESSION_TYPES))
    key = tree.topic(topic).key if topic else None
    if note and (len(note) > 200 or "\n" in note):
        raise CalError("a note is one line (at most 200 characters): what it was about, never copied text")
    if ideas is not None and ideas < 0:
        raise CalError("--ideas counts new ideas: 0 or more")
    repo.append("session_type", when=when, kind=kind, minutes=minutes, topic=key, ideas=ideas, note=note)
    lines = ["%s session recorded%s%s" % (kind, (" on %s" % key) if key else "", (", %d min" % minutes) if minutes else "")]
    if kind == "classic" and (ideas or 0) < 3:
        lines.append("note: a classic read asks for at least three new ideas; name them before closing")
    if key:
        lines.append("next: save its notes fragment (notes fragment %s), then give its testable ideas to the examiner "
                     "as seeds for %s" % (key, key))
    else:
        lines.append("next: pick the closest tree topic for its notes (find <words>), or record it with --topic")
    return "\n".join(lines)


def sessions(repo: Repo, state, when, days: int = 30) -> list:
    since = when - timedelta(days=days)
    return [e for e in repo.events() if e["t"] == "session_type" and e["_dt"] >= since]


def sessions_text(repo: Repo, state, when, days: int = 30) -> str:
    rows = sessions(repo, state, when, days)
    if not rows:
        return "no developer sessions in the last %d days (practice session system-day|classic|outage|oss|vocab)" % days
    counts = {}
    for e in rows:
        c = counts.setdefault(e.get("kind"), [0, 0, 0])
        c[0] += 1
        c[1] += int(e.get("minutes") or 0)
        c[2] += int(e.get("ideas") or 0)
    out = ["developer sessions, last %d days:" % days]
    for kind in SESSION_TYPES:
        if kind in counts:
            n, mins, ideas = counts[kind]
            out.append("  %-10s %d session%s, %d min%s" % (kind, n, "" if n == 1 else "s", mins,
                                                       (", %d new ideas" % ideas) if ideas else ""))
    missing = [k for k in SESSION_TYPES if k not in counts]
    if missing:
        out.append("  not yet: %s" % ", ".join(missing))
    last = rows[-1]
    out.append("last: %s %s%s" % (state.day(last["_dt"]), last.get("kind"), (" on %s" % last["topic"]) if last.get("topic") else ""))
    return "\n".join(out)
