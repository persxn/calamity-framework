# Proposal: hands-on coding to mastery

**Asked by:** Jojo, 2026-10-29 · **Status:** the small, rules-only part
shipped in 2.1.0 (below); the rest awaits Jojo's decision · **Written
by:** Claude (Opus 5.5) in Claude Code

## The problem

In a Compiler Design lesson the tutor pasted a complete C lexer and asked
for two missing cases. The learner read a finished program and typed two
lines. Reading code you are given feels like learning, but very little of
the skill of writing it transfers. Jojo asked for every "write this
program" moment to be hands-on: a description of what the code must do,
the signatures in words, hints per part, and a live watch on the file that
makes a suggestion every 30 seconds. They also asked how to go further,
towards mastery.

## What 2.1.0 ships (rules, prompts and a small script; no engine change)

- `framework/rules/hands-on-coding.md`, the one protocol: the brief (what
  the program and each part do, signatures in words and as empty stubs, a
  sample run, the check, hints held back), what the tutor may and may not
  write, the faded ladder, predict before run, the live watch, judging,
  one step deeper after a pass, and the rewrite from memory.
- `framework/scripts/watch.py`: polls the file every 30 seconds by content
  hash, prints one line per change for Claude Code's Monitor tool, and can
  run one cheap check (a syntax-only compile) on each change. Standard
  library only; read-only.
- Every skill, agent and reference that asks for code points to it:
  `method.md`, `method-teaching.md`, the tutor style, `study`,
  `mastery-coach`, `teach-deep` (and `lesson-anatomy`, `projects`,
  `questions-and-recall`), `build-it-yourself` (and `build-path`,
  `independence`), `cp` and the CP playbook, `practice`, `boss`,
  `items.md`, `examiner`, `checker`, `drill-smith`, and the textbook's
  exercise standard.
- A behaviour eval, `code-exercise-is-hands-on`: asked for a lexer
  exercise, the tutor gives a brief and stubs and no finished lexer.

## Techniques, the evidence, and what each would change

