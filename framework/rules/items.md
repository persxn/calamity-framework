# Writing items

An item is one question or exercise. It is written once, verified once
(`framework/rules/verification.md`) and never edited. This file is the
format and the quality bar for drafts.

## The draft

A draft is a JSON object; a batch is a JSON list of them. Save it in the
examiner's batch folder, `.calamity/tmp/examiner/<batch>/drafts.json`, and
store it with `item import --file <path> --by examiner`.

```json
{
  "type": "mcq",
  "topics": ["docker/multi-stage", "git-gh/daily-loop"],
  "difficulty": 3,
  "stem": "A Dockerfile has two stages, `build` and `run`. Only `run` ends in CMD. Which files end up in the final image?",
  "options": ["Everything from both stages", "Only what `run` contains, including what it copies with COPY --from=build", "Only the files named in CMD", "Nothing from `build` can be used"],
  "answer": "B",
  "solution": "The final image is the last stage. Earlier stages are discarded unless a later stage copies files from them with COPY --from.",
  "expect_s": 60,
  "source": {"kind": "generated"}
}
```

| Field | Rule |
|---|---|
| `type` | `mcq`, `msq`, `nat`, `short` (graded by the engine) or `code`, `task`, `open` (judged by running a check). |
| `topics` | Full keys. The first is the primary topic and decides the skill. Further topics are woven in: one correct answer credits them all. List a topic only if the item cannot be answered without it. |
| `difficulty` | 1 to 5 (see below). Use the one the work list asks for. |
| `stem` | The whole question. Markdown allowed. Everything needed to answer is in it. |
| `options` | `mcq`/`msq`: 2 to 8 options as a list (labelled A, B, C ... in order) or an object. |
| `answer` | `mcq`: one letter. `msq`: the letters, e.g. `"A,C"`. `nat`: a number, `{"value": 0.42, "tol": 0.01}` or `{"min": 0.41, "max": 0.43}`. `short`: a string, a list of accepted strings, or `{"accept": [...], "regex": "..."}`. |
| `solution` | Why the key is right, and why the tempting wrong answers are wrong. Required for engine-graded types. Shown after the answer. |
| `check` | `code`/`task`: the exact commands to run and what must be true to pass. |
| `rubric` | `open` (required), `code`/`task` (optional): the points a correct answer must contain. |
| `marks` | GATE items only: `1` or `2`. |
| `expect_s` | Seconds a prepared learner needs. Default by type: mcq 90, msq 120, nat 150, short 60, code and task 900, open 300; GATE items 90 for 1 mark and 210 for 2 marks. A correct answer slower than twice this counts as hard. |
| `objectives` | The numbers of the primary topic's objectives the item tests, as the NEED_ITEM block and `tree show` number them, e.g. `[2]` or `[1, 3]`. A second item on a topic should test another objective. Coverage of the objectives counts toward `solid` (60%) and `mastered` (all). |
| `strand` | Optional: `T` (theory), `P` (practice), `I` (implementation) or `N` (numerical). |
| `depth` | Optional: `recall`, `apply`, `analyse` or `transfer`. |
| `source` | `{"kind": "generated"}` for your own items. `official` needs `"ref": "GATE CS 2024 Q.31"`; `imported` and `manual` name where the item came from. |

How the engine grades:

- `mcq`, `msq`: letters, in any common form (`b`, `(B)`, `A and C`, `ACD`).
  A multiple-select answer must match the key exactly.
- `nat`: an integer key must be hit exactly. A decimal key such as `0.42`
  accepts half a unit of its last digit or 0.5%, whichever is larger. Give
  `min`/`max` when the paper states a range.
- `short`: compared after trimming, lower-casing and collapsing spaces,
  against every string in `accept`, then against `regex` (whole answer,
  case-insensitive). Use it only when the answer is one word, one number
  with a unit, one command or one identifier, and list every spelling a
  right answer could take. Otherwise write an `mcq`.

## Difficulty

| Level | The learner must |
|---|---|
| 1 | recognise or recall one fact |
| 2 | apply one idea to a plain case |
| 3 | apply it to a case with one twist, or combine two ideas |
| 4 | choose the idea among several, handle edge cases, or debug |
| 5 | design something or solve an unfamiliar problem with the idea |

