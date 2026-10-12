---
id: python-data
title: "Python data stack (NumPy, pandas, plotting)"
track: ai
group: ml
prereqs: [python]
tags: [ai]
weaves_into: [ml, ai]
aliases: [numpy, pandas, matplotlib, jupyter, data analysis]
est_hours: 30
order: 10
summary: "The working tools of ML in Python: arrays, data frames, plots and reproducible notebooks."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- NumPy: arrays, dtypes, indexing, broadcasting, vectorised operations, random number generators
- pandas: Series and DataFrame, loading data, selection, missing values, groupby, joins, reshaping
- plotting with Matplotlib: figures and axes, the plots that answer a question
- notebooks used well: restart-and-run-all, seeds, moving code into modules
- environments and dependencies (venv or uv), pinned requirements
- exploratory data analysis as a routine
- performance habits: avoid Python loops over rows, profile before optimising

# Boss

Take a messy public dataset from raw file to a short analysis report: clean it, answer three questions the tutor sets, and produce the figures.

Passes when:

- the notebook runs top to bottom from a fresh kernel
- no row-wise Python loop remains in the cleaning code
- every figure has labelled axes and a one-line takeaway
- the environment is reproducible from the committed requirements

# Weave

Later ML work should begin with loading and inspecting the data in pandas, not with a model.
