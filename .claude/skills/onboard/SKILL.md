---
name: onboard
description: "First-run setup for a new learner, a new track or a new machine. Use when the brief says NOT ONBOARDED, when the learner adds GATE, competitive programming, the developer path or AI, or on a laptop not set up yet."
argument-hint: "[machine | gate | cp | 10x | ai]"
effort: high
---

# Onboard

Set up the machine, learn who the learner is, and leave them with a first
session ready to start. Ask; never assume. Nothing about a learner is
prefilled from anywhere but their own answers and their own accounts.

If arguments were given: `machine` means do only step 1 (a second laptop);
a track name means do only that track's part of step 3, then steps 4 to 6.

## 1. This machine

    python3 engine/calamity.py doctor

Read the result. Then tell the learner in one sentence what the next
command does and run it (they will be asked to approve it):

    python3 engine/calamity.py setup --hook

It writes a machine id under `.calamity/` and a session-start hook into
`.claude/settings.local.json`. Neither is ever committed. The hook prints
the session brief when a session opens; it takes effect from the next
session. Offer the status line (`setup --statusline`) as optional. If
`doctor` reports a failure, fix it before going on. On Windows run the same
commands with `python engine/calamity.py` or `py -3 engine/calamity.py`;
`setup` prints the form that works on this machine.

## 2. The learner

Ask a few questions at a time (the question tool where it exists,
otherwise plain text), and record each answer as you get it.

| Ask | Record |
|---|---|
| What should I call you? | `profile set name "..."` |
| What do you want from this: which of the developer path, AI engineering, competitive programming, GATE, or one particular skill? | `profile set tracks 10x,cp,gate-cs` (ids: `10x`, `ai`, `cp`, `gate-cs`, `gate-da`) |
| Where do you want to get to first? | `profile set goals mern-stack,cp.rating-1400` (skill or milestone ids; `find` helps) |
| Starting fresh, or refreshing things you once knew? | `profile set mode.default mastery` or `brushup` |
| How do you like to be taught? (examples first, theory first, short answers, a language you think in) | `profile set teach.style --text "..."` |
| When do you usually sleep? | `profile set sleep.start 01:00`, `profile set sleep.end 08:00` |
| How many productive hours a day are you aiming for, workout included? Do you work out, and for how long? | `profile set daily.target_hours 12`, `profile set workout.minutes 60` |
| Do you want reminders on this laptop, and at what times? | `profile set reminders.times 09:00,14:00,21:00` (set them up with the remind skill) |

Record each group of answers in one call, `key=value` pairs, quoting a
pair with spaces:

    python3 engine/calamity.py profile set name=Robin tracks=gate-da mode.default=mastery "teach.style=examples first"

Do not suggest answers to personal questions, and do not carry a number
over from another learner or from an example in these files.

## 3. Each track they chose

- **Developer path (`10x`) or AI (`ai`)**: ask what they can already do.
  For a skill they claim, plan a placement test rather than taking their
  word or doubting it (`framework/rules/syllabus.md`). Show the route to
  their goal: `python3 engine/calamity.py tree path <goal>`. Where the route
  has a choice (language, framework), ask which they prefer and enrol that
  one. Read `framework/rules/tree-editing.md` if they want skills added or
  removed.
- **Competitive programming (`cp`)**: follow
  `framework/rules/cp-onboarding.md` (handle, `cf link`, `cf sync`, target),
  then delegate the first plan to the `cp-coach` agent.
- **GATE**: follow
  `framework/rules/gate-onboarding.md` (year, papers, registration, target,
  source), connect their course or playlist with the bridge skill, run
  `python3 engine/calamity.py gate enroll`, then delegate the first plan to
  the `gate-strategist` agent.

## 4. First enrolments

    python3 engine/calamity.py tree suggest
    python3 engine/calamity.py enroll <skill>

Enrol what they will actually start this week: one or two skills from the
developer or AI track, the next skills of the competitive-programming
route, all GATE subjects. Several skills can run side by side; the engine
interleaves them and weaves earlier ones into later exercises.

## 5. A first day shape

Write `learner/schedule.md` with the learner, following "The day shape" in
`framework/rules/scheduler.md`: a few blocks in order, each with a purpose,
sized to the total they gave. Mark it as a first version with no data
behind it yet.

## 6. Finish

    python3 engine/calamity.py profile set onboarded true
    python3 engine/calamity.py dash
    python3 engine/calamity.py today

Tell them, briefly:

- A day is: open Claude Code here, answer the recall questions, then
  `/study`. `/today` shows the finish line, `/dash` the progress, `/log`
  records a lecture watched elsewhere.
- Everything about them lives under `learner/`. To carry it between laptops
  and keep it safe, it should be pushed to a repository of their own,
  private unless they want their study log public: `/sync` does it when
  they ask.
- On a phone, a session can be continued with Remote Control.

Then offer to start the first session now.
