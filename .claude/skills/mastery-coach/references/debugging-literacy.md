# Debugging literacy: reading the boring signals

Senior engineers read output that juniors scroll past. Logs, flags, exit codes and error bodies are dense with information once you know their shape. Teach that shape for every topic, and drill it.

## What to teach for each tool

- **Streams**: what goes to stdout and what goes to stderr, and why that matters when piping (`2>&1`, `2>/dev/null`, `|&`).
- **Exit codes**: the tool's documented codes; shell conventions (0 is success, 1 a general error, 2 misuse, 126 not executable, 127 command not found, 128+N killed by signal N, so 137 is SIGKILL, often the OOM killer, and 143 is SIGTERM); `$?`, `set -e`, `pipefail`.
- **Verbosity controls**: `-v`/`-vv`/`--debug`/`--trace`, log-level environment variables (`RUST_LOG`, `DEBUG=*`, `GIT_TRACE=1`, `NODE_DEBUG`), dry-run flags (`--dry-run`, `-n`, `--what-if`, `terraform plan`). Teach the learner to reach for these *first*.
- **Log anatomy**: timestamp formats and time zones, levels, structured (JSON) vs unstructured logs, request or correlation IDs, how to follow one request across services, what log rotation does.
- **Error messages**: how this tool phrases errors, which part of the message is the cause and which is just context, and how a stack trace or chain of "caused by" lines reads from the bottom up or the top down.
- **API errors**: HTTP status families (4xx is the caller's fault, 5xx the server's), the specific codes worth knowing (400, 401 vs 403, 404, 409, 422, 429 with `Retry-After`, 500, 502 vs 503 vs 504), error bodies, rate-limit headers, which errors are safe to retry and why idempotency matters.
- **Introspection commands**: `docker inspect`/`logs`/`events`, `kubectl describe`/`get events`, `git reflog`, `journalctl`, `strace`/`ltrace`, `lsof`, `ss`, `EXPLAIN ANALYZE`, browser devtools.
- **Claude Code's own errors**, when the learner uses it as a tool: permission denials and what they protect, tool-call failures and their messages, MCP server connection errors, hook failures, context limits. Treat these like any other tool's errors: read the message, identify the layer, decide the next step.

## The pattern habit

Teach a fixed routine for any unfamiliar output:

1. **Which layer is talking?** The shell, the tool, the runtime, the OS, the network, or a remote service.
2. **What is the first real error?** Later errors are often consequences of the first.
3. **What changed?** Most failures follow a change.
4. **Can I make it smaller or louder?** Reproduce it minimally; turn up verbosity.
5. **What would confirm my theory?** One command that proves or disproves it.

## Drills

Build these into every unit's exercises:

- **Read this output**: show realistic output, logs or an error. Ask what happened, at which layer, and what command they'd run next.
- **Spot the anomaly**: a hundred log lines with one that matters.
- **Exit code detective**: "The CI job died with 137 and no error message. Go."
- **Flag forensics**: a command with six flags. What does each do, and which one is the bug?

Generate drill output that is realistic for the real tool. When possible, have the learner produce the real output on their own machine, and read it together.
