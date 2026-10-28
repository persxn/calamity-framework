"""Terminal dashboards: progress, roadmap, revision queue, GATE board, Codeforces board, the week.

Plain text that reads the same in a terminal, in the desktop app and on a
phone over Remote Control. Unicode by default, --ascii for anything else.
"""
from __future__ import annotations

from datetime import timedelta

from . import plan, stats, treeview
from .store import Repo
from .util import bar, csv_list, day_bounds, fmt_delta, pct, table, truncate, wrap_cells


def _rule(width: int, ascii_only: bool) -> str:
    return ("-" if ascii_only else "─") * width


def header(repo: Repo, tree, state, when, width: int, ascii_only: bool) -> list:
    name = repo.prof_text("name")
    title = "CALAMITY" + ((" · " + name) if name else "") + " · " + when.strftime("%a %d %b %H:%M")
    lines = [title]
    if not repo.onboarded():
        lines.append("not onboarded yet")
        return lines
    t = plan.today(repo, tree, state, when)
    n = t["n"]
    # 0/0 is nothing scheduled, not a full day's work done: show an empty bar
    rev = (n["due_done"] / float(n["due_total"])) if n["due_total"] else 0.0
    new = (n["new_done"] / float(t["new_target"])) if t["new_target"] else 0.0
    lines.append("reviews %s %d/%d   new %s %d/%d%s" % (
        bar(rev, 10, ascii_only), n["due_done"], n["due_total"], bar(new, 10, ascii_only), n["new_done"], t["new_target"],
        ("   lectures %d/%d" % (t["lectures_done"], t["lecture_target"])) if t["lecture_target"] else ""))
    lines.append(plan.finish_text(t) + (" · %d answered today, %s correct" % (n["attempts"], pct(n["ok"] / float(n["attempts"]))) if n["attempts"] else ""))
    return lines


def progress(repo: Repo, tree, state, when, width: int = 80, ascii_only: bool = False) -> str:
    lines = header(repo, tree, state, when, width, ascii_only)
    lines.append(_rule(min(width, 78), ascii_only))
    shown = set(state.enrolled_skills())
    for sid, sk in state.skills.items():
        node = tree.nodes.get(sid)
        if node is not None and not node.dropped and (sk.known or sk.paused or sk.boss_ok):
            shown.add(sid)
    if not shown:
        lines.append("No skill started yet. See: tree suggest")
        return "\n".join(lines)
    due_now = {}
    for key, _ in state.due(when):
        due_now[key.split("/", 1)[0]] = due_now.get(key.split("/", 1)[0], 0) + 1
    name_w = min(30, max(len(s) for s in shown))
    for track in tree.tracks:
        nodes = [n for n in tree.ordered() if n.track == track and n.id in shown]
        if not nodes:
            continue
        lines.append(tree.track_title(track))
        idle = []
        for node in nodes:
            counts = state.skill_counts(node.id)
            st = state.skill_status(node.id)
            sk = state.skills[node.id]
            if st == "active" and not sk.last_ts and counts["total"]:
                idle.append(node.id)    # enrolled, nothing answered yet: one shared line below
                continue
            if counts["total"]:
                share = (counts["solid"] + counts["mastered"]) / float(counts["total"])
                detail = "%d/%d solid" % (counts["solid"] + counts["mastered"], counts["total"])
                if counts["mastered"]:
                    detail += ", %d mastered" % counts["mastered"]
            else:
                share = 1.0 if st in ("mastered", "known") else 0.0
                detail = "known (placement)" if st == "known" else ("milestone" if node.kind == "milestone" else "no syllabus yet")
            extras = []
            if due_now.get(node.id):
                extras.append("%d due" % due_now[node.id])
            if sk.paused:
                extras.append("paused")
            if sk.mode == "brushup":
                extras.append("brush-up")
            if node.has_boss and counts["total"]:
                extras.append("boss passed" if sk.boss_ok else "boss open")
            lines.append("  %s %s %s %s%s" % (
                treeview.glyph(st, ascii_only), node.id.ljust(name_w), bar(share, 10, ascii_only), detail,
                (" · " + ", ".join(extras)) if extras else ""))
        if idle:
            lines.extend(wrap_cells(idle, width, "      ", "  %s not started yet (%d): " % (
                treeview.glyph("active", ascii_only), len(idle))))
    lines.append(treeview.legend(ascii_only, width))
    return "\n".join(lines)


