"""Validate the Calamity plugin strictly, allowing the one warning the design accepts.

    python3 tools/validate_plugin.py

Runs `claude plugin validate . --strict` and passes when every warning is an accepted one:

    CLAUDE.md at the plugin root is not loaded   the clone's session context; the plugin route carries the same
                                                 session start and rules in the output style (force-for-plugin)

Any other warning or error fails. CLAUDE.local.md is a maintainer's own, git-excluded file and is ignored
too. Needs Claude Code on the PATH; no account is used. Standard library only.
"""
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCEPTED = (r"CLAUDE\.md at the plugin root is not loaded", r"CLAUDE\.local\.md at the plugin root")


def main() -> int:
    if not shutil.which("claude"):
        print("claude is not on PATH: install Claude Code first")
        return 2
    proc = subprocess.run(["claude", "plugin", "validate", ".", "--strict"], cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if proc.returncode == 0:
        print("plugin valid (strict)")
        return 0
    findings, errors, advice = [], False, False
    for line in out.splitlines():
        text = line.strip()
        if text.startswith("ℹ Advice"):
            advice = True                      # advice never changes the verdict
        elif text.startswith("Validating "):
            advice = False
        if re.match(r"^✘ Found \d+ error", text):
            errors = True
        if not advice and re.match(r"^❯ (root|[\w./-]+):", text):
            findings.append(text)
    unexpected = [f for f in findings if not any(re.search(a, f) for a in ACCEPTED)]
    if errors or unexpected or not findings:
        print(out)
        print("unexpected findings:\n  " + "\n  ".join(unexpected or ["see the output above"]))
        return 1
    print("plugin valid (strict), with the accepted warning: CLAUDE.md is the clone's context")
    return 0


if __name__ == "__main__":
    sys.exit(main())
