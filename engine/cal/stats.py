"""What the event log says about how this learner works.

Two audiences:
  * flags()    - observations for the tutor, to adapt teaching;
  * patterns() - behaviour patterns for the coach, raised at most one a day
                 and never as a complaint: each comes with a question.
All of it is computed from timestamps and results already in the log.
"""
from __future__ import annotations

from datetime import timedelta

from .store import Repo
from .util import fmt_minutes, pct, table

DAY_PARTS = (("morning", 5, 12), ("afternoon", 12, 17), ("evening", 17, 22), ("night", 22, 5))


def _recent_days(state, when, days: int) -> list:
    """DayStats for the last `days` learner days, oldest first (missing days are None)."""
    out = []
    for back in range(days - 1, -1, -1):
        key = state.day(when - timedelta(days=back))
        out.append((key, state.days.get(key)))
    return out


def accounted(ds) -> float:
    """Minutes of a day the log can account for: activity here, logged lectures, logged workouts."""
    return ds.active_min + ds.src_min + ds.workout_min


def _part_of(hour: int) -> str:
    for name, start, end in DAY_PARTS:
        if (start <= hour < end) if start < end else (hour >= start or hour < end):
            return name
    return "night"


def day_parts(state, when, days: int = 14) -> dict:
    """{part: [attempts, correct]} over the last `days` days."""
    parts = {name: [0, 0] for name, _, _ in DAY_PARTS}
    for _, ds in _recent_days(state, when, days):
        if ds is None:
            continue
        for hour, (n, ok) in ds.hours.items():
            bucket = parts[_part_of(hour)]
            bucket[0] += n
            bucket[1] += ok
    return parts


def _weak_part(state, when):
    parts = day_parts(state, when)
    total = sum(v[0] for v in parts.values())
    correct = sum(v[1] for v in parts.values())
    if total < 40:
        return None
    overall = correct / float(total)
    worst = None
    for name, (n, ok) in parts.items():
        if n >= 20:
            acc = ok / float(n)
            if overall - acc >= 0.15 and (worst is None or acc < worst[1]):
                worst = (name, acc, overall, n)
    return worst


# ---------------------------------------------------------------- tutor flags


def flags(repo: Repo, tree, state, when) -> list:
    out = []
    week_ago = when - timedelta(days=7)
    enrolled = set(state.enrolled_skills())
    by_skill_err = {}
    for key, ts in state.topics.items():
        skill = key.split("/", 1)[0]
        if skill not in enrolled:
            continue
        for dt, tag in ts.err_log:
            if dt >= week_ago and tag != "unclassified":
                by_skill_err[(skill, tag)] = by_skill_err.get((skill, tag), 0) + 1
    for (skill, tag), n in sorted(by_skill_err.items(), key=lambda kv: -kv[1]):
        if n >= 3:
            out.append("%d '%s' errors in %s this week" % (n, tag, skill))
            break
    hinty = []
    slow = []
    for key, ts in state.topics.items():
        if key.split("/", 1)[0] not in enrolled or ts.card is None:
            continue
        if ts.n >= 5 and ts.hints / float(ts.n) > 0.4:
            hinty.append((ts.hints / float(ts.n), key))
        if ts.n_ok >= 4 and ts.slow / float(ts.n_ok) >= 0.5:
            slow.append((ts.slow / float(ts.n_ok), key))
    if hinty:
        out.append("hint use is high on %s" % max(hinty)[1])
    if slow:
        out.append("correct but slow on %s" % max(slow)[1])
    worst = _weak_part(state, when)
    if worst:
        out.append("accuracy in the %s is %s against %s overall" % (worst[0], pct(worst[1]), pct(worst[2])))
    for skill in sorted(enrolled):
        node = tree.nodes.get(skill)
        if node is None:
            continue
        rows = []
        for topic in node.topics:
            ts = state.topics.get(topic.key)
            if ts is not None:
                rows.extend(ts.recent)
        rows.sort(key=lambda r: r[0])
        last = rows[-10:]
        if len(last) == 10 and sum(1 for r in last if r[1]) >= 9:
            out.append("%s: 9+ of the last 10 answers correct, harder items are due" % skill)
            break
    return out


