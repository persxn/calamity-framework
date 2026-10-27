"""Today's plan, the finish line, the single next action, weaving, and the session brief.

There is no timetable. The plan is a rolling answer to "what next?", built
from what is due, what is unlocked and how much new material today's quota
still allows. The day is finished when the finish line is reached; it never
depends on hours spent.
"""
from __future__ import annotations

from . import sources
from .store import Repo
from .util import csv_list, day_bounds, fmt_delta, fmt_minutes, in_window, minutes_until, parse_hhmm, utc

GLYPH = {"mastered": "✓", "known": "✓", "ready": "◕", "active": "◐", "paused": "‖",
         "available": "○", "locked": "·", "dropped": "✗"}
GLYPH_ASCII = {"mastered": "#", "known": "#", "ready": "+", "active": "~", "paused": "=",
               "available": "o", "locked": ".", "dropped": "x"}


# ---------------------------------------------------------------- sleep guard


def sleep_info(repo: Repo, when) -> dict:
    start = parse_hhmm(repo.prof("sleep.start"))
    end = parse_hhmm(repo.prof("sleep.end"))
    if start is None or end is None:
        return {"set": False, "inside": False, "in_guard": False}
    minute = when.hour * 60 + when.minute
    inside = in_window(minute, start, end)
    guard = int(repo.cfg("sleep_guard_minutes", 60))
    to_sleep = minutes_until(minute, start)
    return {
        "set": True,
        "inside": inside,
        "in_guard": (not inside) and to_sleep <= guard,
        "minutes_to_sleep": to_sleep,
        "minutes_to_cutoff": max(0, to_sleep - guard),
        "start": str(repo.prof("sleep.start")),
        "end": str(repo.prof("sleep.end")),
        "guard": guard,
    }


def day_end(repo: Repo, when):
    """(start, end) of the learner day that contains `when`."""
    return day_bounds(when, int(repo.cfg("day_start_hour", 4)))


# ---------------------------------------------------------------- new material


def _untouched(state, key: str) -> bool:
    ts = state.topics.get(key)
    return ts is None or ts.card is None


def _under_way(tree, state, skill_id: str) -> bool:
    """Some of the skill's topics have been answered and some have not."""
    topics = tree.nodes[skill_id].topics
    done = sum(1 for t in topics if not _untouched(state, t.key))
    return 0 < done < len(topics)


def skill_order(repo: Repo, tree, state, when) -> list:
    """Enrolled skills in the order new material should be drawn from them."""
    enrolled = state.enrolled_skills()
    base = []
    gate_skills = [s for s in enrolled if tree.nodes[s].track.startswith("gate")]
    if gate_skills:
        from . import gate

        rank = {row["skill"]: i for i, row in enumerate(gate.triage(repo, tree, state, when))}
        # triage order, except that a subject already under way is finished before another is opened
        base = sorted(gate_skills, key=lambda s: (not _under_way(tree, state, s), rank.get(s, len(rank)), s))
    base += [s for s in enrolled if s not in base]
    focus = focus_skills(repo, tree, base)
    return focus + [s for s in base if s not in focus]


def focus_skills(repo: Repo, tree, enrolled) -> list:
    """Enrolled skills the learner put in focus: skill ids, track ids, or 'gate' for every GATE track."""
    out = []
    for entry in csv_list(repo.prof("focus")):
        if entry in enrolled:
            hits = [entry]
        else:
            hits = [s for s in enrolled
                    if tree.nodes[s].track == entry or (entry == "gate" and tree.nodes[s].track.startswith("gate"))]
        out.extend(s for s in hits if s not in out)
    return out


def lanes(repo: Repo, tree, state, when, waiting=None) -> list:
    """Enrolled skills grouped into lanes that take turns at new material: [(tier, [skill ids])].

    Every skill is a lane of its own, except GATE subjects, which are worked through one after
    another: those that follow a course share one lane (the course sets their order), and those
    studied without one share another. Lanes in the learner's focus (tier 0) come before the rest.
    """
    if waiting is None:
        waiting = sources.waiting_skills(repo, state, tree)
    order = skill_order(repo, tree, state, when)
    focus = set(focus_skills(repo, tree, order))
    out, index = [], {}
    for skill_id in order:
        tier = 0 if skill_id in focus else 1
        if tree.nodes[skill_id].track.startswith("gate"):
            lane = (tier, "gate course" if skill_id in waiting else "gate")
        else:
            lane = (tier, skill_id)
        if lane not in index:
            index[lane] = len(out)
            out.append((tier, []))
        out[index[lane]][1].append(skill_id)
    return out


