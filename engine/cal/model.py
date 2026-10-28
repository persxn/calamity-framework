"""The learner model: how this learner learns, measured from the event log, and n-of-1 experiments.

`model` computes, for a window of days (30 by default), per track and per skill:

    first try       share of new topics whose first verified answer was right
    retention       right answers on verified reviews asked 7+ and 30+ days after the previous answer
    time            median seconds per timed answer, and the share flagged slow
    hints           share of answers given with hints
    errors          the mix of error kinds on wrong answers
    lag             median days from a topic's first teaching (or first answer) to consolidating

and across everything:

    teaching        first-try accuracy by the parts a topic was taught with (ask --taught --parts) and by the
                    part taught first, and the learner's pace feedback
    time of day     accuracy and answers per active hour by part of day
    session minute  accuracy by how long the session had run (0-30, 30-60, 60-90, 90+ minutes), and the
                    length after which accuracy falls more than 10 points below the first half hour
    ROI             durable mastery gained per hour per track: topics secured, weighted by GATE marks per
                    topic, by being on the route to a goal (1) or not (0.5), over the hours that track's
                    answers took (an estimate: time is split between tracks by their share of each day's answers)

Every number comes with its count, and nothing is shown from fewer than MIN answers. The engine never
changes anything because of these numbers: the learning-analyst proposes, the learner decides.

Experiments (`experiment start|status|stop`) compare two or more ways of teaching on the next N new
topics of one skill. Arms alternate in the order topics are first taught, so a replay always assigns
the same arms. `NEXT: new` names the arm to teach the topic with. `status` gives each arm's first-try
accuracy and, for two arms, the chance that the second is better than the first under a uniform
Beta(1, 1) prior; below N topics measured it refuses a conclusion.
"""
from __future__ import annotations

import math
import re
from datetime import timedelta

from . import fsrs
from .util import CalError, fmt_minutes, pct, table

MIN = 5            # fewest answers a rate is shown from
WINDOWS = ((0, 30), (30, 60), (60, 90), (90, 10 ** 6))
METRICS = ("first_try_acc",)


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    mid = len(xs) // 2
    return xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def _rate(ok, n):
    return ("%s (%d)" % (pct(ok / float(n)), n)) if n >= MIN else ("- (%d)" % n if n else "-")


# ---------------------------------------------------------------- the attempts, once


def attempts(repo, tree, state, since=None) -> list:
    """Every counted answer since `since`, in log order, with what the model needs to know about it."""
    rows = []
    prev = {}          # topic -> datetime of its previous evidence answer
    gap_min = timedelta(minutes=int(repo.cfg("session_gap_minutes", 30)))
    session_start, last = None, None
    for e in repo.events():
        dt = e["_dt"]
        if last is None or dt - last > gap_min:
            session_start = dt
        last = dt
        if e["t"] != "attempt" or e["id"] in state._voided or e.get("kind") == "placement":
            continue
        key = state.canon(str(e.get("topic") or ""))
        evidence = bool(e.get("verified")) and not e.get("quick") and not e.get("after_reveal")
        ts = state.topics.get(key)
        first = ts is not None and ts.first_ts == dt
        gap = (dt - prev[key]) if (evidence and key in prev) else None
        if evidence:
            prev[key] = dt
        if since is not None and dt < since:
            continue
        sid = key.split("/", 1)[0]
        node = tree.nodes.get(sid)
        secs = e.get("secs")
        rows.append({"dt": dt, "key": key, "skill": sid, "track": node.track if node else "?",
                     "ok": bool(e.get("ok")), "evidence": evidence, "first": first, "gap": gap,
                     "secs": secs if isinstance(secs, (int, float)) and not isinstance(secs, bool) else None,
                     "slow": bool(e.get("slow")), "hints": int(e.get("hints") or 0),
                     "err": None if e.get("ok") else (state._retag.get(e["id"]) or e.get("err") or "unclassified"),
                     "minute": (dt - session_start).total_seconds() / 60.0})
    return rows


def taught_parts(repo, state) -> dict:
    """topic -> the parts it was first taught with (ask --taught --parts), in the order given."""
    out = {}
    for e in repo.events():
        if e["t"] == "covered" and e.get("parts"):
            out.setdefault(state.canon(str(e.get("topic"))), list(e["parts"]))
    return out


# ---------------------------------------------------------------- the measures


