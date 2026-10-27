"""A disposable snapshot of a replayed state, so a command need not replay the whole log.

The event log stays the only source of truth. After a replay, the state it produced (before the
end-of-replay summaries) is written to `.calamity/cache/replay.json` together with exactly what
it was built from: for every log file, the bytes consumed and their SHA-1, the last event in
replay order, and a key over everything else replay reads (the engine's own code, config.md,
the profile, the GATE year files, each skill's track and paper).

The next command uses the snapshot only if all of that still holds, and then replays just the
events written since, which must all come after the snapshot's last event and must not be of a
kind that changes earlier events (`rename`, `void`, `errtag`). In every other case (a file
rewritten or removed, events merged in from another laptop with earlier times, a changed
profile, a newer engine, a damaged or missing snapshot) the whole log is replayed and a new
snapshot written. Deleting the file is always safe. Set CALAMITY_NO_CACHE=1 to bypass it.

The snapshot is JSON, never pickle: loading it can never run code.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime

from . import fsrs
from .store import Repo, log_text, write_text

FORMAT = 5
NAME = "replay.json"
GLOBAL_TYPES = ("rename", "void", "errtag")  # events that change how earlier events are read


class Uncacheable(Exception):
    """The state holds something JSON cannot carry back unchanged; replay fully instead."""


def enabled() -> bool:
    return os.environ.get("CALAMITY_NO_CACHE", "").strip() in ("", "0")


def path(repo: Repo) -> str:
    return os.path.join(repo.cache_dir, NAME)


# ---------------------------------------------------------------- what replay reads besides the log


def inputs_key(repo: Repo, tree) -> str:
    h = hashlib.sha256()
    h.update(("format %d python %d.%d\n" % ((FORMAT,) + sys.version_info[:2])).encode())
    engine = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(engine, n) for n in sorted(os.listdir(engine)) if n.endswith(".py")]
    files += [os.path.join(repo.framework, "config.md"), repo.profile_path]
    for folder in (os.path.join(repo.framework, "gate"), os.path.join(repo.learner, "gate")):
        if os.path.isdir(folder):
            files += [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if n.endswith(".md")]
    for name in files:
        h.update(name.encode("utf-8", "replace") + b"\0")
        if name.startswith(engine + os.sep):
            try:
                with open(name, "rb") as fh:
                    raw = fh.read()
            except OSError:
                raw = None
        else:
            raw = repo.read_bytes(name)  # the bytes replay reads too, not a newer copy
        h.update(b"-" if raw is None else hashlib.sha256(raw).digest())
    for node in sorted(tree.nodes.values(), key=lambda n: n.id):
        h.update(("%s|%s|%s\n" % (node.id, node.track, node.paper)).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------- reading the log


def read_log(repo: Repo):
    """[(file name, bytes)] of every log file, and problems for files that could not be read."""
    files, problems = [], []
    for full in repo.event_files():
        name = os.path.basename(full)
        try:
            files.append((name, repo.read_event_file(name)))
        except OSError as exc:
            problems.append((name, 0, "unreadable (%s)" % exc))
    return files, problems


def consumed(raw: bytes):
    """How much of a file a snapshot may stand for: whole lines only. (size, sha1, newlines)."""
    size = raw.rfind(b"\n") + 1
    head = raw[:size]
    return size, hashlib.sha1(head).hexdigest(), head.count(b"\n")


def load(repo: Repo, key: str, files):
    """The stored snapshot and the unread tail of each file, or (None, why not)."""
    try:
        with open(path(repo), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None, "no snapshot"
    except (OSError, ValueError):
        return None, "snapshot unreadable"
    if not isinstance(data, dict) or data.get("format") != FORMAT or data.get("key") != key:
        return None, "inputs changed"
    seen = data.get("files")
    if not isinstance(seen, dict):
        return None, "snapshot damaged"
    present = {name for name, _ in files}
    if any(name not in present for name in seen):
        return None, "a log file is gone"
    tails = []
    for name, raw in files:
        try:
            size, sha, lines = seen.get(name, (0, hashlib.sha1(b"").hexdigest(), 0))
            if len(raw) < size or hashlib.sha1(raw[:size]).hexdigest() != sha:
                return None, "a log file changed"
            if size < len(raw):
                tails.append((name, raw[size:], int(lines) + 1))
        except (TypeError, ValueError, AttributeError):
            return None, "snapshot damaged"
    return data, tails


def save(repo: Repo, data: dict) -> None:
    try:
        write_text(path(repo), json.dumps(data, ensure_ascii=False, separators=(",", ":")), durable=False)
    except OSError:
        pass  # a cache that cannot be written is simply not used next time


def discard(repo: Repo) -> None:
    try:
        os.remove(path(repo))
    except OSError:
        pass


def tail_text(raw: bytes) -> str:
    """The text of a file's unread tail. Raises ValueError where a snapshot cannot be trusted."""
    if b"\r" in raw:
        raise ValueError("carriage return")
    return log_text(raw)


