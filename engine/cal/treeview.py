"""Text views of the skill tree: list, one skill, the route to a goal, what to learn next, search."""
from __future__ import annotations

import os

from . import sources
from .plan import GLYPH, GLYPH_ASCII
from .state import SATISFIED
from .store import Repo
from .util import csv_list, fmt_delta, pct, table, term_width, truncate, wrap_cells

LEGEND = (("mastered", "mastered or known"), ("ready", "ready (unlocks the next skills)"), ("active", "learning"),
          ("available", "open to start"), ("locked", "locked"))


def glyph(status: str, ascii_only: bool = False) -> str:
    return (GLYPH_ASCII if ascii_only else GLYPH).get(status, "?")


def legend(ascii_only: bool = False, width: int | None = None, extra=()) -> str:
    cells = ["%s %s" % (glyph(s, ascii_only), label) for s, label in LEGEND] + list(extra)
    if width is None:
        return "  ".join(cells)
    return "\n".join(wrap_cells(cells, width, ""))


def chooser(tree, state):
    """Pick the member of a slot the learner is already on, else the first listed."""

    def choose(alts):
        for wanted in (SATISFIED, ("active", "paused")):
            for a in alts:
                if state.skill_status(a) in wanted:
                    return a
        for a in alts:
            sk = state.skills.get(a)
            if sk is not None and sk.enrolled:
                return a
        return alts[0]

    return choose


def learner_tracks(repo: Repo, tree) -> list:
    chosen = [t for t in csv_list(repo.prof("tracks")) if t in tree.tracks]
    if any(t.startswith("gate-") for t in chosen) and "gate" in tree.tracks and "gate" not in chosen:
        chosen.append("gate")
    return chosen


def list_text(repo: Repo, tree, state, track=None, group=None, status=None, ascii_only: bool = False) -> str:
    rows = []
    for node in tree.ordered():
        st = state.skill_status(node.id)
        if track and node.track != track:
            continue
        if group and node.group != group:
            continue
        if status and st != status:
            continue
        if node.dropped and status != "dropped":
            continue
        counts = state.skill_counts(node.id)
        prog = "%d/%d" % (counts["solid"] + counts["mastered"], counts["total"]) if counts["total"] else "-"
        sk = state.skills.get(node.id)
        flag = "enrolled" if (sk and sk.enrolled and not sk.paused) else ""
        rows.append([glyph(st, ascii_only), node.id, truncate(node.title, 34), node.track, node.group, st, prog, flag])
    if not rows:
        return "No skills match."
    return (table(rows, ["", "skill", "title", "track", "group", "status", "solid", ""]) + "\n"
            + legend(ascii_only, term_width()))


def show_text(repo: Repo, tree, state, when, skill_id: str, ascii_only: bool = False) -> str:
    node = tree.get(skill_id)
    st = state.skill_status(skill_id)
    sk = state.skills.get(skill_id)
    lines = ["%s %s | %s" % (glyph(st, ascii_only), node.id, node.title),
             "status: %s%s · track %s · group %s%s%s" % (
                 st, " (enrolled, %s mode)" % sk.mode if (sk and sk.enrolled) else "", node.track, node.group,
                 " · optional" if node.optional else "", " · milestone" if node.kind == "milestone" else "")]
    if node.summary:
        lines.append(node.summary)
    reqs = tree.requirement_groups(node)
    if reqs:
        parts = []
        for label, alts in reqs:
            shown = " or ".join("%s %s" % (glyph(state.skill_status(a), ascii_only), a) for a in alts) or label
            parts.append(("(%s)" % shown) if len(alts) > 1 else shown)
        lines.append("needs: " + ", ".join(parts))
    if node.slot:
        others = [n.id for n in tree.slot_members(node.slot) if n.id != node.id and not n.dropped]
        lines.append("slot: %s%s" % (node.slot, (" (alternatives: %s)" % ", ".join(others)) if others else ""))
    deps = [d.id for d in tree.dependents(skill_id)]
    if deps:
        lines.append("unlocks: " + ", ".join(deps))
    if node.weaves_into:
        lines.append("weaves into: " + ", ".join(node.weaves_into))
    if node.est_hours:
        lines.append("estimate: about %d hours to the mastery standard" % node.est_hours)
    lines.append("file: %s (%s)" % (repo.rel(node.path), "your own" if node.origin == "learner" else "shipped"))
    if node.topics:
        led = skill_id in sources.led_skills(repo, tree)
        rows, strands, total = [], {}, 0
        for topic in node.topics:
            ts = state.topics.get(topic.key)
            status = state.topic_status(topic.key)
            goals = topic.objectives()
            total += len(goals)
            for o in goals:
                strands[o["strand"]] = strands.get(o["strand"], 0) + 1
            cov = state.coverage(topic.key)
            covered = ("%d/%d" % cov) if cov else ("-/%d" % len(goals) if goals else "")
            if ts is not None and ts.card is not None:
                recall = pct(state.retrievability(topic.key, when))
                due = fmt_delta(ts.card.due - when)
                answers = "%d/%d" % (ts.n_ok, ts.n)
            else:
                recall, due, answers = "", "", ""
            rows.append([topic.id, truncate(topic.title, 40), status, answers, covered, recall, due])
        lines.append("")
        lines.append("topics (%s%s):" % ("your syllabus" if node.topics_origin == "learner" else "shipped syllabus",
                                         ", studied from a source: lecture first, then tested" if led else ""))
        lines.append(table(rows, ["topic", "title", "status", "correct", "objectives", "recall", "review"],
                           aligns="lllrrrl"))
        if total:
            from .tree import STRANDS

            parts = ["%s %d%%" % (STRANDS[s], round(100.0 * strands[s] / total)) for s in "TPIN" if strands.get(s)]
            untagged = strands.get(None, 0)
            lines.append("strands: %s%s (objectives: answered right on a tagged item / in the syllabus)" % (
                " · ".join(parts) or "none tagged",
                (" · %d untagged" % untagged) if untagged and parts else ""))
    elif node.kind != "milestone":
        scope = node.section("Scope")
        lines.append("")
        lines.append("no syllabus yet. Scope to build it from:")
        lines.append(scope or "(the skill file has no Scope section)")
    if node.has_boss:
        done = sk is not None and sk.boss_ok
        lines.append("")
        lines.append("boss: %s (see: boss status %s)" % ("passed" if done else "not passed yet", skill_id))
    return "\n".join(lines)


