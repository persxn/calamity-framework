# Worked example: a shipped app, torn down blind and checked against its source

**Target:** LocalSend 1.18.2 Android APK (`LocalSend-1.18.2-android-arm64v8.apk`, from the project's GitHub releases). LocalSend is open source, so the blind teardown could be checked against the real repository afterwards. This is an excerpt showing the *shape* of the outputs, not a full teardown.

## 1. Artifact recon (blind; `artifact_recon.py`, about 3 s)

- **[E]** Android APK; Flutter (`lib/arm64-v8a/libflutter.so`, `libapp.so` Dart AOT snapshot); Kotlin metadata
- **[E]** A Rust native library, `librust_lib_localsend_app.so`, whose embedded crate paths include `tokio`, `reqwest`, `serde` and crypto crates (`aes`, `aead`, `curve25519-dalek`…)
- **[E]** Dart packages named in the snapshot: `refena` (state), `flutter_rust_bridge` (FFI), `dart_mappable` (serialisation), `slang` (i18n), `pretty_qr_code`, `photo_manager`…
- **[E]** Java/Kotlin code minified with R8 (most class references are in one- or two-letter packages)
- **[I]** Architecture: a Flutter UI over a Rust core reached through flutter_rust_bridge. The networking and crypto live in Rust, because reqwest, tokio and the crypto crates are in the `.so`, not in Dart.
- **[?]** Wire protocol and discovery mechanism: not visible from these bytes. Next step: REA, or the learner's own packet capture on their LAN.

## 2. Checked against the source (`repo_recon.py` on github.com/localsend/localsend)

| Blind claim | Source says | Verdict |
|---|---|---|
| Flutter app | Dart, about 150k lines; `app/pubspec.yaml` depends on `flutter` | ✓ |
| Rust core via FFI | `packages/localsend_isolates/rust/Cargo.toml` (crate `rust_lib_localsend_app`), `flutter_rust_bridge` | ✓ |
| Refena, dart_mappable, slang | All in `app/pubspec.yaml` | ✓ |
| Networking in Rust (tokio, reqwest) | Rust crates `packages/core`, `cli`, `server` use tokio, reqwest, axum | ✓ |
| Discovery: unknown | `packages/localsend_isolates/lib/constants.dart:14,24`: port 53317, multicast group 224.0.0.167; `packages/core/src/multicast/` | Correctly left as unknown; resolved with source |

Archaeology: the first commits (December 2022) run *init → iOS → receiver, discovery, settings → file picker → start/stop server → send-request handling → send files*. That's the real build order and a natural milestone sequence. The licence is Apache-2.0 (it was MIT early in the history). The repo also has `CODE_SIGNING.md`, `fastlane/` and per-platform release workflows, which are good study material for the shipping milestones.

## 3. Skill-map excerpt (for a learner who knows basic Dart)

| # | Node | Layer | Tier | First needed |
|---|---|---|---|---|
| S01 | UDP, multicast groups, LAN discovery | foundation | core | M2 |
| S02 | HTTP/REST server and client basics | foundation | core | M3 |
| S03 | TLS and self-signed certificates, fingerprints | foundation | core | M4 |
| S04 | Flutter widgets, layout, navigation | tool | core | M1 |
| S05 | State management (Refena or Riverpod) | tool | supporting | M1 |
| S06 | Dart isolates and async streams | concept | core | M3 |
| S07 | Rust + flutter_rust_bridge FFI (optional "close rebuild" track) | tool | supporting | M5 |
| S08 | Android/desktop packaging, signing, store release | shipping | supporting | M7–M8 |

## 4. Build-path excerpt

- **M1 Walking skeleton**: a Flutter app showing the device's alias, built for Android and one desktop OS by CI.
- **M2 Discover peers**: devices announce themselves and appear in a list (multicast).
- **M3 Send a text message** between two devices over HTTP.
- **M4 Make it private**: HTTPS with per-device certificates, plus fingerprint verification.
- **M5 Send files**: streaming, progress, cancel, resume on failure.
- **M6 Accept/reject flow and history**.
- **M7 Ship to Android**: release build, signing key handling, an installable APK on GitHub Releases.
- **M8 Ship to desktop**: packaged installers, signing where available, auto-update strategy.

*Compare with the original after each milestone:* for example, after M2 read `packages/core/src/multicast/` and `packages/localsend_isolates/lib/constants.dart`, then discuss why it uses a fixed port and multicast group, and what happens on networks that block multicast.
