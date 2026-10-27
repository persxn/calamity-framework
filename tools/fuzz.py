"""Random command sequences against the engine: nothing may crash, and replay must be exact.

    python3 tools/fuzz.py [--first 1] [--runs 20] [--steps 60] [--no-shuffle]

Each run is a fresh learner in a temporary folder with a small skill tree, driven by a seeded
random sequence of what learners and agents do (enrol, items, answers, lectures, placement,
disputes, renames of focus, configuration changes, boss attempts, tests, other laptops' events
merged in, a damaged or deleted replay snapshot). After every step:

- every read-only view must work: a traceback or an exit code outside 0-4 is a failure;
- the state served through the replay snapshot must equal a full replay of the log;
- a few invariants must hold (reviews done never exceed reviews due, and so on).

At the end of a run the same events are dealt out to other files in another order, with some
duplicated, and the replayed state must not change (`--no-shuffle` skips this). Seeds make a
failure repeatable: `--first <seed> --runs 1`.
"""
import argparse
import json
import os
import random
import re
import sys
import traceback
from datetime import datetime, timedelta

ENGINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
sys.path.insert(0, ENGINE)
from cal.state import State  # noqa: E402
from cal.store import Repo  # noqa: E402
from cal.tree import Tree  # noqa: E402
from tests.helpers import Sandbox, write  # noqa: E402

TOPICS = ["shell/pipes", "shell/perms", "docker/images", "docker/dockerfile", "docker/multi-stage", "java/classes",
          "java/collections", "java/streams", "api/rest", "cp.bs/on-answer", "cp.dp/knapsack", "cp.dp/lis",
          "gate.ga/series", "gate.ga/ratios", "gate.cs.la/matrices", "gate.cs.la/eigen", "gate.cs.os/deadlock",
          "gate.cs.os/scheduling", "gate.cs.os/paging", "gate.da.la/matrices", "gate.da.la/svd"]
SKILLS = sorted({t.split("/")[0] for t in TOPICS}) + ["python", "capstone", "cp.rating-1200"]
VIEWS = (["brief"], ["today"], ["next"], ["dash", "all"], ["dash", "roadmap", "--all-tracks"], ["dash", "queue"],
         ["dash", "week"], ["item", "needs"], ["tree", "suggest"], ["stats", "patterns"], ["stats", "flags"],
         ["statusline"], ["remind", "check", "--always"], ["gate", "status"], ["gate", "triage"], ["source", "status"],
         ["tree", "path", "capstone"], ["boss", "status"], ["observations"])
CATALOGUE = [
    {"id": "l1", "title": "Intro", "order": 1, "minutes": 30, "topics": []},
    {"id": "l2", "title": "Scheduling", "order": 2, "minutes": 50, "topics": ["gate.cs.os/scheduling"]},
    {"id": "l3", "title": "Deadlock", "order": 3, "minutes": 50, "topics": ["gate.cs.os/deadlock"]},
    {"id": "l4", "title": "Matrices", "order": 4, "minutes": 40, "topics": ["gate.cs.la/matrices"]},
    {"id": "l5", "title": "Doubts", "order": 5, "minutes": 20, "topics": []},
    {"id": "l6", "title": "Paging", "order": 6, "minutes": 60, "topics": ["gate.cs.os/paging"]},
]


class Crash(Exception):
    pass


def run(sb, *args):
    try:
        out = sb.run(*args, expect=None)
    except Exception:  # the engine raised instead of reporting an error
        raise Crash("%r raised:\n%s" % (args, traceback.format_exc()))
    if sb.code not in (0, 1, 2, 3, 4) or "Traceback" in sb.err or "Traceback" in out:
        raise Crash("%r exited %s\nstdout: %s\nstderr: %s" % (args, sb.code, out[-1500:], sb.err[-3000:]))
    return out


snapshot_used = [0]


