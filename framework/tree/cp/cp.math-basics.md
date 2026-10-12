---
id: cp.math-basics
title: Math basics
track: cp
group: foundations
prereqs: [cp.cpp]
tags: [cp]
weaves_into: [cp]
aliases: [gcd, modular arithmetic, math]
cf_tags: [math]
band: 800
est_hours: 15
order: 30
summary: "The arithmetic most problems lean on: gcd, parity, modular arithmetic, sums, careful integer division."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.math-basics`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `math`, rated 900 to 1200, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## divisibility-gcd | Divisibility, gcd and lcm
level: 1
- Euclid's algorithm and why it is O(log n); `lcm = a / gcd * b` to avoid overflow

## parity | Parity and simple invariants
level: 1
- argue with odd/even: what an operation can and cannot change

## modular-basics | Modular arithmetic basics
needs: [divisibility-gcd]
level: 2
- add, subtract and multiply under a modulus with `long long`; fix negatives with `(x % m + m) % m`
- division needs a modular inverse; never divide and then take the remainder

## sums-formulas | Sums and closed forms
level: 1
- arithmetic and geometric series; 1 + 2 + ... + n; the number of pairs n(n-1)/2
- watch the overflow in the formula itself

## floor-ceil | Floor, ceiling and integer square roots
needs: [sums-formulas]
level: 2
- `(a + b - 1) / b` for positive ceiling division; stay in integers
- `sqrt` returns a double: correct the result with a loop

## primes-trial-division | Primes and divisors by trial division
needs: [divisibility-gcd]
level: 2
- test primality and list divisors in O(sqrt n); divisors come in pairs
