# The AI era

Two threads run through every topic.

## 1. The comeback of hated topics

Many learners skipped or hated certain foundations, and those foundations turn out to be load-bearing in today's AI systems. Bringing them back with a real AI hook turns a chore into curiosity.

At intake, ask which topics they hated, skipped or never understood. Also watch for avoidance during the course. Then, at fitting points, revisit one with an AI-system angle:

| Hated topic | Where it shows up in AI systems |
|---|---|
| Linear algebra (matrices, dot products) | Embeddings, attention (Q·Kᵀ), why similarity search uses cosine distance |
| Probability and statistics | Sampling temperature, softmax, evaluation metrics, why benchmarks mislead |
| Calculus and gradients | Backpropagation, learning rates, why training diverges |
| Floating point and number formats | fp16/bf16/int8/4-bit quantization, overflow and NaNs in training |
| Memory, caches, pointers | GPU memory limits, the KV cache, why context length is expensive |
| Concurrency and parallelism | Batching, GPU kernels, async inference servers |
| Networking and latency | Streaming tokens, tail latency in LLM APIs, rate limits |
| Databases and indexes | Vector indexes (HNSW, IVF), RAG retrieval, hybrid search |
| Regex, strings, encodings | Tokenization, Unicode bugs, prompt-injection filtering |
| Distributed systems | Multi-GPU training, model sharding, agent orchestration |
| Big-O and algorithms | Why attention is quadratic in sequence length, and what that costs |
| OS and processes | Sandboxing AI agents, containers for code execution |

Pick the rows relevant to the current topic and the learner's dislikes. Teach the comeback at the same depth as anything else. The aim is that the learner sees *why* the topic mattered all along.

## 2. Where AI gets this skill wrong

AI coding tools are now part of every developer's workflow, so mastery includes knowing exactly where they fail in this domain.

For each topic, teach the typical failure modes:

- **Invented surface**: flags, options or API methods that don't exist, or exist only in another version or platform (GNU vs BSD `ls`).
- **Outdated knowledge**: deprecated APIs, old config syntax, old best practices presented as current.
- **Insecure defaults**: running as root, `chmod 777`, secrets in images or code, disabled TLS verification, SQL built from strings.
- **Missing edge cases**: filenames with spaces or newlines, empty inputs, Unicode, concurrency, partial failure.
- **Confidently wrong explanations**: plausible mechanisms that aren't how the system actually works.
- **Works but wrong**: code that passes the happy path while hurting performance, cost or maintainability.

**Drill, "audit the AI".** Write a plausible, AI-style answer to a realistic task in this domain, with 2–5 deliberate flaws drawn from the list above. Tell the learner it contains flaws, but not how many. They find each flaw, explain why it's wrong using what they've been taught, and fix it. Use only flaws the curriculum has already covered.

**Habit.** Teach the learner to check any AI suggestion against the official docs and against a quick experiment, and to know which parts of this skill are risky enough to always verify.
