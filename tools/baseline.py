"""Token baselines: scripted study sessions in a throwaway copy of this checkout, measured from their transcripts.

    python3 tools/baseline.py [--scenario recall|study|review|all] [--model sonnet] [--effort LEVEL] [--keep] [--json]

Each scenario builds a pretend learner through the engine in a fresh copy of the working tree
(with the session-start hook and key guard installed, as onboarding leaves them), runs Claude Code
headless there (`claude -p`, stream-json in and out, one session), answers as a scripted learner,
and reads the session's transcript with tools/tokens.py:

  recall   "/recall" with ten reviews due across two skills; every answer is B, and B is right
  study    "/study gate.cs.digital-logic" with nothing due: two new topics taught and tested
  review   "/coach" over a week of recorded study and two workouts

It spends plan usage (one session per scenario, a few million mostly cached input tokens in all),
so it is run by hand, never in CI. Numbers move with the model and with Claude Code itself:
compare runs made with the same --model on the same Claude Code version. The scripted replies
are crude on purpose; the point is the same session each time, not a realistic learner.
docs/maintainers/token-baseline.md records the results. Standard library only.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tokens  # noqa: E402

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_FORMS = "Bash(calamity *) Bash(python3 engine/calamity.py *)"
OPTIONS = re.compile(r"(?m)^\s*(?:\*\*)?\(?[A-D][).:](?:\*\*)?\s+\S")      # a question with lettered options
RECALL = [("gate.cs.digital-logic", t) for t in ("boolean-algebra", "minimization-kmap", "minimization-tabular",
                                                   "combinational-circuits", "sequential-circuits")] + \
         [("gate.cs.operating-systems", None)]  # its first five topics, read from the tree


class Fixture:
    """A copy of a working tree (this one, or --source) with a pretend learner, driven through the engine. With
    `engine_only` the copy is just engine/ and framework/ (the plugin evals' workspaces: the plugin brings the rest)."""

    def __init__(self, path, engine_only=False, source=SRC):
        self.path = path
        ignore = shutil.ignore_patterns(".git", ".calamity", "__pycache__", "*.pyc", "settings.local.json", "results")
        for part in (("engine", "framework") if engine_only else ("",)):
            shutil.copytree(os.path.join(source, part), os.path.join(path, part), ignore=ignore, dirs_exist_ok=True)
        learner = os.path.join(self.path, "learner")
        for entry in os.listdir(learner) if os.path.isdir(learner) else ():  # no learner of its own
            if entry != "README.md":
                full = os.path.join(learner, entry)
                shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "framework"]):
            subprocess.check_call(["git", "-c", "user.name=Baseline", "-c", "user.email=baseline@example.invalid",
                                   "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"] + args, cwd=self.path,
                                  stdout=subprocess.DEVNULL)
        self.now = datetime.now().astimezone().replace(microsecond=0)

    def cal(self, *args, at=None, stdin=None):
        env = dict(os.environ, CALAMITY_NOW=(at or self.now).isoformat())
        env.pop("CALAMITY_ROOT", None)
        proc = subprocess.run([sys.executable, os.path.join("engine", "calamity.py")] + [str(a) for a in args],
                              cwd=self.path, env=env, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.stdout.decode("utf-8", "replace")
        if proc.returncode not in (0, 3):
            raise SystemExit("fixture: calamity %s -> %d\n%s" % (" ".join(map(str, args)), proc.returncode, out))
        return out

    def onboard(self):
        print(self.cal("setup", "--machine", "baseline", "--hook").strip().split("\n")[-2])
        sleep = (self.now + timedelta(hours=8)).strftime("%H:00")      # far from now and from every fixture time
        wake = (self.now + timedelta(hours=12)).strftime("%H:00")
        self.cal("profile", "set", "name=Baseline", "tracks=gate-cs", "mode.default=mastery", "sleep.start=" + sleep,
                 "sleep.end=" + wake, "onboarded=true")

    def topics(self, skill):
        out = self.cal("tree", "show", skill)
        return re.findall(r"(?m)^([a-z0-9][a-z0-9-]+)\s{2,}.*\snew\b", out)

    def items(self, keys, at):
        """One verified multiple-choice item per topic key (B is right), written and checked as the agents would."""
        drafts = [{"type": "mcq", "topics": [key], "difficulty": 2,
                   "stem": "Fixture question %d on %s: which statement holds?" % (n, key.split("/")[1].replace("-", " ")),
                   "options": ["a plausible slip about it", "the statement that holds", "a common misconception",
                               "an unrelated claim"],
                   "answer": "B", "solution": "B holds; the others are the usual mistakes about this topic.",
                   "expect_s": 60} for n, key in enumerate(keys, 1)]
        batch = os.path.join(self.path, ".calamity", "tmp", "examiner", "fixture")
        os.makedirs(batch, exist_ok=True)
        with open(os.path.join(batch, "drafts.json"), "w", encoding="utf-8") as fh:
            json.dump(drafts, fh)
        out = self.cal("item", "import", "--file", ".calamity/tmp/examiner/fixture/drafts.json", "--by", "examiner", at=at)
        ids = re.findall(r"it-[a-z0-9]{10}", out)
        self.cal("item", "verify", *["%s=B" % i for i in ids], "--by", "checker", at=at)
        return ids

    def study(self, key, at):
        """Teach and answer one topic in the past (right first time), so it comes back as a review."""
        out = self.cal("ask", "--topic", key, "--taught", at=at)
        ident = re.search(r"ITEM (it-[a-z0-9]{10})", out).group(1)
        self.cal("answer", ident, "--answer", "B", "--seconds", "70", at=at + timedelta(minutes=2))


def build(fixture, scenario):
    fixture.onboard()
    past = fixture.now - timedelta(days=12)
    if scenario == "recall":
        keys = []
        for skill, topic in RECALL:
            fixture.cal("enroll", skill, "--force")
            keys += ["%s/%s" % (skill, topic)] if topic else ["%s/%s" % (skill, t) for t in fixture.topics(skill)[:5]]
        fixture.items(keys, past)
        for n, key in enumerate(keys):
            fixture.study(key, past + timedelta(minutes=5 * n))
        return "/recall", 14
    if scenario == "study":
        skill = "gate.cs.digital-logic"
        fixture.cal("enroll", skill, "--force")
        fixture.items(["%s/%s" % (skill, t) for t in fixture.topics(skill)], past)  # the whole skill: no stocking
        return "/study %s" % skill, 18
    # review: a week of study at different hours, two workouts, then the weekly review
    skill = "gate.cs.digital-logic"
    fixture.cal("enroll", skill, "--force")
    topics = fixture.topics(skill)
    fixture.items(["%s/%s" % (skill, t) for t in topics], past)
    for day, (topic, shift) in enumerate(zip(topics[:6], (-3, 2, -5, 3, -2, 1)), start=1):
        when = fixture.now - timedelta(days=8 - day) + timedelta(hours=shift)   # different hours, never in the sleep window
        fixture.study("%s/%s" % (skill, topic), when)
        if day in (2, 5):
            fixture.cal("workout", "45", "--note", "evening lifting", at=when + timedelta(hours=1))
    return "/coach", 4


PLAIN = re.compile(r"^python3 engine/calamity\.py [^|;&<>`$()]*$")         # the pre-approved form, nothing around it
LEAK = re.compile(r"B holds|usual mistakes about this topic", re.I)      # the fixture items' solution


def checks(path):
    """What the session did, to tell a cheaper session from one that stopped doing its job: engine calls and how
    many were not in the plain pre-approved form, answers recorded, topics taught, and whether a fixture key
    showed in the conversation before the first answer was recorded."""
    out = {"engine_calls": 0, "not_plain": 0, "answers": 0, "taught": 0, "key_before_answer": False}
    for entry in tokens._lines(path):
        content = (entry.get("message") or {}).get("content") if entry.get("type") == "assistant" else None
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "text" and not out["answers"] and LEAK.search(block.get("text", "")):
                out["key_before_answer"] = True
            command = str((block.get("input") or {}).get("command", "")) if block.get("type") == "tool_use" else ""
            if "engine/calamity.py" in command:
                out["engine_calls"] += 1
                out["not_plain"] += 0 if PLAIN.match(command.strip()) else 1
                out["answers"] += 1 if re.search(r"calamity\.py answer\b", command) else 0
                out["taught"] += 1 if "--taught" in command else 0
    return out


def reply(scenario, text, state):
    """The scripted learner's next message, or None to end the session."""
    state["turns"] += 1
    if state["turns"] > state["cap"]:
        return None
    if scenario == "review":
        return "That sounds right. Apply it." if state["turns"] == 1 and "?" in text else None
    if OPTIONS.search(text):
        state["answers"] += 1
        return "B"
    if scenario == "recall":
        return None                                             # no question left: the round is over
    if state["taught"] >= 2 and state["answers"] >= 2:
        return None
    return "I follow. Please go on." if text.rstrip().endswith("?") or state["turns"] < state["cap"] else None


def run(fixture, scenario, opening, cap, model, effort):
    cmd = ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
           "--model", model, "--permission-mode", "acceptEdits", "--allowedTools", ENGINE_FORMS]
    if effort:
        cmd += ["--effort", effort]
    proc = subprocess.Popen(cmd, cwd=fixture.path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    state = {"turns": 0, "answers": 0, "taught": 0, "cap": cap}
    session = None

    def send(text):
        proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user",
                                                                  "content": [{"type": "text", "text": text}]}}) + "\n")
        proc.stdin.flush()

    send(opening)
    for line in proc.stdout:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        session = event.get("session_id") or session
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and "--taught" in str(block.get("input", {}).get("command", "")):
                    state["taught"] += 1
        if event.get("type") == "result":
            nxt = reply(scenario, event.get("result") or "", state)
            print("  turn %d done%s" % (state["turns"], "" if nxt else ": end of the session"))
            if nxt is None:
                break
            send(nxt)
    proc.stdin.close()
    proc.wait(timeout=120)
    return session


