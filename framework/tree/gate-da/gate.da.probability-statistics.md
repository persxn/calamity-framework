---
id: gate.da.probability-statistics
title: Probability and Statistics
track: gate-da
group: subjects
tags: [gate]
aliases: [probability, statistics, da probability]
overlaps: [gate.cs.probability]
paper: DA
marks: 12
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf"
est_hours: 70
syllabus_year: 2027
order: 10
summary: "Probability from counting to the central limit theorem, then intervals and hypothesis tests."
---

Topics follow section 1 of the official GATE 2027 syllabus for Data Science and Artificial Intelligence (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.da.probability-statistics.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## counting | Counting (permutations and combinations)
level: 1
- count outcomes for a probability

## probability-axioms | Probability axioms, sample space, events
level: 1
- set up the sample space; apply the axioms and the addition rule

## independence | Independent events, mutually exclusive events
level: 2
- tell the two apart; test independence from probabilities

## joint-marginal-conditional | Marginal, conditional and joint probability
level: 2
- move between a joint table and its marginals and conditionals

## bayes-theorem | Bayes theorem
level: 2
same_as: [gate.cs.probability/conditional-probability-bayes]
- total probability and Bayes theorem on a two-stage experiment

## conditional-expectation | Conditional expectation and variance
level: 3
- E[X | Y]; the laws of total expectation and total variance

## descriptive-statistics | Mean, median, mode and standard deviation
level: 1
same_as: [gate.cs.probability/descriptive-statistics]
- compute and compare them for a data set

## correlation-covariance | Correlation and covariance
level: 2
- compute both; what zero covariance does and does not imply

## random-variables | Random variables: discrete (PMF) and continuous (PDF)
level: 2
same_as: [gate.cs.probability/random-variables]
- expectation and variance from a mass or density function

## discrete-distributions | Uniform, Bernoulli, binomial and Poisson distributions
level: 2
same_as: [gate.cs.probability/discrete-distributions]
- parameters, mean and variance; when each model applies
- the official list names Poisson next to the continuous distributions; it is discrete

## continuous-distributions | Uniform, exponential, normal and standard normal distributions
level: 2
same_as: [gate.cs.probability/continuous-distributions]
- density, mean and variance; standardise and read a normal probability

## sampling-distributions | t-distribution and chi-squared distribution
level: 3
- where each arises; degrees of freedom

## cdf | Cumulative distribution function
level: 2
- from density to CDF and back; probabilities of intervals

## conditional-pdf | Conditional PDF
level: 3
- conditional density from a joint density

## central-limit-theorem | Central limit theorem
level: 3
- approximate the distribution of a sample mean or sum

## confidence-intervals | Confidence interval
level: 3
- build and read an interval for a mean

## z-test | z-test
level: 3
- set up hypotheses, compute the statistic, decide at a significance level

## t-test | t-test
level: 3
- when to use t instead of z; one-sample and two-sample forms

## chi-squared-test | Chi-squared test
level: 3
- goodness of fit and independence in a table
