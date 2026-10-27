"""Findings of the first review round (E, N) and the features added with them: the model and
effort suggestion, and teaching from the basics. Each test names the finding it covers."""
import json
import os
import re
from datetime import timedelta

from tests.helpers import Case, read, write

from cal import advise, remind, snapshot, store
from cal.state import State
from cal.store import Repo
from cal.tree import Tree
from cal.util import CalError


class LogAndReplay(Case):
    def repo(self):
        repo = Repo(self.sb.root)
        repo.set_machine("a")
        return repo

    def test_e1_a_torn_character_costs_one_line_not_the_file(self):
        repo = self.repo()
        when = self.sb.clock
        repo.append("note", when=when, text="before")
        path = os.path.join(repo.events_dir, "%s.a.jsonl" % when.strftime("%Y-%m"))
        with open(path, "ab") as fh:  # a write cut off inside the two bytes of "é"
            fh.write(('{"id":"t1","ts":"%s","m":"a","t":"note","text":"caf' % when.isoformat()).encode("utf-8")
                     + "é".encode("utf-8")[:1])
        repo.append("note", when=when + timedelta(minutes=5), text="after é")
        repo.invalidate()
        self.assertEqual([e["text"] for e in repo.events()], ["before", "after é"])
        self.assertEqual(len(repo.event_errors), 1)
        self.assertIn("UTF-8", repo.event_errors[0])
        tree = Tree(repo)
        full = State(repo, tree, use_cache=False)
        self.assertEqual(full.n_events, 2)
        State(repo, tree, use_cache=True)                     # writes a snapshot
        cached = State(Repo(self.sb.root), Tree(Repo(self.sb.root)), use_cache=True)
        self.assertEqual(cached.fingerprint(), full.fingerprint())

    def test_e4_renaming_back_makes_the_old_name_live_again(self):
        repo = self.repo()
        repo.append("rename", when=self.sb.clock, what="topic", old="shell/pipes", new="shell/perms")
        repo.append("rename", when=self.sb.clock + timedelta(minutes=1), what="topic", old="shell/perms",
                    new="shell/pipes")
        st = self.sb.state()
        self.assertEqual(st.canon("shell/pipes"), "shell/pipes")
        self.assertEqual(st.canon("shell/perms"), "shell/pipes")

    def test_e5_e8_bad_ids_and_times_without_offset_are_reported(self):
        sb = self.sb
        sb.onboard()
        write(sb.path("learner", "events", "2026-03.zz.jsonl"),
              '{"id":"b1","ts":"2026-03-02T09:00:00+05:30","t":"shown","item":5}\n'
              '{"id":"b2","ts":"2026-03-02T09:00:00","t":"note","text":"no offset"}\n')
        out = sb.run("doctor", expect=None)
        self.assertIn(sb.code, (0, 1))
        self.assertIn("'item' is not a string", out)
        self.assertIn("UTC offset", out)
        sb.run("rebuild", expect=None)
        self.assertNotIn("Traceback", sb.err)

    def test_e9_a_damaged_snapshot_falls_back_to_a_full_replay(self):
        sb = self.sb
        sb.onboard()
        sb.run("observe", "something")
        repo = Repo(sb.root)
        State(repo, Tree(repo), use_cache=True)
        path = snapshot.path(repo)
        data = json.loads(read(path))
        data["files"] = {name: "garbage" for name in data["files"]}
        write(path, json.dumps(data))
        repo = Repo(sb.root)
        st = State(repo, Tree(repo), use_cache=True)
        self.assertIn("full replay", st.cache_info)

    def test_n14_the_lock_gives_up_on_every_system(self):
        path = self.sb.path(".calamity", "write.lock")
        with store.file_lock(path):
            with self.assertRaises(CalError):
                with store.file_lock(path, wait=0.2):
                    pass


