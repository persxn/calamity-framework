"""Replay the event log into the learner's current state.

Nothing here is stored: schedules, mastery and statistics are recomputed
from learner/events on every run, so two machines that have merged the same
events always agree, whatever order the files arrive in.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

from . import fsrs, gateinfo, snapshot
from .store import Repo, format_problems, log_text, order_and_dedup, order_key, parse_event_text
from .tree import Tree
from .util import CalError, ceil_int, day_bounds, daykey, in_window, parse_hhmm, utc

TOPIC_ORDER = ("new", "covered", "learning", "consolidating", "solid", "mastered")
PACES = ("mastery", "exam", "brushup")
OPEN = ("covered", "learning")      # taught or answered, not yet secured: what the WIP limit counts
SATISFIED = ("known", "ready", "mastered")


class TopicState:
    __slots__ = (
        "key", "covered_ts", "covered_by", "first_ts", "first_day", "last_ts", "card", "n", "n_ok",
        "n_vok", "recent", "ok_days", "ok_items", "last_ok", "errors", "hints", "seeded",
        "open_day", "open_due", "open_had_card", "fail_day", "err_log", "slow", "vok_log", "last_ev_ok", "ok_objs",
    )

    def __init__(self, key: str):
        self.key = key
        self.covered_ts = None
        self.covered_by = None
        self.first_ts = None
        self.first_day = None
        self.last_ts = None
        self.card = None
        self.n = 0
        self.n_ok = 0
        self.n_vok = 0          # correct answers on verified items
        self.recent = []        # (datetime, ok, counts_as_evidence)
        self.ok_days = set()
        self.ok_items = set()
        self.last_ok = None
        self.errors = {}
        self.hints = 0
        self.seeded = False     # marked known by a placement test
        self.open_day = None    # learner day of the latest attempt ...
        self.open_due = None    # ... and when the topic was due before that day's first attempt
        self.open_had_card = False
        self.fail_day = None    # learner day of the latest failed attempt
        self.err_log = []       # (datetime, error tag) of recent failures
        self.slow = 0           # correct answers that took far longer than expected
        self.vok_log = []       # (datetime, item or problem, objectives it tested) of right answers that are evidence
        self.last_ev_ok = None  # the latest answer that counts as evidence: right or wrong
        self.ok_objs = None     # objectives answered right on tagged items (None while no tagged item was)


def restorable(it) -> bool:
    """A disputed item may be verified again only if it was verified before the dispute, or is an
    official or imported item put on hold because a checker's answer did not match its key."""
    return bool(it.verify and it.verify.get("ok")) or it.src in ("official", "imported")


class SkillState:
    __slots__ = ("enrolled", "mode", "paused", "enrolled_ts", "known", "known_ts", "boss_ok",
                 "boss_tries", "boss_ts", "last_ts", "unenrolled")

    def __init__(self):
        self.enrolled = False
        self.mode = "mastery"
        self.paused = False
        self.enrolled_ts = None
        self.known = False
        self.known_ts = None
        self.boss_ok = False
        self.boss_tries = 0
        self.boss_ts = None
        self.last_ts = None
        self.unenrolled = False


class ItemState:
    __slots__ = ("id", "status", "skill", "topics", "type", "src", "shown_ts", "open", "open_test",
                 "n_shown", "n_ok", "n_fail", "last_ok", "last_ts", "fail_day", "verify", "reason",
                 "last_attempt", "last_err", "objectives", "objsig")

    def __init__(self, ident: str):
        self.id = ident
        self.status = "draft"
        self.skill = None
        self.topics = []
        self.type = None
        self.src = "generated"
        self.shown_ts = None
        self.open = False
        self.open_test = None
        self.n_shown = 0
        self.n_ok = 0
        self.n_fail = 0
        self.last_ok = None
        self.last_ts = None
        self.fail_day = None
        self.verify = None
        self.reason = None
        self.last_attempt = None   # id of the latest attempt event that still counts
        self.last_err = None       # error kind of that attempt when it was wrong
        self.objectives = []       # which of its primary topic's objectives it tests (empty: not tagged)
        self.objsig = {}           # a signature of each of those objectives' text when it was tagged


class DayStats:
    __slots__ = ("day", "attempts", "ok", "new", "reviews", "first", "last", "active_min", "hours",
                 "workout_min", "sessions", "src_done", "src_min", "stamps", "in_sleep")

    def __init__(self, day: str):
        self.day = day
        self.attempts = 0
        self.ok = 0
        self.new = 0
        self.reviews = 0
        self.first = None
        self.last = None
        self.active_min = 0.0
        self.hours = {}
        self.workout_min = 0
        self.sessions = 0
        self.src_done = 0
        self.src_min = 0        # stated length of the lectures logged that day
        self.stamps = []
        self.in_sleep = 0


