---
name: update-framework
description: "Bring a newer Calamity Framework (engine, rules, skills, trees) into the learner's repository without touching their data."
when_to_use: "When the learner asks to update the framework; run by the learner only."
argument-hint: "[address of the framework repository]"
disable-model-invocation: true
---

# Update the framework

The framework lives in `engine/`, `framework/`, `.claude/`, `docs/`,
`tools/`, `CLAUDE.md` and `README.md`, plus `learner/README.md`. The
learner's record (everything else under `learner/`) is never changed by an
update: their syllabi, tree changes and settings override the shipped files
instead of editing them.

1. **A clean start.** `git status --short` must show nothing uncommitted.
   If it does, say so and ask whether to save their progress to their own
   repository first with the sync skill; do not run it unasked.

2. **Where updates come from.** `git remote -v`. The framework should be
   the remote named `upstream`. If it is missing, add the framework's own
   repository, unless the learner names another (or passes one as the
   argument):

       git remote add upstream https://github.com/persxn/calamity-framework.git

3. **Look before merging.**

       git fetch upstream --tags
       git show upstream/main:framework/VERSION

   (Read the local `framework/VERSION` with the Read tool.)
       git merge-base HEAD upstream/main

   If `git merge-base` prints nothing, this copy began as a downloaded
   archive rather than a clone, and git sees no shared history. Connect it
   once to the release it came from, keeping every file as it is now
   (`<version>` is the number in `framework/VERSION`):

       git merge -s ours --allow-unrelated-histories -m "Adopt the framework history at <version>" v<version>

   If there is no tag `v<version>`, stop and tell the learner: the update
   then has to be done by hand. Then:

       git diff --stat HEAD...upstream/main

   (Use the framework's default branch if it is not `main`.) If anything
   under `learner/` other than `learner/README.md` would change, stop and
   tell the learner: an update must never touch their record. Tell the
   learner what changes: versions, which areas, and anything in
   `.claude/settings.json` (permissions) or the engine that they should
   know about before accepting. Read the diff of `.claude/settings.json`
   and of any hook or script in full and describe it plainly.

4. **Merge** when they agree:

       git merge upstream/main

   Conflicts can only arise in framework files that were edited locally.
   Prefer the upstream version and move the local change to where it
   belongs (`learner/tree/`, `learner/syllabus/`, `cfg.*` in the profile).

5. **Verify.**

       python3 engine/calamity.py selftest
       python3 engine/calamity.py doctor
       python3 engine/calamity.py tree check
       python3 engine/calamity.py rebuild

   All four must pass. `tree check` may warn that a learner override now
   shadows a changed shipped skill: show those to the learner. If anything
   fails, undo with `git merge --abort` (during the merge) or
   `git reset --hard ORIG_HEAD` (after it), and report what failed.

6. **Say what is new** in a few lines, and that the session-start hook
   needs no change. Push with the sync skill if they want.

Do not run an update in the middle of a study session, and never from a
source the learner did not name.
