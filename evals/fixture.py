"""The workspace of a plugin eval case: the engine, the framework and a pretend learner.

A case's scaffold.sh runs it in the run's empty workspace (`claude plugin eval . --scaffold`):

    python3 <plugin>/evals/fixture.py recall|study|review

The learners are the ones tools/baseline.py measures (see its docstring); every fixture item's
right answer is B.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import baseline  # noqa: E402

if __name__ == "__main__":
    baseline.build(baseline.Fixture(os.getcwd(), engine_only=True), sys.argv[1])