def roadmap(repo: Repo, tree, state, when, width: int = 80, ascii_only: bool = False, track: str | None = None,
            all_tracks: bool = False) -> str:
    tracks = [track] if track else (tree.tracks if all_tracks else (treeview.learner_tracks(repo, tree) or tree.tracks))
    lines = []
    for tr in tracks:
        nodes = [n for n in tree.live() if n.track == tr]
        if not nodes:
            continue
        tally = {}
        for n in nodes:
            st = state.skill_status(n.id)
            tally[st] = tally.get(st, 0) + 1
        counts = [(tally.get("mastered", 0) + tally.get("known", 0), "done"), (tally.get("ready", 0), "ready"),
                  (tally.get("active", 0), "learning"), (tally.get("paused", 0), "paused"),
                  (tally.get("available", 0), "open"), (tally.get("locked", 0), "locked")]
        summary = "[%d skills: %s]" % (len(nodes), ", ".join("%d %s" % c for c in counts if c[0]))
        title = tree.track_title(tr)
        if len(title) + 2 + len(summary) <= width:
            lines.append("%s  %s" % (title, summary))
        else:
            lines += [title, "  " + summary]
        for group in tree.groups(tr):
            members = [n for n in nodes if n.group == group]
            if not members:
                continue
            lines.append(" " + group)
            cells = []
            for n in members:
                st = state.skill_status(n.id)
                cell = "%s %s" % (treeview.glyph(st, ascii_only), n.id)
                if n.optional:
                    cell += "?"
                cells.append(cell)
            lines.extend(wrap_cells(cells, width, "   "))
        lines.append("")
    lines.append(treeview.legend(ascii_only, width, extra=("? optional",)))
    lines.extend(wrap_cells(["details: tree show <skill>", "route to a goal: tree path <skill>", "what next: tree suggest"],
                            width, ""))
    return "\n".join(lines)


def queue(repo: Repo, tree, state, when, width: int = 80, ascii_only: bool = False, limit: int = 15) -> str:
    due = state.due(when)
    t = plan.today(repo, tree, state, when) if repo.onboarded() else None
    lines = ["REVISION QUEUE · %d due now" % len(due)]
    if t and t["relearn"]:
        lines.append("to answer again today (failed earlier): %s" % ", ".join(t["relearn"][:6]))
    if due:
        rows = [[key, pct(state.retrievability(key, when)), fmt_delta(ts.card.due - when), state.topic_status(key)]
                for key, ts in due[:limit]]
        lines.extend(_queue_rows(rows, [tree.topic(key).title for key, _ in due[:limit]], width))
        if len(due) > limit:
            lines.append("... and %d more" % (len(due) - limit))
    start_hour = int(repo.cfg("day_start_hour", 4))
    _, day_end = day_bounds(when, start_hour)
    counts = []
    scheduled = state.scheduled_topics()
    for offset in range(1, 8):
        lo = day_end + timedelta(days=offset - 1)
        hi = day_end + timedelta(days=offset)
        counts.append(((when + timedelta(days=offset)).strftime("%a"),
                       sum(1 for _, ts in scheduled if lo < ts.card.due <= hi)))
    later_today = sum(1 for _, ts in scheduled if when < ts.card.due <= day_end)
    peak = max([c for _, c in counts] + [1])
    lines.append("")
    lines.append("coming up (later today: %d)" % later_today)
    for label, c in counts:
        lines.append("  %s %s %d" % (label, bar(c / float(peak), 16, ascii_only) if c else " " * 16, c))
    lines.append("in rotation: %d topics across %d skill(s)" % (len(scheduled), len({k.split('/', 1)[0] for k, _ in scheduled})))
    return "\n".join(lines)


