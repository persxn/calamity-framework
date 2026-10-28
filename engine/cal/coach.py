"""Deep coaching on the engine: when a unit of the mastery-coach is done, and the duplicate it must not meet.

A unit is a run of a skill's topics that the coach teaches together (its curriculum lives in
learner/coach/<topic>/curriculum.md and names the topic keys). It is done when every topic in it has
reached `consolidating` (or beyond) on verified items, and the learner has explained at least one of
them back in their own words (`observe "..." --tag explain --topic <key>`). Questions the coach asks
inline while teaching are formative and decide nothing; only the engine's items do.
"""
from __future__ import annotations

import os

from .util import CalError

SECURED = ("consolidating", "solid", "mastered", "known", "ready")


def unit_text(tree, state, skill: str, topics) -> str:
    node = tree.get(skill)
    if not node.topics:
        raise CalError("%s has no topics yet: write its syllabus first (curriculum-architect)" % skill)
    known = {t.id: t.key for t in node.topics}
    keys = []
    for word in topics or [t.id for t in node.topics]:
        tid = word.split("/", 1)[1] if word.startswith(skill + "/") else word
        if tid not in known:
            raise CalError("%s has no topic %s" % (skill, word))
        keys.append(known[tid])
    explained = {state.canon(str(n["topic"])) for n in state.notes if n.get("tag") == "explain" and n.get("topic")}
    width = max(len(k.split("/", 1)[1]) for k in keys)
    lines = ["unit of %s: %d topic%s" % (skill, len(keys), "" if len(keys) == 1 else "s")]
    behind = []
    for key in keys:
        status = state.topic_status(key)
        if status not in SECURED:
            behind.append(key.split("/", 1)[1])
        lines.append("  %s  %-13s %s" % (key.split("/", 1)[1].ljust(width), status,
                                         "explained back" if key in explained else ""))
    missing = []
    if behind:
        missing.append("%s not yet consolidating" % ", ".join(behind))
    if not any(k in explained for k in keys):
        missing.append('no explain-back yet (observe "..." --tag explain --topic <key>)')
    lines.append("UNIT DONE" if not missing else "UNIT OPEN: " + "; ".join(missing))
    return "\n".join(lines)


def claude_home() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def duplicates(names=("mastery-coach",)) -> list:
    """Copies of the framework's companion skills installed for the whole account (for instance synced from
    claude.ai into ~/.claude/skills/), which compete with the engine-backed ones for the same requests."""
    base = os.path.join(claude_home(), "skills")
    found = []
    if not os.path.isdir(base):
        return found
    for root, dirs, _ in os.walk(base):
        depth = os.path.relpath(root, base).count(os.sep)
        for name in dirs:
            if name in names and os.path.isfile(os.path.join(root, name, "SKILL.md")):
                found.append(os.path.join(root, name))
        if depth >= 2:
            dirs[:] = []
    return sorted(found)
