#!/usr/bin/env python3
"""The live watch of a hands-on coding exercise (framework/rules/hands-on-coding.md).

Run under Claude Code's Monitor tool. Every --every seconds (30 by default) it reads the
watched files, compares their content hashes with the last poll, and prints one line per
changed file to stdout, flushed at once, so each change becomes one notification for the
tutor. A save that changes nothing (same bytes) prints nothing: the hash decides, not the
modification time.

    python3 framework/scripts/watch.py learner/work/<skill>/<exercise>/main.c
    python3 framework/scripts/watch.py learner/work/<skill>/<exercise>/ --check "gcc -fsyntax-only -Wall -Wextra learner/work/<skill>/<exercise>/main.c"

It only reads. With --check it also runs that one command after each change (time-limited)
and adds its exit status and first output line to the event; give it a command that is cheap
and writes nothing outside .calamity/tmp/ (a syntax-only compile, a build into scratch).
Standard library only; Linux, macOS and Windows.
"""
import argparse
import difflib
import hashlib
import os
import subprocess
import sys
import time

SKIP_DIRS = {".git", "__pycache__", "node_modules", "build", "dist", "target", ".venv", "venv", ".idea", ".vscode"}
SKIP_EXT = {".o", ".obj", ".exe", ".out", ".class", ".pyc", ".so", ".dll", ".a", ".bin", ".swp", ".swo", ".tmp"}
MAX_FILES = 50
MAX_BYTES = 512 * 1024


def say(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def files_under(paths):
    """The files to watch: each named file, and the source files in each named folder (one level of rules)."""
    found = []
    for path in paths:
        if os.path.isdir(path):
            for folder, dirs, names in os.walk(path):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
                for name in sorted(names):
                    if name.startswith(".") or name.endswith("~") or os.path.splitext(name)[1].lower() in SKIP_EXT:
                        continue
                    found.append(os.path.join(folder, name))
        else:
            found.append(path)          # a file that does not exist yet is watched for its creation
    return found[:MAX_FILES]


def snapshot(path):
    """(hash, lines) of a file, or None when it is missing, too big or unreadable."""
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return ("big", [])
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    text = data.decode("utf-8", "replace")
    return (hashlib.sha256(data).hexdigest(), text.splitlines())


def changed_lines(old, new):
    added = removed = 0
    for line in difflib.unified_diff(old, new, lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def first_changed_line(old, new):
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag != "equal":
            return j1 + 1
    return None


def run_check(command, timeout):
    try:
        proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "check: timed out after %ds" % timeout
    except OSError as exc:
        return "check: could not run (%s)" % exc
    out = [l.strip() for l in proc.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
    telling = [l for l in out if any(w in l.lower() for w in ("error", "warning", "fail", "traceback", "assert"))]
    head = (": " + (telling or out)[0][:160]) if out else ""
    more = (" (+%d more lines)" % (len(out) - 1)) if len(out) > 1 else ""
    return "check: exit %d%s%s" % (proc.returncode, head, more)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print one line per change to the watched files (for the Monitor tool).")
    ap.add_argument("paths", nargs="+", help="files or folders to watch")
    ap.add_argument("--every", type=float, default=30.0, help="seconds between polls (default 30)")
    ap.add_argument("--check", help="a cheap command to run after each change; its exit status joins the event")
    ap.add_argument("--timeout", type=int, default=30, help="seconds the --check command may take (default 30)")
    ap.add_argument("--minutes", type=float, default=0, help="stop on its own after this long (default: until stopped)")
    args = ap.parse_args(argv)
    every = max(1.0, args.every)

    state = {path: snapshot(path) for path in files_under(args.paths)}
    present = [p for p, s in state.items() if s is not None]
    say("%s watching %d file(s) every %ds: %s" % (time.strftime("%H:%M:%S"), len(present), every,
                                                  ", ".join(os.path.basename(p) for p in present) or "none yet"))
    deadline = time.time() + args.minutes * 60 if args.minutes > 0 else None
    try:
        while deadline is None or time.time() < deadline:
            time.sleep(every)
            events = []
            current = files_under(args.paths)
            for path in sorted(set(current) | set(state)):
                old = state.get(path)
                new = snapshot(path) if path in current else None
                name = os.path.normpath(path)
                if old is None and new is not None:
                    events.append("created %s (%d line(s))" % (name, len(new[1])))
                elif old is not None and new is None:
                    events.append("deleted %s" % name)
                elif old is not None and new is not None and old[0] != new[0]:
                    added, removed = changed_lines(old[1], new[1])
                    at = first_changed_line(old[1], new[1])
                    events.append("changed %s: +%d -%d lines from line %s (now %d)" % (
                        name, added, removed, at if at else "?", len(new[1])))
                state[path] = new
            if events:
                line = "%s %s" % (time.strftime("%H:%M:%S"), "; ".join(events))
                if args.check:
                    line += "; " + run_check(args.check, args.timeout)
                say(line)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
