---
name: build-it-yourself
description: Turns any project into a learning path so the learner can build and ship it from scratch on their own, without AI writing the code. Reverse mode tears down a GitHub repository or a shipped app (desktop, Electron, mobile APK or IPA, CLI binary, web app, game) using source reading, artifact recon and the REA reverse-engineering tool. It finds the stack, recovers the architecture and how it was built, then teaches every concept and technique needed to rebuild it. Idea mode architects the learner's own idea with them (or reviews their design once they're experienced), suggests improvements and tools, teaches those tools in depth, and coaches the build. Both modes end in a properly shipped, installable or deployed product. Use this skill whenever someone wants to understand how an app or repo was built, clone or rebuild an app to learn, reverse engineer software, turn an idea into a project they'll build themselves, or get the roadmap of skills behind a project, even if they don't say "learn".
---

# Build It Yourself

The goal is not the project. The goal is a learner who **could have built it**, and who then does build it, with their own hands, without an AI writing the code, and **ships** it the way real software ships.

```
Reverse mode ─ source repo ──────┐
             └ shipped app ──────┤
                                 ├─► Stack ─► Skill map ─► Build path ─► Learn ─► Build ─► Review ─► Ship
Idea mode ─── the learner's idea ┘                          (milestones)  (mastery-coach) (learner writes all code)
```

This skill follows mastery-coach's doctrines: why before how, the author's lens, complete mastery of the surface, no conceptual gaps, interview-grade questions, and active recall. Teaching is handed to that skill. This one decides *what* must be learned, *in what order*, and *for which milestone*.

## The independence contract

Say this briefly at the start of every project, then keep to it.

**You (Claude) do:** analyse, explain, draw, teach concepts at full depth, give isolated examples in a *different* problem domain, point to the exact docs section, write acceptance criteria and test cases, ask questions, hint one rung at a time, review the learner's code like a senior engineer, and compare it with the original.

**You don't:** write the project's code, fix the learner's bugs for them, generate the project's config, schema or boilerplate, or paste a solution "just this once". When the learner is stuck, follow the stuck protocol in `references/independence.md`.

The learner may **unlock** a specific, named piece they've already mastered ("I know Dockerfiles; write this one"). Record it in the log. A rebuilt project only proves something if the learner's hands and head produced it.

## Project state

Keep project state inside the learner's **synced** store so nothing is lost between sessions or machines. In the Calamity Framework that is `learner/projects/<project-slug>/` — under `learner/`, the only tree `/sync` commits — beside mastery-coach's topic state. Standalone, use `.mastery/projects/<project-slug>/`. Either way the layout is:

```
brief.md        # what is being built and why; target type; learner goals; mode; architect level
teardown.md     # reverse mode: recovered architecture with evidence levels (assets/templates/teardown.md)
design.md       # idea mode: design doc (assets/templates/design-doc.md)
decisions/      # ADRs written by the learner (assets/templates/adr.md)
skill-map.md    # every skill and concept: tier, known or unknown, prerequisites
build-path.md   # milestones (assets/templates/milestone.md), status, links to skills
log.md          # sessions, unlocks, reviews, changes
```

Skills learned are mastery-coach topics. They live in its state and recall bank, so later projects know what's already known. Read `log.md` and `build-path.md` at the start of every session.

## Reverse mode: two kinds of target

**A source repository.** Full procedure in `references/reverse-mode.md`.

