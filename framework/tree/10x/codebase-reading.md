---
id: codebase-reading
title: Codebase reading
track: 10x
group: engineering
prereqs: [git-gh, linux-shell]
tags: [engineering, reading]
weaves_into: [10x]
aliases: [reading code, code reading, unfamiliar codebase, legacy code]
est_hours: 30
order: 30
summary: "Find your way around a codebase you did not write: navigation, history, tracing, recovering the architecture."
---

# Scope

What the mastery standard covers: the habits that let an engineer be useful
in a large unfamiliar repository within a day. Practised on real
open-source repositories at pinned commits (`read` drills), never on
summaries of them.

- orienting: entry points, build files, the directory map, the test suite as documentation
- navigation: definitions and references, grep and ripgrep, ctags and an LSP
- history: `git log -S`, `git log -L`, `git blame`, `git bisect`
- tracing a request or a command end to end, with a debugger and with logs
- recovering the architecture: modules, boundaries, data flow, the decisions behind them
- changing safely: characterisation tests, the smallest change, reading the review history

# Boss

Ship a small feature in an unfamiliar open-source repository of about 50,000 lines in four hours: the
change, its tests, and a one-page map of the code it touched (each claim `path:symbol`), defended in a
review.

# Topics

## orient | Orienting in a repository
level: 1
- [P] find a repository's entry points, build and test commands from its files alone
- [T] explain what the tests, the CI file and the directory layout each say about the design
- [I] write a one-page map of a repository at a pinned commit, every claim as `path:symbol`

## navigate | Navigation tools
level: 1
needs: [orient]
- [P] jump to a definition and list its references with grep or ripgrep, ctags and an LSP
- [T] explain where text search misleads (dynamic dispatch, generated code, reflection) and what to use instead
- [I] answer three "where is X done" questions on a real repository in under twenty minutes

## history | Reading the history
level: 2
needs: [navigate]
- [P] find when and why a line changed with `git log -S`, `git log -L` and `git blame`
- [P] find the commit that broke a behaviour with `git bisect`, scripted with a test
- [T] explain how commit messages, pull requests and issues record the reasons code alone hides
- [I] reconstruct the story of one feature from its first commit to now

## trace | Tracing execution
level: 2
needs: [navigate]
- [P] trace a request or a command from its entry point to the code that answers it
- [P] use a debugger's breakpoints and watch expressions, and logs, to confirm a trace
- [T] explain why a trace beats a guess when the code has middleware, hooks or plugins
- [I] draw the call path of one real request as `path:symbol` steps

## architecture | Recovering the architecture
level: 3
needs: [trace, history]
- [T] explain the modules, their boundaries and the data flow of a real system from its code
- [T] explain the design decisions behind a structure, and the constraint each answered
- [P] tell which parts are stable and which change often, from the history
- [I] write an architecture note a newcomer could use, every claim with its evidence

## change | Changing unfamiliar code safely
level: 3
needs: [architecture]
- [P] pin current behaviour with characterisation tests before changing it
- [P] make the smallest change that does the job, and keep the diff reviewable
- [T] explain how to read a project's review norms from its merged pull requests
- [I] land a small change in a real repository that passes its own CI
