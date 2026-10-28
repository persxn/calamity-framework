# Competitive programming: onboarding

How a learner is set up for the `cp` track: handle, language, target, and
placement from their Codeforces record. The rest of the coaching is in
`framework/rules/cp-playbook.md`; plans and analysis in
`framework/rules/cp-planning.md`.

Ask, then record:

| Ask | Record |
|---|---|
| Your Codeforces handle? | `cf link <handle>`, then `cf sync` (public API, no password) |
| Which language do you compete in? | `profile set cp.language cpp`. The track teaches C++; a learner using another language drops `cp.cpp` (`tree drop cp.cpp`) and keeps `cp.stl`, taught with that language's equivalents (the note in `framework/tree/cp/cp.stl.md`) |
| What rating are you aiming for, by when? | `profile set cp.target_rating 1800`, `profile set cp.target_date 2027-08-31`, and add `cp.rating-1800` to `goals` |
| How much time a day, and how do you practise now? | goes into `learner/cp/plan.md` |

Then read the record before planning anything:

    calamity cf status
    calamity cf analyse
    calamity cf rating
    calamity cf upsolve

Place the learner in the tree from that record. A skill may be recorded as
known without a separate test when Codeforces has already tested it: its
band is at least 200 below the learner's rating and its tags show fifteen or
more solves at that band or above.

    calamity placement cp.implementation --result known --note "CF 1540, 96 implementation solves, level 1500"

Everything else is tested or learnt. A newcomer with no handle starts at
`cp.cpp` and makes an account when they are ready for a first contest.
Enrol the skills of the next milestone that are not yet known, add `cp` to
`tracks`, and hand the record to the `cp-coach` agent for the first plan.
