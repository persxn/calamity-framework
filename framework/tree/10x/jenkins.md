---
id: jenkins
title: Jenkins
track: 10x
group: devops
prereqs: [git-gh, docker, testing-basics]
slot: ci
aliases: [jenkinsfile, ci, cd, pipelines]
optional: true
est_hours: 15
order: 40
summary: "The self-hosted alternative for CI/CD: pipelines as code, agents, credentials, shared libraries."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- controller and agents
- declarative pipelines in a Jenkinsfile
- credentials; plugins
- shared libraries
- running builds in containers

# Boss

Give a project a Jenkins pipeline: lint, test, build and push an image.

Passes when:

- the pipeline is defined in the repository
- credentials never appear in logs
- a failing test fails the build
