# Syllabi and placement

A skill file says what mastery covers (its `# Scope`). The list of topics a
particular learner works through is that learner's **syllabus** for the
skill: `learner/syllabus/<skill>.md`. GATE subjects and
competitive-programming skills ship with topics already; developer and AI
skills ship with a scope, and the syllabus is written when the learner
starts the skill, so that it fits them and matches today's documentation.

## When a syllabus is written

- A skill is enrolled and `python3 engine/calamity.py tree show <skill>`
  reports "no syllabus yet".
- The learner asks for a different shape (shorter, deeper, another order).
- The official documentation has moved and a topic no longer matches it.

The `curriculum-architect` agent writes it. Give the agent the skill id and
what is known about the learner; it reads the rest itself.

## Procedure

1. Run `python3 engine/calamity.py syllabus template <skill>`. It prints the
   exact file shape, the target path and the scope.
2. Read the learner's side: `profile show`, `observations`, the skills they
   already have (`tree list --status mastered`, `--status known`,
   `--status ready`) and their goals.
3. Read the current official documentation for the skill and note the
   pages used. Do not rely on memory for versions, commands or APIs.
4. Write the file, then run `python3 engine/calamity.py syllabus check <skill>`
   and fix every error it reports.

```markdown
---
skill: docker
written: 2026-10-11
sources: [https://docs.docker.com/get-started/, https://docs.docker.com/build/]
---

# Topics

## images-containers | Images and containers
level: 1
- say what an image is and what a container is, and start, stop and remove one
- read `docker ps` and `docker images`

## dockerfile | Writing a Dockerfile
needs: [images-containers]
level: 2
- write a Dockerfile for a small program and explain each instruction
```

## Rules

- **8 to 25 topics.** One topic is one idea that can be taught and tested in
  20 to 40 minutes. If it needs more, split it.
- **Objectives are things the learner does**: "write", "explain why",
  "debug", "choose between". Each bullet must be testable by an item.
- **Order by dependency.** List topics so that every `needs` comes earlier.
  `needs` names topic ids of the same skill only.
- **Cover the whole scope**, and end with a topic that pulls the skill
  together in the direction of its boss.
- **Something hands-on in the first topic.** No topic called "Introduction"
  with nothing to do.
- **`level`** is the difficulty items start at (1 to 5).
- **Ids are permanent.** Progress is stored under `<skill>/<topic-id>`. Use
  short lower-case words joined by `-`.

## Fitting the learner

- A novice gets finer steps at the start; an experienced learner gets the
  basics merged into fewer topics and more depth later.
- Emphasise what their goal needs. Someone heading for `mern-stack` learns
  MongoDB through its Node driver; someone heading for data work does not.
- Use their stated preferences (examples first, theory first, the language
  they think in) in how objectives are phrased.
- Do not drop a part of the scope because the learner says they know it.
  Keep the topic and let a placement test show it.

## Placement tests

A placement test finds out what is already known so that it is not taught
again. Use it when a learner claims prior knowledge, and always at the
start of a brush-up.

1. Sample the syllabus: one verified, engine-graded item per topic (or per
   cluster of closely related topics for a long syllabus), at that topic's
   level. Have the examiner and checker prepare them as usual.
2. Ask them back to back without teaching and without showing solutions:
   `ask --topic <key>`, then `answer <item> --answer "..." --kind placement`.
   The flag matters. With it, a right answer counts as evidence without
   using up the day's new topics, and a miss on a topic never studied
   schedules nothing: the topic simply stays in the queue to be taught.
   Without it, every miss comes back as a failed review ten minutes later.
3. Record the outcome with topic ids:

       python3 engine/calamity.py placement <skill> --known a,b,c --gaps d,e

   - Topics answered correctly already carry their own evidence. List under
     `--known` those and any topic that a correct answer clearly implies.
   - `--result known` (only when there are no gaps) marks the whole skill
     as a met prerequisite and keeps its topics in the review rotation.
4. Enrol the skill so the gaps are scheduled. They arrive through `next` as
   new material, in syllabus order. An item missed in the test is not fresh
   evidence on the same day, so the gaps need new items (`item needs`).

A skill is marked `known` on the strength of a test, not of a statement. If
the learner prefers to skip a skill without being tested, that is their
decision: drop it from their tree (`tree drop`), which records it as skipped
rather than as known.

## Changing a syllabus later

- **Add** topics freely.
- **Rename** a topic id: change it in the file, then run
  `python3 engine/calamity.py rename topic <skill>/<old> <skill>/<new>` so
  its history follows.
- **Split** a topic: keep the old id for the part closest to what was
  tested, add new ids for the rest.
- **Remove** a topic: delete it from the file. Its history stays in the log
  and it leaves the review rotation.
- **Replace a shipped syllabus** (a GATE subject, a competitive-programming
  skill) by writing `learner/syllabus/<skill>.md`. It replaces the shipped
  list entirely, so carry over every topic that still applies and keep the
  shipped ids: lecture mappings and the links between equivalent topics of
  two exam papers depend on them.
