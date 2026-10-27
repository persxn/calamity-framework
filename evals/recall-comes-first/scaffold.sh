#!/usr/bin/env bash
# The engine and a pretend learner (review fixture of tools/baseline.py) in the run's empty workspace.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$root/evals/fixture.py" review