def path_text(repo: Repo, tree, state, skill_id: str, ascii_only: bool = False, width: int | None = None) -> str:
    width = width or term_width()
    node = tree.get(skill_id)
    choose = chooser(tree, state)
    met = [a for a in tree.ancestors(skill_id, choose) if state.skill_status(a) in SATISFIED]
    layers = tree.layers(skill_id, choose, skip=lambda nid: state.skill_status(nid) in SATISFIED)
    lines = ["Route to %s | %s" % (node.id, node.title)]
    if state.skill_status(skill_id) in SATISFIED:
        lines.append("already %s." % state.skill_status(skill_id))
        return "\n".join(lines)
    if met:
        lines.append("already met: " + ", ".join(met))
    hours = 0.0
    count = 0
    for i, layer in enumerate(layers, 1):
        cells = []
        for nid in layer:
            cells.append("%s %s" % (glyph(state.skill_status(nid), ascii_only), nid))
            hours += tree.nodes[nid].est_hours or 0
            count += 1
        note = " (start here; these can run in parallel)" if i == 1 and len(layer) > 1 else (" (start here)" if i == 1 else "")
        lines.extend(wrap_cells(cells, width, "         ", "layer %d%s: " % (i, note)))
    if hours:
        lines.append("about %d hours across %d skill(s) at the mastery standard (estimates from the skill files)" % (hours, count))
    slots = []
    seen = set()
    for nid in [n for layer in layers for n in layer]:
        for label, alts in tree.requirement_groups(tree.nodes[nid]):
            if label.startswith("slot:") and len(alts) > 1 and label not in seen:
                seen.add(label)
                slots.append("  %s: %s (or %s)" % (label[5:], choose(alts), ", ".join(a for a in alts if a != choose(alts))))
    if slots:
        lines.append("choices on this route (enrol in an alternative and the route follows it):")
        lines.extend(slots)
    lines.append(legend(ascii_only, width))
    return "\n".join(lines)


