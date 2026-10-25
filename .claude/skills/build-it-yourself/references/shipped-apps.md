# Shipped apps: tearing down software without (all of) its source

The learner points at an app they use, such as a desktop note-taking app, a music player, a file-sharing tool, a chat client, a CLI or a game, and asks how to build it. The output is the same as for a repo: a `teardown.md` that the skill map and build path are built from. The difference is that every statement is labelled with how sure we are.

## 0. Authorisation and limits (check every time)

- The learner obtained the app legitimately (downloaded from the official site or store, or it's open source) and is allowed to examine it. If the licence or terms forbid reverse engineering, say so plainly. Then fall back to the parts that need no artifact analysis: public evidence, black-box behaviour from normal use, and open-source equivalents.
- **Never**: bypass DRM, licensing, anti-cheat, authentication or certificate pinning; extract keys, tokens or other users' data; redistribute the app's code or assets; or run unknown binaries outside a sandbox. Analysing traffic means the learner's own traffic, from their own normal use.
- **The rebuild is original.** Decompiled code and pseudocode are *evidence about behaviour*. They are never source to copy. Names, logos, icons, sounds and copy are the original's trademarks and assets; the learner makes their own.

## 1. Get the artifact

Help the learner locate it. Analysis happens on a copy, never on the installed app in place.

| Platform | What to analyse | Where it usually is |
|---|---|---|
| Electron (Windows/macOS/Linux) | `resources/app.asar` (or an unpacked `resources/app/`) | Windows `%LOCALAPPDATA%\Programs\<App>\resources`; macOS `<App>.app/Contents/Resources`; Linux the AppImage (extract it with `--appimage-extract`) or `/opt/<App>/resources` |
| Android | `.apk` (or split APKs) | the open-source app's releases; `adb shell pm path <pkg>` then `adb pull` from the learner's own device |
| iOS | `.ipa` | only from the learner's own developer builds or open-source apps; App Store binaries are encrypted, so don't try to decrypt them |
| macOS native | the `.app` bundle | `/Applications` |
| Windows native or .NET | the install directory, `.exe`/`.dll`, MSIX | `C:\Program Files\<App>` |
| CLI tools | the binary or release archive | GitHub releases, a package manager cache |
| Web apps | the site itself, the bundled JS and source maps (if published), a HAR capture from the learner's browser | the browser's dev tools |
| Games | the install directory | Unity: `*_Data/`, `global-metadata.dat`; Godot: `.pck`; Unreal: `.pak` |

## 2. Artifact recon (no REA needed)

```bash
python3 <skill-dir>/scripts/artifact_recon.py <path-to-apk|ipa|asar|binary|archive|app-directory>
```

It's static and read-only: it never executes the target. It reports:

- **kind and platform**: APK/AAB/IPA/JAR/MSIX, ASAR, ELF/PE/Mach-O, AppImage, WASM, tar archives, installed directories
- **framework fingerprints**: Electron, Flutter (and its Dart AOT snapshot), React Native/Hermes, Unity/IL2CPP, Godot, Unreal, Xamarin/MAUI, Cordova/Capacitor, Qt, Tauri, PyInstaller, Kotlin, Go, Rust, .NET, Bun/pkg/Node SEA
- **dependencies from real embedded metadata**:
  - npm: every `node_modules/*/package.json` inside the ASAR
  - Go: embedded module build info
  - Rust: crate paths left in the binary
  - Dart: package names in a Flutter snapshot
  - Maven and Android: library versions and `pom.properties`
- **libraries from Android bytecode package names** (OkHttp, Retrofit, Compose, Room, ExoPlayer, Hilt/Koin…), the most-referenced code packages, and obfuscation
- **domains referenced**: candidate backends and services. These are leads to verify, not facts; many are docs links or dead code.
- **licence and third-party notice files**: these often list *every* bundled open-source component

Tested on real artifacts. A Go CLI gave all 59 modules with versions. A Rust CLI gave its crates. A Kotlin Android app gave its library stack and the services it talks to. A Flutter app gave its Dart packages plus a Rust core with its crates. An Electron ASAR gave its entry point and full npm tree. Its pattern lists are incomplete by design, so read the raw output, and use REA for anything deeper.

## 3. REA for depth

Use REA (`rea.md`) to answer specific questions the recon raises. For example:

- **Electron**: `analyze_javascript_application` on the ASAR or extracted tree, for the main and renderer split, preload scripts, IPC channels, windows and the module graph. Use `inspect_electron_fuses` to see how the app is hardened.
- **Android**: `inspect_android_package` for classes, activities and services; `inspect_apk_signature` for signing identity.
- **Native**: `open_binary` with Ghidra, IDA or Hopper, for the specific functions a question depends on (sync, file format, protocol).
- **Go / Rust / .NET / WASM / Unity IL2CPP / firmware**: the matching REA inspector.
- **Web apps**: `capture_browser_scenario` for a declared flow the learner performs, or `inspect_web_network_capture` on a HAR they saved. These give the API surface and the order of calls.

Ask narrow questions ("how does it store notes on disk?", "what happens on the network when I send a message?"), and keep REA's evidence and stated limitations.

## 4. Public evidence (often the richest source)

- **About and third-party notices screens** in the app: the definitive dependency list.
- **Engineering blogs and talks** by the company: architecture write-ups, migrations ("how we moved from X to Y"), performance stories.
- **Job postings**: the stack they hire for.
- **Docs, API references, status pages and changelogs**: the shape of the backend, release cadence, feature history.
- **Open-source pieces** the company publishes (SDKs, protocol specs, libraries).
- **Community analyses**: only as leads; verify them before using.

Cite everything (URL and access date) in the teardown.

## 5. The evidence ladder

Label every architectural statement in `teardown.md`:

| Label | Meaning | Example |
|---|---|---|
| **Evidence** | Directly observed in bytes, files, REA output or an official source | "Bundles `better-sqlite3` 11.10.0 (ASAR `node_modules/better-sqlite3/package.json`)" |
| **Inference** | A reasonable conclusion from evidence, with the reasoning stated | "Probably stores notes in a local SQLite file, since better-sqlite3 is bundled and a `.db` appears in the app's data directory" |
| **Unknown** | Not determinable with the allowed methods | "Server-side conflict resolution: not observable from the client" |

Never promote an inference to a fact in teaching. Unknowns become **design decisions the learner makes themselves** (a natural bridge into idea mode for that part).

## 6. From teardown to behavioural spec

For a shipped app, the build target is a **behavioural spec**, not code parity:

1. List the user-facing features. Mark the core ones for v1, usually 3–6 of them.
2. For each core feature, describe the behaviour: inputs, outputs, states, edge cases, and how it performs ("search results appear as you type, under 50 ms for 10k notes").
3. Name the **hard parts**: the techniques that make the app impressive (a sync engine, CRDTs, offline-first behaviour, a media pipeline, P2P discovery, an incremental parser, a rendering engine). These become **core** skills in the skill map.
4. Choose the learner's stack. Default to the original's stack when the learner wants to learn it (a close rebuild). Otherwise pick an open, equivalent stack that serves their learning goals (then it's a *reinterpretation*). Record this in an ADR.
5. Server-side parts the client can't see are designed by the learner (idea-mode design review applies).

## 7. Comparing with the original (in milestone reviews)

There's no source to diff against, so compare **behaviour**:

- the same scenario run in both apps: correctness, edge cases, latency, memory, startup time, bundle and install size
- network behaviour (the learner's own HAR for both): the number of requests, payload sizes, caching
- the original's design choices revealed in the teardown vs the learner's choices: what each costs

Turn the differences into review questions: "theirs starts in 0.4 s and yours in 2.1 s; what does Electron load before first paint, and what could you defer?"
