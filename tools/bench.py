"""How long engine commands take on a long event log, with and without the replay snapshot.

    python3 tools/demo.py --keep            # prints the path of a six-week pretend learner
    python3 tools/bench.py PATH [--events 50000]

The learner's repository is copied to a temporary folder (PATH is never changed). Its log is
grown to about the number of events asked for by adding older copies of its own study events
with fresh ids, then each command is timed three ways: replaying the whole log
(CALAMITY_NO_CACHE=1), the first run that writes the snapshot, and a later run that starts
from it. Numbers depend on the machine; report them with the machine they came from.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "engine", "calamity.py")
GROWN = ("attempt", "shown", "covered", "src_progress", "activity", "note")


def grow(root, target):
    """Add older copies of the study events until the log holds about `target` events."""
    paths = sorted(glob.glob(os.path.join(root, "learner", "events", "*.jsonl")))
    events = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            events += [json.loads(line) for line in fh if line.strip()]
    copyable = [e for e in events if e["t"] in GROWN]
    span = max(1, (datetime.fromisoformat(max(e["ts"] for e in events))
                   - datetime.fromisoformat(min(e["ts"] for e in events))).days + 1)
    copies = max(0, (target - len(events) + len(copyable) - 1) // max(1, len(copyable)))
    out = {}
    for c in range(1, copies + 1):
        for e in copyable:
            e2 = dict(e)
            when = datetime.fromisoformat(e["ts"]) - timedelta(days=span * c)
            e2["ts"] = when.isoformat(timespec="milliseconds")
            e2["id"] = "%s-c%d" % (e["id"], c)
            e2.pop("k", None)
            e2["q"] = e.get("q", 0) - c * 10 ** 12
            out.setdefault(when.strftime("%Y-%m"), []).append(e2)
    for month, rows in out.items():
        with open(os.path.join(root, "learner", "events", "%s.older.jsonl" % month), "w", encoding="utf-8") as fh:
            fh.write("".join(json.dumps(e, separators=(",", ":")) + "\n" for e in rows))
    return len(events) + sum(len(v) for v in out.values()), max(e["ts"] for e in events)


def timed(root, now, args, cache=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
    env.update(CALAMITY_ROOT=root, CALAMITY_NOW=now)
    if not cache:
        env["CALAMITY_NO_CACHE"] = "1"
    start = time.perf_counter()
    subprocess.run([sys.executable, SCRIPT] + args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - start


def main():
    ap = argparse.ArgumentParser(description="Time engine commands on a long log.")
    ap.add_argument("root", help="a learner repository (for example from tools/demo.py --keep)")
    ap.add_argument("--events", type=int, default=50000)
    args = ap.parse_args()
    work = tempfile.mkdtemp(prefix="calamity-bench-")
    try:
        root = os.path.join(work, "learner-repo")
        shutil.copytree(args.root, root, ignore=shutil.ignore_patterns("cache"))
        if not os.path.isdir(os.path.join(root, "framework")):
            shutil.copytree(os.path.join(REPO, "framework"), os.path.join(root, "framework"))
        total, last = grow(root, args.events)
        now = (datetime.fromisoformat(last) + timedelta(hours=1)).isoformat()
        print("log: %d events; Python %s on %s" % (total, sys.version.split()[0], sys.platform))
        print("%-22s %10s %12s %12s" % ("command", "full replay", "first run", "snapshot"))
        for cmd in (["today"], ["brief"], ["next"], ["dash"], ["dash", "queue"], ["statusline"]):
            full = timed(root, now, cmd, cache=False)
            cache = os.path.join(root, ".calamity", "cache")
            shutil.rmtree(cache, ignore_errors=True)
            first = timed(root, now, cmd)
            warm = timed(root, now, cmd)
            print("%-22s %9.2fs %11.2fs %11.2fs" % (" ".join(cmd), full, first, warm))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
