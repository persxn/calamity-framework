"""The career layer: opportunity records found on the web, readiness computed from the record, nudges and a portfolio.

A record says what was found, where, when it was fetched and what the site's terms allowed. Nothing is
recommended from memory: a record without a source URL, a fetch date and a terms note is refused. The
opportunity-scout writes them (`career add --file`); the gate-strategist reads the gate-mock ones for the mock
calendar. A record may name the tree skills it needs (`must`, `nice`), and then readiness is computed:

    cov(skill) = 1.0 when the skill is mastered or known, or its boss is passed; otherwise the mean over its
                 topics of 1.0 mastered · 0.7 solid · 0.4 consolidating or learning · 0 otherwise
    readiness  = 0.75 * mean(cov(must)) + 0.25 * mean(cov(nice))   (one list alone takes the whole weight)
                 capped at 0.6 while no must-skill has project evidence: a passed project or capstone boss, or a
                 hands-on item (task, code or a drill) answered right on one of its topics
    verdict    = apply now (>= 0.8, deadline open, no blackout) · hold (>= 0.8 in a blackout) ·
                 prepare (0.5-0.8: the gaps, with hours estimated from the tree) · later (< 0.5) · closed

Blackout: no nudges while `career.blackout_until` (a date in the profile) has not passed, nor in GATE's final
phase (the last `gate.final_phase_days` days before the paper). `career nudge` lists what is worth acting on
(a deadline within 14 days at readiness >= 0.7, readiness >= 0.8 on a saved record, a boss passed on a
must-skill in the last 14 days); the task queue shows one `career` line at most once a week.

`career portfolio` writes learner/career/portfolio.md, a view derived from the log: only what has evidence
(bosses passed with their evidence, mastered and known skills, hands-on items passed, Codeforces and mocks).

Events: career_add (one record, `rec` its id; a record with the same kind and url replaces the earlier one and
keeps its status) · career_status (rec, status, note).
"""
from __future__ import annotations

import hashlib
import os
from datetime import date, timedelta

from .store import Repo, write_text
from .util import CalError, csv_list, table

KINDS = ("gate-mock", "test-series", "job", "internship", "oss-program", "hackathon", "mtech-admission", "psu",
         "scholarship")
MODES = ("online", "offline", "both", "remote", "onsite", "hybrid")
PLACED = ("offline", "both", "onsite", "hybrid")         # a mode that happens somewhere names its city
VIA = ("greenhouse-api", "lever-api", "ashby-api", "hn-api", "official-page", "search", "paste")
FIELDS = ("kind", "title", "provider", "url", "source", "fetched", "terms", "via", "mode", "city", "dates",
          "posted", "deadline", "summary", "must", "nice", "cost", "note")
REQUIRED = ("kind", "title", "url", "source", "fetched", "terms")
STATUSES = ("found", "saved", "applied", "interviewing", "offer", "accepted", "rejected", "withdrawn")
OPEN_STATUSES = ("found", "saved")                       # not acted on yet: the only ones nudged
STALE_DAYS = 30
NUDGE_DAYS = 14
TOPIC_COV = {"mastered": 1.0, "solid": 0.7, "consolidating": 0.4, "learning": 0.4}
HANDS_ON = ("task", "code", "debug", "debug-docs", "audit", "chaos")


def record_id(kind: str, url: str) -> str:
    return "op-" + hashlib.sha1(("%s|%s" % (kind, url)).encode("utf-8")).hexdigest()[:8]


def _iso(row, key: str, what: str):
    try:
        return date.fromisoformat(str(row[key]))
    except ValueError:
        raise CalError("%s is %s, such as 2026-10-28; got %r" % (key, what, row[key]))


def _skills(tree, row, key: str) -> list:
    value = row.get(key)
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        value = [v for v in value.replace(",", " ").split() if v]
    if not isinstance(value, list):
        raise CalError("%s is a list of skill ids from the tree" % key)
    out = []
    for ident in value:
        try:
            node = tree.get(str(ident).strip())
        except CalError as exc:
            raise CalError("%s: %s A skill the tree lacks is left out and named in the note (the tree skill can "
                           "add it)." % (key, exc))
        if node.id not in out:
            out.append(node.id)
    return out


