"""End-to-end run of the framework the way a learner's laptops would use it.

    python3 tools/e2e.py [--keep]

It copies this working tree into a temporary folder, "publishes" it as a git repository, clones
it as two laptops, and drives the real engine through the commands the skills call, with a
simulated clock: onboarding, syllabi, items made and checked, study, a woven exercise, a GATE
course followed lecture by lecture, Codeforces (from recorded data, no network), notes and a PDF
(when a TeX engine is installed), dashboards, two laptops studying apart and merging, and a
framework update, both for a clone and for a copy that began as a downloaded archive.

Nothing outside the temporary folder is touched; it is deleted afterwards unless --keep is
given. Needs git. Standard library only, like the engine.
"""
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = tempfile.mkdtemp(prefix="calamity-e2e-")
FIX = os.path.join(BASE, "cf-fixtures")
GIT = ["git", "-c", "user.name=E2E Test", "-c", "user.email=e2e@example.invalid", "-c", "init.defaultBranch=main",
       "-c", "commit.gpgsign=false"]
PY = sys.executable


class Laptop:
    def __init__(self, path, clock):
        self.path = path
        self.clock = datetime.fromisoformat(clock)
        self.env_extra = {}

    def cal(self, *args, expect=0, stdin=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
        env["CALAMITY_NOW"] = self.clock.isoformat()
        env.update(self.env_extra)
        proc = subprocess.run([PY, "engine/calamity.py"] + [str(a) for a in args], cwd=self.path, env=env,
                              input=stdin.encode() if stdin else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")
        if expect is not None and proc.returncode != expect:
            raise SystemExit("FAILED in %s: calamity %s -> exit %s\n%s\n%s" % (self.path, " ".join(map(str, args)),
                                                                              proc.returncode, out, err))
        return out + err

    def git(self, *args, expect=0):
        proc = subprocess.run(GIT + list(args), cwd=self.path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.stdout.decode("utf-8", "replace")
        if expect is not None and proc.returncode != expect:
            raise SystemExit("FAILED in %s: git %s -> %s\n%s" % (self.path, " ".join(args), proc.returncode, out))
        return out

    def tick(self, **kw):
        self.clock += timedelta(**kw)

    def write(self, rel, text):
        full = os.path.join(self.path, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def read(self, rel):
        with open(os.path.join(self.path, rel), "r", encoding="utf-8") as fh:
            return fh.read()

    # what the examiner and checker agents do, reduced to their engine calls
    def make_items(self, specs):
        drafts = []
        for n, (topics, kind, answer) in enumerate(specs):
            d = {"type": kind, "topics": topics, "difficulty": 2,
                 "stem": "E2E question %d on %s: which option is correct here?" % (n, topics[0])}
            if kind == "mcq":
                d.update(options=["alpha %d" % n, "beta %d" % n, "gamma %d" % n, "delta %d" % n], answer=answer,
                         solution="Option %s follows from the definition." % answer)
            elif kind == "nat":
                d.update(answer=answer, solution="Computed step by step to %s." % answer)
            else:
                d.update(check="cd learner/work/e2e && sh check.sh   # passes when it exits 0", rubric=["works"])
            drafts.append(d)
        self.write(".calamity/tmp/drafts.json", json.dumps(drafts))
        out = self.cal("item", "import", "--file", ".calamity/tmp/drafts.json", "--by", "examiner")
        ids = re.findall(r"it-[a-z0-9]{10}", out)
        assert len(ids) == len(specs), out
        assert not os.path.exists(os.path.join(self.path, ".calamity/tmp/drafts.json"))
        for ident, (topics, kind, answer) in zip(ids, specs):
            shown = self.cal("item", "show", ident)
            assert "KEY" not in shown and "Option %s follows" % answer not in shown
            if kind in ("mcq", "nat"):
                res = self.cal("item", "verify", ident, "--answer", answer, "--by", "checker")
            else:
                res = self.cal("item", "verify", ident, "--ran", "--evidence", "reference passed; empty failed",
                               "--by", "checker")
            assert "verified" in res, res
        return ids

    def study(self, topic, answer="B", seconds=70, **flags):
        out = self.cal("ask", "--topic", topic)
        ident = re.search(r"ITEM (it-[a-z0-9]{10})", out).group(1)
        self.tick(seconds=seconds)
        args = ["answer", ident]
        if "--result pass|fail" in out:
            args += ["--result", "pass", "--evidence", "ran the check; exit 0"]
        else:
            args += ["--answer", answer]
        for k, v in flags.items():
            args += ["--" + k, v]
        return self.cal(*args)


def section(title):
    print("\n=== %s" % title)


def remove_tree(path):
    """Delete a folder, including the read-only files git leaves on Windows."""
    def retry(func, name, _):
        os.chmod(name, stat.S_IWRITE)
        func(name)
    shutil.rmtree(path, onerror=retry)


def main():
    # ------------------------------------------------------------------ "publish" the framework and clone it twice
    seed = os.path.join(BASE, "seed")
    shutil.copytree(SRC, seed, ignore=shutil.ignore_patterns(".calamity", "__pycache__", ".git", "*.pyc",
                                                             "settings.local.json"))
    s = Laptop(seed, "2026-10-11T09:00:00+05:30")
    s.git("init", "-q")
    s.git("add", "-A")
    s.git("commit", "-q", "-m", "framework")
    version = s.read("framework/VERSION").strip()
    s.git("tag", "v" + version)
    origin = os.path.join(BASE, "origin.git")
    subprocess.check_call(GIT + ["clone", "-q", "--bare", seed, origin])
    a = Laptop(os.path.join(BASE, "laptop-a"), "2026-10-11T09:00:00+05:30")
    subprocess.check_call(GIT + ["clone", "-q", origin, a.path])

    section("fresh clone")
    out = a.cal("brief")
    assert "NOT ONBOARDED" in out and "150 skills" in out, out
    print(out.strip())
    doctor = a.cal("doctor")
    assert "0 problem(s)" in doctor, doctor
    assert "OK    .gitattributes union merge" in doctor and "OK    .gitignore covers .calamity/" in doctor
    print(doctor.strip().split("\n")[-1])
    st = a.git("status", "--porcelain")
    assert st.strip() == "", "running the engine dirtied the clone:\n" + st       # .calamity/ is ignored

    section("onboarding (what /onboard records)")
    print(a.cal("setup", "--machine", "laptop-a", "--hook").strip())
    hook = json.loads(a.read(".claude/settings.local.json"))["hooks"]["SessionStart"][0]["hooks"][0]
    proc = subprocess.run([hook["command"]] + hook["args"], input=b'{"source":"startup"}', cwd=a.path,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode == 0 and proc.stdout.startswith(b"=== CALAMITY BRIEF ==="), proc.stderr
    assert a.git("status", "--porcelain").strip() == ""                           # settings.local.json is ignored too
    for key, value in (("name", "Asha"), ("tracks", "10x,cp,gate-cs,gate-da"), ("goals", "mern-stack,cp.rating-1400"),
                       ("mode.default", "mastery"), ("sleep.start", "01:00"), ("sleep.end", "08:00"),
                       ("daily.target_hours", "12"), ("workout.minutes", "60"), ("gate.year", "2027"),
                       ("gate.papers", "CS,DA"), ("gate.registered", "true"), ("gate.target_rank", "1000"),
                       ("cfg.new_per_day", "6")):
        a.cal("profile", "set", key, value)
    a.cal("profile", "set", "teach.style", "small chunks, test at once, surprise recall", "--text")
    a.cal("profile", "set", "onboarded", "true")
    print(a.cal("tree", "path", "mern-stack").strip())
    print(a.cal("tree", "suggest").strip())

    section("first skills, with syllabi written for this learner")
    out = a.cal("enroll", "dev-environment")
    assert "no syllabus yet" in out
    template = a.cal("syllabus", "template", "dev-environment")
    assert "learner/syllabus/dev-environment.md" in template and "how a program runs" in template
    a.write("learner/syllabus/dev-environment.md", "---\nskill: dev-environment\nwritten: 2026-10-11\nsources: []\n---\n\n"
            "# Topics\n\n## how-programs-run | How a program runs\nlevel: 1\n- say what an interpreter does\n\n"
            "## reading-errors | Reading error messages\nneeds: [how-programs-run]\nlevel: 1\n- read a stack trace\n")
    a.write("learner/syllabus/docker.md", "---\nskill: docker\nwritten: 2026-10-11\nsources: [https://docs.docker.com/]\n---\n\n"
            "# Topics\n\n## images-containers | Images and containers\nlevel: 1\n- tell an image from a container\n\n"
            "## dockerfile | Writing a Dockerfile\nneeds: [images-containers]\nlevel: 2\n- write a Dockerfile\n\n"
            "## multi-stage | Multi-stage builds\nneeds: [dockerfile]\nlevel: 3\n- write a two-stage build\n")
    a.write("learner/syllabus/java.md", "---\nskill: java\nwritten: 2026-10-11\nsources: []\n---\n\n# Topics\n\n"
            "## classes | Classes and objects\nlevel: 1\n- write a class\n\n"
            "## packaging | Packaging a jar\nneeds: [classes]\nlevel: 2\n- build a runnable jar\n")
    for skill in ("dev-environment", "docker", "java"):
        assert "ok:" in a.cal("syllabus", "check", skill)
    a.tick(minutes=2)
    assert "locked" in a.cal("enroll", "docker", expect=2)
    a.cal("enroll", "docker", "--force")
    a.tick(minutes=1)
    a.cal("enroll", "java", "--force")
    needs = a.cal("item", "needs")
    assert "ITEMS NEEDED" in needs and "dev-environment/how-programs-run" in needs, needs
    a.make_items([(["dev-environment/how-programs-run"], "mcq", "B"), (["dev-environment/reading-errors"], "mcq", "B"),
                  (["docker/images-containers"], "mcq", "B"), (["docker/dockerfile"], "task", None),
                  (["java/classes"], "mcq", "B")])
    assert "NEXT: new" in a.cal("next")
    for topic in ("dev-environment/how-programs-run", "docker/images-containers", "java/classes"):
        a.cal("covered", topic)
        a.tick(minutes=6)
        res = a.study(topic)
        assert "CORRECT" in res, res
    a.cal("covered", "docker/dockerfile")
    a.tick(minutes=20)
    assert "CORRECT" in a.study("docker/dockerfile")
    print(a.cal("today").strip())

    section("next day: surprise recall, and Docker woven into a Java exercise")
    a.tick(days=2, hours=1)
    brief = a.cal("brief")
    assert "Due now (" in brief and "Surprise-recall candidates" in brief, brief
    print("\n".join(l for l in brief.split("\n") if l.startswith(("Due now", "  1.", "Surprise", "Next action", "Today"))))
    weave = a.cal("weave", "java")
    assert "docker/" in weave, weave
    print(weave.strip())
    need = a.cal("ask", "--topic", "java/packaging", expect=4)
    assert "embed (earlier topics" in need and "docker/" in need, need
    a.make_items([(["java/packaging", "docker/dockerfile"], "task", None)])
    a.cal("covered", "java/packaging")
    a.tick(minutes=25)
    res = a.study("java/packaging")
    assert "also credited: docker/dockerfile" in res, res
    print(res.strip().split("\n")[0], "|", res.strip().split("\n")[2])
    for _ in range(8):                                   # clear the reviews the engine serves
        nxt = a.cal("next")
        if "NEXT: review" not in nxt:
            break
        topic = re.search(r"topic: (\S+)", nxt).group(1)
        a.tick(minutes=3)
        a.study(topic)
    a.cal("workout", "45")

    section("GATE: course connected by paste and manual log; lecture, log, test")
    a.cal("gate", "enroll")
    a.cal("source", "add", "course", "--title", "GATE course", "--kind", "course", "--url", "https://example.com/c",
          "--route", "paste", "--tracks", "gate-cs,gate-da", "--note", "automated access disallowed; paste + manual log")
    lectures = [{"id": "os-%02d" % i, "title": t, "section": "Operating System", "order": i, "minutes": 55, "topics": k}
                for i, (t, k) in enumerate([
                    ("System calls and modes", ["gate.cs.operating-systems/system-calls"]),
                    ("Processes", ["gate.cs.operating-systems/processes"]),
                    ("Threads", ["gate.cs.operating-systems/threads"]),
                    ("Doubt session", [])], 1)]
    lectures.append({"id": "la-01", "title": "Eigenvalues", "section": "Linear Algebra", "order": 10, "minutes": 60,
                     "topics": ["gate.cs.linear-algebra/eigenvalues"]})
    a.write(".calamity/tmp/course.json", json.dumps(lectures))
    out = a.cal("source", "import", "course", "--file", ".calamity/tmp/course.json")
    assert "5 added" in out and "ERROR" not in out, out
    a.tick(hours=1)
    assert "ready to be tested: gate.cs.operating-systems/system-calls" in a.cal("log", "course", "os-01")
    a.cal("log", "course", "eigen")
    a.make_items([(["gate.cs.operating-systems/system-calls"], "mcq", "B"),
                  (["gate.cs.linear-algebra/eigenvalues"], "nat", "6")])
    res = a.study("gate.cs.linear-algebra/eigenvalues", answer="6")
    assert "same topic elsewhere: gate.da.linear-algebra/eigenvalues" in res and "marks: +1.00" in res, res
    res = a.study("gate.cs.operating-systems/system-calls", answer="A", err="concept")
    assert "WRONG" in res and "marks: -0.33" in res, res
    a.cal("gate", "mock", "CS", "41.67", "--source", "series, full test 1", "--sections", "GA=10,OS=4.33")
    a.cal("profile", "set", "gate.target_marks.CS", "72")
    status = a.cal("gate", "status")
    assert "CS: 11" in status and "target 72 marks" in status and "last mock 41.7" in status, status
    print("\n".join(status.split("\n")[:5]))
    print(a.cal("gate", "triage").split("\n")[2])

    section("competitive programming: Codeforces through fixtures")
    sys.path.insert(0, os.path.join(SRC, "engine"))
    from tests import test_cf
    old_now = test_cf.NOW
    test_cf.NOW = a.clock.isoformat()
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    for method, result in test_cf.fixtures().items():
        with open(os.path.join(FIX, method + ".json"), "w") as fh:
            json.dump({"status": "OK", "result": result}, fh)
    test_cf.NOW = old_now
    a.env_extra["CALAMITY_CF_FIXTURES"] = FIX
    a.cal("cf", "link", "tester")
    sync = a.cal("cf", "sync")
    assert "milestone reached: cp.rating-1200" in sync, sync
    print(sync.strip().split("\n")[0])
    a.cal("profile", "set", "cp.target_rating", "1800")
    a.cal("enroll", "cp.dp-basics", "--force")
    credit = a.cal("cf", "credit", "1503D", "--topic", "cp.dp-basics/knapsack-01")
    assert "CREDITED 1503D" in credit, credit
    rec = a.cal("cf", "recommend", "--skill", "cp.dp-basics", "--n", "3")
    assert "tags: dp" in rec, rec
    print(rec.strip().split("\n")[0])
    assert "cp.rating-1400" in a.cal("cf", "rating")

    section("notes: fragment, LaTeX section, PDF")
    frag = a.cal("notes", "fragment", "docker/dockerfile").strip()
    a.write(frag, a.read(frag) + "\nA Dockerfile is a recipe; each instruction adds a layer.\n")
    sect = a.cal("notes", "section", "docker/dockerfile").strip()
    a.write(sect, "\\section{Writing a Dockerfile}\\label{sec:docker:dockerfile}\n\n\\begin{keyidea}\nEach instruction "
            "adds a layer.\n\\end{keyidea}\n\n\\begin{lstlisting}[language=Dockerfile]\nFROM alpine:3.20\nCMD [\"echo\", \"hi\"]\n"
            "\\end{lstlisting}\n\n\\begin{recall}\n\\item What does each instruction add?\n\\end{recall}\n")
    a.cal("notes", "stamp", "docker")
    pdf = a.cal("notes", "pdf", "docker")
    print(pdf.strip())

    section("dashboards")
    print(a.cal("dash", "all", "--width", "78").strip())
    print()
    print(a.cal("stats", "week", "--days", "4").strip())

    section("sync: commit learner/, push, second laptop, concurrent study, merge")
    a.cal("rebuild")
    a.git("add", "learner")
    staged = a.git("status", "--porcelain")
    assert ".calamity" not in staged and "settings.local.json" not in staged and "main.pdf" not in staged, staged
    assert "learner/events/" in staged and "learner/PROGRESS.md" in staged and "docker-notes.pdf" not in staged, staged
    a.git("commit", "-q", "-m", "Study log: first days")
    a.git("push", "-q", "origin", "HEAD")
    b = Laptop(os.path.join(BASE, "laptop-b"), a.clock.isoformat())
    subprocess.check_call(GIT + ["clone", "-q", origin, b.path])
    brief_b = b.cal("brief")
    assert "Learner: Asha" in brief_b and "NOT ONBOARDED" not in brief_b, brief_b      # the profile travelled with the clone
    b.cal("setup", "--machine", "laptop-b")
    assert "not synced on this machine yet" in b.cal("brief")                          # Codeforces cache is per machine
    # both laptops now study without syncing in between
    a.tick(days=1)
    b.tick(days=1, hours=3)
    for lap, topic in ((a, "docker/images-containers"), (b, "java/classes")):
        lap.study(topic)
    b.cal("log", "course", "os-02")
    a.cal("observe", "likes examples before theory")
    for lap, msg in ((b, "Study log: laptop b"), (a, "Study log: laptop a")):
        lap.cal("rebuild")
        lap.git("add", "learner")
        lap.git("commit", "-q", "-m", msg)
    b.git("push", "-q", "origin", "HEAD")
    pull = a.git("pull", "--no-rebase", "--no-edit", "origin", "main", expect=None)
    conflicts = a.git("diff", "--name-only", "--diff-filter=U")
    assert conflicts.strip() == "", "merge conflicts:\n%s\n%s" % (conflicts, pull)
    assert "<<<<<<<" not in a.read("learner/PROGRESS.md")
    rebuilt = a.cal("rebuild")
    assert "0 error(s)" in rebuilt and "could not be read" not in rebuilt, rebuilt
    a.git("add", "learner")
    a.git("commit", "-q", "-m", "Rebuild after merge", expect=None)
    a.git("push", "-q", "origin", "HEAD")
    b.git("pull", "-q", "--no-rebase", "--no-edit", "origin", "main")
    b.cal("rebuild")
    assert a.read("learner/PROGRESS.md") == b.read("learner/PROGRESS.md"), "the two laptops disagree"
    files = sorted(os.listdir(os.path.join(a.path, "learner", "events")))
    print("event files:", files)
    assert any("laptop-a" in f for f in files) and any("laptop-b" in f for f in files)
    section("framework update: a clone, and a copy that began as a downloaded archive")
    s.write("framework/VERSION", "9.9.9\n")                # a later release of the framework
    s.git("commit", "-q", "-am", "release 9.9.9")
    a.git("remote", "add", "upstream", seed)                 # what /update-framework does in a clone
    a.git("fetch", "-q", "upstream", "--tags")
    assert a.git("merge-base", "HEAD", "upstream/main").strip()
    a.git("merge", "-q", "--no-edit", "upstream/main")
    assert a.read("framework/VERSION").strip() == "9.9.9"
    assert "likes examples before theory" in a.cal("observations")
    c = Laptop(os.path.join(BASE, "laptop-c"), a.clock.isoformat())
    os.makedirs(c.path)
    archive = subprocess.run(GIT + ["archive", "v" + version], cwd=seed, stdout=subprocess.PIPE, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        try:
            tar.extractall(c.path, filter="data")
        except TypeError:          # Python releases from before extraction filters existed
            tar.extractall(c.path)
    c.git("init", "-q")                                      # what /sync does for a copy that is not a clone
    c.git("add", "-A")
    c.git("commit", "-q", "-m", "Calamity framework " + version)
    for key, value in (("name", "Chandra"), ("onboarded", "true")):
        c.cal("profile", "set", key, value)
    c.cal("observe", "studies from an archive copy")
    c.git("add", "learner")
    c.git("commit", "-q", "-m", "Study log")
    c.git("remote", "add", "upstream", seed)                 # and /update-framework, step 3 onwards
    c.git("fetch", "-q", "upstream", "--tags")
    assert c.git("merge-base", "HEAD", "upstream/main", expect=None).strip() == ""
    c.git("merge", "-q", "-s", "ours", "--allow-unrelated-histories", "-m",
          "Adopt the framework history at " + version, "v" + version)
    c.git("merge", "-q", "--no-edit", "upstream/main")
    assert c.read("framework/VERSION").strip() == "9.9.9"
    assert "studies from an archive copy" in c.cal("observations")
    assert "0 problem(s)" in c.cal("doctor"), "the archive copy is not healthy after the update"
    for lap in (a, c):
        lap.cal("tree", "check")
        lap.cal("rebuild")
    print("a clone and an archive copy both took release 9.9.9; their learner data is intact")

    final = a.cal("doctor")
    assert "0 problem(s)" in final, final
    print(final.strip().split("\n")[-1])
    print(a.cal("selftest").strip().split("\n")[-1])
    print("\nEND-TO-END RUN PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        if "--keep" in sys.argv[1:]:
            print("kept: %s" % BASE)
        else:
            remove_tree(BASE)
