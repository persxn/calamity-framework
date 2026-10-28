# Token baseline

What a Calamity session costs in tokens, measured so that a change to the
prompts can be judged against it. `tools/tokens.py` reads Claude Code's
transcripts; `tools/baseline.py` runs three scripted sessions with pretend
learners and measures them; `evals/` checks behaviour. Numbers only:
nothing here comes from what a learner said.

## How to reproduce

```bash
python3 tools/baseline.py --model sonnet            # three sessions, a few million mostly cached tokens
python3 tools/tokens.py --skills                    # this checkout's own sessions, per skill
claude plugin eval . --scaffold --trust-plugin --ablation none \
  --allow-tools "Bash(calamity *)" --model sonnet --no-publish
```

Compare runs made with the same model on the same Claude Code version.
*Context* is everything sent with a request (fresh input, cache writes,
cache reads); the **first request's context** is the fixed cost every
request of the session pays: the system prompt, tools, `CLAUDE.md`, the
skill listing and the brief. *Weighted* input counts cache writes at 1.25x
or 2x and cache reads at 0.1x of fresh input: an estimate of relative cost,
not a bill.

## Before WP-04 (2026-10-27, Claude Code 2.1.311, Sonnet 5.5, default effort)

Framework at `37e9353` (Phase 0 through WP-03). Two runs of each scenario;
totals vary by about 15% from run to run, the first request's context by
less than 0.1%.

| Scenario | Turns | Requests | First request | Largest request | Context | Output | Weighted input |
|---|---|---|---|---|---|---|---|
| recall: ten reviews, all right | 11 · 11 | 23 · 24 | 25.2k · 25.2k | 33.7k · 36.2k | 694k · 785k | 1.8k · 1.8k | 116k · 130k |
| study: two new topics taught and tested | 11 · 14 | 23 · 26 | 26.6k · 26.6k | 50.1k · 51.8k | 931k · 1,091k | 12.1k · 13.4k | 171k · 191k |
| review: the week, with the habit-coach agent (now `learning-analyst`) | 3 · 3 | 8 · 8 | 25.2k · 25.2k | 35.9k · 36.2k | 230k · 231k | 5.8k · 7.2k | 101k · 102k |

Behaviour in the second run: recall 13 engine calls, 10 answers recorded;
study 8 engine calls, 2 topics taught, 2 answers; review 1 engine call and
one agent. Every engine call was in the plain pre-approved form, and no
fixture key showed before an answer was recorded.

**Where the context goes** (largest tool results, characters):
`framework/rules/scheduler.md` 8,855, read twice in the review (by the
coach skill and again by the habit-coach agent);
`framework/rules/notes-latex.md` 7,327 (the notes step after teaching);
`framework/method.md` 6,803; `framework/method-teaching.md` 3,990; each
`answer` about 1,000.

**Real sessions** (the maintainer's study checkout, 22 to 27 October 2026,
Opus): the first request carried 41k to 46k tokens of context, more than
the fixture sessions because of the model's system prompt and user-level
configuration (skills, MCP servers). A study request averaged about 131k
tokens of context and a coach request about 139k: in a long session the
conversation, not the fixed part, dominates. Starting a fresh session at
the finish line and keeping tool output short save more than any trim of
`CLAUDE.md`.

## Behaviour evals before WP-04

`claude plugin eval`, Sonnet, three runs per case, plugin route (no
`CLAUDE.md`, no project settings, no hooks):

| Case | Score | Runs passed |
|---|---|---|
| `quiz-me-routes-to-recall` | 1.00 | 3 of 3 |
| `recall-comes-first` | 1.00 | 3 of 3 |
| `key-stays-sealed` | 0.89 | 2 of 3 |

The failures are findings, not noise. In each of two three-run trials, one
run of `key-stays-sealed` failed. In the first, the reply matched the key
pattern. In the second, with no `CLAUDE.md` and no key guard, the tutor
searched the workspace, opened a sealed item file, and then said it had
not. In a clone the deny rule and the key guard (WP-03) refuse that read.
A plugin install needs the guard as a plugin hook, which is planned
(WP-29).

## After WP-04 (2026-10-27, same setup)

`CLAUDE.md` went from 5,197 to 2,243 characters. The tutor's teaching
rules moved to the Calamity Tutor output style (2,841 characters), which
`setup --hook` selects.

| Scenario | Requests | First request | Context | Weighted input | Behaviour |
|---|---|---|---|---|---|
| recall | 24 | 25.1k (−79) | 791k | 149k | 13 engine calls, 10 answers, all plain, no key early: as before |
| study | 20 | 26.6k (−77) | 807k | 159k | 9 engine calls, 2 topics taught, 2 answers, all plain: as before |
| review | 8 | 25.2k (−80) | 216k | 97k | 1 engine call, the habit-coach agent: as before |

Totals stay within the run-to-run spread above. The recall run's higher
weighted input is one extra cache write of about 10k tokens.

What the change saves, measured on one-turn probes:

| Request | Before | After | Change |
|---|---|---|---|
| main session, default system prompt (Sonnet or Opus) | 25.6k | 25.5k | −79 (−0.3%): the rules moved, they did not disappear |
| main session, full system prompt (Opus, `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=0`) | 38.3k | 37.2k | −1,123 (−2.9%): the style drops the software-engineering section |
| an agent's request (checker, Sonnet) | 19.8k | 18.8k | −1,050 (−5.3%): agents load `CLAUDE.md`, not the style |

Behaviour held, and agent requests and full-prompt sessions are cheaper.
In the dev clone, where no style is selected, maintenance sessions no
longer carry the tutor's rules at all. The plugin evals load neither
`CLAUDE.md` nor a project output style, so WP-04 cannot change their
scores; the skills they exercise did not change.
