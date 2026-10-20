"""A suggested Claude Code model and effort for the next block of work, as one line at no model cost.

Nothing in this repository can change the conversation's model: only the learner can, with
`/model` and `/effort`. So the engine, which already knows what comes next, names a setting and
the learner decides. The table is judgement, not measurement, and the line says so: it lives in
framework/config.md (`advice.*`), a learner overrides it with `cfg.advice.<kind>` and turns it
off with `cfg.advice false`.

Agents run with `model: inherit`, so the examiner and checker get the session's model. That is
why item stocking (writing and checking items) asks for the stronger setting: the study skill
stocks the bank first, and the line after it suggests the lighter setting for reviews.
"""
from __future__ import annotations

from .store import Repo

# next action -> (tier in config.md, what the block is, in a few words)
BLOCKS = {
    "review": ("light", "reviews"),
    "recall": ("light", "the surprise recall"),
    "watch": ("light", "a lecture, then its test"),
    "wind-down": ("light", "reviews only"),
    "done": ("light", "reviews and notes"),
    "new": ("teach", "teaching a new topic"),
    "stock": ("heavy", "writing and checking items"),
    "syllabus": ("heavy", "writing a syllabus"),
    "boss": ("heavy", "a boss test or project"),
    "plan": ("heavy", "a GATE or CP plan"),
}
TAIL = "(a suggestion, not measured)"


def enabled(repo: Repo) -> bool:
    return bool(repo.cfg("advice", True))


def setting(repo: Repo, tier: str):
    """(model, effort) for a tier; empty strings mean 'keep the learner's usual setting'."""
    words = str(repo.cfg("advice.%s" % tier, "") or "").split()
    return (words[0] if words else ""), (words[1] if len(words) > 1 else "")


def current_text(current) -> str:
    """'sonnet, medium' from what Claude Code reported (hook or status-line input), or ''."""
    if not isinstance(current, dict):
        return ""
    model = current.get("model")
    if isinstance(model, dict):
        model = model.get("display_name") or model.get("id")
    effort = current.get("effort")
    if isinstance(effort, dict):
        effort = effort.get("level")
    parts = [str(x) for x in (model, effort) if isinstance(x, str) and x]
    return ", ".join(parts)


def fits(current, model: str, effort: str) -> bool:
    """Whether the reported setting already matches the suggestion (an alias such as 'sonnet' is
    matched against the model's id or display name)."""
    now = current_text(current).lower()
    if not now:
        return False
    return (not model or model.lower() in now) and (not effort or effort.lower() in now.split(", ")[-1:])


def line(repo: Repo, block: str, current=None, then: str | None = None) -> str:
    """'settings: reviews next; suggested /model sonnet, /effort medium (a suggestion, not measured)',
    or '' when advice is off or the block has no suggestion."""
    if block not in BLOCKS or not enabled(repo):
        return ""
    tier, what = BLOCKS[block]
    model, effort = setting(repo, tier)
    if not model and not effort:
        text = "settings: %s next; keep your usual /model and /effort" % what
    else:
        wanted = ", ".join(x for x in ("/model %s" % model if model else "", "/effort %s" % effort if effort else "") if x)
        if fits(current, model, effort):
            text = "settings: %s next; your current setting (%s) fits" % (what, current_text(current))
        else:
            text = "settings: %s next; suggested %s" % (what, wanted)
    if then and then in BLOCKS:
        t_model, t_effort = setting(repo, BLOCKS[then][0])
        if (t_model, t_effort) != (model, effort):
            after = " ".join(x for x in (t_model, t_effort) if x) or "your usual setting"
            text += ", then %s for %s" % (after, BLOCKS[then][1])
    now = current_text(current)
    if now and "fits" not in text:
        text += "; now on %s" % now
    return "%s %s" % (text, TAIL)


def short(repo: Repo, block: str, current=None) -> str:
    """For the status line: 'try sonnet·medium', or '' when the current setting fits or advice is off."""
    if block not in BLOCKS or not enabled(repo):
        return ""
    model, effort = setting(repo, BLOCKS[block][0])
    if (not model and not effort) or fits(current, model, effort):
        return ""
    return "try " + "·".join(x for x in (model, effort) if x)
