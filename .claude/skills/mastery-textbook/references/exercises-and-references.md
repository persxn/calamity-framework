# Exercises and references

## Exercises

Every chapter ends with an exercise set the reader can complete using **only this chapter and earlier ones** (mastery-coach's coverage rule). If a great exercise needs something not yet in the book, add that to the text first, or move the exercise to a later chapter.

Difficulty, shown as stars:

| Level | Kind | What it tests |
|---|---|---|
| 1 | Recall | Definitions, what a flag does, a key fact |
| 2 | Apply | Use it: write the command or code, predict the output, read this log |
| 3 | Interview | Mechanism traces, why-by-design, trade-offs, find the bug, scale it up |
| 4 | Project | Design or build something that combines this chapter with earlier ones |

A typical set has 8–15 exercises: about a third at level 1, a third at level 2, most of the rest at level 3, and one at level 4. Also include:

- **Retrieval from earlier chapters**: at least two exercises that need an earlier chapter's material combined with this one (for example, a bash chapter's exercise that also uses `ls -A` from chapter 1). Say which chapter is being revisited only in the solution, not in the question.
- **Read the signal**: one exercise built on real output, logs or an error.
- **Audit the AI**: from time to time, a plausible flawed solution to find and fix.
- **Hands-on**: at least one exercise run on the reader's own machine, with what to observe.

Keep wording precise. An exercise should have one defensible reading, unless the ambiguity is the point (and then say so).

## Solutions

Every exercise has a solution in `solutions/chNN.tex`, linked by its label. Good solutions:

- give the answer, then the **reasoning**, at the same depth as the chapter
- name the **tempting wrong answer** and why it's wrong, when there is one
- for level 3, show what a strong interview answer covers, plus a likely follow-up question
- for level 4, give a reference design or outline and the key decisions, not a full project
- point back to the section that teaches each step (`\cref{sec:...}`)

## References

Every claim about the outside world (history, versions, defaults, company practices, incidents, statistics) is cited. Prefer, in order:

1. **Primary sources**: official documentation (the specific page), specifications and RFCs, man pages, the source code (a file at a tagged version), release notes.
2. **Original authors**: design papers, creators' talks and posts, the original announcement.
3. **Post-mortems and engineering blogs**, from the company itself.
4. **Classic books** on the topic.
5. Secondary write-ups, only when nothing better exists.

**Verify before citing.** Fetch the page or find the publisher record, confirm that it says what you claim, and record the access date. Never cite from memory, and never invent a title, author, year or URL. If you can't verify a source, leave the claim out or mark it as unverified in the text.

### BibTeX entries

```bibtex
@book{arpaci-ostep,
  author    = {Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau},
  title     = {Operating Systems: Three Easy Pieces},
  publisher = {Arpaci-Dusseau Books},
  year      = {2018},
  howpublished = {\url{https://pages.cs.wisc.edu/~remzi/OSTEP/}}
}

@misc{rfc9110,
  author = {R. Fielding and M. Nottingham and J. Reschke},
  title  = {{RFC} 9110: {HTTP} Semantics},
  howpublished = {\url{https://www.rfc-editor.org/rfc/rfc9110}},
  year   = {2022},
  note   = {Accessed 2026-10-25}
}

@misc{cloudflare-2019-outage,
  author = {{Cloudflare}},
  title  = {Details of the {Cloudflare} outage on {July} 2, 2019},
  howpublished = {\url{https://blog.cloudflare.com/...}},
  year   = {2019},
  note   = {Accessed 2026-10-25}
}
```

These entries are examples of the format: verify the details of any entry before using it. Web sources are `@misc` with `howpublished = {\url{...}}`, a `year`, and `note = {Accessed YYYY-MM-DD}`; the check warns when the access date is missing. Protect capitals that must survive with braces: `{GNU}`, `{HTTP}`, `{Linux}`. Never put an `@` in `refs.bib` outside a real entry.

### Further reading

End each chapter with 3–6 annotated items. Each one says what it is, why it's worth the reader's time, and which part to read: "The *Exec form* section of the Dockerfile reference [n]: read the warning about signal handling, then reread \cref{sec:pid1}."