# ---------------------------------------------------------------- the state as JSON


def _t(dt):
    return None if dt is None else dt.isoformat()


def _d(text):
    return None if text is None else datetime.fromisoformat(text)


def _keys(mapping) -> dict:
    for k in mapping:
        if not isinstance(k, str):
            raise Uncacheable("key %r" % (k,))
    return mapping


def _card_out(card):
    if card is None:
        return None
    return [card.s, card.d, _t(card.last), _t(card.due), card.reps, card.lapses]


def _card_in(data):
    if data is None:
        return None
    s, d, last, due, reps, lapses = data
    return fsrs.Card(s, d, _d(last), _d(due), reps, lapses)


def encode_state(state) -> dict:
    """Everything a replay produced, as JSON values. Dict order is kept: it is part of the state."""
    topics = {}
    for key, ts in _keys(state.topics).items():
        topics[key] = [
            ts.key, _t(ts.covered_ts), ts.covered_by, _t(ts.first_ts), ts.first_day, _t(ts.last_ts), _card_out(ts.card),
            ts.n, ts.n_ok, ts.n_vok, [[_t(a), b, c] for a, b, c in ts.recent], sorted(ts.ok_days), sorted(ts.ok_items),
            ts.last_ok, _keys(dict(ts.errors)), ts.hints, ts.seeded, ts.open_day, _t(ts.open_due), ts.open_had_card,
            ts.fail_day, [[_t(a), b] for a, b in ts.err_log], ts.slow, [[_t(a), b, c] for a, b, c in ts.vok_log],
            ts.last_ev_ok, ts.ok_objs,
        ]
    skills = {}
    for key, sk in _keys(state.skills).items():
        skills[key] = [sk.enrolled, sk.mode, sk.paused, _t(sk.enrolled_ts), sk.known, _t(sk.known_ts), sk.boss_ok,
                       sk.boss_tries, _t(sk.boss_ts), _t(sk.last_ts), sk.unenrolled]
    items = {}
    for key, it in _keys(state.items).items():
        verify = None
        if it.verify is not None:
            verify = dict(it.verify, ts=_t(it.verify["ts"]))
        items[key] = [it.id, it.status, it.skill, list(it.topics), it.type, it.src, _t(it.shown_ts), it.open,
                      it.open_test, it.n_shown, it.n_ok, it.n_fail, it.last_ok, _t(it.last_ts), it.fail_day, verify,
                      it.reason, it.last_attempt, it.last_err, it.objectives, _keys(dict(it.objsig))]
    days = {}
    for key, ds in _keys(state.days).items():
        days[key] = [ds.day, ds.attempts, ds.ok, ds.new, ds.reviews, _t(ds.first), _t(ds.last), ds.active_min,
                     [[h, v[0], v[1]] for h, v in ds.hours.items()], ds.workout_min, ds.sessions, ds.src_done,
                     ds.src_min, [_t(x) for x in ds.stamps], ds.in_sleep, ds.taught]
    tests = {}
    for key, test in _keys(state.tests).items():
        answers = [[k, dict(v, ts=_t(v["ts"]))] for k, v in test["answers"].items()]
        tests[key] = dict(test, built=_t(test["built"]), finished=_t(test["finished"]), answers=answers)
    src = {}
    for key, entries in _keys(state.src).items():
        src[key] = {k: dict(v, ts=_t(v["ts"])) for k, v in _keys(entries).items()}
    return {
        "topics": topics, "skills": skills, "items": items, "days": days, "mocks": state.mocks, "tests": tests,
        "src": src, "notes": [dict(n, ts=_t(n["ts"])) for n in state.notes],
        "cp_marks": {k: {"marks": [[_t(a), b, c] for a, b, c in v["marks"]], "subtags": v["subtags"]}
                     for k, v in _keys(state.cp_marks).items()},
        "cp_assigned": [dict(a, ts=_t(a["ts"])) for a in state.cp_assigned],
        "cp_credits": {k: _keys(dict(v)) for k, v in _keys(state.cp_credits).items()},
        "weights": {k: [v[0], v[1]] for k, v in _keys(state.weights).items()},
        "first_tries": [[_t(a), b] for a, b in state.first_tries], "review_secs": list(state.review_secs),
        "last_dt": _t(state.last_dt), "n_events": state.n_events, "n_voided": state.n_voided,
        "alias_topic": _keys(state._alias_topic), "alias_skill": _keys(state._alias_skill),
        "retag": _keys(state._retag),
    }


