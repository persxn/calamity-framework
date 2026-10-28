"""The learning loop: enrol, serve an item, record the answer, credit every topic it exercised.

Only this module (through the CLI) writes attempts. Grades are computed
here from correctness, hints and time taken; nobody types a grade in.
"""
from __future__ import annotations

from datetime import timedelta

from . import fsrs, items, plan
from .state import State
from .store import Repo
from .util import CalError, csv_list, fmt_delta, short_id, table

MODES = ("mastery", "brushup")
ERROR_TAGS = ("concept", "careless", "misread", "time", "syntax", "memory", "method", "guess")
NEED_ITEM = 4  # exit code: no verified item is available for the topic


# ---------------------------------------------------------------- enrolment


def enroll(repo: Repo, tree, state, skill_id: str, mode: str = "mastery", force: bool = False) -> str:
    node = tree.get(skill_id)
    if node.dropped:
        raise CalError("%s is dropped from your tree; run: tree restore %s" % (skill_id, skill_id))
    if mode not in MODES:
        raise CalError("mode must be one of: %s" % ", ".join(MODES))
    missing = state.missing_prereqs(skill_id)
    if missing and not force:
        lines = ["%s is locked. It needs:" % skill_id]
        for label, alts in missing:
            lines.append("  %s (%s)" % (" or ".join(alts) if len(alts) > 1 else label,
                                        ", ".join("%s is %s" % (a, state.skill_status(a)) for a in alts)))
        lines.append("See the route with: tree path %s" % skill_id)
        lines.append("To start anyway: enroll %s --force" % skill_id)
        raise CalError("\n".join(lines))
    repo.append("enroll", skill=skill_id, mode=mode)
    out = ["enrolled: %s | %s (%s mode)" % (skill_id, node.title, mode)]
    if missing:
        out.append("note: started with unmet prerequisites: %s" % ", ".join(l for l, _ in missing))
    if not node.topics and node.kind != "milestone":
        out.append("no syllabus yet: have the curriculum-architect agent write learner/syllabus/%s.md, "
                   "then run: syllabus check %s" % (skill_id, skill_id))
    elif node.topics:
        out.append("%d topics; first: %s" % (len(node.topics), node.topics[0].key))
    return "\n".join(out)


def set_enrollment(repo: Repo, tree, state, skill_id: str, what: str) -> str:
    tree.get(skill_id)
    sk = state.skills.get(skill_id)
    if what in ("pause", "resume", "unenroll") and (sk is None or not (sk.enrolled or sk.known)):
        raise CalError("%s is not enrolled" % skill_id)
    repo.append(what, skill=skill_id)
    return {"pause": "paused: %s (its reviews stop until you resume it)",
            "resume": "resumed: %s",
            "unenroll": "unenrolled: %s (progress is kept; its reviews stop)"}[what] % skill_id


def feedback(repo: Repo, tree, pairs, topic: str | None = None) -> str:
    """Record the learner's word on the teaching: pace=fast|slow|ok, depth=more|less|ok, clarity=low|ok."""
    allowed = {"pace": ("fast", "slow", "ok"), "depth": ("more", "less", "ok"), "clarity": ("low", "ok")}
    said = {}
    for pair in pairs:
        name, _, value = pair.partition("=")
        name, value = name.strip().lower(), value.strip().lower()
        if name not in allowed or value not in allowed[name]:
            raise CalError("feedback takes %s (got %r)" % (
                ", ".join("%s=%s" % (k, "|".join(v)) for k, v in allowed.items()), pair))
        said[name] = value
    if not said:
        raise CalError("say what the learner said: pace=fast|slow|ok, depth=more|less|ok, clarity=low|ok")
    skill = None
    if topic:
        topic = tree.topic(topic).key
        skill = topic.split("/", 1)[0]
    repo.append("feedback", topic=topic, skill=skill, **said)
    return "feedback noted: %s%s" % (" ".join("%s=%s" % kv for kv in said.items()), (" on " + topic) if topic else "")


def covered(repo: Repo, tree, keys, by: str = "tutor") -> str:
    out = []
    for key in keys:
        topic = tree.topic(key)
        repo.append("covered", topic=topic.key, by=by)
        out.append("covered: %s | %s" % (topic.key, topic.title))
    return "\n".join(out)


# ---------------------------------------------------------------- asking


# The parts of the depth contract (framework/method-teaching.md), in teaching order, and those a topic's
# level asks for at least. A topic taught with fewer gets a warning, never a block.
PARTS = ("history", "model", "mechanics", "example", "usage", "flags", "tradeoffs", "impl")
REQUIRED_PARTS = {1: ("model", "example"), 2: ("model", "mechanics", "example"),
                  3: ("history", "model", "mechanics", "example", "usage", "tradeoffs")}


