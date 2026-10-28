"""Shared test helpers: a throwaway learner repository with its own clock and a small skill tree."""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ENGINE)
if ENGINE not in sys.path:
    sys.path.insert(0, ENGINE)

from cal import cli  # noqa: E402
from cal.state import State  # noqa: E402
from cal.store import Repo  # noqa: E402
from cal.tree import Tree  # noqa: E402

START = "2026-03-02T09:00:00+05:30"  # a Monday morning

MINI = {
    "tree/tracks.md": """---
tracks: [dev, cp, gate, gate-cs, gate-da]
dev.title: Developer
dev.groups: [base, build, milestones]
cp.title: Competitive programming
gate-cs.title: GATE CS
gate-da.title: GATE DA
---
""",
    "tree/dev/shell.md": """---
id: shell
title: Shell
track: dev
group: base
weaves_into: [dev]
aliases: [bash, terminal]
est_hours: 10
order: 10
summary: Work in a terminal.
---

# Scope

- pipes and permissions

# Topics

## pipes | Pipes
level: 1
- chain two commands with a pipe

## perms | Permissions
needs: [pipes]
level: 2
- read and change file modes
""",
    "tree/dev/docker.md": """---
id: docker
title: Docker
track: dev
group: build
prereqs: [shell]
weaves_into: [runnable]
aliases: [containers]
est_hours: 20
order: 10
summary: Containers.
---

# Scope

- images, Dockerfiles, multi-stage builds

# Boss

Containerise a service.

Passes when:

- the image builds
- the container answers on /health

# Topics

## images | Images and containers
level: 1
- say what an image is

## dockerfile | Writing a Dockerfile
needs: [images]
level: 2
- write a Dockerfile

## multi-stage | Multi-stage builds
needs: [dockerfile]
level: 3
- write a two-stage build
""",
    "tree/dev/java.md": """---
id: java
title: Java
track: dev
group: build
slot: language
tags: [language, runnable]
est_hours: 40
order: 20
summary: The Java language.
---

# Scope

- classes, collections, streams

# Topics

## classes | Classes
level: 1
- write a class

## collections | Collections
needs: [classes]
level: 2
- pick the right collection

## streams | Streams
needs: [collections]
level: 3
- write a stream pipeline
""",
    "tree/dev/python.md": """---
id: python
title: Python
track: dev
group: build
slot: language
tags: [language, runnable]
est_hours: 30
order: 30
summary: The Python language.
---

# Scope

- types, functions, modules
""",
    "tree/dev/api.md": """---
id: api
title: API design
track: dev
group: build
prereqs: ["slot:language"]
est_hours: 15
order: 40
summary: Design an HTTP API.
---

# Topics

## rest | REST resources
level: 2
- model a resource
""",
    "tree/dev/capstone.md": """---
id: capstone
title: Capstone
track: dev
group: milestones
kind: milestone
prereqs: [docker, api]
order: 10
summary: Ship a service.
---

# Boss

Ship one service.

Passes when:

- it runs in a container
""",
    "tree/cp/cp.bs.md": """---
id: cp.bs
title: Binary search
track: cp
group: core
tags: [cp]
weaves_into: [cp]
cf_tags: [binary search]
band: 1100
est_hours: 10
order: 10
summary: Binary search.
---

# Topics

## on-answer | Binary search on the answer
level: 2
- search a monotone predicate
""",
    "tree/cp/cp.dp.md": """---
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

# Topics

## knapsack | Knapsack
level: 3
- 0/1 knapsack

## lis | Longest increasing subsequence
level: 3
- LIS in n log n
""",
    "tree/cp/cp.rating-1200.md": """---
id: cp.rating-1200
title: Codeforces 1200
track: cp
group: milestones
kind: milestone
prereqs: [cp.bs]
rating: 1200
order: 10
summary: Reach 1200.
---

# Boss

Reach 1200.
""",
    "tree/cp/cp.rating-1400.md": """---
id: cp.rating-1400
title: Codeforces 1400
track: cp
group: milestones
kind: milestone
prereqs: [cp.rating-1200, cp.dp]
rating: 1400
order: 20
summary: Reach 1400.
---

# Boss

Reach 1400.
""",
    "tree/gate/gate.ga.md": """---
id: gate.ga
title: General Aptitude
track: gate
group: aptitude
marks: 15
marks_source: official
est_hours: 30
order: 10
summary: Aptitude.
---

# Topics

## series | Series
level: 2
- next term of a series

## ratios | Ratios
level: 1
- ratios and percentages
""",
    "tree/gate-cs/gate.cs.la.md": """---
id: gate.cs.la
title: Linear Algebra
track: gate-cs
group: maths
paper: CS
marks: 4
marks_source: prior
overlaps: [gate.da.la]
est_hours: 25
order: 10
summary: Linear algebra for CS.
---

# Topics

## matrices | Matrices
level: 2
same_as: [gate.da.la/matrices]
- rank and inverse

## eigen | Eigenvalues
level: 3
- eigenvalues of a 2x2 matrix
""",
    "tree/gate-cs/gate.cs.os.md": """---
id: gate.cs.os
title: Operating System
track: gate-cs
group: core
paper: CS
marks: 8
marks_source: prior
est_hours: 60
order: 20
summary: Operating systems.
---

# Topics

## deadlock | Deadlock
level: 3
- Banker's algorithm

## scheduling | CPU scheduling
level: 2
- waiting time under round robin

## paging | Paging
level: 3
- page table size
""",
    "tree/gate-da/gate.da.la.md": """---
id: gate.da.la
title: Linear Algebra
track: gate-da
group: subjects
paper: DA
marks: 12
marks_source: prior
overlaps: [gate.cs.la]
est_hours: 45
order: 10
summary: Linear algebra for DA.
---

# Topics

## matrices | Matrices
level: 2
- rank and inverse

## svd | Singular value decomposition
level: 4
- singular values
""",
}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class Sandbox:
    """A temporary repository root. `mini=True` gives it the small tree above; otherwise the shipped framework."""

    def __init__(self, mini=True, start=START):
        self.root = tempfile.mkdtemp(prefix="calamity-test-")
        self.clock = datetime.fromisoformat(start)
        # no shell start-up file and no Claude Code home: setup and doctor never read or write the real ones
        self.env = {"SHELL": "", "CLAUDE_CONFIG_DIR": os.path.join(self.root, ".claude-home")}
        self.code = 0
        self.err = ""
        if mini:
            fw = os.path.join(self.root, "framework")
            for rel, text in MINI.items():
                write(os.path.join(fw, rel), text)
            for rel in ("config.md", os.path.join("gate", "2027.md"), os.path.join("notes", "preamble.tex")):
                os.makedirs(os.path.dirname(os.path.join(fw, rel)), exist_ok=True)
                shutil.copyfile(os.path.join(REPO, "framework", rel), os.path.join(fw, rel))
            write(os.path.join(fw, "method.md"), "# Method (test stub)\n")
            # Due dates are spread by a hash of each event's random id. Tests that count what is due
            # on a given day need them exact, so the test tree turns the spread off.
            config = os.path.join(fw, "config.md")
            with open(config, "r", encoding="utf-8") as fh:
                text = fh.read()
            assert "\nfuzz: true" in text
            write(config, text.replace("\nfuzz: true", "\nfuzz: false", 1))
        self._n = 0

    # ------------------------------------------------------------ plumbing

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def now(self):
        return self.clock.isoformat()

    def advance(self, seconds=0, minutes=0, hours=0, days=0):
        self.clock += timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        return self

    def at(self, stamp):
        self.clock = datetime.fromisoformat(stamp)
        return self

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def run(self, *args, expect=0, stdin=None):
        """Run one engine command in-process. Returns stdout (stderr is kept in self.err)."""
        env = {"CALAMITY_ROOT": self.root, "CALAMITY_NOW": self.now()}
        env.update(self.env)
        saved = {k: os.environ.get(k) for k in list(env) + ["CALAMITY_FRAMEWORK", "CALAMITY_CF_FIXTURES"]}
        for key in ("CALAMITY_FRAMEWORK", "CALAMITY_CF_FIXTURES"):
            os.environ.pop(key, None)
        os.environ.update(env)
        out, err = io.StringIO(), io.StringIO()
        old_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = cli.main([str(a) for a in args])
                except SystemExit as exc:  # argparse
                    code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdin = old_stdin
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.code, self.err = code, err.getvalue()
        if expect is not None and code != expect:
            raise AssertionError("%r exited %s, expected %s\nstdout: %s\nstderr: %s" % (
                args, code, expect, out.getvalue(), err.getvalue()))
        return out.getvalue()

    def state(self):
        repo = Repo(self.root)
        tree = Tree(repo)
        return State(repo, tree)

    def tree(self):
        return Tree(Repo(self.root))

    # ------------------------------------------------------------ common flows

    def onboard(self, **keys):
        self.run("profile", "set", "name", "Tester")
        for key, value in keys.items():
            self.run("profile", "set", key.replace("__", "."), value)
        self.run("profile", "set", "onboarded", "true")

    def legacy_pace(self):
        """The pace before Mastery Gate v2 (a topic opens once those it needs were answered right, no limit on
        open topics, no consolidation step), for tests about other parts of the plan."""
        for pace in ("mastery", "exam"):
            self.run("profile", "set", "cfg.pace.%s.unlock" % pace, "learning")
            self.run("profile", "set", "cfg.pace.%s.wip" % pace, "50")
            self.run("profile", "set", "cfg.pace.%s.consolidate_minutes" % pace, "0")

    def draft(self, topic, kind="mcq", answer="B", also=(), by="examiner", **more):
        """Store one draft and return its id."""
        data = {"type": kind, "topics": [topic] + list(also), "difficulty": more.pop("difficulty", 2),
                "stem": more.pop("stem", "Question %d about %s: which option is right?" % (self._n, topic)),
                "solution": more.pop("solution", "Option B is right because of how the idea works."),
                "expect_s": more.pop("expect_s", 90)}
        self._n += 1
        if kind in ("mcq", "msq"):
            data["options"] = more.pop("options", ["first choice %d" % self._n, "second choice %d" % self._n,
                                                   "third choice %d" % self._n, "fourth choice %d" % self._n])
            data["answer"] = answer
        elif kind in ("nat", "short"):
            data["answer"] = answer
        else:
            data.pop("solution")
            data.pop("expect_s")  # hands-on work takes the engine's default (15 minutes)
            data["check"] = more.pop("check", "./run-tests.sh  # passes when it exits 0")
            data["rubric"] = more.pop("rubric", ["does the thing"])
        data.update(more)
        path = self.path(".calamity", "tmp", "draft-%d.json" % self._n)
        write(path, json.dumps(data))
        out = self.run("item", "draft", "--file", path, "--by", by)
        return re.search(r"it-[a-z0-9]{10}", out).group(0)

    def item(self, topic, kind="mcq", answer="B", **more):
        """A verified item for a topic. Returns its id."""
        ident = self.draft(topic, kind, answer, **more)
        if kind in ("mcq", "msq", "nat", "short"):
            self.run("item", "verify", ident, "--answer", answer if not isinstance(answer, dict) else answer["value"],
                     "--by", "checker")
        else:
            self.run("item", "verify", ident, "--ran", "--evidence", "reference solution passed; empty one failed",
                     "--by", "checker")
        return ident

    def ask(self, topic=None, expect=0):
        out = self.run("ask", *(["--topic", topic] if topic else []), expect=expect)
        m = re.search(r"ITEM (it-[a-z0-9]{10})", out)
        return m.group(1) if m else None

    def answer(self, ident, answer="B", seconds=60, **flags):
        self.advance(seconds=seconds)
        args = ["answer", ident, "--answer", answer]
        for key, value in flags.items():
            args += ["--" + key, value]
        return self.run(*args)

    def do(self, topic, answer="B", seconds=60, **flags):
        """Ask whatever verified item the engine picks for a topic and answer it."""
        ident = self.ask(topic)
        assert ident, "no item served for %s" % topic
        return self.answer(ident, answer, seconds, **flags)


class Case(unittest.TestCase):
    """A test case with one mini sandbox, cleaned up afterwards."""

    mini = True

    def setUp(self):
        self.sb = Sandbox(mini=self.mini)
        self.addCleanup(self.sb.close)
