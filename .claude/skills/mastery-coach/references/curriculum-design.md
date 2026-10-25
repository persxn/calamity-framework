# Curriculum design

The curriculum is the promise of mastery. If it's missing something, the learner will hit that gap in an interview or in production. Build it carefully, show it to the learner, and treat it as a living document in state.

## 1. Map the territory before ordering it

Gather the full surface of the topic from primary sources:

- **Run the tool if it's installed.** Use `man <cmd>`, `<cmd> --help`, `<cmd> help <subcommand>`, `info`, and the tool's own docs command (`docker --help`, `git help -a`, `kubectl api-resources`, `python -m pydoc`). Enumerate every subcommand and flag from the actual output.
- **Fetch the official reference docs**: the language spec, the CLI reference, the configuration reference, the API reference, and the changelog or release notes.
- **Read the source tree layout** for open-source tools. The way the repo is split into directories often shows the real architecture.

Then sort everything you found using this checklist. A topic isn't fully mapped until each row has been considered (some will be empty for some topics):

| Category | Examples |
|---|---|
| History and philosophy | Origin, design principles, what it replaced |
| Foundations from other fields | CPU and memory for pointers; TCP/IP for HTTP; filesystems and processes for Docker; relational algebra for SQL |
| Core concepts and mental model | The 3–7 ideas that everything else is built from |
| Installation and setup | Every supported install path, version managers, verifying the install, uninstalling cleanly |
| Configuration | Config files, their locations and precedence, environment variables, defaults and where they come from |
| Full command and API surface | Every command, subcommand, function or method |
| Every flag and option | Including rare ones, grouped by purpose |
| Inputs and outputs | Formats, machine-readable output (`--json`, `--format`, `-o yaml`), piping and composition |
| Exit codes and errors | Every documented error class, what triggers it, how to read it |
| Internals | How it actually works underneath: data structures, algorithms, processes, on-disk formats |
| Performance | Where it's slow, how to measure it, how to tune it |
| Security | Threat model, insecure defaults, hardening |
| Failure modes | How it breaks in production, with real incidents |
| Debugging and observability | Logs, verbose and trace modes, introspection commands |
| Testing | How to test code or config that uses it |
| Ecosystem | Plugins, integrations, companion tools, common stacks |
| Legacy and deprecated | Removed features and *why* they were removed (this shows the designers' changing priorities) |
| Alternatives | Competing tools, honest trade-offs, when to pick each |
| What's new and next | Recent releases, the roadmap, successor tools (check with a search) |
| Interview territory | The questions this topic draws in real interviews |

## 2. Build the prerequisite graph

For every unit, list the ideas it *uses*. Each of those must be taught by an earlier unit or already known (confirmed by the intake diagnostic, not assumed).

- Trace the graph down to bedrock. Pointers use addresses; addresses need RAM organisation; RAM organisation needs the idea of memory cells and buses; those need sequential circuits. If the learner hasn't been taught a link in that chain, that link becomes a unit.
- Prerequisites from other fields are first-class units, not footnotes.
- Order the units topologically. Where there's a choice, put the thing that gives the learner the most "aha" earliest.

## 3. The author's lens: the depth standard

Each unit is taught by explaining the mechanism underneath, in the detail its designer would know. The bar is that the learner could have invented the feature, given the problem and the layer below.

The gold standard, for pointers in C:

1. **What digital circuits are.** Voltages as 0 and 1, and logic gates.
2. **Combinational circuits do maths.** Half adders and full adders, ripple-carry adders, and how an ALU picks an operation with a multiplexer.
3. **Sequential circuits remember.** Feedback creates a latch (SR, then D). Add a clock to get a flip-flop. Put flip-flops side by side to get a register.
4. **How they fit together into a CPU.** The ALU, the register file (including the program counter, stack pointer and instruction register), and the control unit, which decodes an instruction and drives the datapath.
5. **The three buses.** The address bus says *where*, the data bus carries *what*, and the control bus says *read or write, and when*. Bus width limits how much memory can be addressed.
6. **What memory looks like inside RAM.** A grid of cells, one address per byte, and words, alignment and endianness. Draw it.
7. **How addresses are allocated.** The process address space (text, data, BSS, heap, stack), virtual and physical addresses, pages, and what `malloc` and the stack frame actually do.
8. **Fetch and operate.** The fetch-decode-execute cycle; how a load instruction puts an address on the bus, the value comes back into a register, and the ALU works on it.
9. **Only now, the pointer.** A variable whose *value is an address*. `*p` puts that address on the bus. `p + 1` scales by `sizeof(*p)` because addresses are byte-granular and the type tells the compiler the stride.

Apply the same descent to every topic:

- Docker → processes, namespaces, cgroups, union filesystems, the container runtime.
- Git → content-addressable storage, hashing, the object model, the DAG.
- React → the DOM, the cost of DOM operations, reconciliation, the fiber architecture.
- SQL → relations, B-trees, pages, the query planner.
- `ls` → syscalls, inodes, directory entries, `stat`, terminal capabilities.

Don't flatten this depth in in-depth mode. Make it digestible instead: chunk it, draw it, and check after each step.

## 4. Unit format in state

```markdown
## U07 — Pointer arithmetic and arrays
- prereqs: U03 (RAM layout), U05 (types and sizeof), U06 (pointer basics)
- covers: p+n scaling, array decay, a[i] == *(a+i), pointer subtraction (ptrdiff_t), out-of-bounds UB
- surface: (none — language feature)
- field reading: Linux kernel container_of macro; Heartbleed (CVE-2014-0160) as a bounds failure
- status: not-started | in-progress | done | needs-review
```

## 5. Show it and keep it alive

- Present the curriculum in conversation as a compact numbered roadmap, grouped into parts. Mention roughly how many sessions it represents. Ask whether anything they care about is missing.
- As teaching reveals gaps (a learner stumbles on something nobody assumed they'd need), insert a unit and say so.
- Units marked `needs-review` come back in recall, and are re-taught if recall keeps failing.
