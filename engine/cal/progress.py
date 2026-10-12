"""learner/PROGRESS.md: a readable snapshot of the learner's growth, rebuilt from the event log.

It is the one generated file that is committed, so progress can be read on
GitHub. Its content depends only on the log, the tree and the profile (never
on the clock or the machine), so two machines that hold the same events
write the same file.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

from . import gateinfo
from .store import Repo, write_text
from .util import fmt_minutes, pct


def _md_table(head, rows) -> list:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |")
    return out


def render(repo: Repo, tree, state) -> str:
    lines = ["# Progress", "",
             "_Rebuilt from the event log by the engine (`rebuild`). Do not edit: it is overwritten._", ""]
    if state.last_dt is None:
        lines.append("No activity recorded yet.")
        return "\n".join(lines) + "\n"
    as_of = state.last_dt
    name = repo.prof("name", "")
    lines.append("%sLast activity: %s · %d events · %d active day(s)" % (
        (name + " · ") if name else "", state.day(as_of), state.n_events, len(state.days)))
    lines.append("")

    rows = []
    for node in tree.ordered():
        sk = state.skills.get(node.id)
        if sk is None or node.dropped or not (sk.enrolled or sk.known or sk.boss_ok or sk.last_ts):
            continue
        counts = state.skill_counts(node.id)
        solid = "%d / %d" % (counts["solid"] + counts["mastered"], counts["total"]) if counts["total"] else "-"
        rows.append([node.id, node.title, node.track, state.skill_status(node.id), solid, counts["mastered"],
                     sk.mode, "passed" if sk.boss_ok else ("open" if node.has_boss else "-"),
                     state.day(sk.last_ts) if sk.last_ts else "-"])
    lines.append("## Skills")
    lines.append("")
    if rows:
        lines += _md_table(["skill", "title", "track", "status", "solid / topics", "mastered", "mode", "boss", "last studied"], rows)
    else:
        lines.append("None started yet.")
    lines.append("")

    papers = gateinfo.papers(repo)
    if papers:
        lines.append("## GATE %s" % (repo.prof("gate.year") or ""))
        lines.append("")
        today = date.fromisoformat(state.day(as_of))
        for paper in papers:
            left = gateinfo.days_left(repo, paper, today)
            target = gateinfo.target_marks(repo, paper)
            bit = "- %s: %s days to the exam as of the last activity" % (paper, left if left is not None else "?")
            if target is not None:
                bit += ", target %.0f marks" % target
            lines.append(bit)
        mocks = sorted(state.mocks, key=lambda m: (str(m.get("date") or m["ts"][:10]), m["ts"]))
        if mocks:
            lines.append("")
            lines += _md_table(["date", "paper", "marks / 100", "source"], [
                [str(m.get("date") or m["ts"][:10]), m.get("paper"), "%.2f" % (100.0 * float(m["score"]) / float(m["max"])),
                 m.get("source") or ""] for m in mocks])
        lines.append("")

    handle = repo.prof("cp.handle")
    if handle:
        lines.append("## Competitive programming")
        lines.append("")
        lines.append("- Codeforces handle: %s (rating history lives on Codeforces; see `cf rating`)" % handle)
        target = repo.prof("cp.target_rating")
        if target:
            lines.append("- target rating: %s%s" % (target, (" by %s" % repo.prof("cp.target_date")) if repo.prof("cp.target_date") else ""))
        marked = sum(1 for rec in state.cp_marks.values() if rec["subtags"])
        lines.append("- problems assigned by the coach: %d · problems sub-tagged: %d" % (len(state.cp_assigned), marked))
        lines.append("")

    weeks = {}
    for key, ds in state.days.items():
        d = date.fromisoformat(key)
        monday = d - timedelta(days=d.weekday())
        w = weeks.setdefault(monday, {"min": 0.0, "n": 0, "ok": 0, "new": 0, "rev": 0, "lec": 0, "days": 0})
        w["min"] += ds.active_min
        w["n"] += ds.attempts
        w["ok"] += ds.ok
        w["new"] += ds.new
        w["rev"] += ds.reviews
        w["lec"] += ds.src_done
        w["days"] += 1
    lines.append("## Weeks")
    lines.append("")
    rows = []
    for monday in sorted(weeks, reverse=True)[:16]:
        w = weeks[monday]
        rows.append([monday.isoformat(), w["days"], fmt_minutes(w["min"]), w["n"],
                     pct(w["ok"] / float(w["n"])) if w["n"] else "-", w["new"], w["rev"], w["lec"] or "-"])
    lines += _md_table(["week of", "active days", "active time", "answers", "accuracy", "new topics", "reviews", "lectures"], rows)
    lines.append("")
    lines.append("Active time is measured from activity in this repository; lectures watched elsewhere are counted, not timed.")
    return "\n".join(lines) + "\n"


def write(repo: Repo, tree, state) -> str:
    path = os.path.join(repo.learner, "PROGRESS.md")
    text = render(repo, tree, state)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            if fh.read() == text:
                return path
    except OSError:
        pass
    write_text(path, text)
    return path
