---
id: gate.da.linear-algebra
title: Linear Algebra
track: gate-da
group: subjects
tags: [gate]
aliases: [linear algebra, da linear algebra]
overlaps: [gate.cs.linear-algebra]
paper: DA
marks: 12
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf"
est_hours: 45
syllabus_year: 2027
order: 20
summary: "Vector spaces, special matrices, linear systems, eigenvalues, projections and decompositions."
---

Topics follow section 2 of the official GATE 2027 syllabus for Data Science and Artificial Intelligence (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.da.linear-algebra.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## vector-spaces | Vector space, subspaces
level: 2
- test whether a set is a subspace; basis and dimension

## linear-dependence | Linear dependence and independence of vectors
level: 2
- decide dependence; relate it to rank

## matrices | Matrices
level: 2
same_as: [gate.cs.linear-algebra/matrices]
- operations, transpose, inverse, rank, trace

## special-matrices | Projection, orthogonal, idempotent and partition matrices
level: 3
- definitions and properties of each; their eigenvalues

## quadratic-forms | Quadratic forms
level: 3
- matrix of a quadratic form; positive definite and semi-definite forms

## linear-systems | Systems of linear equations and solutions; Gaussian elimination
level: 2
same_as: [gate.cs.linear-algebra/linear-systems]
- solve by elimination; count solutions from ranks

## eigenvalues | Eigenvalues and eigenvectors
level: 3
same_as: [gate.cs.linear-algebra/eigenvalues]
- characteristic equation; trace and determinant relations

## determinant | Determinant
level: 2
same_as: [gate.cs.linear-algebra/determinants]
- properties and effect of row operations

## rank-nullity | Rank and nullity
level: 2
- the rank-nullity theorem; null space and column space

## projections | Projections
level: 3
- project a vector onto a line or a subspace; least squares

## lu-decomposition | LU decomposition
level: 3
same_as: [gate.cs.linear-algebra/lu-decomposition]
- factor a matrix as LU and solve with it

## svd | Singular value decomposition
level: 4
- singular values and vectors; link to eigenvalues of A-transpose-A; low-rank approximation
