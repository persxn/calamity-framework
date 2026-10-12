# Engine reference

Every command below is a subcommand of the engine:

    python3 engine/calamity.py <command> [options]        Linux, macOS
    python engine/calamity.py <command> [options]         Windows (or: py -3 engine/calamity.py ...)

Run it from the repository root. `<command> --help` prints the flags.
Requirements: Python 3.9 or newer; nothing to install.

**Exit codes**: 0 done; 1 `doctor` found a problem; 2 an error (the message
on stderr says what to fix); 3 nothing is due (`remind check`); 4 no
verified item exists for the topic (`ask`, `test build`), with a
`NEED_ITEM` block that says what to make.

**Topic keys** are `<skill>/<topic>`. **Item ids** look like `it-7k2m9q4x1c`,
**test ids** like `t-...`. Where a file of JSON is expected, write it under
`.calamity/tmp/` and pass `--file`; the engine deletes draft files from that
folder once they are stored.

## Session

| Command | What it does |
|---|---|
| `brief` | The session-start summary. `--hook` is for the SessionStart hook. |
| `today` | Today's plan: finish line, what is due, what is new, next lecture. |
| `next [--skill S] [--only]` | The single next action: `onboard`, `enroll`, `sleep`, `review`, `new`, `watch`, `wind-down`, `boss` or `done`. `--skill` draws new material from one skill; `--only` also limits reviews to it. |
| `ask [--topic K \| --id ITEM \| --skill S] [--due] [--test T] [--check]` | Serve one verified item without its key and start its timer. With no argument it serves whatever `next` says; `--due` serves a review only and otherwise prints the next action. |
| `answer ITEM --answer "..."` | Record an answer to a multiple-choice (`B`), multiple-select (`A,C`), numeric (`0.42`, `3/8`) or short-text item. The engine grades it and prints the key and solution. |
| `answer ITEM --result pass\|fail --evidence "..."` | Record a hands-on item (code, task, open) after its check was run. |
| | Options for both: `--hints N`, `--err KIND` (when wrong), `--blame K[,K]` (woven items), `--note "..."`, `--seconds N`, `--kind new\|review\|weave\|boss\|placement`. Only `--kind placement` changes anything: in a placement test a miss on a topic never studied schedules nothing, and a right answer does not count as today's new material. |
| `mistake ITEM KIND [--note "..."]` | Say what kind of mistake the last wrong answer to an item was, once the cause is clear: `concept`, `method`, `memory`, `careless`, `misread`, `time`, `syntax` or `guess`. It replaces whatever was recorded with the answer. |
| `quick K pass\|fail [--err KIND] [--hints N] [--note]` | An oral check. Schedules the topic; never counts as mastery evidence. A `fail` is refused for a topic that was never taught or answered: there is nothing to bring back yet. |
| `covered K [K ...] [--by tutor\|self\|source]` | Mark topics as taught and ready for their first test. |
| `weave S [--n N]` | Earlier topics worth embedding in the next exercise for skill S. |

## Skills and the tree

| Command | What it does |
|---|---|
| `enroll S [--mode mastery\|brushup] [--force]` | Start a skill. Refuses when prerequisites are unmet unless `--force`. |
| `pause S`, `resume S`, `unenroll S` | Stop or restart a skill's reviews. Progress is always kept. |
| `placement S --known a,b --gaps c,d [--result known\|partial\|none] [--note]` | Record a placement test: known topics enter the review rotation; `known` marks the whole skill as a met prerequisite. Topic ids, not full keys. |
| `boss status [S]` | Bosses that are due, or one skill's boss specification and state. |
| `boss record S pass\|fail --evidence "..." [--kind project\|test\|capstone]` | Record a boss attempt. |
| `test build --skills a,b --n 10 --minutes 25 [--label "..."]` | Assemble a timed mixed test from verified items. Then `ask --id ITEM --test T` and `answer` for each, and `test finish T`. `test show T` lists its items. |
| `tree list [--track T] [--group G] [--status S]` | All skills with status and progress. |
| `tree show S`, `tree path S`, `tree suggest [--n N]`, `tree check` | One skill in full; the route to a goal in layers that can run in parallel; what to start next; validate the tree. |
| `tree add --id ID --title "..." [--track --group --prereqs a,slot:x --slot --tags --weaves-into --aliases --summary --scope "- ..." --hours N --optional --kind milestone]` | Add a skill for this learner (`learner/tree/ID.md`). |
| `tree set S [same options] [--clear-slot] [--not-optional]` | Change a skill. Shipped skills are overridden in `learner/tree/`, not edited. |
| `tree drop S [--yes]`, `tree restore S` | Drop a skill from this learner's tree (its prerequisite role counts as met) or bring it back. |
| `find WORDS` | Search skills, topics, lectures and notes. |
| `syllabus template S`, `syllabus path S`, `syllabus check S` | The shape of a learner syllabus, where it goes, and validation. |
| `rename topic OLD NEW`, `rename skill OLD NEW` | Carry progress over after a rename (rename in the file first). |

