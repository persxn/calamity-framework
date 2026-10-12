"""The documents Claude reads must agree with the engine they describe.

Every engine command written in a skill, an agent, a rule book or the README
is checked against the real command line: the command exists, its action
exists, and every flag it uses exists. A renamed flag therefore fails here
instead of failing in front of a learner.
"""
import json
import os
import re
import shlex
import unittest

from tests.helpers import REPO

from cal import cli, fm

PREFIX = re.compile(r"(?:python3|python|py -3) engine/calamity\.py\s+([^`\n]*)")
SPAN = re.compile(r"`([^`\n]+)`")

# What ships. A learner may add skills and agents of their own next to these; the checks below
# look only at the framework's files, so the self-test keeps passing in a customised checkout.
SKILLS = ("boss", "bridge", "coach", "cp", "dash", "gate", "log", "notes", "onboard", "recall", "remind", "study",
          "sync", "today", "tree", "update-framework")
AGENTS = ("bridge-engineer", "checker", "cp-coach", "curriculum-architect", "examiner", "gate-strategist",
          "habit-coach", "notes-writer")


def documents():
    paths = [os.path.join(REPO, "CLAUDE.md"), os.path.join(REPO, "README.md"), os.path.join(REPO, "learner", "README.md")]
    for folder, _, files in os.walk(os.path.join(REPO, "framework")):
        if os.sep + "tree" + os.sep in folder + os.sep:
            continue  # skill-tree files mention commands only in prose
        paths += [os.path.join(folder, name) for name in sorted(files) if name.endswith(".md")]
    paths += [os.path.join(REPO, ".claude", "skills", name, "SKILL.md") for name in SKILLS]
    paths += [os.path.join(REPO, ".claude", "agents", name + ".md") for name in AGENTS]
    return paths


def commands():
    parser = cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "cmd")
    table = {}
    for name, sp in sub.choices.items():
        flags = {opt for act in sp._actions for opt in act.option_strings}
        actions = None
        for act in sp._actions:
            if not act.option_strings and act.choices:
                actions = set(act.choices)
                break
        first_positional = next((a for a in sp._actions if not a.option_strings and a.dest != "help"), None)
        if actions is not None and first_positional is not None and not first_positional.choices:
            actions = None  # the choice list belongs to a later argument (e.g. `quick TOPIC pass|fail`)
        table[name] = (flags, actions)
    return table


def tokens(text):
    text = text.replace("\\|", "|").replace("\\\n", " ")
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def clean(token):
    return token.strip("[](),.;:`'\"")


