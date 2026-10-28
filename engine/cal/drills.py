"""Developer drills: item types for debugging, reading code, auditing AI output, writing specs and diagnosing
injected failures. The `drill-smith` agent writes them; the `checker` verifies them blind like any item.

    type        the learner gets                                        checked by                 opens when
    debug       a small repository with failing tests and a seeded bug  its tests pass, test files  the topic is
                (fixture), the files the fix may touch (bounds)         untouched, diff in bounds   consolidating
    debug-docs  the same, but the fix needs one section of the          as debug; hints point only  the skill is
                official docs (docs); recorded as no-AI                 to the docs                 ready (60% solid)
    read        a real repository at a pinned commit, timed: where is   an answer `path:symbol`,    any time
                X done, trace Y                                         graded by the engine
    audit       AI-style code with a stated number of seeded flaws      the rubric                  level 2 and up
    prompt      write the spec an AI agent would need for a task        the rubric                  ai-pair-engineering
    chaos       the learner's own project with a failure injected in a  the diagnosis and fix       after a project
                copy; diagnose from logs alone                          against the injected cause  milestone

A drill that changes code (debug, debug-docs, chaos) is verified only when the checker shows both halves:
the check fails on the fixture as given, and passes once the checker has fixed it blind
(`item verify <item> --ran --unfixed-fails --evidence "..."`).
"""
from __future__ import annotations

import re

from .util import CalError

DRILL_TYPES = ("debug", "debug-docs", "read", "audit", "prompt", "chaos")
FIXED = ("debug", "debug-docs", "chaos")         # the check must fail before the fix and pass after it
EXPECT = {"debug": 1800, "debug-docs": 2400, "read": 1200, "audit": 1200, "prompt": 1500, "chaos": 2700}
SECURED = ("consolidating", "solid", "mastered")
READY = ("ready", "known", "mastered")
SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]{0,60}$")
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


def norm_location(text) -> str:
    """`src/app.js:handleRequest()` and `./src\\app.js : handleRequest` are the same answer."""
    s = str(text).strip().replace("\\", "/")
    s = re.sub(r"\s*:\s*", ":", s)
    while s.startswith("./"):
        s = s[2:]
    s = re.sub(r"\(\s*\)$", "", s)
    return s


def validate(kind: str, data: dict, tree, topics: list, public: dict, sealed: dict) -> None:
    """Check a drill draft's own fields and put them in the public item or its sealed part."""
    skill = topics[0].split("/", 1)[0]
    if kind in FIXED:
        check = str(data.get("check") or "").strip()
        if len(check) < 10:
            raise CalError("%s drills need a 'check': the test command, and what passing means" % kind)
        public["check"] = check
        if kind == "chaos":
            project = str(data.get("project") or "").strip().replace("\\", "/")
            if not project.startswith(("learner/work/", "learner/projects/")):
                raise CalError("a chaos drill names the learner's own project: 'project': 'learner/projects/<slug>'")
            public["project"] = project
        else:
            fixture = str(data.get("fixture") or "").strip()
            if not SLUG.match(fixture):
                raise CalError("a %s drill needs a 'fixture': the folder name under learner/work/%s/drills/" % (kind, skill))
            public["fixture"] = "learner/work/%s/drills/%s" % (skill, fixture)
            bounds = [str(b).strip().replace("\\", "/") for b in (data.get("bounds") or []) if str(b).strip()]
            if not bounds:
                raise CalError("a %s drill needs 'bounds': the files the fix may change (tests are never in them)" % kind)
            if any("test" in b.lower() for b in bounds):
                raise CalError("bounds never include test files: the fix must make the tests pass as written")
            public["bounds"] = bounds
        if kind == "debug-docs":
            docs = str(data.get("docs") or "").strip()
            if not docs.startswith("https://"):
                raise CalError("a debug-docs drill names the official documentation page its fix needs: 'docs': 'https://...'")
            public["docs"] = docs
    elif kind == "read":
        repo, commit = str(data.get("repo") or "").strip(), str(data.get("commit") or "").strip().lower()
        if not repo.startswith("https://"):
            raise CalError("a read drill names the repository: 'repo': 'https://...'")
        if not COMMIT.match(commit):
            raise CalError("a read drill pins a commit: 'commit': '<7 to 40 hex digits>'")
        public["repo"], public["commit"] = repo, commit
        answers = data.get("answer")
        answers = answers if isinstance(answers, list) else [answers]
        accept = [norm_location(a) for a in answers if a and ":" in str(a)]
        if not accept:
            raise CalError("a read drill's answer is a location, path:symbol (for example lib/router/index.js:handle)")
        sealed["answer"] = {"accept": accept}
        public.setdefault("strand", "I")
    elif kind in ("audit", "prompt"):
        rubric = [str(r).strip() for r in (data.get("rubric") or []) if str(r).strip()]
        if len(rubric) < 2:
            raise CalError("%s drills need a 'rubric' of two or more points a good answer meets" % kind)
        public["rubric"] = rubric
        if kind == "audit":
            try:
                flaws = int(data.get("flaws"))
            except (TypeError, ValueError):
                raise CalError("an audit drill says how many flaws are seeded: 'flaws': 4")
            if not 1 <= flaws <= 12:
                raise CalError("flaws is 1 to 12")
            public["flaws"] = flaws
            if int(tree.topic(topics[0]).level or 1) < 2:
                raise CalError("audit drills start at level 2: %s is level 1" % topics[0])
        if kind == "prompt" and skill != "ai-pair-engineering":
            raise CalError("prompt drills belong to ai-pair-engineering topics")
    if kind != "read" and len(sealed.get("solution", "")) < 10:
        raise CalError("a drill needs a 'solution': the seeded cause and its fix (or the model answer), sealed")


def grade(sealed_answer: dict, raw) -> tuple:
    given = norm_location(raw)
    return given in sealed_answer["accept"], given


def locked(state, tree, it) -> str | None:
    """Why a drill cannot be served yet, or None."""
    kind = it.type
    if kind not in DRILL_TYPES or not it.topics:
        return None
    key = it.topics[0]
    skill = key.split("/", 1)[0]
    if kind == "debug" and state.topic_status(key) not in SECURED + ("known",):
        return "a debug drill opens once %s is consolidating" % key
    if kind == "debug-docs" and state.skill_status(skill) not in READY:
        return "a debug-docs drill opens once %s is ready (60%% of its topics solid)" % skill
    if kind == "chaos":
        built = any(o.type in ("task", "code") and o.n_ok > 0 for o in state.items.values()) or \
            any(sk.boss_ok for sk in state.skills.values())
        if not built:
            return "a chaos drill opens after a project milestone (a task passed, or a boss)"
    return None


def blind_lines(item: dict) -> list:
    """What the learner needs besides the stem: where the code is, what may change, where to read."""
    out = []
    if item.get("fixture"):
        out.append("fixture: %s/ (work in a copy; the tests stay as they are)" % item["fixture"])
    if item.get("bounds"):
        out.append("change only: %s" % ", ".join(item["bounds"]))
    if item.get("docs"):
        out.append("the docs (the only help: page, then section, then paragraph): %s" % item["docs"])
    if item.get("repo"):
        out.append("repository: %s at commit %s (clone into .calamity/scratch/, never into learner/)" % (
            item["repo"], item["commit"]))
        out.append("(answer with a location: path:symbol)")
    if item.get("project"):
        out.append("project: %s (a copy with one failure injected; diagnose from the logs alone)" % item["project"])
    if item.get("flaws"):
        out.append("(%d flaws are seeded: find each, say why it is wrong and what is right)" % item["flaws"])
    return out
