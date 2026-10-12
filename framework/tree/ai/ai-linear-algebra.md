---
id: ai-linear-algebra
title: Linear algebra for ML
track: ai
group: math
tags: [ai, math]
weaves_into: [ml, ai]
aliases: [linear algebra, matrices, vectors, eigenvalues, svd]
est_hours: 40
order: 10
summary: "Vectors, matrices and decompositions, to the depth machine learning needs, with every idea checked in code."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- vectors: norms, dot product, cosine similarity, projection, orthogonality
- matrices as linear maps: multiplication, transpose, inverse, rank, null space, column space
- systems of linear equations: Gaussian elimination, least squares, the normal equations
- determinants and what they measure
- eigenvalues and eigenvectors; diagonalisation; symmetric and positive-definite matrices
- singular value decomposition; low-rank approximation; the link to PCA
- matrix calculus conventions: gradients of linear and quadratic forms
- numerical habits: conditioning, why you rarely invert a matrix, broadcasting shapes

# Boss

Implement PCA twice, once through the eigen-decomposition of the covariance matrix and once through the SVD, on a real dataset, and explain every step on paper.

Passes when:

- both implementations agree with scikit-learn's PCA up to sign, to 6 decimal places
- the explained-variance ratios sum to 1
- a written derivation shows why the top singular vectors maximise projected variance
- the learner predicts the output shape of five matrix expressions before running them

# Weave

Model exercises should ask for the shape of every tensor and for the linear algebra behind one step.
