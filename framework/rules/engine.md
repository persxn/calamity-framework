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
folder once they are stored. The examiner works in
`.calamity/tmp/examiner/<batch>/` (`item import` deletes the whole batch
folder once it is stored) and the checker in `.calamity/tmp/checker/<item>/`
(deleted once its result is recorded); the key guard keeps everyone else
out of both.

## Session

| Command | What it does |
|---|---|
| `brief` | The session-start summary. `--hook` is for the SessionStart hook (it reads the model and effort Claude Code passes, when it passes them); after a compaction it adds where the session was, and with `auto.start` true it opens a new or cleared session with `/day` (never in a clone without a learner, never with `CALAMITY_MAINTAIN=1`). |
| `today` | Today's plan: finish line, what is due, what is new, next lecture, the next action, a `settings:` line and, at the finish line or after a long block, a `session:` line suggesting a fresh session. |
| `next [--skill S] [--only]` | The single next action: `onboard`, `enroll`, `sleep`, `review`, `consolidate` (a second item on a topic answered right once, before new material; with `not before HH:MM` while it is too soon), `new`, `watch`, `wind-down`, `boss`, `syllabus` (an enrolled skill has no topics yet) or `done`. `--skill` draws new material from one skill; `--only` also limits reviews to it. |
| `ask [--topic K [--taught [--parts P,...] [--minutes N]] \| --id ITEM \| --skill S] [--due] [--test T] [--check]` | Serve one verified item without its key and start its timer. With no argument it serves whatever `next` says (a review, or a topic taught already) and otherwise prints the next action; `--due` serves a review only. `--taught` first records that the topic was just taught, as `covered` does, and adds a `note:` when topics it builds on were never studied. `--parts` (history, model, mechanics, example, usage, flags, tradeoffs, impl) and `--minutes` are stored on that event and shown by `day`; a `warning:` names parts the topic's level asks for that were not taught (never a block). |

`NEXT: new` for a topic to teach also prints its `level`, what it `builds
on`, its `objectives` and where to start (from zero for a skill's first
topic or a level-1 topic). `next`, `today`, `item needs` and the brief end
with a `settings:` line: the suggested `/model` and `/effort` for the next
block, from `advice.*` in `framework/config.md` (a suggestion, not
measured; `cfg.advice false` turns it off).
| `answer ITEM --answer "..."` | Record an answer to a multiple-choice (`B`), multiple-select (`A,C`), numeric (`0.42`, `3/8`) or short-text item. The engine grades it and prints the key and solution. |
| `answer ITEM --result pass\|fail --evidence "..."` | Record a hands-on item (code, task, open) after its check was run. |
| `answer ITEM ... --next [--skill S] [--due]` | After a right answer, also serve what `ask [--skill S] [--due]` would, below the feedback, in the same call. After a wrong answer it serves nothing: the key, the cause and the repair come first. |
| | Options for both: `--hints N`, `--err KIND` (when wrong), `--blame K[,K]` (woven items), `--note "..."`, `--seconds N`, `--kind new\|review\|weave\|boss\|placement`. Only `--kind placement` changes anything: in a placement test a miss on a topic never studied schedules nothing, and a right answer does not count as today's new material. |
| `mistake ITEM KIND [--note "..."]` | Say what kind of mistake the last wrong answer to an item was, once the cause is clear: `concept`, `method`, `memory`, `careless`, `misread`, `time`, `syntax` or `guess`. It replaces whatever was recorded with the answer. |
| `quick K pass\|fail [--err KIND] [--hints N] [--note]` | An oral check. Schedules the topic; never counts as mastery evidence. A `fail` is refused for a topic that was never taught or answered: there is nothing to bring back yet. |
| `covered K [K ...] [--by tutor\|self\|source]` | Mark topics as taught and ready for their first test. |
| `weave S [--n N]` | Earlier topics worth embedding in the next exercise for skill S. Topics most at risk of being forgotten (lowest recall chance) come first: rescue weaving. |

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
| `tree frontier [--n N]` | Skills not started whose prerequisites are met or well under way (at least half their topics consolidating), ranked by what the learner's own work feeds, what else they combine with that the learner has, shared ground (tags) and the route to a goal, each with its summary and reasons ("builds on React (100% secured); with TypeScript, which you have; opens once Express.js is ready"). |
| `project suggest [--n 3]` | Integration projects: two active skills that belong together (one weaves into the other, or a later skill or milestone needs both), each with at least half its topics consolidating (`project.share`), with the topics to span. The examiner writes the project as one `task` item listing those topics, so one pass credits both skills. |
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
| `item needs [--skill S] [--n N] [--full] [--compact] [--days D] [--per-topic P]` | `--compact`: one line for the tutor (`ITEMS NEEDED: n topic(s): ...` or `ITEMS: stocked`). The examiner's work list: upcoming topics with no unseen verified item. `--full` adds each topic's difficulty, format, objectives and topics to embed. `--days` looks D learner days ahead (reviews due by then, the new topics the quota would open) and `--per-topic` wants P unseen verified items a topic: each entry then says how many more to write, the drafts waiting for the checker and the objectives no item tests yet (`family:` with `--full`). |
| `item draft --file F [--by examiner]` | Store one draft (a JSON object). |
| `item import --file F [--by examiner] [--official]` | Store a list of drafts (the author is `examiner` unless `--by` says otherwise; the examiner never verifies). `--official` stores official-paper items with their official keys; like any draft, each needs the checker's blind answer. |
| `item show ITEM [ITEM ...] [--check] [--reveal]` | The item (or several) without its key. `--check` adds the check and rubric of a hands-on item. `--reveal` adds key and solution, only for an item the learner has already answered (never for a draft, an unanswered item or one that is waiting for an answer). |
| `item verify ITEM --answer "..." --by checker`, `item verify ITEM=ANSWER [ITEM=ANSWER ...] --by checker` | Blind verification of auto-graded items, one or a whole batch: each independent answer must match the sealed key. In a batch every item is checked before anything is recorded. |
| `item verify ITEM --ran --evidence "..." --by checker` | Verification of a hands-on item: its check was run against a reference solution. `--fail` rejects it. |
| `item reject ITEM --reason`, `item dispute ITEM --reason`, `item restore ITEM` | Withdraw an item; put a verified item on hold (only a verified item can be disputed); reinstate a disputed item that had been verified, or an official or imported item held because a checker's answer did not match. |
| `item list [--skill S] [--topic K] [--status draft\|verified\|rejected\|disputed]` | The bank. |
| `item tag ITEM --objectives 1,3 [--strand T\|P\|I\|N] [--depth recall\|apply\|analyse\|transfer]` | Say which of its primary topic's objectives an item tests (numbered as `tree show` and the NEED_ITEM block print them), without opening its key. Right answers already given on it count toward the topic's coverage. |

