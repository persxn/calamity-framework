# The Calamity Framework

A learning system that runs inside [Claude Code](https://claude.com/claude-code).
Clone it, open Claude Code in the folder, and you have a tutor that teaches
in small chunks, tests each one at once, brings old material back
unannounced, and keeps an honest record of what you can actually do.

It ships with three tools built on one method:

- **Adaptive tutor** for development, programming, maths and AI: a skill
  tree of 150 skills with prerequisites, a route to any goal, and exercises
  that weave earlier skills into the one you are learning.
- **GATE companion** (CS and DA): follows you through your own course or
  playlist, tests every lecture the day you watch it, plans backwards from
  the exam date, and ranks subjects by marks per hour.
- **Competitive programming coach**: reads your Codeforces record, finds
  what is holding your rating back, sets problems just above your level,
  and reviews your contests.

Your progress is plain text in the `learner/` folder. Push it to a
repository of your own and continue on any laptop.

## Requirements

- [Claude Code](https://code.claude.com/docs), installed and signed in
- Python 3.9 or newer (standard library only; nothing to install)
- git
- Optional: a TeX distribution (Tectonic, TeX Live or MiKTeX) to turn your
  notes into PDFs

Linux, macOS and Windows are supported.

## Start

```bash
git clone <address of this repository> calamity
cd calamity
claude
```

Accept the workspace trust prompt. The repository's permission rules are in
`.claude/settings.json`: they let Claude run the engine and edit your files
under `learner/`, and nothing else without asking. Then type:

```
/onboard
```

Onboarding sets up this machine, asks who you are and what you want to
learn, and enrols your first skills. Nothing about you is assumed: every
setting comes from an answer you give.

## A day

Open Claude Code in the folder. A short brief of where you stand is loaded,
and the session starts with a few recall questions on things you learnt
earlier. Then:

| Command | What it does |
|---|---|
| `/study [skill]` | A session: recall, then one small chunk at a time, each tested at once |
| `/recall` | Only the questions that are due, as fast as you can answer |
| `/today` | Today's finish line and the next thing to do |
| `/dash [roadmap\|queue\|gate\|cp\|week]` | Your progress, roadmap and revision queue as text |
| `/log <source> <lecture>` | Record a lecture watched elsewhere; its test follows |
| `/tree [path <goal>\|add\|drop]` | The skill tree: what a skill needs, the route to a goal, add or drop skills |
| `/boss [skill]` | The project or timed test that proves a skill |
| `/notes [skill]` | Your notes: a fragment per topic, a LaTeX section on request, a PDF per skill |
| `/gate`, `/cp` | The GATE companion and the competitive programming coach |
| `/coach` | A review of how you have actually been working, and your schedule |
| `/bridge` | Connect a course site, playlist or book so its lectures appear in your plan |
| `/remind` | Operating-system reminders that fire only when something is due |
| `/sync` | Commit and push your progress to your own repository |

You can also just talk: "teach me Docker", "what should I do today", "I
finished lecture 14", "quiz me".

There are no points and no streaks. Each day has a finish line you can
count (reviews due, new topics, lectures); reaching it is the day done.

## What is in the tree

| Track | Skills |
|---|---|
| `10x` Developer | From a first terminal to production: Linux, Git and GitHub, networking, HTML/CSS, JavaScript, TypeScript, bundlers, linting, React (or Vue, Svelte), Tailwind, Framer Motion or GSAP, Redux, TanStack Query, Jest, Playwright or Cypress, REST API design, OpenAPI, GraphQL, WebSockets, tRPC, Node, Express, Fastify, NestJS, Next.js, Python and FastAPI, Java and Spring Boot, SQL, PostgreSQL, MongoDB, Prisma, Redis, JWT and OAuth2, Docker, Compose, GitHub Actions or Jenkins, Kubernetes, Terraform, Prometheus and Grafana, testing, security, system design, Android (native Kotlin or Flutter), and capstone milestones |
| `ai` AI engineering | Linear algebra, calculus, probability; the Python data stack; classical ML; deep learning; LLM fundamentals, Ollama, LangChain, RAG with Qdrant, vectorless RAG, evaluation, agents |
| `cp` Competitive programming | C++ and the STL, then algorithms and data structures by rating band, with Codeforces rating milestones from 1200 to 2200 |
| `gate`, `gate-cs`, `gate-da` | General Aptitude and every subject of the two papers, topic by topic |

Several skills can be learnt side by side. Routes show which skills can
run in parallel and which must wait. The tree changes on request: add a
skill it lacks, choose an alternative (Fastify instead of Express), take a
placement test to skip what you know, or drop what you do not want.

## Your data

- Everything about you is under `learner/`: a log of what you did, your
  practice questions, your syllabi, your notes. See `learner/README.md`.
- To keep it and to move between laptops, push it to a repository of your
  own (private unless you want your study log public). `/sync` does this
  when you ask and never on its own.
- On a second laptop: clone your repository, open Claude Code, run
  `/onboard machine`.
- On a phone, continue a session with Claude Code's Remote Control.

## What it does on your machine

- The engine (`engine/`) is a Python program with no dependencies. It reads
  and writes files inside this folder.
- It contacts one outside service, Codeforces, through its public API, and
  only when you link a handle and sync. No password is involved.
- `/onboard` asks before installing the session-start hook, which is
  written to `.claude/settings.local.json` on your machine and never
  committed. `/remind` asks before adding reminders to your scheduler.
- Course sites are connected only in ways their terms allow. The framework
  never stores passwords, cookies or tokens, and never copies course
  content: it records which lectures you have finished.
- There is no telemetry.

## What it does not do

- It does not ship a question bank or any course's material. Practice
  questions are written for you and verified before you see them; official
  past papers are added by you.
- It cannot promise a rank or a rating. It shows what your record supports
  and what is still missing.
- Subject weights for GATE start as planning estimates and are marked as
  such until you replace them with counts from official papers.

## How it works

```
CLAUDE.md          what Claude loads every session
framework/         the method, rule books, skill trees, exam facts
.claude/skills/    the slash commands
.claude/agents/    specialist agents: examiner, checker, curriculum architect, coaches
engine/            the scheduler and record keeper (spaced repetition, mastery, plans, dashboards)
learner/           you
```

Claude teaches and asks; the engine decides what is due and keeps the
record. Every answer is an event in an append-only log, and schedules,
mastery and dashboards are recomputed from that log, so two laptops that
have synced always agree. Reviews are scheduled with FSRS. A question
reaches you only after a second agent has solved it blind and its answer
matched the sealed key.

`framework/MAP.md` is the index of everything; `framework/method.md` is the
method.

## Maintaining the framework

```bash
python3 engine/calamity.py selftest    # the engine's tests
python3 engine/calamity.py doctor      # health of this checkout
python3 engine/calamity.py tree check  # validate the skill tree
```

On Windows use `python engine/calamity.py ...` or `py -3 engine/calamity.py ...`.

- Skills are single files in `framework/tree/<track>/`. Add one, run
  `tree check`.
- Defaults live in `framework/config.md`. Exam facts live in
  `framework/gate/<year>.md` with their source and the date they were read.
- Learners get updates with `/update-framework`; their data is never
  touched by one.
- Keep the published repository free of anyone's `learner/` data. If you
  maintain the framework and also study with it, study in a second clone
  whose `origin` is a private repository of your own (`/sync` sets that up
  and keeps the framework as `upstream`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| No brief at session start | Run `/onboard machine` to install the hook; Claude runs the brief by hand until then |
| `python3` not found on Windows | Use `python` or `py -3`; `/onboard` records which one works |
| Glyphs look wrong in the terminal | Add `--ascii` to `dash` and `tree` commands |
| "no TeX engine" when building notes | Install Tectonic, TeX Live or MiKTeX; the `.tex` files are ready meanwhile |
| Codeforces sync fails | Check the connection; if Claude Code's sandbox is on, allow `codeforces.com` |
| Something looks off | `python3 engine/calamity.py doctor` |

## Credits and licence

Review scheduling is a port of FSRS by Open Spaced Repetition (MIT); see
`engine/THIRD_PARTY.md`. Add a `LICENSE` file for the framework itself
before publishing it.
