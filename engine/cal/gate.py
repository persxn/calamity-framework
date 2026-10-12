"""GATE companion maths: countdown, subject weights, triage, mocks and the marks board.

Weights start as clearly-labelled priors (the official pattern only fixes the
General Aptitude and Engineering Mathematics totals). They are replaced by
counts from official papers the learner imports, or by `gate weight`.
Nothing here can promise a rank; it shows marks against a target.
"""
from __future__ import annotations

import re

from . import gateinfo, items
from .store import Repo
from .util import CalError, pct, table

_REF_RE = re.compile(r"GATE\s+([A-Z]{2})\s+(\d{4})", re.I)


def learner_tracks(repo: Repo) -> list:
    tracks = ["gate-" + p.lower() for p in gateinfo.papers(repo)]
    return (["gate"] + tracks) if tracks else []


def gate_nodes(repo: Repo, tree, paper: str | None = None) -> list:
    """Live GATE subjects for the learner's papers (or one paper), shared ones included."""
    if paper:
        wanted = {"gate", "gate-" + paper.lower()}
    else:
        wanted = set(learner_tracks(repo))
    return [n for n in tree.live() if n.track in wanted and n.kind == "skill"]


def weight(state, node) -> tuple:
    """(marks, source) for a subject."""
    if node.id in state.weights:
        return state.weights[node.id]
    try:
        marks = float(node.marks)
    except (TypeError, ValueError):
        marks = 0.0
    return marks, str(node.meta.get("marks_source") or "prior")


def subject_numbers(repo: Repo, tree, state, node) -> dict:
    """Coverage and accuracy of one subject, from verified answers only."""
    total = len(node.topics)
    tested = n = ok = 0
    for topic in node.topics:
        ts = state.topics.get(topic.key)
        if ts is None or ts.card is None:
            continue
        ev = [good for _, good, evidence in ts.recent if evidence]
        if ev:
            tested += 1
            n += len(ev)
            ok += sum(1 for g in ev if g)
    counts = state.skill_counts(node.id)
    prior_n, prior_acc = 4.0, 0.3  # an untested subject is assumed weak, not unknown
    acc = (ok + prior_n * prior_acc) / (n + prior_n)
    covered = sum(1 for t in node.topics
                  if (state.topics.get(t.key) is not None and
                      (state.topics[t.key].covered_ts is not None or state.topics[t.key].card is not None)))
    return {
        "total": total, "tested": tested, "answers": n, "correct": ok, "acc": acc,
        "raw_acc": (ok / float(n)) if n else None,
        "solid": counts["solid"] + counts["mastered"], "covered": covered,
        "tested_share": (tested / float(total)) if total else 0.0,
        "solid_share": ((counts["solid"] + counts["mastered"]) / float(total)) if total else 0.0,
    }


