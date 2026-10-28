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
        self.assertIn("names its centre's city", sb.err)
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
