"""GATE revision: subject passes, the volume of numericals, and a revision pack (formula sheet and error book).

A pass is one full revision of a subject; the gate-strategist plans them (`gate pass <subject> <n> --planned
DATE`) and the learner marks them done. Numericals count, per topic with `[N]` objectives, the numerical
questions answered right: verified `nat` items and `nat` questions of practice sets. The revision pack is
Markdown built from the learner's own notes (their `## Formulas` sections) and recorded mistakes; it holds no
item key or solution, because those items come back for review.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

from . import gateinfo
from .store import Repo, write_text
from .util import CalError, table


# ---------------------------------------------------------------- passes


def set_pass(repo: Repo, tree, state, subject: str, n, planned: str | None, done: bool, on: str | None, when) -> str:
    node = tree.get(subject)
    if not node.track.startswith("gate"):
        raise CalError("revision passes are for GATE subjects; %s is on the %s track" % (node.id, node.track))
    try:
        n = int(n)
    except (TypeError, ValueError):
        raise CalError("the pass is a number: gate pass %s 2 --planned 2026-12-10" % node.id)
    if n < 1 or n > 9:
        raise CalError("passes are numbered 1 to 9")
    if not planned and not done:
        raise CalError("say --planned DATE or --done [--date DATE]")
    fields = {}
    for name, text in (("planned", planned), ("done", (on or when.date().isoformat()) if done else None)):
        if text:
            try:
                fields[name] = date.fromisoformat(str(text)).isoformat()
            except ValueError:
                raise CalError("dates look like 2026-12-10; got %r" % text)
    repo.append("gate_pass", skill=node.id, n=n, **fields)
    return "%s pass %d: %s" % (node.id, n, ", ".join("%s %s" % kv for kv in fields.items()))


def pass_text(state, skill_id: str) -> str:
    """'pass 1 done 2026-11-20 · pass 2 planned 2026-12-10', or '' with none."""
    rows = state.passes.get(skill_id) or {}
    bits = []
    for n in sorted(rows, key=int):
        r = rows[n]
        bits.append("pass %s %s" % (n, ("done %s" % r["done"]) if r.get("done") else "planned %s" % r.get("planned")))
    return " · ".join(bits)


# ---------------------------------------------------------------- numericals


def numerical_topics(tree, skill_id: str) -> list:
    """Topic keys of a skill that have at least one `[N]` objective."""
    return [t.key for t in tree.get(skill_id).topics if any(o["strand"] == "N" for o in t.objectives())]


def numericals(state, tree, key: str) -> int:
    """Numerical questions on a topic answered right: verified nat items, and nat practice questions."""
    from . import practice

    count = 0
    for it in state.items.values():
        if it.type == "nat" and it.topics and it.topics[0] == key and it.status == "verified":
            count += min(it.n_ok, 1)
    for pset in state.practice.values():
        for q, rec in pset["qs"].items():
            m = practice.topics_for(pset, q)
            if m["type"] == "nat" and key in m["topics"] and rec.get("result") == "solved":
                count += 1
    return count


def target(repo: Repo) -> int:
    return int(repo.cfg("numericals.target", 10))


def aim_date(repo: Repo):
    """The day the numericals target is meant to be met: when the final phase before the paper starts."""
    days = [gateinfo.exam_date(repo, p) for p in gateinfo.papers(repo)]
    days = [d for d in days if d is not None]
    if not days:
        return None
    return min(days) - timedelta(days=int(repo.cfg("gate.final_phase_days", 21)))


def numericals_text(repo: Repo, tree, state, subject: str | None = None) -> str:
    from .gate import gate_nodes

    nodes = [tree.get(subject)] if subject else gate_nodes(repo, tree)
    goal = target(repo)
    rows = []
    for node in nodes:
        for key in numerical_topics(tree, node.id):
            rows.append([key, str(numericals(state, tree, key)), str(goal)])
    if not rows:
        return "No topic%s has [N] objectives yet (the deepened GATE syllabi tag them)." % (
            (" of %s" % subject) if subject else "")
    aim = aim_date(repo)
    return table(rows, ["topic", "numericals solved", "aim"], aligns="lrr") + \
        "\n'solved' counts verified nat items answered right and nat practice questions solved%s." % (
            "; aim them by %s, when the final phase starts" % aim.isoformat() if aim else "")


def numericals_low(repo: Repo, tree, state, when):
    """The topic most behind on numericals among those studied at least 3 days ago, or None:
    (key, solved, aim, aim date)."""
    goal = target(repo)
    worst = None
    for skill_id in state.enrolled_skills():
        if not tree.get(skill_id).track.startswith("gate"):
            continue
        for key in numerical_topics(tree, skill_id):
            ts = state.topics.get(key)
            began = ts and (ts.first_ts or ts.covered_ts)
            if not began or when - began < timedelta(days=3):
                continue
            n = numericals(state, tree, key)
            if n * 2 < goal and (worst is None or n < worst[1]):
                worst = (key, n)
    if worst is None:
        return None
    return worst[0], worst[1], goal, aim_date(repo)


# ---------------------------------------------------------------- revision pack


def _formulas(repo: Repo, tree, skill_id: str) -> list:
    """The `## Formulas` (or `## Key results`) sections of the skill's notes fragments, in topic order."""
    from . import notes

    out = []
    for topic in tree.get(skill_id).topics:
        path = notes.fragment_path(repo, tree, topic.key, create=False)
        if not path or not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        keep, grab = [], False
        for line in lines:
            if line.startswith("## "):
                grab = line[3:].strip().lower() in ("formulas", "formulae", "key results", "key formulas")
                continue
            if line.startswith("# "):
                grab = False
            if grab:
                keep.append(line)
        body = "\n".join(keep).strip()
        if body:
            out.append((topic, body))
    return out


