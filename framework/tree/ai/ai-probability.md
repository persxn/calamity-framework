---
id: ai-probability
title: "Probability & statistics for ML"
track: ai
group: math
tags: [ai, math]
weaves_into: [ml, ai]
aliases: [probability, statistics, bayes, distributions, hypothesis testing]
est_hours: 40
order: 30
summary: "Random variables, distributions, estimation and testing: the language model evaluation is written in."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- counting, sample spaces, events, conditional probability, independence, Bayes' theorem
- random variables, expectation, variance, covariance, correlation
- common distributions: Bernoulli, binomial, Poisson, uniform, normal, exponential
- joint, marginal and conditional distributions
- the law of large numbers and the central limit theorem
- estimation: maximum likelihood, maximum a posteriori, bias and variance of an estimator
- confidence intervals, hypothesis tests, p-values and their common misreadings
- information theory basics: entropy, cross-entropy, KL divergence
- sampling and the bootstrap

# Boss

Analyse an A/B test from raw data: state the hypothesis, choose and justify a test, compute it by hand and by simulation, and report an interval rather than a verdict.

Passes when:

- the hand-computed statistic matches SciPy's to 3 decimal places
- a bootstrap interval agrees with the analytic one within the tolerance the tutor sets
- the write-up states what the p-value does and does not mean, in one sentence each

# Weave

Evaluation exercises should ask for an interval or a test, never a bare accuracy number.