def parse_parts(text) -> list:
    """The parts named in `--parts history,model,...`, checked against PARTS. Raises CalError."""
    parts = []
    for word in csv_list(text):
        word = word.strip().lower()
        if word not in PARTS:
            raise CalError("--parts names the parts taught: %s (got %r)" % (", ".join(PARTS), word))
        if word not in parts:
            parts.append(word)
    return parts


def missing_parts(topic, parts) -> list:
    """The parts the topic's level asks for that were not taught (level 3 and above ask the most)."""
    need = REQUIRED_PARTS[min(3, max(1, int(topic.level or 1)))]
    return [p for p in need if p not in parts]


def need_item_text(repo: Repo, tree, state, key: str, when, purpose: str) -> str:
    topic = tree.topic(key)
    node = tree.get(topic.skill)
    gate = node.track.startswith("gate")
    difficulty = items.target_difficulty(state, tree, key)
    bank = [it for it in state.items.values() if it.topics and it.topics[0] == key]
    counts = {}
    for it in bank:
        counts[it.status] = counts.get(it.status, 0) + 1
    lines = ["NEED_ITEM", "topic: %s | %s" % (key, topic.title),
             "skill: %s | %s (track %s, %s mode)" % (node.id, node.title, node.track, state.mode_of(node.id)),
             "purpose: %s" % purpose, "difficulty: %d (scale 1-5)" % difficulty]
    if gate:
        lines.append("format: GATE style - mcq, msq or nat, with marks 1 or 2")
    else:
        lines.append("format: whichever tests the skill best - mcq, msq, nat, short, code, task or open "
                     "(hands-on for tools and frameworks)")
    goals = topic.objectives()
    if goals:
        lines.append("objectives (tag the item with the numbers it tests: \"objectives\": [2]):")
        lines.extend("  %d. %s%s" % (o["n"], ("[%s] " % o["strand"]) if o["strand"] else "", o["text"]) for o in goals[:12])
        ts = state.topics.get(key)
        done = set(ts.ok_objs or []) if ts is not None else set()
        open_ = [o["n"] for o in goals if o["n"] not in done]
        if done and open_:
            lines.append("not yet answered right on: objective%s %s (write for one of these)" % (
                "" if len(open_) == 1 else "s", ", ".join(map(str, open_))))
    else:
        body = [l for l in topic.body.split("\n") if l.strip()]
        if body:
            lines.append("objectives:")
            lines.extend("  " + l.strip() for l in body[:12])
    if not gate and purpose != "placement":
        picked = plan.weave_candidates(repo, tree, state, when, node.id)
        if picked:
            lines.append("embed (earlier topics; weave them into the exercise where it is natural):")
            for other, r in picked:
                lines.append("  %s | %s | recall chance %d%%" % (other, tree.topic(other).title, round(100 * r)))
    lines.append("bank for this topic: %s" % (", ".join("%d %s" % (c, s) for s, c in sorted(counts.items())) or "empty"))
    lines.append("then: examiner agent drafts it, checker agent verifies it, and: ask --topic %s" % key)
    return "\n".join(lines)


def unseen_stock(state, key: str) -> int:
    """Verified items for a topic that the learner has never been shown."""
    return sum(1 for it in items.candidates(state, key) if it.n_shown == 0)


def untested_objectives(tree, state, key: str) -> list:
    """The numbers of a topic's objectives that no verified or drafted item is tagged with yet."""
    goals = tree.topic(key).objectives()
    tested = set()
    for it in state.items.values():
        if it.status in ("verified", "draft") and it.topics and it.topics[0] == key:
            tested.update(it.objectives)
    return [o["n"] for o in goals if o["n"] not in tested]


def drafts_waiting(state, key: str) -> int:
    return sum(1 for it in state.items.values() if it.status == "draft" and it.topics and it.topics[0] == key)


def needed_topics(repo: Repo, tree, state, when, skill: str | None = None, n: int = 6, days: int = 1,
                  per_topic: int = 1) -> list:
    """[(topic key, 'review'|'consolidate'|'new')] coming up that have fewer than `per_topic` unseen verified
    items. `days` looks that many learner days ahead: the reviews due by then and the new topics the daily
    quota would open meanwhile (a simulation of the plan, not a promise)."""
    rows, seen = [], set()

    def add(key, purpose):
        if key in seen or not tree.has_topic(key):
            return
        seen.add(key)
        if unseen_stock(state, key) < per_topic:
            rows.append((key, purpose))

    _, day_end = plan.day_end(repo, when)
    until = day_end + timedelta(days=max(1, days) - 1)
    for key, _ in state.due(when, until=until):
        if not skill or key.split("/", 1)[0] == skill:
            add(key, "review")
    ready, later = plan.consolidations(state, when, skill)
    for _, key, _ in ready + later:
        add(key, "consolidate")
    limit = max(n, 4) + 4 if days <= 1 else max(n, 4, state.new_quota(when)["quota"] * days) + 4
    for cand in plan.new_candidates(repo, tree, state, when, skill=skill, limit=limit, lookahead=True):
        add(cand["key"], "new")
    return rows


