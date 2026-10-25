# Reverse mode: tearing down a repository

The output of this phase is `teardown.md` (template in `assets/templates/teardown.md`): an evidence-backed account of what the project is, how it works, and how it came to be. Everything later — the skill map, the milestones, the comparisons — is built from it, so accuracy matters more than speed.

## 0. Scope

- Get the repository URL (or local path), and ask what the learner wants from it: the whole thing, or one part ("just the realtime sync", "just the CLI")? A large monorepo usually means picking a slice.
- Note the licence from the recon. MIT, Apache or BSD: the learner may reuse code with attribution, although in this skill they won't copy anyway. GPL or AGPL: anything derived must stay under the same licence. Source-available (BUSL, Elastic) or no licence at all: studying is fine, but republishing or reusing code isn't. Tell the learner in one line what that means for publishing their rebuild.
- If the target is (or includes) a shipped app, such as release binaries, an installer, an APK or a live site, follow `shipped-apps.md` for that part.

## 1. Recon (deterministic first map)

```bash
python3 <skill-dir>/scripts/repo_recon.py https://github.com/owner/repo --out <project-dir>/source
```

This prints a markdown report and saves `recon-<name>.json`. It covers:

- languages by lines (vendor and build directories skipped)
- every manifest found, with its dependencies, and a **detected stack** grouped by category (from a fixed list of well-known packages, so it's incomplete by design; read the manifests yourself for anything unfamiliar)
- infrastructure: Dockerfiles and their base images, Compose services, CI workflows and their triggers, Terraform, Kubernetes manifests, deploy targets, **env var names** from `.env.example` (each external service usually shows up here)
- entry points: `main` functions, web-app constructors, server `listen` calls, package scripts
- data-layer hints (schemas, migrations, models), tests by directory, and the docs worth reading first
- **git archaeology**: the first commits, when each top-level area first appeared (and whether it was later removed, which signals a rewrite), the most-changed source files, and tags
- GitHub releases with asset names, when `gh` is authenticated. To see how a release is packaged, download an asset and run `artifact_recon.py` on it (`shipped-apps.md`).

Then read the README, the `docs/` folder, any ARCHITECTURE file, ADRs and CONTRIBUTING. Authors often explain their design there.

## 2. Architecture recovery

Work from the outside in, and **cite `path:line` for every claim**:

1. **Boundaries.** What runs as a separate process or deployable (from Compose, Dockerfiles, package workspaces, `cmd/` directories)? What external services does it talk to (from env var names, SDK dependencies, config)?
2. **Modules.** For each deployable, map the top-level directories to responsibilities. Find the layering (routes → controllers/services → data access) and note where it's broken.
3. **Dependency direction.** Which modules import which? A quick check: `grep -rn "^import\|require(" src | ...`, or a dependency graph tool if one is available (madge, pydeps, `go mod graph`). Flag tight coupling and cycles; these become vocabulary and review material.
4. **Configuration.** How config gets in (env vars, files, flags), the defaults, and secrets handling.
5. **Cross-cutting concerns.** Auth, validation, error handling, logging, caching, background jobs, rate limiting, i18n. Find *where* each lives.

Draw a **component diagram** in Mermaid (deployables, modules, external services, the arrows between them). Render it with `mmdc` to make sure it parses.

## 3. Trace real flows end to end

Pick the 2–4 most important user actions (sign up, create the core object, the main read path, one background job). For each, follow the code from the edge to storage and back:

```
HTTP POST /api/articles  → routes/articles.ts:42 (validation: zod schema at :18)
  → services/article.service.ts:77 createArticle()  → slug generation :91
  → prisma.article.create  (schema.prisma:23)  → response mapper :130
```

Turn each into a **sequence diagram**. If the project runs locally without much effort, run it and confirm a trace with real logs or requests. These traces are the best teaching material in the whole teardown.

## 4. Data model

Extract the entities, their relationships and their constraints from schemas or migrations. Draw an ER diagram. Note indexes, cascades, soft deletes and how IDs are generated. Read the migration history in order: it is the story of how the data model evolved.

## 5. Techniques: the reason to study this repo

List the non-obvious things the author did, each with its location and *why* it was done:

- patterns (repository, middleware chain, dependency injection, event sourcing, actor model, plugin system)
- algorithms and data structures (fuzzy matching, diffing, rate limiting, consistent hashing, CRDTs)
- performance tricks (batching, caching layers, streaming, memoisation, connection pooling)
- reliability (retries with backoff, idempotency keys, graceful shutdown, health checks)
- security (password hashing parameters, token rotation, CSRF, input sanitisation)
- developer experience (codegen, scripts, the test setup, CI shape, release automation)

Also note **what you'd do differently** and why. Repos aren't scripture: weaknesses make good review material and interview talking points.

## 6. Archaeology: how the author actually built it

From the recon's git section plus a closer look (`git log --reverse --stat | head`, `git show <first-commit> --stat`, the tag dates):

- What did the first commit contain? That's the author's real "walking skeleton".
- In what order did features arrive? Those commits read almost like a milestone list.
- What got rewritten, and when? (Areas marked *since removed*.) Look for big refactor commits and read their messages. Rewrites teach design better than the final code does.
- Where is the churn (the most-changed source files)? Complexity and bugs live there.

Use this order to shape the build path, simplified, while keeping the author's lesson: start small, then grow.

## 7. Walk the learner through it

Present the teardown conversationally, as the author would, in chunks:

1. The origin: why this project exists, what it replaced, who it's for. Use the README, the first commits and the author's own words where available.
2. The big picture: the component diagram, a minute per box.
3. One flow, traced live: "Open `routes/articles.ts` at line 42…" Have the learner open the files and follow along.
4. The data model.
5. The techniques, one at a time, each with a quick check question.
6. The archaeology story.

Then check understanding with questions in mastery-coach style before moving on to the skill map: "Which file would you change to add rate limiting? Why there?"

## Big or unfamiliar repos

- Use the Explore agent, or several reads in parallel, for broad sweeps, but read the files on the critical paths yourself.
- If the stack includes something you can't verify from the code (a custom DSL, a proprietary service), say so in the teardown. Don't guess.
- For a huge monorepo, tear down the slice the learner chose, and list the rest as "out of scope".
