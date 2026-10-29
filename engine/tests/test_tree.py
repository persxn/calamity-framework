import os
import unittest

from tests.helpers import REPO, Case, Sandbox, write

from cal import fm, tree as tree_mod
from cal.store import Repo
from cal.tree import Tree
from cal.util import CalError


class MiniTree(Case):
    def test_loads_and_validates(self):
        tree = self.sb.tree()
        errors, warnings = tree.check()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(tree.get("docker").prereqs, ["shell"])
        self.assertEqual([t.id for t in tree.get("docker").topics], ["images", "dockerfile", "multi-stage"])
        self.assertEqual(tree.topic("docker/multi-stage").needs, ["dockerfile"])
        self.assertEqual(tree.topic("docker/multi-stage").level, 3)
        self.assertTrue(tree.get("docker").has_boss)
        self.assertFalse(tree.get("java").has_boss)
        self.assertEqual(tree.get("capstone").kind, "milestone")

    def test_order_follows_tracks_and_groups(self):
        tree = self.sb.tree()
        ids = [n.id for n in tree.ordered() if n.track == "dev"]
        self.assertEqual(ids, ["shell", "docker", "java", "python", "api", "capstone"])
        self.assertEqual(tree.groups("dev"), ["base", "build", "milestones"])
        self.assertEqual(tree.track_title("dev"), "Developer")

    def test_slots(self):
        tree = self.sb.tree()
        self.assertEqual([n.id for n in tree.slot_members("language")], ["java", "python"])
        self.assertEqual(tree.requirement_groups(tree.get("api")), [("slot:language", ["java", "python"])])
        self.assertEqual({n.id for n in tree.dependents("java")}, {"api"})
        self.assertEqual({n.id for n in tree.dependents("shell")}, {"docker"})

    def test_routes(self):
        tree = self.sb.tree()
        self.assertEqual(tree.ancestors("capstone"), ["shell", "docker", "java", "api"])
        self.assertEqual(tree.layers("capstone"), [["shell", "java"], ["docker", "api"], ["capstone"]])
        pick_python = lambda alts: "python" if "python" in alts else alts[0]  # noqa: E731
        self.assertEqual(tree.layers("capstone", choose=pick_python)[0], ["shell", "python"])
        skip = lambda nid: nid in ("shell", "java")  # noqa: E731
        self.assertEqual(tree.layers("capstone", skip=skip), [["docker", "api"], ["capstone"]])

    def test_find_uses_aliases(self):
        tree = self.sb.tree()
        self.assertEqual(tree.find("containers")[0].id, "docker")
        self.assertEqual(tree.find("terminal")[0].id, "shell")
        self.assertEqual(tree.find("nothing like this"), [])
        with self.assertRaises(CalError) as ctx:
            tree.get("dokcer")
        self.assertIn("unknown skill", str(ctx.exception))
        with self.assertRaises(CalError):
            tree.topic("docker/nope")

    def test_equivalent_topics_are_symmetric(self):
        tree = self.sb.tree()
        self.assertEqual(tree.equivalents("gate.cs.la/matrices"), ["gate.da.la/matrices"])
        self.assertEqual(tree.equivalents("gate.da.la/matrices"), ["gate.cs.la/matrices"])
        self.assertEqual(tree.equivalents("gate.cs.la/eigen"), [])

    def test_problems_are_reported(self):
        fw = self.sb.path("framework", "tree", "dev")
        write(os.path.join(fw, "a.md"), "---\nid: a\ntitle: A\ntrack: dev\nprereqs: [b, ghost, \"slot:none\"]\n---\n"
              "# Topics\n\n## one | One\nneeds: [two]\n\n## two | Two\nneeds: [one]\n\n## one | Again\n\n## Bad Id | x\n")
        write(os.path.join(fw, "b.md"), "---\nid: b\ntitle: B\ntrack: dev\nprereqs: [a]\n---\n")
        write(os.path.join(fw, "c.md"), "---\ntitle: no id\n---\n")
        errors, _ = self.sb.tree().check()
        text = "\n".join(errors)
        for needle in ("unknown prerequisite 'ghost'", "has no skills in that slot", "prerequisites form a cycle",
                       "topics form a cycle", "duplicate topic id 'one'", "bad topic id", "missing 'id'"):
            self.assertIn(needle, text)
        self.sb.run("tree", "check", expect=2)