def new_candidates(repo: Repo, tree, state, when, skill: str | None = None, limit: int = 12,
                   lookahead: bool = False, pending: bool = True) -> list:
    """Topics to start next, in the order `next` serves them.

    A topic can be started when it has never been answered and the topics it needs have been.
    In a skill studied from a source a topic waits for its lecture, and once that lecture is
    logged it is tested before anything else.

    Skills take turns (see `lanes`): the lane that has had the least new material today goes
    next, so two skills studied side by side alternate.

    `lookahead` also lists what cannot be started yet but will be as the day goes on: topics
    whose prerequisites come earlier in the same syllabus and, with `pending`, topics that the
    next unlogged lectures open. The day's target and the item bank are worked out from it.
    """
    waiting = sources.waiting_skills(repo, state, tree)
    upcoming = sources.upcoming_topics(repo, state, tree, per_source=limit) if (lookahead and pending) else []
    groups = [(0, [skill])] if skill else lanes(repo, tree, state, when, waiting)
    day = state.day(when)
    urgent, tiers = [], {}
    for tier, skills in groups:
        rows, taken, listed = [], 0, set()
        for skill_id in skills:
            node = tree.nodes.get(skill_id)
            if node is None or node.dropped:
                continue
            for topic in node.topics:
                ts = state.topics.get(topic.key)
                if ts is not None and ts.card is not None:
                    taken += 1 if ts.first_day == day else 0
                    continue
                covered = ts is not None and ts.covered_ts is not None
                if not covered and state.deferred(topic):
                    continue                # banded well above the learner's rating: later
                watched = covered and ts.covered_by == "source"
                row = {"key": topic.key, "skill": skill_id, "title": topic.title, "covered": covered, "led": watched}
                if watched:
                    urgent.append(row)      # a lecture that was watched is tested before anything else
                    listed.add(topic.key)
                    continue
                if skill_id in waiting and not covered:
                    continue                # its lecture has not been logged yet
                if not lookahead and any(_untouched(state, need if "/" in need else "%s/%s" % (skill_id, need))
                                         for need in topic.needs):
                    continue
                rows.append(row)
                listed.add(topic.key)
        for key in upcoming:                # then what the next lectures open, in lecture order
            skill_id = key.split("/", 1)[0]
            if skill_id in skills and key not in listed and not tree.nodes[skill_id].dropped:
                listed.add(key)
                rows.append({"key": key, "skill": skill_id, "title": tree.topic(key).title,
                             "covered": False, "led": True})
        if rows:
            tiers.setdefault(tier, []).append([rows, taken])
    out = urgent[:limit]
    for tier in sorted(tiers):
        group = tiers[tier]
        pos = [0] * len(group)
        while len(out) < limit:
            live = [i for i in range(len(group)) if pos[i] < len(group[i][0])]
            if not live:
                break
            i = min(live, key=lambda j: (group[j][1], j))
            out.append(group[i][0][pos[i]])
            pos[i] += 1
            group[i][1] += 1
    return out


# ---------------------------------------------------------------- today


