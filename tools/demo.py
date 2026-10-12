"""Sample output for the README and the guides, from pretend learners on the shipped tree.

    python3 tools/demo.py [--out FOLDER] [--keep]

Two pretend learners, each in a temporary copy of the framework (never in this checkout):

- first-day-*.txt: a learner who has just set a profile and enrolled a first skill;
- weeks-*.txt: a learner simulated for six weeks: developer skills, a GATE CS course followed
  lecture by lecture, Codeforces from recorded test data (no network), workouts and mocks.

Everything shown in the documents comes from these files, unchanged, and is labelled there as
coming from a pretend learner. The simulation is seeded, so a run gives the same learner each
time (dates move with the clock it is given, not with today's date).
"""
import argparse
import json
import os
import random
import re
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(REPO, "engine")
sys.path.insert(0, ENGINE)
from tests.helpers import Sandbox, write  # noqa: E402
from tests import test_cf  # noqa: E402

OUT = FIX = None

SYLLABI = {
    "dev-environment": [("terminal-editor", "Terminal and editor"), ("how-programs-run", "How a program runs"),
                        ("reading-errors", "Reading error messages"), ("debugger", "Using a debugger")],
    "linux-shell": [("files-paths", "Files and paths"), ("pipes-redirects", "Pipes and redirection"),
                    ("permissions", "Permissions"), ("processes", "Processes and signals"),
                    ("text-tools", "grep, sed and awk"), ("scripts", "Shell scripts")],
    "git-gh": [("snapshots", "Commits as snapshots"), ("daily-loop", "The daily loop"), ("branches", "Branches and merges"),
               ("rebase", "Rebase and history"), ("remotes", "Remotes and pull requests"), ("undo", "Undoing things")],
    "html-css": [("semantic-html", "Semantic HTML"), ("box-model", "The box model"), ("flexbox", "Flexbox"),
                 ("grid", "Grid"), ("responsive", "Responsive layout")],
    "javascript": [("values-types", "Values and types"), ("functions-closures", "Functions and closures"),
                   ("arrays-objects", "Arrays and objects"), ("async", "Promises and async/await"),
                   ("modules", "Modules"), ("dom-events", "The DOM and events")],
}
LECTURES = [("Discrete Mathematics", "gate.cs.discrete-math", 12), ("Digital Logic", "gate.cs.digital-logic", 8)]


def syllabus_text(skill, topics):
    out = ["---", "skill: %s" % skill, "written: 2026-08-31", "sources: []", "---", "", "# Topics", ""]
    prev = None
    for tid, title in topics:
        out.append("## %s | %s" % (tid, title))
        if prev:
            out.append("needs: [%s]" % prev)
        out += ["level: 2", "- (objectives)", ""]
        prev = tid
    return "\n".join(out)


def learner_copy(start):
    """A pretend learner's repository: a temporary folder with its own copy of the framework."""
    sb = Sandbox(mini=False, start=start)
    shutil.copytree(os.path.join(REPO, "framework"), os.path.join(sb.root, "framework"))
    return sb


def save(name, text):
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def first_day():
    """A learner a few minutes after onboarding: a profile, a goal and a first skill."""
    sb = learner_copy("2026-10-12T19:30:00+05:30")
    try:
        for key, value in (("name", "Sam"), ("tracks", "10x"), ("goals", "mern-stack"), ("mode.default", "mastery"),
                           ("onboarded", "true")):
            sb.run("profile", "set", key, value)
        sb.run("enroll", "dev-environment")
        os.environ["COLUMNS"] = "78"
        for name, args in (("tree-path-mern-stack", ["tree", "path", "mern-stack"]),
                           ("tree-suggest", ["tree", "suggest"]),
                           ("dash-roadmap", ["dash", "roadmap", "--width", "78"]),
                           ("tree-show-dev-environment", ["tree", "show", "dev-environment"]),
                           ("today", ["today"]), ("next", ["next"])):
            save("first-day-" + name, sb.run(*args, expect=None))
    finally:
        sb.close()


