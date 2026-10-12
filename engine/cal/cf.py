"""Codeforces link for the competitive-programming coach.

Uses only the official public API (https://codeforces.com/apiHelp) with the
learner's handle: no password, no key, at most one request every two
seconds. What Codeforces already stores (submissions, rating history, the
problem set) is cached under .calamity/cache/cf and can be re-fetched at any
time; the event log keeps only what is the coach's own: assignments, marks
and sub-tags.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from .store import Repo
from .util import CalError, csv_list, fmt_delta, iso, now, parse_ts, table

API = "https://codeforces.com/api/"
HANDLE_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")
PROBLEM_RE = re.compile(r"^(\d{1,6})([A-Za-z][A-Za-z0-9]{0,2})$")
CONTEST_TYPES = ("CONTESTANT", "VIRTUAL", "OUT_OF_COMPETITION")
PAUSE = 2.1


# ---------------------------------------------------------------- fetching


def _fetch(method: str, params: dict):
    fixtures = os.environ.get("CALAMITY_CF_FIXTURES")
    if fixtures:
        path = os.path.join(fixtures, method + ".json")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except OSError:
            raise CalError("no fixture for %s in %s" % (method, fixtures))
    else:
        url = API + method + ("?" + urllib.parse.urlencode(params) if params else "")
        request = urllib.request.Request(url, headers={"User-Agent": "calamity-framework (personal study tool)"})
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=40) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                try:
                    data = json.loads(exc.read().decode("utf-8"))
                except (ValueError, OSError):
                    raise CalError("Codeforces returned HTTP %s for %s" % (exc.code, method))
            except (urllib.error.URLError, OSError, ValueError) as exc:
                raise CalError("could not reach Codeforces (%s). Check the connection and run cf sync again."
                               % getattr(exc, "reason", exc))
            if data.get("status") == "FAILED" and "limit" in str(data.get("comment", "")).lower():
                time.sleep(PAUSE * (attempt + 2))
                continue
            break
    if not isinstance(data, dict) or data.get("status") != "OK":
        raise CalError("Codeforces: %s" % ((data or {}).get("comment") or "request failed"))
    return data["result"]


def _pause() -> None:
    if not os.environ.get("CALAMITY_CF_FIXTURES"):
        time.sleep(PAUSE)


def target_rating(repo: Repo):
    """The learner's rating target as a number, or None when it is unset or unreadable."""
    try:
        value = int(float(repo.prof("cp.target_rating")))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def handle_of(repo: Repo) -> str:
    handle = str(repo.prof("cp.handle") or "")
    if not handle:
        raise CalError("no Codeforces handle linked. Run: cf link <handle>")
    return handle


def link(repo: Repo, handle: str) -> str:
    if not HANDLE_RE.match(handle or ""):
        raise CalError("that does not look like a Codeforces handle")
    users = _fetch("user.info", {"handles": handle})
    if not users:
        raise CalError("Codeforces has no user %r" % handle)
    user = users[0]
    repo.set_profile("cp.handle", user.get("handle", handle))
    return "linked Codeforces handle %s (rating %s, max %s). Next: cf sync" % (
        user.get("handle", handle), user.get("rating", "unrated"), user.get("maxRating", "-"))


def _age_hours(stamp, when) -> float:
    try:
        return (when - parse_ts(stamp)).total_seconds() / 3600.0
    except (TypeError, ValueError):
        return 1e9


def sync(repo: Repo, tree=None, state=None, full: bool = False) -> str:
    handle = handle_of(repo)
    when = now()
    info = _fetch("user.info", {"handles": handle})[0]
    _pause()
    rating = _fetch("user.rating", {"handle": handle})
    _pause()
    status = _fetch("user.status", {"handle": handle})
    repo.write_json_cache("cf/user-%s.json" % handle.lower(),
                          {"fetched": iso(when), "info": info, "rating": rating, "status": status})
    notes = []
    ps = repo.read_json_cache("cf/problemset.json")
    if full or ps is None or _age_hours(ps.get("fetched"), when) > 72:
        _pause()
        result = _fetch("problemset.problems", {})
        repo.write_json_cache("cf/problemset.json", {"fetched": iso(when), "problems": result.get("problems", []),
                                                     "problemStatistics": result.get("problemStatistics", [])})
        notes.append("problem set refreshed (%d problems)" % len(result.get("problems", [])))
    cs = repo.read_json_cache("cf/contests.json")
    if full or cs is None or _age_hours(cs.get("fetched"), when) > 12:
        _pause()
        contests = _fetch("contest.list", {"gym": "false"})
        repo.write_json_cache("cf/contests.json", {"fetched": iso(when), "contests": contests})
        notes.append("contest list refreshed")
    solved = len({_pkey(s.get("problem", {})) for s in status if s.get("verdict") == "OK"} - {None})
    line = "synced %s: rating %s (max %s), %d rated contests, %d submissions, %d problems solved" % (
        handle, info.get("rating", "unrated"), info.get("maxRating", "-"), len(rating), len(status), solved)
    if tree is not None and state is not None:
        notes += record_milestones(repo, tree, state, rating)
    return "\n".join([line] + notes)


