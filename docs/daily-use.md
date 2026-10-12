# Daily use

## A normal day

1. Open a terminal in your `calamity` folder and run `claude`. If the
   session-start hook is installed, Claude has already read where you
   stand; otherwise it runs the brief first.
2. Claude greets you and asks a few **surprise recall** questions: topics
   due for review, from any skill, without saying which.
3. `/study` (or "let's carry on"): reviews as they come due, then new
   material, one small chunk at a time, each tested at once. Earlier skills
   turn up inside new exercises.
4. If you follow a course or playlist, watch the next lecture there, then
   `/log <source> <lecture>`: its test follows straight away.
5. `/today` at any point says what is left of the day's finish line.
6. When you stop, Claude saves notes fragments for what you met, and
   `/sync` pushes your progress to your own repository if you ask.

## The finish line

There are no points, levels or streaks. Each day has a finish line you can
count, and reaching it is the day done:

- 90% of the reviews that were due today answered (a few may carry over);
- every topic you got wrong today answered correctly again;
- the day's new topics (`new_per_day`, 8 by default, or fewer if fewer are
  unlocked);
- the day's lectures, if you set a lecture quota (`lectures_per_day`);
- every lecture you logged, tested.

A learner day runs from 04:00 to 04:00, so a session after midnight belongs
to the evening before. Inside your sleep window Claude says so once and
starts nothing new; in the hour before it, only reviews run.

## Commands

| Command | What it does |
|---|---|
| `/study [skill or topic]` | A session: recall first, then one small chunk at a time, each tested at once |
| `/recall [how many]` | Only the questions that are due, most forgotten first, as fast as you can answer |
| `/today` | Today's finish line and the single next thing to do |
| `/dash [progress \| roadmap \| queue \| gate \| cp \| week \| all]` | Progress, roadmap, revision queue, GATE and Codeforces boards, the week, as text |
| `/tree [show \| path \| next \| add \| drop \| goal ...]` | The skill tree: what a skill needs, the route to a goal, what to learn next; add, swap or drop skills |
| `/boss [skill]` | The project or timed test that proves a skill |
| `/log <source> <lecture>` | Record a lecture or chapter done elsewhere (its test follows), or a workout |
| `/notes [skill \| skill/topic \| pdf skill]` | Notes fragments, LaTeX sections, one PDF per skill |
| `/gate` | The GATE companion: countdown, triage, plan, mocks |
| `/cp` | The competitive-programming coach: Codeforces analysis, practice sets, contests |
| `/coach` | A review of how you have actually been working, and your day shape |
| `/bridge` | Connect a course site, playlist or book so its lectures enter the plan |
| `/remind` | Operating-system reminders that fire only when something is due |
| `/sync` | Commit and push your progress to your own repository |
| `/onboard [machine \| gate \| cp \| 10x \| ai]` | First-run setup, a new track, or a second laptop |
| `/update-framework` | Bring in a newer version of the framework without touching your data |

You can also just talk:

- "teach me Docker", "let's do some maths"
- "what should I do today?", "I have forty minutes"
- "I finished lecture 14", "I'm up to lecture 30 of the course"
- "quiz me", "a quick recall round"
- "I already know Git", "skip Terraform", "Fastify instead of Express"
- "how did my week go?", "my schedule isn't working"
- "make a PDF of my Docker notes"

## Hints, mistakes and disputes

- Ask for a hint whenever you are stuck. Hints come in three steps (what is
  asked, the idea, the first step) and are counted; a hinted answer counts
  as a hard one, so the topic comes back sooner.
- After a wrong answer you see the key and the solution, and Claude asks
  what went wrong. The kind of mistake is recorded, and `/coach` and
  `dash` use it: many careless errors call for slower checking, not more
  theory.
- If you think a key is wrong, say so. Claude does not argue from memory: the
  `checker` agent solves the question again from scratch, and if the key
  does not hold, the question is withdrawn and your answer stops counting.

## Reminders

Reminders are notifications from your operating system, so they work while
Claude Code is closed. Each one runs the engine's check and shows a
notification only if something is due: never inside your sleep window, and
not once the day's finish line is reached.

Ask for them with `/remind`. Claude stores the times you choose and writes
the scheduler files for this computer:

```bash
python3 engine/calamity.py profile set reminders.times 09:00,14:00,21:00
python3 engine/calamity.py remind render
```

`remind render` writes the files under `.calamity/reminders/` and prints
two commands: one that installs the reminders and one that removes them
(crontab on Linux, a LaunchAgent on macOS, Task Scheduler on Windows). The
engine installs nothing itself: Claude shows you the command and runs it
when you agree. To see what a reminder would say right now:

```bash
python3 engine/calamity.py remind check --always
```

Reminders are per computer; set them up again on a second laptop.

## The status line

```bash
python3 engine/calamity.py setup --statusline
```

shows the day's numbers at the bottom of Claude Code, for example
`CAL · due 3 · new 2/6 · GATE 117d`. Remove it with
`python3 engine/calamity.py setup --remove-statusline`.

## When you miss days

Nothing breaks. Reviews that were due stay due, most forgotten first; the
scheduler (FSRS-6) takes the longer gap into account when it sets the next
interval. If the queue has grown, `/coach` will suggest pausing new
material for a day or two. A skill you are not working on can be paused:
"pause Kubernetes for now".
