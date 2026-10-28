#!/usr/bin/env bash
# The engine and a pretend learner (the feedback scenario of evals/fixture.py) in the run's empty workspace.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$root/evals/fixture.py" feedback