def needs_text(repo: Repo, tree, state, when, skill: str | None = None, n: int = 6, full: bool = False,
               days: int = 1, per_topic: int = 1) -> str:
    """The upcoming topics that have no unseen verified item: the examiner's work list.

    The tutor only needs to know whether there is work and for which topics; the examiner reads
    the details (objectives, difficulty, format, topics to weave in) with `full`. `days` and
    `per_topic` turn it into the list for stocking ahead: item families for the next days."""
    if skill:
        tree.get(skill)
    rows = needed_topics(repo, tree, state, when, skill, n, days=days, per_topic=per_topic)
    ahead = days > 1 or per_topic > 1
    scope = (" in %s" % skill if skill else "") + (" over the next %d day(s)" % days if days > 1 else "")
    if not rows:
        return "ITEMS: stocked\nEvery topic coming up%s has %s." % (
            scope, "an unseen verified item" if per_topic <= 1 else "%d unseen verified items" % per_topic)
    out = ["ITEMS NEEDED: %d topic(s)%s (showing %d)" % (len(rows), scope, min(n, len(rows)))]

    def family(key):
        """', 2 more (1 draft waiting); objectives untested: 2, 4' for stocking ahead."""
        want = max(0, per_topic - unseen_stock(state, key) - drafts_waiting(state, key))
        waiting = drafts_waiting(state, key)
        bits = ["%d more" % want] + (["%d draft%s waiting for the checker" % (waiting, "" if waiting == 1 else "s")]
                                     if waiting else [])
        gap = untested_objectives(tree, state, key)
        return ", " + ", ".join(bits) + ("; objectives untested: %s" % ", ".join(map(str, gap)) if gap else "")

    if not full:
        from . import advise

        out.extend("  %s (%s%s)" % (key, purpose, family(key) if ahead else "") for key, purpose in rows[:n])
        flags = ((" --skill %s" % skill) if skill else "") + ((" --days %d" % days) if days > 1 else "") + \
            ((" --per-topic %d" % per_topic) if per_topic > 1 else "")
        out.append("Ask the examiner agent to stock them: it reads the details with `item needs --full%s` and "
                   "returns item ids for the checker agent." % flags)
        hint = advise.line(repo, "stock", then="review")
        if hint:
            out.append(hint)
        return "\n".join(out)
    for key, purpose in rows[:n]:
        out.append("")
        out.extend(need_item_text(repo, tree, state, key, when, purpose).split("\n")[1:-1])
        if ahead:
            out.append("family: write%s, across its objectives and depths" % family(key)[1:])
    out.append("")
    if ahead:
        out.append("Write each topic's family (different objectives and depths; a hands-on item for a runnable "
                   "skill), store them with: item import --file <path> --by examiner, and return the new ids for "
                   "the checker agent.")
    else:
        out.append("Draft one item per topic, store them with: item import --file <path> --by examiner, and "
                   "return the new ids for the checker agent.")
    return "\n".join(out)