# ---------------------------------------------------------------- coach patterns


def patterns(repo: Repo, tree, state, when) -> list:
    """Behaviour patterns as [{id, fact, question}], most important first."""
    out = []
    week = _recent_days(state, when, 7)
    active_days = [ds for _, ds in week if ds is not None and (ds.attempts or ds.src_done)]
    if len(state.days) < 4:
        return out  # not enough history to say anything fair

    late = [ds for _, ds in week if ds is not None and ds.in_sleep > 0]
    if len(late) >= 3 and repo.prof("sleep.start"):
        out.append({
            "id": "late-night",
            "fact": "studied inside the sleep window (%s-%s) on %d of the last 7 days"
                    % (repo.prof("sleep.start"), repo.prof("sleep.end"), len(late)),
            "question": "Is the sleep window wrong for you, or are late sessions eating into it?",
        })

    zero = [key for key, ds in week[:-1] if ds is None or not (ds.attempts or ds.src_done)]
    if len(zero) >= 2:
        out.append({
            "id": "zero-days",
            "fact": "no study recorded on %d of the last 6 full days" % len(zero),
            "question": "What got in the way on those days, and what is the smallest session that would still fit?",
        })

    due_now = len(state.due(when))
    done = [ds.reviews for _, ds in week if ds is not None]
    avg_reviews = (sum(done) / 7.0) if done else 0.0
    if due_now >= 15 and due_now > 2 * max(avg_reviews, 1.0):
        out.append({
            "id": "review-backlog",
            "fact": "%d reviews are due, against about %d done per day this week" % (due_now, round(avg_reviews)),
            "question": "Shall we pause new material for a day or two and clear the backlog first?",
        })

    sessions = sum(ds.sessions for ds in active_days)
    minutes = sum(ds.active_min for ds in active_days)
    if sessions >= 6 and minutes / float(sessions) < 10:
        out.append({
            "id": "fragmented",
            "fact": "%d sessions this week averaged %s each" % (sessions, fmt_minutes(minutes / sessions)),
            "question": "Would one protected 45-minute block a day work better than many short ones?",
        })

    workout_goal = repo.prof("workout.minutes")
    try:
        workout_goal = int(workout_goal or 0)
    except (TypeError, ValueError):
        workout_goal = 0
    if workout_goal > 0:
        last3 = week[-4:-1]
        if all(ds is None or ds.workout_min == 0 for _, ds in last3) and any(ds is not None for _, ds in last3):
            out.append({
                "id": "no-workout",
                "fact": "no workout logged in the last 3 days (goal: %d min a day)" % workout_goal,
                "question": "Is the workout slot realistic where it is, or should it move?",
            })

    worst = _weak_part(state, when)
    if worst:
        out.append({
            "id": "daypart-dip",
            "fact": "accuracy in the %s is %s over %d answers, against %s overall"
                    % (worst[0], pct(worst[1]), worst[3], pct(worst[2])),
            "question": "Shall new and hard material move out of the %s, leaving it for light review?" % worst[0],
        })

    quota = int(repo.cfg("new_per_day", 8))
    heavy = [ds for _, ds in week[-3:] if ds is not None and ds.new > 2 * quota]
    if heavy and due_now >= 10:
        out.append({
            "id": "new-over-review",
            "fact": "new topics ran at more than twice the daily quota while %d reviews are waiting" % due_now,
            "question": "New material feels like progress, but unreviewed topics fade. Reviews first tomorrow?",
        })
    return out


def open_pattern(repo: Repo, tree, state, when):
    """The one pattern the coach may raise now, or None (one a day; each rests a few days)."""
    today = state.day(when)
    cooldown = timedelta(days=int(repo.cfg("coach.cooldown_days", 3)))
    raised = [n for n in state.notes if n.get("tag") == "coach"]
    if any(state.day(n["ts"]) == today for n in raised):
        return None
    for pattern in patterns(repo, tree, state, when):
        recent = [n for n in raised if n.get("pattern") == pattern["id"] and when - n["ts"] < cooldown]
        if not recent:
            return pattern
    return None


