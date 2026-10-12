---
id: spring-boot
title: Spring Boot
track: 10x
group: backend
prereqs: [java, rest-api-design, sql-modelling]
slot: backend-framework
tags: [backend, backend-framework, runnable]
aliases: [spring, springboot, spring data, jpa]
est_hours: 50
order: 90
summary: "Production Java services: dependency injection, REST controllers, Spring Data JPA, security, testing."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- inversion of control: beans, configuration, profiles
- REST controllers, validation, exception handling
- Spring Data JPA: entities, repositories, transactions; migrations with Flyway
- Spring Security in outline: the filter chain, a JWT resource server
- testing: slices, MockMvc, Testcontainers
- Actuator, logging, packaging as a jar and as a container image

# Boss

Build a REST service with JPA persistence and secured write routes.

Passes when:

- `mvn verify` passes with a Testcontainers database
- the OpenAPI document is generated
- the Actuator health endpoint returns 200 inside a container
- schema changes run through migrations only