def ask(repo: Repo, tree, state, when, topic: str | None = None, item_id: str | None = None,
        skill: str | None = None, test: str | None = None, show_check: bool = False, due_only: bool = False,
        taught: bool = False, parts: str | None = None, minutes: int | None = None):
    """Serve one item. Returns (exit_code, text).

    With no topic or id it serves whatever `next` would: a review, or a new topic that was taught
    already; anything else (a topic to teach, a lecture, the end of the day) is printed instead.
    `due_only` serves a review and nothing else. `taught` (with a topic) first records that the
    topic was just taught, as `covered` does, so teaching and testing take one call; `parts` and
    `minutes` say what was taught and for how long, stored on that same event.
    """
    if taught and not topic:
        raise CalError("--taught goes with --topic: the topic that was just taught")
    if (parts is not None or minutes is not None) and not taught:
        raise CalError("--parts and --minutes describe a teaching: use them with --topic K --taught")
    taught_parts = parse_parts(parts) if parts is not None else None
    purpose, warn, consolidating = "review", None, False
    if item_id:
        item = items.load(repo, item_id)
        st = state.items.get(item_id)
        if st is None or st.status != "verified":
            raise CalError("item %s is %s; only verified items can be asked" % (item_id, st.status if st else "unknown"))
        key = (st.topics or [state.canon(item["topics"][0])])[0]
    else:
        if topic:
            key = tree.topic(topic).key
            ts = state.topics.get(key)
            first = ts is None or (ts.covered_ts is None and ts.card is None)
            if taught and (first or taught_parts is not None or minutes is not None):
                tele = {k: v for k, v in (("parts", taught_parts), ("minutes", minutes)) if v is not None}
                repo.append("covered", topic=key, by="tutor", **tele)
                notes = []
                missing = plan.unmet_needs(tree, state, tree.topic(key)) if first else []
                if missing:
                    notes.append("note: %s builds on %s, not studied yet. If the learner could not follow, teach "
                                 "that first (next --skill %s) rather than testing this."
                                 % (key, ", ".join(missing), key.split("/", 1)[0]))
                short = missing_parts(tree.topic(key), taught_parts) if taught_parts is not None else []
                if short:
                    notes.append("warning: a level-%d topic asks for %s too (framework/method-teaching.md); teach "
                                 "%s before the next topic, or say why it was left out (observe)"
                                 % (int(tree.topic(key).level or 1), ", ".join(short),
                                    "it" if len(short) == 1 else "them"))
                warn = "\n".join(notes) or None
        else:
            action = plan.next_action(repo, tree, state, when, skill=skill)
            if due_only and action["action"] != "review":
                return 0, ("NOTHING_DUE\nNo review is due right now%s, so the surprise recall is over. Go on with "
                           "the main block: ask%s" % (" in %s" % skill if skill else "", " --skill %s" % skill if skill else ""))
            if action["action"] not in ("review", "new", "consolidate") or action.get("at") is not None:
                return 0, plan.next_text(repo, tree, state, when, action)
            key = action["topic"]
            consolidating = action["action"] == "consolidate"
            if action["action"] == "new" and not action.get("covered"):
                return 0, plan.next_text(repo, tree, state, when, action)
        ts = state.topics.get(key)
        if ts is None or ts.card is None:
            purpose = "new"
        exclude = ()
        if state.consolidation_due(key) is not None:
            # a second item secures it: never the one it was already answered right on
            purpose, exclude = "consolidate (a second item, on another objective)", {entry[1] for entry in ts.vok_log}
        chosen = items.pick(repo, state, key, when, difficulty=items.target_difficulty(state, tree, key),
                            exclude=exclude)
        if chosen is None and exclude and not consolidating:
            # asked for by name (a review, a retry): the same item is better than none; `item needs` lists the topic
            # so the examiner writes the second one
            chosen = items.pick(repo, state, key, when, difficulty=items.target_difficulty(state, tree, key))
        if chosen is None:
            return NEED_ITEM, need_item_text(repo, tree, state, key, when, purpose)
        item = items.load(repo, chosen)
    if test:
        t = state.tests.get(test)
        if t is None:
            raise CalError("unknown test %s" % test)
        if t["finished"]:
            raise CalError("test %s is already finished" % test)
        if item["id"] not in t["items"]:
            raise CalError("item %s is not part of test %s" % (item["id"], test))
    shown = state.items.get(item["id"])
    repo.append("shown", when=when, item=item["id"], topic=(shown.topics if shown and shown.topics
                                                             else [state.canon(item["topics"][0])])[0], test=test)
    text = items.blind_text(item, tree, with_check=show_check)
    text += "\n---\nshow the learner only the text between the dashes (the line above them names the topic)"
    if item["type"] in items.AUTO_TYPES:
        text += "\nrecord with: answer %s --answer <%s>   [--hints N]" % (
            item["id"], {"mcq": "letter", "msq": "letters", "nat": "number", "short": "text"}[item["type"]])
    else:
        text += ("\nrecord with: answer %s --result pass|fail --evidence \"what was run and what happened\""
                 "   [--hints N] [--err %s]" % (item["id"], "|".join(ERROR_TAGS)))
        if not show_check:
            text += "\njudge it with: item show %s --check" % item["id"]
    if warn:
        text += "\n" + warn
    return 0, text


# ---------------------------------------------------------------- answering


def compute_grade(repo: Repo, ok: bool, hints: int, secs, expect, allow_easy: bool):
    """Map correctness, hints and time to an FSRS grade. Returns (grade, slow)."""
    if not ok:
        return fsrs.AGAIN, False
    slow = bool(secs is not None and expect and secs > float(repo.cfg("time.hard_factor", 2.0)) * expect)
    if hints and hints > 0:
        return fsrs.HARD, slow
    if slow:
        return fsrs.HARD, True
    if allow_easy and secs is not None and expect and secs < float(repo.cfg("time.easy_factor", 0.5)) * expect:
        return fsrs.EASY, False
    return fsrs.GOOD, False


