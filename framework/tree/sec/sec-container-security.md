---
id: sec-container-security
title: "Container security"
track: sec
group: cloud-container
prereqs: [sec-os-internals, docker]
tags: [sec]
weaves_into: [sec]
aliases: [container security, docker security, namespaces, capabilities, image provenance]
est_hours: 25
order: 20
summary: "What a container actually is as a Linux construct, and where its isolation holds or leaks: namespaces, capabilities, images, networking and the supply chain behind the image."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- container images and layers, and what each layer carries
- registries and image provenance
- Linux namespaces and cgroups as the isolation primitives
- capabilities and the privilege boundary a container runs with
- rootless containers and what they change
- runtime isolation and its limits
- container networking
- secrets and mounted volumes as exposure points
- image scanning and software composition analysis
- supply-chain integrity for images

# Boss

Build two containers for the same workload, one deliberately over-privileged and one least-privilege, and demonstrate the difference: show the namespaces, capabilities and mounts each has, and what the over-privileged one can reach that the other cannot.

Passes when:

- the namespaces, capabilities and mounts of each container are read correctly and compared
- the extra reach of the over-privileged container is demonstrated inside the lab
- the least-privilege version is shown to run the workload with the excess removed
- the learner explains which Linux primitive provides each piece of the isolation

# Weave

Container internals and the image supply chain carry straight into Kubernetes security and cloud attack paths.