class Items(Case):
    def test_e2_only_verified_items_are_disputed_and_restored(self):
        sb = self.sb
        sb.onboard()
        draft = sb.draft("shell/pipes")
        sb.run("item", "dispute", draft, "--reason", "looks wrong", expect=2)
        good = sb.item("shell/perms")
        sb.run("item", "dispute", good, "--reason", "key looks wrong")
        sb.run("item", "restore", good)
        self.assertEqual(sb.state().items[good].status, "verified")
        bad = sb.draft("shell/pipes")
        sb.run("item", "reject", bad, "--reason", "ambiguous")
        sb.run("item", "restore", bad, expect=2)
        # older logs: a dispute and a restore of a draft change nothing in replay
        old = sb.draft("shell/pipes")
        repo = Repo(sb.root)
        repo.append("item_dispute", when=sb.clock + timedelta(minutes=1), item=old, reason="old log")
        repo.append("item_restore", when=sb.clock + timedelta(minutes=2), item=old)
        self.assertEqual(sb.state().items[old].status, "draft")

    def test_e12_the_examiner_never_verifies(self):
        sb = self.sb
        sb.onboard()
        ident = sb.draft("shell/pipes", by="someone")
        sb.run("item", "verify", ident, "--answer", "B", "--by", "examiner", expect=2)
        self.assertIn("examiner", sb.err)

    def test_e10_bad_drafts_and_names_give_messages_not_tracebacks(self):
        sb = self.sb
        sb.onboard()
        base = {"type": "mcq", "topics": ["shell/pipes"], "stem": "Which option is the right one here?",
                "options": ["a one", "b two"], "answer": "B", "solution": "B is right because it is."}
        for extra in ({"source": 5}, {"difficulty": float("inf")}):
            path = sb.path(".calamity", "tmp", "bad.json")
            write(path, json.dumps(dict(base, **extra)))
            sb.run("item", "draft", "--file", path, "--by", "examiner", expect=2)
            self.assertNotIn("Traceback", sb.err)
        text = read(sb.path("learner", "profile.md")).replace("name: Tester", "name: [a, b]")
        write(sb.path("learner", "profile.md"), text)
        sb.run("dash")
        sb.run("rebuild", expect=None)
        self.assertNotIn("Traceback", sb.err)


class LearnerFiles(Case):
    def test_e6_a_profile_in_another_encoding_is_reported_and_left_alone(self):
        sb = self.sb
        raw = b"---\nname: Jos\xe9\nonboarded: true\n---\n"
        os.makedirs(sb.path("learner"), exist_ok=True)
        with open(sb.path("learner", "profile.md"), "wb") as fh:
            fh.write(raw)
        self.assertIn("not UTF-8", sb.run("brief"))
        self.assertIn("not UTF-8", sb.run("doctor", expect=None))
        sb.run("profile", "set", "sleep.start", "01:00", expect=2)
        with open(sb.path("learner", "profile.md"), "rb") as fh:
            self.assertEqual(fh.read(), raw)


class Reminders(Case):
    def test_n1_n13_removal_needs_no_times_and_is_per_clone(self):
        sb = self.sb
        out = sb.run("remind", "remove", "--os", "linux")
        tag = remind.clone_tag(Repo(sb.root))
        self.assertIn("calamity-remind-%s" % tag, out)
        self.assertIn("LaunchAgents/com.calamity.remind.%s.plist" % tag, sb.run("remind", "remove", "--os", "darwin"))
        self.assertNotEqual(tag, remind.clone_tag(Repo(sb.root + "-other")))

    def test_n6_n7_windows_files(self):
        sb = self.sb
        sb.run("remind", "render", "--times", "09:00,21:00", "--os", "windows")
        folder = sb.path(".calamity", "reminders")
        with open(os.path.join(folder, "install.ps1"), "rb") as fh:
            ps1 = fh.read()
        self.assertTrue(ps1.startswith(b"\xef\xbb\xbf"))                  # UTF-8 with a BOM for PowerShell 5.1
        self.assertIn(b"-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable", ps1)
        with open(os.path.join(folder, "install.cmd"), "rb") as fh:
            cmd = fh.read()
        cmd.decode("ascii")                                               # cmd.exe reads the OEM code page
        self.assertIn(b"%~dp0install.ps1", cmd)
        self.assertTrue(os.path.isfile(os.path.join(folder, "remove.cmd")))

    def test_n11_macos_creates_the_folder(self):
        out = self.sb.run("remind", "render", "--times", "09:00", "--os", "darwin")
        self.assertIn("mkdir -p ~/Library/LaunchAgents", out)