def describe_topic(repo: Repo, state, key: str) -> str:
    """One line on where a topic stands and what it still needs."""
    ts = state.topics.get(key)
    status = state.topic_status(key)
    if ts is None or ts.card is None:
        return "%s: %s" % (key, status)
    cfg = repo.cfg
    need = []
    if status in ("learning", "consolidating"):
        minutes = state.pace(key.split("/", 1)[0])["consolidate_minutes"]
        if status == "learning" and minutes and state.consolidated_at(key) is None:
            need.append("a right answer on a second item, at least %d min after the first (consolidation)" % minutes)
        if state.mode_of(key.split("/", 1)[0]) == "brushup":
            need.append("one correct answer on a verified item")
        else:
            lack = int(cfg("solid.min_correct", 3)) - ts.n_vok
            if lack > 0:
                need.append("%d more correct answer%s on verified items" % (lack, "" if lack == 1 else "s"))
            if len(ts.ok_days) < int(cfg("solid.min_days", 2)):
                need.append("a correct answer on another day")
            if ts.card.s < float(cfg("solid.min_stability", 7)):
                need.append("memory strength %.1fd of %sd" % (ts.card.s, cfg("solid.min_stability", 7)))
            if not ts.last_ok:
                need.append("the last answer was wrong")
        return "%s: %s; solid needs %s" % (key, status, "; ".join(need) or "recent accuracy to recover")
    if status == "solid":
        if ts.seeded and ts.n_vok == 0:
            return "%s: solid (from the placement test; first real review pending)" % key
        if ts.card.s < float(cfg("mastered.min_stability", 21)):
            need.append("memory strength %.0fd of %sd" % (ts.card.s, cfg("mastered.min_stability", 21)))
        lack = int(cfg("mastered.min_items", 4)) - len(ts.ok_items)
        if lack > 0:
            need.append("%d more distinct item%s answered correctly" % (lack, "" if lack == 1 else "s"))
        return "%s: solid; mastered needs %s" % (key, "; ".join(need) or "nothing more")
    return "%s: %s" % (key, status)


def _record(repo: Repo, tree, state, when, primary: str, credit_topics, ok: bool, grade: int, hints: int,
            blame, **extra) -> list:
    """Build the credit list and append the attempt event. Returns the credit list."""
    credit = []
    if ok:
        credit.append({"topic": primary, "g": grade})
        other_grade = fsrs.HARD if (hints and hints > 0) else fsrs.GOOD
        for key in credit_topics:
            if key != primary:
                credit.append({"topic": key, "g": other_grade})
    else:
        blamed = [k for k in (blame or []) if k in credit_topics] or [primary]
        for key in blamed:
            credit.append({"topic": key, "g": fsrs.AGAIN})
    # the same knowledge listed under another skill (e.g. in a second exam paper) moves with it
    listed = {c["topic"] for c in credit}
    for c in list(credit):
        for other in tree.equivalents(c["topic"]):
            if other not in listed:
                listed.add(other)
                credit.append({"topic": other, "g": c["g"], "eq": True})
    ts = state.topics.get(primary)
    kind = extra.pop("kind", None) or ("review" if (ts is not None and ts.card is not None) else "new")
    repo.append("attempt", when=when, topic=primary, ok=bool(ok), g=grade, credit=credit,
                hints=int(hints or 0) or None, kind=kind, **extra)
    return credit