class State:
    """The learner's state, replayed from the event log.

    `use_cache` (default: on unless CALAMITY_NO_CACHE is set) lets a stored snapshot stand in
    for the part of the log it was built from (see snapshot.py); the result is the same either
    way, which the test suite, the fuzzer and `doctor` check. `cache_info` says what happened.
    """

    def __init__(self, repo: Repo, tree: Tree, use_cache: bool | None = None):
        self.repo = repo
        self.tree = tree
        self.topics = {}
        self.skills = {}
        self.items = {}
        self.days = {}
        self.mocks = []
        self.tests = {}
        self.src = {}
        self.notes = []
        self.cp_marks = {}
        self.cp_assigned = []
        self.cp_credits = {}     # problem -> {topic key: True if that credit counted as evidence}
        self.weights = {}
        self.first_tries = []    # (datetime, right) of the first verified answer on each new topic (the quota)
        self.review_secs = []    # seconds the latest timed reviews took (the quota's review forecast)
        self.last_dt = None
        self.n_events = 0
        self.n_voided = 0
        self._alias_topic = {}
        self._alias_skill = {}
        self._retag = {}
        self._sched = {}
        self._status_cache = {}
        self._start_hour = int(repo.cfg("day_start_hour", 4))
        self._settings = {}      # configuration values already read and converted during this replay
        self._day_of = (None, None)
        self._voided = set()
        self._handler_errors = []
        self.cache_info = "off"
        self._build(snapshot.enabled() if use_cache is None else use_cache)

    # ------------------------------------------------------------ basics

    def day(self, dt) -> str:
        if dt is self._day_of[0]:    # replay asks about the same event several times in a row
            return self._day_of[1]
        key = daykey(dt, self._start_hour)
        self._day_of = (dt, key)
        return key

    def _setting(self, key: str, default, kind):
        try:
            return self._settings[key]
        except KeyError:
            value = self._settings[key] = kind(self.repo.cfg(key, default))
            return value

    def canon_skill(self, ident: str) -> str:
        seen = set()
        while ident in self._alias_skill and ident not in seen:
            seen.add(ident)
            ident = self._alias_skill[ident]
        return ident

    def canon(self, key: str) -> str:
        if "/" in key:
            skill, topic = key.split("/", 1)
            key = "%s/%s" % (self.canon_skill(skill), topic)
        seen = set()
        while key in self._alias_topic and key not in seen:
            seen.add(key)
            key = self._alias_topic[key]
        return key

    def topic_state(self, key: str) -> TopicState:
        ts = self.topics.get(key)
        if ts is None:
            ts = self.topics[key] = TopicState(key)
        return ts

    def skill(self, ident: str) -> SkillState:
        sk = self.skills.get(ident)
        if sk is None:
            sk = self.skills[ident] = SkillState()
        return sk

    def item(self, ident: str) -> ItemState:
        it = self.items.get(ident)
        if it is None:
            it = self.items[ident] = ItemState(ident)
        return it

    def _day_stats(self, dt) -> DayStats:
        key = self.day(dt)
        ds = self.days.get(key)
        if ds is None:
            ds = self.days[key] = DayStats(key)
        return ds

    # ------------------------------------------------------------ scheduling policy

    def _exam_dt(self, node, when):
        if node is None or not node.track.startswith("gate"):
            return None
        return gateinfo.exam_datetime(self.repo, node.paper, when)

    def retention_for(self, skill_id: str, when) -> float:
        r = self._setting("retention.%s" % self.mode_of(skill_id), 0.9, float)
        exam = self._exam_dt(self.tree.nodes.get(skill_id), when)
        if exam is not None:
            left = (exam - when).days
            if 0 <= left <= self._setting("gate.final_phase_days", 21, int):
                r = max(r, self._setting("gate.final_retention", 0.93, float))
        return r

    def scheduler(self, skill_id: str, when) -> fsrs.Scheduler:
        r = round(self.retention_for(skill_id, when), 4)
        sched = self._sched.get(r)
        if sched is None:
            sched = self._sched[r] = fsrs.Scheduler(
                retention=r, max_interval=self._setting("max_interval_days", 365, int)
            )
        return sched

    def _apply_review(self, key: str, grade: int, when, event_id: str) -> None:
        ts = self.topic_state(key)
        skill_id = key.split("/", 1)[0]
        u = None
        if self._setting("fuzz", True, bool):
            digest = hashlib.sha256(("%s|%s" % (key, event_id)).encode("utf-8")).hexdigest()
            u = int(digest[:8], 16) / float(1 << 32)
        card, _ = self.scheduler(skill_id, when).review(ts.card, grade, when, fuzz=u)
        if grade == fsrs.AGAIN:
            card.due = when + timedelta(minutes=self._setting("relearn_minutes", 10, int))
        else:
            exam = self._exam_dt(self.tree.nodes.get(skill_id), when)
            if exam is not None and when < exam:
                # A topic that would not come up again before the exam gets one final review,
                # at a fixed place of its own in the final phase so those reviews do not pile up.
                clamp = timedelta(days=self._setting("gate.exam_clamp_days", 3, int))
                final = timedelta(days=self._setting("gate.final_phase_days", 21, int))
                if card.due > exam - clamp and final > clamp:
                    slot = exam - final + (final - clamp) * self._final_slot(key)
                    if when < slot:
                        card.due = slot
        ts.card = card

    @staticmethod
    def _final_slot(key: str) -> float:
        """A stable position in [0, 1) for a topic's final review, derived from its key."""
        return int(hashlib.sha256(("final|" + key).encode("utf-8")).hexdigest()[:8], 16) / float(1 << 32)

    # ------------------------------------------------------------ replay

    def _build(self, use_cache: bool) -> None:
        files, problems = snapshot.read_log(self.repo)
        base, key, why, events = None, None, "snapshot not used", []
        if use_cache and not problems:
            key = snapshot.inputs_key(self.repo, self.tree)
            base, tails = snapshot.load(self.repo, key, files)
            if base is None:
                why = tails
            else:
                try:
                    found, new_problems = [], []
                    for name, raw, first_line in tails:
                        more, bad = parse_event_text(name, snapshot.tail_text(raw), first_line)
                        found += more
                        new_problems += bad
                    kinds = sorted({e["t"] for e in found if e["t"] in snapshot.GLOBAL_TYPES})
                    if kinds:
                        raise ValueError("new %s event" % kinds[0])
                    last = base["last_key"]
                    if last is not None:
                        last = (datetime.fromisoformat(last[0]), last[1], last[2], last[3])
                        if any(order_key(e) <= last for e in found):
                            raise ValueError("events dated before the snapshot")
                    snapshot.decode_state(self, base["state"])
                    self._voided = set(base["voided"])
                    self._handler_errors = list(base["handler_errors"])
                    problems = [tuple(p) for p in base["parse_problems"]] + new_problems
                    events, seen_ids, seen_keys = order_and_dedup(found, set(base["seen_ids"]), set(base["seen_keys"]))
                    last_key = base["last_key"]
                    self.cache_info = "snapshot + %d new event(s)" % len(events)
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, UnicodeDecodeError) as exc:
                    self.__init_fresh()
                    base, why = None, "snapshot not usable (%s)" % exc
        if base is None:
            loaded = []
            for name, raw in files:
                try:
                    text = log_text(raw)
                except UnicodeDecodeError as exc:
                    problems.append((name, 0, "unreadable (%s)" % exc))
                    continue
                more, bad = parse_event_text(name, text)
                loaded += more
                problems += bad
            events, seen_ids, seen_keys = order_and_dedup(loaded, set(), set())
            for e in events:
                if e["t"] == "rename":
                    # The later rename wins: renaming back to a name makes it live again (a->b, b->a).
                    alias = self._alias_skill if e.get("what") == "skill" else self._alias_topic
                    old, new = str(e.get("old")), str(e.get("new"))
                    alias.pop(new, None)
                    if old != new:
                        alias[old] = new
            self._voided = {str(e.get("attempt")) for e in events if e["t"] == "void"}
            # The kind of a mistake is often worked out after the answer was recorded (`mistake`):
            # the latest classification of an attempt replaces whatever the attempt itself carried.
            self._retag = {str(e.get("attempt")): str(e.get("err")) for e in events if e["t"] == "errtag" and e.get("err")}
            last_key = None
            self.cache_info = "full replay (%s)" % why if use_cache else "full replay"
        for e in events:
            self._apply(e)
        if events:
            k = order_key(events[-1])
            last_key = [k[0].isoformat(), k[1], k[2], k[3]]
        self.repo.event_errors = format_problems(problems) + self._handler_errors
        if key is not None and (base is None or events):
            self._save_snapshot(key, files, problems, seen_ids, seen_keys, last_key)
        self._finish()

    def __init_fresh(self) -> None:
        """Forget a half-restored snapshot before replaying from scratch."""
        self.topics, self.skills, self.items, self.days, self.tests, self.src = {}, {}, {}, {}, {}, {}
        self.mocks, self.notes, self.cp_assigned = [], [], []
        self.cp_marks, self.cp_credits, self.weights = {}, {}, {}
        self.first_tries, self.review_secs = [], []
        self.last_dt, self.n_events, self.n_voided = None, 0, 0
        self._alias_topic, self._alias_skill, self._retag = {}, {}, {}
        self._voided, self._handler_errors = set(), []

    def _save_snapshot(self, key, files, problems, seen_ids, seen_keys, last_key) -> None:
        if any(p[1] == 0 for p in problems):
            return  # an unreadable file: nothing to stand on
        for _, raw in files:
            if (raw and not raw.endswith(b"\n")) or b"\r" in raw:
                return  # a line still being written, or line ends the replay reads differently
        try:
            state = snapshot.encode_state(self)
        except (snapshot.Uncacheable, TypeError, ValueError):
            return  # something JSON cannot carry back unchanged: no snapshot, replay in full next time
        snapshot.save(self.repo, {
            "format": snapshot.FORMAT, "key": key,
            "files": {name: list(snapshot.consumed(raw)) for name, raw in files},
            "last_key": last_key, "seen_ids": sorted(seen_ids), "seen_keys": sorted(seen_keys),
            "voided": sorted(self._voided), "parse_problems": [list(p) for p in problems],
            "handler_errors": self._handler_errors, "state": state,
        })

    def _apply(self, e) -> None:
        """Replay one event."""
        handler = getattr(self, "_on_" + e["t"], None)
        dt = e["_dt"]
        self.last_dt = dt
        self.n_events += 1
        self._day_stats(dt).stamps.append(dt)
        if e["t"] == "attempt" and e["id"] in self._voided:
            self.n_voided += 1  # answered against a key later found wrong: it no longer counts
            return
        if handler is not None:
            try:
                handler(e, dt)
            except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
                self._handler_errors.append(
                    "%s:%s: could not apply %s event (%s)" % (e["_seq"][0], e["_seq"][1], e["t"], exc)
                )

    def fingerprint(self) -> str:
        """A digest of everything replay produced; two states with the same digest are the same."""
        data = {"state": snapshot.encode_state(self), "errors": self.repo.event_errors}
        return hashlib.sha256(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _on_enroll(self, e, dt):
        sk = self.skill(self.canon_skill(e["skill"]))
        sk.enrolled, sk.paused, sk.unenrolled = True, False, False
        sk.mode = e.get("mode") or sk.mode
        sk.enrolled_ts = sk.enrolled_ts or dt

    def _on_pause(self, e, dt):
        self.skill(self.canon_skill(e["skill"])).paused = True

    def _on_resume(self, e, dt):
        self.skill(self.canon_skill(e["skill"])).paused = False

    def _on_unenroll(self, e, dt):
        sk = self.skill(self.canon_skill(e["skill"]))
        sk.enrolled, sk.paused, sk.unenrolled = False, False, True

    def _on_covered(self, e, dt):
        ts = self.topic_state(self.canon(e["topic"]))
        if ts.covered_ts is None:
            ts.covered_ts, ts.covered_by = dt, e.get("by") or "tutor"

    def _on_shown(self, e, dt):
        it = self.item(e["item"])
        it.shown_ts, it.open, it.open_test = dt, True, e.get("test")
        it.n_shown += 1

    def _on_attempt(self, e, dt):
        day = self.day(dt)
        primary = self.canon(e["topic"])
        ok = bool(e.get("ok"))
        evidence = bool(e.get("verified")) and not e.get("quick") and not e.get("after_reveal")
        credit = e.get("credit") or [{"topic": e["topic"], "g": e.get("g", 3 if ok else 1)}]
        counted = None  # how the day counts this answer: "new", "review", or neither (placement)
        placement = e.get("kind") == "placement"
        err_tag = self._retag.get(e["id"]) or e.get("err") or "unclassified"
        problem = e.get("problem")  # a judged Codeforces problem counts as a distinct verified exercise
        source_id = e.get("item") or (("cf:%s" % problem) if problem else None)
        if problem:
            self.cp_credits.setdefault(str(problem), {})[primary] = evidence
        for c in credit:
            key = self.canon(c["topic"])
            grade = int(c["g"])
            ts = self.topic_state(key)
            self.skill(key.split("/", 1)[0]).last_ts = dt
            was_new = ts.card is None
            if counted is None:  # the first topic credited decides: the primary, or the one blamed
                counted = ("placement" if placement else "new") if was_new else "review"
            if placement and was_new and grade == fsrs.AGAIN:
                # A miss in a placement test on a topic never studied says only "not known yet":
                # the topic stays new, to be taught in its turn, instead of entering the reviews.
                continue
            if ts.open_day != day:
                ts.open_day = day
                ts.open_had_card = ts.card is not None
                ts.open_due = ts.card.due if ts.card is not None else None
            self._apply_review(key, grade, dt, e["id"])
            good = grade >= fsrs.HARD
            ts.n += 1
            ts.last_ok, ts.last_ts = good, dt
            if was_new:
                ts.first_ts = dt
                # Neither credit mirrored from an equivalent topic nor a placement answer is
                # "new material today": nothing was taught for it.
                if not c.get("eq") and not placement:
                    ts.first_day = day
                    if evidence and key == primary:
                        self.first_tries.append((dt, good))
                        if len(self.first_tries) > 200:
                            del self.first_tries[0]
            if evidence:
                ts.last_ev_ok = good
            if good:
                ts.n_ok += 1
                if evidence:
                    ts.n_vok += 1
                    ts.ok_days.add(day)
                    if source_id:
                        ts.ok_items.add(source_id)
                        tested = self.items[source_id].objectives if (key == primary and source_id in self.items) else []
                        ts.vok_log.append((dt, source_id, list(tested)))
                        if tested:
                            ts.ok_objs = sorted(set(ts.ok_objs or []) | set(tested))
                        if len(ts.vok_log) > 12:
                            del ts.vok_log[0]
            else:
                ts.seeded = False
                ts.fail_day = day
                ts.errors[err_tag] = ts.errors.get(err_tag, 0) + 1
                ts.err_log.append((dt, err_tag))
                if len(ts.err_log) > 12:
                    del ts.err_log[0]
            ts.recent.append((dt, good, evidence))
            if len(ts.recent) > 12:
                del ts.recent[0]
            if key == primary:
                ts.hints += int(e.get("hints") or 0)
                if good and e.get("slow"):
                    ts.slow += 1
        if e.get("item"):
            it = self.item(e["item"])
            it.open, it.last_ok, it.last_ts = False, ok, dt
            it.last_attempt = e["id"]
            it.last_err = None if ok else err_tag
            if ok:
                it.n_ok += 1
            else:
                it.n_fail += 1
                it.fail_day = day
        ds = self._day_stats(dt)
        ds.attempts += 1
        ds.ok += 1 if ok else 0
        if counted == "new":
            ds.new += 1
        elif counted == "review":
            ds.reviews += 1  # a placement answer on an unstudied topic is neither
            secs = e.get("secs")
            if isinstance(secs, (int, float)) and not isinstance(secs, bool) and 0 < secs < 4 * 3600:
                self.review_secs.append(float(secs))
                if len(self.review_secs) > 50:
                    del self.review_secs[0]
        bucket = ds.hours.setdefault(dt.hour, [0, 0])
        bucket[0] += 1
        bucket[1] += 1 if ok else 0
        test = e.get("test")
        if test and test in self.tests:
            self.tests[test]["answers"][e.get("item")] = {
                "ok": ok, "marks": e.get("marks"), "secs": e.get("secs"), "ts": dt,
            }

    def _on_item_draft(self, e, dt):
        it = self.item(e["item"])
        it.status = "draft"
        it.skill = self.canon_skill(e.get("skill") or "")
        it.topics = [self.canon(t) for t in e.get("topics") or []]
        it.type = e.get("type")
        it.src = e.get("src") or "generated"
        it.objectives, it.objsig = list(e.get("objectives") or []), dict(e.get("objsig") or {})

    def _on_item_tag(self, e, dt):
        it = self.item(e["item"])
        it.objectives, it.objsig = list(e.get("objectives") or []), dict(e.get("objsig") or {})
        ts = self.topics.get(it.topics[0]) if it.topics else None
        if ts is not None and it.id in ts.ok_items and it.objectives:    # right answers given before the tag count
            ts.ok_objs = sorted(set(ts.ok_objs or []) | set(it.objectives))
            ts.vok_log = [(at, src, list(it.objectives) if src == it.id else objs) for at, src, objs in ts.vok_log]

    def _on_item_verify(self, e, dt):
        it = self.item(e["item"])
        it.verify = {"ok": bool(e.get("ok")), "method": e.get("method"), "by": e.get("by"),
                     "ts": dt, "note": e.get("note")}
        if e.get("ok"):
            it.status = "verified"
        else:
            it.status = "disputed" if it.src in ("official", "imported") else "rejected"
            it.reason = e.get("note") or "independent check disagreed with the key"

    def _on_item_reject(self, e, dt):
        it = self.item(e["item"])
        it.status, it.reason = "rejected", e.get("reason")

    def _on_item_dispute(self, e, dt):
        it = self.item(e["item"])
        if it.status == "verified":   # a draft or a rejected item is not disputed (older logs may say so)
            it.status, it.reason = "disputed", e.get("reason")

    def _on_item_restore(self, e, dt):
        it = self.item(e["item"])
        if it.status == "disputed" and restorable(it):
            it.status, it.reason = "verified", None

    def _on_placement(self, e, dt):
        skill_id = self.canon_skill(e["skill"])
        sk = self.skill(skill_id)
        if e.get("result") == "known":
            sk.known, sk.known_ts = True, dt
        elif e.get("result") == "none":
            sk.known = False
        for tid in e.get("known") or []:
            key = self.canon("%s/%s" % (skill_id, tid))
            ts = self.topic_state(key)
            if ts.card is None:
                self._apply_review(key, fsrs.GOOD, dt, e["id"])
                # The first real review confirms the placement. Spread those confirmations over
                # two weeks so that placing out of several skills does not flood one day.
                spread = dt + timedelta(days=1 + 13 * self._final_slot("seed|" + key))
                if ts.card.due < spread:
                    ts.card.due = spread
                # first_day stays unset: a placement does not count as "new material today"
                ts.first_ts, ts.last_ts, ts.last_ok = dt, dt, True
            ts.seeded = True

    def _on_boss(self, e, dt):
        sk = self.skill(self.canon_skill(e["skill"]))
        sk.boss_tries += 1
        if e.get("ok"):
            sk.boss_ok, sk.boss_ts = True, dt

    def _on_mock(self, e, dt):
        self.mocks.append({k: v for k, v in e.items() if not k.startswith("_")})

    def _on_test_build(self, e, dt):
        self.tests[e["test"]] = {
            "id": e["test"], "items": list(e.get("items") or []), "minutes": e.get("minutes"),
            "label": e.get("label"), "built": dt, "answers": {}, "finished": None, "result": None,
        }

    def _on_test_finish(self, e, dt):
        test = self.tests.get(e["test"])
        if test is not None:
            test["finished"] = dt
            test["result"] = {k: v for k, v in e.items() if not k.startswith("_")}

    def _on_src_progress(self, e, dt):
        items = self.src.setdefault(e["source"], {})
        bulk = bool(e.get("bulk"))  # a catch-up entry for lectures watched earlier: not today's work
        items[str(e["item"])] = {"done": bool(e.get("done", True)), "ts": dt, "bulk": bulk,
                                 "score": e.get("score"), "method": e.get("method")}
        if e.get("done", True) and not bulk:
            self._day_stats(dt).src_done += 1

    def _on_cp_assign(self, e, dt):
        for p in e.get("problems") or []:
            self.cp_assigned.append({"problem": str(p), "ts": dt, "reason": e.get("reason")})

    def _on_cp_mark(self, e, dt):
        rec = self.cp_marks.setdefault(str(e["problem"]), {"marks": [], "subtags": []})
        rec["marks"].append((dt, e.get("mark"), e.get("note")))
        for tag in e.get("subtags") or []:
            if tag not in rec["subtags"]:
                rec["subtags"].append(tag)

    def _on_note(self, e, dt):
        self.notes.append({"ts": dt, "text": e.get("text", ""), "tag": e.get("tag"),
                           "skill": e.get("skill"), "topic": e.get("topic"), "pattern": e.get("pattern")})

    def _on_activity(self, e, dt):
        if e.get("kind") == "workout":
            self._day_stats(dt).workout_min += int(e.get("minutes") or 0)

    def _on_gate_weight(self, e, dt):
        self.weights[self.canon_skill(e["skill"])] = (float(e["marks"]), e.get("source") or "")

    def _finish(self) -> None:
        gap = timedelta(minutes=int(self.repo.cfg("session_gap_minutes", 30)))
        sleep_start = parse_hhmm(self.repo.prof("sleep.start"))
        sleep_end = parse_hhmm(self.repo.prof("sleep.end"))
        for ds in self.days.values():
            stamps = sorted(ds.stamps, key=utc)
            ds.first, ds.last = stamps[0], stamps[-1]
            ds.sessions, ds.active_min = 1, 1.0
            for a, b in zip(stamps, stamps[1:]):
                if b - a <= gap:
                    ds.active_min += (b - a).total_seconds() / 60.0
                else:
                    ds.sessions += 1
                    ds.active_min += 1.0
            if sleep_start is not None and sleep_end is not None:
                ds.in_sleep = sum(
                    1 for s in stamps if in_window(s.hour * 60 + s.minute, sleep_start, sleep_end)
                )
            ds.stamps = []
        # lectures logged against a study source count as "covered" for their mapped topics
        if self.src:
            from . import sources

            maps = sources.load_maps(self.repo, self.tree)
            minutes = sources.load_minutes(self.repo)
            for source, items in self.src.items():
                mapping = maps.get(source, {})
                for item_id, rec in items.items():
                    if not rec["done"]:
                        continue
                    ds = self.days.get(self.day(rec["ts"]))
                    if ds is not None and not rec.get("bulk"):
                        ds.src_min += minutes.get(source, {}).get(item_id, 0)
                    for key in mapping.get(item_id, ()):
                        ts = self.topic_state(self.canon(key))
                        if ts.covered_ts is None:
                            ts.covered_ts, ts.covered_by = rec["ts"], "source"

    # ------------------------------------------------------------ topic queries

    def mode_of(self, skill_id: str) -> str:
        sk = self.skills.get(skill_id)
        return sk.mode if sk else "mastery"

    def pace(self, skill_id: str) -> dict:
        """The pace profile a skill is studied at: `brushup` for a skill in brush-up mode, else the track's
        (`pace.track.<track>`, `exam` for the GATE tracks), else `mastery`. Its settings come from config.md."""
        name = "brushup" if self.mode_of(skill_id) == "brushup" else None
        if name is None:
            node = self.tree.nodes.get(skill_id)
            name = str(self.repo.cfg("pace.track.%s" % node.track, "mastery")) if node is not None else "mastery"
            name = name if name in PACES else "mastery"
        cfg = self.repo.cfg
        return {"name": name, "unlock": str(cfg("pace.%s.unlock" % name, "consolidating")),
                "wip": max(1, int(cfg("pace.%s.wip" % name, 2))),
                "consolidate_minutes": max(0, int(cfg("pace.%s.consolidate_minutes" % name, 20)))}

    def new_quota(self, when) -> dict:
        """How many new topics today asks for, and why (design §6.1): the most a day (`new_per_day_max`, else
        the highest pace profile among the active skills), shrunk while the next week's reviews near the review
        budget and while first tries on new topics go wrong. Returns {quota, max, forecast, budget, acc, n_acc,
        adaptive}; `acc` is None below 10 first tries in 14 days."""
        cfg = self.repo.cfg
        base = self._learner_cfg("new_per_day_max")
        base = self._learner_cfg("new_per_day") if base is None else base     # the old name, still honoured
        if base is None:
            names = {self.pace(s)["name"] for s in self.enrolled_skills()} or {"mastery"}
            base = max(int(cfg("pace.%s.new_max" % n, {"mastery": 6, "exam": 8, "brushup": 10}[n])) for n in names)
        base = max(0, base)
        budget = max(1, int(cfg("review_budget_min", 60)))
        secs = sorted(self.review_secs)
        per = (secs[len(secs) // 2] if len(secs) % 2 else (secs[len(secs) // 2 - 1] + secs[len(secs) // 2]) / 2) \
            if len(secs) >= 5 else float(cfg("review_secs", 60))
        week = when + timedelta(days=7)
        forecast = sum(1 for _, ts in self.scheduled_topics() if ts.card.due <= week) * per / 60.0 / 7
        recent = [ok for at, ok in self.first_tries if when - timedelta(days=14) <= at <= when]
        acc = (sum(recent) / float(len(recent))) if len(recent) >= 10 else None
        out = {"max": base, "forecast": forecast, "budget": budget, "acc": acc, "n_acc": len(recent),
               "adaptive": bool(cfg("quota.adaptive", True))}
        if not out["adaptive"] or base == 0:
            out["quota"] = base
            return out
        load = min(1.0, max(0.0, (budget - forecast) / budget))
        factor = 1.0 if acc is None else (0.75 if acc < 0.70 else 1.0 if acc < 0.90 else 1.1)
        out["quota"] = min(base, max(1, int(base * (0.4 + 0.6 * load) * factor + 0.5)))
        return out

    def _learner_cfg(self, key: str):
        """A setting's value when the learner set it in their profile (and it is valid), else None."""
        from .profile import coerce_cfg

        prof = self.repo.profile()
        if "cfg." + key not in prof:
            return None
        try:
            return int(coerce_cfg(key, prof["cfg." + key], self.repo.config_defaults()))
        except (CalError, TypeError, ValueError):
            return None

    def consolidated_at(self, key: str):
        """When a topic was secured: its second correct verified answer on another item, given at least
        `consolidate_minutes` after a first one. With no consolidation step (0 minutes) the first one
        secures it. None while it is not."""
        ts = self.topics.get(key)
        if ts is None or not ts.vok_log:
            return None
        gap = timedelta(minutes=self.pace(key.split("/", 1)[0])["consolidate_minutes"])
        if not gap:
            return ts.vok_log[0][0]

        def another(objs, other):          # tagged on both sides: a different objective; untagged: any item
            return not objs or not other or set(objs) != set(other)

        for i, (when, source, objs) in enumerate(ts.vok_log):
            if any(src != source and when - at >= gap and another(objs, o) for at, src, o in ts.vok_log[:i]):
                return when
        return None

    def coverage(self, key: str):
        """(objectives answered right on a tagged item, objectives the topic has), or None while it cannot be
        measured: no objectives, or no tagged item answered right (untagged items still count as before)."""
        ts = self.topics.get(key)
        total = len(self.tree.topic(key).objectives()) if self.tree.has_topic(key) else 0
        if ts is None or ts.ok_objs is None or not total:
            return None
        return len([n for n in ts.ok_objs if n <= total]), total

    def _covered(self, key: str, setting: str, default: float) -> bool:
        cov = self.coverage(key)
        return cov is None or cov[0] >= float(self.repo.cfg(setting, default)) * cov[1] - 1e-9

    def consolidation_due(self, key: str):
        """When a topic answered right once can be consolidated (a second item, `consolidate_minutes` after
        the last right answer), or None when it needs no consolidation now."""
        ts = self.topics.get(key)
        if ts is None or ts.card is None or not ts.vok_log or ts.seeded or ts.last_ev_ok is False:
            return None
        if self.consolidated_at(key) is not None:
            return None
        gap = self.pace(key.split("/", 1)[0])["consolidate_minutes"]
        return ts.vok_log[-1][0] + timedelta(minutes=gap) if gap else None

    def need_met(self, key: str, unlock: str) -> bool:
        """Whether a topic another one builds on is far enough along: `consolidating` (the mastery pace) or
        `learning` with its latest verified answer right (exam and brush-up). An oral check never counts."""
        ts = self.topics.get(key)
        sk = self.skills.get(key.split("/", 1)[0])
        if (ts is not None and ts.seeded) or (sk is not None and sk.known):
            return True
        if ts is None or ts.card is None:
            return False
        if unlock == "learning":
            return ts.last_ev_ok is True or self.topic_status(key) in ("consolidating", "solid", "mastered")
        return self.topic_status(key) in ("consolidating", "solid", "mastered")

    def topic_status(self, key: str) -> str:
        ts = self.topics.get(key)
        if ts is None or ts.card is None:
            return "covered" if (ts is not None and ts.covered_ts is not None) else "new"
        cfg = self.repo.cfg
        consolidated = self.consolidated_at(key) is not None
        if self.mode_of(key.split("/", 1)[0]) == "brushup":
            solid = bool(ts.last_ok) and ts.n_vok >= 1
        else:
            # accuracy over answers that count as evidence: an oral check or a guess after the key was shown
            # neither lifts nor sinks it
            window = [ok for _, ok, ev in ts.recent if ev][-int(cfg("solid.window", 5)):]
            acc = (sum(1 for ok in window if ok) / float(len(window))) if window else 0.0
            solid = (
                consolidated
                and bool(ts.last_ok)
                and ts.n_vok >= int(cfg("solid.min_correct", 3))
                and len(ts.ok_days) >= int(cfg("solid.min_days", 2))
                and acc >= float(cfg("solid.min_accuracy", 0.8))
                and ts.card.s >= float(cfg("solid.min_stability", 7))
            )
        solid = solid and self._covered(key, "solid.objective_coverage", 0.6)
        if (
            solid
            and ts.card.s >= float(cfg("mastered.min_stability", 21))
            and len(ts.ok_items) >= int(cfg("mastered.min_items", 4))
            and self._covered(key, "mastered.objective_coverage", 1.0)
        ):
            return "mastered"
        if solid or ts.seeded:
            return "solid"
        return "consolidating" if consolidated and ts.last_ok else "learning"   # a miss sends it back

    def open_topics(self, skill_id: str) -> list:
        """A skill's topics that are taught or answered but not yet secured (the WIP limit counts them)."""
        node = self.tree.nodes.get(skill_id)
        return [t.key for t in (node.topics if node else []) if self.topic_status(t.key) in OPEN]

    def retrievability(self, key: str, when) -> float:
        ts = self.topics.get(key)
        if ts is None or ts.card is None or ts.card.last is None:
            return 0.0
        elapsed = max(0.0, (when - ts.card.last).total_seconds() / 86400.0)
        return self.scheduler(key.split("/", 1)[0], when).retrievability(ts.card.s, elapsed)

    def reviewable_skill(self, skill_id: str) -> bool:
        node = self.tree.nodes.get(skill_id)
        if node is None or node.dropped:
            return False
        sk = self.skills.get(skill_id)
        if sk is None:
            return False
        if sk.enrolled:
            return not sk.paused
        return sk.known and not sk.unenrolled

    def scheduled_topics(self) -> list:
        """(key, TopicState) for every topic that is in the review rotation."""
        out = []
        for key, ts in self.topics.items():
            if ts.card is None or "/" not in key:
                continue
            if not self.tree.has_topic(key):
                continue
            if self.reviewable_skill(key.split("/", 1)[0]):
                out.append((key, ts))
        return out

    def due(self, when, until=None) -> list:
        """Topics due at `when` (or by `until`), most forgotten first."""
        limit = until or when
        rows = [(self.retrievability(k, when), k, ts) for k, ts in self.scheduled_topics() if ts.card.due <= limit]
        rows.sort(key=lambda r: (r[0], r[1]))
        return [(k, ts) for _, k, ts in rows]

    # ------------------------------------------------------------ skill queries

    def cp_level(self) -> int:
        """The highest Codeforces rating milestone the log shows as reached, or 0."""
        best = 0
        for node in self.tree.nodes.values():
            if node.track == "cp" and node.kind == "milestone":
                sk = self.skills.get(node.id)
                rating = node.meta.get("rating")
                if sk is not None and sk.boss_ok and isinstance(rating, int) and not isinstance(rating, bool):
                    best = max(best, rating)
        return best

    def deferred(self, topic) -> bool:
        """A competitive-programming topic whose `band` is well above the learner's level waits.

        Only for a learner with a Codeforces handle: their level is the highest rating milestone
        reached (from the log), and a topic is deferred while its band is more than
        `cp.band_lookahead` above it. Without a handle nothing is deferred.
        """
        if not topic.band:
            return False
        node = self.tree.nodes.get(topic.skill)
        if node is None or node.track != "cp" or not self.repo.prof("cp.handle"):
            return False
        try:
            ahead = int(self.repo.cfg("cp.band_lookahead", 200))
        except (TypeError, ValueError):
            ahead = 200
        return topic.band > self.cp_level() + ahead

    def skill_counts(self, skill_id: str, in_scope: bool = False) -> dict:
        """Topics of a skill by status. `in_scope` leaves out topics deferred to a later rating."""
        node = self.tree.nodes.get(skill_id)
        counts = dict.fromkeys(TOPIC_ORDER, 0)
        if node is not None:
            for topic in node.topics:
                if in_scope and self.deferred(topic):
                    continue
                counts[self.topic_status(topic.key)] += 1
        counts["total"] = sum(counts[s] for s in TOPIC_ORDER)
        return counts

    def skill_share(self, skill_id: str) -> float:
        counts = self.skill_counts(skill_id)
        if not counts["total"]:
            return 0.0
        return (counts["solid"] + counts["mastered"]) / float(counts["total"])

    def unlocked(self, skill_id: str) -> bool:
        node = self.tree.nodes.get(skill_id)
        if node is None:
            return False
        for _, alts in self.tree.requirement_groups(node):
            live = [a for a in alts if a in self.tree.nodes and not self.tree.nodes[a].dropped]
            if live and not any(self.skill_status(a) in SATISFIED for a in live):
                return False
        return True

    def missing_prereqs(self, skill_id: str) -> list:
        node = self.tree.nodes.get(skill_id)
        out = []
        if node is None:
            return out
        for label, alts in self.tree.requirement_groups(node):
            live = [a for a in alts if a in self.tree.nodes and not self.tree.nodes[a].dropped]
            if live and not any(self.skill_status(a) in SATISFIED for a in live):
                out.append((label, live))
        return out

    def skill_status(self, skill_id: str) -> str:
        """locked | available | active | paused | ready | known | mastered | dropped"""
        cached = self._status_cache.get(skill_id)
        if cached is not None:
            return cached
        self._status_cache[skill_id] = "locked"  # guards against prerequisite cycles
        status = self._skill_status(skill_id)
        self._status_cache[skill_id] = status
        return status

    def _skill_status(self, skill_id: str) -> str:
        node = self.tree.nodes.get(skill_id)
        if node is None:
            return "locked"
        if node.dropped:
            return "dropped"
        sk = self.skills.get(skill_id) or SkillState()
        counts = self.skill_counts(skill_id)
        total = counts["total"]
        brushup = sk.mode == "brushup"
        if total:
            done = counts["mastered"] + (counts["solid"] if brushup else 0)
            if done == total and (sk.boss_ok or brushup or not node.has_boss):
                return "mastered"
        elif node.kind == "milestone" and sk.boss_ok:
            return "mastered"
        if sk.known:
            return "known"
        if total:
            need = float(self.repo.cfg("brushup.ready_share" if brushup else "ready_share", 0.6))
            scope = self.skill_counts(skill_id, in_scope=True)  # topics deferred to a later rating do not count
            if scope["total"] and (scope["solid"] + scope["mastered"]) / float(scope["total"]) >= need:
                return "ready"
        if sk.enrolled:
            return "paused" if sk.paused else "active"
        return "available" if self.unlocked(skill_id) else "locked"

    def enrolled_skills(self) -> list:
        """Enrolled, not paused, not dropped skill ids in the order they were enrolled."""
        rows = []
        for skill_id, sk in self.skills.items():
            node = self.tree.nodes.get(skill_id)
            if sk.enrolled and not sk.paused and node is not None and not node.dropped:
                rows.append((utc(sk.enrolled_ts) if sk.enrolled_ts else None, skill_id))
        rows.sort(key=lambda r: (r[0] is None, r[0], r[1]))
        return [s for _, s in rows]

    # ------------------------------------------------------------ day queries

    def today_numbers(self, when) -> dict:
        """Counts that define today's finish line."""
        day = self.day(when)
        _, day_end = day_bounds(when, self._start_hour)
        due_open, done, relearn, due_now, new_today = [], [], [], [], []
        to_secure, secured = 0, 0   # topics started today that the pace asks to consolidate, and those that are
        for key, ts in self.scheduled_topics():
            attempted_today = ts.open_day == day
            if ts.card.due <= when:
                due_now.append(key)
            if attempted_today and ts.last_ok is False:
                relearn.append(key)  # failed today and not yet answered correctly again
            if ts.first_day == day:
                new_today.append(key)
                if self.pace(key.split("/", 1)[0])["consolidate_minutes"]:
                    to_secure += 1
                    at = self.consolidated_at(key)
                    secured += 1 if at is not None and self.day(at) == day else 0
                continue
            was_due = (ts.open_due if attempted_today else ts.card.due)
            if was_due is not None and was_due <= day_end:
                due_open.append(key)
                if attempted_today:
                    done.append(key)
        ds = self.days.get(day)
        return {
            "day": day,
            "due_total": len(due_open),
            "due_done": len(done),
            "due_now": len(due_now),
            "relearn": relearn,
            "new_done": len(new_today),
            "consolidate_total": to_secure,
            "consolidated": secured,
            "attempts": ds.attempts if ds else 0,
            "ok": ds.ok if ds else 0,
            "active_min": ds.active_min if ds else 0.0,
            "reviews_needed": ceil_int(0.9 * len(due_open)),
        }


def load(repo: Repo, tree: Tree | None = None) -> State:
    return State(repo, tree or Tree(repo))