class Dashboard(Case):
    def test_n5_nothing_scheduled_is_an_empty_bar(self):
        sb = self.sb
        sb.onboard()
        self.assertIn("reviews ░░░░░░░░░░ 0/0", sb.run("dash"))


class Advice(Case):
    def test_the_table_and_its_overrides(self):
        sb = self.sb
        sb.onboard()
        repo = Repo(sb.root)
        line = advise.line(repo, "review")
        self.assertIn("reviews next; suggested /model sonnet, /effort medium", line)
        self.assertTrue(line.endswith("(a suggestion, not measured)"))
        self.assertIn("/model opus, /effort high", advise.line(repo, "stock"))
        self.assertIn("keep your usual /model and /effort", advise.line(repo, "new"))
        self.assertIn("fits", advise.line(repo, "review", {"model": "claude-sonnet-5-5", "effort": "medium"}))
        sb.run("profile", "set", "cfg.advice.light", "haiku low")
        self.assertIn("/model haiku, /effort low", advise.line(Repo(sb.root), "review"))
        self.assertEqual(advise.short(Repo(sb.root), "review"), "try haiku·low")

    def test_the_off_switch(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        self.assertIn("settings:", sb.run("next"))
        sb.run("profile", "set", "cfg.advice", "false")
        self.assertNotIn("settings:", sb.run("next"))
        self.assertNotIn("Settings:", sb.run("brief"))
        self.assertEqual(advise.line(Repo(sb.root), "review"), "")

    def test_the_brief_line(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        brief = sb.run("brief")
        self.assertIn("Settings: writing and checking items next", brief)  # no item yet: stocking comes first
        self.assertLess(len(brief), 6000)
        sb.item("shell/pipes")
        sb.item("shell/perms")
        hooked = sb.run("brief", "--hook", stdin=json.dumps({"source": "startup", "model": "claude-opus-5-5"}))
        self.assertIn("Settings: teaching a new topic next", hooked)


class Basics(Case):
    def test_a_first_topic_is_taught_from_zero(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        out = sb.run("next")
        self.assertIn("NEXT: new", out)
        self.assertIn("level: 1 of 5 · the first topic of shell for this learner", out)
        self.assertIn("objectives: chain two commands with a pipe", out)
        self.assertIn("start from zero", out)

    def test_teaching_a_later_topic_first_is_flagged(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        sb.item("shell/perms")
        out = sb.run("ask", "--topic", "shell/perms", "--taught")
        self.assertIn("note: shell/perms builds on shell/pipes, not studied yet", out)


class AnswerNext(Case):
    def test_a_right_answer_serves_the_next_question_and_a_wrong_one_does_not(self):
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        sb.item("shell/perms")
        sb.run("covered", "shell/pipes", "shell/perms")    # both taught: the next new topic is tested at once
        served = sb.ask("shell/pipes")
        sb.advance(seconds=30)
        out = sb.run("answer", served, "--answer", "B", "--next", "--skill", "shell")
        self.assertTrue(out.startswith("CORRECT"))
        self.assertLess(out.index("next:"), out.index("=== NEXT"))      # feedback first
        self.assertIn("=== NEXT", out)
        nxt = re.search(r"=== NEXT.*?ITEM (it-[a-z0-9]{10})", out, re.S)
        self.assertIsNotNone(nxt, out)
        sb.advance(seconds=30)
        wrong = sb.run("answer", nxt.group(1), "--answer", "A", "--next")
        self.assertTrue(wrong.startswith("WRONG"))
        self.assertIn("--next: nothing served", wrong)
        self.assertNotIn("=== NEXT", wrong)
