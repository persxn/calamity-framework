"""Cross-skill growth: integration projects between skills learnt side by side, and the frontier of what to learn next.

    project suggest   two active skills that belong together (one weaves into the other, or a later skill or
                      milestone needs both) and have both reached `consolidating` on at least half their topics:
                      a 2-6 hour build that uses both, written by the examiner (or the drill-smith) as one `task`
                      item whose topics span both skills, so one pass credits both
    tree frontier     skills not started yet whose prerequisites are met or well under way, ranked by the route
                      to a goal and by how much of what they build on is secured, each with its reasons

A topic counts as secured from `consolidating` on; a skill known or mastered as a whole counts in full.
A skill opens (its status `available`) only once what it needs is `ready`: the frontier shows it earlier.
"""
from __future__ import annotations

from .util import CalError, csv_list, pct

SECURED = ("consolidating", "solid", "mastered", "known", "ready")
SATISFIED = ("known", "ready", "mastered")


def share(state, tree, sid: str) -> float:
    """Of a skill's topics, the share secured; 1.0 for a skill known or mastered as a whole."""
    if state.skill_status(sid) in SATISFIED:
        return 1.0
    node = tree.nodes.get(sid)
    if node is None or not node.topics:
        return 0.0
    return sum(1 for t in node.topics if state.topic_status(t.key) in SECURED) / float(len(node.topics))


def _active(state, tree):
    out = []
    for sid, sk in state.skills.items():
        node = tree.nodes.get(sid)
        if node is None or node.dropped or not node.topics or node.track.startswith("gate"):
            continue
        if sk.enrolled or sk.last_ts:
            out.append(sid)
    return sorted(out)


def _link(tree, a, b):
    """Why two skills belong in one project, or None."""
    na, nb = tree.nodes[a], tree.nodes[b]
    for x, y in ((na, nb), (nb, na)):
        accept = set(y.tags) | {y.id, y.group}
        if set(x.weaves_into) & accept:
            return "%s weaves into %s" % (x.id, y.id)
    for dep in tree.dependents(a):
        if b in [s for _, alts in tree.requirement_groups(dep) for s in alts]:
            return "%s needs both" % dep.id
    return None


def projects(repo, tree, state, when, n: int = 3) -> list:
    need = float(repo.cfg("project.share", 0.5))
    ready = [s for s in _active(state, tree) if share(state, tree, s) >= need]
    rows = []
    for i, a in enumerate(ready):
        for b in ready[i + 1:]:
            why = _link(tree, a, b)
            if why:
                rows.append((-(share(state, tree, a) + share(state, tree, b)), a, b, why))
    rows.sort()
    out = []
    for _, a, b, why in rows[:n]:
        topics = []
        for sid in (a, b):
            keys = [t.key for t in tree.nodes[sid].topics if state.topic_status(t.key) in SECURED]
            keys.sort(key=lambda k: state.retrievability(k, when) if state.topics.get(k) and state.topics[k].card else 1.0)
            topics += keys[:2]
        out.append({"skills": (a, b), "why": why, "topics": topics})
    return out


def projects_text(repo, tree, state, when, n: int = 3) -> str:
    picks = projects(repo, tree, state, when, n)
    if not picks:
        return ("No integration project yet: it needs two active skills that belong together (one weaves into the "
                "other, or a later skill needs both), each with at least half its topics consolidating.")
    lines = ["Integration projects (2-6 hours each, between single-skill items and capstones):"]
    for p in picks:
        a, b = (tree.nodes[s] for s in p["skills"])
        lines.append("  %s + %s (%s; %s and %s secured)" % (a.title, b.title, p["why"],
                                                          pct(share(state, tree, a.id)), pct(share(state, tree, b.id))))
        lines.append("      build: something real that needs both — %s; %s" % (a.summary.rstrip("."), b.summary[:1].lower()
                                                                               + b.summary[1:].rstrip(".")))
        lines.append("      topics: %s" % ", ".join(p["topics"]))
    lines.append("Ask the examiner (or the drill-smith) for one `task` item per project whose topics list those keys "
                 "(the first is the primary), with runnable checks: one pass credits every topic it lists.")
    return "\n".join(lines)


# ---------------------------------------------------------------- the frontier


def frontier(repo, tree, state, n: int = 5) -> list:
    goals = [g for g in csv_list(repo.prof("goals")) if g in tree.nodes]
    route = set()
    for g in goals:
        try:
            route.update(tree.ancestors(g))
        except CalError:
            continue
        route.add(g)
    mine = [s for s in _active(state, tree) if share(state, tree, s) >= 0.5]
    rows = []
    for node in tree.live():
        if node.track.startswith("gate") or node.kind == "milestone":
            continue
        sk = state.skills.get(node.id)
        if sk is not None and (sk.enrolled or sk.last_ts or sk.known):
            continue
        if state.skill_status(node.id) in SATISFIED:
            continue
        groups = tree.requirement_groups(node)
        if not groups:
            continue
        builds, waiting, ok = [], [], True
        for _, alts in groups:
            best = max(alts, key=lambda s: share(state, tree, s)) if alts else None
            if best is None:
                continue
            got = share(state, tree, best)
            if state.skill_status(best) in SATISFIED:
                builds.append((best, 1.0))
            elif got >= 0.5:
                builds.append((best, got))
                waiting.append(best)
            else:
                ok = False
                break
        if not ok:
            continue
        studied = [(s, g) for s, g in builds if (state.skills.get(s) and state.skills[s].last_ts)]
        if not studied:
            continue       # only what the learner's own work leads to, not everything the placements opened
        known = [s for s, _ in builds if (s, _) not in studied]
        # synergy: what the learner's own work feeds, then what else it combines with that is already theirs
        shared = sorted(set(node.tags) & {t for s in mine for t in tree.nodes[s].tags})
        score = 20 * sum(g for _, g in studied) + 8 * len(known) + 3 * len(shared) + (50 if node.id in route else 0) \
            - (node.est_hours or 20) / 10.0
        why = ["builds on %s" % ", ".join("%s (%s secured)" % (tree.nodes[s].title, pct(g)) for s, g in studied)]
        if known:
            why.append("with %s, which you have" % ", ".join(tree.nodes[s].title for s in known))
        if len(shared) >= 2:
            why.append("the same ground as your work (%s)" % ", ".join(shared))
        if node.id in route:
            why.append("on the route to a goal")
        why.append("open now" if not waiting else "opens once %s is ready (60%% solid)" % ", ".join(
            tree.nodes[s].title for s in waiting))
        rows.append((-score, node.id, node, why))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [(node, why) for _, _, node, why in rows[:n]]


def frontier_text(repo, tree, state, n: int = 5) -> str:
    picks = frontier(repo, tree, state, n)
    if not picks:
        return "No frontier yet: it opens from skills you have studied, once half their topics are consolidating."
    lines = ["The frontier, best first:"]
    for node, why in picks:
        lines.append("  %s | %s (%s%s)" % (node.id, node.title, node.track,
                                          (", about %dh" % node.est_hours) if node.est_hours else ""))
        lines.append("      %s" % (node.summary or "").strip())
        lines.append("      why: %s" % "; ".join(why))
    return "\n".join(lines)