class Commands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = commands()
        cls.docs = documents()

    def check(self, where, rest, strict_action=True):
        words = tokens(rest)
        if not words:
            return 0
        name = clean(words[0])
        if not name or name.startswith("<") or name == "--help":
            return 0
        self.assertIn(name, self.table, "%s: unknown engine command in %r" % (where, rest))
        flags, actions = self.table[name]
        for word in words[1:]:
            word = clean(word)
            if word.startswith("--"):
                flag = word.split("=", 1)[0]
                self.assertIn(flag, flags | {"--help"}, "%s: `%s` has no flag %s (in %r)" % (where, name, flag, rest))
        if actions and len(words) > 1 and strict_action:
            action = clean(words[1])
            if action and not action.startswith(("<", "--", "[")) and action != "...":
                options = {clean(x) for x in action.split("|")}
                self.assertTrue(options <= actions, "%s: `%s %s` is not one of %s (in %r)" % (
                    where, name, action, sorted(actions), rest))
        return 1

    def test_full_commands(self):
        seen = 0
        for path in self.docs:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read().replace("\\\n", " ")
            for match in PREFIX.finditer(text):
                seen += self.check(os.path.relpath(path, REPO), match.group(1))
        self.assertGreater(seen, 150)

    def test_short_forms_in_code_spans(self):
        """`cf sync`, `tree drop <skill> --yes` and the like, written without the interpreter prefix."""
        seen = 0
        for path in self.docs:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            for match in SPAN.finditer(text):
                span = match.group(1)
                words = span.replace("\\|", "|").split()
                if len(words) < 2 or words[0] not in self.table or "engine/calamity.py" in span:
                    continue
                if words[0] in ("source", "version", "test", "find", "log") and not self.looks_like_engine(words):
                    continue
                seen += self.check(os.path.relpath(path, REPO), span)
        self.assertGreater(seen, 120)

    def looks_like_engine(self, words):
        _, actions = self.table[words[0]]
        return actions is None or clean(words[1]).split("|")[0] in actions or words[1].startswith(("<", "-", "["))

    def test_engine_reference_lists_every_command(self):
        with open(os.path.join(REPO, "framework", "rules", "engine.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        for name, (flags, actions) in self.table.items():
            self.assertRegex(text, r"`%s\b" % re.escape(name), "engine.md does not document `%s`" % name)
            for action in actions or ():
                self.assertRegex(text, r"\b%s\b" % re.escape(action),
                                 "engine.md does not mention `%s %s`" % (name, action))


class Structure(unittest.TestCase):
    def names(self, folder, skill=False):
        base = os.path.join(REPO, ".claude", folder)
        if skill:
            return sorted(n for n in os.listdir(base) if os.path.isfile(os.path.join(base, n, "SKILL.md")))
        return sorted(n[:-3] for n in os.listdir(base) if n.endswith(".md"))

    def test_every_shipped_skill_and_agent_is_there(self):
        self.assertEqual(sorted(set(SKILLS) - set(self.names("skills", skill=True))), [])
        self.assertEqual(sorted(set(AGENTS) - set(self.names("agents"))), [])

    def test_skills_and_agents_have_valid_front_matter(self):
        skills, agents = SKILLS, AGENTS
        builtin = {"review", "plan", "focus", "stats", "status", "run", "verify", "android", "ios", "design", "checkup",
                   "insights", "new", "reset", "stop", "help", "clear", "compact", "config", "init", "memory", "model",
                   "agents", "permissions", "login", "logout", "doctor", "cost", "resume", "export", "hooks", "mcp"}
        for name in skills:
            meta, body = fm.load(os.path.join(REPO, ".claude", "skills", name, "SKILL.md"))
            self.assertEqual(meta.get("name"), name)
            self.assertNotIn(name, builtin, "%s collides with a built-in command" % name)
            self.assertTrue(40 <= len(meta.get("description", "")) <= 1536, name)
            self.assertLess(len(body), 16000, "%s is too long to survive compaction whole" % name)
            self.assertNotRegex(body, r"(?m)^!`", "%s uses command injection, which aborts the skill when it fails" % name)
            self.assertIn(meta.get("effort"), (None, "low", "medium", "high", "xhigh", "max"))
        for name in agents:
            meta, body = fm.load(os.path.join(REPO, ".claude", "agents", name + ".md"))
            self.assertEqual(meta.get("name"), name)
            self.assertTrue(40 <= len(meta.get("description", "")) <= 1536, name)
            self.assertEqual(meta.get("model"), "inherit", "%s: pinning a model can fail on plans without it" % name)
            self.assertEqual(meta.get("effort"), "high", name)
            self.assertNotIn("(", str(meta.get("tools", "")), "%s: tools takes names only" % name)
            self.assertGreater(len(body), 800, name)

    def test_claude_md_names_every_skill_and_agent(self):
        with open(os.path.join(REPO, "CLAUDE.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        for name in SKILLS + AGENTS:
            self.assertIn("`%s`" % name, text, "CLAUDE.md does not mention %s" % name)
        self.assertIn("@framework/method.md", text)
        self.assertLess(text.count("\n"), 120)
        with open(os.path.join(REPO, "framework", "method.md"), "r", encoding="utf-8") as fh:
            self.assertLess(fh.read().count("\n"), 160)

    def test_agents_named_in_documents_exist(self):
        agents = set(AGENTS)
        for path in documents():
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            for name in re.findall(r"`([a-z][a-z-]+)` agent", text):
                self.assertIn(name, agents, "%s refers to an agent that does not exist: %s" % (path, name))

    def test_files_named_in_documents_exist(self):
        pattern = re.compile(r"`((?:framework|engine|\.claude)/[A-Za-z0-9_./-]+\.(?:md|py|tex|json))`")
        for path in documents():
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            for rel in pattern.findall(text):
                if "<" in rel or rel.endswith("settings.local.json"):
                    continue
                self.assertTrue(os.path.exists(os.path.join(REPO, rel)), "%s names a missing file: %s" % (
                    os.path.relpath(path, REPO), rel))

    def test_topic_keys_in_documents_exist(self):
        """An example that names a topic of a shipped syllabus must name a real one."""
        from tests.helpers import Sandbox

        sb = Sandbox(mini=False)            # the shipped tree, with no learner files in the way
        self.addCleanup(sb.close)
        shipped = {n.id: {t.id for t in n.topics} for n in sb.tree().nodes.values() if n.topics}
        self.assertGreater(len(shipped), 40)
        pattern = re.compile(r"(?<![\w./-])((?:gate|cp)\.[a-z0-9.-]*[a-z0-9])/([a-z0-9][a-z0-9+-]*)")
        seen = 0
        for path in documents():
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            for skill, topic in pattern.findall(text):
                where = os.path.relpath(path, REPO)
                self.assertIn(skill, shipped, "%s names a skill that ships no topics: %s" % (where, skill))
                self.assertIn(topic, shipped[skill], "%s names a missing topic: %s/%s" % (where, skill, topic))
                seen += 1
        self.assertGreaterEqual(seen, 4)    # the check is really looking at something

    def test_map_lists_every_rule_book(self):
        with open(os.path.join(REPO, "framework", "MAP.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        for name in sorted(os.listdir(os.path.join(REPO, "framework", "rules"))):
            self.assertIn("framework/rules/" + name, text)

    def test_settings(self):
        with open(os.path.join(REPO, ".claude", "settings.json"), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(set(data), {"permissions"})       # no hooks or commands run just because a repo was cloned
        perms = data["permissions"]
        for form in ("python3 engine/calamity.py", "python engine/calamity.py", "py -3 engine/calamity.py"):
            self.assertIn("Bash(%s *)" % form, perms["allow"])
            self.assertIn("PowerShell(%s *)" % form, perms["allow"])
            self.assertIn("Bash(%s setup *)" % form, perms["ask"])
        for rule in perms["allow"] + perms["ask"] + perms["deny"]:
            self.assertRegex(rule, r"^(Bash|PowerShell|Edit|Read)\(.+\)$")
            self.assertFalse(rule.startswith("Write("), "path rules must use Edit, not Write")
        self.assertIn("Edit(/learner/events/**)", perms["deny"])
        self.assertIn("Read(/learner/items/**)", perms["deny"])
        self.assertFalse(any("git " in r or "curl" in r or "rm " in r for r in perms["allow"]))

    def test_git_files(self):
        with open(os.path.join(REPO, ".gitattributes"), "r", encoding="utf-8") as fh:
            attrs = fh.read()
        self.assertIn("learner/events/*.jsonl merge=union", attrs)
        with open(os.path.join(REPO, ".gitignore"), "r", encoding="utf-8") as fh:
            ignore = fh.read().split("\n")
        for line in (".calamity/", ".claude/settings.local.json", ".env", "__pycache__/"):
            self.assertIn(line, ignore)

    def test_text_files_are_clean(self):
        for path in documents() + [os.path.join(REPO, ".gitignore"), os.path.join(REPO, ".gitattributes")]:
            with open(path, "rb") as fh:
                raw = fh.read()
            rel = os.path.relpath(path, REPO)
            self.assertNotIn(b"\r", raw, rel)
            self.assertTrue(raw.endswith(b"\n"), rel)
            self.assertNotIn(b"\t", raw, rel)
            raw.decode("utf-8")
            for word in (b"TODO", b"FIXME", b"XXX", b"lorem ipsum"):
                self.assertNotIn(word, raw, "%s contains %s" % (rel, word.decode()))

    def test_version_file(self):
        with open(os.path.join(REPO, "framework", "VERSION"), "r", encoding="utf-8") as fh:
            self.assertRegex(fh.read().strip(), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