def milestone_nodes(tree) -> list:
    """[(rating, node)] for the rating milestones of the cp track, lowest first."""
    out = []
    for node in tree.live():
        if node.track == "cp" and node.kind == "milestone":
            try:
                out.append((int(node.meta.get("rating")), node))
            except (TypeError, ValueError):
                continue
    return sorted(out, key=lambda r: (r[0], r[1].id))


def record_milestones(repo: Repo, tree, state, changes) -> list:
    """Mark rating milestones as passed once the rating history shows them. Returns report lines."""
    lines = []
    for need, node in milestone_nodes(tree):
        sk = state.skills.get(node.id)
        if sk is not None and sk.boss_ok:
            continue
        hit = next((c for c in changes if int(c.get("newRating") or 0) >= need), None)
        if hit is None:
            continue
        evidence = "Codeforces rating %s after %s (contest %s)" % (
            hit.get("newRating"), hit.get("contestName", "a rated contest"), hit.get("contestId", "?"))
        repo.append("boss", key="cf-milestone:%s" % node.id, skill=node.id, ok=True, kind="rating", evidence=evidence)
        lines.append("milestone reached: %s | %s (%s)" % (node.id, node.title, evidence))
    return lines


def next_milestone(tree, state, rating):
    """The lowest rating milestone not passed yet, as (rating, node), or None."""
    for need, node in milestone_nodes(tree):
        sk = state.skills.get(node.id)
        if not (sk is not None and sk.boss_ok) and (not rating or need > int(rating)):
            return need, node
    return None


def load(repo: Repo):
    """Cached Codeforces data, or None if never synced."""
    handle = str(repo.prof("cp.handle") or "")
    if not handle:
        return None
    user = repo.read_json_cache("cf/user-%s.json" % handle.lower())
    if user is None:
        return None
    ps = repo.read_json_cache("cf/problemset.json") or {}
    cs = repo.read_json_cache("cf/contests.json") or {}
    return {"handle": handle, "fetched": user.get("fetched"), "info": user.get("info") or {},
            "rating": user.get("rating") or [], "status": user.get("status") or [],
            "problems": ps.get("problems") or [], "pstats": ps.get("problemStatistics") or [],
            "contests": cs.get("contests") or []}


def _need(repo: Repo) -> dict:
    handle_of(repo)
    data = load(repo)
    if data is None:
        raise CalError("no Codeforces data cached on this machine yet. Run: cf sync")
    return data


# ---------------------------------------------------------------- derived views


def _pkey(problem: dict):
    cid, index = problem.get("contestId"), problem.get("index")
    if cid is None or not index:
        return None
    return "%s%s" % (cid, index)


def _local(seconds, like: datetime) -> datetime:
    return datetime.fromtimestamp(int(seconds), tz=like.tzinfo)


def problems_seen(data: dict) -> dict:
    """Per problem the learner has submitted: tries, verdicts, contest flags."""
    out = {}
    for sub in sorted(data["status"], key=lambda s: (s.get("creationTimeSeconds", 0), s.get("id", 0))):
        problem = sub.get("problem") or {}
        key = _pkey(problem)
        if key is None:
            continue
        rec = out.get(key)
        if rec is None:
            rec = out[key] = {"key": key, "name": problem.get("name", ""), "rating": problem.get("rating"),
                              "tags": list(problem.get("tags") or []), "contest": problem.get("contestId"),
                              "index": problem.get("index"), "first": sub.get("creationTimeSeconds", 0),
                              "last": 0, "ac": None, "tries": 0, "tries_before_ac": 0, "in_contest": False,
                              "ac_in_contest": False}
        rec["last"] = sub.get("creationTimeSeconds", 0)
        ptype = (sub.get("author") or {}).get("participantType")
        live = ptype in CONTEST_TYPES
        rec["in_contest"] = rec["in_contest"] or live
        verdict = sub.get("verdict")
        if verdict in (None, "TESTING", "SKIPPED", "SUBMITTED"):
            continue
        rec["tries"] += 1
        if verdict == "OK":
            if rec["ac"] is None:
                rec["ac"] = sub.get("creationTimeSeconds", 0)
                rec["ac_in_contest"] = live
        elif rec["ac"] is None and verdict != "COMPILATION_ERROR":
            rec["tries_before_ac"] += 1
    return out