def today(repo: Repo, tree, state, when) -> dict:
    n = state.today_numbers(when)
    quota = max(0, int(repo.cfg("new_per_day", 8)))
    lecture_quota = max(0, int(repo.cfg("lectures_per_day", 0)))
    cands = new_candidates(repo, tree, state, when, limit=max(quota, 1) + 4)
    # The day's target counts what today's work will open as well as what can be started now.
    # Topics behind lectures not yet watched count only when no lecture quota is set: with a
    # quota, the lectures are a line of the finish line themselves.
    ahead = new_candidates(repo, tree, state, when, limit=max(quota, 1) + 4, lookahead=True,
                           pending=(lecture_quota == 0))
    new_target = min(quota, n["new_done"] + len(ahead))
    new_left = max(0, new_target - n["new_done"])
    # A lecture that was watched is tested whatever the quota says: count the ones beyond it.
    tests_left = max(0, sum(1 for c in cands if c["led"]) - new_left)
    reviews_left = max(0, n["reviews_needed"] - n["due_done"])
    ds = state.days.get(n["day"])
    lectures_done = ds.src_done if ds else 0
    pending_lectures = sources.next_items(repo, state, tree, limit=max(3, lecture_quota))
    # the lectures line of the finish line never asks for more lectures than the sources still hold
    lecture_target = min(lecture_quota, lectures_done + len(pending_lectures))
    lectures_left = max(0, lecture_target - lectures_done)
    pending_lectures = pending_lectures[:3]
    relearn = n["relearn"]
    finished = (
        reviews_left == 0 and not relearn and new_left == 0 and tests_left == 0 and lectures_left == 0
        and (n["attempts"] > 0 or lectures_done > 0)
    )
    nothing_to_do = (
        n["due_total"] == 0 and not relearn and new_target == 0 and tests_left == 0 and lecture_target == 0
        and not pending_lectures
    )
    return {
        "n": n,
        "quota": quota,
        "new_target": new_target,
        "new_left": new_left,
        "tests_left": tests_left,
        "reviews_left": reviews_left,
        "relearn": relearn,
        "lecture_quota": lecture_quota,
        "lecture_target": lecture_target,
        "lectures_done": lectures_done,
        "lectures_left": lectures_left,
        "pending_lectures": pending_lectures,
        "finished": finished,
        "nothing_to_do": nothing_to_do,
        "candidates": cands,
        "sleep": sleep_info(repo, when),
        "boss_ready": boss_ready(repo, tree, state),
    }


def finish_text(t: dict) -> str:
    if t["finished"]:
        return "finish line reached"
    if t["nothing_to_do"]:
        return "nothing scheduled today"
    left = []
    if t["reviews_left"]:
        left.append("%d review%s" % (t["reviews_left"], "" if t["reviews_left"] == 1 else "s"))
    if t["relearn"]:
        left.append("%d to re-answer correctly" % len(t["relearn"]))
    if t["new_left"]:
        left.append("%d new" % t["new_left"])
    if t["tests_left"]:
        left.append("%d watched lecture%s to test" % (t["tests_left"], "" if t["tests_left"] == 1 else "s"))
    if t["lectures_left"]:
        left.append("%d lecture%s" % (t["lectures_left"], "" if t["lectures_left"] == 1 else "s"))
    if not left:
        return "finish line: nothing counted yet today"
    return "finish line: " + ", ".join(left) + " to go"


def today_line(t: dict) -> str:
    n = t["n"]
    parts = ["reviews %d/%d" % (n["due_done"], n["due_total"]), "new %d/%d" % (n["new_done"], t["new_target"])]
    if t["lecture_target"]:
        parts.append("lectures %d/%d" % (t["lectures_done"], t["lecture_target"]))
    return "today: " + " · ".join(parts) + " · " + finish_text(t)


def boss_ready(repo: Repo, tree, state) -> list:
    """Enrolled skills whose every topic is at least solid and whose boss is not passed yet.

    Topics deferred to a later Codeforces rating (`State.deferred`) are not waited for.
    """
    out = []
    for skill_id in state.enrolled_skills():
        node = tree.nodes[skill_id]
        sk = state.skills[skill_id]
        if sk.boss_ok or sk.mode == "brushup":
            continue
        counts = state.skill_counts(skill_id, in_scope=True)
        if node.kind == "milestone" and not counts["total"]:
            if state.unlocked(skill_id):
                out.append(skill_id)
        elif node.has_boss and counts["total"] and counts["solid"] + counts["mastered"] == counts["total"]:
            out.append(skill_id)
    return out


# ---------------------------------------------------------------- next action


