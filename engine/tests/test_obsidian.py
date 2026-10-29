import os
import unittest

from tests.helpers import Case, read, write


class Obsidian(Case):
    def setup_books(self):
        """A learner with one book: README + two chapters, no frontmatter yet."""
        self.sb.onboard(tracks="dev")
        self.sb.run("enroll", "shell")
        base = self.sb.path("learner", "books", "shell")
        write(os.path.join(base, "README.md"), "# Linux & the shell\n\nWhat this book covers.\n")
        write(os.path.join(base, "01-files.md"), "# Files and paths\n\nThe filesystem.\n")
        write(os.path.join(base, "02-pipes.md"), "# Pipes and redirection\n\nConnecting commands.\n")

    def test_disabled_by_default(self):
        self.sb.onboard(tracks="dev")
        from cal import obsidian
        self.assertFalse(obsidian.enabled(self.sb.state().repo))
        # The brief must not write Today.md when the learner has not turned it on.
        self.sb.run("brief", "--hook", stdin="{}")
        self.assertFalse(os.path.isfile(self.sb.path("learner", "Today.md")))

    def test_command_writes_the_dashboard_and_enables_refresh(self):
        self.sb.onboard(tracks="dev")
        out = self.sb.run("obsidian")
        self.assertIn("Today.md", out)
        today = self.sb.path("learner", "Today.md")
        self.assertTrue(os.path.isfile(today))
        text = read(today)
        self.assertIn("# Today —", text)
        self.assertIn("## Finish line", text)
        self.assertIn("## Next action", text)
        # the flag is now on, and the brief refreshes it
        self.assertEqual(self.sb.run("profile", "get", "obsidian").strip(), "true")
        os.remove(today)
        self.sb.run("brief", "--hook", stdin="{}")
        self.assertTrue(os.path.isfile(today), "the session-start hook should rebuild Today.md")

    def test_books_get_moc_index_and_stable_frontmatter(self):
        self.setup_books()
        self.sb.run("obsidian")
        moc = self.sb.path("learner", "books", "shell", "_MOC.md")
        index = self.sb.path("learner", "books", "_Index.md")
        self.assertTrue(os.path.isfile(moc) and os.path.isfile(index))
        moc_text = read(moc)
        self.assertIn("[[01-files|Files and paths]]", moc_text)
        self.assertIn("[[02-pipes|Pipes and redirection]]", moc_text)
        chapter = read(self.sb.path("learner", "books", "shell", "01-files.md"))
        self.assertTrue(chapter.startswith("---"))
        self.assertIn("calamity: book-chapter", chapter)
        self.assertIn("chapter: 1", chapter)
        index_text = read(index)
        self.assertIn("```dataview", index_text)                       # optional nav block, clearly labelled
        self.assertIn("requires the Dataview plugin", index_text)

    def test_refresh_is_a_noop_when_off(self):
        self.sb.onboard(tracks="dev")
        out = self.sb.run("obsidian", "--refresh")
        self.assertIn("off", out)
        self.assertFalse(os.path.isfile(self.sb.path("learner", "Today.md")))
        self.assertEqual(self.sb.run("profile", "get", "obsidian").strip(), "")   # the flag is not turned on

    def test_refresh_renders_when_on(self):
        self.sb.onboard(tracks="dev")
        self.sb.run("obsidian")                       # enable + render
        today = self.sb.path("learner", "Today.md")
        os.remove(today)
        self.sb.run("obsidian", "--refresh")
        self.assertTrue(os.path.isfile(today))
        self.assertEqual(self.sb.run("profile", "get", "obsidian").strip(), "true")

    def test_frontmatter_never_clobbers_an_existing_block(self):
        self.setup_books()
        hand = self.sb.path("learner", "books", "shell", "01-files.md")
        write(hand, "---\nmine: keep this\n---\n# Files and paths\n\nMy own edits.\n")
        self.sb.run("obsidian")
        text = read(hand)
        self.assertIn("mine: keep this", text)
        self.assertNotIn("calamity: book-chapter", text)   # a chapter with its own frontmatter is left alone

    def test_off_sets_the_flag_false(self):
        self.sb.onboard(tracks="dev")
        self.sb.run("obsidian")
        self.sb.run("obsidian", "--off")
        self.assertEqual(self.sb.run("profile", "get", "obsidian").strip(), "false")


if __name__ == "__main__":
    unittest.main()