def main(argv=None):
    p = argparse.ArgumentParser(description="Scripted study sessions measured from their transcripts.")
    p.add_argument("--scenario", default="all", choices=("recall", "study", "review", "all"))
    p.add_argument("--model", default="sonnet")
    p.add_argument("--source", default=SRC, help="the checkout to copy and measure (default: this one)")
    p.add_argument("--effort")
    p.add_argument("--keep", action="store_true", help="keep the copies and their transcripts")
    p.add_argument("--json", action="store_true")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="build the learners and print their briefs only")
    a = p.parse_args(argv)
    if not shutil.which("claude"):
        raise SystemExit("needs Claude Code (`claude`) on PATH")
    version = subprocess.run(["claude", "--version"], stdout=subprocess.PIPE, text=True).stdout.strip()
    base = tempfile.mkdtemp(prefix="calamity-baseline-")
    results = {}
    try:
        for scenario in (("recall", "study", "review") if a.scenario == "all" else (a.scenario,)):
            print("%s: building the learner" % scenario)
            fixture = Fixture(os.path.join(base, scenario), source=os.path.abspath(a.source))
            opening, cap = build(fixture, scenario)
            print("%s: session (%s)" % (scenario, opening))
            session = None if a.dry_run else run(fixture, scenario, opening, cap, a.model, a.effort)
            folder = tokens.transcripts_dir(fixture.path)
            path = os.path.join(folder, "%s.jsonl" % session)
            if a.dry_run:
                print(fixture.cal("brief"))
                continue
            transcript = tokens.read_session(path)
            results[scenario] = dict(tokens.summary(transcript), per_skill=tokens.by([transcript], "skill"),
                                     per_agent=tokens.by([transcript], "agent"), checks=checks(path))
            if not a.keep:
                shutil.rmtree(folder, ignore_errors=True)
    finally:
        if a.keep:
            print("kept: %s" % base)
        else:
            shutil.rmtree(base, ignore_errors=True)
    meta = {"claude": version, "model": a.model, "effort": a.effort or "default",
            "date": datetime.now().astimezone().strftime("%Y-%m-%d")}
    if a.json:
        print(json.dumps({"meta": meta, "scenarios": results}, indent=1, default=list))
        return 0
    print("\n%s · model %s · effort %s · %s" % (meta["claude"], meta["model"], meta["effort"], meta["date"]))
    rows = [[name, r["turns"], r["requests"], len(r["agents"]), tokens.k(r["first_context"]), tokens.k(r["max_context"]),
             tokens.k(r["context"]), tokens.k(r["output"]), tokens.k(r["weighted"])] for name, r in results.items()]
    print(tokens.table(rows, ["scenario", "turns", "requests", "agents", "first ctx", "max ctx", "context", "output",
                              "weighted in"]))
    rows = [[name, c["engine_calls"], c["not_plain"], c["answers"], c["taught"], "yes" if c["key_before_answer"] else "no"]
            for name, c in ((n, r["checks"]) for n, r in results.items())]
    print("\n" + tokens.table(rows, ["scenario", "engine calls", "not plain", "answers", "taught", "key shown early"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