def next_action(repo: Repo, tree, state, when, skill: str | None = None, only: bool = False) -> dict:
    """Decide the single next thing to do. `skill` narrows new material to one
    skill; reviews stay global unless `only` is set."""
    if not repo.onboarded():
        return {"action": "onboard"}
    t = today(repo, tree, state, when)
    if not state.enrolled_skills() and not state.scheduled_topics():
        return {"action": "enroll", "today": t}
    sleep = t["sleep"]
    due = state.due(when)
    if only and skill:
        due = [(k, ts) for k, ts in due if k.split("/", 1)[0] == skill]
    if sleep["inside"]:
        return {"action": "sleep", "today": t, "due": len(due)}
    relearn_due = [(k, ts) for k, ts in due if k in t["relearn"]]
    if relearn_due:
        key, ts = relearn_due[0]
        return {"action": "review", "topic": key, "why": "failed earlier today; answer it again", "today": t,
                "queue": len(due)}
    if due:
        key, ts = due[0]
        return {"action": "review", "topic": key, "why": "most forgotten of %d due" % len(due), "today": t,
                "queue": len(due)}
    cands = t["candidates"] if not skill else new_candidates(repo, tree, state, when, skill=skill, limit=4)
    quota_open = t["n"]["new_done"] < t["quota"]
    # the quota limits what is taught in a day; a lecture already watched is tested regardless
    startable = bool(cands) and (quota_open or cands[0]["led"])
    lectures = t["pending_lectures"]
    if skill and lectures:
        behind = [c for c in new_candidates(repo, tree, state, when, skill=skill, limit=4, lookahead=True)
                  if c["led"] and not c["covered"]]
        if behind:      # the lectures that lead to this skill's next topic, unmapped ones included
            lectures = sources.lectures_toward(repo, state, tree, behind[0]["key"]) or lectures
    if startable and not sleep["in_guard"]:
        c = cands[0]
        if not c["led"] and (t["lecture_quota"] == 0 or t["lectures_left"] > 0):
            # Whose turn is it? If it belongs to a skill whose next topic sits behind a lecture
            # that has not been watched, the lecture is the next thing to do.
            turn = new_candidates(repo, tree, state, when, skill=skill, limit=1, lookahead=True)
            if turn and all(turn[0]["key"] != x["key"] for x in cands):
                toward = sources.lectures_toward(repo, state, tree, turn[0]["key"])
                if toward:
                    return {"action": "watch", "items": toward, "today": t, "turn": turn[0]["key"], "meanwhile": c}
        why = "lecture logged, not tested yet" if c["led"] else "next unlocked topic"
        return {"action": "new", "topic": c["key"], "why": why, "covered": c["covered"], "led": c["led"],
                "today": t}
    if lectures and (t["lectures_left"] or not cands) and not t["finished"]:
        return {"action": "watch", "items": lectures, "today": t}
    if startable and sleep["in_guard"]:
        return {"action": "wind-down", "today": t}
    if t["relearn"]:
        key = t["relearn"][0]
        return {"action": "review", "topic": key, "why": "failed a few minutes ago; try it again", "today": t,
                "queue": 1}
    if t["boss_ready"]:
        return {"action": "boss", "skill": t["boss_ready"][0], "today": t}
    if cands and not quota_open:
        return {"action": "done", "today": t, "extra": cands[0]["key"]}
    # an enrolled skill with no topics yet gives nothing to study until its syllabus is written
    bare = [s for s in state.enrolled_skills() if not tree.nodes[s].topics and tree.nodes[s].kind != "milestone"
            and (not skill or s == skill)]
    if bare and not cands:
        return {"action": "syllabus", "skill": bare[0], "today": t}
    return {"action": "done", "today": t}


def _begun(state, key: str) -> bool:
    ts = state.topics.get(key)
    return ts is not None and (ts.card is not None or ts.covered_ts is not None)


def unmet_needs(tree, state, topic) -> list:
    """Topics this one builds on that the learner has not studied yet."""
    keys = [need if "/" in need else "%s/%s" % (topic.skill, need) for need in topic.needs]
    return [k for k in keys if tree.has_topic(k) and not _begun(state, k)]


def teaching_lines(tree, state, topic) -> list:
    """What the tutor needs to teach a topic from the right starting point, without reading the
    syllabus: its level, what it builds on, its objectives, and where to start."""
    node = tree.nodes.get(topic.skill)
    first = node is not None and not any(_begun(state, t.key) for t in node.topics)
    lines = ["level: %d of 5%s" % (topic.level, (" · the first topic of %s for this learner" % topic.skill) if first else "")]
    if topic.needs:
        lines.append("builds on: %s" % ", ".join(topic.needs))
    goals = [ln.strip()[2:].strip() for ln in topic.body.split("\n") if ln.strip().startswith(("- ", "* "))]
    if goals:
        text = "; ".join(goals[:4])
        lines.append("objectives: %s" % (text if len(text) <= 300 else text[:297].rstrip() + "..."))
    if first or topic.level <= 1:
        lines.append("start from zero: what it is and why it exists, every new word defined, the simplest possible "
                     "example before a realistic one; assume nothing this learner has not shown here")
    else:
        lines.append("start from what it builds on (one line linking back), then the new idea; if the learner "
                     "looks lost, step back to the basics before testing")
    return lines