def decode_state(state, data: dict) -> None:
    """Put an encoded state back into a fresh State object."""
    from .state import DayStats, ItemState, SkillState, TopicState

    for key, row in data["topics"].items():
        ts = TopicState(key)
        (ts.key, covered_ts, ts.covered_by, first_ts, ts.first_day, last_ts, card, ts.n, ts.n_ok, ts.n_vok, recent,
         ok_days, ok_items, ts.last_ok, errors, ts.hints, ts.seeded, ts.open_day, open_due, ts.open_had_card,
         ts.fail_day, err_log, ts.slow, vok_log, ts.last_ev_ok, ts.ok_objs) = row
        ts.covered_ts, ts.first_ts, ts.last_ts, ts.open_due = _d(covered_ts), _d(first_ts), _d(last_ts), _d(open_due)
        ts.card = _card_in(card)
        ts.recent = [(_d(a), b, c) for a, b, c in recent]
        ts.ok_days, ts.ok_items, ts.errors = set(ok_days), set(ok_items), dict(errors)
        ts.err_log = [(_d(a), b) for a, b in err_log]
        ts.vok_log = [(_d(a), b, c) for a, b, c in vok_log]
        state.topics[key] = ts
    for key, row in data["skills"].items():
        sk = SkillState()
        (sk.enrolled, sk.mode, sk.paused, enrolled_ts, sk.known, known_ts, sk.boss_ok, sk.boss_tries, boss_ts,
         last_ts, sk.unenrolled) = row
        sk.enrolled_ts, sk.known_ts, sk.boss_ts, sk.last_ts = _d(enrolled_ts), _d(known_ts), _d(boss_ts), _d(last_ts)
        state.skills[key] = sk
    for key, row in data["items"].items():
        it = ItemState(key)
        (it.id, it.status, it.skill, it.topics, it.type, it.src, shown_ts, it.open, it.open_test, it.n_shown, it.n_ok,
         it.n_fail, it.last_ok, last_ts, it.fail_day, verify, it.reason, it.last_attempt, it.last_err, it.objectives,
         it.objsig) = row
        it.objsig = dict(it.objsig)
        it.shown_ts, it.last_ts = _d(shown_ts), _d(last_ts)
        it.verify = None if verify is None else dict(verify, ts=_d(verify["ts"]))
        state.items[key] = it
    for key, row in data["days"].items():
        ds = DayStats(key)
        (ds.day, ds.attempts, ds.ok, ds.new, ds.reviews, first, last, ds.active_min, hours, ds.workout_min,
         ds.sessions, ds.src_done, ds.src_min, stamps, ds.in_sleep, ds.taught) = row
        ds.first, ds.last = _d(first), _d(last)
        ds.hours = {h: [n, ok] for h, n, ok in hours}
        ds.stamps = [_d(x) for x in stamps]
        state.days[key] = ds
    state.mocks = list(data["mocks"])
    for key, test in data["tests"].items():
        state.tests[key] = dict(test, built=_d(test["built"]), finished=_d(test["finished"]),
                                answers={k: dict(v, ts=_d(v["ts"])) for k, v in test["answers"]})
    for key, entries in data["src"].items():
        state.src[key] = {k: dict(v, ts=_d(v["ts"])) for k, v in entries.items()}
    state.notes = [dict(n, ts=_d(n["ts"])) for n in data["notes"]]
    state.cp_marks = {k: {"marks": [(_d(a), b, c) for a, b, c in v["marks"]], "subtags": list(v["subtags"])}
                      for k, v in data["cp_marks"].items()}
    state.cp_assigned = [dict(a, ts=_d(a["ts"])) for a in data["cp_assigned"]]
    state.cp_credits = {k: dict(v) for k, v in data["cp_credits"].items()}
    state.weights = {k: (v[0], v[1]) for k, v in data["weights"].items()}
    state.first_tries = [(_d(a), b) for a, b in data["first_tries"]]
    state.review_secs = list(data["review_secs"])
    state.last_dt = _d(data["last_dt"])
    state.n_events, state.n_voided = data["n_events"], data["n_voided"]
    state._alias_topic, state._alias_skill = dict(data["alias_topic"]), dict(data["alias_skill"])
    state._retag = dict(data["retag"])
