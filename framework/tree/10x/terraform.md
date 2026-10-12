---
id: terraform
title: Terraform (infrastructure as code)
track: 10x
group: devops
prereqs: [cloud-basics, git-gh]
aliases: [iac, infrastructure as code, opentofu]
est_hours: 25
order: 80
summary: "Infrastructure in version control: providers and resources, state, modules, plan and apply, drift."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- providers, resources, data sources
- state and remote backends; locking
- variables, outputs, modules
- the plan and apply workflow; environments
- drift and import
- running Terraform in CI

# Boss

Describe the cloud deployment from the cloud-fundamentals boss in Terraform.

Passes when:

- `terraform validate` and `plan` are clean
- `apply` on an empty account recreates the service
- state is remote and locked
- a second `plan` shows no changes