def action_label(action: dict) -> str:
    """The next action in a few words: 'review docker/images', 'watch course os-04', 'done'."""
    label = action["action"]
    if action.get("topic"):
        label += " " + action["topic"]
    elif action.get("skill"):
        label += " " + action["skill"]
    elif action.get("items"):
        label += " %s %s" % (action["items"][0][0].id, action["items"][0][1].id)
    return label


def next_text(repo: Repo, tree, state, when, action: dict) -> str:
    kind = action["action"]
    lines = []
    if kind == "onboard":
        return "NEXT: onboard\nThe learner has no profile yet. Run the onboard skill."
    t = action.get("today")
    if kind == "enroll":
        lines.append("NEXT: enroll")
        lines.append("No skill is enrolled yet. Pick one (tree suggest, tree list) and run: enroll <skill>")
    elif kind == "sleep":
        s = t["sleep"]
        lines.append("NEXT: sleep")
        lines.append("It is inside the learner's sleep window (%s-%s). %d review(s) are due and can wait."
                     % (s["start"], s["end"], action["due"]))
    elif kind == "review":
        key = action["topic"]
        ts = state.topics[key]
        topic = tree.topic(key)
        lines.append("NEXT: review")
        lines.append("topic: %s | %s" % (key, topic.title))
        lines.append("why: %s" % action["why"])
        lines.append("memory: recall chance %d%%, last answered %s, due %s"
                     % (round(100 * state.retrievability(key, when)), fmt_delta(ts.last_ts - when),
                        fmt_delta(ts.card.due - when)))
        lines.append("do: ask --topic %s" % key)
    elif kind == "new":
        key = action["topic"]
        topic = tree.topic(key)
        lines.append("NEXT: new")
        lines.append("topic: %s | %s" % (key, topic.title))
        lines.append("why: %s" % action["why"])
        if action.get("led"):
            lines.append("do: ask --topic %s   (the lecture is logged; test it, teach only what the test exposes)" % key)
        elif action.get("covered"):
            lines.append("do: ask --topic %s   (taught already, not tested yet: test it now; teach again only what "
                         "the answer exposes)" % key)
        else:
            lines.extend(teaching_lines(tree, state, topic))
            lines.append("do: teach one small chunk, then: ask --topic %s --taught   (records the teaching and serves "
                         "the question)" % key)
    elif kind == "watch":
        lines.append("NEXT: watch")
        if action.get("turn"):
            lines.append("why: the next new topic in turn (%s) is behind a lecture not watched yet; the next "
                         "lectures in that source are" % action["turn"])
        else:
            lines.append("why: no logged lecture is waiting to be tested; the next lectures in the source are")
        for src, it in action["items"]:
            mapped = ", ".join(it.topics) or "not mapped to a topic yet"
            lines.append("  %s %s | %s%s -> %s" % (src.id, it.id, it.title,
                                                  (" (%dm)" % it.minutes) if it.minutes else "", mapped))
        lines.append("do: after watching, run: log <source> <item>")
        if action.get("meanwhile"):
            lines.append("or carry on without it for now: %s can be started (next --skill %s)"
                         % (action["meanwhile"]["key"], action["meanwhile"]["skill"]))
    elif kind == "wind-down":
        s = t["sleep"]
        lines.append("NEXT: wind-down")
        lines.append("New material is paused: the sleep window starts at %s (in %s). Reviews are done."
                     % (s["start"], fmt_minutes(s["minutes_to_sleep"])))
    elif kind == "syllabus":
        node = tree.nodes[action["skill"]]
        lines.append("NEXT: syllabus")
        lines.append("skill: %s | %s has no syllabus yet, so it has nothing to teach" % (node.id, node.title))
        lines.append("do: have the curriculum-architect agent write learner/syllabus/%s.md for this learner, "
                     "then: syllabus check %s" % (node.id, node.id))
    elif kind == "boss":
        lines.append("NEXT: boss")
        lines.append("skill: %s | every topic is solid; the boss test or project is due" % action["skill"])
        lines.append("do: boss status %s" % action["skill"])
    else:
        lines.append("NEXT: done")
        if t and t["finished"]:
            lines.append("Today's finish line is reached.")
        elif t and t["reviews_left"]:
            later = t["reviews_left"]
            lines.append("Nothing is due right now; %d more review%s come%s due later today (dash queue shows when)."
                         % (later, "" if later == 1 else "s", "s" if later == 1 else ""))
        else:
            lines.append("Nothing is due right now.")
        if action.get("extra"):
            lines.append("optional: more new material is unlocked (%s), but today's quota is done" % action["extra"])
        elif t and not t["candidates"] and state.enrolled_skills():
            lines.append("The enrolled skills have no new topic left to start: see what is open next with: tree suggest")
    from . import advise

    hint = advise.line(repo, kind)
    if hint:
        lines.append(hint)
    if t:
        lines.append(today_line(t))
    return "\n".join(lines)


