import json
import os
import unittest
from datetime import datetime, timedelta

from tests.helpers import Case, write

NOW = "2026-10-11T10:00:00+05:30"


def ago(days=0, hours=0):
    return int((datetime.fromisoformat(NOW) - timedelta(days=days, hours=hours)).timestamp())


def problem(pid, name, rating, tags):
    digits = "".join(ch for ch in pid if ch.isdigit())
    return {"contestId": int(digits), "index": pid[len(digits):], "name": name, "rating": rating, "tags": tags,
            "type": "PROGRAMMING"}


PROBLEMS = {p["contestId"] * 10 + ord(p["index"][0]): p for p in [
    problem("1500A", "Warm-up", 800, ["implementation"]),
    problem("1501B", "Cut the Rope", 1200, ["binary search", "greedy"]),
    problem("1502C", "Coins Again", 1500, ["dp"]),
    problem("1503D", "Backpack", 1300, ["dp"]),
    problem("1504A", "Old Sum", 1000, ["math"]),
    problem("1505A", "Echo", 900, ["implementation"]),
    problem("1506A", "Grid Walk", 1000, ["implementation"]),
    problem("1507A", "Pairs", 1100, ["implementation", "math"]),
    problem("1508A", "Stairs", 1100, ["implementation"]),
    # never opened by the learner
    problem("1600A", "Fence", 1400, ["binary search"]),
    problem("1601B", "Tiles", 1500, ["dp"]),
    problem("1602C", "Queue", 1300, ["greedy"]),
    problem("1603D", "Too Hard", 1900, ["dp"]),
    problem("1604E", "April Fools", 1400, ["dp", "*special"]),
    problem("1605F", "Bridges", 1600, ["binary search", "dp"]),
    problem("1606A", "Too Easy", 800, ["dp"]),
    problem("1607B", "Unrated", None, ["dp"]),
]}


def by_id(pid):
    return next(p for p in PROBLEMS.values() if "%s%s" % (p["contestId"], p["index"]) == pid)


def sub(n, pid, verdict, when, kind="PRACTICE"):
    p = by_id(pid)
    return {"id": n, "contestId": p["contestId"], "creationTimeSeconds": when, "problem": p,
            "author": {"participantType": kind, "members": [{"handle": "tester"}]}, "verdict": verdict,
            "programmingLanguage": "C++17 (GCC 7-32)"}


def fixtures(rating=1234, changes=True):
    info = {"handle": "tester", "rank": "pupil"}
    if rating:
        info.update(rating=rating, maxRating=1301)
    rating_changes = [
        {"contestId": 1400, "contestName": "Round 900 (Div. 3)", "handle": "tester", "rank": 4000,
         "ratingUpdateTimeSeconds": ago(80), "oldRating": 0, "newRating": 900},
        {"contestId": 1450, "contestName": "Educational Round 150", "handle": "tester", "rank": 3000,
         "ratingUpdateTimeSeconds": ago(50), "oldRating": 900, "newRating": 1150},
        {"contestId": 1480, "contestName": "Round 910 (Div. 2)", "handle": "tester", "rank": 2500,
         "ratingUpdateTimeSeconds": ago(20), "oldRating": 1150, "newRating": 1301},
        {"contestId": 1502, "contestName": "Round 920 (Div. 2)", "handle": "tester", "rank": 5200,
         "ratingUpdateTimeSeconds": ago(5), "oldRating": 1301, "newRating": 1234},
    ] if changes else []
    status = [
        sub(1, "1500A", "OK", ago(20)),
        sub(2, "1504A", "OK", ago(40)),
        sub(3, "1505A", "OK", ago(12)),
        sub(4, "1506A", "OK", ago(11)),
        sub(5, "1507A", "OK", ago(10)),
        sub(6, "1508A", "COMPILATION_ERROR", ago(9, 1)),
        sub(7, "1508A", "OK", ago(9)),
        sub(8, "1502C", "WRONG_ANSWER", ago(5, 2), "CONTESTANT"),
        sub(9, "1502C", "TIME_LIMIT_EXCEEDED", ago(5, 1), "CONTESTANT"),
        sub(10, "1503D", "OK", ago(3)),
        sub(11, "1501B", "WRONG_ANSWER", ago(2, 1)),
        sub(12, "1501B", "OK", ago(2)),
    ]
    stats = [{"contestId": p["contestId"], "index": p["index"], "solvedCount": 1000 + 37 * i}
             for i, p in enumerate(PROBLEMS.values())]
    contests = [
        {"id": 1700, "name": "Codeforces Round 950 (Div. 2)", "type": "CF", "phase": "BEFORE", "durationSeconds": 7200,
         "startTimeSeconds": ago(-2)},
        {"id": 1701, "name": "Educational Codeforces Round 170", "type": "ICPC", "phase": "BEFORE",
         "durationSeconds": 8100, "startTimeSeconds": ago(-6)},
        {"id": 1650, "name": "Codeforces Round 940 (Div. 3)", "type": "ICPC", "phase": "FINISHED",
         "durationSeconds": 8100, "startTimeSeconds": ago(30)},
        {"id": 1651, "name": "Codeforces Round 941 (Div. 1)", "type": "CF", "phase": "FINISHED",
         "durationSeconds": 7200, "startTimeSeconds": ago(31)},
        {"id": 1502, "name": "Round 920 (Div. 2)", "type": "CF", "phase": "FINISHED", "durationSeconds": 7200,
         "startTimeSeconds": ago(5, 3)},
    ]
    return {
        "user.info": [info], "user.rating": rating_changes, "user.status": status,
        "problemset.problems": {"problems": list(PROBLEMS.values()), "problemStatistics": stats},
        "contest.list": contests,
    }


