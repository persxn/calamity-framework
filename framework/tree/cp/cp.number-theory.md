---
id: cp.number-theory
title: Number theory
track: cp
group: core
prereqs: [cp.math-basics, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [number theory, sieve, primes, modular inverse]
cf_tags: [number theory]
band: 1200
est_hours: 25
order: 10
summary: "Primes, factorisation and arithmetic under a modulus, fast enough for 2e5 queries."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.number-theory`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `number theory`, rated 1300 to 1600, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## sieve | Sieve of Eratosthenes
level: 2
- all primes up to 1e7 in O(n log log n); a smallest-prime-factor table

## factorisation | Prime factorisation
needs: [sieve]
level: 2
- by trial division in O(sqrt n); in O(log n) per number with the smallest-prime-factor table
- number and sum of divisors from the exponents

## modpow | Fast modular exponentiation
level: 2
- binary exponentiation in O(log e), written from memory

## mod-inverse | Modular inverse
needs: [modpow]
level: 2
- with a prime modulus p the inverse of a is a^(p-2); it exists only when gcd(a, m) = 1

## gcd-in-problems | gcd in problems
needs: [factorisation]
level: 3
- gcd(a, b) = gcd(a, b - a): the gcd of an array shifted by x depends on differences
- the gcd of a prefix changes at most log times

## multiples-loops | Looping over divisors and multiples
needs: [sieve]
level: 3
- precompute answers for every d by visiting its multiples: O(n log n) in total

## extended-euclid | Extended Euclid and linear Diophantine equations
needs: [mod-inverse]
level: 4
band: 1700
- find x, y with ax + by = gcd(a, b); describe all solutions

## crt | Chinese remainder theorem
needs: [extended-euclid]
level: 4
band: 1900
- combine congruences with coprime moduli; the non-coprime case in outline
