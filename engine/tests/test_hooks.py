"""The hooks suite (WP-17): routing, feedback tokens, the Stop guard, compaction, session end, auto-start."""
import json
import os

from tests.helpers import Case, Sandbox, read, write

SID = "sess-1"


class Hooks(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        sb.item("shell/pipes")

    def hook(self, args, payload, expect=0):
        out = self.sb.run(*args, stdin=json.dumps(payload), expect=expect)
        return json.loads(out) if out.strip().startswith("{") else out

    def prompt(self, text):
        return self.hook(["guard", "prompt"], {"session_id": SID, "prompt": text, "hook_event_name": "UserPromptSubmit"})

    def context(self, out):
        return out["hookSpecificOutput"]["additionalContext"] if isinstance(out, dict) else out

    def test_router_names_the_skill_a_request_belongs_to(self):
        self.assertIn("/log", self.context(self.prompt("I watched lecture 12 of the OS course")))
        self.assertIn("/recall", self.context(self.prompt("quiz me")))
        self.assertIn("/practice", self.context(self.prompt("solved questions 1-10 from the PYQ book")))
        self.assertIn("/career", self.context(self.prompt("find me backend internships")))
        self.assertIn("/gate", self.context(self.prompt("find mocks near me")))
        self.assertIn("/explain", self.context(self.prompt("what is a pipe?")))          # an ad-hoc teaching ask
        self.assertIn("/explain", self.context(self.prompt("explain how a hashmap works")))
        self.assertIn("/explain", self.context(self.prompt("teach me about TCP")))
        self.assertIn("/explain", self.context(self.prompt("I don't understand recursion")))
        self.assertIn("/explain", self.context(self.prompt("I'm confused about closures")))
        self.assertIn("/explain", self.context(self.prompt("break down how TLS works")))
        self.assertIn("/mastery-coach", self.context(self.prompt("I want to master Rust")))  # mastery wins over explain
        self.assertEqual(self.prompt("let's resume where we stopped"), "")    # resume is not a résumé
        self.assertEqual(self.prompt("what is my rating"), "")               # a possessive, not a concept: silence
        self.assertEqual(self.prompt("[SYSTEM NOTIFICATION - NOT USER INPUT] <task-notification>reminders</task-notification>"),
                         "")                                                  # Claude Code's own notices are not routed
        self.assertEqual(self.prompt("/recall quiz me"), "")                 # a slash command routes itself

    def test_feedback_tokens_are_recorded(self):
        out = self.context(self.prompt("ok but !slow and !example please"))
        self.assertIn("slow down", out)
        self.assertIn("worked example", out)
        notes = [n for n in self.sb.state().notes if n["tag"] == "feedback"]
        self.assertEqual((notes[-1]["pace"], notes[-1]["clarity"]), ("fast", "low"))
        self.assertIn("feedback: pace=fast clarity=low", self.sb.run("day"))
        self.prompt("!harder")
        self.assertIn("feedback: level=harder", self.sb.run("day"))

    def test_stop_blocks_once_when_an_answer_was_not_recorded(self):
        sb = self.sb
        self.prompt("/study")
        item = sb.ask("shell/pipes")
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID}), "")     # waiting for the answer
        sb.advance(seconds=30)
        self.prompt("B")
        out = self.hook(["guard", "stop"], {"session_id": SID})
        self.assertEqual(out["decision"], "block")
        self.assertIn(item, out["reason"])
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID, "stop_hook_active": True}), "")
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID}), "")     # raised once, never again

    def test_stop_asks_for_the_notes_fragment_of_a_topic_taught_today(self):
        sb = self.sb
        self.prompt("/study")
        item = sb.ask("shell/pipes")
        sb.run("ask", "--topic", "shell/pipes", "--taught", "--parts", "model,example")
        out = self.hook(["guard", "stop"], {"session_id": SID})
        self.assertIn("shell/pipes was taught today and has no notes fragment", out["reason"])
        path = sb.run("notes", "fragment", "shell/pipes").strip()
        self.assertTrue(item)
        write(os.path.join(sb.root, path) if not os.path.isabs(path) else path,
              "---\ntopic: shell/pipes\n---\n## Idea\n\nA pipe hands stdout to the next stdin.\n")
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID}), "")

    def test_stop_stays_out_of_sessions_that_do_not_teach(self):
        self.prompt("/dash")
        self.sb.ask("shell/pipes")
        self.prompt("B")
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID}), "")

    def test_compaction_resumes_on_the_same_item(self):
        sb = self.sb
        self.prompt("/study")
        item = sb.ask("shell/pipes")
        self.hook(["snapshot", "--session"], {"session_id": SID, "trigger": "auto"})
        out = self.hook(["brief", "--hook"], {"session_id": SID, "source": "compact"})
        text = self.context(out)
        self.assertIn("=== CALAMITY BRIEF ===", text)
        self.assertIn("Resumed after compaction", text)
        self.assertIn("item in flight: %s on shell/pipes" % item, text)
        self.assertIn("skill: /study", text)

    def test_session_end_is_an_event(self):
        self.hook(["guard", "end"], {"session_id": SID, "reason": "logout"})
        ends = [e for e in self.sb.state().repo.events() if e["t"] == "session_end"]
        self.assertEqual(ends[-1]["reason"], "logout")

    def test_auto_start_opens_day_only_when_turned_on(self):
        sb = self.sb
        plain = self.hook(["brief", "--hook"], {"session_id": SID, "source": "startup"})
        self.assertIsInstance(plain, str)                                     # the brief as plain text
        sb.run("profile", "set", "auto.start", "true")
        out = self.hook(["brief", "--hook"], {"session_id": SID, "source": "startup"})
        self.assertEqual(out["hookSpecificOutput"]["initialUserMessage"], "/day")
        self.assertIn("=== CALAMITY BRIEF ===", out["hookSpecificOutput"]["additionalContext"])
        resumed = self.hook(["brief", "--hook"], {"session_id": SID, "source": "resume"})
        self.assertNotIn("initialUserMessage", json.dumps(resumed))
        sb.env["CALAMITY_MAINTAIN"] = "1"
        self.assertNotIn("initialUserMessage", json.dumps(self.hook(["brief", "--hook"], {"source": "startup"})))

    def test_the_kill_switch_silences_every_hook(self):
        sb = self.sb
        sb.env["CALAMITY_HOOKS"] = "off"
        self.assertEqual(self.prompt("quiz me !slow"), "")
        self.prompt("/study")
        sb.ask("shell/pipes")
        self.prompt("B")
        self.assertEqual(self.hook(["guard", "stop"], {"session_id": SID}), "")
        self.hook(["guard", "end"], {"session_id": SID})
        self.assertFalse([e for e in sb.state().repo.events() if e["t"] in ("session_end", "feedback")])


