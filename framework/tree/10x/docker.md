---
id: docker
title: Docker
track: 10x
group: devops
prereqs: [linux-shell]
weaves_into: [runnable]
aliases: [containers, dockerfile, container image]
est_hours: 25
order: 10
summary: "Package and run anything as a container: images and layers, Dockerfiles, volumes, networks, registries."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- images and containers; what a container is at the operating-system level
- Dockerfiles: layers, the build cache, multi-stage builds
- volumes and bind mounts
- networks and port publishing
- registries, tags, digests
- security: non-root users, small base images, scanning
- debugging containers: logs, exec, inspect; resource limits

# Boss

Containerise an existing service with a multi-stage build.

Passes when:

- the final image is under the size the tutor sets
- the process runs as a non-root user
- a health check passes under `docker run`
- changing application code reuses the dependency layer

# Weave

Anything runnable the learner builds later gets a Dockerfile: a Java service, a Node API, a Python tool.