def check(tree, row, when) -> dict:
    if not isinstance(row, dict):
        raise CalError("each record is a JSON object")
    extra = set(row) - set(FIELDS)
    if extra:
        raise CalError("unknown field(s) %s; a record holds %s" % (", ".join(sorted(extra)), ", ".join(FIELDS)))
    missing = [k for k in REQUIRED if not str(row.get(k) or "").strip()]
    if missing:
        raise CalError("%r lacks %s: every record names its source, the day it was fetched and what the site's "
                       "terms allowed" % (row.get("title") or "a record", ", ".join(missing)))
    if row["kind"] not in KINDS:
        raise CalError("kind is one of %s" % ", ".join(KINDS))
    for key in ("url", "source"):
        if not str(row[key]).startswith(("https://", "http://")):
            raise CalError("%s must be a web address (https://...), got %r" % (key, row[key]))
    fetched = _iso(row, "fetched", "the day it was read")
    if fetched > when.date():
        raise CalError("fetched %s is in the future" % fetched)
    mode = row.get("mode")
    if mode is not None and mode not in MODES:
        raise CalError("mode is one of %s" % ", ".join(MODES))
    if mode in PLACED and not str(row.get("city") or "").strip():
        raise CalError("an offline mock or an on-site role names its city")
    via = row.get("via")
    if via is not None and via not in VIA:
        raise CalError("via is one of %s" % ", ".join(VIA))
    must, nice = _skills(tree, row, "must"), _skills(tree, row, "nice")
    if set(must) & set(nice):
        raise CalError("a skill is either must or nice, not both: %s" % ", ".join(sorted(set(must) & set(nice))))
    out = {k: (str(row[k]).strip() if not isinstance(row[k], (int, float)) else row[k]) for k in FIELDS
           if row.get(k) not in (None, "", []) and k not in ("must", "nice")}
    out["fetched"] = fetched.isoformat()
    for key in ("posted", "deadline"):
        if key in out:
            out[key] = _iso(row, key, "a date").isoformat()
    if "posted" in out and out["posted"] > out["fetched"]:
        raise CalError("posted %s is after the day it was fetched" % out["posted"])
    if must:
        out["must"] = must
    if nice:
        out["nice"] = nice
    for k in ("title", "note", "terms"):
        if len(str(out.get(k, ""))) > 300:
            raise CalError("%s is a line, not a page (300 characters at most)" % k)
    summary = str(out.get("summary", ""))
    if len(summary) > 400 or summary.count("\n") > 2:
        raise CalError("summary is three lines at most, in our own words (400 characters), never the posting copied")
    return out


def add(repo: Repo, tree, rows, when) -> str:
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or not rows:
        raise CalError("career add takes a JSON list of records")
    clean = [check(tree, r, when) for r in rows]          # all or none
    for rec in clean:
        # `rec`, not `id`: an event's id is its own, and a payload `id` would replace it and drop a newer fetch
        repo.append("career_add", rec=record_id(rec["kind"], rec["url"]), **rec)
    return "recorded %d record(s): %s" % (len(clean), ", ".join(record_id(r["kind"], r["url"]) for r in clean))


def _get(state, ident: str) -> dict:
    r = state.career.get(ident)
    if r is None:
        raise CalError("unknown record %s (career list)" % ident)
    return r


def list_text(state, when, kind: str | None = None) -> str:
    rows = [r for r in state.career.values() if not kind or r["kind"] == kind]
    if not rows:
        return "No records%s yet. The opportunity-scout agent finds them (gate skill: \"find mocks\")." % (
            (" of kind %s" % kind) if kind else "")
    out = []
    for r in sorted(rows, key=lambda r: (r["kind"], r.get("mode") or "", r["title"])):
        age = (when.date() - date.fromisoformat(r["fetched"])).days
        out.append([r["id"], r["kind"], r["title"][:40], r.get("provider", "")[:24], r.get("mode", "-"),
                    r.get("city", "-"), (r.get("deadline") or r.get("dates", "-"))[:24],
                    r["fetched"] + (" (stale)" if age > STALE_DAYS else "")])
    return table(out, ["id", "kind", "title", "provider", "mode", "city", "dates", "fetched"]) + \
        "\nEach record carries its source and terms note (career show <id>). Older than %d days: check again." \
        % STALE_DAYS


def show_text(state, ident: str) -> str:
    r = _get(state, ident)
    lines = []
    for k in ("id",) + FIELDS + ("status", "status_on", "status_note"):
        if k in r:
            lines.append("%s: %s" % (k, ", ".join(r[k]) if isinstance(r[k], list) else r[k]))
    return "\n".join(lines)