def main():
    global OUT, FIX
    ap = argparse.ArgumentParser(description="Sample output from pretend learners.")
    ap.add_argument("--out", help="folder for the .txt files (default: a new temporary folder)")
    ap.add_argument("--keep", action="store_true", help="keep the six-week learner's repository and say where")
    args = ap.parse_args()
    OUT = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(prefix="calamity-samples-")
    os.makedirs(OUT, exist_ok=True)
    FIX = tempfile.mkdtemp(prefix="calamity-cf-")
    first_day()
    rng = random.Random(11)
    sb = learner_copy("2026-08-31T09:10:00+05:30")
    n_items = [0]

    def run(*args, expect=0):
        return sb.run(*args, expect=expect)

    def new_item(topic, also=()):
        n_items[0] += 1
        gate = topic.startswith("gate")
        draft = {"type": "mcq", "topics": [topic] + list(also), "difficulty": 2,
                 "stem": "Demo question %d on %s: which option is correct?" % (n_items[0], topic),
                 "options": ["a%d" % n_items[0], "b%d" % n_items[0], "c%d" % n_items[0], "d%d" % n_items[0]],
                 "answer": "B", "solution": "Option B follows from the definition.", "expect_s": 90}
        if gate:
            draft["marks"] = rng.choice([1, 2])
            draft.pop("expect_s")
        path = sb.path(".calamity", "tmp", "d.json")
        write(path, json.dumps(draft))
        ident = re.search(r"it-[a-z0-9]{10}", run("item", "draft", "--file", path)).group(0)
        run("item", "verify", ident, "--answer", "B", "--by", "checker")
        return ident

    def answer(topic, p_ok):
        out = run("ask", "--topic", topic, expect=None)
        if sb.code == 4:
            new_item(topic)
            out = run("ask", "--topic", topic)
        ident = re.search(r"ITEM (it-[a-z0-9]{10})", out).group(1)
        ok = rng.random() < p_ok
        sb.advance(seconds=rng.randint(25, 170))
        args = ["answer", ident, "--answer", "B" if ok else "C"]
        if rng.random() < 0.12:
            args += ["--hints", "1"]
        res = run(*args)
        if not ok:
            run("mistake", ident, rng.choice(["concept", "careless", "memory", "misread"]))
        return res

    # ---------------------------------------------------------------- onboarding
    run("setup", "--machine", "thinkpad")
    for key, value in (("name", "Asha"), ("tracks", "10x,cp,gate-cs"), ("goals", "mern-stack,cp.rating-1400"),
                       ("sleep.start", "00:30"), ("sleep.end", "07:30"), ("daily.target_hours", "8"),
                       ("workout.minutes", "45"), ("gate.year", "2027"), ("gate.papers", "CS"),
                       ("gate.target_marks.CS", "70"), ("cfg.new_per_day", "6"), ("cfg.lectures_per_day", "2")):
        run("profile", "set", key, value)
    run("profile", "set", "teach.style", "examples first, then the rule", "--text")
    run("profile", "set", "onboarded", "true")
    for skill, topics in SYLLABI.items():
        write(sb.path("learner", "syllabus", skill + ".md"), syllabus_text(skill, topics))
    run("enroll", "dev-environment")
    sb.advance(minutes=1)
    run("gate", "enroll")
    rows, order = [], 0
    for section, skill, hours in LECTURES:
        for topic in sb.tree().get(skill).topics:
            for part in (1, 2):
                order += 1
                rows.append({"id": "%s-%02d" % (skill.split(".")[-1][:2], order), "title": "%s (%d)" % (topic.title, part),
                             "section": section, "order": order, "minutes": rng.choice([45, 50, 55, 60]),
                             "topics": [topic.key] if part == 2 else []})
    run("source", "add", "gate-course", "--title", "GATE CS course", "--kind", "course", "--route", "paste",
        "--tracks", "gate-cs", "--note", "automated access disallowed (read 2026-08-31): paste and manual log")
    path = sb.path(".calamity", "tmp", "course.json")
    write(path, json.dumps(rows))
    run("source", "import", "gate-course", "--file", path)
    sb.env["CALAMITY_CF_FIXTURES"] = FIX

    # ---------------------------------------------------------------- six weeks
    enrol_plan = {3: "linux-shell", 9: "git-gh", 16: "html-css", 22: "javascript", 6: "cp.cpp", 26: "cp.stl"}
    for day in range(42):
        if day in enrol_plan:
            run("enroll", enrol_plan[day], "--force")
        if day % 7 == 6 and rng.random() < 0.6:          # a day off now and then
            sb.advance(days=1)
            continue
        start = sb.clock
        steps = 0
        print("day %d of 42" % (day + 1), sb.clock.date(), flush=True)
        while steps < 22:
            steps += 1
            nxt = run("next")
            kind = re.search(r"NEXT: (\S+)", nxt).group(1)
            if kind == "review":
                topic = re.search(r"^topic: (\S+)", nxt, re.M).group(1)
                sb.advance(minutes=rng.randint(1, 3))
                answer(topic, 0.9)
            elif kind == "new":
                topic = re.search(r"^topic: (\S+)", nxt, re.M).group(1)
                if "covered %s" % topic in nxt:
                    sb.advance(minutes=rng.randint(12, 28))
                    run("covered", topic)
                answer(topic, 0.82)
            elif kind == "watch":
                m = re.search(r"^  (\S+) (\S+) \|", nxt, re.M)
                sb.advance(minutes=rng.randint(45, 60))
                run("log", m.group(1), m.group(2))
            elif kind == "boss":
                skill = re.search(r"^skill: (\S+)", nxt, re.M).group(1)
                sb.advance(minutes=90)
                run("boss", "record", skill, "pass", "--evidence", "all checks under 'Passes when' ran and held")
            else:
                break
        if rng.random() < 0.7:
            run("workout", str(rng.choice([30, 45, 45, 60])))
        if day == 20:
            run("gate", "mock", "CS", "38.67", "--source", "sectional mix 1", "--sections", "GA=9,DM=7.33,DL=5")
        if day == 34:
            run("gate", "mock", "CS", "47.33", "--source", "sectional mix 2", "--sections", "GA=10.67,DM=9,DL=6.33")
        sb.at((start.replace(hour=9, minute=10)).isoformat()).advance(days=1, minutes=rng.randint(-40, 90))

    # Codeforces from the test fixtures, as of "now"
    test_cf.NOW = sb.clock.isoformat()
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    for method, result in test_cf.fixtures().items():
        with open(os.path.join(FIX, method + ".json"), "w") as fh:
            json.dump({"status": "OK", "result": result}, fh)
    run("cf", "link", "tester")
    run("cf", "sync")
    run("profile", "set", "cp.target_rating", "1800")
    run("profile", "set", "cp.target_date", "2027-08-31")

    sb.advance(hours=1)
    views = {
        "brief": ["brief"], "today": ["today"], "next": ["next"], "dash": ["dash", "--width", "78"],
        "roadmap": ["dash", "roadmap", "--track", "10x", "--width", "78"], "queue": ["dash", "queue", "--width", "78"],
        "path-mern": ["tree", "path", "mern-stack"], "path-tenx": ["tree", "path", "ten-x"],
        "show-git": ["tree", "show", "git-gh"], "suggest": ["tree", "suggest"], "week": ["stats", "week"],
        "hours": ["stats", "hours"], "gate-status": ["gate", "status"], "gate-triage": ["gate", "triage"],
        "gate-mocks": ["gate", "mocks"], "cf-rating": ["cf", "rating"], "cf-analyse": ["cf", "analyse"],
        "cf-recommend": ["cf", "recommend", "--n", "4"], "source": ["source", "status"], "errors": ["stats", "errors"],
        "needs": ["item", "needs", "--n", "2"], "doctor": ["doctor"], "weave": ["weave", "javascript"],
        "statusline": ["statusline"], "path-cp": ["tree", "path", "cp.rating-1400"],
    }
    os.environ["COLUMNS"] = "78"
    for name, cmd in views.items():
        save("weeks-" + name, run(*cmd, expect=None))
    run("rebuild")
    shutil.copyfile(sb.path("learner", "PROGRESS.md"), os.path.join(OUT, "weeks-PROGRESS.md"))
    print("items made: %d | events: %d | samples in %s" % (n_items[0], sb.state().n_events, OUT))
    shutil.rmtree(FIX, ignore_errors=True)
    if args.keep:
        print("the six-week learner's repository: %s" % sb.root)
    else:
        sb.close()


if __name__ == "__main__":
    main()
