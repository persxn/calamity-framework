# The day, the schedule and the coach

There is no timetable that the learner fails by 10 a.m. There are three
things instead: a **finish line** computed by the engine, a **day shape**
written with the learner and revised from evidence, and a **coach** that
raises one pattern at a time.

## The finish line

`python3 engine/calamity.py today` prints it. The day is finished when:

- 90% of the reviews that were due today are done (a few may always carry
  over),
- every topic failed today has been answered correctly again,
- the day's new topics are done (`new_per_day`, default 8, or fewer if
  fewer are unlocked), and each one is consolidated: answered right on a
  second item at least 20 minutes after the first (`pace.*` in
  `framework/config.md`; not in brush-up mode),
- the day's lectures are logged, if the learner set a lecture quota
  (`lectures_per_day`),
- every lecture that was logged has been tested. That holds even when the
  quota of new topics is used up: the quota limits what is taught in a day,
  not the testing of what was already watched.

The day's count of new topics includes what today's work will open: the
topics that follow in a syllabus and, when no lecture quota is set, the
topics behind the next lectures of a course.

A learner day runs from 04:00 to 04:00, so a session after midnight belongs
to the evening before. Change any number for one learner with
`python3 engine/calamity.py profile set cfg.new_per_day 12`.

The order inside a session is fixed by `next`: failed topics first, then
due reviews (most forgotten first), then new material, then lectures, then
a boss that has come due. Do not reorder it by taste. If the learner wants
something else today, do that, and return to `next` afterwards.

## Several skills at once

New material comes from the enrolled skills in turn. Every skill is a lane,
and the lane that has had the least new material today goes next, so Docker
and Java studied side by side alternate. GATE subjects are worked through
one at a time, in two lanes: the subjects that follow a course, in the
course's order, and the subjects studied without one, in triage order with
the subject already under way first.

- A lecture that was logged is tested before anything else.
- When it is the turn of a skill whose next topic sits behind a lecture
  that has not been watched, `next` answers `watch`, names the lecture, and
  says what could be started meanwhile. Offer both; the learner picks.
- `focus` in the profile puts skills ahead of all others:
  `python3 engine/calamity.py profile set focus docker`. An entry may be a
  skill id, a track id, or `gate` for every GATE subject.
- `next --skill <skill>` stays inside one skill for a session without
  changing the profile. Reviews still come from everywhere.

## Sleep

`sleep.start` and `sleep.end` in the profile define the learner's sleep
window. Inside it the engine answers `sleep`: say so once and let the
learner decide; do not start new material. In the hour before it
(`sleep_guard_minutes`) new material stops and only reviews run. Reminders
are never shown inside the window. If the learner regularly studies inside
it, that is a pattern for the coach, not a reason to move the window
silently.

## The day shape: `learner/schedule.md`

Learners here rarely keep fixed hours. The schedule is therefore a shape,
not a clock: a few blocks in an order, each with a purpose, sized to the
learner's stated total. Write it at onboarding with the learner; revise it
only on evidence.

The blocks live in the front matter, one line each,
`"HH:MM-HH:MM | name | purpose"`: `weekday` and `weekend`, and optionally
a day of the week with a shape of its own (`mon` ... `sun`). A block may
run past midnight; the day rolls over at `day_start_hour`. The body is the
learner's own view, in any form.

```markdown
---
updated: 2026-10-11
target_hours: 12
basis: stated at onboarding; no data yet
weekday:
  - "09:00-09:30 | Recall | due reviews across everything, first thing"
  - "09:30-12:30 | Deep block A | GATE lectures, each one tested straight after"
  - "12:30-13:30 | Workout"
  - "14:00-17:00 | Deep block B | the weakest GATE subject from triage; tests and past questions"
  - "17:30-19:30 | Build block | the 10x skill in progress, hands-on"
  - "20:00-21:30 | Contest hour | Codeforces set or upsolving"
  - "21:30-21:45 | Close | finish line, notes fragments, tomorrow's first lecture named"
weekend:
  - "10:00-10:30 | Recall | due reviews"
  - "10:30-13:30 | Mock or past paper | then its error review"
---

# Day shape

Recall first, two deep GATE blocks around a workout, then building and a
contest hour; the weekend is lighter, with a mock.

# This week

- two full mocks (Wed, Sun), each followed by an error review
- Codeforces: Div. 3 on Thursday, upsolve Friday

# Changes

- 2026-10-11: first version, from onboarding answers.
```