# ---------------------------------------------------------------- readiness


def _today(repo, when) -> date:
    from . import day as day_mod

    return day_mod.learner_date(repo, when)


def blackout(repo: Repo, when):
    """(until: date, why) while career nudges are held back, else None."""
    from . import gateinfo

    today = _today(repo, when)
    found = []
    own = repo.prof("career.blackout_until")
    if own:
        try:
            until = date.fromisoformat(str(own)[:10])
        except ValueError:
            until = None
        if until and today <= until:
            found.append((until, "career.blackout_until"))
    gate = any(str(t).startswith("gate") for t in csv_list(repo.prof("tracks"))) or repo.prof("gate.year")
    dates = [d for d in (gateinfo.exam_date(repo, p) for p in gateinfo.papers(repo) or [None]) if d] if gate else []
    exam = min(dates) if dates else None
    if exam is not None:
        final = int(repo.cfg("gate.final_phase_days", 21))
        if 0 <= (exam - today).days <= final:
            found.append((exam, "GATE's final phase"))
    return max(found) if found else None


def skill_cov(tree, state, skill_id: str) -> float:
    """How much of a skill the record proves, 0..1 (the module docstring has the rule)."""
    sk = state.skills.get(skill_id)
    if (sk is not None and sk.boss_ok) or state.skill_status(skill_id) in ("mastered", "known"):
        return 1.0
    node = tree.nodes.get(skill_id)
    topics = list(node.topics) if node is not None else []
    if not topics:
        return 0.0
    return sum(TOPIC_COV.get(state.topic_status("%s/%s" % (skill_id, t.id)), 0.0) for t in topics) / len(topics)


def project_evidence(state, skill_id: str) -> list:
    """What shows the skill was used in a build: passed project or capstone bosses, hands-on items answered right."""
    out = ["%s boss passed %s" % (b["kind"], b["ts"].date().isoformat()) for b in state.bosses
           if b["skill"] == skill_id and b["kind"] in ("project", "capstone")]
    prefix = skill_id + "/"
    for it in state.items.values():
        if it.type in HANDS_ON and it.n_ok > 0 and (it.skill == skill_id or any(t.startswith(prefix) for t in it.topics)):
            out.append("%s %s passed" % (it.type, it.id))
    return out


def readiness(tree, state, rec: dict) -> dict | None:
    """{score, must, nice, capped, gaps: [(skill, cov, hours)]} for a record that names skills, else None."""
    must, nice = rec.get("must") or [], rec.get("nice") or []
    if not must and not nice:
        return None
    covs = {s: skill_cov(tree, state, s) for s in must + nice if s in tree.nodes}
    mean = lambda ids: sum(covs.get(s, 0.0) for s in ids) / len(ids)   # noqa: E731
    if must and nice:
        score = 0.75 * mean(must) + 0.25 * mean(nice)
    else:
        score = mean(must or nice)
    capped = bool(must) and score > 0.6 and not any(project_evidence(state, s) for s in must)
    if capped:
        score = 0.6
    gaps = []
    for s in must + nice:
        cov = covs.get(s, 0.0)
        if cov < 1.0:
            node = tree.nodes.get(s)
            hours = (node.est_hours or 0) * (1.0 - cov) if node is not None else 0
            gaps.append((s, cov, hours))
    return {"score": round(score, 4), "covs": covs, "capped": capped, "gaps": gaps}


def verdict(repo, rec: dict, ready: dict | None, when) -> str:
    today = _today(repo, when)
    if rec.get("status", "found") not in OPEN_STATUSES:
        return rec["status"]
    if rec.get("deadline") and date.fromisoformat(rec["deadline"]) < today:
        return "closed"
    if ready is None:
        return "-"
    score = ready["score"]
    if score >= 0.8:
        held = blackout(repo, when)
        return ("hold until %s" % held[0].isoformat()) if held else "apply now"
    return "prepare" if score >= 0.5 else "later"


def _matched(state, kind=None) -> list:
    return [r for r in state.career.values() if (r.get("must") or r.get("nice")) and (not kind or r["kind"] == kind)]