Status glyphs: `✓` mastered or known, `◕` ready, `◐` learning, `○` open to
start, `·` locked, `‖` paused, `✗` dropped. Pass `--ascii` where a terminal
cannot show them.

## Items

| Command | What it does |
|---|---|
| `item needs [--skill S] [--n N]` | The examiner's work list: upcoming topics with no unseen verified item, each with difficulty, format, objectives and topics to embed. |
| `item draft --file F [--by examiner]` | Store one draft (a JSON object). |
| `item import --file F [--by examiner] [--official]` | Store a list of drafts. `--official` marks official-paper items as verified by provenance. |
| `item show ITEM [--check] [--reveal]` | The item without its key. `--check` adds the check and rubric of a hands-on item. `--reveal` adds key and solution (not for drafts). |
| `item verify ITEM --answer "..." --by checker` | Blind verification of an auto-graded item: the independent answer must match the sealed key. |
| `item verify ITEM --ran --evidence "..." --by checker` | Verification of a hands-on item: its check was run against a reference solution. `--fail` rejects it. |
| `item reject ITEM --reason`, `item dispute ITEM --reason`, `item restore ITEM` | Withdraw an item; put a verified item on hold; reinstate a disputed one. |
| `item list [--skill S] [--topic K] [--status draft\|verified\|rejected\|disputed]` | The bank. |

## Study sources

