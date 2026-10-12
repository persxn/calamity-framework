---
id: cp.cpp
title: C++ for contests
track: cp
group: language
tags: [cp]
weaves_into: [cp]
aliases: [c++, cpp, g++]
band: 800
est_hours: 30
order: 10
summary: "The part of C++ a contest needs, from zero: types and overflow, fast I/O, functions, references, lambdas, sanitizers."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.cpp`.

# Boss

Solve 8 problems rated 800 to 1000 in one 100-minute sitting in C++, each compiled with warnings and sanitizers on before submitting.

Passes when:

- after `cf sync`, at least 7 of the 8 are accepted inside the sitting
- no accepted solution needed more than two wrong submissions
- one planted bug per category (overflow, out-of-bounds, uninitialised) is found using the sanitizers

# Weave

Every later exercise is written in C++: overflow, I/O speed and undefined behaviour stay in play.

# Topics

## program-structure | A contest program end to end
level: 1
- write, compile and run a complete solution: includes, `main`, read input, print output
- compile with warnings on: `g++ -std=c++17 -O2 -Wall -Wextra` (or a newer standard)
- handle `t` test cases with a `solve()` function

## types-overflow | Integer types and overflow
needs: [program-structure]
level: 1
- `int` holds about 2e9, `long long` about 9e18; pick the type from the constraints
- spot the product or sum that overflows and fix it with `1LL *` or a `long long` variable
- integer division truncates toward zero; `%` of a negative number is negative
- `double` carries about 15-16 significant digits; prefer integers whenever the answer is an integer

## io | Input and output
needs: [program-structure]
level: 1
- fast input: `ios::sync_with_stdio(false); cin.tie(nullptr);` and `'\n'` instead of `endl`
- read a line with `getline` after `>>` without losing it; read until end of input
- print doubles with `fixed << setprecision(k)`

## control-flow-functions | Control flow and functions
needs: [program-structure]
level: 1
- loops, conditions, early `return`/`continue`; a helper function instead of repeated code
- pass by value copies; pass big containers by reference (`const vector<int>&`)
- recursion: base case, depth, and when depth becomes a risk

## arrays-strings | Arrays, vectors and strings: the basics
needs: [types-overflow]
level: 1
- `vector<int> a(n)` versus a global array; global arrays start zeroed, local ones do not
- 0-indexed versus 1-indexed loops without off-by-one errors
- `string` as a vector of chars: indexing, `size()`, `+=`, comparing
- reading or writing outside the bounds is undefined behaviour, not an error message

## references-structs | References, structs, pairs and tuples
needs: [control-flow-functions, arrays-strings]
level: 2
- a `struct` with fields and a comparison operator; `pair` and `tuple` compare lexicographically
- structured bindings: `auto [x, y] = p;`
- references as aliases: modifying an element through `auto&` in a range-for

## lambdas-auto | `auto`, range-for and lambdas
needs: [references-structs]
level: 2
- a lambda with a capture list (`[&]`, `[=]`) as a local helper or comparator
- a recursive lambda (`function<void(int)>` or passing `self`)
- `auto` for iterators and long types; when it hides a copy

## small-tools | Small built-in tools
needs: [types-overflow]
level: 2
- `gcd`, `min`/`max` (also over `{a, b, c}`), `swap`, `abs` on the right type
- `__builtin_popcountll`, `__builtin_clzll`, `__builtin_ctzll` and their undefined case (zero)

## undefined-behaviour | Undefined behaviour and the tools that catch it
needs: [arrays-strings]
level: 3
- name the usual suspects: uninitialised variable, signed overflow, out-of-bounds, shift by 64, missing return
- catch them locally with `-fsanitize=address,undefined` and `-D_GLIBCXX_DEBUG`
- "works on my machine, wrong on the judge" means: suspect undefined behaviour first

## template | A personal template
needs: [io, lambdas-auto]
level: 2
- a minimal template the learner fully understands: includes, fast I/O, `solve()`, test-case loop
- nothing in it that the learner could not write from memory
