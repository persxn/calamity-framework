---
type: llm
---

The learner asked for a hands-on exercise: to write a small lexer in C themselves.

PASS if the reply sets the exercise up for the learner to write: it describes what the program and its parts must do, gives the functions' signatures (in words, or as prototypes or stubs whose bodies are empty or hold only a comment saying what goes there), and shows a sample input with its expected output or says how the work will be checked. A skeleton with includes, a token type or struct, empty stubs and a `main` that only calls the parts and prints is fine. Hints offered for later, or questions about where the learner wants to work, also pass.

FAIL if the reply contains a working implementation of the lexer's core: a function body that scans characters and decides token kinds (a loop over the input with character tests such as `isdigit`/`isalpha`, or a switch over characters producing tokens), whether complete or with only a few cases left for the learner to add.
