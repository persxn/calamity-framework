# Development tools

Checks that go beyond the unit tests. None of them is needed to study with
the framework, and none touches this checkout: each works in a temporary
folder and removes it afterwards. Standard library only, like the engine.

| Tool | What it checks | Typical run |
|---|---|---|
| `tools/e2e.py` | The whole framework as two laptops use it: onboarding, syllabi, items made and checked, study, a woven exercise, a GATE course, Codeforces from recorded data, notes and a PDF (when a TeX engine is installed), dashboards, two laptops merging through git, and a framework update for a clone and for a copy that began as an archive. Needs git. | `python3 tools/e2e.py` (about a minute) |
| `tools/fuzz.py` | Random command sequences: no command may crash, the state served through the replay snapshot must equal a full replay after every step, and each run's events must replay to the same state from shuffled files. | `python3 tools/fuzz.py --runs 20 --steps 60` |
| `tools/demo.py` | Produces the sample output shown in the README and the guides, from pretend learners in a temporary copy of the framework. | `python3 tools/demo.py --out /tmp/calamity-samples` (a folder outside the checkout) |
| `tools/bench.py` | Times commands on a long log, with and without the replay snapshot. | `python3 tools/bench.py <learner repository> --events 50000` |

On Windows use `python` or `py -3` instead of `python3`.

## Companion tool

`tools/timetable.py` is not a check — it's a small learner-facing viewer of the
daily routine. It reads the day shape from `learner/schedule.md` and keeps
per-day goals and date-specific overrides in `learner/timetable.json` (so they
sync with the rest of the learner's progress). `timetable help` lists its
commands; `timetable` alone shows today. On its first interactive run it copies
itself to `/var/x` and adds a `timetable` alias to `~/.zshrc`. It finds the
repository through `CALAMITY_REPO` (default `~/calamity-framework`).

Continuous integration runs the unit tests (`python3 engine/calamity.py selftest`)
on Linux, macOS and Windows with every supported Python, and `tools/e2e.py`
and a short `tools/fuzz.py` on each system. Run a longer fuzz before a
release and after any change to how the log is replayed.

A fuzz failure prints its seed: `python3 tools/fuzz.py --first <seed> --runs 1`
repeats it exactly.
