"""Integration projects, the frontier and rescue weaving (WP-22), on the shipped developer tree."""
from tests.helpers import Case, write

REACT = """---
skill: react
written: 2026-03-01
sources: [https://react.dev/learn]
---

# Topics

## components | Components and JSX
level: 1
- write a component that renders a list with keys

## state | State and re-rendering
needs: [components]
level: 2
- explain why setting state schedules a re-render
"""
EXPRESS = """---
skill: express
written: 2026-03-01
sources: [https://expressjs.com/en/guide/routing.html]
---

# Topics

## routing | Routing
level: 1
- write a route with a path parameter

## middleware | The middleware chain
needs: [routing]
level: 2
- explain the order middleware runs in and what next() does
"""


class Frontier(Case):
    mini = False

    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(tracks="10x")
        sb.legacy_pace()
        for skill in ("html-css", "javascript", "npm-bundlers", "node", "rest-api-design", "typescript"):
            sb.run("placement", skill, "--result", "known")
        write(sb.path("learner", "syllabus", "react.md"), REACT)
        write(sb.path("learner", "syllabus", "express.md"), EXPRESS)
        for skill in ("react", "express"):
            sb.run("enroll", skill)
        for topic in ("react/components", "react/state", "express/routing", "express/middleware"):
            sb.item(topic)
            sb.item(topic)

    def secure(self, *topics):
        for topic in topics:
            item = self.sb.run("ask", "--topic", topic, "--taught").split("ITEM ", 1)[1].split()[0]
            self.sb.answer(item, "B")

    def test_two_consolidating_skills_yield_one_project_crediting_both(self):
        sb = self.sb
        self.assertIn("No integration project yet", sb.run("project", "suggest"))
        self.secure("react/components", "express/routing")
        out = sb.run("project", "suggest")
        self.assertIn("Express.js + React (mern-stack needs both; 50% and 50% secured)", out)
        self.assertIn("topics: express/routing, react/components", out)
        task = sb.item("react/state", kind="task", also=["express/middleware"],
                       stem="Build a React page that lists the Express API's items and shows its errors.",
                       check="npm test  # passes when both test suites exit 0")
        self.assertIn("ITEM %s" % task, sb.run("ask", "--id", task))
        sb.advance(minutes=30)
        sb.run("answer", task, "--result", "pass", "--evidence", "npm test: 14 passed")
        state = sb.state()
        for key in ("react/state", "express/middleware"):
            self.assertIsNotNone(state.topics[key].card, key)          # one pass credited both skills

    def test_the_frontier_names_next_and_nest_with_reasons(self):
        sb = self.sb
        self.assertIn("No frontier yet", sb.run("tree", "frontier"))
        self.secure("react/components", "react/state", "express/routing", "express/middleware")
        out = sb.run("tree", "frontier", "--n", "4")
        self.assertIn("nextjs | Next.js", out)
        self.assertIn("nestjs | NestJS", out)
        self.assertIn("builds on React (100% secured)", out)
        self.assertIn("builds on Express.js (100% secured); with TypeScript, which you have", out)
        self.assertNotIn("html-css |", out)                           # known by placement, not a frontier


class RescueWeaving(Case):
    def test_the_weakest_recall_is_woven_in_first(self):
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "shell")
        sb.run("enroll", "docker", "--force")
        for topic in ("shell/pipes", "shell/perms", "docker/images"):
            sb.item(topic)
            sb.item(topic)
        sb.do("shell/pipes")
        sb.advance(days=6)
        sb.do("shell/perms")
        sb.advance(days=1)
        out = sb.run("weave", "docker", "--n", "2")
        lines = [l for l in out.split("\n") if l.startswith("  shell/")]
        self.assertTrue(lines[0].startswith("  shell/pipes"), out)  # answered longest ago: weakest recall first
