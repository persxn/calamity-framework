import json
import os
import unittest
from datetime import datetime

from tests.helpers import Case, write

from cal.store import Repo
from cal.util import CalError, daykey, day_bounds, fmt_delta, in_window, minutes_until, parse_hhmm, parse_ts, table


def at(stamp):
    return datetime.fromisoformat(stamp)


class EventLog(Case):
    def repo(self):
        return Repo(self.sb.root)

    def test_one_file_per_machine_and_month(self):
        repo = self.repo()
        repo.set_machine("laptop-a")
        repo.append("note", when=at("2026-03-31T23:00:00+05:30"), text="march")
        repo.append("note", when=at("2026-04-01T01:00:00+05:30"), text="april")
        names = sorted(os.listdir(repo.events_dir))
        self.assertEqual(names, ["2026-03.laptop-a.jsonl", "2026-04.laptop-a.jsonl"])
        with open(os.path.join(repo.events_dir, names[0]), "rb") as fh:
            raw = fh.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        event = json.loads(raw.decode("utf-8"))
        self.assertEqual(event["m"], "laptop-a")
        self.assertEqual(event["t"], "note")
        self.assertEqual(event["v"], 1)
        self.assertNotIn("skill", event)  # None values are not written

    def test_order_is_by_time_then_machine(self):
        repo = self.repo()
        repo.set_machine("zeta")
        repo.append("note", when=at("2026-03-02T10:00:00+05:30"), text="second")
        repo.append("note", when=at("2026-03-02T09:00:00+05:30"), text="first")
        other = {"id": "x" * 20, "ts": "2026-03-02T04:30:00+00:00", "m": "alpha", "t": "note", "v": 1, "text": "tie"}
        write(os.path.join(repo.events_dir, "2026-03.alpha.jsonl"), json.dumps(other) + "\n")
        repo.invalidate()
        # 04:30 UTC is 10:00 +05:30: the same instant as "second"; alpha sorts before zeta
        self.assertEqual([e["text"] for e in repo.events()], ["first", "tie", "second"])

    def test_duplicates_are_dropped(self):
        repo = self.repo()
        repo.set_machine("a")
        repo.append("note", when=at("2026-03-02T09:00:00+05:30"), text="one")
        repo.append("boss", key="cf-milestone:x", when=at("2026-03-02T09:01:00+05:30"), skill="x", ok=True)
        repo.append("boss", key="cf-milestone:x", when=at("2026-03-02T09:02:00+05:30"), skill="x", ok=True)
        path = os.path.join(repo.events_dir, "2026-03.a.jsonl")
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        write(path, text + text)  # what a careless merge could leave behind
        repo.invalidate()
        events = repo.events()
        self.assertEqual([e["t"] for e in events], ["note", "boss"])
        self.assertEqual(repo.event_errors, [])

    def test_bad_lines_are_reported_not_fatal(self):
        repo = self.repo()
        repo.set_machine("a")
        repo.append("note", when=at("2026-03-02T09:00:00+05:30"), text="good")
        path = os.path.join(repo.events_dir, "2026-03.a.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("<<<<<<< HEAD\n{not json}\n{\"id\": \"q\", \"t\": \"note\"}\n>>>>>>> other\n")
        repo.invalidate()
        self.assertEqual(len(repo.events()), 1)
        self.assertEqual(len(repo.event_errors), 4)
        self.assertTrue(any("conflict marker" in e for e in repo.event_errors))

    def test_missing_trailing_newline_is_repaired(self):
        repo = self.repo()
        repo.set_machine("a")
        repo.append("note", when=at("2026-03-02T09:00:00+05:30"), text="one")
        path = os.path.join(repo.events_dir, "2026-03.a.jsonl")
        with open(path, "rb") as fh:
            raw = fh.read()
        with open(path, "wb") as fh:
            fh.write(raw.rstrip(b"\n"))
        repo.append("note", when=at("2026-03-02T09:05:00+05:30"), text="two")
        self.assertEqual([e["text"] for e in repo.events()], ["one", "two"])

    def test_machine_id(self):
        repo = self.repo()
        first = repo.machine()
        self.assertEqual(Repo(self.sb.root).machine(), first)
        self.assertRegex(first, r"^[a-z0-9][a-z0-9-]{0,31}$")
        self.assertEqual(repo.set_machine("My Laptop!"), "my-laptop")


class Profile(Case):
    def test_set_get_unset(self):
        sb = self.sb
        self.assertIn("No profile yet", sb.run("profile", "show"))
        sb.run("profile", "set", "name", "Asha Rao")
        sb.run("profile", "set", "tracks", "10x,cp")
        sb.run("profile", "set", "goals", "capstone")
        sb.run("profile", "set", "sleep.start", "01:30")
        sb.run("profile", "set", "daily.target_hours", "12")
        sb.run("profile", "set", "teach.style", "examples first, then theory: keep it short", "--text")
        repo = Repo(sb.root)
        self.assertEqual(repo.prof("name"), "Asha Rao")
        self.assertEqual(repo.prof("tracks"), ["10x", "cp"])
        self.assertEqual(repo.prof("goals"), ["capstone"])  # list keys are always lists
        self.assertEqual(repo.prof("sleep.start"), "01:30")
        self.assertEqual(repo.prof("daily.target_hours"), 12)
        self.assertEqual(repo.prof("teach.style"), "examples first, then theory: keep it short")
        self.assertEqual(sb.run("profile", "get", "sleep.start").strip(), '"01:30"')
        sb.run("profile", "unset", "sleep.start")
        self.assertIsNone(Repo(sb.root).prof("sleep.start"))
        self.assertFalse(Repo(sb.root).onboarded())
        sb.run("profile", "set", "onboarded", "true")
        self.assertTrue(Repo(sb.root).onboarded())

    def test_notes_below_the_keys_survive(self):
        sb = self.sb
        sb.run("profile", "set", "name", "A")
        path = sb.path("learner", "profile.md")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\nLearns best from failing tests.\n")
        sb.run("profile", "set", "mode.default", "brushup")
        with open(path, "r", encoding="utf-8") as fh:
            self.assertIn("Learns best from failing tests.", fh.read())

    def test_config_override(self):
        sb = self.sb
        self.assertEqual(Repo(sb.root).cfg("new_per_day"), 0)
        sb.run("profile", "set", "cfg.new_per_day", "3")
        sb.run("profile", "set", "cfg.gate.daily_hours", "7.5")
        repo = Repo(sb.root)
        self.assertEqual(repo.cfg("new_per_day"), 3)
        self.assertEqual(repo.cfg("gate.daily_hours"), 7.5)
        self.assertEqual(repo.cfg("no.such.key", "fallback"), "fallback")

    def test_bad_key(self):
        self.sb.run("profile", "set", "bad key", "x", expect=2)


class TimeHelpers(unittest.TestCase):
    def test_learner_day_rolls_over_at_four(self):
        self.assertEqual(daykey(at("2026-03-03T03:59:00+05:30")), "2026-03-02")
        self.assertEqual(daykey(at("2026-03-03T04:00:00+05:30")), "2026-03-03")
        start, end = day_bounds(at("2026-03-03T01:00:00+05:30"))
        self.assertEqual(start.isoformat(), "2026-03-02T04:00:00+05:30")
        self.assertEqual(end.isoformat(), "2026-03-03T04:00:00+05:30")

    def test_windows_that_wrap_midnight(self):
        start, end = parse_hhmm("23:30"), parse_hhmm("07:00")
        self.assertTrue(in_window(parse_hhmm("23:45"), start, end))
        self.assertTrue(in_window(parse_hhmm("03:00"), start, end))
        self.assertFalse(in_window(parse_hhmm("07:00"), start, end))
        self.assertFalse(in_window(parse_hhmm("12:00"), start, end))
        self.assertEqual(minutes_until(parse_hhmm("23:00"), start), 30)
        self.assertEqual(minutes_until(parse_hhmm("23:45"), start), 1425)
        self.assertIsNone(parse_hhmm("25:00"))
        self.assertIsNone(parse_hhmm("soon"))

    def test_parse_ts(self):
        self.assertEqual(parse_ts("2026-03-02T09:00:00Z").utcoffset().total_seconds(), 0)
        self.assertEqual(parse_ts("2026-03-02T09:00:00+05:30").utcoffset().total_seconds(), 19800)
        self.assertIsNotNone(parse_ts("2026-03-02").tzinfo)
        with self.assertRaises(ValueError):
            parse_ts("yesterday")

    def test_formatting(self):
        a, b = at("2026-03-02T09:00:00+05:30"), at("2026-03-05T09:00:00+05:30")
        self.assertEqual(fmt_delta(b - a), "in 3d")
        self.assertEqual(fmt_delta(a - b), "3d ago")
        self.assertEqual(fmt_delta(a - a), "now")
        text = table([["a", 1], ["bbb", 22]], ["name", "n"], aligns="lr")
        self.assertEqual(text.split("\n"), ["name   n", "----  --", "a      1", "bbb   22"])

    def test_cal_error_is_an_exception(self):
        self.assertTrue(issubclass(CalError, Exception))


if __name__ == "__main__":
    unittest.main()
