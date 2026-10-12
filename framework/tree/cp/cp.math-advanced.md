---
id: cp.math-advanced
title: "Math: advanced"
track: cp
group: advanced
prereqs: [cp.number-theory, cp.combinatorics]
tags: [cp]
weaves_into: [cp]
aliases: [matrix exponentiation, fft, ntt, gaussian elimination, mobius]
cf_tags: [matrices, fft]
band: 2000
est_hours: 30
order: 80
summary: "Linear recurrences by matrices, elimination, xor bases, multiplicative functions and fast polynomial products."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.math-advanced`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `matrices` or `fft`, rated 1900 to 2200, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## matrix-exponentiation | Matrix exponentiation
level: 4
band: 1800
- the n-th term of a linear recurrence in O(k^3 log n); counting walks of length n

## euler-phi | Euler's totient
level: 4
band: 1900
- compute phi; a^phi(m) = 1 mod m for coprime a; reducing huge exponents

## xor-basis | Linear basis over GF(2)
level: 4
band: 1900
- maximum xor of a subset; how many values are representable; inserting in O(log max)

## gaussian-elimination | Gaussian elimination
needs: [xor-basis]
level: 5
- solve a linear system over the reals or modulo a prime; rank; number of solutions

## mobius | Möbius function and sums over divisors
level: 5
band: 2100
- count pairs with gcd exactly 1 by inclusion-exclusion over divisors

## large-binomials | Binomials beyond the factorial table
level: 5
band: 2100
- Lucas' theorem for a small prime modulus

## fft-ntt | FFT and NTT
level: 5
band: 2200
- multiply two polynomials in O(n log n); recognise a convolution in a counting problem
