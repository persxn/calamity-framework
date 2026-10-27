# Your first session

You have Claude Code installed, the framework cloned, and Claude Code open
in its folder with the folder trusted (see the setup guide for
[Linux](setup-linux.md), [macOS](setup-macos.md) or
[Windows](setup-windows.md)). Type:

```
/onboard
```

Onboarding takes ten to fifteen minutes. Nothing about you is assumed or
filled in from examples: every setting comes from an answer you give, and
Claude records each one as you give it.

## 1. This machine

Claude runs `doctor` and tells you what it found. Then it offers to run
`setup --hook`, which does two things on this computer only:

- records the machine's name and the Python command that works here in
  `.calamity/machine.json` (the very first engine command, even `doctor`,
  already gave the machine its name), so that each laptop writes its own
  log file and two laptops never edit the same file;
- installs the **session-start hook** in `.claude/settings.local.json`. From
  the next session on, Claude Code runs the engine as each session starts
  and Claude reads a short brief of where you stand before you type
  anything. The **key guard** comes with it: before Claude reads, searches
  or runs a shell command, it checks that the call cannot reach a
  question's sealed answer.

Both files stay on this machine and are never committed. Claude Code asks
for your approval before `setup` runs; you can say no and run it later.
Without the hook, Claude runs the brief by hand at the start of a session.

## 2. You

A few questions at a time:

| Question | Recorded as |
|---|---|
| What should I call you? | `name` |
| What do you want: the developer path, AI engineering, competitive programming, GATE, or one particular skill? | `tracks` (`10x`, `ai`, `cp`, `gate-cs`, `gate-da`) |
| Where do you want to get to first? | `goals`, as skill or milestone ids from the tree |
| Starting fresh, or refreshing what you once knew? | `mode.default`: `mastery` or `brushup` |
| How do you like to be taught? | `teach.style`, in your words |
| When do you usually sleep? | `sleep.start`, `sleep.end` |
| How many productive hours a day, workout included? | `daily.target_hours`, `workout.minutes` |
| Reminders on this laptop, and when? | `reminders.times` (set up later with `/remind`) |

They are stored in `learner/profile.md`. Claude records a group of answers
in one engine call, for example:

```
python3 engine/calamity.py profile set name=Sam tracks=10x goals=mern-stack mode.default=mastery
```

## 3. Each track you chose

- **Developer path or AI**: Claude asks what you can already do. A skill
  you claim is checked with a short placement test instead of being taken
  on trust (or doubted). It shows the route to your goal, which choices the
  route makes for you (a language, a framework, a CI system), and asks
  which you prefer. See [the skill tree](skill-tree.md).
- **Competitive programming**: your Codeforces handle (or none yet), the
  language you compete in, a target rating and date. Claude links the
  handle, syncs your record and has the `cp-coach` agent write a first plan.
  See [competitive programming](competitive-programming.md).
- **GATE**: the year and paper, whether you have registered, your paper's
  date once known, a target, past mocks, what you study from (a course or
  playlist is connected with `/bridge`), and how many hours a day go to
  GATE. All subjects of your paper are enrolled and the `gate-strategist`
  agent writes a first plan. See [GATE](gate.md).

## 4. First skills and a day shape

Claude runs `tree suggest`, enrols what you will actually start this week,
and writes `learner/schedule.md` with you: a few blocks in order, each with
a purpose, sized to the hours you gave. It is a first version with no data
behind it, revised later from what the log shows (`/coach`).

## 5. Done

Claude marks you as onboarded, shows `dash` and `today`, and offers to
start studying. From now on a day looks like [daily use](daily-use.md)
describes.

## What the first study session looks like

Type `/study`, or simply say "let's start".

1. **The item bank is stocked in the background.** Practice questions do
   not ship with the framework. The `examiner` agent writes them for the
   topics coming up, and the `checker` agent solves each one blind,
   computing wherever it can, without ever seeing the key. Only questions
   whose independent answer matched the sealed key reach you. This takes a
   minute or two the first time; Claude teaches meanwhile.
2. **Surprise recall** opens every session once you have something to
   review. On day one there is nothing yet.
3. **One small chunk, then a test.** One idea, one worked example, one thing
   for you to do. Then a verified question, shown exactly as the engine
   prints it. You answer in your own words; multiple-choice, numeric and
   short answers are graded by the engine, hands-on work by running its
   check.
4. **The result, at once.** Right: one line, and on. Wrong: the key and the
   solution, one question to find out why, a few lines to repair it. The
   kind of mistake (concept, method, careless, misread, ...) is recorded,
   and the topic comes back within minutes and again in later sessions.
5. **Close.** Where today's finish line stands, a notes fragment for each
   topic you met, and a reminder that `/sync` keeps your progress safe.

Developer and AI skills ship a scope rather than a fixed list of topics:
the first time you study one, the `curriculum-architect` agent writes your
syllabus from the skill's scope and the current official documentation.