def current_rating(data: dict):
    return data["info"].get("rating")


def practice_level(seen: dict, since: int) -> int | None:
    """Mean rating of the hardest fifth of problems solved since `since` (at least 5)."""
    ratings = sorted((p["rating"] for p in seen.values() if p["ac"] and p["ac"] >= since and p["rating"]), reverse=True)
    if len(ratings) < 5:
        return None
    top = ratings[: max(5, len(ratings) // 5)]
    return int(round(sum(top) / float(len(top))))


def base_rating(repo: Repo, data: dict, seen: dict, when) -> int:
    """The rating to aim practice from: the contest rating, or practice level for the unrated."""
    r = current_rating(data)
    if r:
        return int(r)
    level = practice_level(seen, int((when - timedelta(days=180)).timestamp()))
    return max(800, (level - 200) if level else 800)


def tag_table(repo: Repo, tree, data: dict, seen: dict, when, days: int = 180) -> list:
    """Per-tag strength over the window, weakest first."""
    since = int((when - timedelta(days=days)).timestamp())
    base = practice_level(seen, since) or base_rating(repo, data, seen, when)
    tags = {}
    for p in seen.values():
        if p["last"] < since:
            continue
        for tag in p["tags"]:
            if tag.startswith("*"):
                continue
            t = tags.setdefault(tag, {"tag": tag, "solved": [], "attempted": 0, "unsolved": 0, "tries": 0})
            t["attempted"] += 1
            if p["ac"]:
                t["tries"] += p["tries_before_ac"]
                if p["rating"]:
                    t["solved"].append(p["rating"])
                else:
                    t["solved"].append(0)
            else:
                t["unsolved"] += 1
    rating = base_rating(repo, data, seen, when)
    expected = {}
    for node in tree.live():
        if node.track == "cp" and node.cf_tags and node.band <= rating + 200:
            for tag in node.cf_tags:
                expected.setdefault(tag, node.id)
    skill_for = tag_skills(tree, rating)
    rows = []
    for tag in sorted(set(tags) | set(expected)):
        t = tags.get(tag, {"tag": tag, "solved": [], "attempted": 0, "unsolved": 0, "tries": 0})
        if tag not in expected and t["attempted"] < 3:
            continue
        rated = sorted((r for r in t["solved"] if r), reverse=True)
        level = int(round(sum(rated[:3]) / float(len(rated[:3])))) if len(rated) >= 3 else None
        gap = 0.5 if level is None else max(0.0, min(1.0, (base - level) / 400.0))
        fail = (t["unsolved"] / float(t["attempted"])) if t["attempted"] else 0.0
        under = (1.0 - min(1.0, len(t["solved"]) / 15.0)) if tag in expected else 0.0
        score = 0.45 * gap + 0.25 * fail + 0.30 * under
        solved_n = len(t["solved"])
        rows.append({"tag": tag, "solved": solved_n, "attempted": t["attempted"], "unsolved": t["unsolved"],
                     "level": level, "tries": (t["tries"] / float(solved_n)) if solved_n else None,
                     "score": score, "expected": tag in expected, "skill": skill_for.get(tag)})
    rows.sort(key=lambda r: (-r["score"], r["tag"]))
    return rows


def recommend(repo: Repo, tree, state, when, n: int = 5, tags=None, low=None, high=None, skill=None) -> dict:
    data = _need(repo)
    if skill and not csv_list(tags):
        node = tree.get(skill)
        if not node.cf_tags:
            raise CalError("%s lists no Codeforces tags (cf_tags); pass --tags instead" % node.id)
        tags = node.cf_tags
    if not data["problems"]:
        raise CalError("the problem set is not cached yet. Run: cf sync")
    seen = problems_seen(data)
    rating = base_rating(repo, data, seen, when)
    lo = rating + int(repo.cfg("cp.band_low", 100) if low is None else low)
    hi = rating + int(repo.cfg("cp.band_high", 300) if high is None else high)
    lo = max(800, int(math.floor(lo / 100.0)) * 100)
    hi = max(lo, int(math.ceil(hi / 100.0)) * 100)
    weak = {r["tag"]: r["score"] for r in tag_table(repo, tree, data, seen, when)}
    wanted = set(csv_list(tags))
    solved_count = {"%s%s" % (s.get("contestId"), s.get("index")): s.get("solvedCount", 0) for s in data["pstats"]}
    solved_names = {p["name"] for p in seen.values() if p["ac"]}
    skipped = {k for k, rec in state.cp_marks.items() if any(m[1] == "skip" for m in rec["marks"])}
    max_cid = max((p.get("contestId") or 0 for p in data["problems"] if (p.get("contestId") or 0) < 100000), default=1)
    rows = []
    for p in data["problems"]:
        key = _pkey(p)
        prating = p.get("rating")
        if key is None or not prating or not lo <= prating <= hi:
            continue
        if (p.get("contestId") or 0) >= 100000 or key in seen or key in skipped:
            continue
        ptags = [t for t in (p.get("tags") or [])]
        if any(t.startswith("*") for t in ptags) or p.get("name") in solved_names:
            continue
        if wanted and not wanted & set(ptags):
            continue
        scored = [(weak.get(t, 0.0), t) for t in ptags if t in weak]
        w, top_tag = max(scored) if scored else (0.1, (ptags[0] if ptags else "untagged"))
        quality = math.log10(solved_count.get(key, 0) + 10) / 5.0
        recency = (p.get("contestId") or 0) / float(max_cid)
        rows.append((0.6 * w + 0.25 * min(1.0, quality) + 0.15 * recency, key, p, top_tag))
    rows.sort(key=lambda r: (-r[0], r[1]))
    picked, per_tag = [], {}
    cap = max(1, int(math.ceil(n / 2.0)))
    for score, key, p, top_tag in rows:
        if len(picked) >= n:
            break
        if per_tag.get(top_tag, 0) >= cap:
            continue
        per_tag[top_tag] = per_tag.get(top_tag, 0) + 1
        picked.append({"key": key, "name": p.get("name", ""), "rating": p.get("rating"),
                       "tags": p.get("tags") or [], "why": top_tag, "solved_by": solved_count.get(key, 0)})
    open_assigned = []
    for a in state.cp_assigned:
        rec = seen.get(a["problem"])
        if (rec is None or not rec["ac"]) and a["problem"] not in [x["problem"] for x in open_assigned]:
            open_assigned.append(a)
    return {"rating": rating, "lo": lo, "hi": hi, "picked": picked, "open_assigned": open_assigned,
            "tags": sorted(wanted)}


def problem_url(key: str) -> str:
    m = PROBLEM_RE.match(key)
    return "https://codeforces.com/problemset/problem/%s/%s" % (m.group(1), m.group(2)) if m else ""


def recommend_text(repo: Repo, tree, state, when, n: int = 5, tags=None, low=None, high=None, hide_tags: bool = True,
                   skill=None) -> str:
    rec = recommend(repo, tree, state, when, n, tags, low, high, skill)
    lines = ["practice set for rating %d: problems rated %d-%d%s" % (
        rec["rating"], rec["lo"], rec["hi"], (" · tags: " + ", ".join(rec["tags"])) if rec["tags"] else "")]
    if rec["open_assigned"]:
        lines.append("still open from earlier assignments: %s" % ", ".join(a["problem"] for a in rec["open_assigned"][:8]))
    if not rec["picked"]:
        lines.append("no unsolved problem matches. Widen the band (--low/--high) or drop the tag filter.")
        return "\n".join(lines)
    rows = []
    for p in rec["picked"]:
        row = [p["key"], p["name"], p["rating"], p["solved_by"]]
        if not hide_tags:
            row.append(p["why"])
        rows.append(row)
    head = ["problem", "name", "rating", "solved by"] + ([] if hide_tags else ["chosen for"])
    lines.append(table(rows, head, aligns="llrr" + ("" if hide_tags else "l")))
    lines.append("open one: https://codeforces.com/problemset/problem/<contest>/<index>")
    if hide_tags:
        lines.append("tags are hidden on purpose: recognising the technique is part of the practice (--show-tags to see why each was chosen).")
    lines.append("record the set: cf assign %s --reason \"...\"" % " ".join(p["key"] for p in rec["picked"]))
    return "\n".join(lines)


def analyse_text(repo: Repo, tree, state, when, days: int = 180) -> str:
    data = _need(repo)
    seen = problems_seen(data)
    since = int((when - timedelta(days=days)).timestamp())
    solved = [p for p in seen.values() if p["ac"]]
    recent = [p for p in solved if p["ac"] >= since]
    rating = current_rating(data)
    level = practice_level(seen, since)
    lines = ["%s: rating %s (max %s) · %d solved in all, %d in the last %d days · practice level %s" % (
        data["handle"], rating if rating else "unrated", data["info"].get("maxRating", "-"), len(solved),
        len(recent), days, level if level else "n/a (needs 5 rated solves)")]
    week = int((when - timedelta(days=7)).timestamp())
    month = int((when - timedelta(days=30)).timestamp())
    lines.append("solved: %d in 7 days, %d in 30 days" % (
        sum(1 for p in solved if p["ac"] >= week), sum(1 for p in solved if p["ac"] >= month)))
    buckets = {}
    for p in recent:
        if p["rating"]:
            buckets[p["rating"]] = buckets.get(p["rating"], 0) + 1
    if buckets:
        lines.append("solved by rating (last %d days): %s" % (
            days, "  ".join("%d:%d" % (r, c) for r, c in sorted(buckets.items()))))
    rows = tag_table(repo, tree, data, seen, when, days)
    practised = [r for r in rows if r["attempted"]]
    untouched = [r for r in rows if not r["attempted"] and r["expected"]]
    if practised:
        body = []
        for r in practised[:14]:
            body.append([r["tag"], r["solved"], r["unsolved"], r["level"] or "-",
                         ("%.1f" % r["tries"]) if r["tries"] is not None else "-",
                         "%.2f" % r["score"], "yes" if r["expected"] else "", r["skill"] or ""])
        lines.append("")
        lines.append("tags, weakest first (level = mean of the 3 hardest solved; tries = wrong tries before AC)")
        lines.append(table(body, ["tag", "solved", "unsolved", "level", "tries", "weakness", "due at this rating", "tree skill"],
                           aligns="lrrrrrll"))
    if untouched:
        lines.append("")
        lines.append("due at this rating but not practised in the last %d days: %s" % (
            days, ", ".join("%s (%s)" % (r["tag"], r["skill"]) for r in untouched[:16])))
    subtags = {}
    for key, rec in state.cp_marks.items():
        for tag in rec["subtags"]:
            subtags.setdefault(tag, []).append(key)
    if subtags:
        lines.append("")
        lines.append("sub-tags recorded by the coach: " + ", ".join(
            "%s x%d" % (t, len(v)) for t, v in sorted(subtags.items(), key=lambda kv: (-len(kv[1]), kv[0]))))
    lines.append("synced %s" % fmt_delta(parse_ts(data["fetched"]) - when))
    return "\n".join(lines)


def upsolve_text(repo: Repo, tree, state, when, limit: int = 12) -> str:
    data = _need(repo)
    seen = problems_seen(data)
    lines = []
    open_ = sorted((p for p in seen.values() if not p["ac"] and p["tries"] > 0), key=lambda p: (-int(p["in_contest"]), -p["last"]))
    if open_:
        rows = [[p["key"], p["name"], p["rating"] or "-", p["tries"], "contest" if p["in_contest"] else "practice",
                 fmt_delta(_local(p["last"], when) - when)] for p in open_[:limit]]
        lines.append("attempted but never solved (contest problems first):")
        lines.append(table(rows, ["problem", "name", "rating", "tries", "from", "last try"], aligns="llrrll"))
    by_contest = {}
    for p in data["problems"]:
        if p.get("contestId") is not None:
            by_contest.setdefault(p["contestId"], []).append(p)
    live = {}
    for p in seen.values():
        if p["in_contest"] and p["contest"] is not None:
            live[p["contest"]] = max(live.get(p["contest"], 0), p["last"])
    nxt = []
    for cid, last in sorted(live.items(), key=lambda kv: -kv[1])[:6]:
        for p in sorted(by_contest.get(cid, []), key=lambda q: q.get("index", "")):
            key = _pkey(p)
            if key in seen and seen[key]["ac"]:
                continue
            if key not in seen:
                nxt.append([key, p.get("name", ""), p.get("rating") or "-", "first problem not reached in contest %s" % cid])
            break
    if nxt:
        lines.append("")
        lines.append("next step up after each recent contest:")
        lines.append(table(nxt, ["problem", "name", "rating", "why"], aligns="llrl"))
    redo = []
    for key, rec in state.cp_marks.items():
        last_editorial = max((m[0] for m in rec["marks"] if m[1] == "editorial"), default=None)
        last_resolved = max((m[0] for m in rec["marks"] if m[1] == "resolved"), default=None)
        if last_editorial and (last_resolved is None or last_resolved < last_editorial):
            due = last_editorial + timedelta(days=int(repo.cfg("cp.resolve_days", 7)))
            redo.append((due, key))
    if redo:
        lines.append("")
        lines.append("solve again without the editorial:")
        for due, key in sorted(redo):
            lines.append("  %s  due %s" % (key, fmt_delta(due - when)))
    if not lines:
        return "Nothing to upsolve: no unsolved attempts, no open re-solves."
    lines.append("")
    lines.append("after reading an editorial: cf mark <problem> editorial   (it comes back in a week); after a clean re-solve: cf mark <problem> resolved")
    return "\n".join(lines)


def _division(name: str) -> str:
    low = name.lower()
    if "div. 1 + div. 2" in low or "div. 1 and div. 2" in low:
        return "1+2"
    for d in ("4", "3", "2", "1"):
        if "div. %s" % d in low:
            return d
    if "educational" in low:
        return "edu"
    return "other"


def tag_skills(tree, rating: int) -> dict:
    """For each Codeforces tag, the skill of the tree that teaches it at this rating.

    A tag can belong to several skills (`data structures`: the STL early, range queries later):
    the one with the highest band within 200 of the rating wins, else the lowest band.
    """
    owners = {}
    for node in tree.live():
        if node.track == "cp":
            for tag in node.cf_tags:
                owners.setdefault(tag, []).append(node)
    out = {}
    for tag, nodes in owners.items():
        near = [n for n in nodes if n.band <= rating + 200]
        out[tag] = (max(near, key=lambda n: (n.band, n.id)) if near else min(nodes, key=lambda n: (n.band, n.id))).id
    return out


def suited_divisions(rating: int) -> tuple:
    if rating < 1200:
        return ("4", "3", "edu")
    if rating < 1600:
        return ("3", "2", "edu")
    if rating < 1900:
        return ("2", "edu", "1+2")
    return ("1", "1+2", "edu")


def running(data: dict, when) -> list:
    """Contests running at `when`, judged by their start and length: the phases in the cache are only
    as fresh as the last sync, and a contest listed as upcoming then may have started since."""
    now = when.timestamp()
    out = []
    for c in data.get("contests") or []:
        start, length = c.get("startTimeSeconds"), c.get("durationSeconds") or 0
        if c.get("phase") in ("BEFORE", "CODING") and isinstance(start, (int, float)) and start <= now < start + length:
            out.append(c)
    return sorted(out, key=lambda c: c["startTimeSeconds"])


def contests_text(repo: Repo, tree, state, when, n: int = 5) -> str:
    data = _need(repo)
    seen = problems_seen(data)
    rating = base_rating(repo, data, seen, when)
    lines = []
    live = running(data, when)
    if live:
        rows = [[c["id"], c.get("name", ""), _local(c["startTimeSeconds"] + c.get("durationSeconds", 0), when)
                 .strftime("%a %d %b %H:%M")] for c in live]
        lines.append("RUNNING NOW (local time of the end):")
        lines.append(table(rows, ["id", "name", "ends"]))
        lines.append("During a rated contest, give no help of any kind with its problems (problem ids start with "
                     "the contest id), until it has ended.")
        lines.append("")
    live_ids = {c["id"] for c in live}
    upcoming = sorted((c for c in data["contests"] if c.get("phase") == "BEFORE" and c.get("startTimeSeconds")
                       and c["id"] not in live_ids and c["startTimeSeconds"] > when.timestamp()),
                      key=lambda c: c["startTimeSeconds"])
    if upcoming:
        rows = [[c["id"], c.get("name", ""), _local(c["startTimeSeconds"], when).strftime("%a %d %b %H:%M"),
                 "%dh%02d" % (c.get("durationSeconds", 0) // 3600, (c.get("durationSeconds", 0) % 3600) // 60)]
                for c in upcoming[:n]]
        lines.append("upcoming contests (local time):")
        lines.append(table(rows, ["id", "name", "starts", "length"]))
    took_part = {s.get("contestId") for s in data["status"]
                 if (s.get("author") or {}).get("participantType") in CONTEST_TYPES}
    touched = {s.get("contestId") for s in data["status"]}
    wanted = suited_divisions(rating)
    cutoff = when.timestamp() - 14 * 86400
    past = [c for c in data["contests"]
            if c.get("phase") == "FINISHED" and c.get("startTimeSeconds", 0) < cutoff
            and c["id"] not in touched and _division(c.get("name", "")) in wanted]
    past.sort(key=lambda c: -c.get("startTimeSeconds", 0))
    if past:
        rows = [[c["id"], c.get("name", ""), "Div. " + _division(c.get("name", "")) if _division(c.get("name", "")) != "edu" else "Educational"]
                for c in past[:3]]
        lines.append("")
        lines.append("virtual contest candidates for rating %d (never opened by this handle):" % rating)
        lines.append(table(rows, ["id", "name", "kind"]))
        lines.append("start one at https://codeforces.com/contest/<id>/virtual ; afterwards run cf sync and cf upsolve")
    changes = data["rating"][-5:]
    if changes:
        rows = [[c.get("contestId"), c.get("contestName", ""), c.get("rank"),
                 "%d -> %d" % (c.get("oldRating", 0), c.get("newRating", 0)),
                 "%+d" % (c.get("newRating", 0) - c.get("oldRating", 0))] for c in reversed(changes)]
        lines.append("")
        lines.append("last rated contests:")
        lines.append(table(rows, ["id", "contest", "rank", "rating", "change"], aligns="llrlr"))
    lines.append("")
    lines.append("rated contests: %d · contests with submissions made as a participant (rated, virtual or "
                 "unofficial): %d" % (len(data["rating"]), len(took_part - {None})))
    return "\n".join(lines)


def rating_text(repo: Repo, state, when, tree=None) -> str:
    data = _need(repo)
    changes = data["rating"]
    rating = current_rating(data)
    lines = ["%s: rating %s, max %s, %d rated contests" % (
        data["handle"], rating if rating else "unrated", data["info"].get("maxRating", "-"), len(changes))]
    if changes:
        rows = [[_local(c["ratingUpdateTimeSeconds"], when).date().isoformat(), c.get("contestName", ""),
                 c.get("rank"), c.get("newRating"), "%+d" % (c.get("newRating", 0) - c.get("oldRating", 0))]
                for c in changes[-10:]]
        lines.append(table(rows, ["date", "contest", "rank", "rating", "change"], aligns="llrrr"))
        for span in (30, 90):
            since = (when - timedelta(days=span)).timestamp()
            inside = [c for c in changes if c["ratingUpdateTimeSeconds"] >= since]
            if inside:
                lines.append("last %d days: %+d over %d contest(s)" % (
                    span, inside[-1]["newRating"] - inside[0]["oldRating"], len(inside)))
            else:
                lines.append("last %d days: no rated contest" % span)
        if len(changes) < 6:
            lines.append("Fewer than six rated contests: Codeforces is still settling a new account's displayed "
                         "rating, so these early gains overstate the pace.")
    target = target_rating(repo)
    target_date = repo.prof("cp.target_date")
    if target and rating:
        gap = int(target) - int(rating)
        line = "target %s: %d point(s) to go" % (target, gap) if gap > 0 else "target %s reached" % target
        if gap > 0 and target_date:
            try:
                months = max(0.5, (parse_ts(str(target_date)) - when).days / 30.4)
                line += " by %s, which needs about %+d a month" % (target_date, round(gap / months))
                since = (when - timedelta(days=90)).timestamp()
                inside = [c for c in changes if c["ratingUpdateTimeSeconds"] >= since]
                if inside:
                    pace = (inside[-1]["newRating"] - inside[0]["oldRating"]) / 3.0
                    line += "; the last 90 days ran at %+d a month" % round(pace)
            except (TypeError, ValueError):
                pass
        lines.append(line)
        lines.append("A rating target is a direction, not a promise: it moves with contests entered and problems solved above your level.")
    if tree is not None:
        nxt = next_milestone(tree, state, rating)
        if nxt is not None:
            need, node = nxt
            lines.append("next milestone: %s | %s%s" % (
                node.id, node.title, (" (%d to go)" % (need - int(rating))) if rating else ""))
    lines.append("synced %s" % fmt_delta(parse_ts(data["fetched"]) - when))
    return "\n".join(lines)


def status_text(repo: Repo, state, when) -> str:
    handle = str(repo.prof("cp.handle") or "")
    if not handle:
        return "No Codeforces handle linked. Run: cf link <handle>"
    data = load(repo)
    if data is None:
        return "Handle %s is linked, but nothing is cached on this machine. Run: cf sync" % handle
    seen = problems_seen(data)
    week = (when - timedelta(days=7)).timestamp()
    solved_week = sum(1 for p in seen.values() if p["ac"] and p["ac"] >= week)
    return "%s: rating %s (max %s) · %d solved, %d this week · %d rated contests · synced %s" % (
        handle, current_rating(data) or "unrated", data["info"].get("maxRating", "-"),
        sum(1 for p in seen.values() if p["ac"]), solved_week, len(data["rating"]),
        fmt_delta(parse_ts(data["fetched"]) - when))


def brief_lines(repo: Repo, state, when) -> list:
    handle = str(repo.prof("cp.handle") or "")
    if not handle:
        return []
    data = load(repo)
    if data is None:
        return ["Codeforces %s: not synced on this machine yet." % handle]
    line = "Codeforces " + status_text(repo, state, when)
    target = target_rating(repo)
    rating = current_rating(data)
    if target and rating and int(target) > int(rating):
        line += " · target %s (%d to go)" % (target, int(target) - int(rating))
    return [line]


# ---------------------------------------------------------------- coach records


def _check_problem(key: str) -> str:
    key = str(key).strip().upper()
    if not PROBLEM_RE.match(key):
        raise CalError("problems are written like 1520C or 1843F2; got %r" % key)
    return key


def mark(repo: Repo, problem: str, what: str, subtags=None, note: str | None = None) -> str:
    key = _check_problem(problem)
    if what not in ("editorial", "resolved", "skip", "subtag", "note"):
        raise CalError("mark is one of: editorial, resolved, skip, subtag, note")
    tags = [t.lower() for t in csv_list(subtags)]
    if what == "subtag" and not tags:
        raise CalError("give the sub-tags: cf mark %s subtag --subtags dp-knapsack,dp-bitmask" % key)
    repo.append("cp_mark", problem=key, mark=what, subtags=tags or None, note=note)
    return "marked %s: %s%s" % (key, what, (" [" + ", ".join(tags) + "]") if tags else "")


def credit(repo: Repo, tree, state, when, problem: str, topic: str, also=None, hints: int = 0,
           note: str | None = None) -> str:
    """Count a problem the handle solved on Codeforces as a verified exercise for a topic.

    The judge is the check: an accepted verdict in the synced data is the
    evidence. A solve that followed the editorial schedules the topic but is
    not counted as evidence until the problem is solved again without it.
    """
    from . import fsrs, plan, session
    from .state import State

    key = _check_problem(problem)
    primary = tree.topic(topic).key
    if tree.get(primary.split("/", 1)[0]).track != "cp":
        raise CalError("cf credit is for topics of the competitive-programming track; %s is not one" % primary)
    topics = [primary]
    for other in csv_list(also):
        other = tree.topic(other).key
        if other not in topics:
            topics.append(other)
    rec = problems_seen(_need(repo)).get(key)
    if rec is None or not rec["ac"]:
        raise CalError("%s has no accepted submission in the synced data. Run cf sync after solving it." % key)
    marks = state.cp_marks.get(key, {"marks": []})["marks"]
    editorial = max((m[0] for m in marks if m[1] == "editorial"), default=None)
    resolved = max((m[0] for m in marks if m[1] == "resolved"), default=None)
    assisted = editorial is not None and (resolved is None or resolved < editorial)
    earlier = state.cp_credits.get(key, {}).get(primary)
    if earlier is True or (earlier is False and assisted):
        raise CalError("%s is already credited to %s%s" % (
            key, primary, "" if earlier else " (as a solve that followed the editorial; solve it again without "
                                             "it, then: cf mark %s resolved)" % key))
    solved_at = _local(rec["ac"], when)
    if resolved is not None and resolved > solved_at:
        solved_at = resolved
    window = int(repo.cfg("cp.credit_days", 14))
    age = (when - solved_at).days
    if age > window:
        raise CalError("%s was solved %d days ago. Credit covers the last %d days; record older knowledge with a "
                       "placement test instead." % (key, age, window))
    wrong = rec["tries_before_ac"]
    grade = fsrs.HARD if (assisted or wrong or hints) else fsrs.GOOD
    evidence = "Codeforces accepted %s (%s%s), %d wrong submission(s) before it%s" % (
        key, rec["name"], (", rated %s" % rec["rating"]) if rec["rating"] else "", wrong,
        "; solved in a contest" if rec["ac_in_contest"] else "")
    made = session._record(repo, tree, state, when, primary, topics, True, grade, hints, None,
                           key="cfcredit:%s:%s%s" % (key, primary, "" if assisted else ":clean"), problem=key,
                           verified=True,
                           after_reveal=assisted or None, evidence=evidence, note=note, kind="cf")
    new_state = State(repo, tree)
    lines = ["CREDITED %s -> %s" % (key, primary)]
    lines.extend(session._credit_lines(new_state, when, made))
    if assisted:
        lines.append("note: the editorial was used, so this schedules the topic but is not counted as evidence. "
                     "Solve it again without the editorial, then: cf mark %s resolved" % key)
    lines.append(session.describe_topic(repo, new_state, primary))
    lines.append(plan.today_line(plan.today(repo, tree, new_state, when)))
    return "\n".join(lines)


def assign(repo: Repo, problems, reason: str | None) -> str:
    keys = [_check_problem(p) for p in problems]
    if not keys:
        raise CalError("name at least one problem")
    repo.append("cp_assign", problems=keys, reason=reason)
    return "assigned %d problem(s): %s" % (len(keys), ", ".join(keys))
