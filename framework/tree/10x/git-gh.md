---
id: git-gh
title: "Git & GitHub (with the gh CLI)"
track: 10x
group: foundations
prereqs: [linux-shell]
weaves_into: [10x, ai]
aliases: [git, github, gh, version control]
est_hours: 20
order: 30
summary: "Version control done properly: the commit graph, branching, rebasing, undoing, pull requests, the gh CLI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the model: working tree, index, commits, branches, HEAD, remotes
- the daily loop: status, add -p, commit, diff, log, restore, stash
- branching and merging; resolving conflicts; rebase, interactive rebase, cherry-pick
- undoing safely: revert, reset (soft, mixed, hard), reflog
- remotes: fetch, pull, push, tracking branches, tags; .gitignore and .gitattributes
- the GitHub flow: forks, pull requests, reviews, issues, protected branches, required checks
- the gh CLI: auth, repo create and clone, pr create/checkout/review/merge, issue, run watch
- history hygiene: small commits, useful messages, bisect, blame

# Boss

Run a small collaborative history on your own: create a repo with `gh`, protect `main`, open two pull requests that conflict, resolve by rebasing, squash-merge, tag a release, then find a planted bug with `git bisect`.

Passes when:

- `main` has a linear history and a release tag
- the bisect log names the commit that introduced the bug
- both pull requests were merged through `gh`, with a required check passing
- one mistake was undone using the reflog, and the commands are noted

# Weave

Every project exercise should end in commits on a branch and, once learnt, a pull request.