def pack(repo: Repo, tree, state, subject: str, pdf: bool = False) -> str:
    node = tree.get(subject)
    if not node.track.startswith("gate"):
        raise CalError("revision packs are for GATE subjects; %s is on the %s track" % (node.id, node.track))
    titles = {t.key: t.title for t in node.topics}
    lines = ["# %s: revision pack" % node.title, "",
             "Built by the engine from your own notes and your recorded mistakes (`gate pack %s`). It holds no "
             "question keys or solutions: those questions come back for review." % node.id, "",
             "## Formula sheet", ""]
    formulas = _formulas(repo, tree, node.id)
    if formulas:
        for topic, body in formulas:
            lines += ["### %s" % topic.title, "", body, ""]
    else:
        lines += ["No formulas yet: add a `## Formulas` section to a topic's notes fragment (notes skill).", ""]
    lines += ["## Error book", ""]
    mine = [m for m in state.mistakes if m["topic"] in titles]
    if mine:
        rows = []
        for m in mine:
            src = str(m.get("src") or "")
            where = "practice " + src[3:] if src.startswith("ps:") else ("item " + src if src.startswith("it-") else
                                                                          src or "oral check")
            rows.append([m["ts"].date().isoformat(), titles[m["topic"]], m["err"], (m.get("note") or "").replace("|", "/"),
                         where])
        lines.append("| date | topic | mistake | your note | where |")
        lines.append("|---|---|---|---|---|")
        lines += ["| %s |" % " | ".join(r) for r in rows]
        kinds = {}
        for m in mine:
            kinds[m["err"]] = kinds.get(m["err"], 0) + 1
        lines += ["", "By kind: %s." % ", ".join("%s %d" % kv for kv in sorted(kinds.items(), key=lambda kv: -kv[1]))]
    else:
        lines.append("No mistakes recorded on this subject yet.")
    folder = os.path.join(repo.root, "learner", "notes", node.id)
    path = os.path.join(folder, "revision-pack.md")
    write_text(path, "\n".join(lines) + "\n")
    out = "revision pack written: %s (%d formula section(s), %d mistake(s))" % (repo.rel(path), len(formulas), len(mine))
    if pdf:
        from . import mdbook

        out += "\n" + mdbook.pdf(repo, path, os.path.join(folder, "revision-pack.pdf"), base=folder)
    return out