def triage(repo: Repo, tree, state, when) -> list:
    """Rank subjects by expected marks gained per hour still needed. Highest first."""
    papers = gateinfo.papers(repo)
    both = len(papers) > 1
    daily_hours = float(repo.cfg("gate.daily_hours", 6))
    rows = []
    for node in gate_nodes(repo, tree):
        marks, source = weight(state, node)
        nums = subject_numbers(repo, tree, state, node)
        attained = nums["tested_share"] * nums["acc"]
        gain = marks * (1.0 - attained)
        overlap = 1.0 + (0.25 if (both and node.overlaps) or node.track == "gate" else 0.0)
        hours_left = max(1.0, float(node.est_hours or 20) * (1.0 - nums["solid_share"]))
        days = gateinfo.days_left(repo, node.paper, when.date())
        time_factor = 1.0
        if days is not None:
            time_factor = min(1.0, max(0.0, days) * daily_hours / hours_left) if days > 0 else 0.0
        value = gain * overlap * time_factor / hours_left
        rows.append({
            "skill": node.id, "title": node.title, "paper": node.paper or "all", "marks": marks,
            "source": source, "nums": nums, "gain": gain, "hours_left": hours_left, "value": value,
            "days": days, "overlap": overlap > 1.0,
        })
    rows.sort(key=lambda r: (-r["value"], r["skill"]))
    if rows:
        cut = max(1, int(round(0.15 * len(rows))))
        late = any(r["days"] is not None and r["days"] < 70 for r in rows)
        for i, row in enumerate(rows):
            if i < max(3, len(rows) // 3):
                row["verdict"] = "focus"
            elif late and i >= len(rows) - cut and row["hours_left"] > 8 and row["nums"]["tested_share"] < 0.2:
                row["verdict"] = "candidate to drop"
            else:
                row["verdict"] = "keep"
    return rows


def triage_text(repo: Repo, tree, state, when) -> str:
    rows = triage(repo, tree, state, when)
    if not rows:
        return "No GATE subjects found. Set the papers first: profile set gate.papers CS,DA"
    body = []
    for r in rows:
        n = r["nums"]
        acc = pct(n["raw_acc"]) if n["raw_acc"] is not None else "-"
        body.append([r["skill"], r["paper"], "%.1f%s" % (r["marks"], "" if r["source"] != "prior" else "*"),
                     "%d/%d" % (n["tested"], n["total"]), acc, "%.1f" % r["gain"], "%dh" % round(r["hours_left"]),
                     "%.2f" % r["value"], r["verdict"]])
    out = [table(body, ["subject", "paper", "marks", "tested", "accuracy", "to gain", "hours left", "marks/h", "verdict"],
                 aligns="llrrrrrrl")]
    if any(r["source"] == "prior" for r in rows):
        out.append("* marks marked with a star are priors, not counts from official papers. Replace them with: "
                   "gate weight <subject> <marks> --source \"...\"  or  gate weights --apply (after importing official papers).")
    out.append("'to gain' = marks not yet backed by verified answers. 'marks/h' ranks where the next hour pays most.")
    out.append("Hours are estimates from the subject files. Dropping a subject is the learner's decision; "
               "'candidate to drop' only appears inside the last 10 weeks.")
    return "\n".join(out)


def enroll_all(repo: Repo, tree, state, mode: str = "mastery") -> str:
    """Enrol every subject of the learner's papers (GATE subjects have no prerequisite gates)."""
    nodes = gate_nodes(repo, tree)
    if not nodes:
        raise CalError("no papers set. Run: profile set gate.papers CS  (or DA, or CS,DA)")
    done = []
    for node in nodes:
        sk = state.skills.get(node.id)
        if sk is not None and sk.enrolled:
            continue
        repo.append("enroll", skill=node.id, mode=mode)
        done.append(node.id)
    if not done:
        return "all %d GATE subjects were already enrolled" % len(nodes)
    return "enrolled %d GATE subject(s): %s" % (len(done), ", ".join(done))


def weight_set(repo: Repo, tree, skill: str, marks: float, source: str) -> str:
    node = tree.get(skill)
    if not node.track.startswith("gate"):
        raise CalError("%s is not a GATE subject" % skill)
    if not 0 <= marks <= 100:
        raise CalError("marks must be between 0 and 100")
    if not (source or "").strip():
        raise CalError("--source is required: say where the number comes from")
    repo.append("gate_weight", skill=skill, marks=float(marks), source=source.strip())
    return "weight set: %s = %.1f marks (%s)" % (skill, marks, source.strip())


def weights_from_items(repo: Repo, tree, state, apply: bool = False) -> str:
    """Average marks per subject over fully-imported official papers."""
    papers = {}
    for st in state.items.values():
        if st.src != "official" or st.status not in ("verified", "disputed") or not st.topics:
            continue
        try:
            item = items.load(repo, st.id)
        except CalError:
            continue
        m = _REF_RE.search(item.get("source", {}).get("ref", ""))
        if not m or not item.get("marks"):
            continue
        key = (m.group(1).upper(), m.group(2))
        skill = item["topics"][0].split("/", 1)[0]
        bucket = papers.setdefault(key, {})
        bucket[skill] = bucket.get(skill, 0) + item["marks"]
    complete = {k: v for k, v in papers.items() if sum(v.values()) >= 90}
    if not complete:
        have = ", ".join("%s %s (%d marks)" % (p, y, sum(v.values())) for (p, y), v in sorted(papers.items()))
        return ("No fully imported official paper yet (a paper counts once at least 90 of its 100 marks are imported).\n"
                "Imported so far: %s" % (have or "none"))
    rows, events = [], []
    by_paper = {}
    for (paper, year), marks in complete.items():
        by_paper.setdefault(paper, []).append((year, marks))
    for paper, years in sorted(by_paper.items()):
        skills = sorted({s for _, marks in years for s in marks})
        for skill in skills:
            avg = sum(marks.get(skill, 0) for _, marks in years) / float(len(years))
            label = "official papers %s (%s)" % (paper, ", ".join(sorted(y for y, _ in years)))
            rows.append([skill, paper, "%.1f" % avg, len(years)])
            events.append((skill, avg, label))
    text = table(rows, ["subject", "paper", "avg marks", "papers"], aligns="llrr")
    if apply:
        for skill, avg, label in events:
            if skill in tree.nodes:
                repo.append("gate_weight", skill=skill, marks=round(avg, 2), source=label)
        return text + "\napplied %d weight(s)" % len(events)
    return text + "\nrun again with --apply to use these weights"


# ---------------------------------------------------------------- mocks


def mock_add(repo: Repo, paper: str, score: float, maximum: float, date: str | None, source: str,
             sections: str | None, minutes, note: str | None) -> str:
    paper = paper.upper()
    if not re.match(r"^[A-Z]{2}$", paper):
        raise CalError("paper is a two-letter GATE code such as CS or DA")
    if not maximum or maximum <= 0 or score > maximum or score < -maximum:
        raise CalError("score must be within the paper's maximum")
    if not (source or "").strip():
        raise CalError("--source is required (which test series or paper this was)")
    parsed = {}
    for part in (sections or "").split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise CalError("sections look like: GA=11.33,PS=9,ML=14")
        name, value = part.split("=", 1)
        parsed[name.strip()] = items.parse_number(value)
    repo.append("mock", paper=paper, score=float(score), max=float(maximum), date=date, source=source.strip(),
                sections=parsed or None, minutes=minutes, note=note)
    target = gateinfo.target_marks(repo, paper)
    line = "mock recorded: %s %.2f of %.0f (%s)" % (paper, score, maximum, source.strip())
    if target is not None:
        scaled = 100.0 * score / maximum
        line += "\nagainst the target of %.0f: %+.1f marks" % (target, scaled - target)
    return line


def _mock_rows(state, paper: str | None = None) -> list:
    rows = []
    for m in state.mocks:
        if paper and m.get("paper") != paper:
            continue
        date = str(m.get("date") or m["ts"][:10])
        scaled = 100.0 * float(m["score"]) / float(m["max"])
        rows.append((date, m.get("paper"), scaled, m.get("source") or "", m))
    rows.sort(key=lambda r: (r[0], r[4]["ts"]))
    return rows


def mocks_text(repo: Repo, state, paper: str | None = None) -> str:
    rows = _mock_rows(state, paper)
    if not rows:
        return "No mock scores recorded yet. Add one with: gate mock <PAPER> <score> --source \"...\""
    body = []
    for date, p, scaled, source, m in rows:
        target = gateinfo.target_marks(repo, p or "")
        gap = ("%+.1f" % (scaled - target)) if target is not None else "-"
        secs = ", ".join("%s %s" % (k, _num(v)) for k, v in (m.get("sections") or {}).items())
        body.append([date, p, "%.2f" % scaled, gap, source, secs])
    out = [table(body, ["date", "paper", "marks/100", "vs target", "source", "sections"], aligns="llrrll")]
    for p in sorted({r[1] for r in rows}):
        mine = [r[2] for r in rows if r[1] == p]
        if len(mine) >= 2:
            last = mine[-3:]
            out.append("%s: last %d average %.1f, best %.1f, change since first %+.1f"
                       % (p, len(last), sum(last) / len(last), max(mine), mine[-1] - mine[0]))
    return "\n".join(out)


def _num(value) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    return ("%d" % f) if f.is_integer() else ("%.2f" % f)


# ---------------------------------------------------------------- status


def phase(repo: Repo, days) -> str:
    if days is None:
        return "exam date unknown"
    if days < 0:
        return "exam passed"
    final = int(repo.cfg("gate.final_phase_days", 21))
    if days <= final:
        return "final phase: reviews held tighter, mocks every other day, no new subjects"
    if days <= 42:
        return "revision phase: finish open subjects, two full mocks a week, error log after each"
    if days <= 84:
        return "build phase: cover remaining subjects, sectional tests weekly, first full mocks"
    return "foundation phase: cover the syllabus in triage order, test every lecture"


def projection(repo: Repo, tree, state, paper: str) -> float:
    """Marks backed by verified practice: sum of weight x share tested x accuracy. A floor, not a forecast."""
    total = 0.0
    for node in gate_nodes(repo, tree, paper):
        marks, _ = weight(state, node)
        nums = subject_numbers(repo, tree, state, node)
        if nums["answers"]:
            total += marks * nums["tested_share"] * (nums["correct"] / float(nums["answers"]))
    return total


def status_text(repo: Repo, tree, state, when) -> str:
    papers = gateinfo.papers(repo)
    if not papers:
        return "No GATE papers set. Run: profile set gate.papers CS  (or DA, or CS,DA)"
    data = gateinfo.year_data(repo)
    out = ["GATE %s" % (repo.prof("gate.year") or "?")]
    for paper in papers:
        days = gateinfo.days_left(repo, paper, when.date())
        date = gateinfo.exam_date(repo, paper)
        own = repo.prof("gate.exam_date.%s" % paper)
        target = gateinfo.target_marks(repo, paper)
        line = "%s: " % paper
        if date is None:
            line += "exam date unknown (set gate.year, or gate.exam_date.%s)" % paper
        else:
            line += "%d days to %s%s" % (days, date.isoformat(), "" if own else " (first exam day; paper date not set)")
        if target is not None:
            line += " · target %.0f marks" % target
        mocks = [r[2] for r in _mock_rows(state, paper)]
        line += " · last mock %s" % (("%.1f" % mocks[-1]) if mocks else "none")
        line += " · backed by practice so far: %.1f marks" % projection(repo, tree, state, paper)
        out.append(line)
        out.append("  " + phase(repo, days))
    if data.get("checked"):
        out.append("dates and pattern as published by %s, checked %s (%s)" % (
            data.get("organiser", "the organising institute"), data.get("checked"), data.get("site", "")))
    rows = []
    for node in gate_nodes(repo, tree):
        nums = subject_numbers(repo, tree, state, node)
        marks, source = weight(state, node)
        sk = state.skills.get(node.id)
        rows.append([node.id, node.paper or "all", "%.1f%s" % (marks, "*" if source == "prior" else ""),
                     "%d/%d" % (nums["covered"], nums["total"]), "%d/%d" % (nums["tested"], nums["total"]),
                     "%d/%d" % (nums["solid"], nums["total"]),
                     pct(nums["raw_acc"]) if nums["raw_acc"] is not None else "-",
                     "yes" if (sk and sk.enrolled) else "no"])
    out.append("")
    out.append(table(rows, ["subject", "paper", "marks", "covered", "tested", "solid", "accuracy", "enrolled"],
                     aligns="llrrrrrl"))
    out.append("* prior weight. 'backed by practice' counts only verified answers; a full mock is the real measure.")
    return "\n".join(out)


def brief_lines(repo: Repo, tree, state, when) -> list:
    papers = gateinfo.papers(repo)
    if not papers:
        return []
    bits = []
    for paper in papers:
        days = gateinfo.days_left(repo, paper, when.date())
        target = gateinfo.target_marks(repo, paper)
        mocks = [r[2] for r in _mock_rows(state, paper)]
        bit = "%s in %s days" % (paper, days if days is not None else "?")
        if target is not None:
            bit += ", target %.0f" % target
        bit += ", last mock %s" % (("%.1f" % mocks[-1]) if mocks else "none")
        bits.append(bit)
    lines = ["GATE %s: %s" % (repo.prof("gate.year") or "?", " · ".join(bits))]
    days = [gateinfo.days_left(repo, p, when.date()) for p in papers]
    days = [d for d in days if d is not None]
    if days:
        lines.append("GATE phase: " + phase(repo, min(days)))
    return lines
