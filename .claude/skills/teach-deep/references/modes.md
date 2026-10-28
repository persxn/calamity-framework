# Modes

In-depth is the default and is described in SKILL.md. The learner can switch modes at any point ("let's go balanced", "just a quick brush-up on X"). Record the mode: `enroll <skill> --mode brushup` for brush-up, `--mode mastery` for in-depth and balanced (the engine's pace is the same for both), and write which of the two in the topic's `curriculum.md`.

## Balanced

For real understanding on a time budget.

- Origin story: full, but tighter.
- Vocabulary: the core 15–20 terms.
- Curriculum: still exhaustive and gap-free. Nothing is dropped from the *map*.
- Core units (the mental model, the main commands or APIs, internals that explain everyday behaviour): taught at full depth.
- Peripheral surface (obscure flags, niche options, rare subcommands): taught as grouped reference tables, each group with one scenario and one drill instead of individual deep dives.
- Field reading: docs and outages are kept; scale write-ups become optional.
- Recall, the coverage rule and interview-grade questions all work exactly as in in-depth mode.

## Brush-up

For revision, interview preparation, or a quick overview of something they once knew.

1. **Origin and core idea**: one paragraph on why it exists, plus the single sentence that captures it.
2. **The mental model**: one diagram plus the 3–7 core concepts.
3. **The 80/20 surface**: the commands, flags or APIs used most, with an example each.
4. **The classic gotchas**: the mistakes everyone makes.
5. **The top interview questions** for this topic, with tight model answers.
6. **A mixed drill**: 8–10 of the engine's items for the skill (`ask --skill <skill>`, stocked by the examiner if `item needs` lists the topics). Misses point to which units to study properly.

Finish by offering in-depth mode on any weak area. If the skill was studied in depth before, brush-up runs on the same engine record: its due reviews first (`ask --due --skill <skill>`), then the drill.