def match_text(repo, tree, state, when, ident: str | None = None, kind: str | None = None) -> str:
    rows = [_get(state, ident)] if ident else _matched(state, kind)
    if not rows:
        return "No record names the skills it needs yet (must, nice), so there is nothing to match."
    lines = []
    for r in sorted(rows, key=lambda r: -(readiness(tree, state, r) or {"score": 0})["score"]):
        ready = readiness(tree, state, r)
        if ready is None:
            lines.append("%s | %s: names no skills (must, nice), so readiness is not computed" % (r["id"], r["title"]))
            continue
        lines.append("%s | %s (%s%s)" % (r["id"], r["title"], r["kind"],
                                          (", deadline %s" % r["deadline"]) if r.get("deadline") else ""))
        lines.append("  readiness %.2f -> %s%s" % (ready["score"], verdict(repo, r, ready, when),
                                                   " (capped at 0.6: no project evidence on a must-skill yet)"
                                                   if ready["capped"] else ""))
        for key in ("must", "nice"):
            if r.get(key):
                lines.append("  %s: %s" % (key, ", ".join("%s %.1f" % (s, ready["covs"].get(s, 0.0)) for s in r[key])))
        if ready["gaps"]:
            hours = sum(h for _, _, h in ready["gaps"])
            lines.append("  gaps: %s%s" % (", ".join(s for s, _, _ in ready["gaps"]),
                                           (" · about %dh to close (est. from the tree)" % round(hours)) if hours else ""))
    held = blackout(repo, when)
    if held:
        lines.append("Blackout until %s (%s): no nudges, and apply-now waits." % (held[0].isoformat(), held[1]))
    lines.append("Readiness counts only the record (career show <id> for the posting); it is no promise of an offer.")
    return "\n".join(lines)


def status_text(repo, tree, state, when) -> str:
    rows = list(state.career.values())
    if not rows:
        return "No career records yet. The opportunity-scout finds them; career add --file records them."
    out = []
    rank = {s: i for i, s in enumerate(STATUSES)}
    for r in sorted(rows, key=lambda r: (rank.get(r.get("status", "found"), len(STATUSES)), r["kind"], r["title"])):
        ready = readiness(tree, state, r)
        out.append([r["id"], r["kind"], r["title"][:36], r.get("status", "found"), r.get("deadline", "-"),
                    "%.2f" % ready["score"] if ready else "-", verdict(repo, r, ready, when)])
    lines = [table(out, ["id", "kind", "title", "status", "deadline", "ready", "verdict"])]
    held = blackout(repo, when)
    lines.append("Blackout until %s (%s)." % (held[0].isoformat(), held[1]) if held else "No blackout.")
    lines.append("career status <id> %s [--note ...] records a step." % "|".join(STATUSES))
    return "\n".join(lines)


def set_status(repo, state, when, ident: str, status: str, note: str | None = None) -> str:
    r = _get(state, ident)
    if status not in STATUSES:
        raise CalError("status is one of %s" % ", ".join(STATUSES))
    if note and len(note) > 300:
        raise CalError("note is a line, not a page (300 characters at most)")
    repo.append("career_status", when=when, rec=ident, status=status, note=(note or "").strip() or None)
    return "%s | %s: %s -> %s" % (ident, r["title"], r.get("status", "found"), status)


# ---------------------------------------------------------------- nudges


def nudges(repo, tree, state, when) -> list:
    """[(kind, record id, line)] worth acting on now, most urgent first; empty during a blackout."""
    if blackout(repo, when):
        return []
    today = _today(repo, when)
    recent = today - timedelta(days=NUDGE_DAYS)
    out = []
    for r in state.career.values():
        if r.get("status", "found") not in OPEN_STATUSES:
            continue
        deadline = date.fromisoformat(r["deadline"]) if r.get("deadline") else None
        if deadline and deadline < today:
            continue
        ready = readiness(tree, state, r)
        if ready is None:
            continue
        score = ready["score"]
        if deadline and (deadline - today).days <= NUDGE_DAYS and score >= 0.7:
            out.append((0, (deadline - today).days, "deadline", r["id"], "%s closes %s (in %d days) at readiness %.2f" % (
                r["title"], r["deadline"], (deadline - today).days, score)))
        elif r.get("status") == "saved" and score >= 0.8:
            out.append((1, -score, "ready", r["id"], "%s: readiness %.2f, ready to apply" % (r["title"], score)))
        else:
            fresh = [b["skill"] for b in state.bosses
                     if b["skill"] in (r.get("must") or []) and b["ts"].date() >= recent]
            if fresh:
                out.append((2, -score, "boss", r["id"], "%s: boss passed on %s, readiness now %.2f" % (
                    r["title"], ", ".join(sorted(set(fresh))), score)))
    return [(kind, rid, line) for _, _, kind, rid, line in sorted(out)]