def answer(repo: Repo, tree, state, when, item_id: str, raw=None, result: str | None = None, hints: int = 0,
           err: str | None = None, note: str | None = None, seconds=None, blame=None,
           evidence: str | None = None, kind: str | None = None) -> str:
    item = items.load(repo, item_id)
    st = state.items.get(item_id)
    if st is None or st.status != "verified":
        raise CalError("item %s is %s; only verified items can be answered" % (item_id, st.status if st else "unknown"))
    if not st.open:
        raise CalError("item %s is not open. Serve it first with: ask --id %s" % (item_id, item_id))
    # The topics as replay knows them, so an item written before a `rename topic` still counts.
    topics = list(st.topics) or [state.canon(k) for k in item["topics"]]
    for key in topics:
        if not tree.has_topic(key):
            raise CalError("item %s refers to topic %s, which is no longer in the syllabus" % (item_id, key))
    if err and err not in ERROR_TAGS:
        raise CalError("--err must be one of: %s" % ", ".join(ERROR_TAGS))
    blame = [tree.topic(k).key for k in csv_list(blame)]

    if item["type"] in items.AUTO_TYPES:
        if raw is None:
            raise CalError("this is a %s item: pass the learner's answer with --answer" % item["type"])
        ok, normalised = items.grade(item, raw)
        shown_answer = ",".join(normalised) if isinstance(normalised, list) else str(normalised)
    else:
        if result not in ("pass", "fail"):
            raise CalError("this is a %s item: run its check, then pass --result pass|fail --evidence \"...\"" % item["type"])
        if not (evidence or "").strip():
            raise CalError("--evidence is required: say what was run and what happened")
        ok, shown_answer = result == "pass", None

    if seconds is None and st.shown_ts is not None:
        elapsed = (when - st.shown_ts).total_seconds()
        seconds = int(elapsed) if 0 <= elapsed <= 7200 else None
    primary = topics[0]
    ts = state.topics.get(primary)
    studied = ts is not None and ts.card is not None
    # "Easy" needs a record to stand on: a topic already answered correctly, or a placement test,
    # where a fast right answer on something never taught here is exactly what is being looked for.
    allow_easy = (studied and bool(ts.last_ok)) or (kind == "placement" and not studied)
    grade, slow = compute_grade(repo, ok, hints, seconds, item.get("expect_s"), allow_easy)
    after_reveal = st.fail_day == state.day(when)
    test = st.open_test
    if test and (test not in state.tests or state.tests[test]["finished"]):
        test = None
    marks = items.marks_for(item, ok)
    credit = _record(
        repo, tree, state, when, primary, topics, ok, grade, hints, blame,
        item=item_id, secs=seconds, exp=item.get("expect_s"), slow=slow or None, err=(err if not ok else None),
        note=note, verified=True, marks=marks, test=test, after_reveal=after_reveal or None,
        ans=shown_answer, evidence=evidence, kind=kind,
    )
    new_state = State(repo, tree)
    if test:
        done = len(new_state.tests[test]["answers"])
        return "recorded for test %s (%d of %d answered). Results come with: test finish %s" % (
            test, done, len(new_state.tests[test]["items"]), test)
    lines = ["%s · %s · %s" % ("CORRECT" if ok else "WRONG", item_id, primary)]
    lines.extend(_credit_lines(new_state, when, credit))
    if marks is not None:
        lines.append("marks: %+.2f" % marks)
    if after_reveal and ok:
        lines.append("note: answered after seeing the solution today; it schedules the topic but is not counted as evidence")
    reveal = items.reveal_text(item)
    if reveal:
        lines.append(reveal)
    lines.append(describe_topic(repo, new_state, primary))
    if kind == "placement" and not ok and not studied:
        lines.append("placement: not known yet. The topic stays in the queue as new material; nothing was scheduled.")
    lines.append(plan.today_line(plan.today(repo, tree, new_state, when)))
    # The learner may not see this output: say what to tell them, right where the next step is decided.
    if kind == "placement":
        lines.append("next: in a placement test, no feedback until the test is over; ask the next question")
    elif ok:
        lines.append("next: tell the learner it was right, in one line, then go on")
    else:
        lines.append("next: tell the learner it was wrong; %s; find the cause and "
                     "%s; repair the gap in a few lines; only then go on" % (
                         "give the KEY and the SOLUTION above" if reveal else "say what the check showed",
                         ("it is recorded as %s (mistake %s <kind> changes that)" % (err, item_id)) if err
                         else "record it: mistake %s %s" % (item_id, "|".join(ERROR_TAGS))))
    return "\n".join(lines)


def _credit_lines(state, when, credit) -> list:
    lines = []
    for i, c in enumerate(credit):
        ts = state.topics.get(c["topic"])
        label = "grade" if i == 0 else ("same topic elsewhere" if c.get("eq") else "also credited")
        if ts is None or ts.card is None:  # a placement miss on a topic never studied
            lines.append("%s: %s %s · not scheduled" % (label, c["topic"], fsrs.GRADE_NAMES[c["g"]]))
            continue
        lines.append("%s: %s %s · next review %s (%s)" % (
            label, c["topic"], fsrs.GRADE_NAMES[c["g"]], fmt_delta(ts.card.due - when), ts.card.due.strftime("%a %d %b")))
    return lines