def group_stats(rows) -> dict:
    ev = [r for r in rows if r["evidence"]]
    first = [r for r in ev if r["first"]]
    r7 = [r for r in ev if r["gap"] is not None and r["gap"] >= timedelta(days=7)]
    r30 = [r for r in ev if r["gap"] is not None and r["gap"] >= timedelta(days=30)]
    secs = [r["secs"] for r in rows if r["secs"]]
    errs = {}
    for r in rows:
        if r["err"]:
            errs[r["err"]] = errs.get(r["err"], 0) + 1
    return {"n": len(rows), "first": (sum(r["ok"] for r in first), len(first)),
            "r7": (sum(r["ok"] for r in r7), len(r7)), "r30": (sum(r["ok"] for r in r30), len(r30)),
            "secs": _median(secs), "n_secs": len(secs), "slow": sum(r["slow"] for r in rows),
            "hints": sum(1 for r in rows if r["hints"]), "errors": errs}


def lag_days(state, keys) -> tuple:
    lags = []
    for key in keys:
        ts = state.topics.get(key)
        at = state.consolidated_at(key)
        start = ts and (ts.covered_ts or ts.first_ts)
        if at is not None and start is not None and at >= start:
            lags.append((at - start).total_seconds() / 86400.0)
    return _median(lags), len(lags)


def part_of_day(hour: int) -> str:
    from .stats import _part_of

    return _part_of(hour)


def session_curve(rows) -> list:
    out = []
    for lo, hi in WINDOWS:
        sel = [r for r in rows if lo <= r["minute"] < hi]
        out.append((lo, hi, sum(r["ok"] for r in sel), len(sel)))
    return out


def recommended_length(curve):
    """Minutes after which accuracy falls more than 10 points below the first half hour, or None."""
    lo0, hi0, ok0, n0 = curve[0]
    if n0 < 10:
        return None
    base = ok0 / float(n0)
    for lo, hi, ok, n in curve[1:]:
        if n >= 10 and ok / float(n) < base - 0.10:
            return lo
    return None


def roi(repo, tree, state, rows, since) -> list:
    """[(track, weighted topics secured, hours, per hour)]: an estimate."""
    goals = set()
    for g in re.split(r"[,\s]+", str(repo.prof("goals") or "")):
        if g and g in tree.nodes:
            try:
                goals.update(tree.ancestors(g))
            except CalError:  # a broken goal only loses the weighting
                pass
            goals.add(g)
    secured = {}
    for key in state.topics:
        at = state.consolidated_at(key)
        if at is None or (since is not None and at < since):
            continue
        sid = key.split("/", 1)[0]
        node = tree.nodes.get(sid)
        if node is None:
            continue
        if node.track.startswith("gate"):
            marks = float(state.weights.get(sid, (node.marks or 0, ""))[0] or 0)
            weight = marks / max(1, len(node.topics))
        else:
            weight = 1.0 if sid in goals else 0.5
        secured[node.track] = secured.get(node.track, 0.0) + weight
    by_day = {}
    for r in rows:
        by_day.setdefault(state.day(r["dt"]), {}).setdefault(r["track"], 0)
        by_day[state.day(r["dt"])][r["track"]] += 1
    hours = {}
    for day, counts in by_day.items():
        ds = state.days.get(day)
        total = sum(counts.values())
        if not ds or not total:
            continue
        for track, n in counts.items():
            hours[track] = hours.get(track, 0.0) + ds.active_min / 60.0 * n / total
    out = []
    for track in sorted(set(secured) | set(hours)):
        h = hours.get(track, 0.0)
        out.append((track, secured.get(track, 0.0), h, (secured.get(track, 0.0) / h) if h >= 0.5 else None))
    return out


# ---------------------------------------------------------------- the report


def _skill_rows(state, tree, rows, key_of):
    groups = {}
    for r in rows:
        groups.setdefault(key_of(r), []).append(r)
    out = []
    for name in sorted(groups):
        g = group_stats(groups[name])
        keys = sorted({r["key"] for r in groups[name]})
        lag, n_lag = lag_days(state, keys)
        top_err = sorted(g["errors"].items(), key=lambda kv: (-kv[1], kv[0]))[:2]
        out.append([name, g["n"], _rate(*g["first"]), _rate(*g["r7"]), _rate(*g["r30"]),
                    ("%ds" % g["secs"]) if g["secs"] and g["n_secs"] >= MIN else "-",
                    pct(g["hints"] / float(g["n"])) if g["n"] >= MIN else "-",
                    ", ".join("%s %d" % kv for kv in top_err) or "-",
                    (("%.1fd (%d)" if lag >= 1 else "%.0fh (%d)") % (lag if lag >= 1 else lag * 24, n_lag))
                    if lag is not None else "-"])
    return out