def nudge_text(repo, tree, state, when) -> str:
    held = blackout(repo, when)
    if held:
        return "Blackout until %s (%s): no career nudges until then." % (held[0].isoformat(), held[1])
    rows = nudges(repo, tree, state, when)
    if not rows:
        return "Nothing to act on: no deadline near at readiness 0.7, no saved record at 0.8, no fresh boss on a must-skill."
    lines = ["Worth acting on (career match <id> for the gaps):"]
    lines += ["  %s %-8s %s" % (rid, kind, line) for kind, rid, line in rows]
    lines.append("tasks done career after acting: the task line then stays away for a week.")
    return "\n".join(lines)


# ---------------------------------------------------------------- portfolio


def portfolio(repo, tree, state) -> str:
    """learner/career/portfolio.md: only what the log proves, each line with its evidence. Depends only on the log,
    the tree and the cached Codeforces data, never on the clock."""
    name = repo.prof_text("name", "the learner")
    lines = ["# Portfolio: %s" % name, "",
             "Derived from the event log by `career portfolio`; it is rewritten each time, so edit nothing here.",
             "Every line names its evidence. What is not in the log is not here.", ""]
    bosses = sorted(state.bosses, key=lambda b: b["ts"])
    if bosses:
        lines += ["## Bosses passed", ""]
        for b in bosses:
            node = tree.nodes.get(b["skill"])
            lines.append("- **%s** (%s, %s): %s" % (node.title if node else b["skill"], b["kind"],
                                                   b["ts"].date().isoformat(), b["evidence"]))
        lines.append("")
    proven = []
    for skill_id in sorted(state.skills):
        status = state.skill_status(skill_id)
        node = tree.nodes.get(skill_id)
        if node is None or status not in ("mastered", "known"):
            continue
        how = "every topic mastered" if status == "mastered" else "placed out by a placement test"
        proven.append("- **%s** (`%s`): %s" % (node.title, skill_id, how))
    if proven:
        lines += ["## Skills proven", ""] + proven + [""]
    hands = {}
    for it in state.items.values():
        if it.type in HANDS_ON and it.n_ok > 0:
            skills = sorted({t.split("/", 1)[0] for t in it.topics} or {it.skill})
            hands.setdefault(" + ".join(s for s in skills if s), []).append((it.last_ts, it.type, it.id))
    if hands:
        lines += ["## Hands-on work passed", ""]
        for skills, rows in sorted(hands.items()):
            rows.sort(key=lambda r: (r[0].isoformat() if r[0] else "", r[2]))
            last = rows[-1][0].date().isoformat() if rows[-1][0] else "-"
            lines.append("- %s: %d passed (%s), latest %s" % (skills, len(rows), ", ".join(
                "%s %s" % (t, i) for _, t, i in rows[:6]) + (" ..." if len(rows) > 6 else ""), last))
        lines.append("")
    from . import cf

    data = cf.load(repo)
    if data is not None:
        seen = cf.problems_seen(data)
        lines += ["## Competitive programming", "",
                  "- Codeforces %s: rating %s (max %s), %d problems solved, %d rated contests (synced %s)" % (
                      data["handle"], cf.current_rating(data) or "unrated", data["info"].get("maxRating", "-"),
                      sum(1 for p in seen.values() if p["ac"]), len(data["rating"]), str(data["fetched"])[:10]), ""]
    if state.mocks:
        lines += ["## GATE mocks", ""]
        for m in sorted(state.mocks, key=lambda m: str(m.get("date") or m.get("ts"))):
            lines.append("- %s %s: %s of %s (%s)" % (str(m.get("date") or m.get("ts"))[:10], m.get("paper", "mock"),
                                                    _num(m.get("score")), _num(m.get("max")), m.get("source", "-")))
        lines.append("")
    if len(lines) == 5:
        lines += ["Nothing evidenced yet: a boss passed, a skill mastered or hands-on work will appear here.", ""]
    return "\n".join(lines)


def _num(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    return ("%d" % f) if f.is_integer() else ("%.2f" % f)


def write_portfolio(repo, tree, state) -> str:
    path = os.path.join(repo.learner, "career", "portfolio.md")
    write_text(path, portfolio(repo, tree, state))
    return path