# ---------------------------------------------------------------- weaving


def weave_candidates(repo: Repo, tree, state, when, skill_id: str, n: int | None = None) -> list:
    """Earlier topics worth embedding into an exercise for `skill_id`.

    A skill offers itself through `weaves_into` (tags, groups, skill ids or
    'any'). Only topics the learner has already answered are returned, most
    forgotten first, at most one per skill until every skill has had a turn.
    """
    n = int(repo.cfg("weave_n", 2)) if n is None else n
    target = tree.get(skill_id)
    accept = set(target.tags) | {target.id, target.group, target.track, "any"}
    day = state.day(when)
    rows = []
    for key, ts in state.scheduled_topics():
        other = key.split("/", 1)[0]
        if other == skill_id or ts.first_day == day:
            continue
        node = tree.nodes[other]
        if not set(node.weaves_into) & accept:
            continue
        rows.append((0 if ts.card.due <= when else 1, state.retrievability(key, when), key))
    rows.sort()
    picked, used = [], set()
    for round_no in (0, 1):
        for _, r, key in rows:
            if len(picked) >= n:
                break
            other = key.split("/", 1)[0]
            if key in [p[0] for p in picked] or (round_no == 0 and other in used):
                continue
            used.add(other)
            picked.append((key, r))
    return picked


def weave_text(repo: Repo, tree, state, when, skill_id: str, n: int | None = None) -> str:
    picked = weave_candidates(repo, tree, state, when, skill_id, n)
    if not picked:
        return "WEAVE: none\nNo earlier topic applies to %s yet (nothing learnt that weaves into it)." % skill_id
    lines = ["WEAVE for %s (embed these earlier topics in the next exercise):" % skill_id]
    for key, r in picked:
        topic = tree.topic(key)
        ts = state.topics[key]
        due = "due" if ts.card.due <= when else "not due yet"
        lines.append("  %s | %s | recall chance %d%%, %s" % (key, topic.title, round(100 * r), due))
        hint = topic.first_line()
        if hint:
            lines.append("      %s" % hint)
    lines.append("List them after the primary topic in the item's 'topics' so one answer credits all of them.")
    return "\n".join(lines)


# ---------------------------------------------------------------- brief