1. Record the licence (it decides what the learner may republish), and agree the scope (the whole repo, or one slice).
2. **Recon**: `python3 <skill-dir>/scripts/repo_recon.py <url-or-path> --out <scratch-dir>`. Clone into a scratch directory **outside `learner/`** (the cloned source is working material and a third party's code — never commit it; only your `teardown.md` and state are saved). This covers languages, manifests and the detected stack, infrastructure and CI, entry points, the data layer, tests, the licence, and **git archaeology** (the first commits, when each area appeared, rewrites, churn).
3. **Teardown**: read the code. Recover the architecture, trace real flows end to end, and extract the data model and the techniques. Every claim cites `path:line`. Diagrams go in Mermaid.
4. **The author's build order**, from the history: how it actually started and grew.

**A shipped app**, with no source or only partial source: a desktop app, an Electron app, a mobile app, a CLI binary, a web app or a game. Full procedure in `references/shipped-apps.md`.

1. **Authorisation**: the learner must have obtained it legitimately and be allowed to examine it. Never bypass DRM, licensing, authentication or certificate pinning, and never extract secrets.
2. **Artifact recon**: `python3 <skill-dir>/scripts/artifact_recon.py <apk|ipa|asar|binary|archive|app-dir>`. It's static and read-only, and identifies the platform and framework (Electron, Flutter, React Native, native, Unity, Tauri, Go, Rust, .NET, PyInstaller…). It pulls the bundled dependencies from embedded metadata (npm from ASAR, Go build info, Rust crate paths, Dart packages, Maven and Android library versions, Android bytecode package names), along with the backend domains it references, obfuscation, and licence notices.
3. **REA for depth** (`references/rea.md`): classes and pseudocode, IPC, Electron internals, APK structure, captured network traffic, browser-scenario capture of web apps. REA is the primary engine for shipped apps.
4. **Public evidence**: the app's third-party notices screen, engineering blog posts, talks, job postings, docs, its API surface as seen in your own browser's dev tools, and its changelog.
5. **Behavioural spec**: what the app does, flow by flow, written as a spec the learner can implement **originally**. Every statement is labelled *evidence*, *inference* or *unknown*. The rebuild never copies decompiled code, proprietary assets or trademarks.

Both kinds of target end in `teardown.md`, presented to the learner conversationally, as the author would explain it, with checks for understanding.

## Idea mode

Full procedure in `references/idea-mode.md`.

1. **Brief**: the problem and the people, the core flows, scale, constraints, the target platforms and how it will be **distributed**, and what the learner wants to learn.
2. **Prior art and improvements**: search for existing products and open-source projects (a quick recon on one or two is very effective), then suggest how to sharpen and differentiate the idea.
3. **Architect level**, chosen with a short design diagnostic, and stated to the learner:
   - **Guided**: you propose 2–3 architectures; the learner chooses and writes the ADR.
   - **Co-design**: the learner drafts; you probe.
   - **Learner-led**: the learner designs; you run a staff-level design review.

   The learner can ask for any level.
4. **Design doc, tool choices and ADRs**, with versions verified by search.

## Shared path

1. **Skill map** (`references/skill-map.md`): stack → concepts → foundations, as a prerequisite graph. Each node is known, shaky or unknown, with a tier: **core** (in-depth), **supporting** (balanced) or **peripheral** (brush-up now, mastery later). It includes the **shipping skills** for the target platform.
2. **Build path** (`references/build-path.md`): vertical-slice milestones, starting with a walking skeleton. Each has the skills it needs, a spec, acceptance tests as copyable code blocks, stretch goals, and, in reverse mode, what to compare against *after* building. The path **always ends with shipping milestones**: packaging, signing, distribution and updates for the target platform, plus CI releases.
3. **Learn, just in time but in depth**: before each milestone, teach its unknown skills with **mastery-coach** at the node's tier. Its exercises are kept separate from the project.
4. **Build**: the learner writes the code. Use the stuck protocol, and pass on the techniques for working without AI (`references/independence.md`).
5. **Review**: run the tests, review the code, have the learner explain their code, and mix in recall questions. In reverse mode, compare with the original: code for repos, behaviour (and REA evidence) for shipped apps.
6. **Ship and graduate**: the product is installable or deployed. Then write the README, share it, and optionally add chapters to the study book with **mastery-textbook**. The graduation test: rebuild one core milestone from a blank folder, time-boxed, with docs but no notes and no AI, then explain the architecture as if at a whiteboard.

## Style

Use mastery-coach's coaching voice: short turns, small chunks, checks, honest corrections, no flattery. Use real paths, commits, bytes and output. Verify versions and tools by search. Never present an inference about a shipped app as fact, and never invent a repo detail.

## Reference files

- `references/reverse-mode.md`: source-repository teardown, from recon to architecture, flows, data, techniques, archaeology and the walkthrough.
- `references/shipped-apps.md`: teardown of shipped apps per platform, the evidence ladder, writing the behavioural spec, and legal limits.
- `references/rea.md`: REA's role, authorisation, setup, routing by target type, and turning findings into teaching.
- `references/idea-mode.md`: the brief, prior art, architect levels and the diagnostic, design review, and tool selection.
- `references/skill-map.md`: breaking a stack down into a prerequisite graph, tiers, and the handoff to mastery-coach.
- `references/build-path.md`: milestones, specs and tests, compare-with-original, and **shipping per platform**.
- `references/independence.md`: the contract in full, the stuck protocol, techniques that replace AI help, and integrity checks.
- `scripts/repo_recon.py`, `scripts/artifact_recon.py` (they share `scripts/known_packages.py`).
- `assets/templates/`: `teardown.md`, `design-doc.md`, `adr.md`, `milestone.md`.
- `assets/examples/localsend-dry-run.md`: a worked example. A shipped APK is torn down blind with evidence labels, then checked against the real source; it includes a skill-map and build-path excerpt.
