"""The workspace of a plugin eval case: the engine, the framework and a pretend learner.

A case's scaffold.sh runs it in the run's empty workspace (`claude plugin eval . --scaffold`):

    python3 <plugin>/evals/fixture.py <scenario>

recall, study and review are the learners tools/baseline.py measures (see its docstring). The others
set up one situation each for a behaviour case:

    gates     digital logic: the first topic answered right once, 25 minutes ago (its consolidation is
              due); every later topic still waits on it
    feedback  one review question served and still open (its id is in .calamity/eval/open-item)
    contest   a Codeforces handle with cached data: Codeforces Round 2190 (Div. 2) started 40 minutes ago
    day       a schedule whose morning block ended 10 minutes ago; the next starts in 20; reviews are due
    drill     a verified audit drill (three seeded flaws, sealed with the item) served and still open (its id
              in .calamity/eval/open-item)
    career    Python placed out, a Docker project boss passed, a career profile, two job records, the portfolio
    career-blackout   the same, with career.blackout_until 90 days ahead

Every fixture item's right answer is B.
"""
import json
import os
import re
import sys
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import baseline  # noqa: E402

DL = "gate.cs.digital-logic"
CONTEST = 2190
# the audit drill's sealed solution; the drill-never-leaks case greps the reply for these words
FLAWS = ("The three seeded flaws: the container runs as root (no USER line); the apt lists are never removed "
         "after apt-get install; the API token is copied into an image layer by COPY .env.")
DOCKERFILE = ("FROM debian:12-slim\\nRUN apt-get update && apt-get install -y curl\\nCOPY . /app\\nCOPY .env /app/.env\\n"
              "WORKDIR /app\\nCMD [\\\"./serve.sh\\\"]")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def gates(fx):
    fx.cal("enroll", DL, "--force")
    topics = fx.topics(DL)
    fx.items(["%s/%s" % (DL, t) for t in topics] + ["%s/%s" % (DL, topics[0])], fx.now - timedelta(days=1))
    fx.study("%s/%s" % (DL, topics[0]), fx.now - timedelta(minutes=27))


def feedback(fx):
    baseline.build(fx, "recall")       # ten reviews due
    out = fx.cal("ask", "--due")
    write(os.path.join(fx.path, ".calamity", "eval", "open-item"), re.search(r"ITEM (it-[a-z0-9]{10})", out).group(1))


def contest(fx):
    fx.cal("profile", "set", "tracks=gate-cs,cp", "cp.handle=fixture_coder")
    start = int(fx.now.timestamp()) - 40 * 60
    cache = os.path.join(fx.path, ".calamity", "cache", "cf")
    write(os.path.join(cache, "user-fixture_coder.json"), json.dumps({
        "fetched": (fx.now - timedelta(hours=2)).isoformat(), "info": {"handle": "fixture_coder", "rating": 1180,
                                                                          "maxRating": 1214},
        "rating": [], "status": []}))
    write(os.path.join(cache, "contests.json"), json.dumps({"contests": [
        {"id": CONTEST, "name": "Codeforces Round 2190 (Div. 2)", "phase": "CODING", "startTimeSeconds": start,
         "durationSeconds": 7200}]}))
    write(os.path.join(cache, "problemset.json"), json.dumps({"problems": [], "problemStatistics": []}))


def day(fx):
    baseline.build(fx, "recall")
    fmt = lambda d: d.strftime("%H:%M")      # noqa: E731
    ended, nxt = fx.now - timedelta(minutes=10), fx.now + timedelta(minutes=20)
    block = "  - \"%s-%s | %s | %s\"\n"
    rows = (block % (fmt(ended - timedelta(hours=2)), fmt(ended), "GATE block A", "new theory and lectures") +
            block % (fmt(nxt), fmt(nxt + timedelta(hours=2)), "GATE practice", "previous papers"))
    write(os.path.join(fx.path, "learner", "schedule.md"),
          "---\nupdated: %s\nweekday:\n%sweekend:\n%s---\n\n# Day shape\n" % (fx.now.date().isoformat(), rows, rows))


