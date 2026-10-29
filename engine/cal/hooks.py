"""The hooks Claude Code runs around a study session (setup --hook installs them in .claude/settings.local.json).

    SessionStart       brief --hook        the brief; after a compaction, where the session was; with
                                           `auto.start` on, opens /day (never in a clone with no learner)
    UserPromptSubmit   guard prompt        one routing line for a request a skill owns; `!slow`-style
                                           feedback recorded; "contest running" for a live Codeforces link
    PreToolUse         guard tool          the key guard (cal.guard), and slices instead of big learner files
    Stop               guard stop          blocks a turn's end once when an answer was given but not
                                           recorded, or a topic was taught today with no notes fragment
    PreCompact         snapshot --session  where the session is, for the SessionStart after the compaction
    SessionEnd         guard end           a session_end event, so session lengths are exact

Every hook reads Claude Code's JSON on stdin, never fails the session (a fault prints nothing), and does
nothing at all with CALAMITY_HOOKS=off, or with CALAMITY_MAINTAIN=1 (a maintenance session), or in a clone
with no learner (the dev clone). The session file .calamity/session.json is machine-local: which skill a
session is running (from its last slash command), when the learner last wrote, and what the Stop guard has
already raised, so it raises each thing once.
"""
from __future__ import annotations

import json
import os
import re

from .store import write_text
from .util import CalError, iso, parse_ts

# The skills whose turns the Stop guard watches: they show items and teach.
WATCHED = ("study", "recall", "day", "mastery-coach", "practice", "boss")
KEEP_SESSIONS = 20

# Requests a skill owns, recognised without a model (first match wins). Each is one line of context.
ROUTES = (
    (r"\b(watched|finished|completed|done with|attended)\b.{0,40}\b(lecture|video|chapter|class|lesson|module)s?\b",
     "log", "record study done elsewhere"),
    (r"\b(worked out|work ?out done|went to the gym|went for a run|did (my )?cardio)\b", "log", "record a workout"),
    (r"\bquiz me\b|\brecall round\b|\bquick (revision|review)\b", "recall", "a review round of what is due"),
    (r"\b(solved|got wrong|skipped|attempted)\b.{0,40}\b(questions?|q\d+|pyqs?|problems? from (the )?(book|pdf))\b",
     "practice", "log questions from outside material"),
    (r"\bwhat (should i do|to do|now|next)\b|\bwhat'?s (left|next) today\b|\bfinish line\b", "today",
     "today's finish line and the next thing"),
    (r"\b(in depth|deep dive|internals of)\b|\bmaster(ing)? [a-z]", "mastery-coach",
     "deep coaching of a tool or topic"),
    (r"\b(dashboard|my progress|roadmap|revision queue|how did (my|the) week go)\b", "dash", "a dashboard"),
    (r"\b(sync|save|back ?up|push) (my )?(progress|record|study log)\b", "sync", "save progress to the learner's repository"),
    (r"\b(remind me|reminders?|notifications?)\b", "remind", "study reminders"),
    (r"\bmocks?\b|\btest series\b|\bgate (plan|target|countdown)\b", "gate", "the GATE companion"),
    (r"\b(jobs?|internships?|placements?|hackathons?|r[eé]sum[eé] (bullets?|points?)|my r[eé]sum[eé]|résumé|"
     r"gsoc|outreachy|open[- ]source programs?|m\.?tech admissions?|psu recruitment)\b", "career", "the career companion"),
    (r"\bcodeforces\b|\bcontest\b|\bcf rating\b|\bupsolve\b", "cp", "the competitive programming coach"),
    (r"\b(explain|teach me|teach myself|eli5|walk me through|help me (understand|learn|with)|break ?down"
     r"|make sense of|get (really )?good at)\b"
     r"|\b(i )?(don'?t|do not|can'?t|cannot) (get|understand|follow|grasp) \w"
     r"|\bconfused about\b"
     r"|\bhow (does|do|did) .{2,60}\bwork(s|ing)?\b|\bwhat (is|are|was|were) (a|an|the) \w", "explain",
     "a deep, from-scratch explanation of a topic"),
)