def text(repo, tree, state, when, days: int = 30, skill: str | None = None, track: str | None = None) -> str:
    since = when - timedelta(days=days)
    rows = attempts(repo, tree, state, since)
    if skill:
        tree.get(skill)
        rows = [r for r in rows if r["skill"] == skill]
    if track:
        rows = [r for r in rows if r["track"] == track]
    if not rows:
        return "model: no answers in the last %d days%s" % (days, (" for " + (skill or track)) if (skill or track) else "")
    head = ["", "answers", "first try", "kept 7d+", "kept 30d+", "median", "hints", "errors", "to consolidate"]
    out = ["Learner model, last %d days (%d answers). Rates show their count; fewer than %d answers show -." % (
        days, len(rows), MIN)]
    out.append(table(_skill_rows(state, tree, rows, lambda r: r["track"]), ["track"] + head[1:]))
    if skill or len({r["skill"] for r in rows}) > 1:
        out.append("")
        out.append(table(_skill_rows(state, tree, rows, lambda r: r["skill"]), ["skill"] + head[1:]))
    # teaching patterns
    parts = taught_parts(repo, state)
    by_set, by_first = {}, {}
    for r in rows:
        if r["evidence"] and r["first"] and r["key"] in parts:
            p = parts[r["key"]]
            by_set.setdefault("+".join(sorted(p)), []).append(r["ok"])
            by_first.setdefault(p[0] if p else "-", []).append(r["ok"])
    if by_set:
        out.append("")
        out.append("Teaching (first-try accuracy by what was taught):")
        for name, oks in sorted(by_set.items(), key=lambda kv: -len(kv[1])):
            out.append("  %-46s %s" % (name, _rate(sum(oks), len(oks))))
        out.append("  by the part taught first: " + ", ".join(
            "%s %s" % (k, _rate(sum(v), len(v))) for k, v in sorted(by_first.items())))
    pace = {}
    for n in state.notes:
        if n.get("tag") == "feedback" and n["ts"] >= since:
            for k in ("pace", "depth", "clarity", "level"):
                if n.get(k):
                    pace["%s=%s" % (k, n[k])] = pace.get("%s=%s" % (k, n[k]), 0) + 1
    if pace:
        out.append("  the learner's feedback: " + ", ".join("%s %d" % kv for kv in sorted(pace.items())))
    # time of day
    parts_day = {}
    for r in rows:
        parts_day.setdefault(part_of_day(r["dt"].hour), []).append(r)
    out.append("")
    out.append("Time of day: " + " · ".join(
        "%s %s" % (name, _rate(sum(r["ok"] for r in rs), len(rs)))
        for name, rs in sorted(parts_day.items(), key=lambda kv: ("morning", "afternoon", "evening", "night").index(kv[0]))))
    curve = session_curve(rows)
    out.append("Session minute: " + " · ".join(
        "%s %s" % (("%d-%d" % (lo, hi)) if hi < 10 ** 6 else "%d+" % lo, _rate(ok, n)) for lo, hi, ok, n in curve))
    length = recommended_length(curve)
    out.append("  accuracy falls after about %d minutes: blocks of that length, then a break (an estimate)" % length
               if length else "  no fall in accuracy measured within a session yet")
    gains = roi(repo, tree, state, rows, since)
    if gains:
        out.append("")
        out.append("ROI (topics secured, weighted, per hour; an estimate): " + " · ".join(
            "%s %.1f in %s%s" % (t, w, fmt_minutes(h * 60), (" = %.2f/h" % per) if per is not None else "")
            for t, w, h, per in gains))
    return "\n".join(out)


# ---------------------------------------------------------------- experiments


def running_for(state, skill: str):
    for ex in state.experiments.values():
        if ex["skill"] == skill and not ex.get("stopped") and len(ex["assigned"]) < ex["n"]:
            return ex
    return None


def next_arm_line(state, skill: str):
    ex = running_for(state, skill)
    if ex is None:
        return None
    k = len(ex["assigned"])
    return "experiment %s: teach this topic %s (topic %d of %d; %s)" % (
        ex["id"], ex["arms"][k % len(ex["arms"])], k + 1, ex["n"], ex.get("desc") or "")


