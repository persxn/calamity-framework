---
name: explain
description: "A deep, from-scratch explanation of any topic, ad-hoc and untracked, taught to the full Calamity depth standard: why before what, layman words then the term, the inner mechanics, a worked example and a compact recap."
when_to_use: "When someone asks to explain a topic, teach them something, or how or why something works — outside a tracked study session."
user-invocable: true
---

# Explain a topic, deeply

This is the entry for an **ad-hoc** "explain X / teach me X / how does X
work". It is not a tracked study session and it does not touch the engine
record — but it teaches to the **same depth standard as everything else
here**, so a casual question gets a real lesson, not a shallow summary.

The failure this fixes: a quick question answered with the popular
one-paragraph surface. Guard against it.

## Before you teach

Read `framework/method-teaching.md` — the non-negotiable depth standard —
and follow it. For a tool or a large topic where the learner wants real
mastery, also read `.claude/skills/teach-deep/SKILL.md` and teach that fuller
arc. Do not teach from memory of the surface.

## How to teach it

Teach the Calamity arc, scaled to the topic (a small idea needs a few
chunks; a big one needs many). In plain words first, then the precise term:

1. **Why it exists / what breaks without it.** Start from the problem it was
   invented to solve and what people did before. Make the learner *feel* the
   need before naming the thing.
2. **The idea, in layman's words.** One clear mental model they can picture.
3. **The inner mechanics.** How it actually works and *why* it behaves that
   way, not only what it does — with an ASCII diagram, a memory/state trace,
   or a step-by-step walk-through. Use an analogy, then say where it breaks.
4. **A worked example**, simplest first, then a realistic one. Prefer the
   learner's own code or problem. Hands-on topics: they run it.
5. **Where it is really used**, a short case or two, and the history if it
   earns its place.
6. **Trade-offs: "why not X?"** the alternatives and when *not* to reach for
   it.
7. **The compression close** (`method-teaching.md`): the mental model, the
   key relationships as `A → B → C`, the precise definitions and exam/
   interview terms, three to seven must-remember points, and one
   reconstruction question that asks them to rebuild the mechanism.

## Sequence it so it feels inevitable

Teach prerequisites first, in the order where each idea makes the next one
obvious; define every new word before you use it (taught before tested). If
the topic rests on something the learner does not have, teach the smallest
necessary piece, then return — do not derail into the whole prerequisite.
Adapt the depth to the topic and to how the learner reacts; short turns, one
idea at a time, check understanding by asking them to explain it back, not
"does that make sense?".

## Make it stick (offer, do not force)

This lesson is not recorded, so nothing schedules its review. If the learner
wants it to last:

- `/study` — study the topic on the engine (spaced recall, verified items,
  progress) if it is in their tree.
- `/mastery-coach` — full, deep mastery of a tool or topic, even one the tree
  lacks (it creates the skill first).
- `/notes` — save what was taught as notes to keep.

Name the one that fits at the end, in a line. If they are new to Calamity,
say in a sentence what tracking would add.

## Honesty

Check facts that change (APIs, versions, flags, dates) against the official
source before teaching them, and say when you could not. Plain words over
jargon; never trade correctness for simplicity.