# Feedback the learner can type into any message: what it records, and the line the tutor gets.
TOKENS = {
    "!slow": ({"pace": "fast"}, "slow down: shorter chunks, one idea at a time"),
    "!fast": ({"pace": "slow"}, "speed up: less repetition, bigger steps"),
    "!deeper": ({"depth": "more"}, "go deeper: the mechanism underneath, not more examples"),
    "!lighter": ({"depth": "less"}, "lighter: the core idea and what it is for, details later"),
    "!example": ({"clarity": "low"}, "give a worked example now, before going on"),
    "!harder": ({"level": "harder"}, "harder questions: the engine's next items stay as they are, so stretch the "
                                     "formative ones"),
    "!easier": ({"level": "easier"}, "easier: step back to the prerequisite, then build up again"),
}
NOTICE = re.compile(r"<task-notification>|^\s*\[SYSTEM NOTIFICATION")
CF_LINK = re.compile(r"codeforces\.com/(?:contest|gym)/(\d+)/problem/|codeforces\.com/problemset/problem/(\d+)/")


def off() -> bool:
    return os.environ.get("CALAMITY_HOOKS", "").strip().lower() in ("off", "0", "false", "no") or \
        os.environ.get("CALAMITY_MAINTAIN", "").strip() not in ("", "0")


# ---------------------------------------------------------------- the session file


def session_path(repo) -> str:
    return os.path.join(repo.local, "session.json")


def load_sessions(repo) -> dict:
    try:
        with open(session_path(repo), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {"sessions": {}}
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), dict):
        return {"sessions": {}}
    return data


def save_sessions(repo, data: dict) -> None:
    sessions = data.get("sessions", {})
    if len(sessions) > KEEP_SESSIONS:
        keep = sorted(sessions, key=lambda k: str(sessions[k].get("seen", "")))[-KEEP_SESSIONS:]
        data["sessions"] = {k: sessions[k] for k in keep}
    try:
        write_text(session_path(repo), json.dumps(data, indent=1, sort_keys=True) + "\n", durable=False)
    except OSError:
        pass


def session_rec(data: dict, sid: str, when) -> dict:
    rec = data["sessions"].setdefault(sid or "-", {})
    rec["seen"] = iso(when)
    return rec


# ---------------------------------------------------------------- UserPromptSubmit


def prompt(repo, tree, payload: dict, when) -> str | None:
    """Context for this prompt (or None), after recording what it says about the session."""
    text = str(payload.get("prompt") or "")
    if NOTICE.search(text):           # Claude Code's own notices (a background task ended): not the learner's words
        return None
    data = load_sessions(repo)
    rec = session_rec(data, str(payload.get("session_id") or ""), when)
    rec["prompt_ts"] = iso(when)
    lines = []
    slash = re.match(r"^\s*/([a-z][\w-]*)", text)
    if slash:
        rec["skill"] = slash.group(1).split(":")[-1]
    said = {}
    hints = []
    for token in re.findall(r"(?<![\w!])![a-z]+\b", text.lower()):
        if token in TOKENS and TOKENS[token][1] not in hints:
            said.update(TOKENS[token][0])
            hints.append(TOKENS[token][1])
    if said:
        repo.append("feedback", when=when, via="prompt", **said)
        lines.append("Calamity: the learner typed feedback (%s), recorded. Now: %s." % (
            " ".join(t for t in TOKENS if TOKENS[t][1] in hints), "; ".join(hints)))
    if CF_LINK.search(text) and repo.prof("cp.handle"):
        from . import cf

        data_cf = cf.load(repo)
        ids = {m.group(1) or m.group(2) for m in CF_LINK.finditer(text)}
        live = [c for c in cf.running(data_cf or {}, when) if str(c.get("id")) in ids]
        if live:
            lines.append("Calamity: contest %s (%s) is running now. During a rated contest give no help of any "
                         "kind with its problems (CLAUDE.md rule 6); offer to review it after the contest ends."
                         % (live[0].get("id"), live[0].get("name", "")))
    if not slash and not said:
        low = text.lower()
        for pattern, skill, what in ROUTES:
            if re.search(pattern, low):
                lines.append("Calamity: this reads like a request for /%s (%s). Use that skill unless the "
                             "learner meant something else." % (skill, what))
                break
    save_sessions(repo, data)
    return "\n".join(lines) or None


# ---------------------------------------------------------------- Stop


def _fragment_written(repo, tree, key: str) -> bool:
    from . import notes

    try:
        path = notes.fragment_path(repo, tree, key, create=False)
    except CalError:
        return True      # a topic no longer in the tree has nothing to save
    return os.path.isfile(path) and not notes._is_blank_fragment(path)