def suggest(repo: Repo, tree, state, n: int = 5) -> list:
    """What to start next: [(node, reason)], best first."""
    tracks = learner_tracks(repo, tree)
    choose = chooser(tree, state)
    goals = [g for g in csv_list(repo.prof("goals")) if g in tree.nodes]
    on_route = {}
    for goal in goals:
        if state.skill_status(goal) in SATISFIED:
            continue
        for depth, layer in enumerate(tree.layers(goal, choose, skip=lambda nid: state.skill_status(nid) in SATISFIED)):
            for nid in layer:
                if nid not in on_route or depth < on_route[nid][0]:
                    on_route[nid] = (depth, goal)
    last_group = None
    latest = None
    for sid, sk in state.skills.items():
        if sk.last_ts and sid in tree.nodes and (latest is None or sk.last_ts > latest):
            latest, last_group = sk.last_ts, tree.nodes[sid].group
    rows = []
    for node in tree.live():
        if state.skill_status(node.id) != "available":
            continue
        sk = state.skills.get(node.id)
        if sk is not None and sk.enrolled:
            continue
        if node.track.startswith("gate"):
            continue  # GATE subjects are enrolled together by the GATE companion
        if tracks and node.track not in tracks and node.id not in on_route:
            continue
        unlocks = []
        for dep in tree.dependents(node.id):
            if state.skill_status(dep.id) != "locked":
                continue
            others = [lab for lab, _ in state.missing_prereqs(dep.id)
                      if lab != node.id and not (node.slot and lab == "slot:" + node.slot)]
            if not others:
                unlocks.append(dep.id)
        score = 0.0
        reason = []
        if node.id in on_route:
            depth, goal = on_route[node.id]
            score += 100 - 10 * depth
            reason.append("on the route to %s" % goal if node.id != goal else "your goal, now unlocked")
        if unlocks:
            score += 6 * len(unlocks)
            reason.append("unlocks %s" % ", ".join(unlocks[:4]))
        if node.group == last_group:
            score += 3
            reason.append("continues %s" % node.group)
        if node.optional:
            score -= 5
            reason.append("optional")
        if not node.prereqs:
            score += 1
        rows.append((-score, node.order, node.id, node, "; ".join(reason) or "open to start"))
    rows.sort(key=lambda r: r[:3])
    return [(r[3], r[4]) for r in rows[:n]]


def suggest_text(repo: Repo, tree, state, n: int = 5, ascii_only: bool = False) -> str:
    picks = suggest(repo, tree, state, n)
    if not picks:
        lines = ["Nothing else is open to start yet."]
        for skill_id in state.enrolled_skills()[:4]:
            waiting = [d.id for d in tree.dependents(skill_id) if state.skill_status(d.id) == "locked"]
            if waiting:
                lines.append("  %s unlocks %s%s once it is ready" % (
                    skill_id, ", ".join(waiting[:6]), " ..." if len(waiting) > 6 else ""))
        lines.append("Carry on with what is enrolled (the route to a goal: tree path <skill>), or add a skill: tree add ...")
        return "\n".join(lines)
    out = ["Open to start, best first:"]
    for node, why in picks:
        hours = (", about %dh" % node.est_hours) if node.est_hours else ""
        out.append("  %s | %s (%s%s)" % (node.id, node.title, node.track, hours))
        out.append("      %s" % why)
    goals = csv_list(repo.prof("goals"))
    if not goals:
        out.append("No goal is set. Set one to get a route, for example: profile set goals mern-stack,kubernetes")
    out.append("start one with: enroll <skill>   ·   see a route with: tree path <skill>")
    return "\n".join(out)


def find_text(repo: Repo, tree, state, query: str) -> str:
    words = [w for w in query.lower().replace("/", " ").split() if w]
    if not words:
        return "Give something to search for."
    rows = []
    for node in tree.find(query, limit=8):
        rows.append(["skill", node.id, truncate(node.title, 40), state.skill_status(node.id), repo.rel(node.path)])
    for node in tree.live():
        for topic in node.topics:
            hay = " ".join([topic.id, topic.title.lower()] + [a.lower() for a in topic.aliases]).replace("-", " ")
            if all(w.replace("-", " ") in hay for w in words):
                rows.append(["topic", topic.key, truncate(topic.title, 40), state.topic_status(topic.key),
                             repo.rel(node.topics_path or node.path)])
    for src in sources.load_all(repo):
        for it in src.items:
            hay = (it.id + " " + it.title).lower()
            if all(w in hay for w in words):
                done = state.src.get(src.id, {}).get(it.id, {}).get("done")
                rows.append(["lecture", "%s %s" % (src.id, it.id), truncate(it.title, 40), "done" if done else "to do",
                             repo.rel(src.path)])
    if os.path.isdir(repo.notes_dir):
        for skill in sorted(os.listdir(repo.notes_dir)):
            d = os.path.join(repo.notes_dir, skill)
            if not os.path.isdir(d):
                continue
            for name in sorted(os.listdir(d)):
                if name.endswith(".md") and all(w in (skill + " " + name).lower() for w in words):
                    rows.append(["notes", "%s/%s" % (skill, name[:-3]), "", "", repo.rel(os.path.join(d, name))])
    if not rows:
        return "Nothing matches %r in skills, topics, lectures or notes." % query
    return table(rows[:30], ["kind", "id", "title", "state", "file"])