def quick(repo: Repo, tree, state, when, key: str, result: str, note: str | None = None,
          err: str | None = None, hints: int = 0) -> str:
    """Record an oral check (no stored item). It schedules the topic but is never mastery evidence."""
    topic = tree.topic(key)
    if result not in ("pass", "fail"):
        raise CalError("result must be pass or fail")
    if err and err not in ERROR_TAGS:
        raise CalError("--err must be one of: %s" % ", ".join(ERROR_TAGS))
    ok = result == "pass"
    ts = state.topics.get(topic.key)
    if not ok and (ts is None or (ts.card is None and ts.covered_ts is None)):
        raise CalError("%s has not been studied yet (never taught, never answered), so a miss needs no record: "
                       "it is still ahead in the plan. If it was taught just now, run: covered %s"
                       % (topic.key, topic.key))
    grade = fsrs.AGAIN if not ok else (fsrs.HARD if hints else fsrs.GOOD)
    credit = _record(repo, tree, state, when, topic.key, [topic.key], ok, grade, hints, None,
                     quick=True, verified=False, err=(err if not ok else None), note=note)
    new_state = State(repo, tree)
    lines = ["%s (oral check) · %s" % ("CORRECT" if ok else "WRONG", topic.key)]
    lines.extend(_credit_lines(new_state, when, credit))
    lines.append(describe_topic(repo, new_state, topic.key))
    lines.append(plan.today_line(plan.today(repo, tree, new_state, when)))
    return "\n".join(lines)


# ---------------------------------------------------------------- placement and boss


def placement(repo: Repo, tree, state, skill_id: str, known, gaps, result: str | None, note: str | None) -> str:
    node = tree.get(skill_id)
    known = csv_list(known)
    gaps = csv_list(gaps)
    for tid in known + gaps:
        if node.topic(tid) is None:
            raise CalError("unknown topic %r in %s (use topic ids, not full keys)" % (tid, skill_id))
    if set(known) & set(gaps):
        raise CalError("a topic cannot be both known and a gap")
    if result is None:
        all_ids = {t.id for t in node.topics}
        if not gaps and (not all_ids or set(known) >= all_ids):
            result = "known"
        elif known:
            result = "partial"
        else:
            result = "none"
    if result not in ("known", "partial", "none"):
        raise CalError("result must be known, partial or none")
    if result == "known" and gaps:
        raise CalError("result 'known' cannot list gaps")
    if result == "known" and not known:
        known = [t.id for t in node.topics]  # the whole skill: every topic enters the review rotation
    repo.append("placement", skill=skill_id, known=known, gaps=gaps, result=result, note=note)
    lines = ["placement recorded: %s -> %s" % (skill_id, result)]
    if known:
        lines.append("%d topic(s) marked known; they enter the review rotation" % len(known))
    if result == "known":
        lines.append("%s now counts as a met prerequisite" % skill_id)
    elif gaps:
        lines.append("gaps to learn: %s" % ", ".join(gaps))
        sk = state.skills.get(skill_id)
        if sk is None or not sk.enrolled:
            lines.append("enroll to schedule the gaps: enroll %s" % skill_id)
    return "\n".join(lines)


def boss_record(repo: Repo, tree, state, skill_id: str, ok: bool, evidence: str, kind: str = "project") -> str:
    node = tree.get(skill_id)
    if not (evidence or "").strip():
        raise CalError("--evidence is required: what was built or tested, and how it was checked")
    repo.append("boss", skill=skill_id, ok=bool(ok), kind=kind, evidence=evidence.strip())
    if not ok:
        return "boss attempt recorded for %s: not passed yet" % skill_id
    new_state = State(repo, tree)
    lines = ["boss passed: %s | %s" % (skill_id, node.title), "status: %s" % new_state.skill_status(skill_id)]
    unlocked = [d.id for d in tree.dependents(skill_id)
                if new_state.skill_status(d.id) == "available" and state.skill_status(d.id) == "locked"]
    if unlocked:
        lines.append("unlocked: %s" % ", ".join(unlocked))
    return "\n".join(lines)


def boss_status(repo: Repo, tree, state, skill_id: str | None = None) -> str:
    if skill_id:
        node = tree.get(skill_id)
        sk = state.skills.get(skill_id)
        counts = state.skill_counts(skill_id)
        lines = ["BOSS %s | %s" % (skill_id, node.title)]
        if sk is not None and sk.boss_ok:
            lines.append("state: passed on %s" % sk.boss_ts.date().isoformat())
        elif counts["total"] and counts["solid"] + counts["mastered"] < counts["total"]:
            lines.append("state: not due yet (%d of %d topics are solid)" % (counts["solid"] + counts["mastered"], counts["total"]))
        else:
            lines.append("state: due")
        spec = node.section("Boss")
        lines.append("")
        lines.append(spec or "(this skill defines no boss; a timed mixed test of its topics serves instead: test build --skills %s)" % skill_id)
        lines.append("")
        lines.append("record with: boss record %s pass|fail --evidence \"repo or test id, checks run, results\"" % skill_id)
        return "\n".join(lines)
    ready = plan.boss_ready(repo, tree, state)
    if not ready:
        return "No boss is due. A boss comes up when every topic of an enrolled skill is solid."
    return "Bosses due:\n" + "\n".join("  %s | %s" % (s, tree.nodes[s].title) for s in ready)


