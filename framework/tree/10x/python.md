---
id: python
title: Python
track: 10x
group: backend
prereqs: [dev-environment]
slot: language
tags: [language, runnable]
weaves_into: [fastapi, ai]
aliases: [py, python3]
est_hours: 45
order: 60
summary: "The language from zero: types and collections, functions, modules, classes, generators, typing, pytest."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- syntax, types, control flow, functions
- lists, dicts, sets, tuples; comprehensions; iterators and generators
- modules and packages; virtual environments; pip or uv
- classes, dataclasses, exceptions, context managers, decorators
- files and JSON; type hints
- testing with pytest; debugging

# Boss

Build a command-line tool with tests, packaged so that it installs cleanly.

Passes when:

- `pytest` passes
- `ruff check` reports nothing
- `pip install .` works in a fresh virtual environment
- a type checker passes in basic mode