## Study sources

| Command | What it does |
|---|---|
| `source add ID --title "..." --kind course\|playlist\|book\|site\|other --url U --route api\|export\|browser-session\|paste\|manual-log --tracks a,b --note "what the terms allow"` | Register a source (`learner/sources/ID.md`). |
| `source import ID --file F [--dry-run]` | Add or replace its lectures from a JSON list: `[{"id", "title", "topics": ["skill/topic"], "minutes", "order", "section", "url"}]`. `--dry-run` checks the list and says what would change, writing nothing. |
| `source status [ID]`, `source check` | Progress and next lectures; validate topic mappings. |
| `source show <id> [--section S] [--unmapped] [--topic K] [--limit N]` | A slice of a source: with no filter its sections with item and unmapped counts; with a filter the matching lectures (id, title, section, topics), at most N (40). Mapping and syllabus tasks read this, never the whole file. |
| `source revise [--limit N]` | Watched lectures whose topics have fallen below 85% recall, most faded first: what to rewatch or reread (8 by default). |
| `log SOURCE ITEM [--undo] [--upto] [--at ISO] [--score X] [--method manual\|manual-log\|paste\|screenshot\|api\|export\|browser-session]` | Mark a lecture done. ITEM is its id, its number, or a unique piece of its title. `--upto` logs everything up to it as watched earlier (it does not count as today's work). `--at` backdates it to when it was watched. |
| `log SOURCE --file ticks.json` | Log many lectures at the times they were ticked: a JSON list `[{"item": "ak-593", "at": "2026-10-23T21:10:00+05:30"}]` or an object `{"ak-593": "<ISO time>"}` (as a tracker stores it; `true` means now). Lectures already logged are skipped, so a sync can run again. |

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
| `gate pass SUBJECT N --planned YYYY-MM-DD`, `gate pass SUBJECT N --done [--date D]` | Plan or mark a revision pass of a subject; `gate status` shows passes done of planned. |
| `gate numericals [SUBJECT]` | Per topic with `[N]` objectives: numerical questions solved (verified `nat` items answered right, `nat` practice questions solved) against `numericals.target` (10), to reach before the final phase. A topic far behind is raised once as the `numericals-low` pattern. |
| `gate pack SUBJECT [--pdf]` | A revision pack, `learner/notes/<subject>/revision-pack.md`: a formula sheet from the `## Formulas` sections of the subject's notes fragments and an error book of the recorded mistakes (date, topic, kind, the learner's note, where). No key or solution: those items come back. `--pdf` also builds a PDF (needs a TeX engine). |

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
| `notes fragment K`, `notes section K` | Path of a topic's markdown fragment (created if missing) and of its long-form section: `md/<topic>.md`, or `tex/<topic>.tex` when `book.format` is `pdf`. |
| `notes stamp S`, `notes assemble S`, `notes pdf S` | Mark sections as current; put the book together (`<skill>-notes.md` from Markdown sections, `main.tex` from LaTeX ones); build the PDF (Markdown is converted by the engine, LaTeX compiled with whatever TeX engine is installed). |
| `book pdf <file.md or folder> [--out F]` | A PDF of a Markdown study book, made by the engine (no LaTeX written by hand): a folder is its `README.md` then its chapters in name order. Needs Tectonic, XeLaTeX or LuaLaTeX. |

