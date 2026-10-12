---
id: ai-calculus
title: "Calculus & optimisation for ML"
track: ai
group: math
tags: [ai, math]
weaves_into: [ml, ai]
aliases: [calculus, gradients, optimisation, optimization, gradient descent, backpropagation math]
est_hours: 35
order: 20
summary: "Derivatives, gradients, the chain rule and the optimisers built on them."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- limits and derivatives in one variable; rules of differentiation
- partial derivatives, gradients, directional derivatives, the Jacobian and the Hessian
- the chain rule on computation graphs: forward mode and reverse mode
- Taylor expansion and local approximation
- convexity, stationary points, saddle points
- gradient descent, stochastic gradient descent, momentum, Adam; learning-rate schedules
- constrained optimisation in outline: Lagrange multipliers
- numerical gradient checking

# Boss

Write a tiny reverse-mode automatic differentiation engine for scalars and use it to train a small network on a two-class toy dataset.

Passes when:

- the engine's gradients match numerical gradients to 1e-6 on ten random expressions
- training loss falls and accuracy on the toy set passes 95%
- the learner derives the gradient of the loss for one layer by hand and it matches the engine

# Weave

Training exercises should make the learner derive one gradient by hand before trusting autograd.
