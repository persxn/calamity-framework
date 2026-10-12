---
id: github-actions
title: GitHub Actions
track: 10x
group: devops
prereqs: [git-gh, docker, testing-basics]
slot: ci
weaves_into: [runnable]
aliases: [ci, cd, ci/cd, workflows, pipelines]
est_hours: 15
order: 30
summary: "CI/CD on GitHub: workflows, jobs, matrices, caching, secrets and environments, image builds, deployments."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- workflows, events, jobs, steps, runners
- matrix builds; caching dependencies
- secrets, variables and environments
- artefacts; reusable workflows and composite actions
- building and pushing images; deployments with approvals
- security: pinned actions, least-privilege token permissions

# Boss

Give a project a pipeline: lint, test on a matrix, build and push an image, deploy to a staging environment.

Passes when:

- a pull request cannot merge while a check fails
- the image is tagged with the commit SHA
- third-party actions are pinned
- the default token has read-only permissions unless a job needs more

# Weave

Project exercises after this one are expected to have a green pipeline.