# ---------------------------------------------------------------- reports


def week_text(repo: Repo, state, when, days: int = 7) -> str:
    rows = []
    recent = _recent_days(state, when, days)
    for key, ds in recent:
        if ds is None:
            rows.append([key, "-", "-", "-", "-", "-", "-", "-", "-", "-"])
            continue
        acc = pct(ds.ok / float(ds.attempts)) if ds.attempts else "-"
        span = "%s-%s" % (ds.first.strftime("%H:%M"), ds.last.strftime("%H:%M"))
        lectures = ("%d (%s)" % (ds.src_done, fmt_minutes(ds.src_min))) if ds.src_min else (ds.src_done or "-")
        rows.append([key, fmt_minutes(ds.active_min), ds.sessions, ds.reviews, ds.new, acc, lectures,
                     fmt_minutes(ds.workout_min) if ds.workout_min else "-", fmt_minutes(accounted(ds)), span])
    head = ["day", "active", "sessions", "reviews", "new", "accuracy", "lectures", "workout", "accounted", "first-last"]
    text = table(rows, head, aligns="lrrrrrrrrl")
    total = sum(accounted(ds) for _, ds in recent if ds is not None)
    target = repo.prof("daily.target_hours")
    tail = ("\naccounted = active time in this repository + stated length of logged lectures + logged workouts."
            "\nTime spent elsewhere (a contest, a book, an unlogged lecture) is not seen: ask before judging a day."
            "\naccounted over %d days: %s, %s a day on average" % (days, fmt_minutes(total), fmt_minutes(total / float(days))))
    if target:
        tail += "\nstated daily target: %s productive hours (study + workout)" % target
    return text + tail


def hours_text(repo: Repo, state, when, days: int = 14) -> str:
    parts = day_parts(state, when, days)
    rows = []
    for name, start, end in DAY_PARTS:
        n, ok = parts[name]
        rows.append([name, "%02d-%02d" % (start, end), n, pct(ok / float(n)) if n else "-"])
    return "accuracy by part of day, last %d days\n" % days + table(rows, ["part", "hours", "answers", "accuracy"], aligns="llrr")


def patterns_text(repo: Repo, tree, state, when) -> str:
    found = patterns(repo, tree, state, when)
    if len(state.days) < 4:
        return "Not enough history yet (patterns need at least 4 days of activity)."
    if not found:
        return "No behaviour pattern stands out in the last 7 days."
    nxt = open_pattern(repo, tree, state, when)
    lines = []
    for p in found:
        mark = "RAISE NOW" if nxt and nxt["id"] == p["id"] else "hold"
        lines.append("[%s] %s: %s" % (mark, p["id"], p["fact"]))
        lines.append("    ask: %s" % p["question"])
    lines.append("Raise at most one a day, as a question. After raising: observe \"...\" --tag coach --pattern <id>")
    return "\n".join(lines)


def errors_text(repo: Repo, tree, state, track_prefix: str | None = None, limit: int = 15) -> str:
    """Error log: topics with the most failures, with their error tags."""
    rows = []
    for key, ts in state.topics.items():
        fails = sum(ts.errors.values())
        if not fails or not tree.has_topic(key):
            continue
        node = tree.nodes[key.split("/", 1)[0]]
        if track_prefix and not node.track.startswith(track_prefix):
            continue
        tags = ", ".join("%s x%d" % (t, c) for t, c in sorted(ts.errors.items(), key=lambda kv: -kv[1]))
        rows.append((fails, key, "%d/%d" % (ts.n_ok, ts.n), tags, state.topic_status(key)))
    if not rows:
        return "No failed answers recorded."
    rows.sort(key=lambda r: (-r[0], r[1]))
    return table([[r[1], r[0], r[2], r[4], r[3]] for r in rows[:limit]],
                 ["topic", "fails", "correct", "status", "error tags"], aligns="lrrll")