| # | Technique | Evidence | Change | Priority | Effort | State |
|---|---|---|---|---|---|---|
| 1 | Faded worked examples, completion problems | Renkl, Atkinson et al. 2002, 2003; van Merriënboer 1990 | The faded ladder, rungs 0 to 4 | high | S | **shipped** |
| 2 | Less support as skill grows | Kalyuga et al. 2003 (expertise reversal) | Up a rung after a clean pass, down after a fail; never kept on rung 0–1 | high | S | **shipped** |
| 3 | Subgoal labels in examples | Morrison, Margulieux, Guzdial 2015 (mixed results in CS) | Rung 0's steps labelled by purpose | medium | S | **shipped** |
| 4 | Predict, then run (PRIMM) | Sentance, Waite, Kallia 2019 | Predict before any program runs; a wrong prediction is traced | high | S | **shipped** |
| 5 | Tracing before writing | Lister et al. 2004; Xie et al. 2019 | Tracing tables after a wrong prediction | high | S | **shipped** |
| 6 | Self-explanation, explain your code | Chi et al. 1989 | After a pass: explain two lines, change a requirement live, or break it | medium | S | **shipped** |
| 7 | Retrieval practice | Roediger, Karpicke 2006 | Rewrite-from-memory seeds, written by the examiner as `code` items on the engine's schedule | high | S | **shipped** (by seeds) |
| 8 | Immediate, focused feedback (deliberate practice) | Ericsson et al. 1993 | The live watch: one short suggestion per change, hints counted | high | S | **shipped** |
| 9 | A predict-the-output item in every code topic's family | as 4 | The examiner's families include one engine-graded predict item per code topic | medium | S | proposed |
| 10 | An engine `watch` command | — | `calamity watch <file>` with language-aware checks it chooses itself (a syntax-only compile per language), so the existing `Bash(calamity *)` rule covers it without pre-approving any command a `--check` names | medium | M | proposed |
| 11 | The rung on the record | as 1, 2 | `answer --rung N` on code items; `stats` shows the rung per topic; `next` suggests the rung | medium | M | proposed |
| 12 | Parsons problems | Ericson, Margulieux, Rick 2017 | A `parsons` item type: shuffled lines (with distractors) to order, graded by the engine; a cheap rung between 0 and 1 | medium | M | proposed |
| 13 | Tests first, scored by mutants | Edwards 2004 | A `tests` drill: the learner writes the tests from the brief; the check runs them against the drill-smith's sealed mutants, and passes when they catch them all | high | M–L | proposed |
| 14 | Spaced rewrite as its own family | as 7 | The engine schedules a rung-4 rewrite of every passed code topic by itself, without a seed | medium | M | proposed |
| 15 | Mistake patterns in code | as 8 | The tutor tags recurring bug kinds seen in watch events (off-by-one, unchecked end of input, aliasing) with `observe`; the `learning-analyst` reads them in the weekly review | medium | S–M | proposed |
| 16 | Productive failure | Kapur 2008 | Sometimes the problem before the lesson, at rung 3, then the teaching | low | S | proposed: conflicts with "taught before tested", so only on Jojo's say |
| 17 | Interleaving, desirable difficulties | Rohrer, Taylor 2007; Bjork 1994 | Already in the engine (woven items, mixed recall); add mixed "which technique" code sets outside CP | low | S | proposed |
| 18 | Pair programming cadence | McDowell et al. 2006 | A "pair" session: the learner drives and thinks aloud, the tutor navigates with the watch; roles never swap to the tutor typing | low | S | proposed |
| 19 | The rule where the tutor always looks | lessons of WP-30 (on the plugin route the engine's output is the one text always read) | `ask` and `item show` print one line under a `code` item: brief and stubs, no finished program, the watch (`framework/rules/hands-on-coding.md`) | high | S | proposed: a small engine change |

S is under a session, M two or three, L four or more (the plan's sizes).

## Recommended next, in order

1. **#19, the one-line reminder in the engine's output for `code` items.**
   The cheapest way to make the rule hold on the plugin route, where the
   rule books may never be opened. A small engine change.
2. **#13 tests first, scored by mutants.** It trains the habit that most
   separates a professional from a student, and it reuses the drill-smith
   and checker pipeline that already seals fixtures. New drill type: an
   engine change.
3. **#10 `calamity watch`.** It removes the one permission prompt the watch
   needs today and makes the check safe by construction. Engine change.
4. **#9 and #14**, so retrieval of code is automatic rather than left to
   the tutor remembering a seed. #9 is rules-only; #14 is an engine change.
5. **#11** once a few weeks of rung notes exist, to see whether the ladder
   is moving.

The rest are cheap but less certain; #16 needs a decision on purpose, since
it inverts the taught-before-tested rule.

## Limits

- The watch runs only while the session is open, and every event costs a
  turn: about 60 events in a 30-minute exercise at most, fewer in practice
  because an unchanged file prints nothing. "quiet" turns it off.
- The first arm asks the learner's permission: the script is deliberately
  not pre-approved, because a rule for it would also pre-approve whatever
  `--check` runs (#10 fixes this).
- The evidence above is mostly from introductory courses, mathematics and
  physics; it was not tested on this framework. The subgoal-label results
  in computing were mixed.

## Sources

- Renkl, Atkinson, Maier, Staley (2002), "From example study to problem
  solving: smooth transitions help learning", *Journal of Experimental
  Education* 70(4); Renkl, Atkinson (2003), *Educational Psychologist*
  38(1), 15–22. Summary of backward fading:
  <https://faculty.engineering.asu.edu/mre/wp-content/uploads/sites/31/2020/02/Exp_Rev_LI06.pdf>
- van Merriënboer (1990), "Strategies for programming instruction in high
  school: program completion vs. program generation", *Journal of
  Educational Computing Research* 6(3), 265–285:
  <https://research.utwente.nl/en/publications/strategies-for-programming-instruction-in-high-school-program-com/>
- Kalyuga, Ayres, Chandler, Sweller (2003), "The expertise reversal
  effect", *Educational Psychologist* 38(1), 23–31:
  <https://ro.uow.edu.au/edupapers/136>
- Morrison, Margulieux, Guzdial (2015), "Subgoals, context, and worked
  examples in learning computing problem solving", ICER '15:
  <https://digitalcommons.unomaha.edu/compsicfacproc/61>
- Sentance, Waite, Kallia (2019), "Teaching computer programming with
  PRIMM: a sociocultural perspective", *Computer Science Education*
  29(2–3), 136–176: <https://qmro.qmul.ac.uk/xmlui/handle/123456789/57800>
- Lister et al. (2004), "A multi-national study of reading and tracing
  skills in novice programmers", ITiCSE working group report:
  <https://www.cs.auckland.ac.nz/~j-hamer/ITiCSE04-wg.pdf>
- Xie et al. (2019), "A theory of instruction for introductory programming
  skills", *Computer Science Education* 29:
  <https://faculty.washington.edu/ajko/papers/Xie2019IntroCSTheoryOfInstruction.pdf>
- Chi, Bassok, Lewis, Reimann, Glaser (1989), "Self-explanations", *Cognitive
  Science* 13, 145–182:
  <https://education.asu.edu/lcl/publications/chi-m-t-h-bassok-m-lewis-m-reimann-p-glaser-r-1989-self-explanations-how-students>
- Roediger, Karpicke (2006), "Test-enhanced learning", *Psychological
  Science* 17(3), 249–255:
  <https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf>
- Ericsson, Krampe, Tesch-Römer (1993), "The role of deliberate practice in
  the acquisition of expert performance", *Psychological Review* 100(3);
  a critical review: <https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.01134/epub>
- Bjork (1994), desirable difficulties:
  <https://www.psychologicalscience.org/observer/desirable-difficulties>
- Rohrer, Taylor (2007), interleaved practice, cited in Rohrer, Dedrick,
  Burgess (2014): <https://link.springer.com/article/10.3758/s13423-014-0588-3>
- Ericson, Margulieux, Rick (2017), "Solving Parsons problems versus fixing
  and writing code", Koli Calling '17; Ericson's dissertation:
  <https://hg.gatech.edu/node/603172>
- Edwards (2004), "Using software testing to move students from
  trial-and-error to reflection-in-action", SIGCSE '04:
  <https://www.acm.org/media-center/2019/march/sigcse-top-10-papers>
- Kapur (2008), "Productive failure", *Cognition and Instruction* 26(3),
  379–424: <https://www.bu.edu/ctl/?p=5396>
- McDowell, Werner, Bullock, Fernald (2006), "Pair programming improves
  student retention, confidence, and program quality", *Communications of
  the ACM* 49(8), 90–95:
  <https://course.ccs.neu.edu/is4800sp12/resources/mcdowell.pdf>

Several of these were confirmed from abstracts and bibliographic records,
not the full papers; the claims above stay at the level of those abstracts.
