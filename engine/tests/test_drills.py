"""Developer drills (WP-21): one of each type verified by the checker, and each opening only when it should."""
import json
import re

from tests.helpers import Case, write

COMMIT = "3f9c2e1a7b"


def drill(sb, kind, topic, by="drill-smith", **fields):
    data = {"type": kind, "topics": [topic], "difficulty": 2,
            "stem": "Drill %s on %s: make the tests pass / answer the question." % (kind, topic),
            "solution": "The seeded cause is an off-by-one in the loop bound; the fix is < instead of <=."}
    data.update(fields)
    path = sb.path(".calamity", "tmp", "drill-smith", "b1", "%s.json" % kind)
    write(path, json.dumps(data))
    out = sb.run("item", "draft", "--file", path, "--by", by)
    return re.search(r"it-[a-z0-9]{10}", out).group(0)


FIXTURE = {"fixture": "off-by-one", "bounds": ["src/range.sh"], "check": "./run-tests.sh  # exit 0 when every test passes"}


class Drills(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "shell")
        sb.run("enroll", "docker", "--force")

    def verify_fixed(self, ident):
        sb = self.sb
        out = sb.run("item", "verify", ident, "--ran", "--evidence", "after: 9 passed", "--by", "checker", expect=2)
        self.assertIn("--unfixed-fails", sb.err)
        self.assertEqual(out, "")
        self.assertIn("verified", sb.run("item", "verify", ident, "--ran", "--unfixed-fails", "--evidence",
                                         "before: 2 of 9 failed; after: 9 passed; fix in src/range.sh", "--by", "checker"))

    def test_the_checker_verifies_one_drill_of_each_type(self):
        sb = self.sb
        debug = drill(sb, "debug", "shell/pipes", **FIXTURE)
        docs = drill(sb, "debug-docs", "docker/images", docs="https://docs.docker.com/build/cache/", **FIXTURE)
        read = drill(sb, "read", "docker/dockerfile", repo="https://github.com/moby/buildkit", commit=COMMIT,
                     answer=["frontend/dockerfile/dockerfile2llb/convert.go:Dockerfile2LLB"],
                     solution="The conversion from the parsed Dockerfile to LLB starts in Dockerfile2LLB.")
        audit = drill(sb, "audit", "docker/dockerfile", flaws=3,
                      rubric=["names each seeded flaw", "says why each is wrong and what is right"])
        chaos = drill(sb, "chaos", "docker/dockerfile", project="learner/projects/notes-api",
                      check="docker compose up; kill the db container; the API must answer 503 and recover")
        for ident in (debug, docs, chaos):
            self.verify_fixed(ident)
        sb.run("item", "verify", read, "--answer", "./frontend\\dockerfile\\dockerfile2llb\\convert.go : Dockerfile2LLB()",
               "--by", "checker")
        sb.run("item", "verify", audit, "--ran", "--evidence", "found the 3 flaws against the rubric", "--by", "checker")
        state = sb.state()
        for ident in (debug, docs, read, audit, chaos):
            self.assertEqual(state.items[ident].status, "verified", ident)
        shown = sb.run("item", "show", docs)
        self.assertIn("fixture: learner/work/docker/drills/off-by-one/", shown)
        self.assertIn("change only: src/range.sh", shown)
        self.assertIn("https://docs.docker.com/build/cache/", shown)
        self.assertNotIn("off-by-one in the loop", shown)                       # the cause stays sealed
        self.assertIn("at commit %s" % COMMIT, sb.run("item", "show", read))

    def test_authors_cannot_verify_and_bad_drills_are_refused(self):
        sb = self.sb
        ident = drill(sb, "debug", "shell/pipes", **FIXTURE)
        sb.run("item", "verify", ident, "--ran", "--unfixed-fails", "--evidence", "x", "--by", "drill-smith", expect=2)
        path = sb.path(".calamity", "tmp", "bad.json")
        for kind, fields in (("debug", {"fixture": "f", "bounds": ["tests/test_x.sh"], "check": "./t.sh  # passes"}),
                             ("debug-docs", dict(FIXTURE)),
                             ("read", {"repo": "https://github.com/x/y", "commit": "main", "answer": "a.go:F"}),
                             ("audit", {"flaws": 2, "rubric": ["a", "b"]}),        # shell/pipes is level 1
                             ("prompt", {"rubric": ["a", "b"]})):                  # not ai-pair-engineering
            data = {"type": kind, "topics": ["shell/pipes"], "stem": "A drill that should be refused.",
                    "solution": "The cause and the fix, sealed away."}
            data.update(fields)
            write(path, json.dumps(data))
            sb.run("item", "draft", "--file", path, "--by", "drill-smith", expect=2)

    def test_drills_open_only_when_they_should(self):
        sb = self.sb
        debug = drill(sb, "debug", "shell/perms", **FIXTURE)
        docs = drill(sb, "debug-docs", "docker/images", docs="https://docs.docker.com/build/cache/", **FIXTURE)
        chaos = drill(sb, "chaos", "docker/dockerfile", project="learner/projects/notes-api",
                      check="kill the db container; the API must answer 503 and recover")
        for ident in (debug, docs, chaos):
            sb.run("item", "verify", ident, "--ran", "--unfixed-fails", "--evidence", "before: fail; after: pass",
                   "--by", "checker")
        sb.run("ask", "--id", debug, expect=2)
        self.assertIn("opens once shell/perms is consolidating", sb.err)
        sb.run("ask", "--id", docs, expect=2)
        self.assertIn("opens once docker is ready", sb.err)
        sb.run("ask", "--id", chaos, expect=2)
        self.assertIn("after a project milestone", sb.err)
        self.assertNotIn(docs, sb.run("ask", "--topic", "docker/images", expect=None))   # never picked either
        # shell/perms consolidates; docker becomes ready (known by placement); a task passes
        sb.item("shell/perms")
        sb.do("shell/perms")
        self.assertIn("ITEM %s" % debug, sb.run("ask", "--id", debug))
        sb.run("placement", "docker", "--result", "known")
        self.assertIn("ITEM %s" % docs, sb.run("ask", "--id", docs))
        task = sb.item("shell/pipes", kind="task")
        sb.run("ask", "--id", task)
        sb.advance(minutes=20)
        sb.run("answer", task, "--result", "pass", "--evidence", "./run-tests.sh exit 0")
        self.assertIn("ITEM %s" % chaos, sb.run("ask", "--id", chaos))


class PromptDrills(Case):
    mini = False

    def test_prompt_drills_belong_to_ai_pair_engineering(self):
        sb = self.sb
        sb.onboard(tracks="10x")
        ident = drill(sb, "prompt", "ai-pair-engineering/spec",
                      rubric=["states constraints and non-goals", "gives acceptance tests and edge cases"],
                      solution="A model specification: goal, constraints, acceptance tests, edge cases, non-goals.")
        sb.run("item", "verify", ident, "--ran", "--evidence", "a reference spec meets both points", "--by", "checker")
        self.assertEqual(sb.state().items[ident].status, "verified")
        self.assertIn("RUBRIC", sb.run("item", "show", ident, "--check"))
