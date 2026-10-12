---
id: cp.strings-advanced
title: String algorithms
track: cp
group: advanced
prereqs: [cp.strings-basics, cp.number-theory]
tags: [cp]
weaves_into: [cp]
aliases: [hashing, kmp, z function, trie, suffix array]
cf_tags: [hashing, strings, string suffix structures]
band: 1700
est_hours: 30
order: 30
summary: "Hashing, the prefix and Z functions, tries, and the heavier suffix structures."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.strings-advanced`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `hashing` or `strings`, rated 1700 to 2000, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## polynomial-hashing | Polynomial hashing
level: 3
- prefix hashes and O(1) substring comparison; why a fixed base and modulus get hacked
- use a random base, or two moduli, or the modulus 2^61 - 1

## prefix-function | Prefix function and KMP
level: 3
- compute the prefix function in O(n); find all occurrences; the smallest period of a string

## z-function | Z-function
level: 3
- compute it in O(n); pattern matching with pattern + separator + text

## trie | Tries
level: 3
- insert and search words; a binary trie for the maximum xor with a query value

## manacher | Manacher's algorithm
needs: [z-function]
level: 4
band: 1900
- all palindromic substrings in O(n)

## suffix-array | Suffix array and LCP array
needs: [polynomial-hashing]
level: 5
band: 2100
- build in O(n log n) or O(n log^2 n); the number of distinct substrings; longest common substring

## aho-corasick | Aho-Corasick
needs: [trie, prefix-function]
level: 5
band: 2200
- match many patterns at once with a trie and failure links