def one_run(seed, steps, shuffle=True):
    rng = random.Random(seed)
    sb = Sandbox()
    items, log = {}, []
    try:
        run(sb, "profile", "set", "name", "Fuzz")
        if rng.random() < 0.8:
            run(sb, "profile", "set", "gate.year", "2027")
            run(sb, "profile", "set", "gate.papers", rng.choice(["CS", "DA", "CS,DA"]))
            run(sb, "profile", "set", "tracks", "dev,cp,gate-cs,gate-da")
        if rng.random() < 0.5:
            run(sb, "profile", "set", "sleep.start", rng.choice(["23:30", "01:00", "22:00"]))
            run(sb, "profile", "set", "sleep.end", rng.choice(["07:00", "08:30"]))
        run(sb, "profile", "set", "onboarded", "true")
        sourced = False
        practiced = False
        for step in range(steps):
            kind = rng.choice(["enroll", "enroll", "item", "item", "item", "study", "study", "study", "study", "study",
                               "covered", "advance", "advance", "advance", "quick", "placement", "pause", "resume",
                               "log", "log", "source", "mistake", "dispute", "focus", "cfg", "next", "next", "boss",
                               "ptest", "drop", "observe", "workout", "unenroll", "test", "weave", "mock", "rename",
                               "merge", "cache", "cache", "practice", "practice", "feedback"])
            log.append(kind)
            if kind == "enroll":
                args = ["enroll", rng.choice(SKILLS)]
                if rng.random() < 0.4:
                    args.append("--force")
                if rng.random() < 0.3:
                    args += ["--mode", "brushup"]
                run(sb, *args)
            elif kind == "item":
                topic = rng.choice(TOPICS)
                also = [t for t in rng.sample(TOPICS, 2) if t != topic] if rng.random() < 0.2 else []
                hands_on = rng.random() < 0.2 and not topic.startswith("gate")
                try:
                    ident = sb.item(topic, kind="task" if hands_on else "mcq", **({"also": also} if also else {}))
                except AssertionError as exc:
                    if "Traceback" in str(exc):
                        raise Crash(str(exc))
                    continue
                items[ident] = (topic, hands_on)
            elif kind == "study":
                topic = rng.choice(TOPICS)
                out = run(sb, *rng.choice([["ask", "--topic", topic], ["ask"], ["ask", "--due"], ["ask", "--skill", topic.split("/")[0]]]))
                m = re.search(r"ITEM (it-[a-z0-9]{10})", out)
                if not m:
                    continue
                ident = m.group(1)
                sb.advance(seconds=rng.randint(5, 400))
                flags = []
                if rng.random() < 0.2:
                    flags += ["--hints", str(rng.randint(1, 3))]
                if rng.random() < 0.15:
                    flags += ["--kind", "placement"]
                if items.get(ident, ("", False))[1]:
                    res = rng.choice(["pass", "pass", "fail"])
                    extra = ["--err", "syntax"] if (res == "fail" and rng.random() < 0.5) else []
                    if res == "fail" and rng.random() < 0.3:
                        extra += ["--blame", rng.choice(TOPICS)]
                    run(sb, "answer", ident, "--result", res, "--evidence", "ran it", *flags, *extra)
                else:
                    given = rng.choice(["B", "B", "B", "A", "C"])
                    extra = ["--err", rng.choice(["concept", "careless", "memory"])] if rng.random() < 0.3 else []
                    run(sb, "answer", ident, "--answer", given, *flags, *extra)
            elif kind == "covered":
                run(sb, "covered", rng.choice(TOPICS))
            elif kind == "advance":
                sb.advance(minutes=rng.choice([3, 11, 45, 240, 600, 1440, 2880, 10080, 43200]))
            elif kind == "quick":
                run(sb, "quick", rng.choice(TOPICS), rng.choice(["pass", "fail"]))
            elif kind == "placement":
                skill = rng.choice(SKILLS)
                ids = [t.split("/")[1] for t in TOPICS if t.split("/")[0] == skill]
                if rng.random() < 0.4 or not ids:
                    run(sb, "placement", skill, "--result", "known")
                else:
                    known = rng.sample(ids, rng.randint(1, len(ids)))
                    gaps = [i for i in ids if i not in known]
                    args = ["placement", skill, "--known", ",".join(known)]
                    if gaps:
                        args += ["--gaps", ",".join(gaps)]
                    run(sb, *args)
            elif kind in ("pause", "resume", "unenroll"):
                run(sb, kind, rng.choice(SKILLS))
            elif kind == "source":
                if not sourced:
                    run(sb, "source", "add", "course", "--title", "Course", "--route", "paste", "--tracks", "gate-cs")
                    path = sb.path(".calamity", "tmp", "c.json")
                    write(path, json.dumps(CATALOGUE))
                    run(sb, "source", "import", "course", "--file", path)
                    sourced = True
            elif kind == "log":
                if sourced:
                    args = ["log", "course", rng.choice(["l1", "l2", "l3", "l4", "l5", "l6", "2", "paging"])]
                    if rng.random() < 0.2:
                        args.append("--upto")
                    elif rng.random() < 0.1:
                        args.append("--undo")
                    run(sb, *args)
            elif kind == "practice":
                if not practiced:
                    run(sb, "practice", "add", "pyq", "--title", "Papers", "--items", "30",
                        "--key", rng.choice(["official", "none"]))
                    path = sb.path(".calamity", "tmp", "p.json")
                    write(path, json.dumps([{"from": 1, "to": 15, "topics": ["gate.cs.os/scheduling"], "pages": "4"},
                                            {"from": 10, "to": 30, "topics": ["gate.cs.os/deadlock"]}]))
                    run(sb, "practice", "map", "pyq", "--file", path)
                    practiced = True
                else:
                    lo = rng.randint(1, 30)
                    run(sb, "practice", "log", "pyq", "%d-%d" % (lo, min(30, lo + rng.randint(0, 4))),
                        rng.choice(["solved", "solved", "wrong", "guessed", "skipped"]))
            elif kind == "feedback":
                run(sb, "feedback", rng.choice(["pace=slow", "depth=more", "clarity=low", "pace=ok"]))
            elif kind == "mistake":
                if items:
                    run(sb, "mistake", rng.choice(sorted(items)), rng.choice(["concept", "careless", "time"]))
            elif kind == "dispute":
                if items and rng.random() < 0.5:
                    args = ["item", rng.choice(["dispute", "reject", "restore"]), rng.choice(sorted(items))]
                    if args[1] != "restore":
                        args += ["--reason", "fuzz"]
                    if args[1] == "dispute" and rng.random() < 0.5:
                        args.append("--void")
                    run(sb, *args)
            elif kind == "focus":
                if rng.random() < 0.3:
                    run(sb, "profile", "unset", "focus")
                else:
                    run(sb, "profile", "set", "focus", rng.choice(["gate", "dev", "java", "cp", "gate-cs", "docker,java", "nope"]))
            elif kind == "cfg":
                key, values = rng.choice([("cfg.new_per_day", ["0", "1", "3", "8"]), ("cfg.lectures_per_day", ["0", "1", "3"]),
                                          ("cfg.fuzz", ["true", "false"]), ("gate.exam_date.CS", ["2026-03-20", "2027-02-07"])])
                run(sb, "profile", "set", key, rng.choice(values))
            elif kind == "next":
                run(sb, "next", *rng.choice([[], ["--skill", rng.choice(SKILLS)], ["--skill", rng.choice(SKILLS), "--only"]]))
            elif kind == "boss":
                run(sb, "boss", "record", rng.choice(SKILLS), rng.choice(["pass", "fail"]), "--evidence", "fuzz")
            elif kind == "ptest":
                run(sb, "tree", rng.choice(["show", "path"]), rng.choice(SKILLS))
            elif kind == "drop":
                skill = rng.choice(SKILLS)
                run(sb, "tree", rng.choice(["drop", "restore"]), skill, *(["--yes"] if rng.random() < 0.5 else []))
            elif kind == "observe":
                run(sb, "observe", "something was noticed", *(["--tag", "coach", "--pattern", "zero-days"] if rng.random() < 0.5 else []))
            elif kind == "workout":
                run(sb, "workout", str(rng.randint(10, 90)))
            elif kind == "test":
                out = run(sb, "test", "build", "--skills", ",".join(rng.sample(SKILLS, 2)), "--n", str(rng.randint(1, 4)))
                m = re.search(r"TEST (t-[a-z0-9]+)", out)
                if m:
                    for ident in re.findall(r"\d+\. (it-[a-z0-9]{10})", out):
                        if rng.random() < 0.8:
                            run(sb, "ask", "--id", ident, "--test", m.group(1))
                            sb.advance(seconds=40)
                            if items.get(ident, ("", False))[1]:
                                run(sb, "answer", ident, "--result", "pass", "--evidence", "x")
                            else:
                                run(sb, "answer", ident, "--answer", rng.choice(["A", "B"]))
                    run(sb, "test", "finish", m.group(1))
            elif kind == "weave":
                run(sb, "weave", rng.choice(SKILLS))
            elif kind == "mock":
                run(sb, "gate", "mock", rng.choice(["CS", "DA"]), str(rng.randint(10, 80)), "--source", "fuzz series")
            elif kind == "rename":
                pass
            elif kind == "merge":
                # another laptop's events arrive after a sync: copies of earlier events with new ids,
                # some dated before everything this laptop has, some in between, some later
                events_dir = sb.path("learner", "events")
                names = sorted(os.listdir(events_dir)) if os.path.isdir(events_dir) else []
                pool = []
                for name in names:
                    with open(os.path.join(events_dir, name), "r", encoding="utf-8") as fh:
                        pool += [l for l in fh.read().split("\n") if l.strip()]
                if pool:
                    out_lines = []
                    for _ in range(rng.randint(1, 4)):
                        e = json.loads(rng.choice(pool))
                        if e.get("t") in ("errtag", "void"):
                            continue
                        e["id"] = "merged%06d" % rng.randint(0, 999999)
                        e["m"] = "laptop-b"
                        e.pop("k", None)
                        shift = rng.choice([-30, -2, 0, 1, 5])
                        e["ts"] = (datetime.fromisoformat(e["ts"]) + timedelta(days=shift)).isoformat(timespec="milliseconds")
                        out_lines.append(json.dumps(e))
                    with open(os.path.join(events_dir, "2026-02.laptop-b.jsonl"), "a", encoding="utf-8") as fh:
                        fh.write("".join(l + "\n" for l in out_lines))
            elif kind == "cache":
                cache = sb.path(".calamity", "cache", "replay.json")
                if os.path.exists(cache):
                    what = rng.choice(["delete", "garbage", "truncate", "keep"])
                    if what == "delete":
                        os.remove(cache)
                    elif what == "garbage":
                        write(cache, "{\"format\": 1, \"key\": 7}")
                    elif what == "truncate":
                        with open(cache, "r", encoding="utf-8") as fh:
                            text = fh.read()
                        write(cache, text[: len(text) // 2])
            for view in VIEWS:
                run(sb, *view)
            # invariants
            state = sb.state()
            full = State(Repo(sb.root), Tree(Repo(sb.root)), use_cache=False)
            if state.fingerprint() != full.fingerprint():
                raise AssertionError("snapshot replay differs from a full replay (%s) after %s" % (state.cache_info, log[-3:]))
            snapshot_used[0] += state.cache_info.startswith("snapshot + ")
            n = state.today_numbers(sb.clock)
            assert n["due_done"] <= n["due_total"], n
            assert all(ts.card is not None for _, ts in state.scheduled_topics())
            if step % 10 == 9:
                out = run(sb, "rebuild")
                assert "wrote learner/PROGRESS.md" in out, out
                run(sb, "doctor")
        if shuffle:
            # the same events dealt out to other files in another order must give the same state
            import shutil
            from tests.test_replay import summary
            reference = summary(sb.root)
            events_dir = sb.path("learner", "events")
            lines = []
            for name in sorted(os.listdir(events_dir)):
                with open(os.path.join(events_dir, name), "r", encoding="utf-8") as fh:
                    lines += [line for line in fh.read().split("\n") if line.strip()]
            for attempt in range(2):
                other = Sandbox()
                try:
                    for sub in ("items", "syllabus", "tree", "sources"):
                        if os.path.isdir(sb.path("learner", sub)):
                            shutil.copytree(sb.path("learner", sub), other.path("learner", sub))
                    shutil.copyfile(sb.path("learner", "profile.md"), other.path("learner", "profile.md"))
                    shuffled = list(lines)
                    rng.shuffle(shuffled)
                    names = ["2026-03.a.jsonl", "2026-03.b.jsonl", "2027-01.c.jsonl"]
                    buckets = {n: [] for n in names}
                    for line in shuffled:
                        buckets[rng.choice(names)].append(line)
                        if rng.random() < 0.1:
                            buckets[rng.choice(names)].append(line)
                    for name, content in buckets.items():
                        write(other.path("learner", "events", name), "\n".join(content) + "\n")
                    got = summary(other.root)
                    if got != reference:
                        diff = [k for k in reference if reference[k] != got[k]]
                        detail = ""
                        if "topics" in diff:
                            for key in reference["topics"]:
                                if reference["topics"][key] != got["topics"].get(key):
                                    detail = "%s: %r vs %r" % (key, reference["topics"][key], got["topics"].get(key))
                                    break
                        raise AssertionError("replay differs in %s %s" % (diff, detail))
                finally:
                    other.close()
        return None
    except (Crash, AssertionError) as exc:
        return "seed %d after %s\n%s" % (seed, log[-6:], exc if isinstance(exc, Crash) else traceback.format_exc())
    finally:
        sb.close()


def main():
    ap = argparse.ArgumentParser(description="Random command sequences against the engine.")
    ap.add_argument("--first", type=int, default=1, help="first seed")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--no-shuffle", dest="shuffle", action="store_false",
                    help="skip replaying each run's events from shuffled files")
    args = ap.parse_args()
    first, count, steps = args.first, args.runs, args.steps
    bad = 0
    for seed in range(first, first + count):
        problem = one_run(seed, steps, args.shuffle)
        if problem:
            bad += 1
            print("FAIL", problem[:6000])
            if bad >= 3:
                break
    print("runs: %d, failures: %d, states served from the snapshot: %d" % (count, bad, snapshot_used[0]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