def start(repo, tree, state, ident: str, skill: str, arms, metric: str, n: int, desc: str | None) -> str:
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,30}$", ident or ""):
        raise CalError("an experiment id is short: letters, digits and dashes (ex-04)")
    if ident in state.experiments:
        raise CalError("experiment %s exists already" % ident)
    tree.get(skill)
    arms = [a.strip() for a in (arms or "").split(",") if a.strip()]
    if len(arms) < 2 or len(set(arms)) != len(arms):
        raise CalError("give two or more different arms: --arms theory-first,example-first")
    if metric not in METRICS:
        raise CalError("the metric is one of %s" % ", ".join(METRICS))
    if n < 2 * len(arms):
        raise CalError("--n must give each arm at least two topics (%d or more)" % (2 * len(arms)))
    if running_for(state, skill):
        raise CalError("%s already has a running experiment: %s" % (skill, running_for(state, skill)["id"]))
    repo.append("experiment_start", exp=ident, skill=skill, arms=arms, metric=metric, n=n, desc=desc)
    return ("experiment %s started: the next %d new topics of %s alternate %s; NEXT: new names the arm to teach "
            "with" % (ident, n, skill, " / ".join(arms)))


def stop(repo, state, ident: str) -> str:
    if ident not in state.experiments:
        raise CalError("no experiment %s" % ident)
    repo.append("experiment_stop", exp=ident)
    return "experiment %s stopped (its results so far stay: experiment status %s)" % (ident, ident)


def _lbeta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def prob_b_beats_a(sa, fa, sb, fb) -> float:
    """P(p_B > p_A) for Beta(1+s, 1+f) posteriors (Evan Miller's closed form)."""
    a_a, b_a, a_b, b_b = sa + 1, fa + 1, sb + 1, fb + 1
    total = 0.0
    for i in range(a_b):
        total += math.exp(_lbeta(a_a + i, b_a + b_b) - math.log(b_b + i) - _lbeta(1 + i, b_b) - _lbeta(a_a, b_a))
    return min(1.0, max(0.0, total))


def status(state, ident: str | None = None) -> str:
    if not state.experiments:
        return "no experiments yet (experiment start <id> --skill S --arms a,b --n 12 --desc \"...\")"
    if ident is None:
        rows = []
        for ex in state.experiments.values():
            done = len(ex["results"])
            rows.append([ex["id"], ex["skill"], " / ".join(ex["arms"]), "%d of %d" % (done, ex["n"]),
                         "stopped" if ex.get("stopped") else ("measuring" if done < ex["n"] else "complete")])
        return table(rows, ["id", "skill", "arms", "measured", "state"])
    ex = state.experiments.get(ident)
    if ex is None:
        raise CalError("no experiment %s" % ident)
    lines = ["experiment %s on %s: %s" % (ex["id"], ex["skill"], ex.get("desc") or "")]
    tally = {arm: [0, 0] for arm in ex["arms"]}
    for topic, arm in ex["assigned"]:
        if topic in ex["results"]:
            tally[arm][0] += 1 if ex["results"][topic] else 0
            tally[arm][1] += 1
    for arm in ex["arms"]:
        ok, n = tally[arm]
        lines.append("  %-20s first try %s" % (arm, ("%d of %d right" % (ok, n)) if n else "no topics measured yet"))
    measured = len(ex["results"])
    if measured < ex["n"]:
        lines.append("no conclusion yet: %d of %d topics measured (an experiment never concludes below its n)"
                     % (measured, ex["n"]))
        return "\n".join(lines)
    if len(ex["arms"]) == 2:
        a, b = ex["arms"]
        p = prob_b_beats_a(tally[a][0], tally[a][1] - tally[a][0], tally[b][0], tally[b][1] - tally[b][0])
        lines.append("P(%s better than %s) = %.2f (Beta(1,1) prior; %d topics)" % (b, a, p, measured))
        verdict = ("%s looks better" % b) if p >= 0.9 else ("%s looks better" % a) if p <= 0.1 else "no clear difference"
        lines.append("reading: %s. A change to teach.style or the pace waits for the learner's yes." % verdict)
    else:
        lines.append("more than two arms: compare the rates above; no single probability is given")
    return "\n".join(lines)