def brief(repo: Repo, tree, state, when, engine_cmd: str = "", current=None) -> str:
    """The session-start summary. Facts only; instructions live in CLAUDE.md."""
    out = ["=== CALAMITY BRIEF ==="]
    stamp = when.strftime("%a %Y-%m-%d %H:%M %z")
    out.append("Time: %s · machine: %s%s" % (stamp, repo.machine(), (" · engine: " + engine_cmd) if engine_cmd else ""))
    if not repo.onboarded():
        live = tree.live()
        out.append("State: NOT ONBOARDED (no learner profile yet).")
        out.append("Skill tree: %d skills across tracks %s." % (len(live), ", ".join(tree.tracks)))
        out.append("=== END BRIEF ===")
        return "\n".join(out)

    name = repo.prof_text("name", "the learner")
    tracks = ", ".join(csv_list(repo.prof("tracks"))) or "none chosen"
    out.append("Learner: %s · tracks: %s · default mode: %s" % (name, tracks, repo.prof("mode.default", "mastery")))
    style = repo.prof("teach.style")
    if style:
        out.append("Teaching preferences: %s" % style)

    if any(str(tr).startswith("gate") for tr in csv_list(repo.prof("tracks"))) or repo.prof("gate.year"):
        from . import gate

        out.extend(gate.brief_lines(repo, tree, state, when))
    if repo.prof("cp.handle"):
        from . import cf

        out.extend(cf.brief_lines(repo, state, when))

    t = today(repo, tree, state, when)
    out.append(today_line(t).replace("today:", "Today:", 1))
    from . import day

    out.extend(day.now_lines(repo, when))   # where the learner is in the day's shape (learner/schedule.md)

    due = state.due(when)
    if due:
        out.append("Due now (%d, most forgotten first):" % len(due))
        for i, (key, ts) in enumerate(due[:6], 1):
            out.append("  %d. %s | recall chance %d%%, due %s" % (
                i, key, round(100 * state.retrievability(key, when)), fmt_delta(ts.card.due - when)))
        recall_n = int(repo.cfg("recall_n", 3))
        out.append("Surprise-recall candidates: the first %d above (from any skill, unannounced)." % min(recall_n, len(due)))
    else:
        out.append("Due now: nothing.")

    enrolled = state.enrolled_skills()
    if enrolled:
        out.append("Active skills:")
        started = sorted((s for s in enrolled if state.skills[s].last_ts),
                         key=lambda s: utc(state.skills[s].last_ts), reverse=True)
        for skill_id in started[:8]:
            counts = state.skill_counts(skill_id)
            sk = state.skills[skill_id]
            prog = "%d/%d solid" % (counts["solid"] + counts["mastered"], counts["total"])
            out.append("  %s · %s · %s · last studied %s" % (skill_id, prog, sk.mode, fmt_delta(sk.last_ts - when)))
        if len(started) > 8:
            out.append("  ... and %d more under way" % (len(started) - 8))
        fresh = [s for s in enrolled if not state.skills[s].last_ts]
        if fresh:
            out.append("  not started yet (%d): %s%s" % (len(fresh), ", ".join(fresh[:6]), " ..." if len(fresh) > 6 else ""))
        bare = [s for s in enrolled if not tree.nodes[s].topics and tree.nodes[s].kind != "milestone"]
        if bare:
            out.append("  no syllabus yet (%d): %s%s" % (len(bare), ", ".join(bare[:6]), " ..." if len(bare) > 6 else ""))
    else:
        out.append("Active skills: none enrolled.")

    action = next_action(repo, tree, state, when)
    out.append("Next action: %s" % action_label(action))
    from . import advise

    if advise.enabled(repo):
        from .session import needed_topics

        # Agents inherit the session's model: when the bank needs stocking, that comes first.
        stock = bool(needed_topics(repo, tree, state, when, n=4))
        hint = advise.line(repo, "stock" if stock else action["action"], current,
                           then=action["action"] if stock else None)
        if hint:
            out.append(hint[0].upper() + hint[1:])

    from . import stats

    flags = stats.flags(repo, tree, state, when)
    if flags:
        out.append("Observations: " + " · ".join(flags[:4]))
    s = t["sleep"]
    if s["set"]:
        if s["inside"]:
            out.append("Sleep window %s-%s: it is inside the window now." % (s["start"], s["end"]))
        elif s["in_guard"]:
            out.append("Sleep window %s-%s starts in %s: new material is paused, reviews only."
                       % (s["start"], s["end"], fmt_minutes(s["minutes_to_sleep"])))
        else:
            out.append("Sleep window %s-%s; new material stops %d min before it (in %s)."
                       % (s["start"], s["end"], s["guard"], fmt_minutes(s["minutes_to_cutoff"])))
    pattern = stats.open_pattern(repo, tree, state, when)
    if pattern:
        out.append("Behaviour pattern not yet raised today: %s" % pattern["fact"])
    if repo.event_errors:
        out.append("Data notes: %d event line(s) could not be read (see doctor)." % len(repo.event_errors))
    if repo.config_errors:
        out.append("Data notes: %d configuration override(s) ignored (see doctor)." % len(repo.config_errors))
    for problem in repo.file_problems[:2]:
        out.append("Data notes: %s." % problem.rstrip("."))
    tree_errors, _ = tree.check()
    if tree_errors:
        out.append("Data notes: the skill tree has %d error(s) (see tree check)." % len(tree_errors))
    out.append("=== END BRIEF ===")
    text = "\n".join(out)
    limit = 6000
    return text if len(text) <= limit else text[: limit - 40].rstrip() + "\n... (brief truncated)\n=== END BRIEF ==="