class LearnerChanges(Case):
    def test_syllabus_replaces_shipped_topics(self):
        sb = self.sb
        write(sb.path("learner", "syllabus", "python.md"),
              "---\nskill: python\n---\n\n# Topics\n\n## types | Types\nlevel: 1\n- name the built-in types\n\n"
              "## functions | Functions\nneeds: [types]\nlevel: 2\n- write a function\n")
        node = sb.tree().get("python")
        self.assertEqual([t.id for t in node.topics], ["types", "functions"])
        self.assertEqual(node.topics_origin, "learner")
        self.assertIn("ok: python has 2 topics (your syllabus)", sb.run("syllabus", "check", "python"))
        write(sb.path("learner", "syllabus", "java.md"), "---\nskill: java\n---\n\n# Topics\n\n## generics | Generics\n")
        self.assertEqual([t.id for t in sb.tree().get("java").topics], ["generics"])

    def test_syllabus_check_reports_errors(self):
        sb = self.sb
        self.assertIn("no topics found", sb.run("syllabus", "check", "python", expect=2))
        write(sb.path("learner", "syllabus", "python.md"),
              "---\nskill: python\n---\n\n# Topics\n\n## a | A\nneeds: [missing]\n")
        self.assertIn("needs unknown topic 'missing'", sb.run("syllabus", "check", "python", expect=2))
        self.assertIn("learner/syllabus/python.md", sb.run("syllabus", "template", "python"))

    def test_add_set_drop_restore(self):
        sb = self.sb
        out = sb.run("tree", "add", "--id", "htmx", "--title", "htmx", "--track", "dev", "--group", "build",
                     "--prereqs", "shell,slot:language", "--tags", "frontend", "--hours", "15",
                     "--summary", "Server-rendered interactivity.", "--scope", "- attributes\n- swaps")
        self.assertIn("added: htmx", out)
        path = sb.path("learner", "tree", "htmx.md")
        self.assertTrue(os.path.isfile(path))
        node = sb.tree().get("htmx")
        self.assertEqual(node.origin, "learner")
        self.assertEqual(node.prereqs, ["shell", "slot:language"])
        self.assertEqual(node.est_hours, 15)
        self.assertIn("- attributes", node.section("Scope"))

        sb.run("tree", "add", "--id", "htmx", "--title", "again", expect=2)
        sb.run("tree", "add", "--id", "Bad Id", "--title", "x", expect=2)
        self.assertIn("unknown prerequisite", sb.run("tree", "add", "--id", "x1", "--title", "x", "--prereqs", "ghost",
                                                     expect=None) + sb.err)
        self.assertFalse(os.path.exists(sb.path("learner", "tree", "x1.md")))

        # a shipped skill is overridden in learner/tree, never edited in framework/
        shipped = sb.path("framework", "tree", "dev", "docker.md")
        with open(shipped, "r", encoding="utf-8") as fh:
            before = fh.read()
        sb.run("tree", "set", "docker", "--prereqs", "shell,java", "--hours", "30")
        with open(shipped, "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)
        node = sb.tree().get("docker")
        self.assertEqual((node.origin, node.prereqs, node.est_hours), ("learner", ["shell", "java"], 30))
        self.assertEqual(len(node.topics), 3)  # the copy keeps the topics

        # a change that would create a cycle is refused and rolled back
        self.assertIn("cycle", sb.run("tree", "set", "shell", "--prereqs", "docker", expect=None) + sb.err)
        self.assertEqual(sb.tree().get("shell").prereqs, [])

        # dropping a prerequisite needs confirmation, then counts as met
        refusal = sb.run("tree", "drop", "shell", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("is a prerequisite of: docker", refusal)
        sb.run("tree", "drop", "shell", "--yes")
        tree = sb.tree()
        self.assertTrue(tree.get("shell").dropped)
        self.assertNotIn("shell", [n.id for n in tree.live()])
        _, warnings = tree.check()
        self.assertTrue(any("is dropped" in w for w in warnings))
        sb.run("tree", "restore", "shell")
        self.assertFalse(sb.tree().get("shell").dropped)
        sb.run("tree", "restore", "shell", expect=2)

        # a learner's own skill can be dropped and restored too
        sb.run("tree", "drop", "htmx")
        self.assertTrue(sb.tree().get("htmx").dropped)
        sb.run("tree", "restore", "htmx")
        self.assertFalse(sb.tree().get("htmx").dropped)

    def test_views_do_not_crash(self):
        sb = self.sb
        sb.onboard(tracks="dev", goals="capstone")
        for args in (("tree", "list"), ("tree", "list", "--track", "dev", "--ascii"), ("tree", "show", "docker"),
                     ("tree", "show", "python"), ("tree", "path", "capstone"), ("tree", "suggest"),
                     ("find", "bash"), ("find", "multi stage"), ("find", "zzz")):
            self.assertTrue(sb.run(*args).strip())
        route = sb.run("tree", "path", "capstone", "--ascii")
        self.assertIn("layer 1", route)
        self.assertIn("language: java (or python)", route)
        self.assertIn("shell", sb.run("tree", "suggest"))


class ShippedTree(unittest.TestCase):
    """Integrity of the tree that ships with the framework."""

    @classmethod
    def setUpClass(cls):
        # The shipped files only, through an empty learner folder: what a learner adds, changes or
        # drops in their own tree must not decide whether the framework's self-test passes.
        cls.sb = Sandbox(mini=False)
        cls.repo = Repo(cls.sb.root)
        cls.tree = Tree(cls.repo)

    @classmethod
    def tearDownClass(cls):
        cls.sb.close()

    def test_no_errors_or_warnings(self):
        errors, warnings = self.tree.check()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_tracks_and_groups_are_declared(self):
        self.assertEqual(self.tree.tracks, ["10x", "ai", "sec", "cp", "gate", "gate-cs", "gate-da"])
        for node in self.tree.nodes.values():
            declared = self.tree.track_meta.get(node.track + ".groups")
            self.assertIn(node.group, declared, "%s: group %r is not listed in tracks.md" % (node.id, node.group))
            self.assertTrue(node.summary, node.id)
            self.assertEqual(os.path.basename(node.path), node.id + ".md")

    def test_every_requested_skill_is_present(self):
        wanted = """networking git-gh html-css javascript typescript npm-bundlers eslint-prettier react vue svelte
            tailwind framer-motion gsap redux tanstack-query jest cypress playwright node express fastify nextjs nestjs
            trpc python fastapi postgresql mongodb prisma redis jwt oauth2 graphql websockets openapi docker kubernetes
            github-actions jenkins terraform prometheus-grafana java spring-boot rest-api-design kotlin android-core
            flutter classical-ml deep-learning llm-basics langchain ollama rag-qdrant rag-vectorless cp.cpp cp.stl
            cp.dp-basics ten-x mern-stack android-app""".split()
        for ident in wanted:
            self.assertIn(ident, self.tree.nodes)

    def test_slots_have_the_documented_members(self):
        members = lambda slot: {n.id for n in self.tree.slot_members(slot)}  # noqa: E731
        self.assertEqual(members("frontend-framework"), {"react", "vue", "svelte"})
        self.assertEqual(members("animation"), {"framer-motion", "gsap"})
        self.assertEqual(members("e2e-testing"), {"playwright", "cypress"})
        self.assertEqual(members("ci"), {"github-actions", "jenkins"})
        self.assertEqual(members("android-app"), {"android-release", "flutter-release"})
        self.assertEqual(members("rag"), {"rag-qdrant", "rag-vectorless"})
        self.assertTrue({"express", "fastify", "nestjs", "fastapi", "spring-boot"} <= members("backend-framework"))

    def test_developer_skills_have_scope_and_boss(self):
        for node in self.tree.nodes.values():
            if node.track in ("10x", "ai", "sec"):
                self.assertTrue(node.has_boss, "%s has no boss" % node.id)
                if node.kind == "skill":
                    self.assertTrue(node.section("Scope"), "%s has no scope" % node.id)
                    self.assertGreater(node.est_hours, 0, node.id)

    def test_the_10x_route_covers_the_requested_stack(self):
        route = set(self.tree.ancestors("ten-x"))
        for ident in ("networking", "git-gh", "typescript", "eslint-prettier", "tailwind", "redux", "tanstack-query",
                      "jest", "express", "fastify", "nextjs", "nestjs", "trpc", "fastapi", "postgresql", "mongodb",
                      "prisma", "redis", "jwt", "oauth2", "graphql", "websockets", "openapi", "docker", "kubernetes",
                      "terraform", "prometheus-grafana", "rest-api-design"):
            self.assertIn(ident, route)

    def test_docker_weaves_into_java(self):
        docker, java = self.tree.get("docker"), self.tree.get("java")
        accept = set(java.tags) | {java.id, java.group, java.track, "any"}
        self.assertTrue(set(docker.weaves_into) & accept)

    def test_competitive_programming_track(self):
        cp = [n for n in self.tree.nodes.values() if n.track == "cp"]
        skills = [n for n in cp if n.kind == "skill"]
        self.assertGreaterEqual(len(skills), 25)
        for node in skills:
            self.assertTrue(node.topics, "%s ships no topics" % node.id)
            self.assertGreaterEqual(node.band, 800, node.id)
            self.assertTrue(node.has_boss, node.id)
        tagged = [n for n in skills if n.cf_tags]
        self.assertGreaterEqual(len(tagged), 20)
        known = {"implementation", "math", "greedy", "dp", "data structures", "brute force", "constructive algorithms",
                 "graphs", "sortings", "binary search", "dfs and similar", "trees", "strings", "number theory",
                 "combinatorics", "two pointers", "bitmasks", "geometry", "dsu", "shortest paths", "probabilities",
                 "divide and conquer", "hashing", "games", "interactive", "matrices", "string suffix structures", "fft",
                 "graph matchings", "ternary search", "meet-in-the-middle", "2-sat", "flows",
                 "chinese remainder theorem", "expression parsing", "schedules"}
        for node in tagged:
            self.assertTrue(set(node.cf_tags) <= known, "%s: unknown Codeforces tag in %s" % (node.id, node.cf_tags))
        ratings = sorted(int(n.meta["rating"]) for n in cp if n.kind == "milestone")
        self.assertEqual(ratings, [1200, 1400, 1600, 1800, 1900, 2100, 2200])

    def test_gate_tracks(self):
        marks = {}
        for node in self.tree.nodes.values():
            if node.track.startswith("gate"):
                self.assertTrue(node.topics, node.id)
                self.assertIn(node.meta.get("marks_source"), ("prior", "official"))
                self.assertTrue(str(node.meta.get("source_url", "")).startswith("https://"), node.id)
                self.assertFalse(node.prereqs, "%s: GATE subjects have no prerequisite gates" % node.id)
                marks[node.track] = marks.get(node.track, 0) + float(node.marks)
                if node.track != "gate":
                    self.assertIn(node.paper, ("CS", "DA"))
        self.assertEqual(marks["gate"], 15)       # General Aptitude: official
        self.assertEqual(marks["gate-cs"], 85)    # 13 Engineering Mathematics + 72 subject marks
        self.assertEqual(marks["gate-da"], 85)
        self.assertEqual(self.tree.get("gate.general-aptitude").meta["marks_source"], "official")
        shared = [t for n in self.tree.nodes.values() if n.track == "gate-cs" for t in n.topics if t.same_as]
        self.assertGreaterEqual(len(shared), 25)
        for topic in shared:
            for other in topic.same_as:
                self.assertTrue(self.tree.has_topic(other), "%s -> %s" % (topic.key, other))
                self.assertIn(topic.key, self.tree.equivalents(other))

    def test_topic_counts(self):
        count = lambda track: sum(len(n.topics) for n in self.tree.nodes.values() if n.track == track)  # noqa: E731
        self.assertEqual(count("gate"), 16)
        self.assertGreaterEqual(count("gate-cs"), 110)
        self.assertGreaterEqual(count("gate-da"), 85)
        self.assertGreaterEqual(count("cp"), 180)

    def test_shipped_files_parse_with_the_strict_parser(self):
        base = os.path.join(REPO, "framework")
        seen = 0
        for folder, _, files in os.walk(base):
            for name in files:
                if name.endswith(".md"):
                    fm.load(os.path.join(folder, name))
                    seen += 1
        self.assertGreater(seen, 150)

    def test_editing_helpers_reject_unknown_skill(self):
        with self.assertRaises(CalError):
            tree_mod.set_node(self.repo, "no-such-skill", {"title": "x"})


if __name__ == "__main__":
    unittest.main()


BANDED_DP = """---
id: cp.dp
title: Dynamic programming
track: cp
group: core
tags: [cp]
weaves_into: [cp]
cf_tags: [dp]
band: 1200
est_hours: 30
order: 20
summary: DP.
---

# Boss

A timed set of DP problems.

Passes when:

- four of five are accepted

# Topics

## knapsack | Knapsack
level: 3
- 0/1 knapsack

## lis | Longest increasing subsequence
level: 3
- LIS in n log n

## sos | Sum over subsets
level: 5
band: 1700
- SOS DP

## on-a-search | DP after a binary search
needs: [cp.bs/on-answer]
level: 3
- a DP whose state is found by searching the answer
"""


class RatingBands(Case):
    """A topic banded well above a linked learner's rating waits; topics can wait for another skill's topic."""

    def setUp(self):
        super().setUp()
        write(self.sb.path("learner", "tree", "cp.dp.md"), BANDED_DP)
        self.sb.onboard()
        self.sb.legacy_pace()

    def new_topics(self):
        from cal import plan
        from cal.util import parse_ts

        sb = self.sb
        state = sb.state()
        return [row["key"] for row in plan.new_candidates(state.repo, state.tree, state, parse_ts(sb.now()), skill="cp.dp")]

    def test_without_a_handle_nothing_waits_for_a_rating(self):
        self.sb.run("enroll", "cp.dp", "--force")
        self.assertIn("cp.dp/sos", self.new_topics())

    def test_a_banded_topic_waits_and_the_boss_does_not_wait_for_it(self):
        sb = self.sb
        sb.run("profile", "set", "cp.handle", "tester")
        sb.run("enroll", "cp.dp", "--force")
        self.assertNotIn("cp.dp/sos", self.new_topics())                  # 1700 > 0 + 200
        self.assertTrue(sb.state().deferred(sb.tree().topic("cp.dp/sos")))
        sb.run("placement", "cp.dp", "--known", "knapsack,lis,on-a-search")
        self.assertIn("NEXT: boss", sb.run("next"))                        # sos is not waited for
        sb.run("boss", "record", "cp.rating-1200", "pass", "--evidence", "rating history shows 1250")
        sb.run("boss", "record", "cp.rating-1400", "pass", "--evidence", "rating history shows 1450")
        self.assertEqual(sb.state().cp_level(), 1400)
        self.assertNotIn("cp.dp/sos", self.new_topics())                  # 1700 > 1400 + 200
        sb.run("profile", "set", "cfg.cp.band_lookahead", "300")
        self.assertIn("cp.dp/sos", self.new_topics())                     # 1700 <= 1400 + 300
        self.assertNotIn("NEXT: boss", sb.run("next"))                     # now the boss waits for it too
        out = sb.run("ask", "--topic", "cp.dp/sos", expect=4)             # asking for it by name always works
        self.assertTrue(out.startswith("NEED_ITEM"))

    def test_a_topic_waits_for_the_topic_of_another_skill_it_needs(self):
        sb = self.sb
        sb.run("enroll", "cp.dp", "--force")
        self.assertNotIn("cp.dp/on-a-search", self.new_topics())
        sb.item("cp.bs/on-answer")
        sb.do("cp.bs/on-answer")
        self.assertIn("cp.dp/on-a-search", self.new_topics())

    def test_an_unknown_topic_of_another_skill_is_an_error(self):
        write(self.sb.path("learner", "tree", "cp.dp.md"), BANDED_DP.replace("cp.bs/on-answer", "cp.bs/nope"))
        self.assertIn("needs unknown topic 'cp.bs/nope'", self.sb.run("tree", "check", expect=2) + self.sb.err)


class ShippedCompetitiveProgramming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = Tree(Repo(REPO))

    def test_a_tag_goes_to_the_skill_that_teaches_it_at_this_rating(self):
        from cal import cf

        self.assertEqual(cf.tag_skills(self.tree, 1000)["data structures"], "cp.stl")
        self.assertEqual(cf.tag_skills(self.tree, 1500)["data structures"], "cp.range-queries")
        self.assertEqual(cf.tag_skills(self.tree, 1200)["graphs"], "cp.graphs-basics")
        self.assertEqual(cf.tag_skills(self.tree, 1700)["graphs"], "cp.graphs-advanced")

    def test_prerequisites_are_only_what_the_topics_use(self):
        get = self.tree.get
        self.assertNotIn("cp.sorting-greedy", get("cp.binary-search").prereqs)
        self.assertIn("cp.sorting-greedy/sort-then-scan", get("cp.binary-search").topic("predicate-design").needs)
        self.assertNotIn("cp.trees", get("cp.dp-advanced").prereqs)
        self.assertEqual(get("cp.dp-advanced").topic("tree-dp").needs, ["cp.trees/subtree-dp"])
        self.assertNotIn("cp.dp-advanced", get("cp.advanced-techniques").prereqs)
        for node in self.tree.nodes.values():
            for topic in node.topics:
                for need in topic.needs:
                    if "/" in need:
                        self.assertTrue(self.tree.has_topic(need), "%s needs %s" % (topic.key, need))

    def test_rare_tags_are_optional_and_off_the_milestone_routes(self):
        for ident in ("cp.game-theory", "cp.geometry"):
            self.assertTrue(self.tree.get(ident).optional)
            self.assertNotIn(ident, self.tree.ancestors("cp.rating-2200"))

    def test_every_language_member_can_meet_a_language_prerequisite(self):
        self.assertEqual(self.tree.get("dart").slot, "language")