## The learner, the machine, the data

| Command | What it does |
|---|---|
| `profile show`, `profile get KEY`, `profile set KEY VALUE [--text]`, `profile set KEY=VALUE [KEY=VALUE ...]`, `profile unset KEY` | The learner profile; several keys can be set in one call, all or none. The keys below are checked (times, dates, numbers); lists take comma-separated values; `name`, `teach.style` and `gate.target_source` are stored as written, and `--text` does the same for any key; `none` unsets a key. Free notes about the learner go in the text below the keys in `learner/profile.md`. |
| `observe "..." [--tag teaching\|coach\|explain] [--pattern ID] [--skill S] [--topic K]`, `observations [--tag T] [--n N]` | Record and read what has been learnt about how this learner works. `--tag explain --topic K` records that the learner explained a topic back in their own words (a unit of deep coaching needs one). |
| `model [--days N] [--skill S] [--track T]` | The learner model over the last N days (30), from the log: per track and skill, first-try accuracy on new topics, retention on verified reviews 7+ and 30+ days after the previous answer, median answer time, hint rate, error kinds, days to consolidate; then first-try accuracy by the parts taught and by the part taught first, the learner's feedback, accuracy by part of day and by session minute (with the length after which it falls), and topics secured per hour per track (ROI, weighted by GATE marks per topic or by being on a goal's route; an estimate). Every rate shows its count; below 5 answers it shows `-`. |
| `experiment start <id> --skill S --arms a,b [--n 12] [--metric first_try_acc] [--desc "..."]`, `experiment status [<id>]`, `experiment stop <id>` | An n-of-1 teaching experiment on the next N new topics of a skill: arms alternate in the order topics are first taught (the same on every replay), and `NEXT: new` names the arm to teach with. `status` shows each arm's first-try accuracy and, for two arms, P(second better than first) under a Beta(1,1) prior, and refuses any conclusion before N topics are measured. A result changes nothing by itself. |
| `tasks [list]`, `tasks done <id> [--days N]`, `tasks snooze <id> [--days N]` | Work around the studying that has fallen due, most pressing first, each with what handles it: `weekly-review` (none for 7 days), `gate-plan` and `cp-plan` (the plan's `review_on` has come, or a mock was recorded after the GATE plan), `stock` (topics of the next two days without an unseen verified item), `notes` (sections to write or rewrite), `push` (learner changes not pushed for 3 days), `numericals`, `revise` (faded lectures), `mocks` (GATE mock records older than 30 days). `done` hides a task for its cooldown (or `--days`), `snooze` for a day; both are events. The brief and `today` show the top two. |
| `unit S [TOPIC ...]` | Whether a unit of deep coaching is done (`mastery-coach`): each topic's status and whether it was explained back, then `UNIT DONE`, or `UNIT OPEN:` with what is missing (topics not yet `consolidating`, no explain-back). Topic ids or keys; no topics means the whole skill. |
| `feedback pace=fast\|slow\|ok depth=more\|less\|ok clarity=low\|ok level=harder\|easier\|ok [--topic K]` | Record the learner's own word on the teaching (any of the three); `day` shows it, `observations --tag feedback` lists it. |
| `workout MINUTES [--note]` | Log a workout. |
| `stats [flags\|brief\|week\|hours\|patterns\|errors] [--days N] [--track T]` | Teaching observations; the last days in two lines (`brief`, for prompts and agents); the last days; accuracy by part of day; behaviour patterns; error log. |
| `dash [progress\|roadmap\|queue\|gate\|cp\|week\|all] [--track T] [--all-tracks] [--width N] [--ascii] [--html]` | Dashboards as plain text. `--html` writes the view to `.calamity/dash/<view>.html` and prints two lines, its headline and the page's path, so the table never enters the conversation. |
| `statusline [--stdin]` | One line for the Claude Code status line. With `--stdin` (as `setup --statusline` writes it) it reads the session data Claude Code passes and adds `try <model>·<effort>` when the suggested setting differs from the current one. |
| `practice add <set> --title "..." --items N --key official\|unofficial\|none [--kind ...] [--source "..."]`, `practice map <set> --file F`, `practice log <set> <questions> solved\|wrong\|guessed\|skipped [--err E] [--secs N] [--note "..."]`, `practice due`, `practice status [<set>]`, `practice stats` | Practice sets: outside questions as metadata only (numbers, topics, pages; never a question's text). Each question is revisited (wrong, guessed or skipped: 2, 7, 21 days; solved: 10, 30) and retires after two right revisits in a row; `next` serves revisits after due reviews, before new material. A logged batch is one attempt per mapped topic: evidence when the key is official, scheduling only otherwise. `learner/practice/<set>.md` is the engine's view. |
| `career add --file F`, `career list [--kind gate-mock]`, `career show <id>` | Opportunity records found on the web (for now GATE mocks, from the opportunity-scout). Each must carry `url`, `source`, `fetched` (YYYY-MM-DD) and `terms` (what the site allowed), or the file is refused; one with the same kind and url replaces the earlier. `list` marks records older than 30 days as stale. |
| `stock render --at 23:45 [--model M] [--effort E] [--os ...]`, `stock remove [--os ...]` | Nightly stocking: write scheduler files for a headless `claude -p "/stock"` run (tools limited to the engine, the agents' scratch and the web; `--permission-mode dontAsk`) that starts only when `item needs --days 2 --per-topic 3` lists work, logging to `.calamity/logs/`; print how to install and remove it. `stock.at` in the profile holds the time. Nothing is installed by the engine. |
| `remind check [--always]`, `remind render --times 09:00,20:30 [--os linux\|darwin\|windows]`, `remind remove [--os ...]` | Is anything due (for a scheduler); write scheduler files and print how to install and remove them; print the removal command again (no times needed). Files and task names carry a tag of this clone. Nothing is installed by the engine. |
| `setup [--machine NAME] [--hook] [--statusline] [--alias] [--remove-hook] [--remove-statusline] [--remove-alias]` | Prepare this machine. `--hook` writes the session-start hook, the key guard and the study hooks (prompt, stop, compaction, session end), and selects the Calamity Tutor output style (a style the learner chose is kept), `--statusline` the status line, to `.claude/settings.local.json`; `--alias` adds a `calamity` alias to `~/.zshrc` or `~/.bashrc` (`~/.bash_profile` on macOS) that changes to this folder and runs `claude --dangerously-skip-permissions`; the `--remove-` flags take them out again. |
| `day [<day>] [--json]`, `day note <day> "..."`, `day goal "..." [--at HH:MM] [--block NAME] [--date D]`, `day done|undone N [--date D]`, `day migrate [--write]` | The day's shape from `learner/schedule.md` (blocks, the current one marked), the day's note and goals from `learner/timetable.json`, today's finish line, and what was recorded that day (time, answers, topics taught and secured, lectures, practice, workouts); `<day>` is today, tomorrow, yesterday, +N, mon..sun or YYYY-MM-DD. `migrate` turns a schedule written as weekday and weekend tables into front-matter blocks (shown first, written with `--write`). |
| `history [--from D] [--to D] [--days N] [--by day\|week\|month] [--skill S\|--track T]` | What was done, one row per period: active days and time, answers and accuracy, new topics and reviews, topics taught and secured, lectures, practice, workouts. With a skill or a track, only its answers, teaching and consolidation. `day <date>` shows the same record for one day, under its shape. |
| `layout check`, `layout migrate [--write]` | The learner store's layout. `migrate` moves what is still under `learner/mastery/` to `learner/coach/<topic>/`, `learner/books/<topic>/` (a topic's `book/`) and `learner/projects/<slug>/`, with `git mv` for tracked files; it shows the moves first, makes them with `--write`, and never overwrites a target. `doctor` warns while anything is left. |
| `guard prompt`, `guard stop`, `guard end`, `snapshot --session` | The study hooks `setup --hook` installs, each reading Claude Code's JSON on stdin and never failing the session. `prompt` (UserPromptSubmit): one line naming the skill a request belongs to, `!slow !fast !deeper !lighter !example !harder !easier` recorded as `feedback`, and "contest running" for a pasted link to a live Codeforces contest. `stop` (Stop): blocks a turn's end once when the learner replied after an item was shown and no answer is recorded, or a topic taught today has no notes fragment (only in `/study`, `/recall`, `/day`, `/mastery-coach`, `/practice`, `/boss` sessions; never twice for one thing, never while `stop_hook_active`). `snapshot --session` (PreCompact) writes where the session stands to `.calamity/session.json`; the next `brief --hook` (source `compact`) adds a `Resumed after compaction` block with the item in flight. `end` (SessionEnd) records a `session_end` event. `CALAMITY_HOOKS=off` or `CALAMITY_MAINTAIN=1` silences them all, and they do nothing in a clone with no learner. |
| `guard tool` | The key guard, run by Claude Code as a PreToolUse hook before every Read, Grep, Glob and shell call (`setup --hook` installs it): it refuses `learner/items/` to everyone, the examiner's scratch to all but the examiner and the checker's to all but the checker, including shell commands that name them and searches that would reach them. It also refuses a whole-file Read over 20 KB of `learner/sources/`, `learner/events/` or `learner/PROGRESS.md`, naming the engine slice to use. It reads the call as JSON on stdin and prints a refusal or nothing. |
| `clean tmp [--dry-run]` | Empty the scratch folder `.calamity/tmp/`, worked answers included; `--dry-run` lists what would go. |
| `doctor`, `rebuild`, `selftest`, `version` | Health check (it also checks the replay snapshot against a full replay, that the key guard refuses what it must, and warns about scratch files older than a day and about an account-level `mastery-coach` that would compete with the framework's); replay the whole log and rewrite `learner/PROGRESS.md` and the monthly journal `learner/journal/<YYYY-MM>.md` (a summary and a line per day, from the log alone, so every machine writes the same files); run the engine's tests; versions. |

## Profile keys

`name`, `onboarded`, `tracks`, `goals`, `focus`, `mode.default`,
`teach.style`, `sleep.start`, `sleep.end`, `workout.minutes`,
`daily.target_hours`, `reminders.times`, `gate.year`, `gate.papers`,
`gate.registered`, `gate.target_rank`, `gate.target_marks.<PAPER>`,
`gate.target_source`, `gate.exam_date.<PAPER>`, `cp.handle`, `book.format`,
`cp.target_rating`, `cp.target_date`, `cp.language`, `stock.at`, `location.city`,
`location.radius_km`, `auto.start` (true: open each new session with `/day`), and `cfg.<key>` to
override any default in `framework/config.md` (for example
`cfg.advice false` to turn off the model suggestions, or
`cfg.advice.heavy "opus xhigh"`).

- `tracks`: the tracks the learner follows, for example `10x,cp,gate-cs,gate-da`.
- `goals`: skill ids the learner is heading for, for example `mern-stack,cp.rating-1800`.
  `tree suggest` and `tree path` plan toward them.
- `focus`: what new material is drawn from before anything else: skill ids,
  track ids, or `gate` for every GATE subject. Without it, enrolled skills
  take turns (`framework/rules/scheduler.md`).

## Environment variables (for tests and tools)

`CALAMITY_NO_CACHE=1` makes every command replay the whole log instead of
starting from the snapshot in `.calamity/cache/replay.json` (the snapshot is
disposable: deleting it changes nothing but speed). `CALAMITY_ROOT` points
the engine at another repository root,
`CALAMITY_FRAMEWORK` at another framework folder, `CALAMITY_NOW` fixes the
clock (an ISO timestamp), and `CALAMITY_CF_FIXTURES` makes the Codeforces
commands read `<method>.json` files from a folder instead of the network.
`CALAMITY_HOOKS=off` silences the study hooks (routing, feedback tokens, the
Stop guard, compaction, session end) and auto-start for that shell;
`CALAMITY_MAINTAIN=1` does the same for a maintenance session.
