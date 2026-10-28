"""Deep coaching on the engine (WP-16): when a unit is done, and the duplicate skill doctor warns about."""
import os

from tests.helpers import Case, write


class Unit(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "docker", "--force")
        self.sb.run("profile", "set", "cfg.pace.mastery.consolidate_minutes", "20")
        for topic in ("docker/images", "docker/dockerfile"):
            self.sb.item(topic)
            self.sb.item(topic)

    def test_a_unit_is_open_until_each_topic_consolidates_and_one_is_explained(self):
        sb = self.sb
        out = sb.run("unit", "docker", "images", "dockerfile")
        self.assertIn("unit of docker: 2 topics", out)
        self.assertRegex(out, r"images\s+new")
        self.assertIn("UNIT OPEN: images, dockerfile not yet consolidating; no explain-back yet", out)
        sb.run("ask", "--topic", "docker/images", "--taught")
        sb.answer(self._open(), "B")
        self.assertRegex(sb.run("unit", "docker", "images"), r"images\s+learning")
        sb.advance(minutes=25)
        sb.do("docker/images")
        self.assertRegex(sb.run("unit", "docker", "docker/images"), r"images\s+consolidating")
        sb.run("observe", "explained a layer as a filesystem diff", "--tag", "explain", "--topic", "docker/images")
        done = sb.run("unit", "docker", "images")
        self.assertIn("explained back", done)
        self.assertIn("UNIT DONE", done)
        self.assertIn("UNIT OPEN: dockerfile not yet consolidating", sb.run("unit", "docker", "images", "dockerfile"))

    def test_unknown_topics_and_skills_are_refused(self):
        self.sb.run("unit", "docker", "volumes", expect=2)
        self.sb.run("unit", "python", expect=2)      # no topics yet
        self.sb.run("unit", "nope", expect=2)

    def _open(self):
        return next(i for i, it in self.sb.state().items.items() if it.open)


class Duplicate(Case):
    def test_doctor_warns_about_an_account_level_mastery_coach(self):
        sb = self.sb
        sb.onboard()
        self.assertNotIn("account-level mastery-coach", sb.run("doctor", expect=None))
        home = sb.env["CLAUDE_CONFIG_DIR"]
        write(os.path.join(home, "skills", "synced", "abc_def", "mastery-coach", "SKILL.md"), "---\nname: x\n---\n")
        out = sb.run("doctor", expect=None)
        self.assertRegex(out, r"WARN\s+account-level mastery-coach\s+.*competes")