class Codeforces(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.at(NOW)
        sb.onboard(tracks="cp")
        self.fixture_dir = sb.path("fixtures")
        self.install(fixtures())
        sb.env["CALAMITY_CF_FIXTURES"] = self.fixture_dir

    def install(self, data):
        for method, result in data.items():
            write(os.path.join(self.fixture_dir, method + ".json"), json.dumps({"status": "OK", "result": result}))

    def linked(self):
        self.sb.run("cf", "link", "tester")
        return self.sb.run("cf", "sync")

    def test_link_and_sync(self):
        sb = self.sb
        self.assertIn("No Codeforces handle linked", sb.run("cf", "status"))
        sb.run("cf", "sync", expect=2)
        sb.run("cf", "link", "bad handle!", expect=2)
        sb.run("cf", "link", expect=2)
        self.assertIn("linked Codeforces handle tester (rating 1234, max 1301)", sb.run("cf", "link", "tester"))
        self.assertIn("nothing is cached on this machine", sb.run("cf", "status"))
        self.assertIn("not synced on this machine yet", sb.run("brief"))
        sb.run("cf", "analyse", expect=2)
        out = sb.run("cf", "sync")
        self.assertIn("synced tester: rating 1234 (max 1301), 4 rated contests, 12 submissions, 8 problems solved", out)
        self.assertIn("problem set refreshed (17 problems)", out)
        self.assertIn("contest list refreshed", out)
        self.assertIn("milestone reached: cp.rating-1200", out)
        self.assertIn("Codeforces rating 1301 after Round 910 (Div. 2) (contest 1480)", out)
        self.assertNotIn("cp.rating-1400", out)
        state = sb.state()
        self.assertEqual(state.skill_status("cp.rating-1200"), "mastered")
        self.assertFalse(state.skills.get("cp.rating-1400") and state.skills["cp.rating-1400"].boss_ok)
        again = sb.run("cf", "sync")                                       # nothing is recorded or fetched twice
        self.assertNotIn("milestone", again)
        self.assertNotIn("problem set refreshed", again)
        self.assertEqual(sb.state().skills["cp.rating-1200"].boss_tries, 1)
        self.assertIn("problem set refreshed", sb.run("cf", "sync", "--full"))
        self.assertTrue(os.path.isfile(sb.path(".calamity", "cache", "cf", "user-tester.json")))
        status = sb.run("cf", "status")
        self.assertIn("tester: rating 1234 (max 1301) · 8 solved, 2 this week · 4 rated contests", status)
        self.assertIn("Codeforces tester", sb.run("doctor", expect=None))

    def test_api_failure_is_reported(self):
        sb = self.sb
        write(os.path.join(self.fixture_dir, "user.info.json"),
              json.dumps({"status": "FAILED", "comment": "handles: User with handle nobody not found"}))
        out = sb.run("cf", "link", "nobody", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("not found", out)
        os.remove(os.path.join(self.fixture_dir, "user.info.json"))
        sb.run("cf", "link", "tester", expect=2)

    def test_rating_and_target(self):
        sb = self.sb
        self.linked()
        sb.run("profile", "set", "cp.target_rating", "1800")
        sb.run("profile", "set", "cp.target_date", "2027-08-31")
        out = sb.run("cf", "rating")
        self.assertIn("tester: rating 1234, max 1301, 4 rated contests", out)
        self.assertIn("last 30 days: +84 over 2 contest(s)", out)                 # 1150 -> 1234
        self.assertIn("last 90 days: +1234 over 4 contest(s)", out)
        self.assertIn("target 1800: 566 point(s) to go by 2027-08-31, which needs about +53 a month", out)
        self.assertIn("A rating target is a direction, not a promise", out)
        self.assertIn("Fewer than six rated contests", out)
        self.assertIn("next milestone: cp.rating-1400 | Codeforces 1400 (166 to go)", out)
        self.assertIn("target 1800 (566 to go)", sb.run("brief"))
        self.assertIn("next milestone", sb.run("dash", "cp"))
        sb.run("rebuild")
        with open(sb.path("learner", "PROGRESS.md"), "r", encoding="utf-8") as fh:
            self.assertIn("Codeforces handle: tester", fh.read())

    def test_analysis(self):
        sb = self.sb
        self.linked()
        sb.run("cf", "mark", "1503D", "subtag", "--subtags", "dp-knapsack")
        out = sb.run("cf", "analyse")
        self.assertIn("8 solved in all, 8 in the last 180 days · practice level 1140", out)   # mean of the 5 hardest
        self.assertIn("solved: 2 in 7 days, 7 in 30 days", out)
        self.assertIn("800:1  900:1  1000:2  1100:2  1200:1  1300:1", out)
        rows = {line.split("  ")[0].strip(): line for line in out.split("\n")}
        self.assertIn("cp.dp", rows["dp"])                                  # the tree skill that teaches the tag
        self.assertIn("cp.bs", rows["binary search"])
        order = [line.split("  ")[0].strip() for line in out.split("\n")]
        self.assertLess(order.index("dp"), order.index("implementation"))   # the weak tag comes first
        self.assertIn("sub-tags recorded by the coach: dp-knapsack x1", out)

    def test_recommendations(self):
        sb = self.sb
        self.linked()
        out = sb.run("cf", "recommend", "--n", "4")
        self.assertIn("practice set for rating 1234: problems rated 1300-1600", out)
        picked = [line.split()[0] for line in out.split("\n") if line[:4].isdigit()]
        self.assertEqual(set(picked), {"1600A", "1601B", "1602C", "1605F"})  # unsolved, in the band, not special
        self.assertIn("tags are hidden on purpose", out)
        self.assertNotIn("binary search", out)
        self.assertIn("chosen for", sb.run("cf", "recommend", "--show-tags"))

        only_dp = sb.run("cf", "recommend", "--skill", "cp.dp")
        self.assertIn("tags: dp", only_dp)
        self.assertEqual({l.split()[0] for l in only_dp.split("\n") if l[:4].isdigit()}, {"1601B", "1605F"})
        by_tag = sb.run("cf", "recommend", "--tags", "greedy")
        self.assertEqual([l.split()[0] for l in by_tag.split("\n") if l[:4].isdigit()], ["1602C"])
        wide = sb.run("cf", "recommend", "--low", "-500", "--high", "700", "--n", "8")
        self.assertIn("1603D", wide)
        self.assertIn("1606A", wide)
        self.assertNotIn("1604E", wide)                                      # special problems are never suggested
        self.assertNotIn("1607B", wide)                                      # nor unrated ones
        self.assertNotIn("1503D", wide)                                      # nor anything already tried
        self.assertIn("no unsolved problem matches", sb.run("cf", "recommend", "--tags", "fft"))
        sb.run("cf", "recommend", "--skill", "docker", expect=2)             # that skill has no Codeforces tags

        sb.run("cf", "mark", "1600A", "skip", "--note", "seen in class")
        self.assertNotIn("1600A", sb.run("cf", "recommend"))
        self.assertIn("assigned 2 problem(s): 1601B, 1602C", sb.run("cf", "assign", "1601b", "1602C", "--reason", "dp + greedy"))
        self.assertIn("still open from earlier assignments: 1601B, 1602C", sb.run("cf", "recommend"))
        sb.run("cf", "assign", "not-a-problem", expect=2)
        sb.run("cf", "assign", expect=2)
        sb.run("cf", "mark", "1601B", "liked", expect=2)
        sb.run("cf", "mark", "1601B", "subtag", expect=2)

    def test_upsolve_and_contests(self):
        sb = self.sb
        self.linked()
        up = sb.run("cf", "upsolve")
        self.assertIn("attempted but never solved", up)
        self.assertIn("1502C", up)
        self.assertIn("contest", up)
        self.assertNotIn("solve again without the editorial", up)
        sb.run("cf", "mark", "1503D", "editorial")
        up = sb.run("cf", "upsolve")
        self.assertIn("solve again without the editorial", up)
        self.assertIn("1503D  due in 7d", up)
        sb.advance(days=8)
        sb.run("cf", "mark", "1503D", "resolved")
        self.assertNotIn("solve again without the editorial", sb.run("cf", "upsolve"))
        sb.at(NOW)
        contests = sb.run("cf", "contests")
        self.assertIn("upcoming contests (local time)", contests)
        self.assertIn("Codeforces Round 950 (Div. 2)", contests)
        self.assertIn("2h00", contests)
        self.assertIn("virtual contest candidates for rating 1234", contests)
        self.assertIn("1650", contests)                                      # a Div. 3 the handle never opened
        self.assertNotIn("Round 941 (Div. 1)", contests)                     # not the learner's division
        self.assertIn("1301 -> 1234", contests)
        self.assertIn("-67", contests)
        self.assertIn("rated contests: 4 · contests with submissions made as a participant", contests)
        self.assertNotIn("RUNNING NOW", contests)
        # half an hour into round 950: the cache from the last sync still says it has not started
        sb.at("2026-10-13T10:30:00+05:30")
        live = sb.run("cf", "contests")
        self.assertIn("RUNNING NOW", live)
        self.assertIn("1700  Codeforces Round 950 (Div. 2)", live)
        self.assertIn("give no help of any kind", live)
        self.assertIn("ends\n", live)
        self.assertEqual(live.count("Round 950"), 1)                          # listed as running, not as upcoming
        sb.at("2026-10-13T12:30:00+05:30")                                     # over: two hours long
        self.assertNotIn("RUNNING NOW", sb.run("cf", "contests"))

    def test_credit(self):
        sb = self.sb
        self.linked()
        sb.run("enroll", "cp.dp")
        sb.run("enroll", "cp.bs")
        out = sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack")
        self.assertIn("CREDITED 1503D -> cp.dp/knapsack", out)
        self.assertIn("grade: cp.dp/knapsack Good", out)
        ts = sb.state().topics["cp.dp/knapsack"]
        self.assertEqual((ts.n_vok, sorted(ts.ok_items)), (1, ["cf:1503D"]))  # a judged solve is verified evidence
        hard = sb.run("cf", "credit", "1501B", "--topic", "cp.bs/on-answer", "--also", "cp.dp/lis")
        self.assertIn("grade: cp.bs/on-answer Hard", hard)                    # one wrong submission before it
        self.assertIn("also credited: cp.dp/lis Good", hard)
        refused = sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("already credited", refused)
        sb.run("cf", "credit", "1503D", "--topic", "cp.dp/lis")               # another topic of the same problem is fine
        old = sb.run("cf", "credit", "1504A", "--topic", "cp.bs/on-answer", expect=None) + sb.err
        self.assertIn("was solved 40 days ago", old)
        self.assertIn("placement test", old)
        self.assertIn("no accepted submission", sb.run("cf", "credit", "1502C", "--topic", "cp.dp/knapsack",
                                                       expect=None) + sb.err)
        sb.run("cf", "credit", "1503D", "--topic", "docker/images", expect=2)  # not a competitive-programming topic
        sb.run("cf", "credit", "1503D", expect=2)
        events = [e for e in sb.state().repo.events() if e["t"] == "attempt"]
        self.assertTrue(all(e.get("problem") and e.get("verified") for e in events))
        self.assertIn("Codeforces accepted 1501B (Cut the Rope, rated 1200), 1 wrong submission(s)", events[1]["evidence"])

    def test_credit_after_an_editorial(self):
        sb = self.sb
        self.linked()
        sb.run("enroll", "cp.dp")
        sb.run("cf", "mark", "1503D", "editorial")
        out = sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack")
        self.assertIn("not counted as evidence", out)
        self.assertIn("grade: cp.dp/knapsack Hard", out)
        self.assertEqual(sb.state().topics["cp.dp/knapsack"].n_vok, 0)
        self.assertIn("followed the editorial", sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack",
                                                       expect=None) + sb.err)
        sb.advance(days=8)
        sb.run("cf", "mark", "1503D", "resolved")
        clean = sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack")  # the clean re-solve now counts
        self.assertNotIn("not counted as evidence", clean)
        self.assertEqual(sb.state().topics["cp.dp/knapsack"].n_vok, 1)
        sb.run("cf", "credit", "1503D", "--topic", "cp.dp/knapsack", expect=2)

    def test_unrated_newcomer(self):
        sb = self.sb
        self.install(fixtures(rating=None, changes=False))
        out = self.linked()
        self.assertIn("rating unrated", out)
        self.assertNotIn("milestone", out)
        rec = sb.run("cf", "recommend")
        self.assertIn("practice set for rating 940", rec)                    # practice level 1140, less 200
        rating = sb.run("cf", "rating")
        self.assertIn("rating unrated", rating)
        self.assertIn("next milestone: cp.rating-1200", rating)
        self.assertIn("unrated", sb.run("cf", "status"))


if __name__ == "__main__":
    unittest.main()