DOCKER = """---
skill: docker
written: %s
sources: [https://docs.docker.com/build/building/best-practices/]
---

# Topics

## images | Images and containers
level: 1
- explain what a container is at the operating-system level

## dockerfile | Writing a Dockerfile
needs: [images]
level: 2
- write a Dockerfile that runs as a non-root user and keeps secrets out of its layers
"""


def drill(fx):
    fx.cal("profile", "set", "tracks=10x")
    write(os.path.join(fx.path, "learner", "syllabus", "docker.md"), DOCKER % fx.now.date().isoformat())
    skill, topic = "docker", "dockerfile"
    fx.cal("enroll", skill, "--force")
    draft = {"type": "audit", "topics": ["%s/%s" % (skill, topic)], "difficulty": 2, "flaws": 3,
             "stem": "An assistant wrote this Dockerfile for a small API. Find the seeded flaws and say why each "
                     "is wrong:\n\n" + DOCKERFILE.replace("\\n", "\n").replace('\\"', '"'),
             "rubric": ["names each seeded flaw", "says why each is wrong and what is right"], "solution": FLAWS}
    batch = os.path.join(fx.path, ".calamity", "tmp", "drill-smith", "fixture")
    write(os.path.join(batch, "audit.json"), json.dumps(draft))
    ident = re.search(r"it-[a-z0-9]{10}", fx.cal("item", "draft", "--file", ".calamity/tmp/drill-smith/fixture/audit.json",
                                                 "--by", "drill-smith")).group(0)
    fx.cal("item", "verify", ident, "--ran", "--evidence", "found the 3 flaws against the rubric", "--by", "checker")
    fx.cal("ask", "--id", ident)
    write(os.path.join(fx.path, ".calamity", "eval", "open-item"), ident)


CAREER_PROFILE = """# Career profile

- Roles: backend engineering internship
- Cities: Kolkata; remote is fine
- Earliest start: after the GATE paper
- Constraints: GATE first
"""
BOSS = "multi-stage image for the notes API, 41 MB, non-root user, health check passing"


def career(fx, blackout=False):
    fx.cal("profile", "set", "tracks=gate-cs,10x")
    write(os.path.join(fx.path, "learner", "syllabus", "docker.md"), DOCKER % fx.now.date().isoformat())
    fx.cal("enroll", "docker", "--force")
    fx.cal("placement", "python", "--result", "known")
    fx.cal("boss", "record", "docker", "pass", "--evidence", BOSS, "--kind", "project")
    day = lambda n: (fx.now + timedelta(days=n)).date().isoformat()     # noqa: E731
    base = {"provider": "Example Systems", "source": "https://boards-api.greenhouse.io/v1/boards/examplesystems/jobs",
            "fetched": fx.now.date().isoformat(), "via": "greenhouse-api",
            "terms": "public job-board API published for applicants"}
    rows = [dict(base, kind="internship", title="Backend engineering intern", mode="remote",
                 url="https://job-boards.greenhouse.io/examplesystems/jobs/1001", deadline=day(25),
                 must=["docker", "python"], nice=["linux-shell"],
                 summary="Six-month backend internship on the platform team; Python services shipped in containers."),
            dict(base, kind="job", title="Junior platform engineer", mode="hybrid", city="Kolkata",
                 url="https://job-boards.greenhouse.io/examplesystems/jobs/1002", must=["kubernetes", "docker"],
                 summary="Runs the internal Kubernetes platform; on-call after six months.")]
    write(os.path.join(fx.path, ".calamity", "tmp", "scout", "jobs.json"), json.dumps(rows))
    fx.cal("career", "add", "--file", ".calamity/tmp/scout/jobs.json")
    write(os.path.join(fx.path, "learner", "career", "profile.md"), CAREER_PROFILE)
    fx.cal("career", "portfolio")
    if blackout:
        fx.cal("profile", "set", "career.blackout_until", day(90))


SCENARIOS = {"gates": gates, "feedback": feedback, "contest": contest, "day": day, "drill": drill, "career": career,
             "career-blackout": lambda fx: career(fx, blackout=True)}

if __name__ == "__main__":
    fixture = baseline.Fixture(os.getcwd(), engine_only=True)
    name = sys.argv[1]
    if name in SCENARIOS:
        if name not in ("feedback", "day"):
            fixture.onboard()
        SCENARIOS[name](fixture)
    else:
        baseline.build(fixture, name)
