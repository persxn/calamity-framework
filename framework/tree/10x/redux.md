---
id: redux
title: Redux (Redux Toolkit)
track: 10x
group: frontend
prereqs: [react]
slot: state-management
tags: [frontend, js-ecosystem]
aliases: [rtk, redux toolkit, global state]
est_hours: 15
order: 50
summary: "Predictable global state: store, slices, thunks, selectors, and when not to reach for it."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- when global state is warranted and when local state is enough
- principles: one store, actions, pure reducers
- Redux Toolkit: configureStore, createSlice, createAsyncThunk
- selectors and memoisation; normalised state
- RTK Query in outline; devtools and time travel

# Boss

Add a feature with real shared state (a cart or a multi-step workflow) to the React app with Redux Toolkit.

Passes when:

- reducers are unit-tested
- no state is mutated outside slices
- the flow can be replayed in Redux DevTools
