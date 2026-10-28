"""Mock scouting (WP-15): every opportunity record carries its source, fetch date and terms note."""
import json
import os

from tests.helpers import REPO, Case, read, write

GOOD = {"kind": "gate-mock", "title": "GATE 2027 mock test (CS)", "provider": "organising institute",
        "url": "https://gate2027.example.ac.in/mock", "source": "https://gate2027.example.ac.in/",
        "fetched": "2026-03-01", "terms": "robots.txt allows /; terms silent on automated access", "mode": "online",
        "dates": "opens Jan 2027"}


class Career(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        self.path = self.sb.path(".calamity", "tmp", "scout", "mocks.json")

    def add(self, rows, expect=0):
        write(self.path, json.dumps(rows))
        return self.sb.run("career", "add", "--file", self.path, expect=expect)

    def test_a_record_needs_source_date_and_terms(self):
        sb = self.sb
        for missing in ("source", "fetched", "terms", "url"):
            self.add([dict(GOOD, **{missing: ""})], expect=2)
            self.assertIn("lacks %s" % missing, sb.err)
        self.add([GOOD, dict(GOOD, url="https://x.example/2", mode="offline")], expect=2)   # all or none
        self.assertIn("names its city", sb.err)
        self.assertIn("No records", sb.run("career", "list"))
        self.add([dict(GOOD, fetched="2099-01-01")], expect=2)
        self.add([dict(GOOD, rank=1)], expect=2)
        self.assertIn("unknown field", sb.err)

    def test_records_are_listed_shown_replaced_and_marked_stale(self):
        sb = self.sb
        out = self.add([GOOD, dict(GOOD, title="Series A full test 1", provider="Series A",
                                   url="https://a.example/ft1", mode="offline", city="Kolkata")])
        self.assertIn("recorded 2 record(s)", out)
        listing = sb.run("career", "list", "--kind", "gate-mock")
        self.assertIn("Series A full test 1", listing)
        self.assertIn("Kolkata", listing)
        ident = listing.split("\n")[2].split()[0]
        shown = sb.run("career", "show", ident)
        self.assertIn("terms: ", shown)
        self.assertIn("source: https://", shown)
        self.add([dict(GOOD, fetched="2026-03-02", dates="opens 5 Jan 2027")])          # a newer fetch replaces
        self.assertEqual(len(sb.state().career), 2)
        sb.advance(days=40)
        self.assertIn("(stale)", sb.run("career", "list"))

    def test_the_city_is_a_profile_key_and_the_scout_respects_robots(self):
        sb = self.sb
        sb.run("profile", "set", "location.city", "Kolkata, West Bengal")
        self.assertIn("Kolkata, West Bengal", sb.run("profile", "get", "location.city"))
        sb.run("profile", "set", "location.radius_km", "0", expect=2)
        sb.run("profile", "set", "location.radius_km", "80")
        agent = read(os.path.join(REPO, ".claude", "agents", "opportunity-scout.md"))
        self.assertIn("robots.txt", agent)
        self.assertIn("do not fetch it", agent)
        self.assertIn("omitClaudeMd: true", agent)
        self.assertIn("career list --kind gate-mock", read(os.path.join(REPO, ".claude", "agents", "gate-strategist.md")))

    def test_a_newer_fetch_replaces_the_record_and_keeps_its_status(self):
        sb = self.sb
        self.add([GOOD])
        ident = sb.run("career", "list").split("\n")[2].split()[0]
        sb.run("career", "status", ident, "saved", "--note", "fits the January slot")
        sb.advance(days=1)
        self.add([dict(GOOD, fetched="2026-03-02", dates="opens 5 Jan 2027")])
        shown = sb.run("career", "show", ident)
        self.assertIn("dates: opens 5 Jan 2027", shown)       # the payload id no longer swallows the refresh
        self.assertIn("status: saved", shown)
        self.assertIn("status_note: fits the January slot", shown)


def job(title, must=(), nice=(), **more):
    return dict({"kind": "job", "title": title, "provider": "Example Co", "url": "https://jobs.example/%s" % title,
                 "source": "https://boards.example/example-co", "fetched": "2026-03-01", "via": "greenhouse-api",
                 "terms": "public job board API, documented for applicants", "mode": "remote",
                 "must": list(must), "nice": list(nice)}, **more)


class Readiness(Case):
    """WP-25: readiness reproduces by hand, no nudge in a blackout, the portfolio lists only evidence."""

    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(tracks="dev")
        sb.legacy_pace()
        sb.run("placement", "python", "--result", "known")              # python: 1.0 (known)
        sb.run("boss", "record", "docker", "pass", "--evidence", "multi-stage image for the notes app, 41 MB",
               "--kind", "project")                                     # docker: 1.0, and project evidence
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        sb.item("shell/pipes")
        sb.do("shell/pipes")                                            # shell: (0.4 + 0) / 2 = 0.2
        self.path = sb.path(".calamity", "tmp", "scout", "jobs.json")

    def add(self, rows, expect=0):
        write(self.path, json.dumps(rows))
        return self.sb.run("career", "add", "--file", self.path, expect=expect)

    def ident(self, title):
        return next(r["id"] for r in self.sb.state().career.values() if r["title"] == title)

    def test_readiness_reproduces_by_hand(self):
        sb = self.sb
        self.assertIn(sb.state().topic_status("shell/pipes"), ("learning", "consolidating"))
        self.add([job("a", must=["docker", "python"], nice=["shell"]),     # 0.75 * 1.0 + 0.25 * 0.2 = 0.80
                  job("b", must=["python", "api"]),                        # (1.0 + 0) / 2 = 0.50
                  job("c", must=["python"]),                               # 1.0, but no project on python: 0.60
                  dict(GOOD, title="a mock")])
        out = sb.run("career", "match")
        self.assertIn("readiness 0.80 -> apply now", out)
        self.assertIn("readiness 0.50 -> prepare\n", out)
        self.assertIn("readiness 0.60 -> prepare (capped at 0.6", out)
        self.assertIn("gaps: api · about 15h to close (est. from the tree)", out)
        self.assertIn("nice: shell 0.2", out)
        self.assertNotIn("a mock", out)                                    # names no skills: nothing to match
        self.assertIn("readiness 0.80", sb.run("career", "match", self.ident("a")))
        self.add([job("d", must=["kubernetes"])], expect=2)
        self.assertIn("unknown skill", sb.err)
        self.add([job("e", must=["python"], nice=["python"])], expect=2)
        self.add([job("f", mode="onsite")], expect=2)
        self.assertIn("names its city", sb.err)

    def test_status_steps_and_nudges(self):
        sb = self.sb
        self.add([job("a", must=["docker", "python"], nice=["shell"], deadline="2026-03-10"),
                  job("b", must=["python", "api"]), job("e", must=["docker", "api"])])
        a, b, e = self.ident("a"), self.ident("b"), self.ident("e")
        out = sb.run("career", "nudge")
        self.assertIn("%s deadline" % a, out)                              # closes in 8 days at 0.80 >= 0.7
        self.assertIn("%s boss" % e, out)                                  # docker boss passed this week
        self.assertNotIn(b, out)
        self.assertIn("career", sb.run("tasks"))
        sb.run("career", "status", a, "applied")
        self.assertNotIn(a, sb.run("career", "nudge"))                     # acted on: never nudged again
        sb.run("career", "status", a, "sent", expect=2)
        sb.run("career", "status", "op-nothing", "saved", expect=2)
        status = sb.run("career", "status")
        self.assertIn("applied", status)
        self.assertIn("No blackout.", status)
        sb.run("tasks", "done", "career")
        self.assertNotIn("career ", sb.run("tasks"))
        sb.advance(days=15)                                                # the boss is no longer fresh
        self.assertIn("Nothing to act on", sb.run("career", "nudge"))

    def test_no_nudge_during_a_blackout(self):
        sb = self.sb
        self.add([job("a", must=["docker", "python"], nice=["shell"], deadline="2026-03-10")])
        sb.run("career", "status", self.ident("a"), "saved")
        sb.run("profile", "set", "career.blackout_until", "2026-03-05")
        sb.run("profile", "set", "career.blackout_until", "soon", expect=2)
        self.assertIn("Blackout until 2026-03-05 (career.blackout_until)", sb.run("career", "nudge"))
        self.assertNotIn("career", sb.run("tasks"))
        self.assertIn("hold until 2026-03-05", sb.run("career", "match"))
        sb.advance(days=4)
        self.assertIn("deadline", sb.run("career", "nudge"))               # the blackout is over
        sb.run("profile", "set", "career.blackout_until", "none")
        sb.run("profile", "set", "tracks", "dev,gate-cs")
        sb.run("profile", "set", "gate.papers", "CS")
        sb.run("profile", "set", "gate.exam_date.CS", "2026-03-20")         # 14 days left: GATE's final phase
        self.assertIn("(GATE's final phase)", sb.run("career", "nudge"))
        self.assertNotIn("career", sb.run("tasks"))

    def test_the_portfolio_lists_only_evidence(self):
        sb = self.sb
        sb.run("boss", "record", "api", "fail", "--evidence", "endpoints missing")
        task = sb.item("shell/perms", kind="task", stem="Lock a shared folder down to one group.",
                       check="./check-perms.sh  # passes when it exits 0")
        sb.run("ask", "--id", task)
        sb.advance(minutes=20)
        sb.run("answer", task, "--result", "pass", "--evidence", "check-perms.sh exited 0")
        out = sb.run("career", "portfolio")
        self.assertIn("wrote learner/career/portfolio.md", out.replace(os.sep, "/"))
        text = read(sb.path("learner", "career", "portfolio.md"))
        self.assertIn("**Docker** (project, 2026-03-02): multi-stage image for the notes app, 41 MB", text)
        self.assertIn("**Python** (`python`): placed out by a placement test", text)
        self.assertIn("- shell: 1 passed (task %s)" % task, text)
        self.assertNotIn("API design", text)                               # a failed boss is no evidence
        self.assertNotIn("**Shell", text)                                  # learning is not proven
        self.assertNotIn(job("x")["url"], text)
        for line in text.split("\n"):
            if line.startswith("- "):
                self.assertRegex(line, r"\d{4}-\d{2}-\d{2}|placement test|it-[a-z0-9]{10}", line)
        sb.run("rebuild")
        self.assertEqual(read(sb.path("learner", "career", "portfolio.md")), text)
        self.assertEqual(sb.run("career", "portfolio", "--stdout").rstrip("\n"), text.rstrip("\n"))   # prints, writes nothing new
