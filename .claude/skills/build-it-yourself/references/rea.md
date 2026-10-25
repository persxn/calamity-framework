# REA (Reverse Engineer Anything)

REA (`github.com/morluto/rea`, npm package `rea-agents`, MIT licensed) is an MCP server and CLI that lets an agent inspect **built software** and returns evidence-backed findings with stated limitations. Supported targets include native binaries (through Hopper, Ghidra or IDA), JavaScript and Electron apps, .NET assemblies, Android APKs (through JADX), PyInstaller executables, Go and Rust binary metadata, WASM, Unity IL2CPP metadata, Godot packs, firmware (through Binwalk or Unblob), browser scenarios and HAR or SAZ captures, packet captures, and more.

## Its role in this skill

- **Shipped apps: REA is the primary deep-analysis engine** (`shipped-apps.md`). `artifact_recon.py` gives the first map without REA; REA answers the specific questions that follow.
- **Source repositories: read the source instead.** REA's own skill says to skip it for ordinary source-repository analysis. Use REA on a repo only for its *built outputs* (release binaries, bundles, WASM, native addons) or to compare runtime behaviour with what the source suggests.

## Authorisation (every time)

REA is meant for lawful research, education, interoperability, software preservation, and the analysis of software you own or are authorised to examine. Before running it, confirm the learner obtained the target legitimately and that its terms don't forbid analysis. Commercial engines (IDA Pro, Hopper, JEB) need the learner's own legitimate licence. Never bypass DRM, licensing, anti-cheat, authentication or certificate pinning, and never extract secrets.

## Is it connected?

1. **If REA's tools are in the session**, use them, following the server's actual tool list and schemas. If REA's own `reverse-engineer-anything` skill is installed, load it: it has the up-to-date routing table and recovery steps.
2. **If not, offer the setup.** It changes the learner's agent configuration, so preview it and get approval first:
   ```bash
   npx -y rea-agents@latest setup --client claude_code --dry-run --json   # preview the paths and changes
   npx -y rea-agents@latest setup --client claude_code --yes             # after approval
   ```
   Then restart the agent so the tools appear. REA needs a recent Node.js (22.x or newer at the time of writing; check its README). Native-binary analysis also needs Ghidra, IDA or Hopper installed by the learner; REA doesn't install them. Android code needs JADX and Java.
3. **CLI fallback without MCP**, for a JavaScript or Electron tree or an ASAR:
   ```bash
   npx -y rea-agents@latest analyze-javascript-application /absolute/path/to/app --json
   ```
4. REA changes quickly. Check its README and the tool list for current names; don't trust this file's examples blindly.

## Routing by target (as of REA's current skill; verify against the live tool list)

| Target | First tool |
|---|---|
| Electron ASAR or extracted JS tree | `analyze_javascript_application`; `inspect_electron_fuses` for hardening |
| APK/IPA/MSIX/DMG/PyInstaller archive inventory | `open_binary`, then `inspect_artifact` |
| Android code and classes | `inspect_android_package`; `inspect_apk_signature` for signing |
| .NET assembly | `inspect_managed_artifact` |
| Native binary (ELF/PE/Mach-O) | `open_binary` (Ghidra, IDA or Hopper) |
| Go or Rust binary metadata | `inspect_go_binary` / `inspect_rust_binary` |
| WebAssembly | `inspect_wasm_artifact` |
| Unity IL2CPP | `inspect_il2cpp_metadata` |
| Firmware | `inspect_firmware_regions` / `extract_firmware` |
| A web app flow the learner performs | `capture_browser_scenario` |
| A saved HAR or SAZ | `inspect_web_network_capture` |
| A running Electron app the learner owns | `list_electron_targets` |

## Turning findings into teaching

REA tells you *what the artifact does*. This skill's job is still to teach *how to build it*:

- Put the findings into the teardown with **evidence**, **inference** and **unknown** labels, keeping REA's limitations.
- Map them onto a component picture (processes, modules, IPC, storage, network calls) and a list of techniques.
- Use them as *teaching material*: "here is how the original structures its main and renderer IPC; here are the security trade-offs; now design yours". Never use them as code to copy.
