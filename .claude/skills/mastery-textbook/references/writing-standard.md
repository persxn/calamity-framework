# Writing standard

The target is the feeling a reader gets from the best technical books. *Code* (Petzold) builds a computer from relays without ever losing the reader. *Operating Systems: Three Easy Pieces* asks "the crux of the problem" before solving it. *Designing Data-Intensive Applications* makes trade-offs feel inevitable. *Pro Git* draws the object model until Git stops being magic. Readers of those books say the same things: *it explained why*, *I could finally picture it*, *it never assumed something it hadn't taught*, *I read it like a novel*. Write for that reaction.

## Voice

- **The author speaking to one smart reader.** Use "you", be warm and direct, and keep a quiet confidence. No hype, no filler, and no "simply", "obviously" or "just", which make a struggling reader feel stupid.
- **Precise without being stiff.** Say the plain version first, then the exact version. Use the field's terms once they're defined, and use the *same* term every time (the glossary decides which). Don't switch between synonyms for variety.
- **Concrete before abstract.** Show a real command, a real number or a real failure, then generalise from it.
- **One idea per paragraph.** The first sentence says what the paragraph is for. Short paragraphs, mostly active voice.
- **Signpost.** Say where we are and where we're going: "We now have a register. To compute anything we need to wire it to an ALU, and that is the next section." End sections with an open loop into the next one where it's natural.
- **Honest.** Say when something is a simplification and where it breaks: "This picture ignores caches; Chapter 9 adds them." Never present a guess as fact.

## From chat to book

Session material is raw input, never the text itself. When turning it into a chapter:

- Rewrite from scratch, in the book's voice. Drop the back-and-forth, false starts and "great question".
- Reorder into the chapter anatomy below. Chat follows the learner's path; the book follows the clearest path.
- Fill in what the chat glossed over. Anything the learner had to ask about is something the book must explain *before* the reader needs it.
- Turn learner mistakes into *Common misconception* boxes and exercise items, written generally ("a common mistake is…"), never naming the learner.
- Lift the best analogies and diagrams from the session, polished, and add where each analogy breaks down.

## Chapter anatomy

A chapter adapts this skeleton to the topic. Order matters; length per part varies.

1. **Opening hook (half a page).** A puzzle, a surprising fact, or a failure the reader can't yet explain, plus a promise of what they will be able to do by the end.
2. **Origin and motivation.** In the first chapter of a topic this is the full origin story (an *Origin story* box plus prose): the world before, who built it and why, the core idea, the philosophy, what it replaced. In later chapters, the specific pain this feature removes.
3. **Definitions.** An *In plain words* box, then a *Definition* box with the precise version. New terms go into that chapter's vocabulary list.
4. **The mechanism (the core of the chapter).** The author's lens: descend to the layer that makes it make sense (see mastery-coach's curriculum depth standard), with figures, step-by-step traces, and *Under the hood* boxes for the deepest detail. Use *Designer's note* boxes for "why it is built this way" and the alternatives the designers rejected.
5. **Hands-on.** Installation if it's new to the reader, then the smallest working example with real captured output, then *Try it* boxes the reader can run.
6. **The full surface.** Every flag, option or API in this chapter's scope, in grouped tables (what it does, when you'd want it), followed by prose on the non-obvious ones. Obscure entries get a niche scenario. Platform differences (GNU vs BSD, version changes) are stated explicitly.
7. **Case studies.** Three to five realistic scenarios, each needing a different part of the surface. Answer *when to use what* and *why not the alternative*.
8. **In the wild.** One or more of: an *At scale* box (how a large company runs this, cited), an *From the outage files* box (the decision, the failure chain, the lesson, cited), and a *When the AI gets it wrong* box (the typical AI mistake in this area and how to catch it).
9. **Gotchas and misconceptions.** The traps, each with *why* it happens.
10. **Interview corner.** Two to four questions this chapter equips the reader to answer, with what a strong answer must contain.
11. **Chapter summary.** Five to eight bullets, each a complete sentence the reader could say in an interview.
12. **Vocabulary.** Every term introduced, with a one-line definition.
13. **Exercises.** See `exercises-and-references.md`.
14. **Further reading.** Annotated: one sentence each on *why* to read it and what to look for.

## Book-level features

- **A running example.** Pick one realistic system or task early on and return to it in every chapter, so ideas accumulate on something familiar.
- **Cross-references, both ways.** Look back ("recall from \cref{sec:inode}…") and forward ("we'll see in \cref{ch:perms} why…"). They are the book's prerequisite graph, made visible.
- **Consistency.** Same terms, same notation, same figure style, same box meanings throughout. When a convention changes, update the earlier chapters.
- **The preface ("How to use this book")** is written once two or three chapters exist, and updated as the book grows.

## Sentence-level polish (check every paragraph)

- Does every sentence earn its place? Cut throat-clearing ("It is important to note that…").
- Is each term defined before its first use?
- Could a careful reader misread this? If so, rewrite it.
- Are numbers, flags, paths and output exact and verified?
- Do long paragraphs hide two ideas? Split them.
- Would a figure or table say this better than prose? Then make one, and let the prose point at it.