def _queue_rows(rows, titles, width: int) -> list:
    """The due topics as a table. A topic key is what the learner types, so it is never cut short:
    on a narrow screen the title goes first, and then each topic takes two lines."""
    plain = table(rows, ["topic", "recall", "due", "status"], aligns="lrll")
    used = max(len(line) for line in plain.split("\n"))
    room = width - used - 2
    if room >= 16:
        wide = [[r[0], truncate(t, min(room, 34))] + r[1:] for r, t in zip(rows, titles)]
        return table(wide, ["topic", "title", "recall", "due", "status"], aligns="llrll").split("\n")
    if used <= width:
        return plain.split("\n")
    out = []
    for key, recall, due, status in rows:
        out += [key, "    recall %s · due %s · %s" % (recall, due, status)]
    return out


def everything(repo: Repo, tree, state, when, width: int = 80, ascii_only: bool = False) -> str:
    parts = [progress(repo, tree, state, when, width, ascii_only), "", queue(repo, tree, state, when, width, ascii_only, limit=8)]
    if any(str(t).startswith("gate") for t in csv_list(repo.prof("tracks"))):
        from . import gate

        parts += [""] + gate.brief_lines(repo, tree, state, when)
    if repo.prof("cp.handle"):
        from . import cf

        parts += [""] + cf.brief_lines(repo, state, when)
    return "\n".join(parts)


def week(repo: Repo, tree, state, when, days: int = 7) -> str:
    return stats.week_text(repo, state, when, days) + "\n\n" + stats.hours_text(repo, state, when)


def statusline(repo: Repo, tree, state, when, current=None) -> str:
    if not repo.onboarded():
        return "CAL · not onboarded"
    t = plan.today(repo, tree, state, when)
    parts = ["CAL", "due %d" % t["n"]["due_now"], "new %d/%d" % (t["n"]["new_done"], t["new_target"])]
    if t["lecture_target"]:
        parts.append("lec %d/%d" % (t["lectures_done"], t["lecture_target"]))
    if t["finished"]:
        parts.append("done")
    from . import gateinfo

    days = [gateinfo.days_left(repo, p, when.date()) for p in gateinfo.papers(repo)]
    days = [d for d in days if d is not None and d >= 0]
    if days:
        parts.append("GATE %dd" % min(days))
    if not t["finished"]:
        from . import advise

        hint = advise.short(repo, plan.next_action(repo, tree, state, when)["action"], current)
        if hint:
            parts.append(hint)
    return " · ".join(parts)


def write_html(repo, view: str, text: str) -> str:
    """The view as a page in .calamity/dash/<view>.html (the same text, in a monospace block), and two lines:
    its first line and where the page is. The conversation never carries the table."""
    import html
    import os

    from .store import write_text

    folder = os.path.join(repo.local, "dash")
    path = os.path.join(folder, "%s.html" % view)
    page = ("<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>Calamity: %s</title>\n<style>"
            "body{font:14px/1.45 ui-monospace,Menlo,Consolas,monospace;margin:24px;background:#fbfaf7;color:#222}"
            "@media (prefers-color-scheme:dark){body{background:#16161a;color:#e8e6e1}}"
            "pre{white-space:pre;overflow-x:auto}</style></head>\n<body><pre>%s</pre></body></html>\n"
            % (html.escape(view), html.escape(text)))
    write_text(path, page, durable=False)
    first = next((line for line in text.split("\n") if line.strip()), "")
    return "%s\n%s view written to %s (open it in a browser)" % (first.strip()[:160], view, path)
