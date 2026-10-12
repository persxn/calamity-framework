---
id: classical-ml
title: Classical machine learning
track: ai
group: ml
prereqs: [ai-linear-algebra, ai-calculus, ai-probability, python-data]
tags: [ai, ml]
weaves_into: [ml, ai]
aliases: [machine learning, ml, scikit-learn, sklearn, regression, classification]
est_hours: 70
order: 20
summary: "Supervised and unsupervised learning with the maths behind each model, and honest evaluation."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the learning setup: features, labels, loss, train/validation/test splits, data leakage
- linear regression and regularisation (ridge, lasso); gradient descent and the closed form
- logistic regression; the decision boundary; multi-class
- k-nearest neighbours, naive Bayes, support vector machines and kernels
- decision trees, random forests, gradient boosting
- the bias-variance trade-off, overfitting, cross-validation, hyperparameter search
- metrics: accuracy, precision, recall, F1, ROC and PR curves, calibration; regression metrics
- unsupervised learning: k-means, hierarchical clustering, PCA
- feature engineering, scaling, encoding, pipelines in scikit-learn
- imbalanced data, baselines, error analysis

# Boss

Run an end-to-end tabular project: a baseline, three model families compared under cross-validation, a chosen model with a justification, and an error analysis. One model (logistic regression) is also written from scratch in NumPy.

Passes when:

- the from-scratch model matches scikit-learn's coefficients within the tolerance the tutor sets
- no information from the test set reaches training (the pipeline is fitted inside each fold)
- the report gives a metric with a confidence interval and compares against a trivial baseline
- the error analysis names two concrete failure groups

# Weave

Deep learning and LLM evaluation exercises should reuse split discipline, baselines and metrics from here.