class NoLearner(Case):
    def test_a_clone_without_a_learner_never_auto_starts_or_records(self):
        sb = self.sb
        out = sb.run("brief", "--hook", stdin=json.dumps({"source": "startup"}))
        self.assertIn("NOT ONBOARDED", out)
        self.assertNotIn("initialUserMessage", out)
        self.assertEqual(sb.run("guard", "prompt", stdin=json.dumps({"prompt": "!slow quiz me"})), "")
        sb.run("guard", "end", stdin=json.dumps({"reason": "x"}))
        self.assertFalse(os.path.isdir(sb.path("learner", "events")) and os.listdir(sb.path("learner", "events")))


class BigFiles(Case):
    def test_a_whole_read_of_a_big_source_file_is_turned_to_a_slice(self):
        from cal import guard

        sb = self.sb
        big = sb.path("learner", "sources", "course.md")
        write(big, "x" * (25 * 1024))
        small = sb.path("learner", "sources", "book.md")
        write(small, "small\n")
        notes = sb.path("learner", "notes", "shell", "pipes.md")
        write(notes, "y" * (25 * 1024))
        call = {"tool_name": "Read", "cwd": sb.root}
        reason = guard.decide(dict(call, tool_input={"file_path": big}), sb.root)
        self.assertIn("source show", reason)
        self.assertIsNone(guard.decide(dict(call, tool_input={"file_path": big, "limit": 40}), sb.root))
        self.assertIsNone(guard.decide(dict(call, tool_input={"file_path": small}), sb.root))
        self.assertIsNone(guard.decide(dict(call, tool_input={"file_path": notes}), sb.root))   # notes are the learner's


class Slices(Case):
    def test_compact_needs_brief_stats_and_html_dashboards(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        out = sb.run("item", "needs", "--compact")
        self.assertRegex(out, r"^ITEMS NEEDED: \d+ topic\(s\): shell/pipes")
        self.assertEqual(len(out.strip().split("\n")), 1)
        sb.run("workout", "30")
        brief = sb.run("stats", "brief")
        self.assertIn("last 7 days: 1 active", brief)
        self.assertLessEqual(len(brief.strip().split("\n")), 2)
        two = sb.run("dash", "queue", "--html").strip().split("\n")
        self.assertEqual(len(two), 2)
        page = two[1].split(" written to ")[1].split(" (open")[0]
        self.assertTrue(page.endswith(os.path.join("dash", "queue.html")))
        self.assertIn("<pre>", read(page))