`python3 engine/calamity.py day [<day>]` prints a day's blocks with the
current one marked, its note and goals, and the finish line; the brief's
`Now:` line says which block a session falls in. One day that differs (an
exam, travel, time that will be lost) gets a note,
`python3 engine/calamity.py day note <day> "..."`, and goals are added
with `day goal "..." [--at HH:MM]`; both live in `learner/timetable.json`,
which `tools/timetable.py` also edits. A schedule written as tables under
`## Weekday` and `## Weekend` headings is read too;
`python3 engine/calamity.py day migrate` shows it in the one format and
`--write` rewrites it.

Rules for writing and changing it:

- Ask for the total the learner wants. Many aim for twelve or more
  productive hours a day including a workout; that is their choice to make.
  Say honestly what the log shows they sustain, and build up to a target in
  steps rather than writing a day they will not live.
- Put the hardest new material where their accuracy is highest
  (`python3 engine/calamity.py stats hours`), and reviews where it dips.
- Keep recall first. Reviews done late are reviews skipped.
- Every block names what it is for. Hours without a purpose are not a plan.
- A change is made with the learner, dated under `# Changes`, with the
  reason. Never rewrite the schedule silently.
- Workouts are part of the day: log them with
  `python3 engine/calamity.py workout <minutes>`.

## What the log can and cannot see

`python3 engine/calamity.py stats week` shows, per day, active time in this
repository, logged lectures with their stated length, logged workouts, and
their sum ("accounted"). It cannot see a contest on Codeforces, a book, or a
lecture that was not logged. Before reading a short day as a lost day, ask
what else happened, and log what can be logged.

## Behaviour patterns

`python3 engine/calamity.py stats patterns` reports what the last seven
days show, once there are at least four days of history:

| Pattern | What it means | A reasonable response |
|---|---|---|
| `late-night` | studying inside the sleep window on 3 or more days | move the window or protect it; ask which is true |
| `zero-days` | 2 or more recent days with nothing recorded | find the smallest session that would still have fitted |
| `review-backlog` | far more reviews due than are being done | pause new material for a day or two |
| `fragmented` | many sessions under ten minutes | one protected block of 45 minutes |
| `no-workout` | no workout in 3 days against a stated goal | move the workout slot |
| `daypart-dip` | accuracy clearly lower in one part of the day | move hard material out of it |
| `new-over-review` | new topics far above quota while reviews wait | reviews first tomorrow |

How to raise one:

- **One a day at most**, and only the one the engine marks `RAISE NOW`.
  The session brief shows it as "Behaviour pattern not yet raised today".
- **As a question, with the number.** "You studied past 01:00 on four of the
  last seven days. Is the sleep window wrong for you, or are late sessions
  eating into it?" No lecture, no praise sandwich.
- **At a natural pause**, never in the middle of a question.
- **Record it**, with what the learner said:

      python3 engine/calamity.py observe "raised late nights; wants sleep window moved to 02:00-09:00" --tag coach --pattern late-night

  The pattern then rests for a few days (`coach.cooldown_days`).
- If the learner decides to change something, change it (profile key or
  schedule) in the same turn. If they decide not to, record that and drop
  it.

The `habit-coach` agent does the weekly version of this: it reads the week,
compares it with the schedule and proposes at most three changes with the
evidence for each. It changes nothing itself. The coach skill puts the
proposals to the learner and edits `learner/schedule.md` for the ones they
accept.

## Reminders

Reminders are operating-system notifications that fire only when something
is due and never inside the sleep window.

    python3 engine/calamity.py remind render --times 09:00,14:00,20:30

writes the files for this machine under `.calamity/reminders/` and prints
the one command that installs them and the one that removes them (cron on
Linux, a LaunchAgent on macOS, Task Scheduler on Windows). The engine never
installs them itself: show the learner the install command and run it only
when they say so. Reminders are per machine; set them up again on a second
laptop.

## What is not built in

No points, no levels, no streaks, no leaderboards. Motivation here comes
from a visible finish line, a roadmap that fills in, review counts that
shrink when the work is done, and bosses that prove a skill. Do not invent
rewards or guilt on top of that.