# ---------------------------------------------------------------- timed tests


def test_build(repo: Repo, tree, state, when, skills, n: int, minutes: int, label: str | None = None):
    """Assemble a timed mixed test from verified items. Returns (exit_code, text)."""
    skills = [tree.get(s).id for s in csv_list(skills)]
    if not skills:
        raise CalError("name the skills to draw from: --skills a,b")
    if n < 1 or n > 100:
        raise CalError("--n must be between 1 and 100")
    by_topic = {}
    for it in state.items.values():
        if it.status != "verified" or not it.topics:
            continue
        if it.topics[0].split("/", 1)[0] not in skills or not tree.has_topic(it.topics[0]):
            continue
        last = it.last_ts or it.shown_ts
        rank = (0 if it.n_shown == 0 else 1, last.timestamp() if last else 0.0, it.id)
        by_topic.setdefault(it.topics[0], []).append(rank)
    pools = [sorted(v) for _, v in sorted(by_topic.items())]
    chosen, depth = [], 0
    while len(chosen) < n and any(depth < len(p) for p in pools):
        for pool in pools:
            if depth < len(pool) and len(chosen) < n:
                chosen.append(pool[depth][2])
        depth += 1
    if len(chosen) < n:
        lines = ["NEED_ITEM", "A %d-item test needs %d more verified item(s)." % (n, n - len(chosen)), "verified items per skill:"]
        for s in skills:
            have = sum(len(v) for k, v in by_topic.items() if k.split("/", 1)[0] == s)
            empty = [t.key for t in tree.nodes[s].topics if t.key not in by_topic]
            lines.append("  %s: %d item(s); topics with none: %s" % (s, have, ", ".join(empty[:8]) or "-"))
        lines.append("Have the examiner and checker agents fill the gaps, then build the test again.")
        return NEED_ITEM, "\n".join(lines)
    test_id = short_id("t-")
    repo.append("test_build", test=test_id, items=chosen, minutes=int(minutes), label=label, skills=skills)
    lines = ["TEST %s%s · %d items · %d minutes" % (test_id, (" (%s)" % label) if label else "", len(chosen), minutes),
             "Exam conditions: no hints, no solutions until the end.", "items, in order:"]
    lines += ["  %d. %s" % (i, item_id) for i, item_id in enumerate(chosen, 1)]
    lines.append("for each: ask --id <item> --test %s   then   answer <item> --answer ..." % test_id)
    lines.append("when done (or time is up): test finish %s" % test_id)
    return 0, "\n".join(lines)


def test_finish(repo: Repo, tree, state, when, test_id: str) -> str:
    test = state.tests.get(test_id)
    if test is None:
        raise CalError("unknown test %s" % test_id)
    if test["finished"]:
        raise CalError("test %s is already finished" % test_id)
    rows, score, best, right, wrong = [], 0.0, 0.0, 0, 0
    has_marks = False
    reveals = []
    for item_id in test["items"]:
        item = items.load(repo, item_id)
        full = float(item.get("marks") or 1)
        has_marks = has_marks or bool(item.get("marks"))
        best += full
        ans = test["answers"].get(item_id)
        if ans is None:
            rows.append([item_id, item["topics"][0], "skipped", "0"])
            continue
        got = ans["marks"] if ans.get("marks") is not None else (full if ans["ok"] else 0.0)
        score += got
        right += 1 if ans["ok"] else 0
        wrong += 0 if ans["ok"] else 1
        rows.append([item_id, item["topics"][0], "correct" if ans["ok"] else "wrong", "%+.2f" % got])
        if not ans["ok"]:
            reveals.append("%s\n%s" % (item_id, items.reveal_text(item)))
    skipped = len(test["items"]) - right - wrong
    used = int((when - test["built"]).total_seconds() // 60)
    share = (score / best) if best else 0.0
    repo.append("test_finish", test=test_id, score=round(score, 2), max=best, correct=right, wrong=wrong,
                skipped=skipped, minutes_used=used, share=round(share, 4))
    lines = ["TEST %s finished%s" % (test_id, (" (%s)" % test["label"]) if test.get("label") else ""),
             "score: %.2f of %.0f (%d%%)%s" % (score, best, round(100 * share),
                                               " with GATE negative marking" if has_marks else ""),
             "correct %d · wrong %d · skipped %d · time %d of %s min" % (right, wrong, skipped, used, test.get("minutes") or "?"),
             "", table(rows, ["item", "topic", "result", "marks"], aligns="lllr")]
    if reveals:
        lines += ["", "Solutions for the missed items:"] + reveals
    return "\n".join(lines)
