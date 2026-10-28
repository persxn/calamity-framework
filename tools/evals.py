"""Run the behaviour evals (evals/) on this machine, on the Claude account Claude Code is logged into.

    python3 tools/evals.py                  the cases this branch touches (against origin/main)
    python3 tools/evals.py --all            every case
    python3 tools/evals.py --case NAME ...  the cases named (a glob works: 'career-*')
    python3 tools/evals.py --dry-run        say which cases would run, and run nothing

A branch touches a case when it changes the case's own folder; it touches every case when it changes
what the tutor reads or how the cases are set up (.claude/, the plugin manifest, framework/rules/,
framework/method*.md, evals/fixture.py, tools/baseline.py). Engine changes run no case by themselves:
when one changes what the tutor reads (an item's display, a next action), run --all.

Each case runs once (--runs) with Sonnet as model and judge (--model), with the engine's command and the
web tools granted, through `claude plugin eval`. No token or secret is involved: it is your own logged-in
Claude Code, and every case spends plan usage (about $0.07-0.15 a case with Sonnet, measured 2026-10-28).
Results go to evals/results/ (ignored by git); the summary names each failing grader with its reason.
Exit 0 when every case passed, 1 when one did not, 2 when nothing could run. Standard library only.
"""
import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS = os.path.join(ROOT, "evals")
# Changes that can move every case: what the tutor reads, and how the cases are set up.
BROAD = (".claude/", ".claude-plugin/", "framework/rules/", "framework/method.md", "framework/method-teaching.md",
         "evals/fixture.py", "tools/baseline.py")
ALLOW = ["Bash(python3 engine/calamity.py *)", "WebFetch", "WebSearch"]


def all_cases() -> list:
    return sorted(d for d in os.listdir(EVALS) if os.path.isfile(os.path.join(EVALS, d, "prompt.md")))


def select(changed, cases) -> list:
    """The cases a set of changed paths (relative, with /) touches."""
    picked = set()
    for path in changed:
        if path.startswith(BROAD):
            return list(cases)
        parts = path.split("/")
        if len(parts) > 2 and parts[0] == "evals" and parts[1] in cases:
            picked.add(parts[1])
    return [c for c in cases if c in picked]


def changed_paths(base: str) -> list:
    def git(*args):
        proc = subprocess.run(["git"] + list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise SystemExit("git %s failed: %s" % (" ".join(args), proc.stderr.decode("utf-8", "replace").strip()))
        return [l for l in proc.stdout.decode("utf-8", "replace").splitlines() if l.strip()]

    paths = git("diff", "--name-only", "%s...HEAD" % base)
    paths += git("diff", "--name-only", "HEAD")                       # not committed yet
    paths += git("ls-files", "--others", "--exclude-standard")         # new files
    return sorted(set(p.replace("\\", "/") for p in paths))


def summary(case: str, path: str):
    """(passed, lines) from one case's --json result."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False, ["%s: no result (see the output above)" % case]
    lines, ok = [], True
    for found in data.get("cases") or []:
        for run in (found.get("arms") or {}).get("with") or []:
            ok = ok and bool(run.get("passed"))
            lines.append("%s: %s (score %.2f)%s" % (case, "pass" if run.get("passed") else "FAIL", run.get("score") or 0,
                                                    (", error: %s" % run["error"]) if run.get("error") else ""))
            for g in run.get("graders") or []:
                if not g.get("passed"):
                    lines.append("    %s: %s" % (g.get("name"), g.get("explanation")))
    if not lines:
        return False, ["%s: the result holds no run" % case]
    return ok, lines


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--all", action="store_true", help="every case")
    p.add_argument("--case", nargs="+", help="these cases (globs allowed)")
    p.add_argument("--base", default="origin/main", help="what the branch is compared with (default origin/main)")
    p.add_argument("--runs", type=int, default=1, help="runs per case (default 1)")
    p.add_argument("--model", default="sonnet", help="model and judge (default sonnet)")
    p.add_argument("--dry-run", action="store_true", help="say which cases would run, and run nothing")
    a = p.parse_args(argv)

    cases = all_cases()
    if a.case:
        chosen = [c for c in cases if any(fnmatch.fnmatch(c, pat) for pat in a.case)]
        if not chosen:
            print("no case matches %s (cases: %s)" % (" ".join(a.case), ", ".join(cases)))
            return 2
    elif a.all:
        chosen = cases
    else:
        changed = changed_paths(a.base)
        chosen = select(changed, cases)
        if not chosen:
            print("this branch touches no eval case (%d changed file(s) against %s); --all runs every case"
                  % (len(changed), a.base))
            return 0
    print("cases (%d): %s" % (len(chosen), ", ".join(chosen)))
    print("each runs %d time(s) on %s, on the Claude account Claude Code is logged into, and spends plan usage"
          % (a.runs, a.model))
    if a.dry_run:
        return 0
    if not shutil.which("claude"):
        print("claude is not on PATH: install Claude Code and log in first")
        return 2
    out_dir = os.path.join(EVALS, "results")
    os.makedirs(out_dir, exist_ok=True)
    report, failed = [], 0
    for case in chosen:
        print("\n=== %s" % case, flush=True)
        result = os.path.join(out_dir, "%s.json" % case)
        if os.path.exists(result):
            os.remove(result)
        subprocess.run(["claude", "plugin", "eval", ".", "--scaffold", "--trust-plugin", "--ablation", "none",
                        "--allow-tools"] + ALLOW + ["--model", a.model, "--judge-model", a.model, "--no-publish",
                                                    "--runs", str(a.runs), "--case", case, "--json", result], cwd=ROOT)
        ok, lines = summary(case, result)
        failed += 0 if ok else 1
        report += lines
    print("\n" + "\n".join(report))
    print("\n%d of %d case(s) passed" % (len(chosen) - failed, len(chosen)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
