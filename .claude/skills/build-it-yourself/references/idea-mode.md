# Idea mode: from an idea to a design the learner can build

## 1. The brief (`brief.md`)

Have a conversation, two or three questions at a time, and stop as soon as you have enough:

- **The problem and the people**: who has this problem, how they solve it today, why that's painful.
- **Core flows**: the three to five things a user must be able to do in v1. Everything else is v2.
- **Scale and shape**: expected users and data, read-heavy or write-heavy, realtime or not, offline or not, platforms (web, mobile, CLI, desktop, hardware).
- **Distribution**: how people will get it (a URL, app stores, desktop installers, a package manager, a game storefront). This decides the shipping milestones and skills from day one.
- **Constraints**: time available, budget, where it will be hosted, team size, anything that must be used or avoided.
- **The learner's goals**: what they want to *learn* from building it, which roles they're targeting, and the skills they want on their resume. These decide tool choices as much as the requirements do.
- **What done looks like**: a demo, real users, an open-source release, or a portfolio piece.

## 2. Prior art and improvements

Search before designing:

- existing products and open-source projects that solve the same problem (GitHub, Product Hunt, Hacker News "Show HN", Reddit, app stores)
- how they're built, if open source (a quick recon with `repo_recon.py` on one or two is very effective)
- what their users complain about, which is where differentiation lives

Then suggest **improvements to the idea**, in a short list: a sharper core use case, a feature that makes it unlike the alternatives, a scope cut that makes v1 achievable, a technical angle that makes it interesting to show off. The learner decides. Record the decisions in `brief.md`.

## 3. Architect level

Run a **design diagnostic** unless the learner's level is already in state. Ask them to sketch, in 10–15 minutes and in words or a rough diagram, how they'd build *this* idea's core flow. Score what they produce:

| Signal | Novice | Developing | Ready to lead |
|---|---|---|---|
| Components and responsibilities | One big box | Sensible split, fuzzy boundaries | Clear boundaries and interfaces |
| Data model | Not considered | Entities but no relationships or constraints | Entities, relationships, access patterns |
| Failure and edge cases | None | Some, when prompted | Raised unprompted |
| Scale and performance | None | Vague ("add caching") | Specific bottlenecks and remedies |
| Trade-off reasoning | Picks the familiar | Names alternatives | Weighs alternatives against the requirements |

From the scores, choose a level, and say which one you chose:

- **Guided** (mostly novice): propose 2–3 candidate architectures (for example, a modular monolith vs a BaaS-backed client vs services plus a queue), each with a diagram, pros and cons, what it would teach, and its risks. The learner chooses and **writes the ADR** justifying the choice; you review the ADR.
- **Co-design** (mostly developing): the learner drafts each section of the design doc. You ask probing questions ("what happens when two users edit the same item?", "where does this run when your laptop is off?") and offer options only when they're stuck.
- **Learner-led** (mostly ready): the learner writes the whole design. You run a **design review** like a staff engineer (below). Improvements and tool suggestions arrive as review comments, not as a rewrite.

The learner can always request a level. Move them up when they've handled two reviews well.

## 4. The design doc (`design.md`)

Use `assets/templates/design-doc.md`: context, goals and non-goals, requirements (functional and non-functional), architecture (component diagram), data model (ER diagram), API or interface sketch, key flows (sequence diagrams), tech choices (each linked to an ADR), the failure modes and how they're handled, security, observability, deployment, milestones (they come later, from the build path), and open questions.

Diagrams are Mermaid. Render them with `mmdc` to make sure they parse.

## 5. Design review checklist (any level)

- **Requirements fit**: does every core flow have a home? Is anything over-engineered for the stated scale?
- **Boundaries**: are the responsibilities clear? Look for coupling and a big ball of mud, and ask what has to change together.
- **Data**: are the access patterns supported by the model and its indexes? Consistency needs? Migrations?
- **Failure modes**: a dependency down, a slow network, a duplicate request (idempotency), a partial failure, retries, data loss, a poison message.
- **Scale**: the first bottleneck at 10× and at 100×, and what you'd change at each.
- **Security**: authentication and authorisation, secrets, input validation, the OWASP basics relevant here, multi-tenant isolation.
- **Operability**: logs, metrics, health checks, deploys, rollback, backups.
- **Cost**: hosting cost at the expected scale, and free-tier limits.
- **Buildability**: can *this learner* build it in the time they have? Ask what to cut.

Write each comment with severity (must, should, consider), the reason, and the question that would lead the learner to fix it themselves.

## 6. Tool selection

For each layer that needs a tool, present a short comparison, never a single answer:

| Option | Fits because | Watch out for | What you'd learn | Maturity / community |
|---|---|---|---|---|

Principles:

- **Requirements first, then learning goals.** If the learner targets backend roles, a choice that teaches backend fundamentals (Postgres, a real API layer) beats a BaaS that hides them, unless shipping fast is the stated goal.
- **Boring by default, one exciting thing on purpose.** Mature tools for most layers, and at most one newer tool the learner especially wants to learn.
- **Verify currency.** Search for current versions, maintenance status and recent breaking changes before recommending anything. Mention newer alternatives (mastery-coach's "what's new").
- **Cost and lock-in**, stated honestly.

Each final choice becomes an ADR (`assets/templates/adr.md`), written by the learner.