def stop(repo, tree, state, payload: dict, when) -> str | None:
    """The reason to keep the turn going (raised once per session and thing), or None to let it end."""
    if payload.get("stop_hook_active"):
        return None
    data = load_sessions(repo)
    sid = str(payload.get("session_id") or "")
    rec = session_rec(data, sid, when)
    if rec.get("skill") not in WATCHED:
        save_sessions(repo, data)
        return None
    raised = set(rec.get("raised") or [])
    reasons = []
    replied = rec.get("prompt_ts")
    replied = parse_ts(replied) if replied else None
    for it in state.items.values():
        if it.open and not it.open_test and it.shown_ts is not None and replied is not None and it.shown_ts < replied \
                and ("item:" + it.id) not in raised:
            reasons.append(("item:" + it.id, "the learner replied after %s was shown, and no answer is recorded: "
                                             "record it (answer %s ...), or say it was set aside" % (it.id, it.id)))
    today = state.days.get(state.day(when))
    for topic, _, _ in (today.taught if today else []):
        if ("notes:" + topic) not in raised and not _fragment_written(repo, tree, topic):
            reasons.append(("notes:" + topic, "%s was taught today and has no notes fragment yet: save it now "
                                              "(notes fragment %s), so the teaching is not left in chat" % (topic, topic)))
    if not reasons:
        save_sessions(repo, data)
        return None
    rec["raised"] = sorted(raised | {k for k, _ in reasons})
    save_sessions(repo, data)
    return "Calamity: before ending the turn, " + "; and ".join(r for _, r in reasons) + "."


# ---------------------------------------------------------------- PreCompact and SessionStart (compact)


def snapshot(repo, state, payload: dict, when) -> dict:
    """Where the session stands, written before a compaction: its skill, the item in flight, the topic."""
    data = load_sessions(repo)
    sid = str(payload.get("session_id") or "")
    rec = session_rec(data, sid, when)
    open_items = sorted((it for it in state.items.values() if it.open and it.shown_ts is not None),
                        key=lambda it: it.shown_ts)
    item = open_items[-1] if open_items else None
    taught = []
    today = state.days.get(state.day(when))
    if today and today.taught:
        taught = [t for t, _, _ in today.taught]
    snap = {"at": iso(when), "skill": rec.get("skill"), "item": item.id if item else None,
            "item_topic": (item.topics[0] if item and item.topics else None),
            "item_test": item.open_test if item else None, "topic": taught[-1] if taught else None,
            "trigger": payload.get("trigger")}
    rec["snapshot"] = snap
    save_sessions(repo, data)
    return snap


def resume_lines(repo, state, payload: dict) -> list:
    """After a compaction: what the session was doing, so it carries on with the same item."""
    data = load_sessions(repo)
    rec = data["sessions"].get(str(payload.get("session_id") or "")) or {}
    snap = rec.get("snapshot")
    if not snap:
        return []
    out = ["Resumed after compaction (%s):" % snap.get("at", "")[:16].replace("T", " ")]
    if snap.get("skill"):
        out.append("  skill: /%s — carry on with it" % snap["skill"])
    item = snap.get("item")
    if item and item in state.items and state.items[item].open:
        out.append("  item in flight: %s on %s, shown and not answered — show it again with item show %s and wait "
                   "for the answer%s" % (item, snap.get("item_topic") or "?", item,
                                         (" (test %s)" % snap["item_test"]) if snap.get("item_test") else ""))
    elif item:
        out.append("  last item: %s, answered since" % item)
    if snap.get("topic"):
        out.append("  last topic taught today: %s" % snap["topic"])
    return out


# ---------------------------------------------------------------- SessionEnd


def end(repo, payload: dict, when) -> None:
    repo.append("session_end", when=when, reason=str(payload.get("reason") or "")[:20] or None)


# ---------------------------------------------------------------- SessionStart auto-start


def auto_start(repo, payload: dict) -> str | None:
    """The message to open the session with, or None: /day, only when the learner turned `auto.start` on,
    only for a new or cleared session, and never in a clone without a learner or in a maintenance session."""
    if off() or not repo.onboarded():
        return None
    if repo.prof("auto.start") is not True:
        return None
    if str(payload.get("source") or "startup") not in ("startup", "clear"):
        return None
    return "/day"
