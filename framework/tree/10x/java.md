---
id: java
title: Java
track: 10x
group: backend
prereqs: [dev-environment]
slot: language
tags: [language, runnable]
weaves_into: [spring-boot]
aliases: [jvm, jdk, maven, gradle]
est_hours: 60
order: 80
summary: "Modern Java from zero: objects, collections and generics, streams, records, concurrency basics, JUnit."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- syntax and types; classes, interfaces, inheritance, polymorphism
- collections and generics; exceptions
- lambdas and streams; records and sealed types
- concurrency basics: threads, executors, CompletableFuture
- build tools (Maven or Gradle) and packaging
- testing with JUnit
- the JVM in outline: memory areas and garbage collection

# Boss

Model a small domain (a library or a bank ledger) in Java with a full test suite.

Passes when:

- `mvn verify` (or the Gradle equivalent) passes
- JaCoCo line coverage is 80% or more
- the build treats compiler warnings as errors