| Command | What it does |
|---|---|
| `source add ID --title "..." --kind course\|playlist\|book\|site\|other --url U --route api\|export\|browser-session\|paste\|manual-log --tracks a,b --note "what the terms allow"` | Register a source (`learner/sources/ID.md`). |
| `source import ID --file F` | Add or replace its lectures from a JSON list: `[{"id", "title", "topics": ["skill/topic"], "minutes", "order", "section", "url"}]`. |
| `source status [ID]`, `source check` | Progress and next lectures; validate topic mappings. |
| `log SOURCE ITEM [--undo] [--upto] [--score X] [--method manual\|manual-log\|paste\|screenshot\|api\|export\|browser-session]` | Mark a lecture done. ITEM is its id, its number, or a unique piece of its title. `--upto` logs everything up to it as watched earlier (it does not count as today's work). |

## GATE

| Command | What it does |
|---|---|
| `gate status` | Countdown, phase, target, last mock, and coverage per subject. |
| `gate triage` | Subjects ranked by marks still to gain per hour of study left. |
| `gate enroll [--mode M]` | Enrol every subject of the learner's papers. |
| `gate mock PAPER SCORE [--max 100] --source "..." [--date YYYY-MM-DD] [--sections GA=11.33,OS=6] [--minutes N] [--note]` | Record a mock score. `gate mocks [PAPER]` lists them. |
| `gate errors` | Topics with the most wrong answers, with error kinds. |
| `gate weight SUBJECT MARKS --source "..."` | Replace a subject's prior weight. |
| `gate weights [--apply]` | Average marks per subject from fully imported official papers. |

## Codeforces

| Command | What it does |
|---|---|
| `cf link HANDLE`, `cf sync [--full]` | Link a handle (public API, no password) and fetch submissions, rating history, problem set and contest list into the local cache. Sync also records rating milestones. |
| `cf status`, `cf rating`, `cf analyse [--days 180]` | One line; rating history, pace against the target and next milestone; tags weakest first. |
| `cf recommend [--skill S \| --tags "dp,greedy"] [--n 5] [--low 100] [--high 300] [--show-tags]` | A practice set of unsolved problems rated above the current rating, weighted toward weak tags. Tags stay hidden unless asked. |
| `cf assign P [P ...] [--reason "..."]` | Record a set as assigned. |
| `cf credit P --topic K [--also K,K] [--hints N]` | Count a problem solved in the last 14 days as a verified exercise for a topic. |
| `cf mark P editorial\|resolved\|skip\|subtag\|note [--subtags a,b] [--note]` | Editorial used (comes back in a week); solved again without it; never suggest; finer tags. |
| `cf upsolve`, `cf contests [--n 5]` | Unsolved attempts and re-solves due; upcoming contests, virtual candidates, recent results. |

## Notes

| Command | What it does |
|---|---|
| `notes status [S]` | What exists and which sections must be written or rewritten. |
| `notes fragment K`, `notes section K` | Path of a topic's markdown fragment (created if missing) and of its LaTeX section. |
| `notes stamp S`, `notes assemble S`, `notes pdf S` | Mark sections as current; write `main.tex`; build the PDF with whatever TeX engine is installed. |

## The learner, the machine, the data

| Command | What it does |
|---|---|
| `profile show`, `profile get KEY`, `profile set KEY VALUE [--text]`, `profile unset KEY` | The learner profile. Comma-separated values become lists; `--text` stores free text. |
| `observe "..." [--tag teaching\|coach] [--pattern ID] [--skill S] [--topic K]`, `observations [--tag T] [--n N]` | Record and read what has been learnt about how this learner works. |
| `workout MINUTES [--note]` | Log a workout. |
| `stats [flags\|week\|hours\|patterns\|errors] [--days N] [--track T]` | Teaching observations; the last days; accuracy by part of day; behaviour patterns; error log. |
| `dash [progress\|roadmap\|queue\|gate\|cp\|week\|all] [--track T] [--all-tracks] [--width N] [--ascii]` | Dashboards as plain text. |
| `statusline` | One line for the Claude Code status line. |
| `remind check [--always]`, `remind render --times 09:00,20:30 [--os linux\|darwin\|windows]` | Is anything due (for a scheduler); write scheduler files and print how to install them. Nothing is installed by the engine. |
| `setup [--machine NAME] [--hook] [--statusline] [--remove-hook]` | Prepare this machine. `--hook` writes the session-start hook to `.claude/settings.local.json`. |
| `doctor`, `rebuild`, `selftest`, `version` | Health check; replay the log and rewrite `learner/PROGRESS.md`; run the engine's tests; versions. |

## Profile keys

`name`, `onboarded`, `tracks`, `goals`, `focus`, `mode.default`,
`teach.style`, `sleep.start`, `sleep.end`, `workout.minutes`,
`daily.target_hours`, `reminders.times`, `gate.year`, `gate.papers`,
`gate.registered`, `gate.target_rank`, `gate.target_marks.<PAPER>`,
`gate.target_source`, `gate.exam_date.<PAPER>`, `cp.handle`,
`cp.target_rating`, `cp.target_date`, `cp.language`, and `cfg.<key>` to
override any default in `framework/config.md`.

- `tracks`: the tracks the learner follows, for example `10x,cp,gate-cs,gate-da`.
- `goals`: skill ids the learner is heading for, for example `mern-stack,cp.rating-1800`.
  `tree suggest` and `tree path` plan toward them.
- `focus`: what new material is drawn from before anything else: skill ids,
  track ids, or `gate` for every GATE subject. Without it, enrolled skills
  take turns (`framework/rules/scheduler.md`).

## Environment variables (for tests and tools)

`CALAMITY_ROOT` points the engine at another repository root,
`CALAMITY_FRAMEWORK` at another framework folder, `CALAMITY_NOW` fixes the
clock (an ISO timestamp), and `CALAMITY_CF_FIXTURES` makes the Codeforces
commands read `<method>.json` files from a folder instead of the network.
