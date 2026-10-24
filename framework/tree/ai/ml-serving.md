---
id: ml-serving
title: Serving and operating models
track: ai
group: infra
prereqs: [classical-ml, fastapi, docker]
tags: [ai, ml, runnable]
aliases: [mlops, model serving, model deployment, experiment tracking]
optional: true
est_hours: 30
order: 50
summary: "Take a trained model to a service that is versioned, tested and watched."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- packaging a model: serialisation formats, versioning data and models
- an inference API with FastAPI: validation, batching, timeouts
- experiment tracking and a model registry in outline (MLflow or similar)
- containerising inference; CPU versus GPU images
- testing ML code: data checks, model behaviour tests, a golden set
- monitoring: latency, errors, input drift, prediction drift
- rollouts: shadow traffic, canary, rollback

# Boss

Serve the classical-ML project model behind an API in a container, with a golden-set test in CI and a drift report.

Passes when:

- the container answers a prediction request within the latency budget the tutor sets
- the golden-set test fails when a planted regression is introduced
- the drift report flags a shifted input sample and passes an unshifted one