## Quality bar

- **One idea per item**, plus the woven topics. If a learner fails, it
  should be clear what they did not know.
- **Test understanding, not only recall.** Prefer items that ask *why* —
  the mechanism, the reason, the trade-off — over items that only recall a
  fact or run a recipe. When a topic gets more than one item, at least one
  tests the mechanism or a trade-off; for a tool or command, at least one
  tests choosing or combining its flags for a stated goal.
- **Answerable from the stem alone.** No "as discussed", no reliance on a
  file the learner may not have.
- **Wrong options are real mistakes**: each distractor is what a specific
  misconception produces. No joke options, no "all of the above".
- **A different question each time.** Check the bank first
  (`item list --topic <key>`) and do not restate an existing item with new
  numbers unless the topic is a calculation.
- **Current.** If the answer depends on a version, name the version in the
  stem, and check the fact against the official documentation.
- **No trick wording.** Negations ("which is NOT") are marked in capitals
  and used sparingly.
- **Your own words.** Do not copy questions from books, courses or question
  banks. Official exam questions enter only as `official` items that the
  learner supplies, with their reference.

## Hands-on items

For tools, frameworks and programming, the default is an exercise that is
done, not described.

```json
{
  "type": "task",
  "topics": ["docker/multi-stage", "java/packaging"],
  "difficulty": 3,
  "stem": "In `learner/work/docker/ex-multistage/` there is a small Java service (created by this exercise's setup below). Write a Dockerfile that builds the jar in one stage and runs it from a JRE-only image as a non-root user.\n\nSetup: ...",
  "check": "docker build -t ex-ms . && docker run --rm ex-ms id -u | grep -vx 0 && docker image inspect ex-ms --format '{{.Size}}' | awk '$1 < 250000000 {ok=1} END {exit !ok}'\nRuns from inside the exercise folder. Passes when every command exits 0.",
  "rubric": ["two stages; the final stage has no JDK or build tool", "USER set to a non-root user", "dependency layer cached separately from the source"],
  "expect_s": 1200
}
```

- The stem says where the work happens (`learner/work/<skill>/<exercise>/`)
  and includes any setup the tutor must create first.
- The check is a short list of commands whose exit status or output decides
  the result, followed by one line that says what "pass" means. It must fail
  on an empty solution.
- A check runs from inside the exercise folder, so it never names
  `learner/work/` (the engine refuses one that does): the checker runs it on
  its own solution in a scratch folder, the tutor on the learner's work.
- A check runs only inside the exercise folder, needs no elevated rights,
  deletes nothing outside that folder and pulls nothing from the network
  except the project's own declared dependencies.
- `code` items state the function or program to write and are checked by
  tests: give the test commands and the cases, including edge cases.
- `open` items ask for an explanation or a design; the rubric lists what a
  correct answer contains. Use them sparingly: they are the weakest
  evidence.

## Weaving

The work list (`item needs --full`) names earlier topics under `embed`. Build them
into the exercise where a practitioner would really meet them: a Java
exercise that ends in a Dockerfile and a commit; a FastAPI endpoint whose
test needs a SQL join. List each embedded topic in `topics` after the
primary one. Do not bolt on an unrelated extra question; if an embedded
topic does not fit naturally, leave it out.

## Formats by track

- **GATE** (`gate*` skills): only `mcq`, `msq` and `nat`, with `marks` 1 or
  2, in the style and depth of the exam. Numerical answers state the
  required precision in the stem. No weaving across subjects.
- **Competitive programming** (`cp.*` skills): prefer `code` items checked
  by compiling with `g++ -std=c++17 -O2 -Wall -Wextra` and running against
  cases that include a brute-force comparison; `mcq` and `nat` for
  complexity, tracing and "which technique" questions. Judged Codeforces
  problems are credited with `cf credit`, not written as items.
- **Developer and AI skills**: `task` and `code` first, then `mcq`/`short`
  for concepts and for reading code or configuration.
- **Placement tests**: one item per topic at that topic's level, engine
  graded where possible, so a whole skill can be sampled in minutes.
