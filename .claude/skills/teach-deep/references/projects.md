# Build and ship

Projects turn knowledge into evidence. The aim is something *new* that people in the tool's community would find interesting, not another to-do app.

## Choosing a project

- **Fresh**: search GitHub, Reddit and the tool's community before committing, to check the idea isn't already saturated. If it exists, find the angle that doesn't: a missing feature, a new platform, a fresher stack, or a niche audience.
- **Combines skills**: draw on the current topic plus earlier topics the learner has secured (`tree show <skill>` lists where each stands), such as bash + Docker + a small API, or C + Linux internals.
- **Scratches a real itch**: the learner's own workflow, their college or community, or a pain they hit during the course.
- **Shows depth**: uses the boring corners they mastered (unusual flags, internals, performance tuning), so it proves mastery and not just familiarity.
- **Scoped in tiers**: a weekend micro-project, a 1–2 week project, and a capstone. Offer one of each and let the learner choose.

Example shapes (adapt to the topic and check freshness with a search): a terminal UI for something people currently do by hand; a tiny reimplementation of a core mechanism (a mini container runtime using namespaces, a toy Git using its object model); a linter or checker for a common mistake taught in the course; a visualiser for an internal (a page-table explorer, an image-layer inspector); a plugin or extension for the tool itself.

## Contributing upstream

For open-source tools, contributing to the tool itself is the strongest "think like the author" exercise there is.

- Find `good first issue` or `help wanted` labels, the contributing guide, and the code of conduct.
- Read the part of the source that matches a unit already learned. Trace one feature end to end.
- Start small (docs, tests, error messages are often welcome) and work up to code.

## Shipping it

A project nobody sees doesn't build a reputation. Guide the learner to:

- write a README with the problem, a demo GIF or screenshot, install, usage, design notes ("why it works this way"), and limitations
- add tests and CI, plus an open-source licence they choose
- share it where this tool's community actually gathers: find the relevant subreddits, Discord servers and Slack communities with a search, and **read each community's self-promotion rules** before posting
- write a short post about one interesting decision or bug from building it. This doubles as interview material.

Review their code as a senior engineer would, and tie review comments back to curriculum units.
