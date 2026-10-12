---
id: cp.strings-basics
title: "Strings: the basics"
track: cp
group: foundations
prereqs: [cp.stl]
tags: [cp]
weaves_into: [cp]
aliases: [strings, palindrome]
cf_tags: [strings]
band: 900
est_hours: 12
order: 50
summary: "Counting characters, palindromes, subsequences and bracket sequences."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.strings-basics`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `strings`, rated 1000 to 1300, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## char-counting | Character counts
level: 1
- a 26-entry frequency array with `c - 'a'`; anagram and rearrangement checks

## palindromes | Palindromes
level: 1
- check with two pointers; when the letters of a string can be rearranged into a palindrome

## substrings-subsequences | Substrings and subsequences
needs: [char-counting]
level: 2
- the difference; test for a subsequence with two pointers; a string has n(n+1)/2 substrings

## lexicographic-order | Lexicographic order
needs: [substrings-subsequences]
level: 2
- compare strings; build the smallest or largest string greedily, position by position

## bracket-sequences | Bracket sequences
needs: [char-counting]
level: 2
- balanced means the running balance never drops below zero and ends at zero; matching with a stack
