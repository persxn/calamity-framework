# The skill tree

Everything the tutor teaches hangs off one tree of 150 skills. Each skill
is a file in `framework/tree/<track>/`: what it needs first, what mastery
covers, the boss that proves it, and, for exam and contest skills, its
topics.

## What is in it

| Track | Skills | Shipped topics | What it covers |
|---|---|---|---|
| `10x` Developer | 77 (7 capstone milestones) | written per learner | From a first terminal to production: Linux, Git, networking, HTML/CSS, JavaScript, TypeScript, bundlers, React (or Vue, Svelte), Tailwind, state and data fetching, testing (Jest, Playwright or Cypress), REST, OpenAPI, GraphQL, WebSockets, gRPC, tRPC, Node, Express (or Fastify, NestJS), Next.js, Python and FastAPI, Java and Spring Boot, SQL, PostgreSQL, MongoDB, Prisma, Redis, auth, Docker, Compose, CI (GitHub Actions or Jenkins), Kubernetes, Terraform, observability, security, system design, Android (Kotlin or Flutter) |
| `ai` AI engineering | 17 (2 milestones) | written per learner | Linear algebra, calculus, probability; the Python data stack; classical ML; deep learning; transformer internals; serving models; LLM fundamentals, local models with Ollama, LangChain, RAG (with Qdrant, or without a vector store), evaluation, agents |
| `cp` Competitive programming | 35 (7 rating milestones) | 194 | C++ and the STL, then algorithms and data structures by Codeforces rating band, with milestones from 1200 to 2200 |
| `gate` GATE, every paper | 1 | 16 | General Aptitude |
| `gate-cs` GATE CS | 13 | 119 | Every subject of the Computer Science and Information Technology paper |
| `gate-da` GATE DA | 7 | 89 | Every subject of the Data Science and Artificial Intelligence paper |

Developer and AI skills ship a scope instead of a fixed topic list. The
first time you study one, the `curriculum-architect` agent writes your
syllabus (8 to 25 topics, each a 20 to 40 minute idea) from the scope and
the current official documentation, fitted to what you already know. It
lives in `learner/syllabus/<skill>.md`.

## Looking around

```bash
python3 engine/calamity.py dash roadmap --all-tracks   # every skill, by track and group
python3 engine/calamity.py tree show docker             # one skill: needs, unlocks, topics, your standing
python3 engine/calamity.py tree path mern-stack         # the route to a goal, in layers
python3 engine/calamity.py tree suggest                 # what to start next
python3 engine/calamity.py find containers              # search skills, topics, lectures, notes
```

Or ask: "what does Kubernetes need?", "how do I get to full-stack?", "what
should I learn next?".

Status symbols: `✓` mastered or known, `◕` ready (it unlocks what depends on
it), `◐` learning, `○` open to start, `·` locked, `‖` paused, `✗` dropped.
Add `--ascii` where a terminal cannot show them.

## Routes and parallel skills

`tree path <goal>` lays the route out in layers. Skills in one layer can be
learnt side by side; each layer needs the one before it. The hours shown
are estimates from the skill files, and say so.

Several skills studied at once take turns: the one that has had the least
new material today goes next, so Docker and Java alternate. Earlier skills
are **woven** into exercises of later ones where practitioners really meet
them: a Java exercise can end in a Dockerfile and a commit, and one correct
answer credits every topic it used.

## Alternatives

Some prerequisites accept any one skill of a group (a **slot**). A route
follows the member you are on; enrol in another and the route follows it.

| Slot | Shipped members |
|---|---|
| `language` | javascript, python, java, kotlin |
| `frontend-framework` | react, vue, svelte |
| `state-management` | redux |
| `animation` | framer-motion, gsap |
| `e2e-testing` | playwright, cypress |
| `backend-framework` | express, fastify, nestjs, fastapi, spring-boot |
| `ci` | github-actions, jenkins |
| `android-app` | android-release (Kotlin), flutter-release (Flutter) |
| `rag` | rag-qdrant, rag-vectorless |

## Changing the tree

Your changes live in `learner/tree/` and override the shipped files, so a
framework update never undoes them. Ask in plain words:

- **"Add Rust"**: Claude searches first; if the skill is truly missing,
  the `curriculum-architect` agent designs it (prerequisites, scope, a boss
  with checks that can be run) and it is added with `tree add`.
- **"Fastify instead of Express"**: enrol in the alternative; it shares the
  slot, so everything downstream accepts it.
- **"Skip Terraform"**: `tree drop`. If other skills depend on it, Claude
  shows you which and what they will miss before you confirm. A dropped
  prerequisite counts as met; `tree restore` brings the skill back.
- **"Docker now, Linux later"**: `enroll docker --force`; Claude names the
  prerequisites you are skipping and weaves their basics into early
  exercises.

## Already knowing something

A skill you claim to know is checked with a **placement test**: one verified
question per topic, back to back, no teaching and no solutions until the
end. What you get right enters the review rotation as known; the gaps are
taught in their turn. A skill is marked known on the strength of a test,
not of a statement. If you would rather skip a skill untested, drop it.

## Mastery and brush-up

Each skill is studied in one of two modes (`enroll <skill> --mode brushup`):

| | Complete mastery | Brush-up |
|---|---|---|
| For | learning a skill properly | refreshing something once known |
| Starts | from the first topic | with a placement test, then only the gaps |
| A topic is solid after | 3 correct answers on verified questions on 2 or more days, 80% recent accuracy, memory strength of 7 days | 1 correct answer on a verified question |
| A skill unlocks the next ones at | 60% of its topics solid | 50% |
| Finished when | every topic mastered (memory strength 21 days, 4 different questions answered correctly) and the boss passed | every topic solid |

These numbers are defaults in `framework/config.md`; you can change any of
them for yourself (see [how it works](how-it-works.md#configuration)).

## Bosses and milestones

A **boss** is the project or timed test that proves a skill. It comes up
when every topic is solid. A project boss has a brief and a list under
"Passes when"; each line is checked by running it, and one failed check is
a fail (which costs nothing: fix it and try again). Skills without a
project boss, such as the GATE subjects, are proved by a timed mixed test.

**Milestones** (`mern-stack`, `fullstack-production`, `ten-x`, `ai-capstone`
and the others) have no topics: they are a capstone project over several
sessions. The competitive-programming milestones (`cp.rating-1200` to
`cp.rating-2200`) are passed by your Codeforces rating itself, recorded when
`cf sync` sees it.

## Adding a skill to the framework itself

To add a skill for everyone rather than for yourself, see
[CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-skill-to-the-tree).
