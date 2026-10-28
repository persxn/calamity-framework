"""The engine's task queue: work around the studying that falls due, each with its own cooldown.

    weekly-review   no weekly review (coach skill) for 7 days
    gate-plan       learner/gate/plan.md's review_on has come, or a mock was recorded after the plan
    cp-plan         learner/cp/plan.md's review_on has come
    stock           topics coming up in the next two days lack unseen verified items
    notes           notes sections to write or rewrite
    push            learner commits not pushed for 3 days (or changes not committed for 3 days)
    numericals      a GATE topic far behind on numerical questions
    revise          watched lectures whose topics have faded
    mocks           GATE mock records older than 30 days (the opportunity-scout refreshes them)

`tasks` lists what is due, most pressing first; the brief shows the top two and `/day` takes one that
belongs to the block. `tasks done <id>` records that it was handled and `tasks snooze <id> [--days N]`
puts it off; either hides it for its cooldown (both are events, so every machine agrees). A task that
is due again after its cooldown comes back by itself.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import date, timedelta

from . import fm
from .store import read_text
from .util import CalError, parse_ts

# id: (cooldown days after done, what the brief says, what handles it)
TASKS = {
    "weekly-review": (7, "weekly review due", "/coach (weekly review)"),
    "gate-plan": (7, "GATE plan review due", "/gate (the gate-strategist revises the plan)"),
    "cp-plan": (7, "CP plan review due", "/cp (the cp-coach revises the plan)"),
    "stock": (1, "item bank not stocked for the next two days", "/stock, or the examiner and checker now"),
    "notes": (2, "notes to write up", "/notes"),
    "push": (1, "progress not pushed", "/sync"),
    "numericals": (7, "numericals behind", "/gate numericals, then practice"),
    "revise": (3, "lectures to revise", "source revise"),
    "mocks": (14, "GATE mock records stale", "/gate (the opportunity-scout refreshes them)"),
}
ORDER = tuple(TASKS)


def _plan_review(repo, rel: str, today: date):
    path = os.path.join(repo.learner, *rel.split("/"))
    if not os.path.isfile(path):
        return None
    try:
        meta, _ = fm.parse(read_text(path))
    except (CalError, UnicodeDecodeError, OSError):
        return None
    raw = str(meta.get("review_on") or "").strip()
    try:
        due = date.fromisoformat(raw[:10])
    except ValueError:
        return None
    return due if due <= today else None


def _git(repo, *args):
    try:
        proc = subprocess.run(["git"] + list(args), cwd=repo.root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.decode("utf-8", "replace").strip() if proc.returncode == 0 else None


def _unpushed_days(repo, when):
    """Days since the oldest learner commit not on the upstream, or since the last learner commit when
    learner/ has changes not committed; None when everything is pushed (or this is no git checkout)."""
    if not os.path.exists(os.path.join(repo.root, ".git")):
        return None
    stamps = _git(repo, "log", "--format=%ct", "@{u}..HEAD", "--", "learner")
    oldest = None
    if stamps:
        oldest = min(int(s) for s in stamps.split() if s.isdigit())
    dirty = _git(repo, "status", "--porcelain", "--", "learner")
    if dirty and oldest is None:
        last = _git(repo, "log", "-1", "--format=%ct", "--", "learner")
        oldest = int(last) if last and last.isdigit() else None
    if oldest is None:
        return None
    return (when.timestamp() - oldest) / 86400.0


def handled(state) -> dict:
    """{task id: the date until which it is hidden}, from task events."""
    return dict(state.tasks)


def due(repo, tree, state, when) -> list:
    """[(id, detail)] of tasks due now, most pressing first."""
    from . import day as day_mod

    today = day_mod.learner_date(repo, when)
    hidden = handled(state)
    out = []

    def add(tid, detail):
        until = hidden.get(tid)
        if until and until > today.isoformat():
            return
        out.append((tid, detail))

    last_review = state.last_task.get("weekly-review")
    if repo.onboarded() and state.days and (last_review is None or last_review <= (today - timedelta(days=7)).isoformat()):
        first = min(state.days)
        if first <= (today - timedelta(days=6)).isoformat():
            add("weekly-review", "last one %s" % (last_review or "never"))
    gate_due = _plan_review(repo, "gate/plan.md", today)
    plan_path = os.path.join(repo.learner, "gate", "plan.md")
    if gate_due:
        add("gate-plan", "review_on %s" % gate_due.isoformat())
    elif os.path.isfile(plan_path) and state.mocks:
        written = os.path.getmtime(plan_path)
        late = [m for m in state.mocks if parse_ts(m["ts"]).timestamp() > written]
        if late:
            add("gate-plan", "a mock was recorded after the plan was written")
    cp_due = _plan_review(repo, "cp/plan.md", today)
    if cp_due:
        add("cp-plan", "review_on %s" % cp_due.isoformat())
    if state.enrolled_skills():
        from .session import needed_topics

        need = needed_topics(repo, tree, state, when, n=50, days=2, per_topic=1)
        if need:
            add("stock", "%d topic(s), first %s" % (len(need), need[0][0]))
        from . import notes

        todo = 0
        for skill_id in state.enrolled_skills():
            try:
                todo += sum(1 for r in notes.rows(repo, tree, skill_id) if r["state"] in ("to write", "stale"))
            except (CalError, OSError):
                continue
        if todo:
            add("notes", "%d section(s) to write or rewrite" % todo)
    days = _unpushed_days(repo, when)
    if days is not None and days >= 3:
        add("push", "learner changes waiting %d days" % int(days))
    if any(tree.nodes[s].track.startswith("gate") for s in state.enrolled_skills() if s in tree.nodes):
        from . import revision

        low = revision.numericals_low(repo, tree, state, when)
        if low:
            add("numericals", "%s at %d" % (low[0], low[1]))
        from .career import STALE_DAYS

        stale = [r for r in state.career.values() if r.get("kind") == "gate-mock"
                 and (when.date() - date.fromisoformat(r["fetched"])).days > STALE_DAYS]
        if stale:
            add("mocks", "%d record(s) older than 30 days" % len(stale))
    if state.src:
        from . import sources

        fading = sources.revise(repo, state, tree, when, n=3)
        if fading:
            first = fading[0]
            add("revise", "%d lecture(s), first %s %s" % (len(fading), first[0], getattr(first[1], "id", first[1])))
    return out


def text(repo, tree, state, when) -> str:
    rows = due(repo, tree, state, when)
    if not rows:
        return "no tasks due"
    lines = []
    for tid, detail in rows:
        _, what, handler = TASKS[tid]
        lines.append("%-14s %s (%s) -> %s" % (tid, what, detail, handler))
    lines.append("tasks done <id> when one is handled; tasks snooze <id> [--days N] to put it off")
    return "\n".join(lines)


def brief_line(repo, tree, state, when):
    rows = due(repo, tree, state, when)
    if not rows:
        return None
    shown = ["%s (%s)" % (TASKS[t][1], TASKS[t][2]) for t, _ in rows[:2]]
    more = (" · +%d more (tasks)" % (len(rows) - 2)) if len(rows) > 2 else ""
    return "Tasks: " + " · ".join(shown) + more


def mark(repo, tree, state, when, tid: str, action: str, days: int | None = None) -> str:
    if tid not in TASKS:
        raise CalError("no task %s (tasks: %s)" % (tid, ", ".join(ORDER)))
    from . import day as day_mod

    today = day_mod.learner_date(repo, when)
    span = days if days is not None else (TASKS[tid][0] if action == "done" else 1)
    until = (today + timedelta(days=span)).isoformat()
    repo.append("task", when=when, task=tid, action=action, until=until)
    return "%s %s: hidden until %s" % (tid, "done" if action == "done" else "snoozed", until)
