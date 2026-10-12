import json
import os
import random
import shutil
import unittest

from tests.helpers import Case, Sandbox, write

from cal import progress
from cal.state import State
from cal.store import Repo
from cal.tree import Tree


def summary(root):
    """Everything derived from the log that a learner would notice, as plain data."""
    repo = Repo(root)
    tree = Tree(repo)
    state = State(repo, tree)
    topics = {}
    for key, ts in sorted(state.topics.items()):
        card = ts.card
        topics[key] = (
            state.topic_status(key), ts.n, ts.n_ok, ts.n_vok, sorted(ts.ok_days), sorted(ts.errors.items()),
            None if card is None else (round(card.s, 9), round(card.d, 9), card.due.isoformat(), card.reps, card.lapses),
        )
    skills = {sid: state.skill_status(sid) for sid in sorted(tree.nodes)}
    items = {iid: (it.status, it.n_shown, it.n_ok, it.n_fail) for iid, it in sorted(state.items.items())}
    days = {day: (ds.attempts, ds.ok, ds.new, ds.reviews, ds.src_done, round(ds.active_min, 6), ds.sessions)
            for day, ds in sorted(state.days.items())}
    return {"topics": topics, "skills": skills, "items": items, "days": days, "events": state.n_events,
            "progress": progress.render(repo, tree, state)}


class Determinism(Case):
    def build_history(self):
        sb = self.sb
        sb.onboard(tracks="dev", cfg__fuzz="true")     # with the spread on: it must replay identically too
        sb.run("enroll", "shell")
        sb.advance(minutes=1)
        sb.run("enroll", "java")
        keys = {}
        for topic in ("shell/pipes", "shell/perms", "java/classes", "java/collections", "java/streams"):
            for _ in range(2):
                keys[sb.item(topic)] = "B"
        rng = random.Random(7)
        for day in range(12):
            for topic in ("shell/pipes", "shell/perms", "java/classes", "java/collections", "java/streams"):
                ts = sb.state().topics.get(topic)
                if ts is not None and ts.card is not None and ts.card.due > sb.clock:
                    continue
                sb.advance(minutes=rng.randint(2, 9))
                ident = sb.ask(topic)
                wrong = rng.random() < 0.25
                sb.answer(ident, "A" if wrong else "B", seconds=rng.randint(20, 150),
                          **({"err": "memory"} if wrong else {}))
            sb.run("workout", "30")
            sb.advance(days=1)
        sb.run("boss", "record", "shell", "fail", "--evidence", "script not idempotent")
        sb.run("observe", "prefers examples first", "--skill", "java")
        # events that change what earlier events mean: a placement test, a mistake classified
        # after the fact (twice), and an answer voided because its key was wrong
        docker = {t: sb.item("docker/" + t) for t in ("images", "dockerfile")}
        for topic, given in (("images", "B"), ("dockerfile", "A")):
            sb.ask("docker/" + topic)
            sb.answer(docker[topic], given, seconds=30, kind="placement")
        sb.run("placement", "docker", "--known", "images", "--gaps", "dockerfile,multi-stage")
        late = sb.item("shell/pipes", answer="C")
        sb.run("ask", "--id", late)
        sb.answer(late, "A")
        sb.run("mistake", late, "careless")
        sb.advance(minutes=3)
        sb.run("mistake", late, "concept", "--note", "on reflection")
        unfair = sb.item("java/classes", answer="D")
        sb.run("ask", "--id", unfair)
        sb.answer(unfair, "A", err="memory")
        sb.run("item", "dispute", unfair, "--reason", "two options were right", "--void")

    def test_same_events_in_any_arrangement_give_the_same_state(self):
        self.build_history()
        sb = self.sb
        reference = summary(sb.root)
        self.assertGreater(reference["events"], 80)
        self.assertTrue(any(v[0] != "new" for v in reference["topics"].values()))
        self.assertIn(("concept", 1), reference["topics"]["shell/pipes"][5])       # the later classification stands
        self.assertNotIn("careless", dict(reference["topics"]["shell/pipes"][5]))
        self.assertIsNone(reference["topics"]["docker/dockerfile"][6])             # the placement miss scheduled nothing
        self.assertEqual(reference["topics"]["docker/images"][0], "solid")

        events_dir = sb.path("learner", "events")
        lines = []
        for name in sorted(os.listdir(events_dir)):
            with open(os.path.join(events_dir, name), "r", encoding="utf-8") as fh:
                lines += [line for line in fh.read().split("\n") if line.strip()]
        original_machine = json.loads(lines[0])["m"]

        for seed in (1, 2, 3):
            rng = random.Random(seed)
            other = Sandbox()
            self.addCleanup(other.close)
            for sub in ("items", "syllabus"):
                if os.path.isdir(sb.path("learner", sub)):
                    shutil.copytree(sb.path("learner", sub), other.path("learner", sub))
            shutil.copyfile(sb.path("learner", "profile.md"), other.path("learner", "profile.md"))
            # deal the same events out to three files in a shuffled order, with some lines duplicated
            # (what copying, re-ordering and a union merge between laptops can do to the files)
            shuffled = list(lines)
            rng.shuffle(shuffled)
            buckets = {"2026-03.a.jsonl": [], "2026-03.%s.jsonl" % original_machine: [], "2026-04.zzz.jsonl": []}
            names = sorted(buckets)
            for line in shuffled:
                buckets[rng.choice(names)].append(line)
                if rng.random() < 0.1:
                    buckets[rng.choice(names)].append(line)
            for name, content in buckets.items():
                write(other.path("learner", "events", name), "\n".join(content) + "\n")
            self.assertEqual(summary(other.root), reference, "arrangement %d differs" % seed)

    def test_progress_file_does_not_depend_on_the_clock(self):
        self.build_history()
        sb = self.sb
        first = sb.run("rebuild")
        self.assertIn("wrote learner/PROGRESS.md", first)
        with open(sb.path("learner", "PROGRESS.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("| shell | Shell | dev |", text)
        self.assertIn("## Weeks", text)
        sb.advance(days=400)
        sb.run("rebuild")
        with open(sb.path("learner", "PROGRESS.md"), "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), text)

    def test_rebuild_reports_damage(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        name = os.listdir(sb.path("learner", "events"))[0]
        with open(sb.path("learner", "events", name), "a", encoding="utf-8") as fh:
            fh.write("=======\n")
        out = sb.run("rebuild", expect=2)
        self.assertIn("could not be read", out)
        self.assertIn("conflict marker", out)

    def test_unknown_event_types_are_ignored(self):
        sb = self.sb
        sb.onboard()
        Repo(sb.root).append("something_from_a_newer_version", when=sb.clock, payload={"a": 1})
        self.assertIn("NEXT: enroll", sb.run("next"))


if __name__ == "__main__":
    unittest.main()
