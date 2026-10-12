---
id: gate.da.machine-learning
title: Machine Learning
track: gate-da
group: subjects
tags: [gate]
aliases: [ml, machine learning]
paper: DA
marks: 13
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf"
est_hours: 80
syllabus_year: 2027
order: 60
summary: "Supervised learning from regression to neural networks, then clustering and dimensionality reduction."
---

Topics follow section 6 of the official GATE 2027 syllabus for Data Science and Artificial Intelligence (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.da.machine-learning.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## regression-classification | Supervised learning: regression and classification problems
level: 1
- tell the two apart; loss functions and evaluation for each

## linear-regression | Simple and multiple linear regression
level: 2
- least squares; the normal equations; reading coefficients and residuals

## ridge-regression | Ridge regression
level: 3
- the L2 penalty and its effect on coefficients and variance

## logistic-regression | Logistic regression
level: 2
- the sigmoid, log-odds and the decision boundary

## knn | k-nearest neighbour
level: 2
- classify by majority among neighbours; effect of k and of the distance

## naive-bayes | Naive Bayes classifier
level: 2
- the conditional-independence assumption; compute a posterior

## lda | Linear discriminant analysis
level: 3
- class means and a shared covariance; the linear decision rule

## svm | Support vector machine
level: 3
- margin, support vectors, hard and soft margin, kernels

## decision-trees | Decision trees
level: 2
- entropy, information gain and Gini; build and prune a tree

## bias-variance | Bias-variance trade-off
level: 2
- underfitting and overfitting; how model complexity moves each

## cross-validation | Cross-validation: leave-one-out and k-fold
level: 2
- how each splits the data; what it estimates and what it costs

## neural-networks | Multi-layer perceptron, feed-forward neural network
level: 3
- forward pass; activations; count parameters; gradient descent and backpropagation in outline

## kmeans-kmedoid | Clustering: k-means and k-medoid
level: 2
- the two alternating steps; run an iteration by hand; how the two differ

## hierarchical-clustering | Hierarchical clustering: top-down, bottom-up, single-linkage, multiple-linkage
level: 3
- build a dendrogram by hand from a distance matrix

## dimensionality-reduction | Dimensionality reduction
level: 2
- why reduce dimensions; projection versus selection

## pca | Principal component analysis
level: 3
- directions of largest variance; eigenvectors of the covariance matrix; explained variance
